from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime


class InsightBase(BaseModel):
    """Base schema for Insight."""
    dataset_id: str
    query_id: Optional[str] = None
    insight_type: str
    title: str = Field(..., max_length=200)
    description: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    # Accept both dict and list formats
    supporting_data: Union[Dict[str, Any], List[Dict[str, Any]], List[Any]] = Field(default_factory=dict)
    visualization_config: Dict[str, Any] = Field(default_factory=dict)


class InsightCreate(InsightBase):
    """Schema for creating an insight."""
    pass


class Insight(InsightBase):
    """Schema for Insight response."""
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class InsightListResponse(BaseModel):
    """Schema for paginated insight list response."""
    insights: List[Insight]
    total: int
    page: int
    page_size: int