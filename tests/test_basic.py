"""
Basic tests without Ollama to verify Census API and data fetching works.
"""
from resolver import resolve_measure, normalize_measure
from acs_tools import fetch_acs_tracts_LA, fetch_tiger_tract_areas_LA

def test_resolver():
    print("Testing resolver...")
    
    # Test normalize
    assert normalize_measure("median income") == "median household income"
    assert normalize_measure("pop density") == "population density"
    print("  ✓ Measure normalization works")
    
    # Test derived metric
    result = resolve_measure("population density")
    assert result[0]["is_derived"] == True
    assert "B01003_001E" in result[0]["variables"]
    print("  ✓ Derived metric resolution works")
    
    # Test Census variable resolution
    result = resolve_measure("median household income")
    print(f"  ✓ Resolved 'median household income' to: {result[0]['variable_id']}")

def test_acs_fetch():
    print("\nTesting ACS data fetch...")
    
    # Fetch a simple variable for Orleans Parish
    df = fetch_acs_tracts_LA(
        year=2023,
        var_ids=["B01003_001E"],  # Total population
        county_fips="071"  # Orleans Parish
    )
    
    print(f"  ✓ Fetched {len(df)} tracts for Orleans Parish")
    print(f"  ✓ Columns: {', '.join(df.columns)}")
    assert "GEOID" in df.columns
    assert "B01003_001E" in df.columns
    assert len(df) > 0

def test_tiger_areas():
    print("\nTesting TIGER tract areas...")
    
    df = fetch_tiger_tract_areas_LA(vintage=2024)
    
    print(f"  ✓ Fetched areas for {len(df)} tracts")
    assert "GEOID" in df.columns
    assert "area_km2" in df.columns
    assert len(df) > 0
    
    # Check some areas are reasonable (LA tracts range from ~0.1 to ~1000 km²)
    assert df["area_km2"].min() > 0
    assert df["area_km2"].max() < 10000
    print(f"  ✓ Area range: {df['area_km2'].min():.2f} - {df['area_km2'].max():.2f} km²")

if __name__ == "__main__":
    print("=" * 70)
    print("Basic Functionality Tests (No Ollama Required)")
    print("=" * 70)
    
    try:
        test_resolver()
        test_acs_fetch()
        test_tiger_areas()
        
        print("\n" + "=" * 70)
        print("✅ All tests passed!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Make sure Ollama is running: ollama serve")
        print("2. Pull the model: ollama pull phi3:mini")
        print("3. Run the app: python mvp.py")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
