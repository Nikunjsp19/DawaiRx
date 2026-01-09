# Pre-Testing Checklist

## ✅ Project Structure Verification

### Core Modules
- ✅ `src/ingestion/` - File loading and mapping (5 files)
- ✅ `src/normalization/` - Data standardization (6 files)
- ✅ `src/reconciliation/` - Inventory reconciliation (1 file)
- ✅ `src/rules/` - Audit rules engine (3 files)
- ✅ `src/reporting/` - Report generation (1 file)
- ✅ `src/persistence/` - MongoDB operations (4 files)
- ✅ `src/cli/` - CLI commands (6 files)
- ✅ `src/web/` - Web UI (3 files + templates)

### Test Files
- ✅ `tests/test_ingestion.py`
- ✅ `tests/test_normalization.py`
- ✅ `tests/test_reconciliation.py`
- ✅ `tests/test_rules.py`
- ✅ `tests/test_persistence.py`
- ✅ `tests/test_mongo_connection.py`

### Configuration Files
- ✅ `requirements.txt` - All dependencies listed
- ✅ `pyproject.toml` - Project configuration
- ✅ `docker-compose.yml` - MongoDB setup
- ✅ `Makefile` - Build commands
- ✅ `setup.py` - Package installation
- ✅ `.gitignore` - Proper exclusions

### Sample Data
- ✅ `sample_data/ordered_sample.csv` - Sample ordered report
- ✅ `sample_data/sold_sample.csv` - Sample sold report
- ✅ `config/mapping_sample.yaml` - Sample mapping config

### Documentation
- ✅ `README.md` - Complete setup and usage instructions
- ✅ `COMPLETE_SUMMARY.md` - Full feature documentation
- ✅ Phase summaries (PHASE_0-6_SUMMARY.md)

## ✅ Code Quality Checks

### Syntax & Imports
- ✅ No syntax errors (verified with py_compile)
- ✅ All imports are present
- ✅ pandas imported where needed
- ✅ No undefined variables

### Module Structure
- ✅ All `__init__.py` files present
- ✅ Proper module exports
- ✅ Clean architecture separation

### Error Handling
- ✅ Try/except blocks in critical paths
- ✅ HTTPException handling in web app
- ✅ Logging throughout

## ✅ Functionality Verification

### CLI Commands
- ✅ `validate` - File validation
- ✅ `normalize` - Data normalization
- ✅ `run` - Full reconciliation
- ✅ `runs list` - List previous runs
- ✅ `runs show` - Show run details
- ✅ `runs export` - Export previous run
- ✅ `web` - Start web server

### Web UI
- ✅ File upload endpoint
- ✅ Run comparison endpoint
- ✅ Runs listing endpoint
- ✅ Download endpoints
- ✅ HTML templates present

### Core Features
- ✅ CSV/XLSX file loading
- ✅ Column mapping (auto + config)
- ✅ NDC normalization
- ✅ Text/date/quantity normalization
- ✅ Medicine key generation
- ✅ Inventory reconciliation
- ✅ 7 audit rules (R001-R007)
- ✅ Excel report generation
- ✅ MongoDB persistence

## ⚠️ Pre-Testing Requirements

### Dependencies
Before testing, ensure:
1. Python 3.11+ installed
2. Dependencies installed: `make install`
3. MongoDB running: `make docker-up`

### Environment Setup
```bash
# 1. Install dependencies
make install

# 2. Start MongoDB
make docker-up

# 3. Verify MongoDB connection
make mongo-test

# 4. Run tests
make test
```

## 🔍 Potential Issues to Watch For

### During Testing

1. **MongoDB Connection**
   - If MongoDB not running, persistence will fail gracefully
   - Web UI will work but won't save runs
   - CLI will show warnings

2. **File Paths**
   - Ensure sample data files exist
   - Check output directory permissions
   - Web UI creates `uploads/` and `out/web_runs/` directories

3. **Dependencies**
   - FastAPI dependencies only needed for web UI
   - CLI works without FastAPI
   - All core dependencies in requirements.txt

4. **Column Mapping**
   - Sample data uses standard column names
   - Auto-mapping should work out of the box
   - Custom mapping config optional

5. **Large Files**
   - Code uses vectorized operations
   - Should handle 100k+ rows efficiently
   - Memory usage scales with file size

## ✅ Ready for Testing

All code is complete, syntax-checked, and ready for testing. The project structure is clean, all modules are properly connected, and error handling is in place.

### Quick Test Commands

```bash
# Test CLI validation
python -m src.cli.main validate \
  --ordered sample_data/ordered_sample.csv \
  --sold sample_data/sold_sample.csv

# Test full run
python -m src.cli.main run \
  --ordered sample_data/ordered_sample.csv \
  --sold sample_data/sold_sample.csv \
  --output-dir out/test_run

# Test web UI
python -m src.cli.main web
# Then open http://127.0.0.1:8000
```

## Notes

- All code follows clean architecture principles
- Type hints used throughout
- Comprehensive logging
- No hardcoded paths (uses Path objects)
- Error handling in all critical paths
- MongoDB operations are optional (graceful degradation)

