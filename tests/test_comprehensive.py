"""Comprehensive test of all query types."""
from mvp import run_query, print_result

print("=" * 80)
print("COMPREHENSIVE QUERY TESTS")
print("=" * 80)

tests = [
    ("Top query (non-percentage)", "What tract has the highest median income in New Orleans?", 
     lambda r: len(r) == 1),
    
    ("Filter with percentage", "Give me all tracts with poverty rate over 40 percent in New Orleans",
     lambda r: len(r) > 0 and (r['value'] >= 40).all()),
    
    ("Range with percentage", "Show me tracts with poverty rate between 15% and 25% in Baton Rouge",
     lambda r: len(r) > 0 and ((r['value'] >= 15) & (r['value'] <= 25)).all()),
    
    ("Top with derived metric", "Show me the top 3 highest population density tracts",
     lambda r: len(r) == 3),
    
    ("Filter with percentage (African American)", "Give me tracts with 50% or more African Americans",
     lambda r: len(r) > 0 and (r['value'] >= 50).all()),
]

passed = 0
failed = 0

for i, (name, query, validator) in enumerate(tests, 1):
    print(f"\n{'='*80}")
    print(f"Test {i}: {name}")
    print(f"Query: {query}")
    print(f"{'='*80}")
    
    try:
        result = run_query(query)
        if validator(result):
            print(f"[PASS] - {len(result)} results, validation successful")
            passed += 1
        else:
            print(f"[FAIL] - Validation failed")
            print(f"   Results: {len(result)} tracts")
            if len(result) > 0:
                print(f"   Value range: {result['value'].min():.2f} - {result['value'].max():.2f}")
            failed += 1
    except Exception as e:
        print(f"[FAIL] - Exception: {e}")
        failed += 1

print(f"\n{'='*80}")
print(f"SUMMARY: {passed}/{len(tests)} tests passed")
print(f"{'='*80}")
