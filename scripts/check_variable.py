"""Check which variable is selected for median income"""
import sys
sys.path.insert(0, 'src')
sys.path.insert(0, 'src/single_agent')

from resolver import resolve_measure

result = resolve_measure('median income', top_n=1)[0]
print(f'Variable: {result["variable_id"]}')
print(f'Label: {result["label"]}')
print(f'Description: {result.get("description", "N/A")}')
