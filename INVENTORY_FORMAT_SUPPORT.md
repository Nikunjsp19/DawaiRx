# Inventory Report Format Support

## Overview

DawaiRx now supports the standard pharmacy inventory report format with the following columns:

## Supported Column Names

### Core Fields (Required)
- **NDC NUMBER** → Maps to `ndc`
- **DRUG NAME** → Maps to `drug_name`
- **QUANTITY** → Maps to `sold_qty` (for sold reports) or `ordered_qty` (for ordered reports)
- **DATE FILLED** → Maps to `claim_date`

### Additional Fields (Optional)
- **PKG SIZE** → Maps to `pkg_size`
- **PKG SIZE QTY** → Maps to `pkg_size_qty`
- **PRIMARY INSURANCE BIN NUMBER** → Maps to `primary_insurance_bin`
- **PRIMARY INSURANCE PAID** → Maps to `primary_insurance_paid`
- **PRIMARY INSURANCE NAME** → Maps to `primary_insurance_name`
- **SECONDARY INSURANCE BIN NUMBER** → Maps to `secondary_insurance_bin`
- **SECONDARY INSURANCE PAID** → Maps to `secondary_insurance_paid`
- **SECONDARY INSURANCE NAME** → Maps to `secondary_insurance_name`

## Auto-Detection

The system automatically detects these column names using:
1. Case-insensitive matching
2. Space and underscore normalization
3. Partial matching for compound names

### Examples

| Original Column Name | Mapped To |
|---------------------|-----------|
| `NDC NUMBER` | `ndc` |
| `DRUG NAME` | `drug_name` |
| `QUANTITY` | `sold_qty` (sold) or `ordered_qty` (ordered) |
| `DATE FILLED` | `claim_date` |
| `PKG SIZE` | `pkg_size` |
| `PRIMARY INSURANCE BIN NUMBER` | `primary_insurance_bin` |

## Usage

### CLI

```bash
# Process inventory format file as sold report
python -m src.cli.main run \
  --ordered your_ordered_file.csv \
  --sold inventory_report.csv \
  --output-dir out/my_run
```

### Web UI

1. Upload your inventory report file as the "Sold Report"
2. The system will automatically detect and map the columns
3. Run reconciliation

## Sample File

A sample file is available at:
```
sample_data/inventory_report_sample.csv
```

## Column Mapping Details

### NDC Handling
- Supports formats with 'Q' prefix (e.g., `Q31722-0551-90`)
- Normalizes to 11-digit format
- Handles dashes and spaces

### Quantity Handling
- Automatically converts `QUANTITY` to `sold_qty` for sold reports
- Supports decimal values (e.g., `0.33`, `3.75`)
- Handles zero and negative values

### Date Handling
- Supports `MM/DD/YYYY` format (e.g., `05/01/2025`)
- Also supports other common date formats
- Automatically parses and normalizes dates

### Insurance Fields
- All insurance fields are preserved but optional
- Not used in reconciliation but available in output
- Can be used for custom reporting

## Testing

Test with the sample file:

```bash
python -m src.cli.main run \
  --ordered sample_data/ordered_sample.csv \
  --sold sample_data/inventory_report_sample.csv \
  --output-dir out/test
```

## Custom Mapping

If auto-detection doesn't work for your specific column names, you can create a mapping configuration file:

```yaml
# mapping.yaml
sold:
  "NDC NUMBER": ndc
  "DRUG NAME": drug_name
  "QUANTITY": sold_qty
  "DATE FILLED": claim_date
```

Then use it:

```bash
python -m src.cli.main run \
  --ordered ordered.csv \
  --sold sold.csv \
  --mapping mapping.yaml \
  --output-dir out/my_run
```

## Notes

- Column names are case-insensitive
- Spaces are normalized to underscores
- The system preserves original column names with `_original` suffix
- All additional fields (insurance, package size) are preserved in output files

