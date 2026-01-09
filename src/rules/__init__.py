"""Rules engine for audit issue detection"""

from src.rules.base import Rule, RuleRegistry
from src.rules.implementations import (
    R001_DuplicateClaim,
    R002_InvalidNDC,
    R003_SoldNotInOrdered,
    R004_NegativeOrZeroQuantity,
    R005_OverSold,
    R006_SuspiciousDaysSupply,
    R007_MissingCriticalFields,
    create_default_registry,
)

try:
    from src.rules.implementations_extended import (
        R008_ExcessiveQuantity,
        R009_PriceAnomaly,
        R010_MissingNDC,
        R011_DateAnomaly,
        R012_QuantityMismatch,
        R013_InvalidMedicineKey,
        R014_ConcurrentFills,
        R015_RefillTooSoon,
        create_extended_registry,
    )
    EXTENDED_RULES_AVAILABLE = True
except ImportError:
    EXTENDED_RULES_AVAILABLE = False

__all__ = [
    "Rule",
    "RuleRegistry",
    "R001_DuplicateClaim",
    "R002_InvalidNDC",
    "R003_SoldNotInOrdered",
    "R004_NegativeOrZeroQuantity",
    "R005_OverSold",
    "R006_SuspiciousDaysSupply",
    "R007_MissingCriticalFields",
    "create_default_registry",
]

if EXTENDED_RULES_AVAILABLE:
    __all__.extend([
        "R008_ExcessiveQuantity",
        "R009_PriceAnomaly",
        "R010_MissingNDC",
        "R011_DateAnomaly",
        "R012_QuantityMismatch",
        "R013_InvalidMedicineKey",
        "R014_ConcurrentFills",
        "R015_RefillTooSoon",
        "create_extended_registry",
    ])
