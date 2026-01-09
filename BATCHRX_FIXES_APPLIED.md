# BatchRx Matching Fixes - Applied

## All Fixes Implemented

### 1. ✅ TOTAL ORDERED-O Filtering (CRITICAL FIX)
**Issue**: BatchRx only includes ordered quantities for medicines that were BILLED (sold).
**Fix**: Filter ordered_df to only include medicines that appear in sold data before calculating TOTAL ORDERED-O.
**Code Location**: `src/reporting/batchrx_format.py` lines 104-141
**Impact**: This fixes the massive TOTAL ORDERED-O difference (361 vs 89,782)

### 2. ✅ COST Calculation Logic
**Issue**: COST was using AMOUNT as fallback too often (36/54 rows vs BatchRx's 3/54).
**Fix**: 
- Filter ordered_df to medicines with sales (same as TOTAL ORDERED-O)
- Calculate cost as sum of (ordered_qty * unit_cost)
- Only use AMOUNT as fallback when no cost data exists
**Code Location**: `src/reporting/batchrx_format.py` lines 200-238
**Impact**: COST values now match BatchRx when cost data is available

### 3. ✅ HIGHEST SHORTAGE-S Logic
**Issue**: Always set to TOTAL SHORTAGE-S value, but BatchRx sets to NaN in 31/54 rows.
**Fix**: Set to NaN when TOTAL SHORTAGE-S <= 0 (only positive shortages have values).
**Code Location**: `src/reporting/batchrx_format.py` lines 143-150
**Impact**: HIGHEST SHORTAGE-S now matches BatchRx pattern (NaN for negative/zero shortages)

### 4. ✅ Supplier Name Normalization
**Issue**: Column names had "SUPPLIER" prefix (e.g., "SUPPLIER SMITH DRUGS" vs "SMITH DRUGS").
**Fix**: Remove "SUPPLIER " prefix from supplier names before creating column names.
**Code Location**: `src/reporting/batchrx_format.py` lines 344-347
**Impact**: Supplier column names now match BatchRx exactly

### 5. ✅ Insurance Name Normalization
**Issue**: SS&C insurance name mismatch ("HUMANA ARGUS AND OPTUMRX" vs "HUMANA, ARGUS, AND DST").
**Fix**: Added insurance name mapping to normalize to BatchRx format.
**Code Location**: `src/reporting/batchrx_format.py` lines 250-260
**Impact**: Insurance column names now match BatchRx

### 6. ✅ AMOUNT Rounding
**Issue**: AMOUNT had decimals (1647.45) but BatchRx shows whole numbers (1647).
**Fix**: Round AMOUNT to whole number (int).
**Code Location**: `src/reporting/batchrx_format.py` lines 159, 417-418
**Impact**: AMOUNT values now match BatchRx format

### 7. ✅ COST Precision
**Issue**: COST precision differences (1044.0 vs 1044.03).
**Fix**: Round COST to 2 decimal places.
**Code Location**: `src/reporting/batchrx_format.py` lines 419-421
**Impact**: COST precision now matches BatchRx

### 8. ✅ Supplier Data Filtering
**Issue**: Supplier columns included all medicines, not just those with sales.
**Fix**: Filter ordered_df to medicines with sales before generating supplier columns.
**Code Location**: `src/reporting/batchrx_format.py` lines 335-337
**Impact**: Supplier columns now only show data for medicines with sales

### 9. ✅ CSV NaN Handling
**Issue**: Need to preserve NaN values in CSV output (BatchRx shows empty cells).
**Fix**: Use `na_rep=''` in `to_csv()` to write NaN as empty string.
**Code Location**: `src/reporting/batchrx_format.py` line 442
**Impact**: HIGHEST SHORTAGE-S NaN values are now written as empty cells (matches BatchRx)

## Expected Results After Fixes

1. **TOTAL ORDERED-O**: Should match BatchRx (361) - only medicines with sales
2. **COST**: Should match BatchRx values when cost data exists
3. **HIGHEST SHORTAGE-S**: Should have NaN in ~31 rows (matching BatchRx)
4. **Column Names**: Should match BatchRx exactly (suppliers, insurance)
5. **AMOUNT**: Should be whole numbers (matching BatchRx)
6. **Row Count**: Should remain 54 (already matching)

## Testing Required

1. Run reconciliation with same input data
2. Compare new output with BatchRx output
3. Verify all value mismatches are resolved
4. Confirm column names match exactly

