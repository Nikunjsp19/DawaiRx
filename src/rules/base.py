"""Base rule interface and registry"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class Rule(ABC):
    """Base class for audit rules"""
    
    def __init__(self, rule_id: str, name: str, severity: str = "medium"):
        """
        Initialize rule.
        
        Args:
            rule_id: Unique rule identifier (e.g., "R001")
            name: Human-readable rule name
            severity: "high", "medium", or "low"
        """
        self.rule_id = rule_id
        self.name = name
        self.severity = severity
    
    @abstractmethod
    def check(self, data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        """
        Check rule and return list of issues.
        
        Args:
            data: Dictionary with dataframes (e.g., {"ordered": df, "sold": df, "reconciled": df})
        
        Returns:
            List of issue dictionaries, each with:
            - rule_id: Rule identifier
            - severity: Issue severity
            - medicine_key: Medicine key (if applicable)
            - details: Human-readable description
            - row_ref: Dictionary with source and row_number (if applicable)
            - raw_snippet: Optional raw data snippet
        """
        pass
    
    def create_issue(
        self,
        details: str,
        medicine_key: Optional[str] = None,
        row_ref: Optional[Dict[str, Any]] = None,
        raw_snippet: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized issue dictionary.
        
        Args:
            details: Issue description
            medicine_key: Medicine key if applicable
            row_ref: Row reference dictionary
            raw_snippet: Raw data snippet
            
        Returns:
            Issue dictionary
        """
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "medicine_key": medicine_key,
            "details": details,
            "row_ref": row_ref or {},
            "raw_snippet": raw_snippet or {},
        }


class RuleRegistry:
    """Registry for managing audit rules"""
    
    def __init__(self):
        self.rules: Dict[str, Rule] = {}
    
    def register(self, rule: Rule):
        """Register a rule."""
        self.rules[rule.rule_id] = rule
        logger.info(f"Registered rule: {rule.rule_id} - {rule.name}")
    
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get a rule by ID."""
        return self.rules.get(rule_id)
    
    def get_all_rules(self) -> List[Rule]:
        """Get all registered rules."""
        return list(self.rules.values())
    
    def run_all(self, data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        """
        Run all registered rules and collect issues.
        
        Args:
            data: Dictionary with dataframes
            
        Returns:
            List of all issues found
        """
        all_issues = []
        
        for rule in self.rules.values():
            try:
                issues = rule.check(data)
                all_issues.extend(issues)
                logger.debug(f"Rule {rule.rule_id} found {len(issues)} issues")
            except Exception as e:
                logger.error(f"Error running rule {rule.rule_id}: {e}", exc_info=True)
        
        return all_issues

