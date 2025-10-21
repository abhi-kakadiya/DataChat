import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DatasetBase(BaseModel):
    """Base dataset schema."""
    
    name: str = Field(..., description="Dataset name")
    description: Optional[str] = Field(None, description="Dataset description")


class DatasetCreate(DatasetBase):
    """Dataset creation schema."""
    pass


class DatasetUpdate(BaseModel):
    """Dataset update schema."""
    
    name: Optional[str] = Field(None, description="Dataset name")
    description: Optional[str] = Field(None, description="Dataset description")


class DatasetInDBBase(DatasetBase):
    """Base dataset in database schema."""
    
    id: uuid.UUID = Field(..., description="Dataset ID")
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="File path in storage")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="File content type")
    row_count: Optional[int] = Field(None, description="Number of rows")
    column_count: Optional[int] = Field(None, description="Number of columns")
    column_info: Optional[Dict[str, Any]] = Field(None, description="Column information")
    status: str = Field(..., description="Processing status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(description="Last update timestamp")
    owner_id: str = Field(..., description="Owner user ID")
    
    class Config:
        from_attributes = True


class DatasetInDB(DatasetInDBBase):
    """Dataset in database schema."""
    pass


class Dataset(DatasetInDBBase):
    """Dataset response schema."""
    pass


class DatasetPreview(BaseModel):
    """Dataset preview schema."""
    
    id: uuid.UUID = Field(..., description="Dataset ID")
    name: str = Field(..., description="Dataset name")
    row_count: Optional[int] = Field(None, description="Number of rows")
    column_count: Optional[int] = Field(None, description="Number of columns")
    column_info: Optional[Dict[str, Any]] = Field(None, description="Column information")
    status: str = Field(..., description="Processing status")
    preview_data: Optional[List[Dict[str, Any]]] = Field(None, description="Preview data (first 10 rows)")

