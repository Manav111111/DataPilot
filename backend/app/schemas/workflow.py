from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowRunBase(BaseModel):
    project_id: str
    status: Optional[WorkflowStatus] = WorkflowStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class WorkflowRunCreate(BaseModel):
    project_id: str


class WorkflowRunResponse(WorkflowRunBase):
    id: str
    user_id: str
    status: WorkflowStatus
    created_at: datetime
    project_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
