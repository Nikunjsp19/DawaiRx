"""Pydantic models for MongoDB documents"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional, List
from datetime import datetime
from bson import ObjectId


class RunDocument(BaseModel):
    """Model for runs collection"""
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()}
    )
    
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    run_id: str = Field(..., description="Unique run identifier")
    user_id: str = Field(..., description="User ID who owns this run")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    input_metadata: Dict[str, Any] = Field(default_factory=dict)
    stats: Dict[str, Any] = Field(default_factory=dict)
    config_summary: Dict[str, Any] = Field(default_factory=dict)


class RunItemDocument(BaseModel):
    """Model for run_items collection"""
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    run_id: str = Field(..., description="Run identifier")
    user_id: str = Field(..., description="User ID who owns this run")
    medicine_key: str = Field(..., description="Medicine key")
    drug_name: Optional[str] = None
    strength: Optional[str] = None
    manufacturer: Optional[str] = None
    ordered_qty: float = 0.0
    sold_qty: float = 0.0
    remaining_qty: float = 0.0
    shortage_qty: float = 0.0
    leftover_qty: float = 0.0


class RunIssueDocument(BaseModel):
    """Model for run_issues collection"""
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    run_id: str = Field(..., description="Run identifier")
    user_id: str = Field(..., description="User ID who owns this run")
    rule_id: str = Field(..., description="Rule identifier")
    severity: str = Field(..., description="Issue severity")
    medicine_key: Optional[str] = None
    details: str = Field(..., description="Issue description")
    row_ref: Dict[str, Any] = Field(default_factory=dict)
    raw_snippet: Dict[str, Any] = Field(default_factory=dict)

