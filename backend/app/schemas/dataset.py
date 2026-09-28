from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class DatasetStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DatasetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[DatasetStatus] = DatasetStatus.PENDING
    row_count: Optional[int] = Field(0, ge=0)


class DatasetCreate(BaseModel):
    project_id: str
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[DatasetStatus] = DatasetStatus.PENDING
    row_count: Optional[int] = Field(0, ge=0)


class DatasetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[DatasetStatus] = None
    row_count: Optional[int] = Field(None, ge=0)


class DatasetResponse(DatasetBase):
    id: str
    project_id: str
    user_id: str
    status: DatasetStatus
    row_count: int
    created_at: datetime
    updated_at: datetime
    project_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
