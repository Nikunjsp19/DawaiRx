"""Reconciliation engine for comparing ordered vs sold inventory"""

import pandas as pd
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def aggregate_by_medicine(df: pd.DataFrame, qty_field: str) -> pd.DataFrame:
    """
    Aggregate quantities by medicine_key.
    
    Args:
        df: DataFrame with medicine_key and quantity field
        qty_field: Name of quantity column to aggregate
        
    Returns:
        DataFrame with one row per medicine_key and aggregated quantity
    """
    if qty_field not in df.columns:
        logger.warning(f"Quantity field '{qty_field}' not found in DataFrame")
        return pd.DataFrame()
    
    # Group by medicine_key and sum quantities
    agg_dict = {qty_field: "sum"}
    
    # Also capture representative values for display fields
    display_fields = ["drug_name", "strength", "manufacturer", "ndc"]
    for field in display_fields:
        if field in df.columns:
            # Use most frequent non-null value, or first if all null
            agg_dict[field] = lambda x: x.dropna().mode().iloc[0] if not x.dropna().empty else x.iloc[0] if len(x) > 0 else None
    
    grouped = df.groupby("medicine_key", as_index=False).agg(agg_dict)
    
    logger.info(f"Aggregated {len(df)} rows into {len(grouped)} unique medicines")
    
    return grouped


def reconcile_inventory(
    ordered_df: pd.DataFrame,
    sold_df: pd.DataFrame,
    ordered_qty_field: str = "ordered_qty",
    sold_qty_field: str = "sold_qty"
) -> pd.DataFrame:
    """
    Reconcile ordered and sold inventory.
    
    Computes:
    - ordered_total: Total quantity ordered per medicine
    - sold_total: Total quantity sold per medicine
    - remaining_qty: ordered_total - sold_total (positive means inventory left)
    - shortage_qty: Negative remaining_qty (if sold > ordered)
    - leftover_qty: Positive remaining_qty (if ordered > sold)
    
    Args:
        ordered_df: DataFrame with ordered quantities (must have medicine_key)
        sold_df: DataFrame with sold quantities (must have medicine_key)
        ordered_qty_field: Name of ordered quantity column
        sold_qty_field: Name of sold quantity column
        
    Returns:
        DataFrame with reconciliation results, one row per medicine_key
    """
    # Aggregate ordered quantities
    if ordered_qty_field not in ordered_df.columns and "quantity" in ordered_df.columns:
        ordered_qty_field = "quantity"
    
    ordered_agg = aggregate_by_medicine(ordered_df, ordered_qty_field)
    if len(ordered_agg) == 0:
        logger.warning("No ordered data to aggregate")
        ordered_agg = pd.DataFrame({"medicine_key": []})
    
    # Aggregate sold quantities
    if sold_qty_field not in sold_df.columns and "quantity" in sold_df.columns:
        sold_qty_field = "quantity"
    
    sold_agg = aggregate_by_medicine(sold_df, sold_qty_field)
    if len(sold_agg) == 0:
        logger.warning("No sold data to aggregate")
        sold_agg = pd.DataFrame({"medicine_key": []})
    
    # Merge ordered and sold
    # Use outer join to include medicines that appear in only one dataset
    merged = pd.merge(
        ordered_agg,
        sold_agg,
        on="medicine_key",
        how="outer",
        suffixes=("_ordered", "_sold")
    )
    
    # Determine quantity field names after merge
    ordered_col = f"{ordered_qty_field}_ordered" if f"{ordered_qty_field}_ordered" in merged.columns else ordered_qty_field
    sold_col = f"{sold_qty_field}_sold" if f"{sold_qty_field}_sold" in merged.columns else sold_qty_field
    
    # Fill missing values with 0
    if ordered_col in merged.columns:
        merged[ordered_col] = merged[ordered_col].fillna(0)
    else:
        merged[ordered_col] = 0
    
    if sold_col in merged.columns:
        merged[sold_col] = merged[sold_col].fillna(0)
    else:
        merged[sold_col] = 0
    
    # Rename to standard names
    merged["ordered_total"] = merged[ordered_col]
    merged["sold_total"] = merged[sold_col]
    
    # Calculate remaining quantity
    merged["remaining_qty"] = merged["ordered_total"] - merged["sold_total"]
    
    # Calculate shortage (negative remaining = oversold)
    merged["shortage_qty"] = merged["remaining_qty"].apply(lambda x: abs(x) if x < 0 else 0)
    
    # Calculate leftover (positive remaining = inventory left)
    merged["leftover_qty"] = merged["remaining_qty"].apply(lambda x: x if x > 0 else 0)
    
    # Clean up: prefer non-suffixed display fields
    for field in ["drug_name", "strength", "manufacturer", "ndc"]:
        ordered_field = f"{field}_ordered"
        sold_field = f"{field}_sold"
        
        if ordered_field in merged.columns and sold_field in merged.columns:
            # Prefer non-null value, or ordered if both present
            merged[field] = merged[ordered_field].fillna(merged[sold_field])
            # Drop suffixed columns
            merged = merged.drop(columns=[ordered_field, sold_field], errors="ignore")
        elif ordered_field in merged.columns:
            merged[field] = merged[ordered_field]
            merged = merged.drop(columns=[ordered_field], errors="ignore")
        elif sold_field in merged.columns:
            merged[field] = merged[sold_field]
            merged = merged.drop(columns=[sold_field], errors="ignore")
    
    # Reorder columns for readability
    priority_cols = [
        "medicine_key",
        "drug_name",
        "strength",
        "manufacturer",
        "ndc",
        "ordered_total",
        "sold_total",
        "remaining_qty",
        "shortage_qty",
        "leftover_qty",
    ]
    
    other_cols = [c for c in merged.columns if c not in priority_cols]
    final_cols = [c for c in priority_cols if c in merged.columns] + other_cols
    
    result = merged[final_cols].copy()
    
    logger.info(f"Reconciled {len(result)} medicines")
    logger.info(f"  Total ordered: {result['ordered_total'].sum():.0f}")
    logger.info(f"  Total sold: {result['sold_total'].sum():.0f}")
    logger.info(f"  Total remaining: {result['remaining_qty'].sum():.0f}")
    logger.info(f"  Shortages: {(result['shortage_qty'] > 0).sum()}")
    logger.info(f"  Leftovers: {(result['leftover_qty'] > 0).sum()}")
    
    return result


def generate_summary(reconciled_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate summary statistics from reconciled data.
    
    Args:
        reconciled_df: DataFrame from reconcile_inventory
        
    Returns:
        Dictionary with summary statistics
    """
    if len(reconciled_df) == 0:
        return {
            "total_medicines": 0,
            "total_ordered": 0,
            "total_sold": 0,
            "total_remaining": 0,
            "total_shortage": 0,
            "total_leftover": 0,
            "medicines_with_shortage": 0,
            "medicines_with_leftover": 0,
        }
    
    summary = {
        "total_medicines": len(reconciled_df),
        "total_ordered": float(reconciled_df["ordered_total"].sum()),
        "total_sold": float(reconciled_df["sold_total"].sum()),
        "total_remaining": float(reconciled_df["remaining_qty"].sum()),
        "total_shortage": float(reconciled_df["shortage_qty"].sum()),
        "total_leftover": float(reconciled_df["leftover_qty"].sum()),
        "medicines_with_shortage": int((reconciled_df["shortage_qty"] > 0).sum()),
        "medicines_with_leftover": int((reconciled_df["leftover_qty"] > 0).sum()),
    }
    
    # Add percentages
    if summary["total_ordered"] > 0:
        summary["sold_percentage"] = (summary["total_sold"] / summary["total_ordered"]) * 100
    else:
        summary["sold_percentage"] = 0.0
    
    return summary

