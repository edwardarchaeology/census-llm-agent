"""
Test the corrected Caddo Parish poverty query.
"""
from mvp import run_query, print_result

query = "What are the top 5 census tracts in Caddo Parish by poverty rate?"

print(f"Testing: {query}\n")
result = run_query(query)
print_result(result)

print("\nExpected top 5 (from Census API):")
print("  1. Census Tract 253: 70.62%")
print("  2. Census Tract 238.02: 66.44%")
print("  3. Census Tract 233: 54.31%")
print("  4. Census Tract 211: 53.97%")
print("  5. Census Tract 206: 51.82%")
