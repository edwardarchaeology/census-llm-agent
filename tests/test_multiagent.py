"""
Test script for multi-agent system.
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mvp_multiagent import run_multiagent_query, print_result

# Test queries
test_queries = [
    "What are the top 5 census tracts in Caddo Parish by poverty rate?",
    "Show me the top 3 tracts in Ouachita Parish by median income",
    "What tracts in East Baton Rouge have population density over 3000?",
    "Find tracts in Lafayette with poverty rate under 10%",
    "Top 5 tracts in St. Tammany Parish by median income",
]

def main():
    print("=" * 80)
    print("TESTING MULTI-AGENT SYSTEM")
    print("=" * 80)
    print()
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nTest {i}/{len(test_queries)}: {query}")
        print("-" * 80)
        try:
            result = run_multiagent_query(query, verbose=True)
            print_result(result)
            print("[PASS] Query executed successfully")
        except Exception as e:
            print(f"\n[FAIL] Error: {e}")
            import traceback
            traceback.print_exc()
        print("=" * 80)

if __name__ == "__main__":
    main()
