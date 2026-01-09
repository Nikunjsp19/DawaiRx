# Web UI Guide - DawaiRx

## Quick Start

### 1. Start the Web Server

```bash
python -m src.cli.main web
# OR
make web
```

The server will start at: **http://127.0.0.1:8000**

### 2. Open in Browser

Navigate to: **http://127.0.0.1:8000**

## Using the Web UI

### Step 1: Upload Files

1. **Select Ordered Report**: Click "Select Ordered Report" and choose your CSV or XLSX file
2. **Select Sold Report**: Click "Select Sold Report" and choose your CSV or XLSX file
3. **Optional - Mapping Config**: If you have a custom mapping file (YAML/JSON), select it
4. **Click "Run Reconciliation"**

### Step 2: View Results

After processing, you'll see:

#### Summary Statistics
- Total Medicines
- Total Ordered
- Total Sold
- Total Remaining
- Shortages Count
- Issues Found

#### Data Tables (Displayed in UI)
- **Audit Issues**: Shows all audit issues found with severity badges
- **Shortages**: Medicines that were over-sold
- **Remaining Inventory**: Medicines with leftover stock

Each table shows the first 20 rows. Full data is available for download.

#### Download Links
- Remaining Inventory (CSV)
- Shortages (CSV)
- Leftovers (CSV)
- Issues (CSV)
- Audit Report (Excel) - Complete workbook with all sheets
- Summary (JSON)

### Step 3: Browse Previous Runs

Click "Previous Runs" in the navigation to see all previous reconciliation runs.

## Features

✅ **File Upload**: Drag and drop or click to select files
✅ **Real-time Processing**: See status updates during processing
✅ **Results Display**: View results directly in the browser
✅ **Data Tables**: See issues, shortages, and inventory in tables
✅ **Download Reports**: Download all outputs as CSV or Excel
✅ **Run History**: Browse and access previous runs

## File Requirements

### Ordered Report
Should contain columns like:
- `drug_name` or `Drug Name`
- `ndc` or `NDC Code`
- `quantity` or `Quantity`

### Sold Report
Should contain columns like:
- `drug_name` or `Drug Name`
- `ndc` or `NDC Code`
- `quantity_sold` or `Quantity Sold`

The system will auto-detect common column names. If your columns have different names, create a mapping configuration file.

## Troubleshooting

### Server Won't Start
- Check if port 8000 is already in use
- Try a different port: `python -m src.cli.main web --port 8080`

### Upload Fails
- Ensure files are CSV or XLSX format
- Check file size (should handle large files, but very large files may take time)
- Verify files have required columns

### No Results Displayed
- Check browser console for errors (F12)
- Verify files were processed successfully
- Check server logs for errors

## API Endpoints

The web UI uses these endpoints:

- `POST /api/upload` - Upload and validate files
- `POST /api/run` - Run reconciliation
- `GET /api/runs` - List previous runs
- `GET /api/runs/{run_id}` - Get run details
- `GET /api/download/{run_id}/{file_type}` - Download output files

## Example Workflow

1. Start server: `python -m src.cli.main web`
2. Open browser: http://127.0.0.1:8000
3. Upload `sample_data/ordered_sample.csv` as Ordered Report
4. Upload `sample_data/sold_sample.csv` as Sold Report
5. Click "Run Reconciliation"
6. View results in the browser
7. Download full reports if needed

