"""Tests for rules engine"""

import pytest
import pandas as pd

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


class TestRuleRegistry:
    """Test rule registry"""
    
    def test_register_rule(self):
        """Test registering a rule"""
        registry = RuleRegistry()
        rule = R001_DuplicateClaim()
        registry.register(rule)
        
        assert registry.get_rule("R001") == rule
        assert len(registry.get_all_rules()) == 1
    
    def test_create_default_registry(self):
        """Test creating default registry"""
        registry = create_default_registry()
        assert len(registry.get_all_rules()) == 7


class TestR001:
    """Test R001: Duplicate Claim"""
    
    def test_duplicate_claim(self):
        """Test detecting duplicate claims"""
        rule = R001_DuplicateClaim()
        
        sold_df = pd.DataFrame({
            "rx_number": ["RX001", "RX001", "RX002"],
            "fill_number": [1, 1, 1],
            "claim_date": ["2024-01-15", "2024-01-15", "2024-01-16"],
            "medicine_key": ["KEY1", "KEY1", "KEY2"],
        })
        
        issues = rule.check({"sold": sold_df})
        assert len(issues) == 2  # Both duplicates flagged
        assert all(issue["rule_id"] == "R001" for issue in issues)
    
    def test_no_duplicates(self):
        """Test no duplicates case"""
        rule = R001_DuplicateClaim()
        
        sold_df = pd.DataFrame({
            "rx_number": ["RX001", "RX002"],
            "fill_number": [1, 1],
            "claim_date": ["2024-01-15", "2024-01-16"],
        })
        
        issues = rule.check({"sold": sold_df})
        assert len(issues) == 0


class TestR002:
    """Test R002: Invalid NDC"""
    
    def test_invalid_ndc(self):
        """Test detecting invalid NDC"""
        rule = R002_InvalidNDC()
        
        df = pd.DataFrame({
            "ndc": ["123", "12345-6789-01", "invalid"],
            "medicine_key": ["KEY1", "KEY2", "KEY3"],
        })
        
        issues = rule.check({"ordered": df})
        assert len(issues) >= 2  # At least 2 invalid NDCs


class TestR003:
    """Test R003: Sold Not in Ordered"""
    
    def test_sold_not_in_ordered(self):
        """Test detecting sold items not in ordered"""
        rule = R003_SoldNotInOrdered()
        
        reconciled_df = pd.DataFrame({
            "medicine_key": ["KEY1", "KEY2"],
            "ordered_total": [100, 0],
            "sold_total": [80, 50],
        })
        
        issues = rule.check({"reconciled": reconciled_df})
        assert len(issues) == 1
        assert issues[0]["rule_id"] == "R003"


class TestR004:
    """Test R004: Negative or Zero Quantity"""
    
    def test_negative_quantity(self):
        """Test detecting negative quantities"""
        rule = R004_NegativeOrZeroQuantity()
        
        df = pd.DataFrame({
            "ordered_qty": [100, 0, -10],
            "medicine_key": ["KEY1", "KEY2", "KEY3"],
        })
        
        issues = rule.check({"ordered": df})
        assert len(issues) >= 2  # Zero and negative


class TestR005:
    """Test R005: Over-Sold"""
    
    def test_oversold(self):
        """Test detecting over-sold"""
        rule = R005_OverSold()
        
        reconciled_df = pd.DataFrame({
            "medicine_key": ["KEY1", "KEY2"],
            "ordered_total": [100, 200],
            "sold_total": [80, 250],
            "shortage_qty": [0, 50],
        })
        
        issues = rule.check({"reconciled": reconciled_df})
        assert len(issues) == 1
        assert issues[0]["rule_id"] == "R005"


class TestR006:
    """Test R006: Suspicious Days Supply"""
    
    def test_suspicious_days_supply(self):
        """Test detecting suspicious days supply"""
        rule = R006_SuspiciousDaysSupply()
        
        df = pd.DataFrame({
            "days_supply": [30, 0, 200],
            "medicine_key": ["KEY1", "KEY2", "KEY3"],
        })
        
        issues = rule.check({"sold": df})
        assert len(issues) == 2  # 0 and 200 are outside 1-120


class TestR007:
    """Test R007: Missing Critical Fields"""
    
    def test_missing_fields(self):
        """Test detecting missing critical fields"""
        rule = R007_MissingCriticalFields()
        
        df = pd.DataFrame({
            "drug_name": ["Drug1", None, "Drug3"],
            "ndc": ["123", None, None],
            "ordered_qty": [100, 0, 50],
            "medicine_key": ["KEY1", "KEY2", "KEY3"],
        })
        
        issues = rule.check({"ordered": df})
        assert len(issues) >= 1  # At least KEY2 should be flagged

