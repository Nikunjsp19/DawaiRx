# Compare Reports: Python vs Java/React

Run the same report (5 supplier files + 1 inventory) in both apps and compare CSV outputs.

## 1. Sample data

- **Location:** `/Users/nikunjpatel/Desktop/sample_data`
- **Inventory:** `inventory_report.csv`
- **Suppliers:** `1.akron_generics.csv`, `2_alpine_health.csv`, `3_kinray.csv`, `4 supplier_legacy_health.csv`, `5_supplier_smith_drugs.csv`
- **Date range:** 2025-01-01 to 2026-01-01 (passed to Java; Python CLI uses full file data)

## 2. Run Python report

```bash
cd /path/to/DawaiRx
python3 -m src.cli.main run \
  --ordered "/Users/nikunjpatel/Desktop/sample_data/1.akron_generics.csv" \
  --ordered "/Users/nikunjpatel/Desktop/sample_data/2_alpine_health.csv" \
  --ordered "/Users/nikunjpatel/Desktop/sample_data/3_kinray.csv" \
  --ordered "/Users/nikunjpatel/Desktop/sample_data/4 supplier_legacy_health.csv" \
  --ordered "/Users/nikunjpatel/Desktop/sample_data/5_supplier_smith_drugs.csv" \
  --sold "/Users/nikunjpatel/Desktop/sample_data/inventory_report.csv" \
  --output-dir /tmp/dawai_compare/python_out
```

Outputs: `remaining_inventory.csv`, `shortages.csv`, `reconciliation_full.csv`, `issues.csv`, etc.

## 3. Run Java/React report

1. **Start backend** (if not already): `cd backend && mvn spring-boot:run`
2. **Set credentials** (use a user that exists in MongoDB):
   ```bash
   export DAWAI_USER="Admin@DawaiRx.us"
   export DAWAI_PASSWORD="Niks@1908"
   ```
3. **Run script:**
   ```bash
   python3 scripts/run_java_report_and_compare.py --out-dir /tmp/dawai_compare/java_out
   ```
   This logs in, uploads the 5 supplier + 1 inventory file, runs the report (with date_from=2025-01-01, date_to=2026-01-01), and downloads CSVs to the given dir.

## 4. Compare results

```bash
python3 scripts/compare_report_results.py \
  --python-dir /tmp/dawai_compare/python_out \
  --java-dir /tmp/dawai_compare/java_out
```

Prints row counts for each CSV and, when Java output exists, diffs by `medicine_key` and key numeric columns.

## Backend fix applied

If the Java run previously failed with **500 "Unsupported field: YearOfEra"**:

- **RunService:** runId formatter changed from `yyyyMMdd_HHmmss` to `uuuuMMdd_HHmmss`; `RunDocument.setCreatedAt` now uses `java.util.Date` instead of `Instant` to avoid MongoDB serialization issues.
- **Restart the Spring Boot backend** so these changes are loaded, then re-run step 3.
