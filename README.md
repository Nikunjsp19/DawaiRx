# DawaiRx - Pharmacy Audit & Reconciliation Tool

A local-only pharmacy audit/reconciliation application for comparing ordered and sold medication reports. Built with Python 3.11+ and MongoDB.

## Features

- **Ingest** pharmacy reports (CSV/XLSX)
- **Normalize** data (NDC codes, drug names, quantities)
- **Reconcile** inventory (ordered vs sold)
- **Flag** audit issues with rule-based detection
- **Generate** reports (CSV exports + Excel workbook)
- **Persist** run history in MongoDB

## Requirements

- Python 3.11 or higher
- MongoDB (Atlas recommended)
- pip

## Quick Start

### 1. Setup

```bash
# Clone or navigate to project directory
cd DawaiRx

# Create virtual environment (recommended)
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
make install
# OR: pip install -r requirements.txt
```

### 2. Configure MongoDB

Set a MongoDB connection string (Atlas recommended):

```bash
export MONGO_URI="mongodb+srv://username:password@cluster.mongodb.net/DawaiRx?retryWrites=true&w=majority"
```

If you run MongoDB locally, set `MONGO_URI` to your local connection string:

```bash
export MONGO_URI="mongodb://localhost:27017/dawai_rx"
```

### 3. Run Tests

```bash
make test
```

### 4. Usage

#### CLI Usage

```bash
# Validate input files
python -m src.cli.main validate \
  --ordered sample_data/ordered_sample.csv \
  --sold sample_data/sold_sample.csv

# Run full reconciliation
python -m src.cli.main run \
  --ordered sample_data/ordered_sample.csv \
  --sold sample_data/sold_sample.csv \
  --output-dir out/sample_run

# List previous runs
python -m src.cli.main runs list

# Show run details
python -m src.cli.main runs show <run_id>

# Export a previous run
python -m src.cli.main runs export <run_id>
```

#### Web UI Usage

```bash
# Start web server
python -m src.cli.main web
# OR: make web

# Open browser to http://127.0.0.1:8000
```

The web UI provides:
- File upload interface
- Run reconciliation
- View results and statistics
- Download outputs
- Browse previous runs

## Project Structure

```
DawaiRx/
├── src/
│   ├── ingestion/      # File reading and column mapping
│   ├── normalization/  # Data standardization
│   ├── reconciliation/ # Inventory reconciliation
│   ├── rules/          # Audit rule engine
│   ├── reporting/      # Report generation
│   ├── persistence/    # MongoDB operations
│   ├── cli/            # Command-line interface
│   └── web/            # Web UI (FastAPI)
├── tests/              # Unit tests
├── config/             # Configuration files
├── scripts/            # Utility scripts (password reset, setup verification)
├── sample_data/        # Sample input files
├── out/                # Output directory (generated)
├── requirements.txt
├── pyproject.toml
└── Makefile
```

## Development

```bash
# Format code
make format

# Run linters
make lint

# Run tests with coverage
make test

# Start web UI
make web

# Clean temporary files
make clean
```

## MongoDB Connection

**Recommended**: MongoDB Atlas cloud connection  
Set `MONGO_URI` with your own connection string.

**Local MongoDB**:
```bash
export MONGO_URI="mongodb://localhost:27017/dawai_rx"
```

**To customize connection:**
- Set `MONGO_URI` environment variable with your connection string
- Or modify `src/persistence/config.py`

## Deploy to Azure (Simple GitHub → App Service)

This is the simplest path: push to GitHub, and Azure deploys automatically.

### 1. Create the Azure Web App (Code, not Docker)
1. Azure Portal → **Create resource** → **Web App**
2. **Publish**: `Code`
3. **Runtime**: `Python 3.11`
4. **Operating system**: Linux
5. **Plan**: your Basic B1 plan

### 2. Configure App Settings
Azure Portal → your Web App → **Configuration** → **Application settings**
Add:
- `MONGO_URI` = your MongoDB connection string
- `SECRET_KEY` = any strong random string
- `PORT` = `8000`

Then **Save** (this restarts the app).

### 3. Set Startup Command
Azure Portal → your Web App → **Configuration** → **General settings**
Set **Startup Command**:
```
python -m src.cli.main web --host 0.0.0.0 --port 8000
```

### 4. Add GitHub Actions Deployment
1. In Azure Portal → **Deployment Center**
2. Choose **GitHub** and connect your repo
3. Azure will create a workflow in `.github/workflows/`

Or use the included workflow below (see `DEPLOYMENT-AZURE-GITHUB.md`).

### 5. Push to GitHub
Any push to `main` deploys automatically.

## Status

- ✅ Phase 0: Repository bootstrap
- ✅ Phase 1: Ingestion + schema mapping
- ✅ Phase 2: Normalization layer
- ✅ Phase 3: Reconciliation engine
- ✅ Phase 4: Rules engine + issues output
- ✅ Phase 5: MongoDB persistence + run history
- ✅ Phase 6: Minimal local UI

## License

MIT
