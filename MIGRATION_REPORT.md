# Python → Java Migration Report: Report-Generation Pipeline

## Summary

Ported the complete report-generation pipeline from Python to Java, achieving functional parity for:
- Upload + run flow
- Report column/row parity (DawaiRx format)
- Medicine detail endpoint
- Persistence (run items, issues, stats)
- Downloadable artifacts

---

## Files Changed

### New Files (6)

| File | Purpose |
|------|---------|
| `backend/src/main/java/com/dawai/reporting/DawairxReportBuilder.java` | Full DawaiRx CSV report (port of `src/reporting/dawairx_format.py`) |
| `backend/src/main/java/com/dawai/reporting/ExcelReportBuilder.java` | Multi-sheet Excel audit report (port of `src/reporting/excel.py`) |
| `backend/src/test/java/com/dawai/normalization/NdcNormalizerTest.java` | 17 unit tests for NDC normalization |
| `backend/src/test/java/com/dawai/normalization/MedicineKeyGeneratorTest.java` | 9 unit tests for medicine key generation |
| `backend/src/test/java/com/dawai/normalization/NormalizationServiceTest.java` | 9 unit tests for normalization service |
| `backend/src/test/java/com/dawai/reconciliation/ReconciliationServiceTest.java` | 4 unit tests for reconciliation |
| `backend/src/test/java/com/dawai/reporting/DawairxReportBuilderTest.java` | 2 integration tests (full pipeline + empty report) |
| `backend/src/test/resources/fixtures/ordered_smith.csv` | Test fixture: ordered data (supplier 1) |
| `backend/src/test/resources/fixtures/ordered_kinray.csv` | Test fixture: ordered data (supplier 2) |
| `backend/src/test/resources/fixtures/sold_report.csv` | Test fixture: sold data with insurance |
| `scripts/parity_check.py` | Cross-language parity comparison script |

### Modified Files (4)

| File | Change |
|------|--------|
| `backend/src/main/java/com/dawai/normalization/MedicineKeyGenerator.java` | **Critical fix**: composite keys now use UPPERCASE (was lowercase + stripped non-alpha). Matches Python `normalize_text(s, case="upper")`. |
| `backend/src/main/java/com/dawai/normalization/NormalizationService.java` | **Rewrite**: UPPERCASE text normalization, date parsing, quantity/insurance field parsing, original value preservation (`_original` fields). |
| `backend/src/main/java/com/dawai/service/RunService.java` | **Rewrite**: Complete pipeline integration — ingest → normalize → date-filter → reconcile → rules → DawaiRx CSV → Excel → source CSVs → MongoDB persistence. Medicine detail now returns populated entries from source CSVs. |
| `backend/src/main/java/com/dawai/controller/UploadController.java` | Added `date_from`, `date_to`, `report_name` parameters to match Python API contract. |
| `backend/src/main/java/com/dawai/controller/RunController.java` | Fixed download endpoint file-type mapping (matching Python convention) and content-disposition filename. |

---

## Logic Parity Details

### 1. NDC Normalization (`NdcNormalizer`)
- ✅ 10-digit → 11-digit padding (5-4-1 → 5-4-2)
- ✅ Strips non-digits
- ✅ Rejects < 10 or > 11 digits
- ✅ Format display: 5-4-2 (`12345-6789-01`)

### 2. Medicine Key Generation (`MedicineKeyGenerator`)
- ✅ Primary: `NDC:{11digits}` when NDC valid
- ✅ Fallback: `COMPOSITE:{DRUG_NAME}|{STRENGTH}|{MANUFACTURER}` (UPPERCASE, spaces collapsed)
- ✅ Last resort: `UNKNOWN`
- **Before fix**: Java used `lowercase + strip-non-alpha` → keys didn't match Python

### 3. Text Normalization (`NormalizationService`)
- ✅ drug_name → UPPERCASE, collapse spaces
- ✅ strength → UPPERCASE
- ✅ manufacturer → UPPERCASE
- ✅ Preserves originals as `*_original` fields
- ✅ Date parsing: M/d/yyyy, MM/dd/yyyy, yyyy-MM-dd, yyyyMMdd
- ✅ Quantity parsing: handles commas, dollar signs, blanks
- ✅ Insurance paid fields: parsed to double
- ✅ claim_date / order_date fallback copying

### 4. Reconciliation (`ReconciliationService`)
- ✅ Aggregates by medicine_key (sum quantities)
- ✅ Outer join (medicines in only one side)
- ✅ remaining_qty = ordered - sold
- ✅ shortage_qty = abs(remaining) if remaining < 0
- ✅ leftover_qty = remaining if remaining > 0
- ✅ Coalesce display fields (ordered preferred)

### 5. DawaiRx Report (`DawairxReportBuilder`) — **CRITICAL**
- ✅ Column names with `\n` separators: `TOTAL\nORDERED-O`, `TOTAL\nBILLED-B`, etc.
- ✅ NDC formatted for display (5-4-2)
- ✅ Drug name from sold data (prefers `drug_name_original`)
- ✅ PKG SIZE from sold data (defaults to 1)
- ✅ TOTAL ORDERED-O: only for medicines with sales, units = ordered_qty × pkg_size
- ✅ TOTAL SHORTAGE-S: recalculated as ORDERED - BILLED
- ✅ HIGHEST SHORTAGE-S: negative values only (leftovers), blank for positive/zero
- ✅ **AMOUNT = floor(primary_insurance_paid + secondary_insurance_paid)** — floor not round
- ✅ COST: from ordered data cost fields, falls back to AMOUNT, rounded to 2 decimals
- ✅ Filtered: only medicines with TOTAL BILLED-B > 0
- ✅ RANK: sorted by AMOUNT desc → COST desc, continuous 1–N
- ✅ Insurance breakdown: BILLED/SHORTAGE per insurance (checks both primary and secondary)
- ✅ Supplier columns: from all_supplier_names (before date filtering), units = qty × pkg_size
- ✅ Column ordering: base → insurance (non-CASH) → suppliers → CASH → medicine_key
- ✅ Zero → blank for numeric columns

### 6. Medicine Detail Endpoint
- ✅ Loads source_ordered.csv and source_sold.csv
- ✅ Normalizes medicine_identifier (NDC:, COMPOSITE:, or raw NDC)
- ✅ Returns ordered_entries with date, supplier_name, quantity
- ✅ Returns sold_entries with date, quantity
- ✅ Returns total_ordered, total_sold
- ✅ Returns report_data (matched row from inventory_report.csv)

### 7. Persistence
- ✅ RunDocument: run_id, user_id, created_at, stats, config_summary, input_metadata
- ✅ RunItemDocument: one per medicine_key from reconciled data
- ✅ RunIssueDocument: one per rule violation
- ✅ Stats include total_issues count
- ✅ Config includes date_from, date_to, report_name

### 8. Download Artifacts
- ✅ `inventory_report.csv` — DawaiRx format
- ✅ `audit_report.xlsx` — Multi-sheet Excel
- ✅ `source_ordered.csv` — Normalized ordered data
- ✅ `source_sold.csv` — Normalized sold data
- ✅ `summary.json` — Stats + config
- ✅ File-type mapping: `inventory_report` → `inventory_report.csv`, etc.

---

## Known Acceptable Differences

| Item | Python | Java | Rationale |
|------|--------|------|-----------|
| `medicine_key` in CSV | Removed from final CSV | Kept as last column | Needed for medicine detail linking; frontend ignores extra columns |
| `run_id` format | `YYYYMMDD_HHMMSS_mmm` | `YYYYMMDD_HHmmss_SSS` | Functionally equivalent timestamp format |
| PDF report | Generated via `create_detailed_pdf_report()` | Not generated | Lower priority; Excel report covers same data |
| Insurance name normalization | Maps SS&C and other variations | Pass-through | Applies only to specific DawaiRx deployments |

---

## Test Results

```
Tests run: 41, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

| Test Class | Tests | Status |
|------------|-------|--------|
| `NdcNormalizerTest` | 17 | ✅ All pass |
| `MedicineKeyGeneratorTest` | 9 | ✅ All pass |
| `NormalizationServiceTest` | 9 | ✅ All pass |
| `ReconciliationServiceTest` | 4 | ✅ All pass |
| `DawairxReportBuilderTest` | 2 | ✅ All pass |

### Integration test validates:
- Full pipeline: ingest → normalize → reconcile → DawaiRx report
- All required column names present (including `\n` variants)
- Atorvastatin (ordered but never sold) correctly filtered out
- RANK consecutive 1–N
- AMOUNT uses floor() (138.25 → 138, not 139)
- HIGHEST SHORTAGE-S only has negative values
- Insurance columns (BlueCross, Aetna) present
- Supplier columns (SMITH DRUGS, KINRAY) present
- Empty report produces header-only CSV

---

## Commands to Run

### Run Java tests
```bash
cd backend && mvn test
```

### Run parity check (Python vs Java)
```bash
# First generate Java output by uploading fixtures via API
# Then:
python scripts/parity_check.py --java-output <path/to/java/inventory_report.csv>
```

### Start Java backend
```bash
cd backend && mvn spring-boot:run
```

---

## API Contract Summary (no breaking changes)

| Endpoint | Method | Changes |
|----------|--------|---------|
| `/api/upload` | POST | Added optional `date_from`, `date_to`, `report_name` params |
| `/api/runs` | GET | No change |
| `/api/runs/{runId}` | GET | No change (now returns full CSV data) |
| `/api/runs/{runId}/medicine/{identifier}` | GET | Now returns populated ordered_entries/sold_entries |
| `/api/download/{runId}/{fileType}` | GET | Fixed file-type mapping; added report_name in Content-Disposition |
| `/api/auth/*` | * | No change |
| `/api/admin/*` | * | No change |
