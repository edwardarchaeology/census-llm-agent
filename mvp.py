"""
MVP CLI runner for LLM Census Data Getter.
"""
import sys
from typing import Optional

import pandas as pd

from intent import extract_intent, Intent
from resolver import resolve_measure, get_derived_metric_info
from acs_tools import fetch_data_for_query


def run_query(question: str) -> pd.DataFrame:
    """
    Main query orchestration: extract intent, resolve measure, fetch data, compute result.
    
    Args:
        question: Natural language query
    
    Returns:
        DataFrame with GEOID, tract_name, value, sorted appropriately
        The human-readable label is stored in df.attrs["label"]
    """
    print(f"\n>>> Analyzing: {question}")
    
    # Extract intent from question
    intent = extract_intent(question)
    print(f"Task: {intent.task}, Measure: {intent.measure}")
    if intent.geography.county_fips:
        print(f"County FIPS: {intent.geography.county_fips}")
    
    # Resolve measure to variable(s)
    resolved = resolve_measure(intent.measure, year=2023, top_n=1)
    
    if not resolved:
        raise ValueError(f"Could not resolve measure: {intent.measure}")
    
    result_info = resolved[0]
    label = result_info["label"]
    
    print(f"Resolved to: {label}")
    
    # Fetch data based on whether it's derived or direct
    is_percentage_metric = False
    
    if result_info.get("is_derived", False):
        # Derived metric
        var_ids = result_info["variables"]
        needs_area = result_info["needs_area"]
        formula = result_info["formula"]
        
        # Check if this is a percentage metric (label contains %)
        is_percentage_metric = "%" in label
        
        df = fetch_data_for_query(
            var_ids=var_ids,
            year=2023,
            county_fips=intent.geography.county_fips,
            needs_area=needs_area
        )
        
        # Compute derived value
        df["value"] = formula(df)
        
    else:
        # Direct ACS variable
        var_id = result_info["variable_id"]
        
        df = fetch_data_for_query(
            var_ids=[var_id],
            year=2023,
            county_fips=intent.geography.county_fips,
            needs_area=False
        )
        
        df["value"] = df[var_id]
    
    # Build tract_name from NAME
    df["tract_name"] = df["NAME"].str.replace(r"Census Tract \d+(\.\d+)?,\s*", "", regex=True)
    df["tract_name"] = df["tract_name"].str.replace(", Louisiana", "")
    
    # Filter out rows with missing values
    df = df[df["value"].notna()].copy()
    
    if df.empty:
        print("WARNING: No data found matching criteria")
        result = pd.DataFrame(columns=["GEOID", "tract_name", "value"])
        result.attrs["label"] = label
        return result
    
    # Adjust intent values for percentage metrics if needed
    # If the metric is in % (0-100) but intent value is 0-1, scale it up
    if is_percentage_metric and intent.task in ["filter", "range"]:
        if intent.value is not None and intent.value < 1:
            intent.value = intent.value * 100
        if intent.range_min is not None and intent.range_min < 1:
            intent.range_min = intent.range_min * 100
        if intent.range_max is not None and intent.range_max < 1:
            intent.range_max = intent.range_max * 100
    
    # Apply task-specific logic
    if intent.task == "filter":
        df = _apply_filter(df, intent)
    elif intent.task == "range":
        df = _apply_range(df, intent)
    elif intent.task in ["top", "bottom"]:
        df = _apply_top_bottom(df, intent)
    
    # Select final columns
    result = df[["GEOID", "tract_name", "value"]].copy()
    result.attrs["label"] = label
    
    print(f"Found {len(result)} tracts")
    
    return result


def _apply_filter(df: pd.DataFrame, intent: Intent) -> pd.DataFrame:
    """Apply filter operation."""
    if intent.op and intent.value is not None:
        if intent.op == ">=":
            df = df[df["value"] >= intent.value]
        elif intent.op == "<=":
            df = df[df["value"] <= intent.value]
        elif intent.op == ">":
            df = df[df["value"] > intent.value]
        elif intent.op == "<":
            df = df[df["value"] < intent.value]
        elif intent.op == "=":
            df = df[df["value"] == intent.value]
    
    # Sort descending by default for filters
    df = df.sort_values("value", ascending=False)
    
    return df


def _apply_range(df: pd.DataFrame, intent: Intent) -> pd.DataFrame:
    """Apply range filtering."""
    if intent.range_min is not None:
        df = df[df["value"] >= intent.range_min]
    if intent.range_max is not None:
        df = df[df["value"] <= intent.range_max]
    
    # Sort ascending for range queries
    df = df.sort_values("value", ascending=True)
    
    return df


def _apply_top_bottom(df: pd.DataFrame, intent: Intent) -> pd.DataFrame:
    """Apply top/bottom selection."""
    ascending = intent.sort == "asc" if intent.sort else (intent.task == "bottom")
    
    df = df.sort_values("value", ascending=ascending)
    
    if intent.limit:
        df = df.head(intent.limit)
    
    return df


def print_result(df: pd.DataFrame):
    """Print result table in a tidy format."""
    if df.empty:
        print("\nNo results found.\n")
        return
    
    label = df.attrs.get("label", "Value")
    
    print(f"\n{'='*80}")
    print(f"Measure: {label}")
    print(f"{'='*80}")
    
    # Format the DataFrame for display
    display_df = df.copy()
    
    # Format value column based on type
    if "%" in label or "Rate" in label or "Share" in label:
        display_df["value"] = display_df["value"].map(lambda x: f"{x:.2f}%")
    elif "Density" in label:
        display_df["value"] = display_df["value"].map(lambda x: f"{x:.2f}")
    elif "Income" in label or "$" in label:
        display_df["value"] = display_df["value"].map(lambda x: f"${x:,.0f}")
    else:
        display_df["value"] = display_df["value"].map(lambda x: f"{x:,.0f}")
    
    # Print without index
    print(display_df.to_string(index=False))
    print(f"{'='*80}\n")


def main():
    """Main CLI loop."""
    print("=" * 80)
    print("LLM Census Data Getter - Louisiana Edition")
    print("=" * 80)
    print("\nAsk natural language questions about Louisiana census tracts.")
    print("Examples:")
    print("  - What tract has the highest median income in New Orleans?")
    print("  - Give me all tracts with 20% or more African Americans")
    print("  - Show me the top 10 highest population density tracts")
    print("\nType 'quit' or 'exit' to stop.\n")
    
    while True:
        try:
            question = input("❓ Your question: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ["quit", "exit", "q"]:
                print("\nGoodbye!")
                break
            
            # Run query
            result = run_query(question)
            
            # Print result
            print_result(result)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nERROR: {e}\n")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
