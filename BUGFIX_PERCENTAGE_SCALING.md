# Bug Fix: Percentage Value Scaling

## Problem

When querying percentage-based metrics (poverty rate, African American share), the filter was not working correctly.

### Example Issue

Query: "Give me all tracts with poverty rate over 40 percent in New Orleans"

**Expected:** Only tracts with poverty rate ≥ 40%
**Actual:** All 180 tracts returned, including many with values < 40%

## Root Cause

1. **Derived metrics** calculate percentages on a 0-100 scale:

   - `poverty_rate = (below_poverty / total_pop) * 100`
   - Returns values like 87.96, 66.67, 40.08, etc.

2. **Intent normalization** converts "40 percent" to decimal:

   - "40%" → 0.4 (on 0-1 scale)

3. **Filter comparison** was broken:
   - Comparing 0.4 against 87.96 → All values pass the ≥ filter!

## Solution

Added percentage value scaling in `mvp.py`:

```python
# Detect if metric is percentage-based (label contains %)
is_percentage_metric = "%" in label

# Scale intent values if needed (0-1 scale → 0-100 scale)
if is_percentage_metric and intent.task in ["filter", "range"]:
    if intent.value is not None and intent.value < 1:
        intent.value = intent.value * 100
    if intent.range_min is not None and intent.range_min < 1:
        intent.range_min = intent.range_min * 100
    if intent.range_max is not None and intent.range_max < 1:
        intent.range_max = intent.range_max * 100
```

## Verification

All tests now pass:

✅ **Filter with percentage**: "poverty rate over 40 percent" → 26 tracts, all ≥ 40%
✅ **Range with percentage**: "poverty rate between 15% and 25%" → 18 tracts, all in [15, 25]
✅ **African American filter**: "50% or more African Americans" → 375 tracts, all ≥ 50%
✅ **Top/bottom queries**: Still work correctly (no scaling needed)
✅ **Non-percentage metrics**: Unaffected (e.g., median income, population density)

## Impact

This fix ensures that percentage-based filters and ranges work correctly for:

- Poverty rate (%)
- African American population share (%)
- Any future percentage-based derived metrics

Non-percentage metrics (income, population density) are unaffected.
