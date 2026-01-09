# DawaiRx Enhancements - BatchRx-like Features

## Overview

DawaiRx has been enhanced to match BatchRx functionality with comprehensive audit rules and detailed PDF reporting.

## New Features

### 1. Extended Audit Rules (15 Total)

**Original Rules (7):**
- R001: Duplicate Claim/Row
- R002: Invalid NDC Format
- R003: Sold Item Not in Ordered Set
- R004: Negative or Zero Quantity
- R005: Over-Sold
- R006: Suspicious Days Supply
- R007: Missing Critical Fields

**New Extended Rules (8):**
- **R008: Excessive Quantity** - Flags unusually high quantities (default threshold: 1000)
- **R009: Price Anomaly** - Detects unusually high or low unit prices
- **R010: Missing NDC** - Identifies drugs with names but missing NDC codes
- **R011: Date Anomaly** - Flags future dates or dates too far in past (>2 years)
- **R012: Quantity Mismatch** - Detects significant differences between ordered and sold (5% tolerance)
- **R013: Invalid Medicine Key** - Flags rows where medicine cannot be identified
- **R014: Concurrent Fills** - Detects overlapping fills for same prescription
- **R015: Refill Too Soon** - Flags refills before 80% of days supply elapsed

### 2. Detailed PDF Reports

Comprehensive PDF reports similar to BatchRx with:

- **Executive Summary** - Key metrics and statistics
- **Issues Summary by Rule** - Breakdown of issues by rule ID and severity
- **Detailed Issues** - Sample of issues with full details
- **Shortages Section** - Over-sold medicines with details
- **Remaining Inventory** - Medicines with leftover stock
- **Reconciliation Details** - Sample of all medicines with status

**PDF Features:**
- Professional formatting with color-coded sections
- Multiple pages with proper pagination
- Tables with proper styling
- Summary statistics
- Sample data (first 30-50 rows) with note about full data in CSV

### 3. Enhanced Reporting

- **Excel Reports** - Multi-sheet workbooks (unchanged)
- **PDF Reports** - New detailed PDF reports
- **CSV Exports** - All data exports (unchanged)
- **JSON Summary** - Machine-readable summary (unchanged)

## Usage

### CLI

```bash
# Run with extended rules (automatic)
python -m src.cli.main run \
  --ordered sample_data/ordered_sample.csv \
  --sold sample_data/sold_sample.csv \
  --output-dir out/my_run

# Output includes:
# - audit_report.xlsx (Excel)
# - audit_report_detailed.pdf (PDF) ✨ NEW
# - All CSV files
# - summary.json
```

### Web UI

1. Upload files via web UI
2. Run reconciliation
3. Download **Detailed PDF Report** from download links
4. View results in browser tables

## Configuration

### Rule Thresholds

Rules can be customized by modifying the rule classes:

```python
# Example: Change excessive quantity threshold
R008_ExcessiveQuantity(threshold=2000.0)  # Default: 1000.0

# Example: Change price range
R009_PriceAnomaly(min_price=0.10, max_price=5000.0)

# Example: Change refill tolerance
R015_RefillTooSoon(min_days_elapsed_percent=75.0)  # Default: 80%
```

## Dependencies

New dependencies added:
- `reportlab>=4.0.0` - PDF generation
- `matplotlib>=3.7.0` - (Optional, for future charting)

Install with:
```bash
pip install -r requirements.txt
```

## File Structure

```
src/
├── rules/
│   ├── implementations.py          # Original 7 rules
│   └── implementations_extended.py # New 8 rules ✨
├── reporting/
│   ├── excel.py                    # Excel reports
│   └── pdf.py                      # PDF reports ✨
```

## Comparison with BatchRx

| Feature | BatchRx | DawaiRx |
|---------|---------|---------|
| Audit Rules | ~15+ rules | 15 rules ✅ |
| PDF Reports | Yes | Yes ✅ |
| Excel Reports | Yes | Yes ✅ |
| CSV Exports | Yes | Yes ✅ |
| Web UI | Yes | Yes ✅ |
| Local Execution | No | Yes ✅ |
| Open Source | No | Yes ✅ |
| Customizable | Limited | Fully ✅ |

## Next Steps

Potential future enhancements:
- [ ] Configurable rule thresholds via YAML/JSON
- [ ] Charts and graphs in PDF reports
- [ ] Email notifications
- [ ] Scheduled runs
- [ ] Advanced filtering and search
- [ ] Multi-pharmacy support
- [ ] Custom rule creation UI

## Notes

- Extended rules are automatically used if available
- Falls back to standard 7 rules if extended rules fail to load
- PDF generation requires `reportlab` package
- All rules run automatically during reconciliation
- Issues are categorized by severity (high, medium, low)

