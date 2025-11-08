"""
Verify Caddo Parish poverty rates - check actual top values.
"""
import requests
import pandas as pd

# Fetch raw data from Census API for Caddo Parish (017)
url = "https://api.census.gov/data/2023/acs/acs5"

params = {
    "get": "NAME,B17001_001E,B17001_002E",  # Total population, population below poverty
    "for": "tract:*",
    "in": "state:22 county:017",  # Louisiana, Caddo Parish
}

print("Fetching Caddo Parish poverty data from Census API...")
response = requests.get(url, params=params)
response.raise_for_status()

data = response.json()
header = data[0]
rows = data[1:]

df = pd.DataFrame(rows, columns=header)

# Calculate poverty rate
df['B17001_001E'] = pd.to_numeric(df['B17001_001E'], errors='coerce')
df['B17001_002E'] = pd.to_numeric(df['B17001_002E'], errors='coerce')

# Filter out tracts with 0 or missing population
df = df[(df['B17001_001E'] > 0) & (df['B17001_002E'].notna())]

df['poverty_rate'] = (df['B17001_002E'] / df['B17001_001E']) * 100

# Create GEOID
df['GEOID'] = df['state'] + df['county'] + df['tract']

# Sort by poverty rate descending (HIGHEST first)
df_sorted = df.sort_values('poverty_rate', ascending=False)

print("\n" + "=" * 80)
print("TOP 10 HIGHEST POVERTY RATES IN CADDO PARISH")
print("=" * 80)
print(df_sorted[['GEOID', 'NAME', 'poverty_rate']].head(10).to_string(index=False))

print("\n" + "=" * 80)
print("BOTTOM 10 LOWEST POVERTY RATES IN CADDO PARISH")
print("=" * 80)
print(df_sorted[['GEOID', 'NAME', 'poverty_rate']].tail(10).to_string(index=False))
