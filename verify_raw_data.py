"""
Simple script to get raw Census data for verification.
Run this to see the actual Census API responses.
"""
import requests
import pandas as pd

print("=" * 80)
print("RAW CENSUS DATA FOR VERIFICATION")
print("=" * 80)

# Configuration
BASE_URL = "https://api.census.gov/data/2023/acs/acs5"
ORLEANS_FIPS = "071"

print("\n1. Total Population (B01003_001E) - Orleans Parish")
print("-" * 80)

params = {
    "get": "NAME,B01003_001E",
    "for": "tract:*",
    "in": "state:22 county:071"
}

response = requests.get(BASE_URL, params=params, timeout=30)
data = response.json()
df = pd.DataFrame(data[1:], columns=data[0])
df["B01003_001E"] = pd.to_numeric(df["B01003_001E"], errors="coerce")

print(f"Total tracts retrieved: {len(df)}")
print(f"\nHighest population tracts:")
print(df.nlargest(5, "B01003_001E")[["NAME", "B01003_001E"]])

# Check specific tract 76.04
tract_7604 = df[df["tract"] == "007604"]
if len(tract_7604) > 0:
    print(f"\n*** Tract 76.04 (GEOID: 22071007604) ***")
    print(f"Population: {tract_7604['B01003_001E'].values[0]:,.0f}")

print("\n\n2. Median Household Income (B19013_001E) - Orleans Parish")
print("-" * 80)

params2 = {
    "get": "NAME,B19013_001E",
    "for": "tract:*",
    "in": "state:22 county:071"
}

response2 = requests.get(BASE_URL, params=params2, timeout=30)
data2 = response2.json()
df2 = pd.DataFrame(data2[1:], columns=data2[0])
df2["B19013_001E"] = pd.to_numeric(df2["B19013_001E"], errors="coerce")

print(f"\nHighest income tracts:")
print(df2.nlargest(5, "B19013_001E")[["NAME", "B19013_001E"]])

print(f"\nLowest income tracts:")
print(df2.nsmallest(5, "B19013_001E")[["NAME", "B19013_001E"]])

print("\n\n3. Poverty Data (B17001_002E, B01001_001E) - Orleans Parish")
print("-" * 80)

params3 = {
    "get": "NAME,B17001_002E,B01001_001E",
    "for": "tract:*",
    "in": "state:22 county:071"
}

response3 = requests.get(BASE_URL, params=params3, timeout=30)
data3 = response3.json()
df3 = pd.DataFrame(data3[1:], columns=data3[0])
df3["B17001_002E"] = pd.to_numeric(df3["B17001_002E"], errors="coerce")
df3["B01001_001E"] = pd.to_numeric(df3["B01001_001E"], errors="coerce")

# Calculate poverty rate
df3["poverty_rate"] = (df3["B17001_002E"] / df3["B01001_001E"]) * 100

print(f"\nHighest poverty rate tracts:")
df3_high = df3.nlargest(5, "poverty_rate")[["NAME", "B17001_002E", "B01001_001E", "poverty_rate"]]
df3_high["poverty_rate"] = df3_high["poverty_rate"].map(lambda x: f"{x:.2f}%")
print(df3_high)

# Count tracts over 40%
high_poverty = df3[df3["poverty_rate"] >= 40]
print(f"\n*** Tracts with poverty rate >= 40%: {len(high_poverty)} ***")

print("\n\n4. African American Population (B02001_003E, B02001_001E) - Statewide")
print("-" * 80)

params4 = {
    "get": "NAME,B02001_003E,B02001_001E",
    "for": "tract:*",
    "in": "state:22"
}

response4 = requests.get(BASE_URL, params=params4, timeout=30)
data4 = response4.json()
df4 = pd.DataFrame(data4[1:], columns=data4[0])
df4["B02001_003E"] = pd.to_numeric(df4["B02001_003E"], errors="coerce")
df4["B02001_001E"] = pd.to_numeric(df4["B02001_001E"], errors="coerce")

# Calculate share
df4["aa_share"] = (df4["B02001_003E"] / df4["B02001_001E"]) * 100

# Count tracts with >= 20%
aa_20plus = df4[df4["aa_share"] >= 20]
print(f"Tracts with African American share >= 20%: {len(aa_20plus)}")

# Count tracts with >= 50%
aa_50plus = df4[df4["aa_share"] >= 50]
print(f"Tracts with African American share >= 50%: {len(aa_50plus)}")

print("\n" + "=" * 80)
print("VERIFICATION CHECKLIST")
print("=" * 80)
print("""
Compare these raw Census API values with our app results:

✓ Total tracts in Orleans Parish should match
✓ Tract 76.04 population should match
✓ Top 5 highest income tracts should match (order & values)
✓ Number of tracts with poverty >= 40% should match (26 tracts)
✓ Number of tracts with AA share >= 20% should match (774 tracts)
✓ Number of tracts with AA share >= 50% should match (375 tracts)
""")
