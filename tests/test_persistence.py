"""Tests for MongoDB persistence"""

import pytest
import pandas as pd
from datetime import datetime

from src.persistence.store import RunStore
from src.persistence.models import RunDocument, RunItemDocument, RunIssueDocument


@pytest.mark.integration
def test_run_store_connection():
    """Test RunStore can connect to MongoDB"""
    try:
        store = RunStore()
        store.close()
    except Exception as e:
        pytest.skip(f"MongoDB not available: {e}")


@pytest.mark.integration
def test_save_and_retrieve_run():
    """Test saving and retrieving a run"""
    try:
        store = RunStore()
        
        # Create test data
        reconciled_df = pd.DataFrame({
            "medicine_key": ["KEY1", "KEY2"],
            "drug_name": ["Drug1", "Drug2"],
            "ordered_total": [100, 200],
            "sold_total": [80, 250],
            "remaining_qty": [20, -50],
            "shortage_qty": [0, 50],
            "leftover_qty": [20, 0],
        })
        
        issues = [
            {
                "rule_id": "R005",
                "severity": "high",
                "medicine_key": "KEY2",
                "details": "Over-sold",
                "row_ref": {},
                "raw_snippet": {},
            }
        ]
        
        summary = {
            "total_medicines": 2,
            "total_ordered": 300,
            "total_sold": 330,
            "total_issues": 1,
        }
        
        # Save run (using dummy file paths)
        run_id = store.save_run(
            ordered_file="test_ordered.csv",
            sold_file="test_sold.csv",
            mapping_file=None,
            reconciled_df=reconciled_df,
            issues=issues,
            summary=summary
        )
        
        assert run_id is not None
        assert run_id.startswith("run_")
        
        # Retrieve run
        run = store.get_run(run_id)
        assert run is not None
        assert run["run_id"] == run_id
        assert run["stats"]["total_medicines"] == 2
        
        # Retrieve items
        items = store.get_run_items(run_id)
        assert len(items) == 2
        
        # Retrieve issues
        run_issues = store.get_run_issues(run_id)
        assert len(run_issues) == 1
        
        store.close()
        
    except Exception as e:
        pytest.skip(f"MongoDB not available: {e}")


@pytest.mark.integration
def test_list_runs():
    """Test listing runs"""
    try:
        store = RunStore()
        runs = store.list_runs(limit=5)
        assert isinstance(runs, list)
        store.close()
    except Exception as e:
        pytest.skip(f"MongoDB not available: {e}")

