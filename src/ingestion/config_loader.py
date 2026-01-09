"""Load column mapping configuration from YAML/JSON files"""

import json
import yaml
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def load_mapping_config(config_path: str) -> Dict[str, Dict[str, str]]:
    """
    Load column mapping configuration from YAML or JSON file.
    
    Expected format:
    {
        "ordered": {
            "original_column_name": "canonical_field_name",
            ...
        },
        "sold": {
            "original_column_name": "canonical_field_name",
            ...
        }
    }
    
    Or simpler format (applies to both):
    {
        "original_column_name": "canonical_field_name",
        ...
    }
    
    Args:
        config_path: Path to YAML or JSON config file
        
    Returns:
        Dictionary with "ordered" and "sold" mappings
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    suffix = path.suffix.lower()
    
    try:
        if suffix in ['.yaml', '.yml']:
            with open(path, 'r') as f:
                config = yaml.safe_load(f)
        elif suffix == '.json':
            with open(path, 'r') as f:
                config = json.load(f)
        else:
            raise ValueError(f"Unsupported config format: {suffix}. Use .yaml or .json")
        
        # Normalize config structure
        if "ordered" in config or "sold" in config:
            # Already in correct format
            result = {
                "ordered": config.get("ordered", {}),
                "sold": config.get("sold", {}),
            }
        else:
            # Single mapping applies to both
            result = {
                "ordered": config,
                "sold": config,
            }
        
        logger.info(f"Loaded mapping config from {config_path}")
        return result
        
    except Exception as e:
        raise ValueError(f"Failed to load config {config_path}: {e}") from e


def save_mapping_config(config: Dict[str, Dict[str, str]], config_path: str, format: str = "yaml"):
    """
    Save column mapping configuration to file.
    
    Args:
        config: Dictionary with "ordered" and "sold" mappings
        config_path: Path to save config file
        format: "yaml" or "json"
    """
    path = Path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if format.lower() == "yaml":
            with open(path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        elif format.lower() == "json":
            with open(path, 'w') as f:
                json.dump(config, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Saved mapping config to {config_path}")
        
    except Exception as e:
        raise ValueError(f"Failed to save config {config_path}: {e}") from e

