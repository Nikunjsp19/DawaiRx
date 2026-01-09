"""Text field normalization"""

import re
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


def normalize_text(text: Union[str, float, None], case: str = "upper") -> Optional[str]:
    """
    Normalize text field: strip, collapse spaces, apply case.
    
    Args:
        text: Text to normalize
        case: "upper", "lower", or "title" (default: "upper")
        
    Returns:
        Normalized text or None if input is empty/null
    """
    if text is None:
        return None
    
    # Convert to string
    text_str = str(text).strip()
    
    # Check for null-like values
    if not text_str or text_str.lower() in ['nan', 'none', 'null', '']:
        return None
    
    # Collapse multiple spaces to single space
    text_str = re.sub(r'\s+', ' ', text_str)
    
    # Apply case
    if case == "upper":
        text_str = text_str.upper()
    elif case == "lower":
        text_str = text_str.lower()
    elif case == "title":
        text_str = text_str.title()
    # else: keep as-is
    
    return text_str


def normalize_drug_name(name: Union[str, float, None]) -> Optional[str]:
    """
    Normalize drug name (typically uppercase, collapsed spaces).
    
    Args:
        name: Drug name to normalize
        
    Returns:
        Normalized drug name
    """
    return normalize_text(name, case="upper")


def normalize_manufacturer(mfr: Union[str, float, None]) -> Optional[str]:
    """
    Normalize manufacturer name.
    
    Args:
        mfr: Manufacturer name to normalize
        
    Returns:
        Normalized manufacturer name
    """
    return normalize_text(mfr, case="upper")


def normalize_strength(strength: Union[str, float, None]) -> Optional[str]:
    """
    Normalize strength/dosage field.
    
    Args:
        strength: Strength to normalize
        
    Returns:
        Normalized strength
    """
    return normalize_text(strength, case="upper")

