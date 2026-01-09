# Phase 1: Ingestion + Schema Mapping - Complete ✅

## Files Created

### Source Code
- `src/ingestion/loaders.py` - CSV/XLSX file loaders
- `src/ingestion/mapper.py` - Column mapping system with auto-detection
- `src/ingestion/validator.py` - Data validation logic
- `src/ingestion/config_loader.py` - YAML/JSON config loading
- `src/ingestion/processor.py` - Main ingestion pipeline
- `src/cli/validate_cmd.py` - CLI validate command

### Sample Data
- `sample_data/ordered_sample.csv` - Sample ordered report
- `sample_data/sold_sample.csv` - Sample sold report
- `config/mapping_sample.yaml` - Sample mapping configuration

### Tests
- `tests/test_ingestion.py` - Comprehensive unit tests for ingestion module

## Features Implemented

1. **File Loaders**
   - CSV and XLSX support
   - Automatic file type detection
   - File metadata extraction

2. **Column Mapping**
   - Auto-detection of common column names
   - YAML/JSON configuration support
   - Flexible mapping with case-insensitive matching
   - Support for both explicit and auto-generated mappings

3. **Validation**
   - Required field checking
   - Data quality checks (nulls, empty rows)
   - Numeric field validation
   - Comprehensive error and warning reporting

4. **CLI Command**
   - `validate --ordered FILE --sold FILE [--mapping CONFIG]`
   - Preview CSV generation
   - Auto-mapping generation

## How to Run and Verify Phase 1

### 1. Install Dependencies
```bash
make install
```

### 2. Test with Sample Data
```bash
python -m src.cli.main validate \
  --ordered sample_data/ordered_sample.csv \
  --sold sample_data/sold_sample.csv
```

### 3. With Custom Mapping
```bash
python -m src.cli.main validate \
  --ordered sample_data/ordered_sample.csv \
  --sold sample_data/sold_sample.csv \
  --mapping config/mapping_sample.yaml
```

### 4. Generate Auto-Mapping
```bash
python -m src.cli.main validate \
  --ordered sample_data/ordered_sample.csv \
  --sold sample_data/sold_sample.csv \
  --generate-mapping config/auto_mapping.yaml
```

### 5. Generate Preview CSVs
```bash
python -m src.cli.main validate \
  --ordered sample_data/ordered_sample.csv \
  --sold sample_data/sold_sample.csv \
  --output-preview out/preview
```

### 6. Run Tests
```bash
make test
```

## Mapping Configuration Format

### YAML Format
```yaml
ordered:
  drug_name: drug_name
  ndc: ndc
  quantity: ordered_qty

sold:
  drug_name: drug_name
  ndc: ndc
  quantity_sold: sold_qty
```

### JSON Format
```json
{
  "ordered": {
    "drug_name": "drug_name",
    "ndc": "ndc",
    "quantity": "ordered_qty"
  },
  "sold": {
    "drug_name": "drug_name",
    "ndc": "ndc",
    "quantity_sold": "sold_qty"
  }
}
```

## Canonical Field Names

The system recognizes these canonical fields:
- `drug_name` - Drug/medication name
- `ndc` - National Drug Code
- `strength` - Dosage strength
- `manufacturer` - Manufacturer name
- `quantity` / `ordered_qty` / `sold_qty` - Quantities
- `rx_number` - Prescription number
- `fill_number` - Fill number
- `claim_date` - Transaction date
- `days_supply` - Days supply

## Next Steps (Phase 2)

Phase 2 will implement:
- NDC normalization to 11 digits
- Text field normalization
- Date parsing
- Medicine key generation
- `cli normalize` command

