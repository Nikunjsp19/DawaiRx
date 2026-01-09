"""Implementation of audit rules"""

import pandas as pd
from typing import List, Dict, Any
import logging

from src.rules.base import Rule, RuleRegistry

logger = logging.getLogger(__name__)


class R001_DuplicateClaim(Rule):
    """R001: Duplicate claim/row (same rx_number + fill_number + claim_date)"""
    
    def __init__(self):
        super().__init__("R001", "Duplicate Claim/Row", severity="high")
    
    def check(self, data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        issues = []
        
        # Check sold data for duplicates
        sold_df = data.get("sold")
        if sold_df is None or len(sold_df) == 0:
            return issues
        
        # Check if required columns exist
        required_cols = ["rx_number", "fill_number", "claim_date"]
        if not all(col in sold_df.columns for col in required_cols):
            return issues  # Can't check without required columns
        
        # Find duplicates
        duplicates = sold_df.duplicated(subset=required_cols, keep=False)
        if duplicates.any():
            dup_rows = sold_df[duplicates]
            for idx, row in dup_rows.iterrows():
                issues.append(self.create_issue(
                    details=f"Duplicate claim: rx_number={row.get('rx_number')}, "
                           f"fill_number={row.get('fill_number')}, "
                           f"claim_date={row.get('claim_date')}",
                    medicine_key=row.get("medicine_key"),
                    row_ref={"source": "sold", "row_number": int(idx) + 1},
                    raw_snippet={
                        "rx_number": str(row.get("rx_number", "")),
                        "fill_number": str(row.get("fill_number", "")),
                        "claim_date": str(row.get("claim_date", "")),
                    }
                ))
        
        return issues


class R002_InvalidNDC(Rule):
    """R002: Invalid NDC format (not 10/11 digits after cleanup)"""
    
    def __init__(self):
        super().__init__("R002", "Invalid NDC Format", severity="high")
    
    def check(self, data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        issues = []
        
        from src.normalization.ndc import normalize_ndc
        
        # Check both ordered and sold
        for source_name, df in [("ordered", data.get("ordered")), ("sold", data.get("sold"))]:
            if df is None or len(df) == 0 or "ndc" not in df.columns:
                continue
            
            # Check each NDC
            for idx, row in df.iterrows():
                ndc = row.get("ndc")
                if pd.isna(ndc) or ndc is None:
                    continue  # Missing NDC is handled by R007
                
                normalized = normalize_ndc(str(ndc))
                if normalized is None:
                    issues.append(self.create_issue(
                        details=f"Invalid NDC format: '{ndc}' (must be 10 or 11 digits)",
                        medicine_key=row.get("medicine_key"),
                        row_ref={"source": source_name, "row_number": int(idx) + 1},
                        raw_snippet={"ndc": str(ndc)}
                    ))
        
        return issues


class R003_SoldNotInOrdered(Rule):
    """R003: Sold item not found in ordered set (medicine_key present in sold but not ordered)"""
    
    def __init__(self):
        super().__init__("R003", "Sold Item Not in Ordered Set", severity="high")
    
    def check(self, data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        issues = []
        
        ordered_df = data.get("ordered")
        sold_df = data.get("sold")
        reconciled_df = data.get("reconciled")
        
        if reconciled_df is None or len(reconciled_df) == 0:
            return issues
        
        # Find medicines in sold but not in ordered (ordered_total == 0)
        missing = reconciled_df[
            (reconciled_df["ordered_total"] == 0) & 
            (reconciled_df["sold_total"] > 0)
        ]
        
        for _, row in missing.iterrows():
            issues.append(self.create_issue(
                details=f"Medicine sold but not found in ordered set: "
                       f"{row.get('drug_name', 'Unknown')} "
                       f"(sold_qty={row.get('sold_total', 0):.0f})",
                medicine_key=row.get("medicine_key"),
                row_ref={},
                raw_snippet={
                    "drug_name": str(row.get("drug_name", "")),
                    "ndc": str(row.get("ndc", "")),
                    "sold_total": float(row.get("sold_total", 0)),
                }
            ))
        
        return issues


class R004_NegativeOrZeroQuantity(Rule):
    """R004: Negative or zero quantities (qty <= 0)"""
    
    def __init__(self):
        super().__init__("R004", "Negative or Zero Quantity", severity="medium")
    
    def check(self, data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        issues = []
        
        # Check ordered quantities
        ordered_df = data.get("ordered")
        if ordered_df is not None and len(ordered_df) > 0:
            qty_field = "ordered_qty" if "ordered_qty" in ordered_df.columns else "quantity"
            if qty_field in ordered_df.columns:
                invalid = ordered_df[ordered_df[qty_field] <= 0]
                for idx, row in invalid.iterrows():
                    issues.append(self.create_issue(
                        details=f"Ordered quantity is zero or negative: {row.get(qty_field)}",
                        medicine_key=row.get("medicine_key"),
                        row_ref={"source": "ordered", "row_number": int(idx) + 1},
                        raw_snippet={qty_field: float(row.get(qty_field, 0))}
                    ))
        
        # Check sold quantities
        sold_df = data.get("sold")
        if sold_df is not None and len(sold_df) > 0:
            qty_field = "sold_qty" if "sold_qty" in sold_df.columns else "quantity"
            if qty_field in sold_df.columns:
                invalid = sold_df[sold_df[qty_field] <= 0]
                for idx, row in invalid.iterrows():
                    issues.append(self.create_issue(
                        details=f"Sold quantity is zero or negative: {row.get(qty_field)}",
                        medicine_key=row.get("medicine_key"),
                        row_ref={"source": "sold", "row_number": int(idx) + 1},
                        raw_snippet={qty_field: float(row.get(qty_field, 0))}
                    ))
        
        return issues


class R005_OverSold(Rule):
    """R005: Over-sold (sold_qty > ordered_qty at medicine level)"""
    
    def __init__(self):
        super().__init__("R005", "Over-Sold", severity="high")
    
    def check(self, data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        issues = []
        
        reconciled_df = data.get("reconciled")
        if reconciled_df is None or len(reconciled_df) == 0:
            return issues
        
        # Find medicines where sold > ordered
        oversold = reconciled_df[reconciled_df["shortage_qty"] > 0]
        
        for _, row in oversold.iterrows():
            issues.append(self.create_issue(
                details=f"Over-sold: sold {row.get('sold_total', 0):.0f} but only "
                       f"{row.get('ordered_total', 0):.0f} ordered "
                       f"(shortage: {row.get('shortage_qty', 0):.0f})",
                medicine_key=row.get("medicine_key"),
                row_ref={},
                raw_snippet={
                    "drug_name": str(row.get("drug_name", "")),
                    "ordered_total": float(row.get("ordered_total", 0)),
                    "sold_total": float(row.get("sold_total", 0)),
                    "shortage_qty": float(row.get("shortage_qty", 0)),
                }
            ))
        
        return issues


class R006_SuspiciousDaysSupply(Rule):
    """R006: Suspicious days_supply (outside 1..120) if column exists"""
    
    def __init__(self):
        super().__init__("R006", "Suspicious Days Supply", severity="low")
    
    def check(self, data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        issues = []
        
        sold_df = data.get("sold")
        if sold_df is None or len(sold_df) == 0 or "days_supply" not in sold_df.columns:
            return issues
        
        # Find rows with days_supply outside 1-120
        invalid = sold_df[
            (sold_df["days_supply"] < 1) | (sold_df["days_supply"] > 120)
        ]
        
        for idx, row in invalid.iterrows():
            days = row.get("days_supply")
            issues.append(self.create_issue(
                details=f"Days supply outside normal range (1-120): {days}",
                medicine_key=row.get("medicine_key"),
                row_ref={"source": "sold", "row_number": int(idx) + 1},
                raw_snippet={"days_supply": float(days) if pd.notna(days) else None}
            ))
        
        return issues


class R007_MissingCriticalFields(Rule):
    """R007: Missing critical fields (ndc or drug_name, quantity)"""
    
    def __init__(self):
        super().__init__("R007", "Missing Critical Fields", severity="high")
    
    def check(self, data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        issues = []
        
        # Check ordered data
        ordered_df = data.get("ordered")
        if ordered_df is not None and len(ordered_df) > 0:
            qty_field = "ordered_qty" if "ordered_qty" in ordered_df.columns else "quantity"
            
            for idx, row in ordered_df.iterrows():
                missing = []
                
                # Check NDC or drug_name
                has_ndc = pd.notna(row.get("ndc")) and str(row.get("ndc")).strip() != ""
                has_drug_name = pd.notna(row.get("drug_name")) and str(row.get("drug_name")).strip() != ""
                
                if not has_ndc and not has_drug_name:
                    missing.append("ndc or drug_name")
                
                # Check quantity
                if qty_field in ordered_df.columns:
                    has_qty = pd.notna(row.get(qty_field)) and row.get(qty_field) != 0
                    if not has_qty:
                        missing.append(qty_field)
                
                if missing:
                    issues.append(self.create_issue(
                        details=f"Missing critical fields: {', '.join(missing)}",
                        medicine_key=row.get("medicine_key"),
                        row_ref={"source": "ordered", "row_number": int(idx) + 1},
                        raw_snippet={}
                    ))
        
        # Check sold data
        sold_df = data.get("sold")
        if sold_df is not None and len(sold_df) > 0:
            qty_field = "sold_qty" if "sold_qty" in sold_df.columns else "quantity"
            
            for idx, row in sold_df.iterrows():
                missing = []
                
                # Check NDC or drug_name
                has_ndc = pd.notna(row.get("ndc")) and str(row.get("ndc")).strip() != ""
                has_drug_name = pd.notna(row.get("drug_name")) and str(row.get("drug_name")).strip() != ""
                
                if not has_ndc and not has_drug_name:
                    missing.append("ndc or drug_name")
                
                # Check quantity
                if qty_field in sold_df.columns:
                    has_qty = pd.notna(row.get(qty_field)) and row.get(qty_field) != 0
                    if not has_qty:
                        missing.append(qty_field)
                
                if missing:
                    issues.append(self.create_issue(
                        details=f"Missing critical fields: {', '.join(missing)}",
                        medicine_key=row.get("medicine_key"),
                        row_ref={"source": "sold", "row_number": int(idx) + 1},
                        raw_snippet={}
                    ))
        
        return issues


def create_default_registry() -> RuleRegistry:
    """Create and register all default rules."""
    registry = RuleRegistry()
    
    registry.register(R001_DuplicateClaim())
    registry.register(R002_InvalidNDC())
    registry.register(R003_SoldNotInOrdered())
    registry.register(R004_NegativeOrZeroQuantity())
    registry.register(R005_OverSold())
    registry.register(R006_SuspiciousDaysSupply())
    registry.register(R007_MissingCriticalFields())
    
    return registry

