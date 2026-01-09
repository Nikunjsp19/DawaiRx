"""Medicine key generation for grouping medications"""

from typing import Optional
import logging

from src.normalization.ndc import normalize_ndc
from src.normalization.text import normalize_drug_name, normalize_strength, normalize_manufacturer

logger = logging.getLogger(__name__)


def generate_medicine_key(
    ndc: Optional[str] = None,
    drug_name: Optional[str] = None,
    strength: Optional[str] = None,
    manufacturer: Optional[str] = None
) -> str:
    """
    Generate a unique medicine key for grouping.
    
    Strategy:
    1. Prefer normalized NDC (11 digits) if valid
    2. Fallback: normalized(drug_name + strength + manufacturer)
    
    Args:
        ndc: NDC code
        drug_name: Drug name
        strength: Dosage strength
        manufacturer: Manufacturer name
        
    Returns:
        Medicine key string
    """
    # Try NDC first
    if ndc:
        normalized_ndc = normalize_ndc(ndc)
        if normalized_ndc:
            return f"NDC:{normalized_ndc}"
    
    # Fallback to composite key
    parts = []
    
    if drug_name:
        normalized_name = normalize_drug_name(drug_name)
        if normalized_name:
            parts.append(normalized_name)
    
    if strength:
        normalized_strength = normalize_strength(strength)
        if normalized_strength:
            parts.append(normalized_strength)
    
    if manufacturer:
        normalized_mfr = normalize_manufacturer(manufacturer)
        if normalized_mfr:
            parts.append(normalized_mfr)
    
    if parts:
        composite_key = "|".join(parts)
        return f"COMPOSITE:{composite_key}"
    
    # Last resort: use whatever we have
    logger.warning("Could not generate medicine key - missing all fields")
    return "UNKNOWN"


def extract_medicine_key_components(medicine_key: str) -> dict:
    """
    Extract components from a medicine key.
    
    Args:
        medicine_key: Medicine key string
        
    Returns:
        Dictionary with key type and components
    """
    if medicine_key.startswith("NDC:"):
        return {
            "type": "ndc",
            "ndc": medicine_key[4:],
            "original_key": medicine_key,
        }
    elif medicine_key.startswith("COMPOSITE:"):
        parts = medicine_key[10:].split("|")
        return {
            "type": "composite",
            "drug_name": parts[0] if len(parts) > 0 else None,
            "strength": parts[1] if len(parts) > 1 else None,
            "manufacturer": parts[2] if len(parts) > 2 else None,
            "original_key": medicine_key,
        }
    else:
        return {
            "type": "unknown",
            "original_key": medicine_key,
        }

