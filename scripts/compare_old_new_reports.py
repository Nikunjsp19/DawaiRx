#!/usr/bin/env python3
"""
Compare old app Report CSV vs new app remaining_inventory CSV.
Usage:
  python scripts/compare_old_new_reports.py \\
    --old /Users/nikunjpatel/Downloads/Report_20250114_to_20260206.csv \\
    --new /Users/nikunjpatel/Downloads/remaining_inventory.csv

Normalizes NDC for matching (old: 00003-0894-21 -> 00003089421).
Compares overlapping columns and reports value differences.
"""
import argparse
import csv
import re
import sys
from pathlib import Path


def normalize_ndc(ndc: str) -> str:
    """11-digit NDC for matching: strip non-digits and take first 11."""
    if not ndc or not str(ndc).strip():
        return ""
    digits = re.sub(r"\D", "", str(ndc).strip())
    return digits[:11].zfill(11) if digits else ""


def parse_old_report(path: Path) -> tuple[list[str], list[dict]]:
    """Parse old app CSV with possible quoted newlines in headers (standard csv handles it)."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header_row = next(reader, None)
        if not header_row:
            return [], []
        headers = [h.strip().replace("\n", " ").strip() for h in header_row]
        rows = []
        for values in reader:
            if len(values) < len(headers):
                row = {headers[i]: values[i] if i < len(values) else "" for i in range(len(headers))}
            else:
                row = {headers[i]: (values[i].strip() if i < len(values) else "") for i in range(len(headers))}
            rows.append(row)
    return headers, rows


def parse_new_remaining(path: Path) -> tuple[list[str], list[dict]]:
    """Parse new app remaining_inventory CSV (standard)."""
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        headers = r.fieldnames or []
        rows = list(r)
    return headers, rows


def safe_float(v, default=None):
    if v is None or v == "" or (isinstance(v, str) and v.strip() == ""):
        return default
    try:
        return float(str(v).replace(",", "").strip())
    except ValueError:
        return default


def main():
    p = argparse.ArgumentParser(description="Compare old app Report CSV vs new app remaining_inventory CSV")
    p.add_argument("--old", required=True, help="Path to Report_*.csv (old app)")
    p.add_argument("--new", required=True, help="Path to remaining_inventory.csv (new app)")
    p.add_argument("--tolerance", type=float, default=0.01, help="Numeric comparison tolerance")
    p.add_argument("--out", default="", help="Write diff_report.csv to this path (e.g. out/compare/diff_report.csv)")
    args = p.parse_args()

    old_path = Path(args.old)
    new_path = Path(args.new)
    if not old_path.exists():
        print(f"Error: Old file not found: {old_path}", file=sys.stderr)
        sys.exit(1)
    if not new_path.exists():
        print(f"Error: New file not found: {new_path}", file=sys.stderr)
        sys.exit(1)

    old_headers, old_rows = parse_old_report(old_path)
    new_headers, new_rows = parse_new_remaining(new_path)

    # Build old index by normalized NDC (first row wins)
    old_by_ndc = {}
    for r in old_rows:
        ndc_raw = r.get("NDC", "")
        ndc = normalize_ndc(ndc_raw)
        if ndc and ndc not in old_by_ndc:
            old_by_ndc[ndc] = r

    new_by_ndc = {}
    for r in new_rows:
        ndc_raw = r.get("ndc", "")
        ndc = normalize_ndc(ndc_raw)
        if ndc and ndc not in new_by_ndc:
            new_by_ndc[ndc] = r

    all_ndcs = sorted(set(old_by_ndc) | set(new_by_ndc))
    tolerance = args.tolerance

    # Column mapping: old report key -> new report key (for same concept)
    # Old: TOTAL ORDERED-O (units), TOTAL BILLED-B (units). New: ordered_total, sold_total (may be packages or units)
    compare_pairs = [
        ("TOTAL BILLED-B", "sold_total", "Sold / Billed"),
        ("TOTAL ORDERED-O", "ordered_total", "Ordered"),
    ]

    print("=" * 70)
    print("OLD APP vs NEW APP REPORT COMPARISON")
    print("=" * 70)
    print(f"Old file: {old_path.name}  ->  {len(old_rows)} rows, {len(old_headers)} columns")
    print(f"New file: {new_path.name}  ->  {len(new_rows)} rows, {len(new_headers)} columns")
    print()
    print("Note: Old report = full DawaiRx report (only rows with sales).")
    print("      New file   = remaining_inventory (leftover qty > 0). Different row set.")
    print()

    only_in_old = [ndc for ndc in all_ndcs if ndc in old_by_ndc and ndc not in new_by_ndc]
    only_in_new = [ndc for ndc in all_ndcs if ndc in new_by_ndc and ndc not in old_by_ndc]
    in_both = [ndc for ndc in all_ndcs if ndc in old_by_ndc and ndc in new_by_ndc]

    print("--- ROW COVERAGE ---")
    print(f"NDCs only in OLD report: {len(only_in_old)}")
    print(f"NDCs only in NEW file:   {len(only_in_new)}")
    print(f"NDCs in BOTH:            {len(in_both)}")
    if only_in_old and len(only_in_old) <= 15:
        print(f"  Only in old (sample): {only_in_old[:15]}")
    elif only_in_old:
        print(f"  Only in old (first 15): {only_in_old[:15]} ...")
    if only_in_new and len(only_in_new) <= 15:
        print(f"  Only in new (sample): {only_in_new[:15]}")
    elif only_in_new:
        print(f"  Only in new (first 15): {only_in_new[:15]} ...")
    print()

    print("--- VALUE DIFFERENCES (matching NDC) ---")
    diffs = []
    for ndc in in_both:
        o = old_by_ndc[ndc]
        n = new_by_ndc[ndc]
        for old_key, new_key, label in compare_pairs:
            ov = o.get(old_key)
            nv = n.get(new_key)
            of = safe_float(ov)
            nf = safe_float(nv)
            if of is None and nf is None:
                continue
            if of is None:
                of = 0
            if nf is None:
                nf = 0
            if abs(of - nf) > tolerance:
                diffs.append((ndc, o.get("DRUG NAME", "")[:40], label, old_key, ov, new_key, nv, of, nf))

    if not diffs:
        print("No value differences found for overlapping columns (TOTAL BILLED-B/sold_total, TOTAL ORDERED-O/ordered_total).")
    else:
        print(f"Found {len(diffs)} value difference(s):\n")
        for ndc, drug, label, ok, ov, nk, nv, of, nf in diffs[:50]:
            print(f"  NDC {ndc}  {drug}")
            print(f"    {label}:  OLD {ok}={ov} ({of})  vs  NEW {nk}={nv} ({nf})  ->  diff={nf - of}")
            print()
        if len(diffs) > 50:
            print(f"  ... and {len(diffs) - 50} more.")
    print()

    # Write diff_report.csv for Phase 3 artifact (ndc, column, legacy_value, new_value, status)
    out_path = getattr(args, "out", None)
    if out_path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ndc", "column", "legacy_value", "new_value", "status"])
            for ndc, drug, label, ok, ov, nk, nv, of, nf in diffs:
                w.writerow([ndc, ok or nk, str(ov) if ov is not None else "", str(nv) if nv is not None else "", "mismatch"])
            if not diffs:
                w.writerow(["#", "No value diffs", "", "", "ok"])
        print(f"Wrote {out_path}")

    print("Done.")


if __name__ == "__main__":
    main()
