#!/usr/bin/env python3
"""
Compare reconciliation CSV outputs from Python app vs Java app.
Usage:
  python scripts/compare_report_results.py [--python-dir /tmp/dawai_compare/python_out] [--java-dir /tmp/dawai_compare/java_out]
If java-dir is missing or empty, only Python summary is printed.
"""
import argparse
import csv
import os
import sys
from pathlib import Path

# Columns to compare (order and names may differ slightly; we normalize by medicine_key and these)
NUM_COLS = ["ordered_total", "sold_total", "remaining_qty", "shortage_qty", "leftover_qty"]
KEY_COL = "medicine_key"


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def norm_row(r: dict) -> dict:
    """Normalize numeric values for comparison."""
    out = {k: v for k, v in r.items()}
    for col in NUM_COLS:
        if col in out and out[col] not in (None, ""):
            try:
                out[col] = round(float(out[col]), 6)
            except (ValueError, TypeError):
                pass
    return out


def compare_csvs(name: str, py_path: Path, java_path: Path) -> dict:
    py_rows = load_csv(py_path)
    java_rows = load_csv(java_path)
    result = {
        "name": name,
        "python_rows": len(py_rows),
        "java_rows": len(java_rows),
        "match": False,
        "only_in_python": [],
        "only_in_java": [],
        "value_diffs": [],
    }
    if not py_rows and not java_rows:
        return result
    if not java_rows:
        result["only_in_python"] = [r.get(KEY_COL, "") for r in py_rows][:20]
        return result
    if not py_rows:
        result["only_in_java"] = [r.get(KEY_COL, "") for r in java_rows][:20]
        return result

    py_by_key = {norm_row(r).get(KEY_COL): norm_row(r) for r in py_rows if r.get(KEY_COL)}
    java_by_key = {norm_row(r).get(KEY_COL): norm_row(r) for r in java_rows if r.get(KEY_COL)}
    keys_py = set(py_by_key)
    keys_java = set(java_by_key)
    result["only_in_python"] = sorted(keys_py - keys_java)[:20]
    result["only_in_java"] = sorted(keys_java - keys_py)[:20]
    result["common_keys"] = len(keys_py & keys_java)
    value_diffs = []
    for k in keys_py & keys_java:
        pr, jr = py_by_key[k], java_by_key[k]
        for col in NUM_COLS:
            if col not in pr or col not in jr:
                continue
            pv, jv = pr.get(col), jr.get(col)
            try:
                pn = round(float(pv), 6) if pv not in (None, "") else None
                jn = round(float(jv), 6) if jv not in (None, "") else None
            except (ValueError, TypeError):
                pn, jn = pv, jv
            if pn != jn:
                value_diffs.append((k, col, pn, jn))
                if len(value_diffs) >= 15:
                    break
        if len(value_diffs) >= 15:
            break
    result["value_diffs"] = value_diffs
    result["match"] = (
        result["only_in_python"] == []
        and result["only_in_java"] == []
        and result["value_diffs"] == []
    )
    return result


def main():
    p = argparse.ArgumentParser(description="Compare Python vs Java report CSVs")
    p.add_argument("--python-dir", default="/tmp/dawai_compare/python_out", help="Python CLI output dir")
    p.add_argument("--java-dir", default="/tmp/dawai_compare/java_out", help="Java API output dir")
    args = p.parse_args()
    py_dir = Path(args.python_dir)
    java_dir = Path(args.java_dir)

    print("=" * 60)
    print("DawaiRx Report Comparison (Python vs Java)")
    print("=" * 60)
    print(f"Python output dir: {py_dir}")
    print(f"Java output dir:   {java_dir}")
    print()

    # Python summary
    for fname, label in [
        ("remaining_inventory.csv", "Remaining inventory"),
        ("shortages.csv", "Shortages"),
        ("reconciliation_full.csv", "Full reconciliation"),
        ("issues.csv", "Issues"),
    ]:
        path = py_dir / fname
        rows = load_csv(path)
        print(f"  Python {label}: {len(rows)} rows" + (f"  ({path})" if path.exists() else "  (missing)"))

    # Java summary
    has_java = (java_dir / "remaining_inventory.csv").exists()
    if has_java:
        for fname, label in [
            ("remaining_inventory.csv", "Remaining inventory"),
            ("shortages.csv", "Shortages"),
            ("issues.csv", "Issues"),
        ]:
            path = java_dir / fname
            rows = load_csv(path)
            print(f"  Java   {label}: {len(rows)} rows")
    else:
        print("  Java:   No output (run failed or not run). Restart backend and run scripts/run_java_report_and_compare.py")

    print()
    if has_java:
        print("--- Comparison ---")
        for name, fname in [("remaining_inventory", "remaining_inventory.csv"), ("shortages", "shortages.csv")]:
            res = compare_csvs(name, py_dir / fname, java_dir / fname)
            print(f"\n{res['name']}:")
            print(f"  Python rows: {res['python_rows']}, Java rows: {res['java_rows']}")
            if res.get("common_keys") is not None:
                print(f"  Common keys: {res['common_keys']}")
            if res["only_in_python"]:
                print(f"  Only in Python (first 20): {res['only_in_python']}")
            if res["only_in_java"]:
                print(f"  Only in Java (first 20):   {res['only_in_java']}")
            if res["value_diffs"]:
                print(f"  Value differences (first 15): {res['value_diffs']}")
            print(f"  Match: {res['match']}")
    else:
        print("--- Comparison skipped (no Java output) ---")

    print()
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
