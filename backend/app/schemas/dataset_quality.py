import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ColumnProfile(BaseModel):
    column_name: str
    display_label: str
    inferred_type: str
    non_null_count: int
    null_count: int
    missing_percentage: float
    unique_count: int
    duplicate_count: int
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    mean: Optional[float] = None
    median: Optional[float] = None
    top_values: List[Dict[str, Any]] = Field(default_factory=list)
    string_length_stats: Optional[Dict[str, Any]] = None
    valid_format_percentage: float = 100.0
    sample_values: List[Any] = Field(default_factory=list)


class QualityDimensionDetail(BaseModel):
    score: float
    affected_count: int
    rule: str
    explanation: str
    suggestions: List[str] = Field(default_factory=list)


class QualityReportData(BaseModel):
    overall_score: float
    dimension_scores: Dict[str, float]
    dimensions: Dict[str, QualityDimensionDetail]
    scoring_method_version: str = "v1.0"


class DatasetOverviewProfile(BaseModel):
    total_records: int
    total_columns: int
    total_sources: int
    valid_records: int
    records_with_warnings: int
    invalid_records: int
    duplicate_records: int
    unique_records: int
    created_at: str
    updated_at: str


class DatasetProfileResponse(BaseModel):
    dataset_id: uuid.UUID
    dataset_name: str
    overview: DatasetOverviewProfile
    columns: List[ColumnProfile]
    quality: QualityReportData
    profiled_at: str

    model_config = ConfigDict(from_attributes=True)


class QualityReportResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    quality_score: float
    dimension_scores: Dict[str, float]
    report_data: Dict[str, Any]
    scoring_method_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
