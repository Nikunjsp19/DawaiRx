#!/usr/bin/env python3
"""
Parity check: run the same fixture inputs through both Python and Java pipelines,
compare outputs field-by-field and row-by-row, and emit a mismatch report.

Usage:
    python scripts/parity_check.py [--java-output <dir>] [--python-output <dir>]

Prerequisites:
    1. Python backend: cd DawaiRx && python -c "..." (see below for inline run)
    2. Java backend: cd DawaiRx/backend && mvn spring-boot:run
       Then upload the same fixtures via curl / API.

This script:
    - Runs the Python pipeline on fixtures/
    - Reads the Java-generated inventory_report.csv from --java-output
    - Compares columns, rows, and per-field values
    - Prints a detailed mismatch report
"""

import sys
import os
import csv
import argparse
from pathlib import Path

# Add project root to path so we can import src modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_csv(path):
    """Load a CSV file into a list of dicts."""
    rows = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def run_python_pipeline(ordered_paths, sold_path, output_dir):
    """Run the Python pipeline on given files and return the report path."""
    from src.ingestion.processor import process_file
    from src.normalization.processor import normalize_dataframe
    from src.reconciliation.engine import reconcile_inventory, generate_summary
    from src.reporting.dawairx_format import create_dawairx_report
    import pandas as pd

    # Process ordered files
    ordered_dfs = []
    all_supplier_names = []
    for i, path in enumerate(ordered_paths):
        result = process_file(str(path), "ordered", None)
        df = result["dataframe"]
        supplier = Path(path).stem.split("_", 2)[-1] if "_" in Path(path).stem else Path(path).stem
        supplier = supplier.replace("_", " ").replace(".", " ").upper().strip()
        df["supplier_name"] = supplier
        all_supplier_names.append(supplier)
        ordered_dfs.append(df)

    if ordered_dfs:
        ordered_df = pd.concat(ordered_dfs, ignore_index=True)
    else:
        ordered_df = pd.DataFrame()

    # Process sold file
    sold_result = process_file(str(sold_path), "sold", None)
    sold_df = sold_result["dataframe"]

    # Normalize
    ordered_normalized = normalize_dataframe(ordered_df, "ordered")
    sold_normalized = normalize_dataframe(sold_df, "sold")

    # Reconcile
    reconciled = reconcile_inventory(ordered_normalized, sold_normalized)
    summary = generate_summary(reconciled)

    # Generate DawaiRx report
    report_path = output_dir / "inventory_report.csv"
    dawairx_report = create_dawairx_report(
        str(report_path), reconciled, sold_normalized, ordered_normalized,
        summary, all_supplier_names=all_supplier_names
    )

    return report_path


def compare_reports(python_rows, java_rows):
    """Compare two report outputs and print mismatch details."""
    mismatches = []
    
    # Column comparison
    py_cols = set(python_rows[0].keys()) if python_rows else set()
    java_cols = set(java_rows[0].keys()) if java_rows else set()
    
    missing_in_java = py_cols - java_cols
    extra_in_java = java_cols - py_cols
    common_cols = py_cols & java_cols
    
    print("=" * 70)
    print("PARITY CHECK REPORT")
    print("=" * 70)
    print(f"\nPython columns ({len(py_cols)}): {sorted(py_cols)}")
    print(f"Java columns   ({len(java_cols)}): {sorted(java_cols)}")
    print(f"\nCommon: {len(common_cols)}")
    if missing_in_java:
        print(f"Missing in Java: {sorted(missing_in_java)}")
        mismatches.append(f"Column mismatch: {len(missing_in_java)} missing in Java")
    if extra_in_java:
        print(f"Extra in Java: {sorted(extra_in_java)}")
        mismatches.append(f"Column mismatch: {len(extra_in_java)} extra in Java")
    
    # Row count
    print(f"\nPython rows: {len(python_rows)}")
    print(f"Java rows:   {len(java_rows)}")
    if len(python_rows) != len(java_rows):
        mismatches.append(f"Row count mismatch: Python={len(python_rows)} Java={len(java_rows)}")
    
    # Build index by medicine_key for row matching
    py_by_key = {}
    for r in python_rows:
        key = r.get("medicine_key", "")
        if key:
            py_by_key[key] = r
    
    java_by_key = {}
    for r in java_rows:
        key = r.get("medicine_key", "")
        if key:
            java_by_key[key] = r
    
    missing_rows = set(py_by_key.keys()) - set(java_by_key.keys())
    extra_rows = set(java_by_key.keys()) - set(py_by_key.keys())
    common_keys = set(py_by_key.keys()) & set(java_by_key.keys())
    
    if missing_rows:
        print(f"\nRows in Python but not Java: {sorted(missing_rows)}")
        mismatches.append(f"Missing rows in Java: {len(missing_rows)}")
    if extra_rows:
        print(f"\nRows in Java but not Python: {sorted(extra_rows)}")
        mismatches.append(f"Extra rows in Java: {len(extra_rows)}")
    
    # Per-field comparison for common rows
    field_mismatches = 0
    for key in sorted(common_keys):
        py_row = py_by_key[key]
        java_row = java_by_key[key]
        for col in sorted(common_cols):
            py_val = py_row.get(col, "")
            java_val = java_row.get(col, "")
            
            # Normalize for comparison
            py_str = str(py_val).strip() if py_val else ""
            java_str = str(java_val).strip() if java_val else ""
            
            # Numeric comparison with tolerance
            try:
                py_num = float(py_str) if py_str else 0.0
                java_num = float(java_str) if java_str else 0.0
                if abs(py_num - java_num) > 0.01:
                    field_mismatches += 1
                    print(f"  [{key}] {col}: Python={py_str} Java={java_str} (diff={py_num-java_num:.4f})")
                continue
            except ValueError:
                pass
            
            # String comparison
            if py_str != java_str:
                field_mismatches += 1
                print(f"  [{key}] {col}: Python='{py_str}' Java='{java_str}'")
    
    if field_mismatches:
        mismatches.append(f"Field mismatches: {field_mismatches}")
    
    # Summary
    print("\n" + "=" * 70)
    if not mismatches:
        print("RESULT: PASS - All outputs match!")
    else:
        print(f"RESULT: FAIL - {len(mismatches)} issues found:")
        for m in mismatches:
            print(f"  - {m}")
    print("=" * 70)
    
    return len(mismatches) == 0


def main():
    parser = argparse.ArgumentParser(description="DawaiRx parity check: Python vs Java")
    parser.add_argument("--java-output", type=str,
                        help="Path to Java-generated inventory_report.csv")
    parser.add_argument("--python-output", type=str, default=None,
                        help="Path to Python-generated inventory_report.csv (runs Python pipeline if not provided)")
    parser.add_argument("--fixtures-dir", type=str, 
                        default=str(PROJECT_ROOT / "backend" / "src" / "test" / "resources" / "fixtures"),
                        help="Directory containing fixture CSVs")
    args = parser.parse_args()
    
    fixtures = Path(args.fixtures_dir)
    if not fixtures.is_dir():
        print(f"ERROR: Fixtures dir not found: {fixtures}")
        sys.exit(1)
    
    # Find fixture files
    ordered_files = sorted(fixtures.glob("ordered_*.csv"))
    sold_files = sorted(fixtures.glob("sold_*.csv"))
    
    if not ordered_files or not sold_files:
        print(f"ERROR: No fixture files found in {fixtures}")
        sys.exit(1)
    
    print(f"Fixtures: {len(ordered_files)} ordered, {len(sold_files)} sold")
    
    # Run Python pipeline (or load pre-computed)
    if args.python_output:
        python_csv = Path(args.python_output)
    else:
        py_output_dir = Path("/tmp/dawai-parity-check/python")
        py_output_dir.mkdir(parents=True, exist_ok=True)
        print("\nRunning Python pipeline...")
        python_csv = run_python_pipeline(ordered_files, sold_files[0], py_output_dir)
        print(f"Python output: {python_csv}")
    
    python_rows = load_csv(str(python_csv))
    print(f"Python report loaded: {len(python_rows)} rows")
    
    # Load Java output
    if args.java_output:
        java_csv = Path(args.java_output)
    else:
        # Try default Java output location
        java_csv = None
        java_output_base = PROJECT_ROOT / "out" / "web_runs"
        if java_output_base.exists():
            # Find most recent run
            runs = sorted([d for d in java_output_base.iterdir() if d.is_dir()], reverse=True)
            for run_dir in runs:
                candidate = run_dir / "inventory_report.csv"
                if candidate.exists():
                    java_csv = candidate
                    break
        
        if java_csv is None:
            print("\nNo Java output found. Run the Java pipeline first:")
            print("  cd backend && mvn spring-boot:run")
            print("  Then upload the fixture files via the API.")
            print("  Or provide --java-output <path/to/inventory_report.csv>")
            sys.exit(1)
    
    java_rows = load_csv(str(java_csv))
    print(f"Java report loaded: {len(java_rows)} rows")
    
    # Compare
    passed = compare_reports(python_rows, java_rows)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
