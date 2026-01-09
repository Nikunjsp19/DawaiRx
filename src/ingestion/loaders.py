"""File loaders for CSV and XLSX files"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


def load_csv(file_path: str, **kwargs) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame.
    
    Args:
        file_path: Path to CSV file
        **kwargs: Additional arguments passed to pd.read_csv
        
    Returns:
        DataFrame with loaded data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file cannot be parsed
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    try:
        df = pd.read_csv(file_path, **kwargs)
        logger.info(f"Loaded CSV: {file_path} ({len(df)} rows, {len(df.columns)} columns)")
        return df
    except Exception as e:
        raise ValueError(f"Failed to load CSV {file_path}: {e}") from e


def load_xlsx(file_path: str, sheet_name: Optional[str] = None, **kwargs) -> pd.DataFrame:
    """
    Load an XLSX file into a pandas DataFrame.
    
    Args:
        file_path: Path to XLSX file
        sheet_name: Name or index of sheet to load (default: first sheet)
        **kwargs: Additional arguments passed to pd.read_excel
        
    Returns:
        DataFrame with loaded data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file cannot be parsed
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"XLSX file not found: {file_path}")
    
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', **kwargs)
        logger.info(f"Loaded XLSX: {file_path} ({len(df)} rows, {len(df.columns)} columns)")
        return df
    except Exception as e:
        raise ValueError(f"Failed to load XLSX {file_path}: {e}") from e


def load_file(file_path: str, **kwargs) -> pd.DataFrame:
    """
    Automatically detect file type and load CSV or XLSX.
    
    Args:
        file_path: Path to file
        **kwargs: Additional arguments passed to loader
        
    Returns:
        DataFrame with loaded data
    """
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    if suffix == '.csv':
        return load_csv(file_path, **kwargs)
    elif suffix in ['.xlsx', '.xls']:
        return load_xlsx(file_path, **kwargs)
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Supported: .csv, .xlsx, .xls")


def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    Get metadata about a file without loading full contents.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with file metadata
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    suffix = path.suffix.lower()
    
    info = {
        "path": str(path.absolute()),
        "size_bytes": path.stat().st_size,
        "extension": suffix,
        "exists": True,
    }
    
    # Try to get column names without loading full file
    try:
        if suffix == '.csv':
            # Read just first row for column names
            df_sample = pd.read_csv(file_path, nrows=0)
            info["columns"] = list(df_sample.columns)
            info["column_count"] = len(df_sample.columns)
        elif suffix in ['.xlsx', '.xls']:
            df_sample = pd.read_excel(file_path, nrows=0, engine='openpyxl')
            info["columns"] = list(df_sample.columns)
            info["column_count"] = len(df_sample.columns)
    except Exception as e:
        logger.warning(f"Could not read column info from {file_path}: {e}")
        info["columns"] = []
        info["column_count"] = 0
    
    return info

