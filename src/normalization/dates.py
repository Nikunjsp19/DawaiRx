"""Date parsing and normalization"""

import pandas as pd
from typing import Optional, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def parse_date(date_value: Union[str, datetime, pd.Timestamp, float, None]) -> Optional[pd.Timestamp]:
    """
    Safely parse a date value into pandas Timestamp.
    
    Args:
        date_value: Date as string, datetime, Timestamp, or None
        
    Returns:
        pandas Timestamp or None if invalid/unparseable
    """
    if date_value is None:
        return None
    
    # Already a Timestamp
    if isinstance(date_value, pd.Timestamp):
        return date_value
    
    # Already a datetime
    if isinstance(date_value, datetime):
        return pd.Timestamp(date_value)
    
    # String or numeric
    if pd.isna(date_value):
        return None
    
    try:
        # Try pandas to_datetime (handles many formats)
        parsed = pd.to_datetime(date_value, errors='coerce')
        if pd.isna(parsed):
            return None
        return parsed
    except Exception as e:
        logger.debug(f"Failed to parse date '{date_value}': {e}")
        return None


def format_date(date_value: Optional[pd.Timestamp], format: str = "%Y-%m-%d") -> Optional[str]:
    """
    Format a date for display.
    
    Args:
        date_value: pandas Timestamp
        format: strftime format string (default: "%Y-%m-%d")
        
    Returns:
        Formatted date string or None
    """
    if date_value is None or pd.isna(date_value):
        return None
    
    try:
        return date_value.strftime(format)
    except Exception:
        return None

