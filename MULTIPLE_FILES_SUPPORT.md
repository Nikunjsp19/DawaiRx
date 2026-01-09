# Multiple Inventory Report Files Support

## Overview

DawaiRx now supports uploading and processing **multiple inventory report files** for the sold/inventory report. This allows you to combine data from multiple sources (e.g., different wholesalers, different time periods) into a single reconciliation.

## Features

### Web UI
- **Multiple file selection** - Select multiple CSV/XLSX files for inventory reports
- **Automatic combination** - All files are automatically combined before processing
- **File count display** - Shows how many files were uploaded and total rows

### CLI
- **Multiple `--sold` options** - Specify `--sold` multiple times for multiple files
- **Automatic combination** - Files are processed and combined automatically
- **Progress feedback** - Shows progress for each file being processed

## Usage

### Web UI

1. Go to the upload page
2. Select **one** ordered report file
3. Select **multiple** inventory report files (hold Ctrl/Cmd to select multiple)
4. Click "Run Reconciliation"
5. All inventory files will be combined automatically

**Example:**
- Ordered Report: `ordered_report.csv` (1 file)
- Inventory Reports: `primerx_report.csv`, `alpine_report.csv`, `akron_report.csv` (3 files)
- Result: All 3 inventory files are combined and reconciled against the ordered report

### CLI

```bash
# Single inventory file (as before)
python -m src.cli.main run \
  --ordered ordered.csv \
  --sold inventory.csv \
  --output-dir out/run

# Multiple inventory files
python -m src.cli.main run \
  --ordered ordered.csv \
  --sold primerx_report.csv \
  --sold alpine_report.csv \
  --sold akron_report.csv \
  --output-dir out/run
```

## How It Works

1. **Upload Phase:**
   - All inventory files are uploaded and saved
   - Each file is validated individually
   - Validation results are combined

2. **Processing Phase:**
   - Each inventory file is processed separately
   - All DataFrames are combined using `pd.concat()`
   - Combined DataFrame is normalized
   - Reconciliation runs on the combined data

3. **Output:**
   - All reports show the combined data
   - Total row counts reflect all files combined

## File Requirements

All inventory files must:
- Have the same column structure (or compatible columns)
- Use the same column names (auto-mapping handles variations)
- Be in CSV or XLSX format

## Example Use Cases

### 1. Multiple Wholesalers
Combine reports from different wholesalers:
```bash
--sold wholesaler1_report.csv \
--sold wholesaler2_report.csv \
--sold wholesaler3_report.csv
```

### 2. Multiple Time Periods
Combine monthly reports:
```bash
--sold november_report.csv \
--sold december_report.csv \
--sold january_report.csv
```

### 3. Different Sources
Combine different report types:
```bash
--sold primerx_report.csv \
--sold alpine_report.csv \
--sold akron_report.csv
```

## Technical Details

### Data Combination
- Files are combined using `pandas.concat()` with `ignore_index=True`
- Column alignment is automatic (pandas handles missing columns)
- Duplicate rows are preserved (can be identified by audit rules)

### Performance
- Each file is processed individually first
- Combination happens after processing
- Memory usage scales with total data size

### Validation
- Each file is validated separately
- Combined validation shows:
  - Total file count
  - Total row count
  - Any errors from individual files

## Limitations

1. **Column Compatibility:** All files should have compatible column structures
2. **Memory:** Very large files may require significant memory
3. **Processing Time:** Multiple files take longer to process

## Best Practices

1. **Consistent Formats:** Use the same column format across all files
2. **File Naming:** Use descriptive names to identify sources
3. **File Size:** Consider file sizes when combining many files
4. **Validation:** Check validation results for each file before combining

## Troubleshooting

### Files Not Combining
- Check that all files have compatible columns
- Verify file formats (CSV/XLSX)
- Check validation errors for individual files

### Memory Issues
- Process files in smaller batches
- Use smaller date ranges per file
- Consider processing separately and combining results

### Column Mismatches
- Use mapping configuration files
- Ensure column names are consistent
- Check auto-mapping results

