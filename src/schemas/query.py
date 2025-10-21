from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class QueryBase(BaseModel):
    natural_language_query: str = Field(..., min_length=1, max_length=1000)
    dataset_id: str


class QueryCreate(QueryBase):
    pass


class QueryUpdate(BaseModel):
    user_feedback: Optional[str] = Field(None, pattern="^(thumbs_up|thumbs_down|none)$")


class QueryResult(BaseModel):
    result_data: Optional[list[dict[str, Any]]] = None
    result_summary: Optional[str] = None
    row_count: Optional[int] = None
    execution_time: Optional[float] = None


class Query(QueryBase):
    id: str
    user_id: str
    generated_sql: Optional[str] = None
    query_type: Optional[str] = None
    result_data: Optional[list[dict[str, Any]]] = None
    result_summary: Optional[str] = None
    execution_time: Optional[float] = None
    row_count: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    user_feedback: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class QueryListResponse(BaseModel):
    queries: list[Query]
    total: int
    page: int
    page_size: int
