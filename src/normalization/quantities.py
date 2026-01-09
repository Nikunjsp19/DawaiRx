"""Quantity/numeric field normalization"""

import pandas as pd
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


def parse_quantity(qty: Union[str, int, float, None]) -> Optional[float]:
    """
    Parse quantity to numeric value.
    
    Args:
        qty: Quantity value (string, int, float, or None)
        
    Returns:
        Numeric quantity or None if invalid
    """
    if qty is None:
        return None
    
    if pd.isna(qty):
        return None
    
    # Already numeric
    if isinstance(qty, (int, float)):
        if pd.isna(qty):
            return None
        return float(qty)
    
    # String: try to parse
    if isinstance(qty, str):
        qty_str = str(qty).strip()
        if not qty_str or qty_str.lower() in ['nan', 'none', 'null', '']:
            return None
        
        try:
            # Remove common formatting (commas, currency symbols)
            qty_clean = qty_str.replace(',', '').replace('$', '').strip()
            parsed = float(qty_clean)
            return parsed if not pd.isna(parsed) else None
        except (ValueError, TypeError):
            logger.debug(f"Could not parse quantity: {qty}")
            return None
    
    return None


def normalize_quantity(qty: Union[str, int, float, None]) -> float:
    """
    Normalize quantity, defaulting to 0 if invalid.
    
    Args:
        qty: Quantity value
        
    Returns:
        Numeric quantity (defaults to 0.0 if invalid)
    """
    parsed = parse_quantity(qty)
    return parsed if parsed is not None else 0.0

