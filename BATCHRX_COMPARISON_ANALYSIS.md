# BatchRx vs DawaiRx Comparison Analysis

## STEP 1: Deep File Understanding - COMPLETED

### Row Counts
- ✅ **MATCH**: Both have 54 rows

### Column Schema
- ✅ **MATCH**: Both have 27 columns
- ❌ **MISMATCH**: Column name differences:
  1. Insurance: `SS&C (FORMERLY HUMANA, ARGUS, AND DST)` vs `SS&C (FORMERLY HUMANA ARGUS AND OPTUMRX)`
  2. Suppliers: `SMITH DRUGS` vs `SUPPLIER SMITH DRUGS`
  3. Suppliers: `LEGACY HEALTH` vs `SUPPLIER LEGACY HEALTH`

### Key Metrics Comparison
- ❌ **TOTAL ORDERED-O**: BatchRx=361, DawaiRx=89,782 (MASSIVE DIFFERENCE)
- ✅ **TOTAL BILLED-B**: BatchRx=47.17, DawaiRx=47.17 (MATCH)
- ❌ **AMOUNT**: BatchRx=6,723, DawaiRx=6,741 (Diff=-18)
- ❌ **COST**: BatchRx=6,455.86, DawaiRx=6,741 (Diff=-285.14)

## STEP 2: Categorized Mismatches

### Category 1: Filtering Logic Difference (CRITICAL)
**Issue**: BatchRx only includes TOTAL ORDERED-O for medicines that were BILLED (sold).
- 10 rows where BatchRx shows TOTAL ORDERED-O = 0 but DawaiRx shows non-zero
- These medicines have TOTAL BILLED-B = 0 in BatchRx
- **Root Cause**: BatchRx filters ordered data to only include medicines that appear in sold data

### Category 2: COST Calculation Error (HIGH PRIORITY)
**Issue**: COST calculation logic is incorrect
- BatchRx: COST = AMOUNT in only 3 out of 54 rows (uses actual cost data)
- DawaiRx: COST = AMOUNT in 36 out of 54 rows (fallback too often)
- **Root Cause**: Need to properly calculate cost from ordered data (ordered_qty * unit_cost)

### Category 3: HIGHEST SHORTAGE-S Logic (MEDIUM PRIORITY)
**Issue**: HIGHEST SHORTAGE-S should be NaN in specific cases
- BatchRx: NaN in 31 rows (when TOTAL SHORTAGE < 0 or when no "highest" shortage exists)
- DawaiRx: Always set to TOTAL SHORTAGE-S value
- **Root Cause**: Should only set HIGHEST SHORTAGE-S when there's a positive shortage AND it represents the "highest" shortage scenario

### Category 4: Normalization Issues (MEDIUM PRIORITY)
**Issues**:
1. Insurance name: "SS&C (FORMERLY HUMANA, ARGUS, AND DST)" vs "SS&C (FORMERLY HUMANA ARGUS AND OPTUMRX)"
2. Supplier names: "SMITH DRUGS" vs "SUPPLIER SMITH DRUGS", "LEGACY HEALTH" vs "SUPPLIER LEGACY HEALTH"
3. DRUG NAME formatting: "ELIQUIS 5MG TAB" vs "ELIQUIS TAB 5MG"

### Category 5: Rounding/Numeric Precision (LOW PRIORITY)
**Issues**:
- AMOUNT: Small rounding differences (1647 vs 1647.45)
- COST: Precision differences (1044.03 vs 1044.0)

## STEP 3: BatchRx Logic Inference

### Grouping Key
- Primary: `NDC` (11-digit normalized)
- Secondary: `medicine_key` (NDC + drug_name + strength + manufacturer)

### Aggregation Logic
1. **TOTAL ORDERED-O**: 
   - Only include medicines that appear in sold data (TOTAL BILLED-B > 0)
   - Sum of (ordered_qty * pkg_size) for each medicine
   - If medicine not in sold data, set to 0

2. **TOTAL BILLED-B**: 
   - Sum of sold_qty from sold_df, grouped by medicine_key
   - Only medicines with sales > 0 appear in report

3. **TOTAL SHORTAGE-S**: 
   - TOTAL ORDERED-O - TOTAL BILLED-B

4. **HIGHEST SHORTAGE-S**: 
   - Set to NaN when TOTAL SHORTAGE-S < 0 (negative shortage = leftover)
   - Set to NaN when TOTAL SHORTAGE-S = 0
   - Only set to value when TOTAL SHORTAGE-S > 0 (actual shortage)

5. **AMOUNT**: 
   - Sum of (primary_insurance_paid + secondary_insurance_paid)
   - Rounded to whole number

6. **COST**: 
   - If cost data exists: sum of (ordered_qty * unit_cost) from ordered_df
   - Otherwise: COST = AMOUNT
   - Rounded to 2 decimal places

### Filtering Rules
- **Primary Filter**: Only medicines with TOTAL BILLED-B > 0 appear in report
- **Ordered Data Filter**: Only include ordered quantities for medicines that appear in sold data

## STEP 4: Required Code Changes

1. **Filter ordered data to only include medicines in sold data**
2. **Fix COST calculation to use actual cost data properly**
3. **Fix HIGHEST SHORTAGE-S logic (set to NaN when appropriate)**
4. **Fix supplier name normalization (remove "SUPPLIER" prefix)**
5. **Fix insurance name normalization**
6. **Fix AMOUNT rounding (round to whole number)**
7. **Fix COST precision (round to 2 decimal places)**

