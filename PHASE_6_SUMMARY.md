# Phase 6: Minimal Local Web UI - Complete ✅

## Files Created

### Web Application
- `src/web/app.py` - FastAPI application with all endpoints
- `src/web/server.py` - Server startup script
- `src/web/templates/index.html` - Main upload and results page
- `src/web/templates/runs.html` - Previous runs listing page
- `src/cli/web_cmd.py` - CLI command to start web server

### Updated Files
- `requirements.txt` - Added FastAPI dependencies
- `Makefile` - Added `make web` command
- `README.md` - Added web UI usage instructions

## Features Implemented

### 1. File Upload
- Upload ordered and sold reports (CSV/XLSX)
- Optional mapping configuration file
- File validation on upload
- Session-based file management

### 2. Run Comparison
- Run full reconciliation from web UI
- Real-time status updates
- Results display with statistics
- Automatic MongoDB persistence

### 3. Results Display
- Summary statistics (medicines, quantities, issues)
- Download links for all outputs:
  - Remaining Inventory (CSV)
  - Shortages (CSV)
  - Leftovers (CSV)
  - Issues (CSV)
  - Audit Report (Excel)
  - Summary (JSON)

### 4. Previous Runs
- List all previous runs
- View run details
- Browse run history

### 5. Download Endpoints
- Download any output file by run ID
- Support for CSV, Excel, and JSON files

## API Endpoints

### Web Pages
- `GET /` - Home page (upload and run)
- `GET /runs` - Previous runs listing page

### API Endpoints
- `POST /api/upload` - Upload and validate files
- `POST /api/run` - Run reconciliation
- `GET /api/runs` - List recent runs
- `GET /api/runs/{run_id}` - Get run details
- `GET /api/download/{run_id}/{file_type}` - Download output file

## How to Run

### Start Web Server

```bash
# Using CLI command
python -m src.cli.main web

# Using Makefile
make web

# With custom host/port
python -m src.cli.main web --host 0.0.0.0 --port 8080
```

### Access Web UI

Open browser to: `http://127.0.0.1:8000`

### Usage Flow

1. **Upload Files**
   - Select ordered report file (CSV/XLSX)
   - Select sold report file (CSV/XLSX)
   - Optionally select mapping configuration file
   - Click "Run Reconciliation"

2. **View Results**
   - See summary statistics
   - Download output files
   - Results are automatically saved to MongoDB

3. **Browse Previous Runs**
   - Click "Previous Runs" link
   - View list of all runs
   - Click run ID to see details

## UI Design

- **Minimal and functional** - Focus on usability, not design
- **Responsive** - Works on different screen sizes
- **Clean interface** - Simple, intuitive layout
- **Real-time feedback** - Status messages during processing
- **Download ready** - Easy access to all outputs

## Technical Details

- **Framework**: FastAPI
- **Templates**: Jinja2
- **File Handling**: Temporary upload directory with session-based management
- **Error Handling**: Comprehensive error messages and status feedback
- **Integration**: Full integration with existing CLI functionality

## Dependencies Added

- `fastapi>=0.104.0` - Web framework
- `uvicorn>=0.24.0` - ASGI server
- `jinja2>=3.1.2` - Template engine
- `python-multipart>=0.0.6` - File upload support

## Notes

- Web UI runs on localhost only (127.0.0.1) by default
- No authentication required (local-only, single-user)
- All functionality matches CLI capabilities
- Files are stored temporarily in `uploads/` directory
- Outputs are stored in `out/web_runs/` directory
- MongoDB integration works the same as CLI

## Next Steps (Optional Enhancements)

- Add run detail view page
- Add file preview before running
- Add progress indicators for long-running operations
- Add export functionality directly from web UI
- Add filtering and search for runs

