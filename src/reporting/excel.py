"""Excel report generation"""

from pathlib import Path
from typing import Dict, Any
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def create_audit_report(
    output_path: str,
    reconciled_df: pd.DataFrame,
    issues_df: pd.DataFrame,
    summary: Dict[str, Any]
):
    """
    Create Excel workbook with multiple sheets.
    
    Args:
        output_path: Path to output Excel file
        reconciled_df: Reconciled inventory DataFrame
        issues_df: Issues DataFrame
        summary: Summary statistics dictionary
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Sheet 1: Summary
        summary_data = {
            "Metric": [
                "Total Medicines",
                "Total Ordered",
                "Total Sold",
                "Total Remaining",
                "Total Shortage",
                "Total Leftover",
                "Medicines with Shortage",
                "Medicines with Leftover",
                "Sold Percentage",
            ],
            "Value": [
                summary.get("total_medicines", 0),
                f"{summary.get('total_ordered', 0):,.0f}",
                f"{summary.get('total_sold', 0):,.0f}",
                f"{summary.get('total_remaining', 0):,.0f}",
                f"{summary.get('total_shortage', 0):,.0f}",
                f"{summary.get('total_leftover', 0):,.0f}",
                summary.get("medicines_with_shortage", 0),
                summary.get("medicines_with_leftover", 0),
                f"{summary.get('sold_percentage', 0):.1f}%",
            ],
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        
        # Sheet 2: Remaining Inventory
        remaining = reconciled_df[reconciled_df["leftover_qty"] > 0].copy()
        if len(remaining) > 0:
            remaining.to_excel(writer, sheet_name="Remaining", index=False)
        else:
            pd.DataFrame(columns=reconciled_df.columns).to_excel(
                writer, sheet_name="Remaining", index=False
            )
        
        # Sheet 3: Shortages
        shortages = reconciled_df[reconciled_df["shortage_qty"] > 0].copy()
        if len(shortages) > 0:
            shortages.to_excel(writer, sheet_name="Shortages", index=False)
        else:
            pd.DataFrame(columns=reconciled_df.columns).to_excel(
                writer, sheet_name="Shortages", index=False
            )
        
        # Sheet 4: Leftovers
        leftovers = reconciled_df[reconciled_df["leftover_qty"] > 0].copy()
        if len(leftovers) > 0:
            leftovers.to_excel(writer, sheet_name="Leftovers", index=False)
        else:
            pd.DataFrame(columns=reconciled_df.columns).to_excel(
                writer, sheet_name="Leftovers", index=False
            )
        
        # Sheet 5: Issues
        if len(issues_df) > 0:
            # Flatten row_ref and raw_snippet for Excel
            issues_export = issues_df.copy()
            if "row_ref" in issues_export.columns:
                issues_export["row_source"] = issues_export["row_ref"].apply(
                    lambda x: x.get("source", "") if isinstance(x, dict) else ""
                )
                issues_export["row_number"] = issues_export["row_ref"].apply(
                    lambda x: x.get("row_number", "") if isinstance(x, dict) else ""
                )
                issues_export = issues_export.drop(columns=["row_ref"], errors="ignore")
            
            if "raw_snippet" in issues_export.columns:
                issues_export = issues_export.drop(columns=["raw_snippet"], errors="ignore")
            
            issues_export.to_excel(writer, sheet_name="Issues", index=False)
        else:
            pd.DataFrame(columns=["rule_id", "severity", "medicine_key", "details"]).to_excel(
                writer, sheet_name="Issues", index=False
            )
    
    logger.info(f"Created Excel report: {output_path}")

