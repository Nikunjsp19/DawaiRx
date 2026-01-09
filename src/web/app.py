"""FastAPI application for web UI"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Depends, status
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, Response, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBearer
from fastapi.middleware.gzip import GZipMiddleware
import tempfile
import shutil
from pathlib import Path
import logging
from typing import Optional, List
import uuid
from datetime import datetime

import pandas as pd
from src.ingestion.processor import process_file, validate_inputs
from src.normalization.processor import normalize_dataframe
from src.reconciliation.engine import reconcile_inventory, generate_summary
from src.rules.implementations import create_default_registry
try:
    from src.rules.implementations_extended import create_extended_registry
    USE_EXTENDED_RULES = True
except ImportError:
    USE_EXTENDED_RULES = False
from src.reporting.excel import create_audit_report
from src.persistence.store import RunStore
from src.auth.models import UserLogin, TokenResponse, UserCreate, UserUpdate, UserUpdate
from src.auth.user_store import UserStore
from src.auth.utils import create_access_token, verify_password
from src.auth.middleware import get_current_user_id

logger = logging.getLogger(__name__)

app = FastAPI(title="DawaiRx", description="Pharmacy Audit & Reconciliation Tool")

# Add compression middleware for faster responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Pre-warm MongoDB connection on startup
@app.on_event("startup")
async def startup_event():
    """Pre-warm MongoDB connection pool on server startup"""
    try:
        logger.info("🔥 Pre-warming MongoDB connection pool...")
        from src.persistence.connection_pool import get_mongo_client
        import time
        start = time.time()
        client = get_mongo_client()
        client.server_info()  # Test connection
        elapsed = time.time() - start
        logger.info(f"✅ MongoDB connection pool pre-warmed in {elapsed:.2f}s")
    except Exception as e:
        logger.warning(f"⚠️ Could not pre-warm connection (will connect on first request): {e}")

# Add custom validation error handler to see exact errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom handler to log validation errors in detail"""
    logger.error("❌ Request validation error:")
    logger.error(f"   URL: {request.url}")
    logger.error(f"   Method: {request.method}")
    for error in exc.errors():
        logger.error(f"   Error: {error}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(await request.body())},
    )

# Setup templates
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# Static files directory
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Temporary upload directory
upload_dir = Path("uploads")
upload_dir.mkdir(exist_ok=True)

# Output directory
output_base = Path("out/web_runs")
output_base.mkdir(parents=True, exist_ok=True)


@app.get("/favicon.ico")
async def favicon():
    """Return empty favicon to prevent 404 errors"""
    return Response(status_code=204)  # No Content

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Dashboard page - check auth in frontend"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/new-report", response_class=HTMLResponse)
async def new_report_page(request: Request):
    """Start new report page - check auth in frontend"""
    return templates.TemplateResponse("new-report.html", {"request": request})


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Profile settings page - check auth in frontend"""
    return templates.TemplateResponse("settings.html", {"request": request})


@app.put("/api/auth/settings")
async def update_settings(
    user_update: UserUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """Update user settings (email and/or password)"""
    try:
        user_store = UserStore()
        
        # Verify current password if changing password
        if user_update.new_password:
            if not user_update.current_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is required to change password"
                )
            
            # Verify current password
            user = user_store.authenticate_user(user_id, user_update.current_password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Current password is incorrect"
                )
        
        # Update user
        updated_user = user_store.update_user(
            user_id=user_id,
            email=user_update.email,
            new_password=user_update.new_password
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return JSONResponse({
            "success": True,
            "message": "Settings updated successfully",
            "user_id": updated_user.user_id,
            "email": updated_user.email
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update settings"
        )


@app.post("/api/auth/login")
async def login(login_data: UserLogin):
    """Login endpoint (optimized with connection pool)"""
    try:
        # Reuse connection pool - no need to close
        user_store = UserStore()
        user = user_store.authenticate_user(login_data.user_id, login_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect user_id or password"
            )
        
        # Create access token
        access_token = create_access_token(data={"sub": user.user_id})
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.user_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@app.post("/api/auth/register")
async def register(user_data: UserCreate):
    """Register a new user"""
    try:
        user_store = UserStore()
        user = user_store.create_user(user_data)
        
        # Create access token
        access_token = create_access_token(data={"sub": user.user_id})
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.user_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@app.post("/api/upload")
async def upload_files(
    request: Request,
    user_id: str = Depends(get_current_user_id)
):
    """Upload files and validate - supports multiple ordered files (suppliers) and single inventory report"""
    try:
        # Parse multipart form data manually
        form = await request.form()
        
        logger.info(f"📥 Upload request received")
        logger.info(f"   Form keys: {list(form.keys())}")
        
        # Get ordered files (multiple)
        ordered_files = form.getlist("ordered_files")
        sold_file = form.get("sold_file")
        mapping_file = form.get("mapping_file")
        
        logger.info(f"   ordered_files: {len(ordered_files)} files")
        logger.info(f"   sold_file: {sold_file.filename if sold_file else 'None'}")
        logger.info(f"   mapping_file: {mapping_file.filename if mapping_file else 'None'}")
        
        # Validate that we received files
        if not ordered_files or len(ordered_files) == 0:
            logger.error("❌ No supplier files provided")
            raise HTTPException(status_code=400, detail="No supplier files provided")
        if not sold_file:
            logger.error("❌ No inventory report file provided")
            raise HTTPException(status_code=400, detail="No inventory report file provided")
        
        # Save uploaded files
        session_id = str(uuid.uuid4())
        session_dir = upload_dir / session_id
        session_dir.mkdir(exist_ok=True)
        
        # Save all ordered files (from suppliers)
        ordered_paths = []
        logger.info(f"💾 Saving {len(ordered_files)} supplier file(s)...")
        for i, ordered_file in enumerate(ordered_files):
            ordered_path = session_dir / f"ordered_{i}_{ordered_file.filename}"
            logger.info(f"   Saving supplier file {i+1}: {ordered_file.filename} -> {ordered_path.name}")
            # Read file content
            file_content = await ordered_file.read()
            with open(ordered_path, "wb") as f:
                f.write(file_content)
            ordered_paths.append(str(ordered_path))
        
        # Save single inventory report (sold file)
        sold_path = session_dir / sold_file.filename
        logger.info(f"💾 Saving inventory report: {sold_file.filename} -> {sold_path.name}")
        # Read file content
        sold_content = await sold_file.read()
        with open(sold_path, "wb") as f:
            f.write(sold_content)
        
        mapping_path = None
        if mapping_file:
            mapping_path = session_dir / mapping_file.filename
            mapping_content = await mapping_file.read()
            with open(mapping_path, "wb") as f:
                f.write(mapping_content)
        
        # Validate files - combine ordered files for validation
        from src.ingestion.processor import process_file
        import pandas as pd
        
        # Process and combine ordered files (suppliers)
        ordered_dfs = []
        total_ordered_rows = 0
        ordered_errors = []
        ordered_warnings = []
        
        logger.info(f"🔍 Validating {len(ordered_paths)} supplier file(s)...")
        for ordered_path in ordered_paths:
            try:
                logger.info(f"   Processing: {Path(ordered_path).name}")
                result = process_file(ordered_path, "ordered", None)
                ordered_dfs.append(result["dataframe"])
                total_ordered_rows += len(result["dataframe"])
                logger.info(f"   ✅ Valid: {len(result['dataframe'])} rows")
            except Exception as e:
                logger.error(f"   ❌ Error: {str(e)}")
                ordered_errors.append(f"Error processing {Path(ordered_path).name}: {str(e)}")
        
        # Validate inventory report (sold file)
        logger.info(f"🔍 Validating inventory report: {sold_path.name}")
        sold_result = process_file(str(sold_path), "sold", None)
        logger.info(f"   ✅ Valid: {sold_result['stats']['row_count']} rows, errors: {len(sold_result['validation']['errors'])}")
        
        # Combine ordered DataFrames if multiple
        combined_ordered_df = None
        if ordered_dfs:
            combined_ordered_df = pd.concat(ordered_dfs, ignore_index=True)
            logger.info(f"📊 Combined {len(ordered_dfs)} supplier files: {len(combined_ordered_df)} total rows")
        
        logger.info(f"✅ Upload validation complete:")
        logger.info(f"   Supplier files: {len(ordered_paths)} files, {total_ordered_rows} rows, {len(ordered_errors)} errors")
        logger.info(f"   Inventory report: {sold_result['stats']['row_count']} rows, valid: {sold_result['validation']['valid']}")
        
        return JSONResponse({
            "success": len(ordered_errors) == 0 and sold_result["validation"]["valid"],
            "session_id": session_id,
            "validation": {
                "ordered": {
                    "valid": len(ordered_errors) == 0,
                    "row_count": total_ordered_rows,
                    "file_count": len(ordered_paths),
                    "errors": ordered_errors,
                    "warnings": ordered_warnings,
                },
                "sold": {
                    "valid": sold_result["validation"]["valid"],
                    "row_count": sold_result["stats"]["row_count"],
                    "errors": sold_result["validation"]["errors"],
                    "warnings": sold_result["validation"]["warnings"],
                },
            }
        })
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.exception("❌ Upload failed with exception")
        logger.error(f"   Error type: {type(e).__name__}")
        logger.error(f"   Error message: {str(e)}")
        # Provide more detailed error message
        error_detail = str(e)
        if hasattr(e, '__cause__') and e.__cause__:
            error_detail += f": {str(e.__cause__)}"
        raise HTTPException(status_code=500, detail=error_detail)


@app.post("/api/run")
async def run_comparison(
    session_id: str = Form(...),
    mapping_file: Optional[UploadFile] = File(None),
    date_from: Optional[str] = Form(None),
    date_to: Optional[str] = Form(None),
    report_name: Optional[str] = Form(None),
    user_id: str = Depends(get_current_user_id)
):
    """Run reconciliation"""
    import time
    start_time = time.time()
    logger.info(f"🚀 Starting reconciliation for user {user_id}, session {session_id}")
    logger.info(f"   Request received at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        session_dir = upload_dir / session_id
        if not session_dir.exists():
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Find uploaded files
        all_files = list(session_dir.glob("*"))
        ordered_paths = []
        sold_path = None
        
        # Find ordered files (starting with "ordered_") and sold file (inventory report)
        for f in all_files:
            if f.is_file() and f.suffix.lower() in ['.csv', '.xlsx', '.xls']:
                if f.name.startswith("ordered_"):
                    ordered_paths.append(f)
                elif not f.name.startswith("ordered_") and sold_path is None:
                    # This is the inventory report (sold file)
                    sold_path = f
        
        # Sort ordered paths to maintain order
        ordered_paths.sort()
        
        if not ordered_paths or not sold_path:
            raise HTTPException(status_code=400, detail="Could not find uploaded files")
        
        # Handle mapping file if provided
        mapping_path = None
        if mapping_file:
            mapping_path = session_dir / mapping_file.filename
            with open(mapping_path, "wb") as f:
                shutil.copyfileobj(mapping_file.file, f)
        
        # Process and combine all ordered files (suppliers)
        import pandas as pd
        ordered_dfs = []
        for ordered_path in ordered_paths:
            ordered_result = process_file(str(ordered_path), "ordered", None)
            ordered_df = ordered_result["dataframe"]
            
            # Extract supplier name from filename
            # Format: ordered_0_filename.csv -> extract supplier name from filename
            # Examples: "1.akron_generics.csv" -> "AKRON GENERICS"
            #           "2_alpine_health.csv" -> "ALPINE HEALTH"
            filename = ordered_path.stem  # Remove extension
            # Remove "ordered_X_" prefix if present
            if filename.startswith("ordered_"):
                parts = filename.split("_", 2)
                if len(parts) >= 3:
                    filename = parts[2]
            
            # Clean up supplier name: remove numbers, underscores, dots
            supplier_name = filename.replace("_", " ").replace(".", " ").replace("-", " ")
            # Remove leading numbers and spaces
            supplier_name = " ".join([w for w in supplier_name.split() if not w.isdigit()])
            supplier_name = supplier_name.strip().upper()
            
            # If empty, use filename
            if not supplier_name:
                supplier_name = filename.upper()
            
            # Add supplier_name column
            ordered_df["supplier_name"] = supplier_name
            logger.info(f"Processed supplier file: {ordered_path.name} -> supplier: {supplier_name} ({len(ordered_df)} rows)")
            ordered_dfs.append(ordered_df)
        
        # Combine all ordered DataFrames (from multiple suppliers)
        if len(ordered_dfs) > 1:
            ordered_df = pd.concat(ordered_dfs, ignore_index=True)
            logger.info(f"Combined {len(ordered_dfs)} supplier files: {len(ordered_df)} total rows")
        else:
            ordered_df = ordered_dfs[0] if ordered_dfs else pd.DataFrame()
        
        # Track all supplier names BEFORE date filtering (for BatchRX report)
        all_supplier_names = ordered_df["supplier_name"].dropna().unique().tolist() if "supplier_name" in ordered_df.columns else []
        logger.info(f"📋 All suppliers (before date filtering): {all_supplier_names}")
        
        ordered_normalized = normalize_dataframe(ordered_df, "ordered")
        
        # Process single inventory report (sold file)
        sold_result = process_file(str(sold_path), "sold", None)
        sold_df = sold_result["dataframe"]
        logger.info(f"Processed inventory report: {sold_path.name} ({len(sold_df)} rows)")
        
        sold_normalized = normalize_dataframe(sold_df, "sold")
        
        # Apply date range filter if provided
        if date_from or date_to:
            from datetime import datetime
            import pandas as pd
            
            # Parse date strings
            date_from_dt = None
            date_to_dt = None
            
            if date_from:
                try:
                    date_from_dt = pd.to_datetime(date_from).normalize()
                    logger.info(f"Date filter FROM: {date_from_dt}")
                except Exception as e:
                    logger.warning(f"Invalid date_from format: {date_from}, error: {e}")
            
            if date_to:
                try:
                    date_to_dt = pd.to_datetime(date_to).normalize()
                    # Include the entire end date (set to end of day)
                    date_to_dt = date_to_dt + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                    logger.info(f"Date filter TO: {date_to_dt}")
                except Exception as e:
                    logger.warning(f"Invalid date_to format: {date_to}, error: {e}")
            
            # Filter sold data by claim_date
            if "claim_date" in sold_normalized.columns:
                rows_before = len(sold_normalized)
                if date_from_dt is not None:
                    sold_normalized = sold_normalized[sold_normalized["claim_date"] >= date_from_dt]
                if date_to_dt is not None:
                    sold_normalized = sold_normalized[sold_normalized["claim_date"] <= date_to_dt]
                rows_after = len(sold_normalized)
                logger.info(f"   Filtered sold data by date range: {rows_before} → {rows_after} rows (removed {rows_before - rows_after} rows)")
                if rows_after == 0 and rows_before > 0:
                    logger.warning(f"   ⚠️ WARNING: Date filter removed ALL sold data! Date range: {date_from} to {date_to}")
                    logger.warning(f"   Consider adjusting the date range or leaving it empty to include all data.")
            else:
                logger.warning("   No claim_date column in sold data - cannot apply date filter")
            
            # Filter ordered data by order_date, invoice_date, or other date columns
            # CRITICAL: This must happen BEFORE processing to exclude orders outside date range
            date_col_ordered = None
            # Check for order_date first (preferred), then invoice_date, then other date fields
            for col in ["order_date", "invoice_date", "purchase_date", "claim_date", "date_filled", "fill_date"]:
                if col in ordered_normalized.columns:
                    date_col_ordered = col
                    break
            
            if date_col_ordered:
                rows_before = len(ordered_normalized)
                # Filter out rows where date is None/NaN (can't determine if in range)
                ordered_normalized = ordered_normalized[ordered_normalized[date_col_ordered].notna()]
                
                if date_from_dt is not None:
                    ordered_normalized = ordered_normalized[ordered_normalized[date_col_ordered] >= date_from_dt]
                if date_to_dt is not None:
                    ordered_normalized = ordered_normalized[ordered_normalized[date_col_ordered] <= date_to_dt]
                rows_after = len(ordered_normalized)
                logger.info(f"   ✅ Filtered ordered data by date range ({date_col_ordered}): {rows_before} → {rows_after} rows (removed {rows_before - rows_after} rows outside {date_from or 'start'} to {date_to or 'end'})")
                if rows_after == 0 and rows_before > 0:
                    logger.warning(f"   ⚠️ WARNING: Date filter removed ALL ordered data! Date range: {date_from} to {date_to}")
                    logger.warning(f"   Consider adjusting the date range or leaving it empty to include all data.")
            else:
                logger.warning("   ⚠️  No date column found in ordered data - cannot apply date filter. All ordered data will be included.")
        
        # Reconcile
        reconciled = reconcile_inventory(ordered_normalized, sold_normalized)
        
        # Warn if reconciliation produced no results
        if len(reconciled) == 0:
            logger.warning("⚠️ WARNING: Reconciliation produced 0 rows!")
            logger.warning(f"   Ordered data: {len(ordered_normalized)} rows")
            logger.warning(f"   Sold data: {len(sold_normalized)} rows")
            if date_from or date_to:
                logger.warning(f"   This may be due to date filtering. Consider removing date filters or adjusting the range.")
        
        summary = generate_summary(reconciled)
        
        # Run rules (use extended if available)
        if USE_EXTENDED_RULES:
            rule_registry = create_extended_registry()
        else:
            rule_registry = create_default_registry()
        issues = rule_registry.run_all({
            "ordered": ordered_normalized,
            "sold": sold_normalized,
            "reconciled": reconciled,
        })
        
        issues_df = pd.DataFrame(issues) if issues else pd.DataFrame()
        
        # Generate outputs with date_time format (YYYYMMDD_HHMMSS)
        # Add microseconds to ensure uniqueness if multiple runs in same second
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds (last 3 digits of microseconds)
        run_id = timestamp
        output_dir = output_base / run_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save CSV outputs
        remaining = reconciled[reconciled["leftover_qty"] > 0]
        remaining.to_csv(output_dir / "remaining_inventory.csv", index=False)
        
        shortages = reconciled[reconciled["shortage_qty"] > 0]
        shortages.to_csv(output_dir / "shortages.csv", index=False)
        
        leftovers = reconciled[reconciled["leftover_qty"] > 0]
        leftovers.to_csv(output_dir / "leftovers.csv", index=False)
        
        if len(issues_df) > 0:
            issues_df.to_csv(output_dir / "issues.csv", index=False)
        
        # Save processed source data for medicine detail queries
        # Save ordered data with supplier information
        ordered_normalized.to_csv(output_dir / "source_ordered.csv", index=False)
        # Save sold data (inventory report)
        sold_normalized.to_csv(output_dir / "source_sold.csv", index=False)
        
        # Save summary
        summary_with_issues = summary.copy()
        summary_with_issues["total_issues"] = len(issues_df)
        summary_with_issues["issues_by_severity"] = {
            "high": int((issues_df["severity"] == "high").sum()) if len(issues_df) > 0 else 0,
            "medium": int((issues_df["severity"] == "medium").sum()) if len(issues_df) > 0 else 0,
            "low": int((issues_df["severity"] == "low").sum()) if len(issues_df) > 0 else 0,
        }
        
        import json
        with open(output_dir / "summary.json", 'w') as f:
            json.dump(summary_with_issues, f, indent=2)
        
        # Generate BatchRx-style unified report (main output)
        batchrx_report = None
        try:
            from src.reporting.batchrx_format import create_batchrx_report
            logger.info("🔄 Starting BatchRx report generation...")
            logger.info(f"   Reconciled: {len(reconciled)} rows, columns: {list(reconciled.columns)[:10]}")
            logger.info(f"   Sold normalized: {len(sold_normalized)} rows, columns: {list(sold_normalized.columns)[:10]}")
            logger.info(f"   Ordered normalized: {len(ordered_normalized)} rows, columns: {list(ordered_normalized.columns)[:10]}")
            
            # Debug: Check if medicine_key exists
            if "medicine_key" not in reconciled.columns:
                logger.error(f"❌ medicine_key missing in reconciled. Available columns: {list(reconciled.columns)}")
                # Try to create medicine_key if ndc exists
                if "ndc" in reconciled.columns:
                    logger.info("   Creating medicine_key from ndc...")
                    reconciled["medicine_key"] = reconciled["ndc"].astype(str)
                else:
                    raise ValueError("Neither medicine_key nor ndc found in reconciled DataFrame")
            
            logger.info(f"📋 Passing {len(all_supplier_names) if all_supplier_names else 0} suppliers to create_batchrx_report: {all_supplier_names}")
            
            # DEBUG: Check sold_normalized data for specific NDC before calling create_batchrx_report
            test_ndc = 'NDC:00536129497'
            test_rows = sold_normalized[sold_normalized['medicine_key'] == test_ndc] if 'medicine_key' in sold_normalized.columns else pd.DataFrame()
            if len(test_rows) > 0:
                primary_sum = test_rows['primary_insurance_paid'].sum() if 'primary_insurance_paid' in test_rows.columns else 0
                secondary_sum = test_rows['secondary_insurance_paid'].sum() if 'secondary_insurance_paid' in test_rows.columns else 0
                total = primary_sum + secondary_sum
                import numpy as np
                floor_val = int(np.floor(total))
                logger.info(f"🔍 DEBUG: Before create_batchrx_report - NDC {test_ndc}: total={total}, floor={floor_val}, expected=11")
            
            batchrx_report = create_batchrx_report(
                str(output_dir / "inventory_report.csv"),
                reconciled,
                sold_normalized,
                ordered_normalized,
                summary_with_issues,
                all_supplier_names=all_supplier_names  # Pass all suppliers (before date filtering)
            )
            
            # DEBUG: Check result after create_batchrx_report
            if 'NDC' in batchrx_report.columns:
                test_result = batchrx_report[batchrx_report['NDC'] == '00536-1294-97']
                if len(test_result) > 0:
                    amount_val = test_result['AMOUNT'].values[0]
                    logger.info(f"🔍 DEBUG: After create_batchrx_report - NDC 00536-1294-97: AMOUNT={amount_val}, expected=11")
            logger.info(f"✅ Created BatchRx-style report: {len(batchrx_report)} rows, {len(batchrx_report.columns)} columns")
        except Exception as e:
            logger.error(f"❌ BatchRx report generation failed: {e}", exc_info=True)
            import traceback
            logger.error(traceback.format_exc())
            batchrx_report = None
        
        # Generate Excel report (legacy format)
        create_audit_report(str(output_dir / "audit_report.xlsx"), reconciled, issues_df, summary_with_issues)
        
        # Generate PDF report (detailed)
        try:
            from src.reporting.pdf import create_detailed_pdf_report
            create_detailed_pdf_report(
                str(output_dir / "audit_report_detailed.pdf"),
                reconciled,
                issues_df,
                summary_with_issues,
                ordered_normalized,
                sold_normalized
            )
        except Exception as e:
            logger.warning(f"PDF generation failed: {e}")
        
        # Save to MongoDB - use the same run_id for consistency
        try:
            store = RunStore()
            # Prepare config metadata with date range and report name
            config_metadata = {
                "date_from": date_from,
                "date_to": date_to,
                "report_name": report_name,
                "session_id": session_id,  # Save session_id to allow source file regeneration
            }
            # Save with the same run_id used for file paths
            saved_run_id = store.save_run(
                user_id=user_id,
                ordered_file=str(ordered_path),
                sold_file=str(sold_path),
                mapping_file=str(mapping_path) if mapping_path else None,
                reconciled_df=reconciled,
                issues=issues,
                summary=summary_with_issues,
                run_id=run_id,  # Use the same run_id as file paths
                config_metadata=config_metadata
            )
            logger.info(f"✅ Saved run to MongoDB with run_id: {saved_run_id}")
        except Exception as e:
            logger.warning(f"Failed to save to MongoDB: {e}")
            saved_run_id = run_id  # Fallback to original run_id
        
        # Convert BatchRx report to JSON for UI display (limit to first 100 rows for performance)
        batchrx_json = None
        batchrx_row_count = 0
        batchrx_columns = []
        
        logger.info(f"🔍 Checking BatchRx report: is None={batchrx_report is None}, length={len(batchrx_report) if batchrx_report is not None else 'N/A'}")
        
        if batchrx_report is not None and len(batchrx_report) > 0:
            try:
                batchrx_row_count = len(batchrx_report)
                logger.info(f"📊 Processing BatchRx report for UI: {batchrx_row_count} rows, {len(batchrx_report.columns)} columns")
                # Convert to dict for JSON serialization - send FULL report (no limit)
                # Use vectorized operations for speed
                # Replace 0 values with NaN (will be converted to empty string/null for UI)
                # BatchRX shows blank cells for 0 values
                batchrx_full = batchrx_report.copy()
                # Replace 0 and 0.0 with NaN (will show as blank in UI)
                batchrx_full = batchrx_full.replace(0, pd.NA)
                batchrx_full = batchrx_full.replace(0.0, pd.NA)
                # Replace inf values with NaN
                batchrx_full = batchrx_full.replace([float('inf'), float('-inf')], pd.NA)
                # Fill remaining NaN with empty string for string columns, keep NaN for numeric (will be null in JSON)
                batchrx_full = batchrx_full.fillna('')
                # Convert to dict (much faster than manual loops)
                # Limit to first 1000 rows for performance - large reports can hang the browser
                max_rows_for_ui = 1000
                if len(batchrx_full) > max_rows_for_ui:
                    logger.warning(f"⚠️ BatchRx report has {len(batchrx_full)} rows, limiting to {max_rows_for_ui} for UI")
                    batchrx_full = batchrx_full.head(max_rows_for_ui)
                
                logger.info(f"📊 Converting {len(batchrx_full)} rows to JSON...")
                convert_start = time.time()
                batchrx_json = batchrx_full.to_dict(orient='records')
                logger.info(f"✅ JSON conversion took {time.time() - convert_start:.2f}s")
                
                # Cleanup: convert empty strings back to null for numeric columns (shows as blank in UI)
                import numpy as np
                numeric_cols = batchrx_report.select_dtypes(include=['number']).columns
                cleanup_start = time.time()
                for record in batchrx_json:
                    for col in numeric_cols:
                        if col in record:
                            # Convert empty string to null for numeric columns (shows as blank)
                            if record[col] == '' or record[col] == 'nan' or pd.isna(record[col]):
                                record[col] = None
                            elif isinstance(record[col], (int, float)) and (pd.isna(record[col]) or np.isinf(record[col])):
                                record[col] = None
                logger.info(f"✅ Cleanup took {time.time() - cleanup_start:.2f}s")
                # Get column names
                batchrx_columns = list(batchrx_report.columns)
                logger.info(f"✅ BatchRx report ready for UI: {len(batchrx_json)} rows (FULL report), {len(batchrx_columns)} columns")
                logger.info(f"   First row sample: {batchrx_json[0] if batchrx_json else 'empty'}")
            except Exception as e:
                logger.error(f"❌ Failed to process BatchRx report for UI: {e}", exc_info=True)
                batchrx_json = None
                batchrx_columns = []
                batchrx_row_count = 0
        else:
            logger.warning(f"⚠️ BatchRx report is None or empty - will not show in UI")
            logger.error(f"❌ BatchRx report generation failed - check logs above for details")
            # Don't add fallback - we want BatchRx report to work, not show sample data
        
        # Prepare response with data for UI display
        response_data = {
            "success": True,
            "run_id": run_id,
            "saved_run_id": saved_run_id,
            "summary": summary_with_issues,
            "batchrx_report": batchrx_json,  # BatchRx report data for UI
            "batchrx_columns": batchrx_columns,
            "batchrx_row_count": batchrx_row_count,
        }
        
        # Log what we're sending
        logger.info(f"📤 Sending response to UI:")
        logger.info(f"   batchrx_report: {type(batchrx_json)}, length: {len(batchrx_json) if batchrx_json else 0}")
        logger.info(f"   batchrx_columns: {len(batchrx_columns)} columns")
        logger.info(f"   batchrx_row_count: {batchrx_row_count}")
        if batchrx_json and len(batchrx_json) > 0:
            logger.info(f"   First row keys: {list(batchrx_json[0].keys())[:5]}...")
        
        # Add sample data for UI display (first 20 rows of each) - keep for reference
        # Add counts only (not sample data - we want full BatchRx report)
        response_data["remaining_count"] = len(remaining)
        response_data["shortages_count"] = len(shortages)
        response_data["issues_count"] = len(issues_df)
        response_data["rules_count"] = len(rule_registry.get_all_rules())
        
        total_elapsed = time.time() - start_time
        logger.info(f"✅ Reconciliation completed in {total_elapsed:.2f}s")
        logger.info(f"   Run ID: {run_id}")
        logger.info(f"   BatchRx rows: {batchrx_row_count}")
        
        return JSONResponse(response_data)
        
    except Exception as e:
        elapsed = time.time() - start_time if 'start_time' in locals() else 0
        logger.error(f"❌ Run failed after {elapsed:.2f}s: {e}")
        logger.exception("Run failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/runs")
async def list_runs(
    limit: int = 10,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id)
):
    """List recent runs for authenticated user with pagination"""
    import time
    request_start = time.time()
    
    try:
        # Initialize RunStore (connection pool should already be warm)
        try:
            store = RunStore()
        except Exception as init_error:
            logger.error(f"❌ Failed to initialize RunStore: {init_error}")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
            return JSONResponse({"runs": [], "total": 0, "limit": limit, "offset": offset})
        
        # Call list_runs with pagination
        try:
            runs = store.list_runs(user_id=user_id, limit=limit, offset=offset)
            # Get total count for pagination (with timeout protection)
            try:
                total_count = store.count_runs(user_id=user_id)
            except Exception as count_error:
                logger.warning(f"⚠️ Failed to count runs, using list length: {count_error}")
                total_count = len(runs)  # Fallback to list length
            logger.info(f"📊 /api/runs: user={user_id}, limit={limit}, offset={offset}, runs={len(runs)}, total={total_count}")
        except Exception as db_error:
            logger.error(f"❌ Database query failed: {db_error}")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
            runs = []
            total_count = 0
        
        total_elapsed = time.time() - request_start
        
        # Log only if slow
        if total_elapsed > 2.0:
            logger.warning(f"⚠️ Slow /api/runs: {total_elapsed:.2f}s for user {user_id}")
        
        return JSONResponse({
            "runs": runs,
            "total": total_count,
            "limit": limit,
            "offset": offset
        })
    except HTTPException:
        # Re-raise HTTP exceptions (like 401 Unauthorized)
        raise
    except Exception as e:
        logger.error(f"❌ Error in /api/runs: {e}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        # Always return empty list - never fail the request
        return JSONResponse({"runs": [], "total": 0, "limit": limit, "offset": offset})


@app.delete("/api/runs/{run_id}")
async def delete_run(run_id: str, user_id: str = Depends(get_current_user_id)):
    """Delete a run and all associated data for authenticated user"""
    try:
        store = RunStore()
        success = store.delete_run(user_id=user_id, run_id=run_id)
        
        if success:
            return {"success": True, "message": f"Run {run_id} deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run {run_id} not found or you don't have permission to delete it"
            )
    except Exception as e:
        logger.error(f"Error deleting run {run_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete run: {str(e)}"
        )

@app.get("/api/runs/{run_id}")
async def get_run(run_id: str, user_id: str = Depends(get_current_user_id)):
    """Get run details for authenticated user"""
    try:
        store = RunStore()
        run = store.get_run(user_id=user_id, run_id=run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Don't load items/issues - not needed for viewing report (saves time)
        
        # Check if BatchRx report exists and get metadata only (fast)
        batchrx_columns = []
        batchrx_row_count = 0
        batchrx_report = None
        
        try:
            # Files are stored in out/web_runs/{run_id}/
            batchrx_file = output_base / run_id / "inventory_report.csv"
            # Fallback check - output_base already includes "web_runs"
            if not batchrx_file.exists():
                # Try direct path as fallback
                batchrx_file = Path("out") / run_id / "inventory_report.csv"
            if batchrx_file.exists():
                import pandas as pd
                # Only read first row to get columns (very fast)
                df_sample = pd.read_csv(batchrx_file, nrows=1)
                batchrx_columns = list(df_sample.columns)
                
                # Get row count efficiently (read only first column)
                with open(batchrx_file, 'r') as f:
                    batchrx_row_count = sum(1 for line in f) - 1  # -1 for header
                
                # Load FULL report (not just preview) for viewing
                # Use chunking for large files to avoid memory issues
                try:
                    df_full = pd.read_csv(batchrx_file)
                    logger.info(f"📊 Loading full report: {len(df_full)} rows")
                except MemoryError:
                    logger.warning(f"⚠️ Memory error loading full report, using chunked approach")
                    # Fallback: load in chunks and combine
                    chunk_list = []
                    for chunk in pd.read_csv(batchrx_file, chunksize=1000):
                        chunk_list.append(chunk)
                    df_full = pd.concat(chunk_list, ignore_index=True)
                
                # Replace 0 values with NaN (will show as blank in UI, matching BatchRX)
                df_full = df_full.replace(0, pd.NA)
                df_full = df_full.replace(0.0, pd.NA)
                # Fill NaN with empty string, then convert to dict
                df_full = df_full.fillna('')
                batchrx_report = df_full.to_dict(orient='records')
                
                # Quick cleanup for all rows - convert empty strings to null for numeric columns
                import numpy as np
                numeric_cols = df_full.select_dtypes(include=['number']).columns
                for record in batchrx_report:
                    for key, value in record.items():
                        if key in numeric_cols:
                            # Convert empty string to null for numeric columns (shows as blank)
                            if value == '' or value == 'nan' or pd.isna(value):
                                record[key] = None
                            elif isinstance(value, (int, float)) and (pd.isna(value) or np.isinf(value)):
                                record[key] = None
                        elif pd.isna(value):
                            record[key] = ""
                
                logger.info(f"✅ Loaded BatchRx report: {len(batchrx_report)} rows (full report), {len(batchrx_columns)} columns")
        except Exception as e:
            logger.warning(f"Could not load BatchRx report for run {run_id}: {e}")
        
        return JSONResponse({
            "run": run,
            "batchrx_report": batchrx_report,
            "batchrx_columns": batchrx_columns,
            "batchrx_row_count": batchrx_row_count,
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get run")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/{run_id}/{file_type}")
async def download_file(run_id: str, file_type: str, user_id: str = Depends(get_current_user_id)):
    """Download output file for authenticated user"""
    try:
        # Verify user owns this run
        store = RunStore()
        run = store.get_run(user_id=user_id, run_id=run_id)
        
        if not run:
            logger.error(f"Run {run_id} not found for user {user_id}")
            raise HTTPException(status_code=404, detail="Run not found")
        
        logger.info(f"Downloading file for run_id: {run_id}, file_type: {file_type}")
        
        # Get report name from run document if available
        report_name = None
        if run and "config_summary" in run and "report_name" in run["config_summary"]:
            report_name = run["config_summary"]["report_name"]
            logger.info(f"Found report name: {report_name}")
        
        # Sanitize report name for filename (remove invalid characters)
        def sanitize_filename(name):
            if not name:
                return None
            # Remove or replace invalid filename characters
            import re
            # Replace invalid characters with underscore
            sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
            # Remove leading/trailing spaces and dots
            sanitized = sanitized.strip(' .')
            # Limit length
            if len(sanitized) > 100:
                sanitized = sanitized[:100]
            return sanitized if sanitized else None
        
        sanitized_report_name = sanitize_filename(report_name)
        
        # Files are stored in out/web_runs/{run_id}/
        # output_base is already "out/web_runs", so just use output_base / run_id
        file_path = None
        filename = None
        
        # Map file_type to actual file paths and generate user-friendly filename
        if file_type == "inventory_report":
            file_path = output_base / run_id / "inventory_report.csv"
            if sanitized_report_name:
                filename = f"{sanitized_report_name}.csv"
            else:
                filename = "inventory_report.csv"
        elif file_type == "audit_report":
            file_path = output_base / run_id / "audit_report.xlsx"
            if sanitized_report_name:
                filename = f"{sanitized_report_name}.xlsx"
            else:
                filename = "audit_report.xlsx"
        elif file_type in ("audit_report_pdf", "audit_report_detailed"):
            file_path = output_base / run_id / "audit_report_detailed.pdf"
            if sanitized_report_name:
                filename = f"{sanitized_report_name}.pdf"
            else:
                filename = "audit_report_detailed.pdf"
        elif file_type == "summary":
            file_path = output_base / run_id / "summary.json"
            if sanitized_report_name:
                filename = f"{sanitized_report_name}_summary.json"
            else:
                filename = "summary.json"
        else:
            # Fallback: try as-is
            file_path = output_base / run_id / f"{file_type}"
            if sanitized_report_name and file_path.suffix:
                filename = f"{sanitized_report_name}{file_path.suffix}"
            else:
                filename = file_path.name
        
        if not file_path or not file_path.exists():
            logger.error(f"File not found: {file_path}")
            raise HTTPException(status_code=404, detail=f"File not found: {file_type}")
        
        # Determine media type based on file extension
        if file_path.suffix == ".pdf":
            media_type = "application/pdf"
        elif file_path.suffix == ".xlsx":
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif file_path.suffix == ".csv":
            media_type = "text/csv"
        elif file_path.suffix == ".json":
            media_type = "application/json"
        else:
            media_type = "application/octet-stream"
        
        logger.info(f"Downloading file: {filename} (path: {file_path}, media_type: {media_type})")
        
        # Return FileResponse with proper headers to force download (not open in browser)
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Download failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/runs/{run_id}/medicine/{medicine_identifier}")
async def get_medicine_entries(
    run_id: str,
    medicine_identifier: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get source entries for a specific medicine from uploaded files"""
    try:
        # Verify user owns this run
        store = RunStore()
        run = store.get_run(user_id=user_id, run_id=run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Load source data files
        ordered_file = output_base / run_id / "source_ordered.csv"
        sold_file = output_base / run_id / "source_sold.csv"
        
        # If source files don't exist, try to regenerate them from original uploaded files
        if not ordered_file.exists() or not sold_file.exists():
            logger.info(f"Source files not found for run {run_id}, attempting to regenerate...")
            
            # Get session_id from run config
            session_id = None
            if hasattr(run, 'config_summary') and isinstance(run.config_summary, dict):
                session_id = run.config_summary.get('session_id')
            
            # Fallback: try to extract session_id from file paths in input_metadata
            if not session_id and hasattr(run, 'input_metadata') and isinstance(run.input_metadata, dict):
                # Try to extract session_id from file paths (uploads/{session_id}/...)
                ordered_file_path = run.input_metadata.get('ordered_file_path', '')
                if ordered_file_path and 'uploads' in ordered_file_path:
                    # Extract session_id from path like "uploads/{session_id}/ordered_..."
                    path_parts = Path(ordered_file_path).parts
                    if 'uploads' in path_parts:
                        uploads_idx = path_parts.index('uploads')
                        if uploads_idx + 1 < len(path_parts):
                            session_id = path_parts[uploads_idx + 1]
                            logger.info(f"Extracted session_id from file path: {session_id}")
            
            # Debug logging
            logger.info(f"Looking for session_id for run {run_id}: found={bool(session_id)}")
            
            if session_id:
                session_dir = upload_dir / session_id
                if session_dir.exists():
                    try:
                        # Find uploaded files
                        all_files = list(session_dir.glob("*"))
                        ordered_paths = []
                        sold_path = None
                        
                        for f in all_files:
                            if f.is_file() and f.suffix.lower() in ['.csv', '.xlsx', '.xls']:
                                if f.name.startswith("ordered_"):
                                    ordered_paths.append(f)
                                elif not f.name.startswith("ordered_") and sold_path is None:
                                    sold_path = f
                        
                        if ordered_paths and sold_path:
                            # Process files to regenerate source data
                            from src.ingestion.processor import process_file
                            from src.normalization.processor import normalize_dataframe
                            
                            # Process ordered files
                            ordered_dfs = []
                            for ordered_path in sorted(ordered_paths):
                                ordered_result = process_file(str(ordered_path), "ordered", None)
                                ordered_dfs.append(ordered_result["dataframe"])
                            
                            ordered_df = pd.concat(ordered_dfs, ignore_index=True)
                            ordered_normalized = normalize_dataframe(ordered_df, "ordered")
                            
                            # Process sold file
                            sold_result = process_file(str(sold_path), "sold", None)
                            sold_df = sold_result["dataframe"]
                            sold_normalized = normalize_dataframe(sold_df, "sold")
                            
                            # Save regenerated source files
                            output_dir = output_base / run_id
                            output_dir.mkdir(parents=True, exist_ok=True)
                            ordered_normalized.to_csv(ordered_file, index=False)
                            sold_normalized.to_csv(sold_file, index=False)
                            logger.info(f"✅ Regenerated source files for run {run_id}")
                        else:
                            raise HTTPException(status_code=404, detail="Source data files not found and cannot be regenerated (original files missing)")
                    except Exception as e:
                        logger.exception(f"Failed to regenerate source files for run {run_id}")
                        raise HTTPException(status_code=404, detail=f"Source data files not found and could not be regenerated: {str(e)}")
                else:
                    raise HTTPException(status_code=404, detail="Source data files not found (original upload session no longer available)")
            else:
                raise HTTPException(status_code=404, detail="Source data files not found (this appears to be an older report without source data)")
        
        # Load DataFrames
        ordered_df = pd.read_csv(ordered_file)
        sold_df = pd.read_csv(sold_file)
        
        # Parse medicine identifier (could be NDC, medicine_key, or drug_name)
        from src.normalization.medicine_key import extract_medicine_key_components, generate_medicine_key
        from src.normalization.ndc import normalize_ndc
        
        # Try to identify the medicine
        medicine_key = None
        if medicine_identifier.startswith("NDC:"):
            medicine_key = medicine_identifier
        elif medicine_identifier.startswith("COMPOSITE:"):
            medicine_key = medicine_identifier
        else:
            # Try to normalize as NDC (handles both display format like "00003-0894-21" and raw format)
            normalized_ndc = normalize_ndc(medicine_identifier)
            if normalized_ndc:
                medicine_key = f"NDC:{normalized_ndc}"
            else:
                # Try to find matching medicine_key in the data
                if "medicine_key" in ordered_df.columns:
                    matching_keys = ordered_df[ordered_df["medicine_key"] == medicine_identifier]["medicine_key"].unique()
                    if len(matching_keys) > 0:
                        medicine_key = matching_keys[0]
                    else:
                        # Try to find by NDC (in case identifier is NDC in different format)
                        if "ndc" in ordered_df.columns and normalized_ndc:
                            # Normalize all NDCs in the dataframe for comparison
                            ordered_df_normalized = ordered_df.copy()
                            ordered_df_normalized["ndc_normalized"] = ordered_df_normalized["ndc"].apply(
                                lambda x: normalize_ndc(str(x)) if pd.notna(x) else None
                            )
                            matching = ordered_df_normalized[ordered_df_normalized["ndc_normalized"] == normalized_ndc]
                            if len(matching) > 0:
                                medicine_key = matching["medicine_key"].iloc[0]
                
                # If still not found, try in sold_df
                if not medicine_key and "medicine_key" in sold_df.columns:
                    matching_keys = sold_df[sold_df["medicine_key"] == medicine_identifier]["medicine_key"].unique()
                    if len(matching_keys) > 0:
                        medicine_key = matching_keys[0]
                    else:
                        # Try to find by drug_name (case-insensitive partial match)
                        if "drug_name" in sold_df.columns:
                            matching = sold_df[sold_df["drug_name"].str.contains(medicine_identifier, case=False, na=False)]
                            if len(matching) > 0:
                                medicine_key = matching["medicine_key"].iloc[0]
                        # Also try in ordered_df
                        if not medicine_key and "drug_name" in ordered_df.columns:
                            matching = ordered_df[ordered_df["drug_name"].str.contains(medicine_identifier, case=False, na=False)]
                            if len(matching) > 0:
                                medicine_key = matching["medicine_key"].iloc[0]
        
        if not medicine_key:
            raise HTTPException(status_code=404, detail=f"Medicine not found: {medicine_identifier}")
        
        # Filter entries by medicine_key
        ordered_entries = ordered_df[ordered_df["medicine_key"] == medicine_key].copy()
        sold_entries = sold_df[sold_df["medicine_key"] == medicine_key].copy()
        
        # Convert to list of dictionaries for JSON response
        def format_entry(row, source_type, source_name):
            """Format a row as an entry dictionary"""
            entry = {
                "source_type": source_type,  # "ordered" or "sold"
                "source_name": source_name,
                "date": None,
                "quantity": None,
                "ndc": None,
                "drug_name": None,
            }
            
            # Extract date
            for date_col in ["claim_date", "date_filled", "order_date", "invoice_date", "purchase_date"]:
                if date_col in row and pd.notna(row[date_col]):
                    date_val = row[date_col]
                    # Convert to string, handling datetime objects
                    if isinstance(date_val, pd.Timestamp):
                        entry["date"] = date_val.strftime("%Y-%m-%d")
                    else:
                        entry["date"] = str(date_val)
                    break
            
            # Extract quantity
            for qty_col in ["ordered_qty", "sold_qty", "quantity"]:
                if qty_col in row and pd.notna(row[qty_col]):
                    entry["quantity"] = float(row[qty_col])
                    break
            
            # Extract NDC
            if "ndc" in row and pd.notna(row["ndc"]):
                entry["ndc"] = str(row["ndc"])
            
            # Extract drug name
            if "drug_name" in row and pd.notna(row["drug_name"]):
                entry["drug_name"] = str(row["drug_name"])
            
            # Add supplier name for ordered entries
            if source_type == "ordered" and "supplier_name" in row and pd.notna(row["supplier_name"]):
                entry["supplier_name"] = str(row["supplier_name"])
            
            return entry
        
        # Format ordered entries
        ordered_results = []
        if "supplier_name" in ordered_entries.columns:
            for supplier in ordered_entries["supplier_name"].unique():
                supplier_entries = ordered_entries[ordered_entries["supplier_name"] == supplier]
                for _, row in supplier_entries.iterrows():
                    ordered_results.append(format_entry(row, "ordered", supplier))
        else:
            for _, row in ordered_entries.iterrows():
                ordered_results.append(format_entry(row, "ordered", "Supplier"))
        
        # Format sold entries (inventory report)
        sold_results = []
        for _, row in sold_entries.iterrows():
            sold_results.append(format_entry(row, "sold", "Inventory Report"))
        
        # Sort by date (most recent first)
        def sort_key(entry):
            if entry["date"]:
                try:
                    return pd.to_datetime(entry["date"])
                except:
                    return pd.Timestamp.min
            return pd.Timestamp.min
        
        ordered_results.sort(key=sort_key, reverse=True)
        sold_results.sort(key=sort_key, reverse=True)
        
        return JSONResponse({
            "medicine_key": medicine_key,
            "ordered_entries": ordered_results,
            "sold_entries": sold_results,
            "total_ordered": len(ordered_results),
            "total_sold": len(sold_results),
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get medicine entries")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/runs", response_class=HTMLResponse)
async def runs_page(request: Request):
    """Runs listing page - check auth in frontend"""
    return templates.TemplateResponse("runs.html", {"request": request})

