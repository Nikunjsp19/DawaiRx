"""Validation logic for ingested data"""

from typing import Dict, List, Any, Set
import pandas as pd
import logging

from src.ingestion.mapper import REQUIRED_FIELDS_ORDERED, REQUIRED_FIELDS_SOLD

logger = logging.getLogger(__name__)


def validate_dataframe(
    df: pd.DataFrame,
    required_fields: Set[str],
    report_type: str
) -> Dict[str, Any]:
    """
    Validate a DataFrame has required fields and basic data quality.
    
    Args:
        df: DataFrame to validate
        required_fields: Set of required canonical field names
        report_type: "ordered" or "sold"
        
    Returns:
        Dictionary with validation results
    """
    results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "row_count": len(df),
        "column_count": len(df.columns),
        "missing_fields": [],
        "empty_rows": 0,
        "null_counts": {},
    }
    
    # Check required fields exist
    missing = required_fields - set(df.columns)
    if missing:
        results["valid"] = False
        results["missing_fields"] = list(missing)
        results["errors"].append(f"Missing required fields: {missing}")
    
    # Check for empty DataFrame
    if len(df) == 0:
        results["valid"] = False
        results["errors"].append("DataFrame is empty")
    
    # Count nulls in required fields
    for field in required_fields:
        if field in df.columns:
            null_count = df[field].isna().sum()
            results["null_counts"][field] = int(null_count)
            if null_count > 0:
                pct = (null_count / len(df)) * 100
                results["warnings"].append(
                    f"Field '{field}' has {null_count} null values ({pct:.1f}%)"
                )
    
    # Count completely empty rows
    if len(df) > 0:
        empty_rows = df.isna().all(axis=1).sum()
        results["empty_rows"] = int(empty_rows)
        if empty_rows > 0:
            results["warnings"].append(f"{empty_rows} completely empty rows found")
    
    # Check data types for key fields
    if "quantity" in df.columns or "ordered_qty" in df.columns or "sold_qty" in df.columns:
        qty_field = None
        for field in ["ordered_qty", "sold_qty", "quantity"]:
            if field in df.columns:
                qty_field = field
                break
        
        if qty_field:
            # Try to convert to numeric
            try:
                numeric_qty = pd.to_numeric(df[qty_field], errors='coerce')
                non_numeric = numeric_qty.isna().sum() - df[qty_field].isna().sum()
                if non_numeric > 0:
                    results["warnings"].append(
                        f"Field '{qty_field}' has {non_numeric} non-numeric values"
                    )
            except Exception as e:
                results["warnings"].append(f"Could not validate numeric field '{qty_field}': {e}")
    
    return results


def get_summary_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Get summary statistics for a DataFrame.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        Dictionary with summary statistics
    """
    stats = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns),
        "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
    }
    
    # Add basic stats for numeric columns
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 0:
        stats["numeric_columns"] = list(numeric_cols)
        stats["numeric_summary"] = df[numeric_cols].describe().to_dict()
    
    return stats

