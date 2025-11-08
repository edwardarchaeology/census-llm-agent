"""
Fetch median household income for all census tracts in Orleans Parish (New Orleans)
Sorted by descending income.
"""
import requests
import pandas as pd

# Census API parameters
BASE_URL = "https://api.census.gov/data/2023/acs/acs5"
VARIABLE = "B19013_001E"  # Median Household Income
STATE = "22"  # Louisiana
COUNTY = "071"  # Orleans Parish (New Orleans)

print("Fetching median household income data for Orleans Parish (New Orleans)...")
print(f"Using variable: {VARIABLE} (Median Household Income in past 12 months)\n")

# Make API request
params = {
    "get": f"NAME,{VARIABLE}",
    "for": "tract:*",
    "in": f"state:{STATE} county:{COUNTY}"
}

response = requests.get(BASE_URL, params=params, timeout=30)

if response.status_code != 200:
    print(f"Error: Census API returned status code {response.status_code}")
    print(f"Response: {response.text}")
    exit(1)

# Parse response
data = response.json()
df = pd.DataFrame(data[1:], columns=data[0])

# Convert income to numeric
df[VARIABLE] = pd.to_numeric(df[VARIABLE], errors='coerce')

# Create GEOID
df['GEOID'] = df['state'] + df['county'] + df['tract']

# Rename columns for clarity
df = df.rename(columns={
    'NAME': 'Tract Name',
    VARIABLE: 'Median Household Income'
})

# Sort by income (descending)
df_sorted = df[['GEOID', 'Tract Name', 'Median Household Income']].sort_values(
    'Median Household Income', 
    ascending=False
)

# Display results
print(f"{'='*80}")
print(f"Median Household Income by Census Tract - Orleans Parish, Louisiana")
print(f"{'='*80}")
print(f"\nTotal tracts: {len(df_sorted)}")
print(f"\nTop 20 highest income tracts:")
print(f"{'-'*80}")

for idx, row in df_sorted.head(20).iterrows():
    income = row['Median Household Income']
    if pd.isna(income):
        income_str = "N/A"
    else:
        income_str = f"${income:,.0f}"
    
    print(f"{row['GEOID']}\t{row['Tract Name']:<50} {income_str:>15}")

print(f"\n{'-'*80}")
print(f"\nBottom 20 lowest income tracts:")
print(f"{'-'*80}")

for idx, row in df_sorted.tail(20).iterrows():
    income = row['Median Household Income']
    if pd.isna(income):
        income_str = "N/A"
    else:
        income_str = f"${income:,.0f}"
    
    print(f"{row['GEOID']}\t{row['Tract Name']:<50} {income_str:>15}")

# Summary statistics
print(f"\n{'='*80}")
print(f"Summary Statistics:")
print(f"{'='*80}")

valid_incomes = df_sorted['Median Household Income'].dropna()

if len(valid_incomes) > 0:
    print(f"Highest Income:  ${valid_incomes.max():,.0f}")
    print(f"Lowest Income:   ${valid_incomes.min():,.0f}")
    print(f"Median Income:   ${valid_incomes.median():,.0f}")
    print(f"Average Income:  ${valid_incomes.mean():,.0f}")
    print(f"Std Deviation:   ${valid_incomes.std():,.0f}")
    print(f"Tracts with data: {len(valid_incomes)} of {len(df_sorted)}")

# Save to CSV
output_file = "orleans_parish_median_income.csv"
df_sorted.to_csv(output_file, index=False)
print(f"\n✅ Full data saved to: {output_file}")
