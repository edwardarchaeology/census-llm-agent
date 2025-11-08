"""
Side-by-side comparison of app results vs raw Census data.
"""
from mvp import run_query
import requests
import pandas as pd

print("=" * 80)
print("SIDE-BY-SIDE VERIFICATION")
print("=" * 80)

# Test 1: Poverty rate filter
print("\n1. POVERTY RATE >= 40% IN NEW ORLEANS")
print("-" * 80)

app_result = run_query("Give me all tracts with poverty rate over 40 percent in New Orleans")
print(f"\n[APP] Result: {len(app_result)} tracts")
print(f"  Min value: {app_result['value'].min():.2f}%")
print(f"  Max value: {app_result['value'].max():.2f}%")

# Raw Census data
url = "https://api.census.gov/data/2023/acs/acs5"
params = {
    "get": "NAME,B17001_002E,B01001_001E",
    "for": "tract:*",
    "in": "state:22 county:071"
}
response = requests.get(url, params=params, timeout=30)
data = response.json()
df = pd.DataFrame(data[1:], columns=data[0])
df["B17001_002E"] = pd.to_numeric(df["B17001_002E"], errors="coerce")
df["B01001_001E"] = pd.to_numeric(df["B01001_001E"], errors="coerce")
df["poverty_rate"] = (df["B17001_002E"] / df["B01001_001E"]) * 100
raw_result = df[df["poverty_rate"] >= 40]

print(f"\n[RAW] Census API: {len(raw_result)} tracts")
print(f"  Min value: {raw_result['poverty_rate'].min():.2f}%")
print(f"  Max value: {raw_result['poverty_rate'].max():.2f}%")

print(f"\n*** {'MATCH!' if len(app_result) == len(raw_result) else 'MISMATCH!'} ***")

# Test 2: African American share
print("\n\n2. AFRICAN AMERICAN SHARE >= 50% (STATEWIDE)")
print("-" * 80)

app_result2 = run_query("Give me tracts with 50% or more African Americans")
print(f"\n[APP] Result: {len(app_result2)} tracts")
print(f"  Min value: {app_result2['value'].min():.2f}%")

# Raw Census data
params2 = {
    "get": "NAME,B02001_003E,B02001_001E",
    "for": "tract:*",
    "in": "state:22"
}
response2 = requests.get(url, params=params2, timeout=30)
data2 = response2.json()
df2 = pd.DataFrame(data2[1:], columns=data2[0])
df2["B02001_003E"] = pd.to_numeric(df2["B02001_003E"], errors="coerce")
df2["B02001_001E"] = pd.to_numeric(df2["B02001_001E"], errors="coerce")
df2["aa_share"] = (df2["B02001_003E"] / df2["B02001_001E"]) * 100
raw_result2 = df2[df2["aa_share"] >= 50]

print(f"\n[RAW] Census API: {len(raw_result2)} tracts")
print(f"  Min value: {raw_result2['aa_share'].min():.2f}%")

print(f"\n*** {'MATCH!' if len(app_result2) == len(raw_result2) else 'MISMATCH!'} ***")

# Test 3: Check specific GEOIDs match
print("\n\n3. GEOID VALIDATION (Poverty >= 40% sample)")
print("-" * 80)

app_geoids = set(app_result['GEOID'].values)
raw_geoids = set(df[df["poverty_rate"] >= 40]['state'].values + 
                 df[df["poverty_rate"] >= 40]['county'].values + 
                 df[df["poverty_rate"] >= 40]['tract'].values)

sample_geoids = list(app_geoids)[:5]
print("\nSample GEOIDs from app:")
for geoid in sample_geoids:
    in_raw = geoid in raw_geoids
    print(f"  {geoid} {'[OK]' if in_raw else '[MISSING]'}")

matches = len(app_geoids.intersection(raw_geoids))
print(f"\nMatching GEOIDs: {matches}/{len(app_geoids)}")
print(f"*** {'ALL MATCH!' if matches == len(app_geoids) else 'SOME MISSING!'} ***")

# Test 4: Value comparison for specific tracts
print("\n\n4. VALUE COMPARISON (Top 5 Poverty Rate Tracts)")
print("-" * 80)

app_top5 = app_result.nlargest(5, 'value')[['GEOID', 'tract_name', 'value']].copy()
app_top5['value'] = app_top5['value'].round(2)

print("\nApp values:")
for _, row in app_top5.iterrows():
    # Find matching tract in raw data
    geoid = row['GEOID']
    state, county, tract = geoid[0:2], geoid[2:5], geoid[5:]
    raw_tract = df[(df['state'] == state) & (df['county'] == county) & (df['tract'] == tract)]
    
    if len(raw_tract) > 0:
        raw_value = raw_tract['poverty_rate'].values[0]
        diff = abs(row['value'] - raw_value)
        status = '[OK]' if diff < 0.01 else '[DIFF]'
        print(f"  {geoid}: App={row['value']:.2f}% | Raw={raw_value:.2f}% | Diff={diff:.3f} {status}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("""
If all tests show *** MATCH! ***, the app is correctly:
- Fetching the same data from Census API
- Applying filters correctly (percentage scaling works!)
- Calculating derived metrics accurately
- Returning the exact same tracts as raw queries

Any [MISSING] or [DIFF] or *** MISMATCH! *** indicates a problem to investigate.
""")
