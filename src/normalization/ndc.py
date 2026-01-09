"""NDC (National Drug Code) normalization"""

import re
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


def normalize_ndc(ndc: Union[str, float, None]) -> Optional[str]:
    """
    Normalize NDC to 11-digit format.
    
    NDC formats:
    - 10-digit: 12345-6789-0 (labeler-product-package)
    - 11-digit: 12345-6789-01 (padded package)
    - Various separators: hyphens, spaces, or none
    
    Args:
        ndc: NDC code as string (may contain hyphens, spaces)
        
    Returns:
        11-digit NDC string (no separators) or None if invalid
    """
    if ndc is None:
        return None
    
    # Convert to string and strip
    ndc_str = str(ndc).strip()
    
    if not ndc_str or ndc_str.lower() in ['nan', 'none', 'null', '']:
        return None
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', ndc_str)
    
    # Validate length
    if len(digits_only) < 10 or len(digits_only) > 11:
        logger.debug(f"Invalid NDC length: {ndc} -> {digits_only} (length {len(digits_only)})")
        return None
    
    # Convert to 11-digit format
    if len(digits_only) == 10:
        # 10-digit: assume format is 5-4-1, pad package to 2 digits
        # Format: LLLLL-PPPP-P -> LLLLL-PPPP-0P
        labeler = digits_only[:5]
        product = digits_only[5:9]
        package = digits_only[9:]
        # Pad package to 2 digits
        normalized = f"{labeler}{product}0{package}"
    elif len(digits_only) == 11:
        # Already 11 digits
        normalized = digits_only
    else:
        return None
    
    # Validate: should be exactly 11 digits
    if len(normalized) != 11 or not normalized.isdigit():
        return None
    
    return normalized


def format_ndc_display(ndc: str) -> str:
    """
    Format 11-digit NDC for display (5-4-2 format).
    
    Args:
        ndc: 11-digit NDC string
        
    Returns:
        Formatted NDC string (e.g., "12345-6789-01")
    """
    if not ndc or len(ndc) != 11:
        return ndc
    
    return f"{ndc[:5]}-{ndc[5:9]}-{ndc[9:]}"


def is_valid_ndc(ndc: str) -> bool:
    """
    Check if NDC is valid (can be normalized).
    
    Args:
        ndc: NDC code to validate
        
    Returns:
        True if valid, False otherwise
    """
    normalized = normalize_ndc(ndc)
    return normalized is not None

