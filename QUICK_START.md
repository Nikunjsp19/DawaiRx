# Quick Start Guide - DawaiRx

## Step 1: Initial Setup

### Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies
make install
# OR: pip install -r requirements.txt
```

### Start MongoDB

```bash
# Start MongoDB using Docker Compose
make docker-up

# Verify MongoDB is running
make mongo-test
```

You should see: `✅ MongoDB connection successful`

## Step 2: Test with Sample Data

### Option A: Using CLI

#### 1. Validate Files
```bash
python -m src.cli.main validate \
  --ordered sample_data/ordered_sample.csv \
  --sold sample_data/sold_sample.csv
```

#### 2. Run Full Reconciliation
```bash
python -m src.cli.main run \
  --ordered sample_data/ordered_sample.csv \
  --sold sample_data/sold_sample.csv \
  --output-dir out/my_first_run
```

This will:
- Process and normalize the files
- Reconcile inventory
- Run audit rules
- Generate reports
- Save to MongoDB

Output files will be in `out/my_first_run/`:
- `remaining_inventory.csv`
- `shortages.csv`
- `leftovers.csv`
- `issues.csv`
- `reconciliation_full.csv`
- `summary.json`
- `audit_report.xlsx`

#### 3. View Previous Runs
```bash
# List all runs
python -m src.cli.main runs list

# Show details of a specific run
python -m src.cli.main runs show <run_id>

# Export a previous run
python -m src.cli.main runs export <run_id>
```

### Option B: Using Web UI

#### 1. Start Web Server
```bash
python -m src.cli.main web
# OR: make web
```

#### 2. Open Browser
Navigate to: **http://127.0.0.1:8000**

#### 3. Upload and Run
- Click "Select Ordered Report" and choose `sample_data/ordered_sample.csv`
- Click "Select Sold Report" and choose `sample_data/sold_sample.csv`
- Click "Run Reconciliation"
- View results and download files

## Step 3: Using Your Own Data

### Prepare Your Files

Your files should have columns like:
- **Ordered report**: drug_name, ndc, quantity (or similar)
- **Sold report**: drug_name, ndc, quantity_sold (or similar)

### Option 1: Auto-Mapping (Recommended)

The system will automatically detect common column names:

```bash
python -m src.cli.main run \
  --ordered your_ordered_file.csv \
  --sold your_sold_file.csv \
  --output-dir out/my_run
```

### Option 2: Custom Mapping

Create a mapping file (YAML or JSON):

```yaml
# config/my_mapping.yaml
ordered:
  your_drug_column: drug_name
  your_ndc_column: ndc
  your_qty_column: ordered_qty

sold:
  your_drug_column: drug_name
  your_ndc_column: ndc
  your_qty_column: sold_qty
```

Then use it:
```bash
python -m src.cli.main run \
  --ordered your_ordered_file.csv \
  --sold your_sold_file.csv \
  --mapping config/my_mapping.yaml \
  --output-dir out/my_run
```

### Generate Auto-Mapping

If you're unsure about column names, generate a mapping:

```bash
python -m src.cli.main validate \
  --ordered your_ordered_file.csv \
  --sold your_sold_file.csv \
  --generate-mapping config/auto_mapping.yaml
```

Then review and edit `config/auto_mapping.yaml` if needed.

## Common Commands

### CLI Commands

```bash
# Show all available commands
python -m src.cli.main --help

# Validate files
python -m src.cli.main validate --ordered FILE --sold FILE

# Normalize data only
python -m src.cli.main normalize --ordered FILE --sold FILE

# Run full reconciliation
python -m src.cli.main run --ordered FILE --sold FILE

# List previous runs
python -m src.cli.main runs list

# Show run details
python -m src.cli.main runs show <run_id>

# Export previous run
python -m src.cli.main runs export <run_id>

# Start web UI
python -m src.cli.main web
```

### Makefile Commands

```bash
make install      # Install dependencies
make docker-up    # Start MongoDB
make docker-down  # Stop MongoDB
make mongo-test   # Test MongoDB connection
make test         # Run unit tests
make lint         # Check code style
make format       # Format code
make web          # Start web server
make clean        # Clean temporary files
```

## Troubleshooting

### MongoDB Not Running
```bash
# Check if MongoDB is running
docker ps

# Start MongoDB
make docker-up

# Check logs
docker-compose logs mongodb
```

### Import Errors
```bash
# Ensure dependencies are installed
make install

# Check Python version (must be 3.11+)
python3 --version
```

### File Not Found
- Ensure file paths are correct
- Use absolute paths if relative paths don't work
- Check file permissions

### Column Mapping Issues
- Use `validate` command first to see detected columns
- Generate auto-mapping and review it
- Create custom mapping file if needed

## Next Steps

1. **Review Outputs**: Check the generated CSV and Excel files
2. **Check Issues**: Review `issues.csv` for audit findings
3. **Explore Runs**: Use `runs list` to see all previous runs
4. **Customize Rules**: Review audit rules in `src/rules/implementations.py`

## Getting Help

- Check `README.md` for detailed documentation
- Review `COMPLETE_SUMMARY.md` for feature overview
- See `PRE_TEST_CHECKLIST.md` for testing guidance

