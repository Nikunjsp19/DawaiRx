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
- MongoDB (via Docker recommended)
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

### 2. Start MongoDB

```bash
# Start MongoDB using Docker Compose
make docker-up
# OR: docker-compose up -d

# Verify MongoDB is running
make mongo-test
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
├── docker-compose.yml
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

**Default**: MongoDB Atlas cloud connection
- Connection: `mongodb+srv://user:user@temp.tzhzodo.mongodb.net/DawaiRx`

**To use local MongoDB instead:**
```bash
# Set environment variable
export MONGO_URI="mongodb://localhost:27017/dawai_rx"

# OR start local MongoDB with Docker
make docker-up
```

**To customize connection:**
- Set `MONGO_URI` environment variable with your connection string
- Or create a `.env` file (see `.env.example`)
- Or modify `src/persistence/config.py`

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

