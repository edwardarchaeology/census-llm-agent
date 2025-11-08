"""
Multi-agent MVP CLI runner for LLM Census Data Getter.
Uses specialized agents for improved accuracy and robustness.
"""
import sys
import pandas as pd
from typing import Dict, Any

from agents.orchestrator_agent import OrchestratorAgent
from acs_tools import fetch_data_for_query


def run_multiagent_query(question: str, verbose: bool = True) -> pd.DataFrame:
    """
    Run query through multi-agent system.
    
    Args:
        question: Natural language query
        verbose: Whether to print detailed progress
        
    Returns:
        DataFrame with GEOID, tract_name, value
    """
    # Initialize orchestrator (which initializes all agents)
    orchestrator = OrchestratorAgent()
    
    # Process query through agent system
    result = orchestrator.process_query(question, verbose=verbose)
    
    # Check for low confidence - ask for clarification
    if result["variable"]["confidence"] < 0.6:
        clarification = orchestrator.ask_clarification(result["variable"])
        print(f"\n{clarification}\n")
        return pd.DataFrame(columns=["GEOID", "tract_name", "value"])
    
    # Execute query based on complexity
    if result["execution_type"] == "simple":
        return _execute_simple_query(result, verbose)
    else:
        return _execute_complex_query(result, verbose)


def _execute_simple_query(result: Dict[str, Any], verbose: bool = True) -> pd.DataFrame:
    """Execute a simple single-step query."""
    intent = result["intent"]
    geography = result["geography"]
    variable = result["variable"]
    
    if verbose:
        print(f">>> Executing simple query...")
    
    # Determine if it's a percentage metric
    is_percentage_metric = "%" in variable["label"]
    
    # Fetch data based on whether it's derived or direct
    if variable["is_derived"]:
        # Derived metric
        df = fetch_data_for_query(
            var_ids=variable["variables"],
            year=2023,
            county_fips=geography["fips"],
            needs_area=variable.get("needs_area", False)
        )
        
        # Compute derived value
        df["value"] = variable["formula"](df)
        
    else:
        # Direct ACS variable
        var_id = variable.get("variable_id")
        if not var_id:
            raise ValueError("No variable ID found")
        
        df = fetch_data_for_query(
            var_ids=[var_id],
            year=2023,
            county_fips=geography["fips"],
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
        result_df = pd.DataFrame(columns=["GEOID", "tract_name", "value"])
        result_df.attrs["label"] = variable["label"]
        return result_df
    
    # Adjust intent values for percentage metrics if needed
    if is_percentage_metric and intent["task"] in ["filter", "range"]:
        if intent.get("value") is not None and intent["value"] < 1:
            intent["value"] = intent["value"] * 100
    
    # Apply task-specific logic
    task = intent["task"]
    
    if task == "filter":
        op = intent.get("op")
        value = intent.get("value")
        if op and value is not None:
            if op == ">=":
                df = df[df["value"] >= value]
            elif op == "<=":
                df = df[df["value"] <= value]
            elif op == ">":
                df = df[df["value"] > value]
            elif op == "<":
                df = df[df["value"] < value]
            elif op == "=":
                df = df[df["value"] == value]
        df = df.sort_values("value", ascending=False)
    
    elif task == "range":
        range_min = intent.get("range_min")
        range_max = intent.get("range_max")
        if range_min is not None:
            df = df[df["value"] >= range_min]
        if range_max is not None:
            df = df[df["value"] <= range_max]
        df = df.sort_values("value", ascending=True)
    
    elif task in ["top", "bottom"]:
        ascending = (task == "bottom")
        df = df.sort_values("value", ascending=ascending)
        limit = intent.get("limit", 10)
        df = df.head(limit)
    
    # Select final columns
    result_df = df[["GEOID", "tract_name", "value"]].copy()
    result_df.attrs["label"] = variable["label"]
    
    if verbose:
        print(f">>> Found {len(result_df)} tracts")
    
    return result_df


def _execute_complex_query(result: Dict[str, Any], verbose: bool = True) -> pd.DataFrame:
    """Execute a complex multi-step query."""
    plan = result["plan"]
    
    if verbose:
        print(f">>> Executing complex query with {len(plan.get('steps', []))} steps...")
    
    # For now, complex queries return a message
    # Future: Implement full multi-step execution
    print("\nComplex query detected! This requires multi-step processing.")
    print(f"Plan: {plan.get('reasoning', 'No reasoning provided')}")
    print("\nSteps:")
    for step in plan.get("steps", []):
        print(f"  {step['step']}. {step.get('description', step.get('action', 'Unknown'))}")
    
    print("\nNote: Complex query execution is not yet fully implemented.")
    print("For now, please try breaking your query into simpler parts.\n")
    
    result_df = pd.DataFrame(columns=["GEOID", "tract_name", "value"])
    result_df.attrs["label"] = "Complex Query (Not Yet Implemented)"
    return result_df


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
    print("Multi-Agent LLM Census Data Getter - Louisiana Edition")
    print("=" * 80)
    print("\nUsing specialized agents for improved accuracy:")
    print("  - Orchestrator Agent: Coordinates the system")
    print("  - Geography Agent: Resolves Louisiana parishes and cities")
    print("  - Variable Agent: Matches measures to Census variables")
    print("  - Query Planner: Decomposes complex queries")
    print("\nAll agents use phi3:mini (~2GB memory)")
    print("\nAsk natural language questions about Louisiana census tracts.")
    print("Examples:")
    print("  - What tract has the highest median income in New Orleans?")
    print("  - Give me all tracts with 20% or more African Americans")
    print("  - Show me the top 10 highest population density tracts")
    print("  - Compare poverty rates in New Orleans and Baton Rouge")
    print("\nType 'quit' or 'exit' to stop.\n")
    
    while True:
        try:
            question = input("Your question: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ["quit", "exit", "q"]:
                print("\nGoodbye!")
                break
            
            # Run query through multi-agent system
            result = run_multiagent_query(question, verbose=True)
            
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
