"""Tests for ingestion module"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os

from src.ingestion.loaders import load_csv, load_xlsx, load_file, get_file_info
from src.ingestion.mapper import (
    normalize_column_name,
    guess_canonical_field,
    create_mapping_from_columns,
    apply_mapping,
    validate_mapping,
    REQUIRED_FIELDS_ORDERED,
)
from src.ingestion.validator import validate_dataframe, get_summary_stats
from src.ingestion.config_loader import load_mapping_config, save_mapping_config
from src.ingestion.processor import process_file, validate_inputs


class TestLoaders:
    """Test file loading functions"""
    
    def test_load_csv(self, tmp_path):
        """Test CSV loading"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("col1,col2\nval1,val2\nval3,val4")
        
        df = load_csv(str(csv_file))
        assert len(df) == 2
        assert list(df.columns) == ["col1", "col2"]
    
    def test_load_csv_nonexistent(self):
        """Test loading nonexistent CSV"""
        with pytest.raises(FileNotFoundError):
            load_csv("nonexistent.csv")
    
    def test_load_file_auto_detect_csv(self, tmp_path):
        """Test auto-detection of CSV files"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("col1,col2\nval1,val2")
        
        df = load_file(str(csv_file))
        assert len(df) == 1
    
    def test_load_file_unsupported(self):
        """Test unsupported file type"""
        with pytest.raises(ValueError, match="Unsupported file type"):
            load_file("test.txt")
    
    def test_get_file_info(self, tmp_path):
        """Test file info extraction"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("col1,col2\nval1,val2")
        
        info = get_file_info(str(csv_file))
        assert info["extension"] == ".csv"
        assert "col1" in info["columns"]
        assert info["column_count"] == 2


class TestMapper:
    """Test column mapping functions"""
    
    def test_normalize_column_name(self):
        """Test column name normalization"""
        assert normalize_column_name("Drug Name") == "drug_name"
        assert normalize_column_name("NDC Code") == "ndc_code"
        assert normalize_column_name("  Quantity  ") == "quantity"
        assert normalize_column_name("RX#") == "rx"
    
    def test_guess_canonical_field(self):
        """Test canonical field guessing"""
        assert guess_canonical_field("drug_name") == "drug_name"
        assert guess_canonical_field("Drug Name") == "drug_name"
        assert guess_canonical_field("ndc") == "ndc"
        assert guess_canonical_field("NDC Code") == "ndc"
        assert guess_canonical_field("quantity") == "quantity"
        assert guess_canonical_field("qty") == "quantity"
        assert guess_canonical_field("unknown_field") is None
    
    def test_create_mapping_from_columns(self):
        """Test automatic mapping creation"""
        columns = ["Drug Name", "NDC", "Quantity", "Unknown"]
        mapping = create_mapping_from_columns(columns, "ordered")
        
        assert "Drug Name" in mapping
        assert mapping["Drug Name"] == "drug_name"
        assert mapping["NDC"] == "ndc"
        assert mapping["Quantity"] == "ordered_qty"
    
    def test_apply_mapping(self):
        """Test applying mapping to DataFrame columns"""
        df_columns = ["Drug Name", "NDC", "Quantity"]
        mapping = {
            "Drug Name": "drug_name",
            "NDC": "ndc",
            "Quantity": "ordered_qty",
        }
        
        rename_map = apply_mapping(df_columns, mapping)
        assert rename_map == {
            "Drug Name": "drug_name",
            "NDC": "ndc",
            "Quantity": "ordered_qty",
        }
    
    def test_validate_mapping_valid(self):
        """Test mapping validation - valid case"""
        mapping = {
            "Drug Name": "drug_name",
            "NDC": "ndc",
            "Quantity": "ordered_qty",
        }
        df_columns = ["Drug Name", "NDC", "Quantity"]
        
        is_valid, missing = validate_mapping(
            mapping, df_columns, REQUIRED_FIELDS_ORDERED, "ordered"
        )
        assert is_valid
        assert len(missing) == 0
    
    def test_validate_mapping_missing(self):
        """Test mapping validation - missing required field"""
        mapping = {
            "Drug Name": "drug_name",
            "NDC": "ndc",
            # Missing quantity
        }
        df_columns = ["Drug Name", "NDC"]
        
        is_valid, missing = validate_mapping(
            mapping, df_columns, REQUIRED_FIELDS_ORDERED, "ordered"
        )
        assert not is_valid
        assert "quantity" in missing or "ordered_qty" in missing


class TestValidator:
    """Test validation functions"""
    
    def test_validate_dataframe_valid(self):
        """Test DataFrame validation - valid case"""
        df = pd.DataFrame({
            "drug_name": ["Drug1", "Drug2"],
            "ndc": ["123", "456"],
            "quantity": [10, 20],
        })
        
        results = validate_dataframe(df, {"drug_name", "ndc", "quantity"}, "ordered")
        assert results["valid"]
        assert results["row_count"] == 2
    
    def test_validate_dataframe_missing_field(self):
        """Test DataFrame validation - missing required field"""
        df = pd.DataFrame({
            "drug_name": ["Drug1"],
            # Missing ndc and quantity
        })
        
        results = validate_dataframe(df, {"drug_name", "ndc", "quantity"}, "ordered")
        assert not results["valid"]
        assert len(results["missing_fields"]) > 0
    
    def test_validate_dataframe_empty(self):
        """Test DataFrame validation - empty DataFrame"""
        df = pd.DataFrame()
        
        results = validate_dataframe(df, {"drug_name", "ndc", "quantity"}, "ordered")
        assert not results["valid"]
        assert "empty" in results["errors"][0].lower()
    
    def test_get_summary_stats(self):
        """Test summary statistics"""
        df = pd.DataFrame({
            "drug_name": ["Drug1", "Drug2"],
            "quantity": [10, 20],
        })
        
        stats = get_summary_stats(df)
        assert stats["row_count"] == 2
        assert stats["column_count"] == 2
        assert "drug_name" in stats["columns"]


class TestConfigLoader:
    """Test configuration loading"""
    
    def test_load_mapping_config_yaml(self, tmp_path):
        """Test loading YAML mapping config"""
        config_file = tmp_path / "mapping.yaml"
        config_file.write_text("""
ordered:
  col1: drug_name
sold:
  col1: drug_name
        """)
        
        config = load_mapping_config(str(config_file))
        assert "ordered" in config
        assert "sold" in config
    
    def test_load_mapping_config_json(self, tmp_path):
        """Test loading JSON mapping config"""
        config_file = tmp_path / "mapping.json"
        config_file.write_text('{"ordered": {"col1": "drug_name"}}')
        
        config = load_mapping_config(str(config_file))
        assert "ordered" in config
    
    def test_save_mapping_config(self, tmp_path):
        """Test saving mapping config"""
        config = {
            "ordered": {"col1": "drug_name"},
            "sold": {"col1": "drug_name"},
        }
        config_file = tmp_path / "mapping.yaml"
        
        save_mapping_config(config, str(config_file))
        assert config_file.exists()
        
        # Verify it can be loaded back
        loaded = load_mapping_config(str(config_file))
        assert loaded == config


class TestProcessor:
    """Test main processor functions"""
    
    def test_process_file(self, tmp_path):
        """Test file processing"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("drug_name,ndc,quantity\nDrug1,123,10\nDrug2,456,20")
        
        result = process_file(str(csv_file), "ordered")
        
        assert result["report_type"] == "ordered"
        assert len(result["dataframe"]) == 2
        assert "drug_name" in result["dataframe"].columns
        assert "ndc" in result["dataframe"].columns
    
    def test_validate_inputs(self, tmp_path):
        """Test input validation"""
        ordered_file = tmp_path / "ordered.csv"
        ordered_file.write_text("drug_name,ndc,quantity\nDrug1,123,10")
        
        sold_file = tmp_path / "sold.csv"
        sold_file.write_text("drug_name,ndc,quantity\nDrug1,123,5")
        
        results = validate_inputs(str(ordered_file), str(sold_file))
        
        assert "ordered" in results
        assert "sold" in results
        assert "valid" in results

