"""
Census variable resolver with fuzzy matching and derived metrics registry.
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
from rapidfuzz import fuzz

CACHE_DIR = Path("./cache")
CACHE_DIR.mkdir(exist_ok=True)

# Derived metrics registry with safe formulas
DERIVED_METRICS = {
    "population density": {
        "label": "Population Density (per km²)",
        "variables": ["B01003_001E"],  # Total population
        "needs_area": True,
        "formula": lambda df: df["B01003_001E"] / df["area_km2"]
    },
    "poverty rate": {
        "label": "Poverty Rate (%)",
        "variables": ["B17001_002E", "B01001_001E"],  # Income below poverty / Total pop
        "needs_area": False,
        "formula": lambda df: (df["B17001_002E"] / df["B01001_001E"]) * 100
    },
    "african american share": {
        "label": "African American Population Share (%)",
        "variables": ["B02001_003E", "B02001_001E"],  # Black alone / Total
        "needs_area": False,
        "formula": lambda df: (df["B02001_003E"] / df["B02001_001E"]) * 100
    }
}

# Measure synonyms for normalization
MEASURE_SYNONYMS = {
    "median income": "median household income",
    "income": "median household income",
    "percent black": "african american share",
    "black share": "african american share",
    "percent african american": "african american share",
    "pop density": "population density",
    "density": "population density",
}

# Louisiana helpers
STATE_FIPS = {"louisiana": "22", "la": "22"}

CITY_TO_COUNTY_FIPS = {
    "new orleans": "071",
    "baton rouge": "033",
    "lafayette": "055",
}


def normalize_measure(phrase: str) -> str:
    """Normalize measure phrase using synonym mapping."""
    phrase_lower = phrase.lower().strip()
    return MEASURE_SYNONYMS.get(phrase_lower, phrase_lower)


def clean_census_label(label: str) -> str:
    """
    Clean up Census variable labels for display.
    
    Removes:
    - "Estimate!!" prefixes
    - "Annotation!!" prefixes
    - Multiple exclamation marks
    - Leading/trailing whitespace
    
    Examples:
        "Estimate!!Median nonfamily household income..." -> "Median nonfamily household income..."
        "Estimate!!Total!!Population" -> "Total Population"
    """
    if not label:
        return label
    
    # Remove "Estimate!!" and "Annotation!!" prefixes
    label = label.replace("Estimate!!", "")
    label = label.replace("Annotation!!", "")
    
    # Replace remaining double exclamation marks with spaces
    label = label.replace("!!", " ")
    
    # Clean up multiple spaces and trim
    label = " ".join(label.split())
    
    return label


def get_census_variables_cached(year: int = 2023, ttl_days: int = 14) -> pd.DataFrame:
    """
    Download and cache Census ACS 5-year variables metadata.
    Returns DataFrame with estimate variables (*_E).
    """
    cache_file = CACHE_DIR / f"acs_{year}_acs5_variables.json"
    
    # Check cache age
    if cache_file.exists():
        file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if file_age < timedelta(days=ttl_days):
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = _download_variables(year, cache_file)
    else:
        data = _download_variables(year, cache_file)
    
    # Build DataFrame of estimate variables
    records = []
    variables = data.get("variables", {})
    for var_id, meta in variables.items():
        # Filter for estimate variables (those ending with E and are not geography/metadata vars)
        if isinstance(meta, dict) and meta.get("predicateType") in ["int", "float", "string"]:
            # Check if it's a data variable (starts with letter, contains underscore, ends with E)
            if "_" in var_id and var_id[0].isalpha() and "E" in var_id:
                label = meta.get("label", "")
                concept = meta.get("concept", "")
                
                # Create human-readable description
                description = _create_variable_description(var_id, label, concept)
                
                records.append({
                    "variable_id": var_id,
                    "label": label,
                    "concept": concept,
                    "description": description,
                    "predicateType": meta.get("predicateType", ""),
                })
    
    df = pd.DataFrame(records)
    
    if df.empty:
        print("Warning: No variables found in Census metadata")
        return df
    
    # Extract table prefix (e.g., "B19013" from "B19013_001E")
    df["table"] = df["variable_id"].str.extract(r"^([A-Z]+\d+)")[0]
    
    return df


def _create_variable_description(var_id: str, label: str, concept: str) -> str:
    """
    Create a human-readable description for a Census variable.
    Helps LLM agents understand what the variable represents.
    """
    # Clean up the label
    clean_label = clean_census_label(label)
    
    # Build description
    parts = []
    
    # Add what it measures
    if clean_label:
        parts.append(f"Measures: {clean_label}")
    
    # Add context from concept if different from label
    if concept and concept.lower() != clean_label.lower():
        clean_concept = clean_census_label(concept)
        # Check if concept adds new information
        if clean_concept.lower() not in clean_label.lower():
            parts.append(f"Context: {clean_concept}")
    
    # Identify the type of data based on table prefix
    table_prefix = var_id.split("_")[0] if "_" in var_id else ""
    
    if table_prefix.startswith("B01"):
        parts.append("Category: Population and Age")
    elif table_prefix.startswith("B02"):
        parts.append("Category: Race")
    elif table_prefix.startswith("B03"):
        parts.append("Category: Hispanic/Latino Origin")
    elif table_prefix.startswith("B17"):
        parts.append("Category: Poverty Status")
    elif table_prefix.startswith("B19"):
        parts.append("Category: Income")
    elif table_prefix.startswith("B23"):
        parts.append("Category: Employment Status")
    elif table_prefix.startswith("B25"):
        parts.append("Category: Housing Characteristics")
    
    # Indicate if it's a total/main estimate
    if var_id.endswith("_001E"):
        parts.append("Type: Main estimate or total")
    
    return " | ".join(parts) if parts else clean_label


def _download_variables(year: int, cache_file: Path) -> dict:
    """Download variables JSON from Census API."""
    url = f"https://api.census.gov/data/{year}/acs/acs5/variables.json"
    print(f"Downloading Census variables for {year}...")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f)
    
    return data


def resolve_measure(phrase: str, year: int = 2023, top_n: int = 1) -> list[dict]:
    """
    Resolve a measure phrase to Census variable IDs using fuzzy matching.
    
    Returns list of dicts with keys: variable_id, label, concept, score.
    Prefers DP tables, then S, then B when scores are tied.
    """
    phrase_normalized = normalize_measure(phrase)
    
    # Check if it's a derived metric
    if phrase_normalized in DERIVED_METRICS:
        metric_info = DERIVED_METRICS[phrase_normalized]
        return [{
            "variable_id": "DERIVED",
            "label": metric_info["label"],
            "concept": phrase_normalized,
            "score": 100.0,
            "is_derived": True,
            "variables": metric_info["variables"],
            "needs_area": metric_info["needs_area"],
            "formula": metric_info["formula"]
        }]
    
    df = get_census_variables_cached(year)
    
    # Fuzzy match over label and concept
    df["label_score"] = df["label"].apply(
        lambda x: fuzz.token_set_ratio(phrase_normalized, x.lower())
    )
    df["concept_score"] = df["concept"].apply(
        lambda x: fuzz.token_set_ratio(phrase_normalized, x.lower())
    )
    
    # Combined score (weighted average)
    df["score"] = df["label_score"] * 0.7 + df["concept_score"] * 0.3
    
    # Penalty for demographic-specific variables (prefer general population stats)
    # Look for race/ethnicity qualifiers in the concept or label
    demographic_keywords = [
        "white alone", "black alone", "african american alone", "asian alone", 
        "hispanic", "latino", "native hawaiian", "pacific islander", 
        "american indian", "alaska native", "two or more races",
        "nonveteran", "veteran", "food stamps", "snap",
        "foreign born", "native born", "citizen", "noncitizen",
        "renter occupied", "owner occupied", "with a mortgage", "without a mortgage",
        "male householder", "female householder", "nonfamily household"
    ]
    
    def has_demographic_filter(text):
        if pd.isna(text):
            return False
        text_lower = str(text).lower()
        return any(keyword in text_lower for keyword in demographic_keywords)
    
    df["has_demographic"] = df["concept"].apply(has_demographic_filter) | df["label"].apply(has_demographic_filter)
    
    # Apply penalty: subtract 15 points for demographic-specific variables
    df.loc[df["has_demographic"], "score"] = df.loc[df["has_demographic"], "score"] - 15
    
    # Boost for simple, canonical variables (e.g., B19013_001E for median household income)
    # Variables ending in _001E are often the "total" or main estimate
    df["is_main_estimate"] = df["variable_id"].str.endswith("_001E")
    df.loc[df["is_main_estimate"], "score"] = df.loc[df["is_main_estimate"], "score"] + 5
    
    # Table preference penalty: DP=0, S=0.5, B=1.0, others=2.0
    def table_penalty(table_prefix):
        if pd.isna(table_prefix):
            return 2.0
        if table_prefix.startswith("DP"):
            return 0.0
        elif table_prefix.startswith("S"):
            return 0.5
        elif table_prefix.startswith("B"):
            return 1.0
        else:
            return 2.0
    
    df["penalty"] = df["table"].apply(table_penalty)
    df["adjusted_score"] = df["score"] - df["penalty"]
    
    # Sort and return top results
    df_sorted = df.sort_values("adjusted_score", ascending=False)
    results = []
    
    for _, row in df_sorted.head(top_n).iterrows():
        results.append({
            "variable_id": row["variable_id"],
            "label": clean_census_label(row["label"]),
            "concept": row["concept"],
            "description": row.get("description", ""),
            "score": row["adjusted_score"],
            "is_derived": False
        })
    
    return results


def get_derived_metric_info(measure: str) -> Optional[dict]:
    """Get derived metric information if measure is a derived metric."""
    normalized = normalize_measure(measure)
    return DERIVED_METRICS.get(normalized)
