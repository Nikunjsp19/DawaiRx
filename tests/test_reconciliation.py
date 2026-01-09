"""Tests for reconciliation module"""

import pytest
import pandas as pd

from src.reconciliation.engine import (
    aggregate_by_medicine,
    reconcile_inventory,
    generate_summary,
)


class TestAggregation:
    """Test aggregation functions"""
    
    def test_aggregate_by_medicine(self):
        """Test aggregating quantities by medicine_key"""
        df = pd.DataFrame({
            "medicine_key": ["KEY1", "KEY1", "KEY2"],
            "quantity": [10, 20, 30],
            "drug_name": ["Drug1", "Drug1", "Drug2"],
        })
        
        result = aggregate_by_medicine(df, "quantity")
        
        assert len(result) == 2
        assert result[result["medicine_key"] == "KEY1"]["quantity"].iloc[0] == 30
        assert result[result["medicine_key"] == "KEY2"]["quantity"].iloc[0] == 30
    
    def test_aggregate_empty_dataframe(self):
        """Test aggregation with empty DataFrame"""
        df = pd.DataFrame(columns=["medicine_key", "quantity"])
        result = aggregate_by_medicine(df, "quantity")
        assert len(result) == 0


class TestReconciliation:
    """Test reconciliation functions"""
    
    def test_reconcile_inventory_basic(self):
        """Test basic reconciliation"""
        ordered = pd.DataFrame({
            "medicine_key": ["KEY1", "KEY2"],
            "ordered_qty": [100, 200],
            "drug_name": ["Drug1", "Drug2"],
        })
        
        sold = pd.DataFrame({
            "medicine_key": ["KEY1", "KEY2"],
            "sold_qty": [80, 250],
            "drug_name": ["Drug1", "Drug2"],
        })
        
        result = reconcile_inventory(ordered, sold)
        
        assert len(result) == 2
        assert "ordered_total" in result.columns
        assert "sold_total" in result.columns
        assert "remaining_qty" in result.columns
        assert "shortage_qty" in result.columns
        assert "leftover_qty" in result.columns
        
        # Check KEY1: 100 ordered, 80 sold = 20 remaining
        key1 = result[result["medicine_key"] == "KEY1"].iloc[0]
        assert key1["ordered_total"] == 100
        assert key1["sold_total"] == 80
        assert key1["remaining_qty"] == 20
        assert key1["leftover_qty"] == 20
        assert key1["shortage_qty"] == 0
        
        # Check KEY2: 200 ordered, 250 sold = -50 (shortage)
        key2 = result[result["medicine_key"] == "KEY2"].iloc[0]
        assert key2["ordered_total"] == 200
        assert key2["sold_total"] == 250
        assert key2["remaining_qty"] == -50
        assert key2["leftover_qty"] == 0
        assert key2["shortage_qty"] == 50
    
    def test_reconcile_with_missing_medicine(self):
        """Test reconciliation when medicine appears in only one dataset"""
        ordered = pd.DataFrame({
            "medicine_key": ["KEY1"],
            "ordered_qty": [100],
        })
        
        sold = pd.DataFrame({
            "medicine_key": ["KEY2"],
            "sold_qty": [50],
        })
        
        result = reconcile_inventory(ordered, sold)
        
        # Should have both medicines
        assert len(result) == 2
        assert set(result["medicine_key"]) == {"KEY1", "KEY2"}
        
        # KEY1: only in ordered
        key1 = result[result["medicine_key"] == "KEY1"].iloc[0]
        assert key1["ordered_total"] == 100
        assert key1["sold_total"] == 0
        
        # KEY2: only in sold
        key2 = result[result["medicine_key"] == "KEY2"].iloc[0]
        assert key2["ordered_total"] == 0
        assert key2["sold_total"] == 50
    
    def test_reconcile_empty_ordered(self):
        """Test reconciliation with empty ordered data"""
        ordered = pd.DataFrame(columns=["medicine_key", "ordered_qty"])
        sold = pd.DataFrame({
            "medicine_key": ["KEY1"],
            "sold_qty": [50],
        })
        
        result = reconcile_inventory(ordered, sold)
        assert len(result) == 1
        assert result.iloc[0]["ordered_total"] == 0
        assert result.iloc[0]["sold_total"] == 50


class TestSummary:
    """Test summary generation"""
    
    def test_generate_summary(self):
        """Test summary generation"""
        reconciled = pd.DataFrame({
            "medicine_key": ["KEY1", "KEY2", "KEY3"],
            "ordered_total": [100, 200, 150],
            "sold_total": [80, 250, 150],
            "remaining_qty": [20, -50, 0],
            "shortage_qty": [0, 50, 0],
            "leftover_qty": [20, 0, 0],
        })
        
        summary = generate_summary(reconciled)
        
        assert summary["total_medicines"] == 3
        assert summary["total_ordered"] == 450
        assert summary["total_sold"] == 480
        assert summary["total_remaining"] == -30
        assert summary["total_shortage"] == 50
        assert summary["total_leftover"] == 20
        assert summary["medicines_with_shortage"] == 1
        assert summary["medicines_with_leftover"] == 1
    
    def test_generate_summary_empty(self):
        """Test summary with empty DataFrame"""
        reconciled = pd.DataFrame()
        summary = generate_summary(reconciled)
        
        assert summary["total_medicines"] == 0
        assert summary["total_ordered"] == 0

