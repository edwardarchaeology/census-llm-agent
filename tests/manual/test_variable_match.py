"""Test variable matching for median income"""
import sys
sys.path.insert(0, 'src')
sys.path.insert(0, 'src/single_agent')

from resolver import resolve_measure

print("Testing: 'median household income'")
results = resolve_measure('median household income', top_n=5)

for i, r in enumerate(results, 1):
    print(f"\n{i}. {r['variable_id']}")
    print(f"   Label: {r['label']}")
    print(f"   Description: {r.get('description', 'N/A')}")
    print(f"   Score: {r['score']:.1f}")
