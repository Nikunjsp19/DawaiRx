#!/usr/bin/env python3
"""
Compare legacy (Python) vs new (Java) report CSVs.
Normalizes headers (trim, newline->space), uses medicine_key or NDC+DRUG NAME as row key.
Outputs PARITY_DIFF_REPORT.md with summary, column/row/cell mismatches.
"""
import csv
import re
import sys
from pathlib import Path
from collections import defaultdict

def normalize_header(h):
    return (h or "").replace("\n", " ").strip()

def parse_numeric(s):
    if s is None or (isinstance(s, str) and s.strip() == ""):
        return None
    if isinstance(s, (int, float)):
        return float(s) if not isinstance(s, float) or s == s else None  # NaN check
    s = str(s).strip().replace(",", "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None

def row_key(row, raw_headers):
    """Use NDC + DRUG NAME for matching (legacy has no medicine_key)."""
    ndc_col = drug_col = None
    for h in raw_headers:
        n = normalize_header(h)
        if n == "NDC":
            ndc_col = h
        elif n == "DRUG NAME":
            drug_col = h
    ndc = (row.get(ndc_col) or "").strip()
    drug = (row.get(drug_col) or "").strip()
    return f"{ndc}|{drug}"

def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        raw_headers = next(reader)
    # Re-read: some CSVs have multi-line headers in one cell
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        raw_headers = next(reader)
        rows = list(reader)
    headers = [normalize_header(h) for h in raw_headers]
    # Rows as list of dicts keyed by original header
    data = []
    for r in rows:
        if len(r) < len(raw_headers):
            r = r + [""] * (len(raw_headers) - len(r))
        row = {raw_headers[i]: (r[i] if i < len(r) else "") for i in range(len(raw_headers))}
        data.append(row)
    return raw_headers, headers, data

def all_headers_normalized(legacy_headers, new_headers):
    """Set of normalized header names from both."""
    s = set(legacy_headers) | set(new_headers)
    return s

def main():
    legacy_path = Path("/Users/nikunjpatel/Downloads/Report_20250114_to_20260206.csv")
    new_path = Path("/Users/nikunjpatel/Downloads/download.csv")
    if len(sys.argv) >= 3:
        legacy_path = Path(sys.argv[1])
        new_path = Path(sys.argv[2])

    leg_raw, leg_headers, leg_rows = load_csv(legacy_path)
    new_raw, new_headers, new_rows = load_csv(new_path)

    all_norm = all_headers_normalized(leg_headers, new_headers)
    missing_in_new = [n for n in set(leg_headers) if n not in set(new_headers)]
    extra_in_new = [n for n in set(new_headers) if n not in set(leg_headers)]

    def build_key_map(rows, raw_headers):
        key_to_row = {}
        for row in rows:
            k = row_key(row, raw_headers)
            key_to_row[k] = row
        return key_to_row

    leg_key_map = build_key_map(leg_rows, leg_raw)
    new_key_map = build_key_map(new_rows, new_raw)

    leg_keys = set(leg_key_map.keys())
    new_keys = set(new_key_map.keys())
    common_keys = leg_keys & new_keys
    only_legacy = leg_keys - new_keys
    only_new = new_keys - leg_keys

    norm_to_leg_raw = {normalize_header(leg_raw[i]): leg_raw[i] for i in range(len(leg_raw))}
    norm_to_new_raw = {normalize_header(new_raw[i]): new_raw[i] for i in range(len(new_raw))}
    comparable_cols = [n for n in all_norm if n in leg_headers and n in new_headers and n != "medicine_key"]
    cell_mismatches = []
    for k in common_keys:
        leg_row = leg_key_map[k]
        new_row = new_key_map[k]
        for norm_col in comparable_cols:
            leg_raw_col = norm_to_leg_raw.get(norm_col)
            new_raw_col = norm_to_new_raw.get(norm_col)
            if leg_raw_col is None or new_raw_col is None:
                continue
            v_leg = leg_row.get(leg_raw_col, "")
            v_new = new_row.get(new_raw_col, "")
            v_leg_s = (v_leg or "").strip()
            v_new_s = (v_new or "").strip()
            if v_leg_s == v_new_s:
                continue
            num_leg = parse_numeric(v_leg_s)
            num_new = parse_numeric(v_new_s)
            delta = None
            if num_leg is not None and num_new is not None:
                delta = num_new - num_leg
                if abs(delta) < 1e-9:
                    continue
            cell_mismatches.append({
                "row_id": k[:80],
                "column": norm_col,
                "legacy": v_leg_s or "(blank)",
                "new": v_new_s or "(blank)",
                "delta": delta,
            })

    # Column order: compare order of normalized headers (excluding medicine_key)
    leg_order = [normalize_header(h) for h in leg_raw]
    new_order = [normalize_header(h) for h in new_raw if normalize_header(h) != "medicine_key"]
    leg_order_no_key = [x for x in leg_order if x != "medicine_key"]
    order_diff = leg_order_no_key != new_order

    # ---- Write report ----
    out_path = Path(__file__).resolve().parent.parent / "PARITY_DIFF_REPORT.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Legacy (Python) vs New (Java) Report Parity Diff\n\n")
        f.write(f"- **Legacy:** `{legacy_path.name}`\n")
        f.write(f"- **New:** `{new_path.name}`\n\n")
        f.write("## 1. Summary counts\n\n")
        f.write("| Metric | Legacy | New |\n")
        f.write("|--------|--------|-----|\n")
        f.write(f"| Rows | {len(leg_rows)} | {len(new_rows)} |\n")
        f.write(f"| Columns (normalized) | {len(set(leg_headers))} | {len(set(new_headers))} |\n")
        f.write(f"| Common row keys | | {len(common_keys)} |\n")
        f.write(f"| Rows only in legacy | {len(only_legacy)} |\n")
        f.write(f"| Rows only in new | {len(only_new)} |\n")
        f.write(f"| Cell-level mismatches | | {len(cell_mismatches)} |\n\n")

        f.write("## 2. Column differences\n\n")
        f.write("- **Missing in new (expected in legacy):** " + (", ".join(missing_in_new) if missing_in_new else "None") + "\n")
        f.write("- **Extra in new:** " + (", ".join(extra_in_new) if extra_in_new else "None (medicine_key is intentional)") + "\n")
        if order_diff:
            f.write("- **Column order:** Differs (legacy vs new order).\n")
        f.write("\n")

        f.write("## 3. Row differences\n\n")
        if only_legacy:
            f.write("**Only in legacy (first 10):**\n")
            for k in list(only_legacy)[:10]:
                f.write(f"- `{k[:60]}`\n")
            f.write("\n")
        if only_new:
            f.write("**Only in new (first 10):**\n")
            for k in list(only_new)[:10]:
                f.write(f"- `{k[:60]}`\n")
            f.write("\n")

        f.write("## 4. Mismatch counts by column (before/after parity)\n\n")
        col_counts = defaultdict(int)
        for m in cell_mismatches:
            col_counts[m["column"]] += 1
        f.write("| Column | Mismatch count |\n|--------|----------------|\n")
        for col, count in sorted(col_counts.items(), key=lambda x: -x[1]):
            f.write(f"| {col} | {count} |\n")
        f.write("\n")
        f.write("## 5. Top mismatch categories (by column)\n\n")
        for col, count in sorted(col_counts.items(), key=lambda x: -x[1])[:20]:
            f.write(f"- `{col}`: {count} mismatches\n")
        f.write("\n")

        f.write("## 6. Sample cell-level mismatches\n\n")
        f.write("| Row identifier | Column | Legacy | New | Delta (if numeric) |\n")
        f.write("|----------------|--------|--------|-----|---------------------|\n")
        for m in cell_mismatches[:50]:
            delta_s = str(m["delta"]) if m["delta"] is not None else ""
            f.write(f"| {m['row_id'][:40]} | {m['column'][:30]} | {str(m['legacy'])[:20]} | {str(m['new'])[:20]} | {delta_s} |\n")
        f.write("\n")

        f.write("## 7. Logic notes\n\n")
        f.write("- **TOTAL ORDERED-O / TOTAL SHORTAGE-S:** Differences often due to different run inputs (date range or ordered data). Legacy may have had date filter excluding some ordered rows; Java uses same formula: TOTAL SHORTAGE-S = TOTAL ORDERED-O - TOTAL BILLED-B.\n")
        f.write("- **Insurance column name:** Legacy uses normalized name `SS&C (FORMERLY HUMANA, ARGUS, AND DST)`; new uses raw `SS&C (FORMERLY HUMANA ARGUS AND OPTUMRX)`. Backend should normalize insurance names to match Python.\n")
        f.write("- **medicine_key:** New CSV includes `medicine_key`; legacy does not. Optional backend change to omit for exact column match.\n")
        f.write("- **RANK:** Order differs when AMOUNT/COST differ (e.g. blank in legacy vs value in new); sort is AMOUNT desc, COST desc in both.\n")

    col_counts = defaultdict(int)
    for m in cell_mismatches:
        col_counts[m["column"]] += 1
    print(f"Wrote {out_path}")
    print(f"Summary: {len(leg_rows)} legacy rows, {len(new_rows)} new rows, {len(cell_mismatches)} cell mismatches")
    print("Mismatch counts by column:")
    for col, count in sorted(col_counts.items(), key=lambda x: -x[1]):
        print(f"  {col}: {count}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
