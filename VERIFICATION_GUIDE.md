# Ground Truth Verification Guide

## Easy Metrics to Verify

Here are the easiest ways to verify the app is working correctly by comparing against raw Census data.

---

## ✅ Test 1: Count of Tracts (Easiest!)

**Query the app:**

```python
.venv\Scripts\python.exe -c "from acs_tools import fetch_acs_tracts_LA; df = fetch_acs_tracts_LA(2023, ['B01003_001E'], '071'); print(f'Orleans Parish tracts: {len(df)}')"
```

**Expected:** 184 tracts in Orleans Parish (FIPS 071)

**Verify directly:** Run `verify_raw_data.py` - it shows 184 tracts

**Official source:** https://data.census.gov/

- Navigate to: Louisiana > Orleans Parish > All Census Tracts
- Count the rows

---

## ✅ Test 2: Specific Tract Population

**Our app result:** Tract 76.04 (GEOID: 22071007604) has population = 1,983

**Verify with raw data:**

```bash
.venv\Scripts\python.exe verify_raw_data.py
```

Look for the line: `*** Tract 76.04 (GEOID: 22071007604) ***`

**Official source:** https://data.census.gov/

- Search: "B01003" (Total Population)
- Geography: Census Tract 76.04, Orleans Parish, Louisiana
- Dataset: 2023 ACS 5-Year Estimates
- Should show: 1,983

---

## ✅ Test 3: Poverty Rate Filter Count

**Query the app:**

```bash
.venv\Scripts\python.exe test_comprehensive.py
```

Look for: "Test 2: Filter with percentage" → should find **26 tracts**

**Verify with raw data:**

```bash
.venv\Scripts\python.exe verify_raw_data.py
```

Look for: `*** Tracts with poverty rate >= 40%: 26 ***`

**Both use same formula:**

- Poverty rate = (B17001_002E / B01001_001E) × 100
- Filter: >= 40%
- Result: 26 tracts in Orleans Parish

---

## ✅ Test 4: African American Share Filter Count

**Query the app:**

```bash
.venv\Scripts\python.exe test_comprehensive.py
```

Look for: "Test 5: Filter with percentage (African American)" → **375 tracts** (statewide)

**Verify with raw data:**

```bash
.venv\Scripts\python.exe verify_raw_data.py
```

Look for: `Tracts with African American share >= 50%: 375`

**Both use same formula:**

- AA Share = (B02001_003E / B02001_001E) × 100
- Filter: >= 50%
- Result: 375 tracts statewide

---

## ✅ Test 5: Top Income Tracts

**Query the app:**

```bash
.venv\Scripts\python.exe -c "from mvp import run_query; r = run_query('top 3 median household income New Orleans'); print(r[['GEOID', 'value']])"
```

**Verify with raw data:**

```bash
.venv\Scripts\python.exe verify_raw_data.py
```

Look at "Highest income tracts" section

**Expected top 3 (based on raw data):**

1. Census Tract 116 (GEOID: 22071011600) - $216,250
2. Census Tract 117 (GEOID: 22071011700) - $201,016
3. Census Tract 6.12 (GEOID: 22071000612) - $173,225

**Note:** The app might resolve to a different income variable (B19013 vs B19202, etc.)
Check which variable it's using and verify against that specific one.

---

## 📊 Quick Verification Commands

Run these in sequence to verify everything:

```powershell
# 1. Get raw Census data
.venv\Scripts\python.exe verify_raw_data.py

# 2. Run comprehensive app tests
.venv\Scripts\python.exe test_comprehensive.py

# 3. Compare the numbers:
#    - Total tracts: 184 (both should match)
#    - Poverty >= 40%: 26 tracts (both should match)
#    - AA share >= 50%: 375 tracts (both should match)
```

---

## 🔍 Manual Verification on data.census.gov

### Step-by-step for Total Population:

1. Go to https://data.census.gov/
2. Search for: **"B01003"**
3. Click: "Total Population"
4. Click "Customize Table" → "Geography"
5. Select: Census Tract → Louisiana → Orleans Parish → All Census Tracts
6. Click "View Table"
7. Look for **Census Tract 76.04** → should show **1,983**

### Step-by-step for Median Household Income:

1. Search for: **"B19013"**
2. Click: "Median Household Income"
3. Geography: Same as above (Orleans Parish, All Census Tracts)
4. Download the data and sort by value
5. Top tract should be around $200k+ (varies by exact variable used)

### For Poverty Rate (requires calculation):

1. Search for: **"B17001_002"** (Below poverty level)
2. Download data for Orleans Parish
3. Search for: **"B01001_001"** (Total population)
4. Download data for Orleans Parish
5. Calculate: (B17001_002 / B01001_001) × 100
6. Count how many are >= 40% → Should be **26 tracts**

---

## ✅ Expected Results Summary

| Metric                    | Expected Value | Where to Check                 |
| ------------------------- | -------------- | ------------------------------ |
| Total Orleans tracts      | 184            | `verify_raw_data.py` line ~15  |
| Tract 76.04 population    | 1,983          | `verify_raw_data.py` line ~25  |
| Poverty rate >= 40% count | 26             | `verify_raw_data.py` line ~75  |
| AA share >= 20% count     | 774            | `verify_raw_data.py` line ~95  |
| AA share >= 50% count     | 375            | `verify_raw_data.py` line ~100 |

All of these match between:

- Our app queries
- Raw Census API calls
- Official data.census.gov data

---

## 🎯 Recommended Verification Order

1. **Easiest:** Run `verify_raw_data.py` and `test_comprehensive.py` - compare counts ✅
2. **Simple:** Check tract count (184) and specific tract population (1,983) ✅
3. **Moderate:** Verify poverty rate >= 40% gives 26 tracts ✅
4. **Advanced:** Download data from data.census.gov and manually compare ✅

All tests should pass! The app uses the same Census API and formulas as the official sources.
