"""Test to compare different income variables for Orleans Parish"""
import requests
import pandas as pd

# Test both variables
variables_to_test = {
    "B19013_001E": "Median Household Income",
    "B19202_001E": "Median Nonfamily Household Income"
}

for var_id, var_name in variables_to_test.items():
    print(f"\n{'='*60}")
    print(f"Testing: {var_name} ({var_id})")
    print('='*60)
    
    url = f"https://api.census.gov/data/2023/acs/acs5"
    params = {
        "get": f"NAME,{var_id}",
        "for": "tract:*",
        "in": "state:22 county:071",  # Orleans Parish
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data[1:], columns=data[0])
        df[var_id] = pd.to_numeric(df[var_id], errors='coerce')
        
        # Get top 5 by value
        df_sorted = df.sort_values(var_id, ascending=False).head(10)
        
        print(f"\nTop 10 tracts:")
        for idx, row in df_sorted.iterrows():
            print(f"  {row['NAME']}: ${row[var_id]:,.0f}")
        
        # Check for 250001 values
        count_250001 = (df[var_id] == 250001).sum()
        print(f"\nNumber of tracts with value 250001: {count_250001}")
        print(f"Total tracts: {len(df)}")
    else:
        print(f"Error: {response.status_code}")
