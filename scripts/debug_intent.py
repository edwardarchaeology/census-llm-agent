"""
Debug intent extraction for Caddo poverty query.
"""
from intent import extract_intent

query = "What are the top 5 census tracts in Caddo Parish by poverty rate?"

print(f"Query: {query}")
print("\nExtracted Intent:")

intent = extract_intent(query)
print(f"  Task: {intent.task}")
print(f"  Measure: {intent.measure}")
print(f"  Limit: {intent.limit}")
print(f"  Sort: {intent.sort}")
print(f"  County FIPS: {intent.geography.county_fips}")

print("\n" + "="*80)
print("ISSUE IDENTIFIED:")
print("="*80)
print(f"The LLM extracted task='{intent.task}' with sort='{intent.sort}'")
print(f"For 'top by poverty rate', we want HIGHEST poverty (sort='desc')")
print(f"But '{intent.task}' task gets sort='{intent.sort}' which returns LOWEST values")
