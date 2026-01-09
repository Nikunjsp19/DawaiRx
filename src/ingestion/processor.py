"""Main processor for ingestion pipeline"""

from typing import Dict, Any, Optional
import pandas as pd
from pathlib import Path
import logging

from src.ingestion.loaders import load_file, get_file_info
from src.ingestion.mapper import (
    create_mapping_from_columns,
    apply_mapping,
    validate_mapping,
    normalize_column_name,
    REQUIRED_FIELDS_ORDERED,
    REQUIRED_FIELDS_SOLD,
)
from src.ingestion.validator import validate_dataframe, get_summary_stats
from src.ingestion.config_loader import load_mapping_config

logger = logging.getLogger(__name__)


def process_file(
    file_path: str,
    report_type: str,
    mapping_config: Optional[Dict[str, str]] = None,
    auto_map: bool = True
) -> Dict[str, Any]:
    """
    Process a file: load, map columns, validate.
    
    Args:
        file_path: Path to input file
        report_type: "ordered" or "sold"
        mapping_config: Optional explicit column mapping
        auto_map: If True, auto-guess mappings for unmapped columns
        
    Returns:
        Dictionary with processed DataFrame and metadata
    """
    if report_type not in ["ordered", "sold"]:
        raise ValueError(f"report_type must be 'ordered' or 'sold', got '{report_type}'")
    
    # Get file info
    file_info = get_file_info(file_path)
    
    # Load file
    df = load_file(file_path)
    
    # Determine mapping
    if mapping_config:
        mapping = mapping_config.copy()
    else:
        mapping = {}
    
    # Auto-map if enabled and mapping is incomplete
    if auto_map:
        auto_mapping = create_mapping_from_columns(df.columns.tolist(), report_type)
        # Merge: explicit mapping takes precedence
        for col, canonical in auto_mapping.items():
            if col not in mapping:
                mapping[col] = canonical
    
    # Apply mapping
    rename_map = apply_mapping(df.columns.tolist(), mapping)
    if rename_map:
        df = df.rename(columns=rename_map)
    
    # Determine required fields
    required_fields = REQUIRED_FIELDS_ORDERED if report_type == "ordered" else REQUIRED_FIELDS_SOLD
    
    # Validate mapping - check if required fields are present in mapped columns
    # The mapping dict has original -> canonical, but validate_mapping expects
    # canonical -> original. We need to check what canonical fields we have.
    mapped_canonical_fields = set(rename_map.values()) if rename_map else set()
    
    # Also check the original mapping for any fields that weren't renamed
    for orig_col, canonical in mapping.items():
        if orig_col in df.columns:
            mapped_canonical_fields.add(canonical)
    
    # Simple validation: check if required fields are in mapped canonical fields
    missing_fields = required_fields - mapped_canonical_fields
    mapping_valid = len(missing_fields) == 0
    
    # Validate data
    validation_results = validate_dataframe(df, required_fields, report_type)
    
    # Get summary stats
    stats = get_summary_stats(df)
    
    return {
        "file_path": file_path,
        "file_info": file_info,
        "dataframe": df,
        "mapping": mapping,
        "mapping_valid": mapping_valid,
        "missing_fields": missing_fields,
        "validation": validation_results,
        "stats": stats,
        "report_type": report_type,
    }


def validate_inputs(
    ordered_file: str,
    sold_file: str,
    mapping_config_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate both input files and their mappings.
    
    Args:
        ordered_file: Path to ordered report file
        sold_file: Path to sold report file
        mapping_config_path: Optional path to mapping config file
        
    Returns:
        Dictionary with validation results for both files
    """
    # Load mapping config if provided
    ordered_mapping = None
    sold_mapping = None
    
    if mapping_config_path:
        config = load_mapping_config(mapping_config_path)
        ordered_mapping = config.get("ordered")
        sold_mapping = config.get("sold")
    
    # Process both files
    ordered_result = process_file(ordered_file, "ordered", ordered_mapping)
    sold_result = process_file(sold_file, "sold", sold_mapping)
    
    # Overall validation
    overall_valid = (
        ordered_result["mapping_valid"] and
        ordered_result["validation"]["valid"] and
        sold_result["mapping_valid"] and
        sold_result["validation"]["valid"]
    )
    
    return {
        "valid": overall_valid,
        "ordered": ordered_result,
        "sold": sold_result,
    }

