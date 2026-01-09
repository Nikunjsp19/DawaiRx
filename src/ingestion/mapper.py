"""Column mapping system for flexible field mapping"""

import re
from typing import Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)

# Canonical field names
CANONICAL_FIELDS = {
    "drug_name": [
        "drug_name", "drug", "medication", "med_name", "product_name",
        "drug name", "drugname", "drug_name", "medication_name"
    ],
    "ndc": [
        "ndc", "ndc_code", "ndc11", "ndc_11", "national_drug_code",
        "ndc number", "ndcnumber", "ndc_number", "ndc_code"
    ],
    "strength": ["strength", "dosage", "dose", "dosage_strength"],
    "manufacturer": ["manufacturer", "mfr", "maker", "manufacturer_name"],
    "quantity": [
        "quantity", "qty", "qty_dispensed", "quantity_dispensed", "amount",
        "qty_disp", "dispensed_qty"
    ],
    "ordered_qty": [
        "ordered_qty", "ordered_quantity", "qty_ordered", "order_qty",
        "ordered qty", "orderedqty"
    ],
    "sold_qty": [
        "sold_qty", "sold_quantity", "qty_sold", "sold",
        "quantity", "qty", "qty_dispensed", "quantity_dispensed"
    ],
    "rx_number": [
        "rx_number", "rx_num", "prescription_number", "rx_no", "rx#",
        "rx number", "rxnumber", "prescription number"
    ],
    "fill_number": [
        "fill_number", "fill_num", "fill_no", "fill#",
        "fill number", "fillnumber"
    ],
    "claim_date": [
        "claim_date", "date", "fill_date", "dispense_date", "transaction_date",
        "date filled", "datefilled", "date_filled", "fill date", "dispense date"
    ],
    "order_date": [
        "order_date", "ordered_date", "invoice_date", "invoice date", "order date",
        "purchase_date", "purchase date", "invoice_date", "invoice date"
    ],
    "days_supply": ["days_supply", "days", "supply_days", "days supply"],
    # Additional fields for inventory reports
    "pkg_size": ["pkg_size", "pkg size", "package_size", "package size", "pkgsize"],
    "pkg_size_qty": [
        "pkg_size_qty", "pkg size qty", "package_size_qty",
        "package size qty", "pkgsizeqty"
    ],
    "primary_insurance_bin": [
        "primary_insurance_bin_number", "primary insurance bin number",
        "primary_insurance_bin", "primary insurance bin", "bin_number"
    ],
    "primary_insurance_paid": [
        "primary_insurance_paid", "primary insurance paid",
        "insurance_paid", "insurance paid"
    ],
    "primary_insurance_name": [
        "primary_insurance_name", "primary insurance name",
        "insurance_name", "insurance name"
    ],
    "secondary_insurance_bin": [
        "secondary_insurance_bin_number", "secondary insurance bin number",
        "secondary_insurance_bin", "secondary insurance bin"
    ],
    "secondary_insurance_paid": [
        "secondary_insurance_paid", "secondary insurance paid"
    ],
    "secondary_insurance_name": [
        "secondary_insurance_name", "secondary insurance name"
    ],
}

# Required fields for ordered and sold reports
# Note: quantity gets mapped to ordered_qty or sold_qty based on report type
REQUIRED_FIELDS_ORDERED = {"drug_name", "ndc", "ordered_qty"}
REQUIRED_FIELDS_SOLD = {"drug_name", "ndc", "sold_qty"}


def normalize_column_name(col: str) -> str:
    """Normalize column name for matching."""
    # Convert to lowercase, strip whitespace, replace spaces/special chars with underscore
    normalized = re.sub(r'[^\w]', '_', col.lower().strip())
    # Collapse multiple underscores
    normalized = re.sub(r'_+', '_', normalized)
    return normalized


def guess_canonical_field(column_name: str) -> Optional[str]:
    """
    Guess canonical field name from a column name using fuzzy matching.
    
    Args:
        column_name: Original column name
        
    Returns:
        Canonical field name or None if no match
    """
    normalized = normalize_column_name(column_name)
    
    # Special handling for common variations
    # Handle "NDC NUMBER" -> "ndc"
    if "ndc" in normalized and ("number" in normalized or "code" in normalized):
        return "ndc"
    if normalized in ["ndc_number", "ndcnumber", "ndc_code", "ndccode"]:
        return "ndc"
    
    # Handle "DRUG NAME" -> "drug_name"
    if "drug" in normalized and "name" in normalized:
        return "drug_name"
    if normalized in ["drug_name", "drugname"]:
        return "drug_name"
    # Handle "ITEM DESCRIPTION" -> "drug_name" (common in supplier reports)
    if ("item" in normalized and "description" in normalized) or normalized in ["item_description", "itemdescription"]:
        return "drug_name"
    
    # Handle "DATE FILLED" -> "claim_date"
    if ("date" in normalized and "filled" in normalized) or normalized == "datefilled":
        return "claim_date"
    if normalized in ["date_filled", "fill_date", "filldate", "dispense_date"]:
        return "claim_date"
    
    # Handle "QUANTITY" -> "quantity" (will be converted to sold_qty/ordered_qty based on report type)
    if normalized in ["quantity", "qty", "qty_dispensed", "quantity_dispensed"]:
        return "quantity"
    
    # Direct match
    for canonical, variants in CANONICAL_FIELDS.items():
        canonical_normalized = normalize_column_name(canonical)
        if normalized == canonical_normalized:
            return canonical
        # Check variants
        for variant in variants:
            variant_normalized = normalize_column_name(variant)
            if normalized == variant_normalized:
                return canonical
    
    # Partial match (contains) - check if normalized contains key terms
    if "pkg" in normalized and "size" in normalized:
        if "qty" in normalized:
            return "pkg_size_qty"
        return "pkg_size"
    
    if "insurance" in normalized:
        if "primary" in normalized:
            if "bin" in normalized:
                return "primary_insurance_bin"
            if "paid" in normalized:
                return "primary_insurance_paid"
            if "name" in normalized:
                return "primary_insurance_name"
        elif "secondary" in normalized:
            if "bin" in normalized:
                return "secondary_insurance_bin"
            if "paid" in normalized:
                return "secondary_insurance_paid"
            if "name" in normalized:
                return "secondary_insurance_name"
    
    return None


def create_mapping_from_columns(columns: List[str], report_type: str = "auto") -> Dict[str, str]:
    """
    Create a column mapping by guessing canonical fields from column names.
    
    Args:
        columns: List of column names from the file
        report_type: "ordered", "sold", or "auto"
        
    Returns:
        Dictionary mapping original column names to canonical field names
    """
    mapping = {}
    
    for col in columns:
        canonical = guess_canonical_field(col)
        if canonical:
            # Handle special case: quantity field depends on report type
            if canonical == "quantity":
                if report_type == "ordered":
                    canonical = "ordered_qty"
                elif report_type == "sold":
                    canonical = "sold_qty"
            mapping[col] = canonical
            logger.debug(f"Mapped '{col}' -> '{canonical}'")
    
    return mapping


def apply_mapping(df_columns: List[str], mapping: Dict[str, str]) -> Dict[str, str]:
    """
    Apply a mapping configuration to rename columns.
    
    Args:
        df_columns: Original column names from DataFrame
        mapping: Mapping dictionary (original -> canonical)
        
    Returns:
        Dictionary of columns to rename (for df.rename)
    """
    rename_map = {}
    unmapped = set(df_columns)
    
    for orig_col, canonical in mapping.items():
        # Try exact match first
        if orig_col in df_columns:
            rename_map[orig_col] = canonical
            unmapped.discard(orig_col)
        else:
            # Try case-insensitive match
            for col in df_columns:
                if normalize_column_name(col) == normalize_column_name(orig_col):
                    rename_map[col] = canonical
                    unmapped.discard(col)
                    break
    
    if unmapped:
        logger.warning(f"Unmapped columns: {unmapped}")
    
    return rename_map


def validate_mapping(
    mapping: Dict[str, str],
    df_columns: List[str],
    required_fields: Set[str],
    report_type: str
) -> tuple[bool, List[str]]:
    """
    Validate that mapping covers required fields.
    
    Args:
        mapping: Column mapping
        df_columns: Original column names
        required_fields: Set of required canonical field names
        report_type: "ordered" or "sold"
        
    Returns:
        Tuple of (is_valid, list of missing fields)
    """
    # Get mapped canonical fields
    mapped_canonical = set(mapping.values())
    
    # Check required fields
    missing = []
    for req_field in required_fields:
        if req_field not in mapped_canonical:
            missing.append(req_field)
    
    # Check that mapped columns exist in DataFrame
    invalid_cols = []
    for orig_col in mapping.keys():
        if orig_col not in df_columns:
            # Try case-insensitive
            found = False
            for col in df_columns:
                if normalize_column_name(col) == normalize_column_name(orig_col):
                    found = True
                    break
            if not found:
                invalid_cols.append(orig_col)
    
    if invalid_cols:
        logger.warning(f"Mapping references non-existent columns: {invalid_cols}")
    
    is_valid = len(missing) == 0
    
    return is_valid, missing

