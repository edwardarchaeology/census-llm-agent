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
                records.append({
                    "variable_id": var_id,
                    "label": meta.get("label", ""),
                    "concept": meta.get("concept", ""),
                    "predicateType": meta.get("predicateType", ""),
                })
    
    df = pd.DataFrame(records)
    
    if df.empty:
        print("Warning: No variables found in Census metadata")
        return df
    
    # Extract table prefix (e.g., "B19013" from "B19013_001E")
    df["table"] = df["variable_id"].str.extract(r"^([A-Z]+\d+)")[0]
    
    return df


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
            "label": row["label"],
            "concept": row["concept"],
            "score": row["adjusted_score"],
            "is_derived": False
        })
    
    return results


def get_derived_metric_info(measure: str) -> Optional[dict]:
    """Get derived metric information if measure is a derived metric."""
    normalized = normalize_measure(measure)
    return DERIVED_METRICS.get(normalized)
