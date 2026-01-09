"""Ingestion module for reading CSV and XLSX files"""

from src.ingestion.loaders import load_file, load_csv, load_xlsx, get_file_info
from src.ingestion.mapper import (
    normalize_column_name,
    guess_canonical_field,
    create_mapping_from_columns,
    apply_mapping,
    validate_mapping,
    CANONICAL_FIELDS,
    REQUIRED_FIELDS_ORDERED,
    REQUIRED_FIELDS_SOLD,
)
from src.ingestion.validator import validate_dataframe, get_summary_stats
from src.ingestion.config_loader import load_mapping_config, save_mapping_config
from src.ingestion.processor import process_file, validate_inputs

__all__ = [
    "load_file",
    "load_csv",
    "load_xlsx",
    "get_file_info",
    "normalize_column_name",
    "guess_canonical_field",
    "create_mapping_from_columns",
    "apply_mapping",
    "validate_mapping",
    "CANONICAL_FIELDS",
    "REQUIRED_FIELDS_ORDERED",
    "REQUIRED_FIELDS_SOLD",
    "validate_dataframe",
    "get_summary_stats",
    "load_mapping_config",
    "save_mapping_config",
    "process_file",
    "validate_inputs",
]
