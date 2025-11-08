"""Test GUI imports and function calls."""
import sys
from pathlib import Path

# Mimic GUI imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "single_agent"))

print("Testing GUI imports...")
print("=" * 60)

try:
    print("\n1. Importing single_agent.mvp...")
    from single_agent.mvp import run_query as run_single_agent_query
    print("✅ Import successful")
    
    print("\n2. Testing function call...")
    query = "What are the top 5 census tracts in Orleans Parish by median income?"
    result = run_single_agent_query(query, return_debug_info=True)
    print(f"✅ Query successful - got {len(result)} results")
    
    print("\n3. Checking result attributes...")
    print(f"   - label: {result.attrs.get('label', 'Not found')}")
    print(f"   - debug_info: {'Present' if result.attrs.get('debug_info') else 'Not found'}")
    print(f"   - columns: {list(result.columns)}")
    
    print("\n✅ All tests passed!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
