# BatchRX Report Comparison Analysis

## Test Results Summary

**Date:** 2026-01-06  
**Test Run ID:** 20260106_151754_760  
**Date Range:** 2025-05-01 to 2025-12-01

### ✅ Successes
1. **Report Generation:** Successfully generated report with 54 rows (matches BatchRX)
2. **Row Count:** Perfect match (54 rows in both)
3. **NDC Matching:** All 54 NDCs match between generated and BatchRX reports
4. **Core Columns:** All base columns present (NDC, DRUG NAME, RANK, PKG SIZE, etc.)

### ⚠️ Issues Found

#### 1. Missing Supplier Columns (2 columns)
- **Missing:** `ORDERED\nKINRAY-O`, `ORDERED\nAKRON GENERICS-O`
- **Root Cause:** 
  - KINRAY file has dates `12/15/2024` (before date range `05/01/2025 to 12/01/2025`)
  - After date filtering, KINRAY data is excluded
  - AKRON GENERICS has 0 matching NDCs with inventory report
- **BatchRX Behavior:** Shows these columns even with all zeros
- **Fix Required:** Include all suppliers from original upload (before date filtering), show columns with zeros if no data

#### 2. COST Value Mismatches (51 rows)
- **Issue:** COST values are whole numbers (e.g., 983.0, 1044.0) instead of decimals (983.07, 1044.03)
- **Root Cause:** 
  - Supplier files don't contain cost/price columns
  - Code falls back to AMOUNT for COST
  - AMOUNT is rounded to whole numbers, so COST becomes whole numbers
- **BatchRX Behavior:** COST has 2 decimal places (e.g., 1519.45, 983.07)
- **Fix Status:** ✅ Code updated to round COST to 2 decimals, but still using AMOUNT as source
- **Additional Fix Needed:** Need actual cost data from supplier files or separate cost file

#### 3. AMOUNT Value Mismatches (18 rows)
- **Issue:** AMOUNT values differ by ±1 in 18 rows
- **Examples:**
  - 00536-1294-97: Generated=12, BatchRX=11
  - 33342-0075-10: Generated=18, BatchRX=17
- **Root Cause:** 
  - Rounding differences in insurance payment aggregation
  - Possible floating-point precision issues
  - May be due to how secondary insurance is handled
- **Fix Required:** Review insurance payment aggregation logic, ensure exact matching

#### 4. RANK Mismatches (28 rows)
- **Issue:** RANK values differ in 28 rows
- **Examples:**
  - 00904-7591-80: Generated=110, BatchRX=52 (large difference)
  - 16103-0361-11: Generated=45, BatchRX=47
- **Root Cause:** 
  - RANK is based on AMOUNT (descending), then COST (descending) as tiebreaker
  - Since AMOUNT and COST values differ, RANK will differ
  - Large differences (like 110 vs 52) suggest AMOUNT calculation issues
- **Fix Required:** Fix AMOUNT calculation first, then RANK will align

## Detailed Analysis

### Supplier Column Issue
**Current Behavior:**
- Only suppliers with data for medicines that have sales (after date filtering) are included
- KINRAY excluded because all its data is before the date range
- AKRON GENERICS excluded because no matching NDCs

**BatchRX Behavior:**
- Shows ALL suppliers that were uploaded, even if they have no data in the date range
- Columns show zeros for suppliers with no matching data

**Recommended Fix:**
1. Track all supplier names from original upload (before date filtering)
2. Create columns for all suppliers
3. Populate with data only for medicines with sales (may be zeros)

### COST Calculation Issue
**Current Implementation:**
```python
# Falls back to AMOUNT if no cost data in ordered_df
if "AMOUNT" in report_df.columns:
    report_df["COST"] = report_df["AMOUNT"]
```

**Problem:**
- Supplier files don't have cost/price columns
- No separate cost file provided
- COST = AMOUNT (rounded to whole numbers)

**BatchRX Behavior:**
- COST values have 2 decimal places
- COST ≠ AMOUNT in many cases (e.g., ELIQUIS: AMOUNT=1647, COST=1519.45)
- Suggests BatchRX has access to actual cost data

**Recommended Fix:**
1. ✅ Round COST to 2 decimals (already fixed)
2. ⚠️ Need actual cost data source (supplier files with cost columns, or separate cost file)
3. If cost data unavailable, use AMOUNT but ensure it has 2 decimal places

### AMOUNT Calculation Issue
**Current Implementation:**
```python
primary_paid = insurance_agg["primary_insurance_paid"].fillna(0)
secondary_paid = insurance_agg.get("secondary_insurance_paid", ...).fillna(0)
total_amount = primary_paid + secondary_paid
insurance_agg["AMOUNT"] = total_amount.round(0).astype(int)
```

**Problem:**
- Rounding to whole numbers may cause ±1 differences
- Possible issues with how secondary insurance is aggregated
- Floating-point precision in aggregation

**Recommended Fix:**
1. Review insurance payment aggregation logic
2. Ensure exact matching of BatchRX's aggregation method
3. Check if BatchRX uses different rounding (floor vs round vs ceil)

### RANK Calculation Issue
**Current Implementation:**
```python
report_df = report_df.sort_values(["AMOUNT", "COST"], ascending=[False, False])
report_df["RANK"] = range(1, len(report_df) + 1)
```

**Problem:**
- RANK depends on AMOUNT and COST values
- Since these values differ, RANK will differ
- Large differences (110 vs 52) suggest AMOUNT calculation is significantly off for some rows

**Recommended Fix:**
1. Fix AMOUNT calculation first
2. Fix COST calculation
3. RANK will automatically align once AMOUNT and COST are correct

## Priority Fixes

### High Priority
1. ✅ **COST Decimal Precision:** Fixed (rounds to 2 decimals)
2. ⚠️ **AMOUNT Calculation:** Review aggregation logic, fix ±1 differences
3. ⚠️ **Supplier Columns:** Include all suppliers even if filtered out by date

### Medium Priority
4. **RANK Calculation:** Will fix automatically once AMOUNT/COST are fixed
5. **Cost Data Source:** Need to identify where BatchRX gets cost data from

### Low Priority
6. **Documentation:** Update code comments to explain BatchRX matching logic

## Next Steps

1. **Investigate AMOUNT Calculation:**
   - Compare insurance payment aggregation row-by-row
   - Check if BatchRX uses different rounding method
   - Verify secondary insurance handling

2. **Supplier Column Fix:**
   - Modify `create_batchrx_report` to accept list of all suppliers
   - Create columns for all suppliers, populate with zeros if no data

3. **Cost Data Source:**
   - Check if BatchRX uses a separate cost file
   - Check if supplier files should have cost columns
   - If unavailable, document that COST = AMOUNT is expected

4. **Re-test:**
   - After fixes, re-run full test
   - Compare all values row-by-row
   - Verify RANK matches

## Files Modified

1. `src/reporting/batchrx_format.py`:
   - ✅ Added `.round(2)` to COST calculation (line 290)

## Files to Modify (Next)

1. `src/reporting/batchrx_format.py`:
   - Fix AMOUNT calculation precision
   - Add logic to include all suppliers

2. `src/web/app.py`:
   - Track all suppliers before date filtering
   - Pass supplier list to `create_batchrx_report`

