"""Extended audit rules matching DawaiRx functionality"""

import pandas as pd
from typing import List, Dict, Any
import logging

from src.rules.base import Rule

logger = logging.getLogger(__name__)


class R008_ExcessiveQuantity(Rule):
    """R008: Excessive quantity dispensed (unusually high quantity)"""
    
    def __init__(self, threshold: float = 1000.0):
        super().__init__("R008", "Excessive Quantity", severity="medium")
        self.threshold = threshold
    
    def check(self, data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        issues = []
        
        sold_df = data.get("sold")
        if sold_df is None or len(sold_df) == 0:
            return issues
        
        qty_field = "sold_qty" if "sold_qty" in sold_df.columns else "quantity"
        if qty_field not in sold_df.columns:
            return issues
        
        excessive = sold_df[sold_df[qty_field] > self.threshold]
        for idx, row in excessive.iterrows():
            issues.append(self.create_issue(
                details=f"Excessive quantity: {row.get(qty_field):.0f} (threshold: {self.threshold})",
                medicine_key=row.get("medicine_key"),
                row_ref={"source": "sold", "row_number": int(idx) + 1},
                raw_snippet={qty_field: float(row.get(qty_field, 0))}
            ))
        
        return issues


class R009_PriceAnomaly(Rule):
    """R009: Price anomaly (unusually high or low unit price)"""
    
    def __init__(self, min_price: float = 0.01, max_price: float = 10000.0):
        super().__init__("R009", "Price Anomaly", severity="low")
        self.min_price = min_price
        self.max_price = max_price
    
    def check(self, data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        issues = []
        
        sold_df = data.get("sold")
        if sold_df is None or len(sold_df) == 0:
            return issues
        
        # Check if price fields exist
        price_fields = ["unit_price", "price", "cost", "amount"]
        price_field = None
        for field in price_fields:
            if field in sold_df.columns:
                price_field = field
                break
        
        if not price_field:
            return issues
        
        anomalies = sold_df[
            (sold_df[price_field] < self.min_price) | 
            (sold_df[price_field] > self.max_price)
        ]
        
        for idx, row in anomalies.iterrows():
            price = row.get(price_field)
            issue_type = "too low" if price < self.min_price else "too high"
            issues.append(self.create_issue(
                details=f"Price anomaly: ${price:.2f} is {issue_type} (expected: ${self.min_price:.2f} - ${self.max_price:.2f})",
                medicine_key=row.get("medicine_key"),
                row_ref={"source": "sold", "row_number": int(idx) + 1},
                raw_snippet={price_field: float(price)}
            ))
        
        return issues


class R010_MissingNDC(Rule):
    """R010: Missing NDC when drug_name is present"""
    
    def __init__(self):
        super().__init__("R010", "Missing NDC", severity="high")
    
    def check(self, data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        issues = []
        
        for source_name, df in [("ordered", data.get("ordered")), ("sold", data.get("sold"))]:
            if df is None or len(df) == 0:
                continue
            
            if "drug_name" not in df.columns or "ndc" not in df.columns:
                continue
            
            missing_ndc = df[
                (df["drug_name"].notna()) & 
                (df["drug_name"].astype(str).str.strip() != "") &
                (df["ndc"].isna() | (df["ndc"].astype(str).str.strip() == ""))
            ]
            
            for idx, row in missing_ndc.iterrows():
                issues.append(self.create_issue(
                    details=f"Drug name present but NDC is missing: {row.get('drug_name')}",
                    medicine_key=row.get("medicine_key"),
                    row_ref={"source": source_name, "row_number": int(idx) + 1},
                    raw_snippet={"drug_name": str(row.get("drug_name", ""))}
                ))
        
        return issues


class R011_DateAnomaly(Rule):
    """R011: Date anomaly (claim date in future or too far in past)"""
    
    def __init__(self):
        super().__init__("R011", "Date Anomaly", severity="medium")
    
    def check(self, data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        issues = []
        
        from datetime import datetime, timedelta
        
        sold_df = data.get("sold")
        if sold_df is None or len(sold_df) == 0 or "claim_date" not in sold_df.columns:
            return issues
        
        today = pd.Timestamp.now()
        max_past_days = 365 * 2  # 2 years
        
        for idx, row in sold_df.iterrows():
            claim_date = row.get("claim_date")
            if pd.isna(claim_date):
                continue
            
            if isinstance(claim_date, pd.Timestamp):
                if claim_date > today:
                    issues.append(self.create_issue(
                        details=f"Future date: {claim_date.strftime('%Y-%m-%d')}",
                        medicine_key=row.get("medicine_key"),
                        row_ref={"source": "sold", "row_number": int(idx) + 1},
                        raw_snippet={"claim_date": str(claim_date)}
                    ))
                elif (today - claim_date).days > max_past_days:
                    issues.append(self.create_issue(
                        details=f"Date too far in past: {claim_date.strftime('%Y-%m-%d')} (more than {max_past_days} days)",
                        medicine_key=row.get("medicine_key"),
                        row_ref={"source": "sold", "row_number": int(idx) + 1},
                        raw_snippet={"claim_date": str(claim_date)}
                    ))
        
        return issues


class R012_QuantityMismatch(Rule):
    """R012: Quantity mismatch between ordered and sold for same medicine"""
    
    def __init__(self, tolerance_percent: float = 5.0):
        super().__init__("R012", "Quantity Mismatch", severity="medium")
        self.tolerance_percent = tolerance_percent
    
    def check(self, data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        issues = []
        
        reconciled_df = data.get("reconciled")
        if reconciled_df is None or len(reconciled_df) == 0:
            return issues
        
        # Find medicines where sold is significantly different from ordered
        for _, row in reconciled_df.iterrows():
            ordered = row.get("ordered_total", 0)
            sold = row.get("sold_total", 0)
            
            if ordered > 0:
                diff_percent = abs((sold - ordered) / ordered) * 100
                if diff_percent > self.tolerance_percent and sold > 0:
                    issues.append(self.create_issue(
                        details=f"Quantity mismatch: Ordered {ordered:.0f}, Sold {sold:.0f} ({diff_percent:.1f}% difference)",
                        medicine_key=row.get("medicine_key"),
                        row_ref={},
                        raw_snippet={
                            "ordered_total": float(ordered),
                            "sold_total": float(sold),
                            "difference_percent": diff_percent
                        }
                    ))
        
        return issues


class R013_InvalidMedicineKey(Rule):
    """R013: Invalid or missing medicine key (cannot identify medicine)"""
    
    def __init__(self):
        super().__init__("R013", "Invalid Medicine Key", severity="high")
    
    def check(self, data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        issues = []
        
        for source_name, df in [("ordered", data.get("ordered")), ("sold", data.get("sold"))]:
            if df is None or len(df) == 0:
                continue
            
            if "medicine_key" not in df.columns:
                continue
            
            invalid_keys = df[
                (df["medicine_key"].isna()) |
                (df["medicine_key"].astype(str).str.strip() == "") |
                (df["medicine_key"].astype(str).str.startswith("UNKNOWN"))
            ]
            
            for idx, row in invalid_keys.iterrows():
                issues.append(self.create_issue(
                    details="Invalid or missing medicine key - cannot identify medicine",
                    medicine_key=None,
                    row_ref={"source": source_name, "row_number": int(idx) + 1},
                    raw_snippet={}
                ))
        
        return issues


class R014_ConcurrentFills(Rule):
    """R014: Concurrent fills (same rx_number with overlapping days_supply)"""
    
    def __init__(self):
        super().__init__("R014", "Concurrent Fills", severity="medium")
    
    def check(self, data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        issues = []
        
        sold_df = data.get("sold")
        if sold_df is None or len(sold_df) == 0:
            return issues
        
        required_cols = ["rx_number", "claim_date", "days_supply"]
        if not all(col in sold_df.columns for col in required_cols):
            return issues
        
        # Group by rx_number and check for overlapping dates
        for rx_num, group in sold_df.groupby("rx_number"):
            if len(group) < 2:
                continue
            
            # Sort by claim_date
            group_sorted = group.sort_values("claim_date")
            
            for i in range(len(group_sorted) - 1):
                row1 = group_sorted.iloc[i]
                row2 = group_sorted.iloc[i + 1]
                
                date1 = pd.to_datetime(row1["claim_date"])
                date2 = pd.to_datetime(row2["claim_date"])
                days1 = row1.get("days_supply", 0)
                
                if pd.notna(days1) and days1 > 0:
                    end_date1 = date1 + pd.Timedelta(days=float(days1))
                    if date2 < end_date1:
                        issues.append(self.create_issue(
                            details=f"Concurrent fills: Fill on {date2.strftime('%Y-%m-%d')} overlaps with fill ending {end_date1.strftime('%Y-%m-%d')}",
                            medicine_key=row2.get("medicine_key"),
                            row_ref={"source": "sold", "row_number": int(row2.name) + 1},
                            raw_snippet={
                                "rx_number": str(rx_num),
                                "claim_date": str(date2),
                                "days_supply": float(days1)
                            }
                        ))
        
        return issues


class R015_RefillTooSoon(Rule):
    """R015: Refill too soon (refill before 80% of days_supply elapsed)"""
    
    def __init__(self, min_days_elapsed_percent: float = 80.0):
        super().__init__("R015", "Refill Too Soon", severity="medium")
        self.min_days_elapsed_percent = min_days_elapsed_percent
    
    def check(self, data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        issues = []
        
        sold_df = data.get("sold")
        if sold_df is None or len(sold_df) == 0:
            return issues
        
        required_cols = ["rx_number", "claim_date", "days_supply", "fill_number"]
        if not all(col in sold_df.columns for col in required_cols):
            return issues
        
        # Group by rx_number
        for rx_num, group in sold_df.groupby("rx_number"):
            if len(group) < 2:
                continue
            
            group_sorted = group.sort_values(["fill_number", "claim_date"])
            
            for i in range(len(group_sorted) - 1):
                row1 = group_sorted.iloc[i]
                row2 = group_sorted.iloc[i + 1]
                
                date1 = pd.to_datetime(row1["claim_date"])
                date2 = pd.to_datetime(row2["claim_date"])
                days1 = row1.get("days_supply", 0)
                
                if pd.notna(days1) and days1 > 0:
                    days_elapsed = (date2 - date1).days
                    days_required = days1 * (self.min_days_elapsed_percent / 100)
                    
                    if days_elapsed < days_required:
                        issues.append(self.create_issue(
                            details=f"Refill too soon: Only {days_elapsed} days elapsed, need {days_required:.0f} days (80% of {days1} days supply)",
                            medicine_key=row2.get("medicine_key"),
                            row_ref={"source": "sold", "row_number": int(row2.name) + 1},
                            raw_snippet={
                                "rx_number": str(rx_num),
                                "fill_number": int(row2.get("fill_number", 0)),
                                "days_elapsed": days_elapsed,
                                "days_required": days_required
                            }
                        ))
        
        return issues


def create_extended_registry():
    """Create registry with all rules including extended DawaiRx-like rules."""
    from src.rules.implementations import (
        R001_DuplicateClaim,
        R002_InvalidNDC,
        R003_SoldNotInOrdered,
        R004_NegativeOrZeroQuantity,
        R005_OverSold,
        R006_SuspiciousDaysSupply,
        R007_MissingCriticalFields,
    )
    from src.rules.base import RuleRegistry
    
    registry = RuleRegistry()
    
    # Original rules
    registry.register(R001_DuplicateClaim())
    registry.register(R002_InvalidNDC())
    registry.register(R003_SoldNotInOrdered())
    registry.register(R004_NegativeOrZeroQuantity())
    registry.register(R005_OverSold())
    registry.register(R006_SuspiciousDaysSupply())
    registry.register(R007_MissingCriticalFields())
    
    # Extended DawaiRx-like rules
    registry.register(R008_ExcessiveQuantity())
    registry.register(R009_PriceAnomaly())
    registry.register(R010_MissingNDC())
    registry.register(R011_DateAnomaly())
    registry.register(R012_QuantityMismatch())
    registry.register(R013_InvalidMedicineKey())
    registry.register(R014_ConcurrentFills())
    registry.register(R015_RefillTooSoon())
    
    return registry

