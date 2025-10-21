from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class InsightBase(BaseModel):
    insight_type: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class InsightCreate(InsightBase):
    dataset_id: str
    query_id: Optional[str] = None
    supporting_data: Optional[dict[str, Any]] = None
    visualization_config: Optional[dict[str, Any]] = None


class InsightUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)


class Insight(InsightBase):
    id: str
    dataset_id: str
    query_id: Optional[str] = None
    supporting_data: Optional[dict[str, Any]] = None
    visualization_config: Optional[dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InsightListResponse(BaseModel):
    insights: list[Insight]
    total: int
    page: int
    page_size: int
