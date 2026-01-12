"""Main normalization processor"""

import pandas as pd
from typing import Dict, Any, Optional
import logging

from src.normalization.ndc import normalize_ndc
from src.normalization.text import normalize_drug_name, normalize_strength, normalize_manufacturer
from src.normalization.dates import parse_date
from src.normalization.quantities import normalize_quantity
from src.normalization.medicine_key import generate_medicine_key

logger = logging.getLogger(__name__)


def normalize_dataframe(
    df: pd.DataFrame,
    report_type: str,
    preserve_originals: bool = True
) -> pd.DataFrame:
    """
    Normalize a DataFrame with canonical column names.
    
    Args:
        df: DataFrame with canonical column names
        report_type: "ordered" or "sold"
        preserve_originals: If True, keep original columns with _original suffix
        
    Returns:
        Normalized DataFrame with additional normalized columns
    """
    df_normalized = df.copy()
    
    # Normalize NDC
    if "ndc" in df_normalized.columns:
        if preserve_originals and "ndc_original" not in df_normalized.columns:
            df_normalized["ndc_original"] = df_normalized["ndc"]
        df_normalized["ndc_normalized"] = df_normalized["ndc"].apply(normalize_ndc)
        # Update ndc column with normalized values (keep original if normalization fails)
        df_normalized["ndc"] = df_normalized["ndc_normalized"].fillna(df_normalized["ndc"])
    
    # Normalize text fields
    if "drug_name" in df_normalized.columns:
        if preserve_originals and "drug_name_original" not in df_normalized.columns:
            df_normalized["drug_name_original"] = df_normalized["drug_name"]
        # CRITICAL: For DawaiRx compatibility, preserve original drug name format
        # Only normalize if explicitly needed (for matching), but keep original for display
        # The dawairx_format.py will use the original format from sold_df
        # For now, we still normalize for matching purposes, but preserve original
        df_normalized["drug_name"] = df_normalized["drug_name"].apply(normalize_drug_name)
    
    if "strength" in df_normalized.columns:
        if preserve_originals and "strength_original" not in df_normalized.columns:
            df_normalized["strength_original"] = df_normalized["strength"]
        df_normalized["strength"] = df_normalized["strength"].apply(normalize_strength)
    
    if "manufacturer" in df_normalized.columns:
        if preserve_originals and "manufacturer_original" not in df_normalized.columns:
            df_normalized["manufacturer_original"] = df_normalized["manufacturer"]
        df_normalized["manufacturer"] = df_normalized["manufacturer"].apply(normalize_manufacturer)
    
    # Normalize quantities
    qty_field = None
    if report_type == "ordered" and "ordered_qty" in df_normalized.columns:
        qty_field = "ordered_qty"
    elif report_type == "sold" and "sold_qty" in df_normalized.columns:
        qty_field = "sold_qty"
    elif "quantity" in df_normalized.columns:
        qty_field = "quantity"
    
    if qty_field:
        if preserve_originals and f"{qty_field}_original" not in df_normalized.columns:
            df_normalized[f"{qty_field}_original"] = df_normalized[qty_field]
        df_normalized[qty_field] = df_normalized[qty_field].apply(normalize_quantity)
    
    # Parse dates - handle multiple date field names
    # For sold data: claim_date, date_filled, fill_date, dispense_date
    # For ordered data: order_date, invoice_date, purchase_date
    if report_type == "sold":
        date_fields = ["claim_date", "date_filled", "fill_date", "dispense_date"]
    else:  # ordered
        date_fields = ["order_date", "invoice_date", "purchase_date", "claim_date", "date_filled"]
    
    for date_field in date_fields:
        if date_field in df_normalized.columns:
            if preserve_originals and f"{date_field}_original" not in df_normalized.columns:
                df_normalized[f"{date_field}_original"] = df_normalized[date_field]
            df_normalized[date_field] = df_normalized[date_field].apply(parse_date)
            # If we have date_filled but not claim_date, copy it (for sold data)
            if date_field == "date_filled" and "claim_date" not in df_normalized.columns:
                df_normalized["claim_date"] = df_normalized[date_field]
            # If we have invoice_date but not order_date, copy it (for ordered data)
            if date_field == "invoice_date" and "order_date" not in df_normalized.columns:
                df_normalized["order_date"] = df_normalized[date_field]
            break
    
    # Generate medicine key
    df_normalized["medicine_key"] = df_normalized.apply(
        lambda row: generate_medicine_key(
            ndc=row.get("ndc"),
            drug_name=row.get("drug_name"),
            strength=row.get("strength"),
            manufacturer=row.get("manufacturer")
        ),
        axis=1
    )
    
    logger.info(f"Normalized {len(df_normalized)} rows")
    
    return df_normalized

