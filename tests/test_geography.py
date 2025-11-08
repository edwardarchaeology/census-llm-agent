"""
Test script for enhanced geography capabilities.
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'single_agent'))

from mvp import run_query

# Test queries for different parishes and cities
test_queries = [
    "What are the top 5 census tracts in Caddo Parish by poverty rate?",
    "Show me the top 3 tracts in Ouachita Parish by median income",
    "What tracts in East Baton Rouge have population density over 3000?",
    "Find tracts in Shreveport with African American share above 60 percent",
    "Top 5 tracts in St. Tammany Parish by median income",
    "Tracts in Calcasieu Parish with poverty rate under 10%",
]

def main():
    print("=" * 80)
    print("TESTING ENHANCED GEOGRAPHY SYSTEM")
    print("=" * 80)
    print()
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nTest {i}/{len(test_queries)}: {query}")
        print("-" * 80)
        try:
            run_query(query)
            print("\n[PASS] Query executed successfully")
        except Exception as e:
            print(f"\n[FAIL] Error: {e}")
        print("=" * 80)

if __name__ == "__main__":
    main()
