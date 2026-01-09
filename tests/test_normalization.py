"""Tests for normalization module"""

import pytest
import pandas as pd
from datetime import datetime

from src.normalization.ndc import normalize_ndc, format_ndc_display, is_valid_ndc
from src.normalization.text import normalize_text, normalize_drug_name, normalize_strength
from src.normalization.dates import parse_date, format_date
from src.normalization.quantities import parse_quantity, normalize_quantity
from src.normalization.medicine_key import generate_medicine_key, extract_medicine_key_components
from src.normalization.processor import normalize_dataframe


class TestNDC:
    """Test NDC normalization"""
    
    def test_normalize_ndc_11_digit(self):
        """Test 11-digit NDC"""
        assert normalize_ndc("12345-6789-01") == "12345678901"
        assert normalize_ndc("12345678901") == "12345678901"
    
    def test_normalize_ndc_10_digit(self):
        """Test 10-digit NDC (should pad)"""
        assert normalize_ndc("12345-6789-0") == "12345678900"
        assert normalize_ndc("1234567890") == "12345678900"
    
    def test_normalize_ndc_with_spaces(self):
        """Test NDC with spaces"""
        assert normalize_ndc("12345 6789 01") == "12345678901"
    
    def test_normalize_ndc_invalid(self):
        """Test invalid NDC"""
        assert normalize_ndc("123") is None
        assert normalize_ndc("") is None
        assert normalize_ndc(None) is None
        assert normalize_ndc("abc") is None
    
    def test_format_ndc_display(self):
        """Test NDC display formatting"""
        assert format_ndc_display("12345678901") == "12345-6789-01"
        assert format_ndc_display("123") == "123"  # Invalid, return as-is
    
    def test_is_valid_ndc(self):
        """Test NDC validation"""
        assert is_valid_ndc("12345-6789-01") is True
        assert is_valid_ndc("123") is False
        assert is_valid_ndc(None) is False


class TestText:
    """Test text normalization"""
    
    def test_normalize_text_upper(self):
        """Test uppercase normalization"""
        assert normalize_text("  hello  world  ", "upper") == "HELLO WORLD"
        assert normalize_text("test", "upper") == "TEST"
    
    def test_normalize_text_lower(self):
        """Test lowercase normalization"""
        assert normalize_text("  HELLO  WORLD  ", "lower") == "hello world"
    
    def test_normalize_text_collapse_spaces(self):
        """Test space collapsing"""
        assert normalize_text("a   b   c") == "A B C"
    
    def test_normalize_text_none(self):
        """Test None handling"""
        assert normalize_text(None) is None
        assert normalize_text("") is None
        assert normalize_text("nan") is None
    
    def test_normalize_drug_name(self):
        """Test drug name normalization"""
        assert normalize_drug_name("  lisinopril  10mg  ") == "LISINOPRIL 10MG"
    
    def test_normalize_strength(self):
        """Test strength normalization"""
        assert normalize_strength("  10mg  ") == "10MG"


class TestDates:
    """Test date parsing"""
    
    def test_parse_date_string(self):
        """Test parsing date from string"""
        result = parse_date("2024-01-15")
        assert result is not None
        assert isinstance(result, pd.Timestamp)
    
    def test_parse_date_datetime(self):
        """Test parsing date from datetime"""
        dt = datetime(2024, 1, 15)
        result = parse_date(dt)
        assert result is not None
        assert result.year == 2024
    
    def test_parse_date_none(self):
        """Test parsing None"""
        assert parse_date(None) is None
    
    def test_format_date(self):
        """Test date formatting"""
        ts = pd.Timestamp("2024-01-15")
        assert format_date(ts) == "2024-01-15"
        assert format_date(None) is None


class TestQuantities:
    """Test quantity parsing"""
    
    def test_parse_quantity_int(self):
        """Test parsing integer quantity"""
        assert parse_quantity(100) == 100.0
        assert parse_quantity(0) == 0.0
    
    def test_parse_quantity_string(self):
        """Test parsing string quantity"""
        assert parse_quantity("100") == 100.0
        assert parse_quantity("1,000") == 1000.0
    
    def test_parse_quantity_none(self):
        """Test parsing None quantity"""
        assert parse_quantity(None) is None
        assert parse_quantity("") is None
    
    def test_normalize_quantity_defaults_to_zero(self):
        """Test quantity normalization defaults to 0"""
        assert normalize_quantity(None) == 0.0
        assert normalize_quantity("invalid") == 0.0
        assert normalize_quantity(100) == 100.0


class TestMedicineKey:
    """Test medicine key generation"""
    
    def test_generate_key_with_ndc(self):
        """Test key generation with valid NDC"""
        key = generate_medicine_key(ndc="12345-6789-01")
        assert key.startswith("NDC:")
        assert "12345678901" in key
    
    def test_generate_key_composite(self):
        """Test composite key generation"""
        key = generate_medicine_key(
            drug_name="Lisinopril",
            strength="10mg",
            manufacturer="ABC"
        )
        assert key.startswith("COMPOSITE:")
        assert "LISINOPRIL" in key
        assert "10MG" in key
    
    def test_generate_key_prefers_ndc(self):
        """Test that NDC is preferred over composite"""
        key = generate_medicine_key(
            ndc="12345-6789-01",
            drug_name="Lisinopril"
        )
        assert key.startswith("NDC:")
    
    def test_extract_key_components_ndc(self):
        """Test extracting NDC key components"""
        components = extract_medicine_key_components("NDC:12345678901")
        assert components["type"] == "ndc"
        assert components["ndc"] == "12345678901"
    
    def test_extract_key_components_composite(self):
        """Test extracting composite key components"""
        components = extract_medicine_key_components("COMPOSITE:LISINOPRIL|10MG|ABC")
        assert components["type"] == "composite"
        assert components["drug_name"] == "LISINOPRIL"
        assert components["strength"] == "10MG"


class TestProcessor:
    """Test normalization processor"""
    
    def test_normalize_dataframe(self):
        """Test DataFrame normalization"""
        df = pd.DataFrame({
            "drug_name": ["  Lisinopril  ", "Metformin"],
            "ndc": ["12345-6789-01", "98765-4321-10"],
            "quantity": [100, 200],
        })
        
        normalized = normalize_dataframe(df, "ordered")
        
        assert "medicine_key" in normalized.columns
        assert normalized["drug_name"].iloc[0] == "LISINOPRIL"
        assert normalized["ndc"].iloc[0] == "12345678901"
        assert normalized["quantity"].iloc[0] == 100.0

