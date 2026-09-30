from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class FilterCondition(BaseModel):
    column: str
    operator: str = "=="  # "==", "!=", ">", "<", ">=", "<=", "contains", "is_null", "is_not_null"
    value: Optional[Any] = None


class ChartConfig(BaseModel):
    chart_type: str = "bar"  # "bar", "line", "pie", "area", "histogram", "scatter"
    x_axis: str
    y_axis: Optional[str] = None
    title: str
    series_keys: List[str] = Field(default_factory=list)


class AnalyticalQueryPlan(BaseModel):
    operation: str = "aggregate"  # "aggregate", "group_by", "sort_limit", "filter", "distribution", "outlier_detection", "correlation", "missing_analysis", "general_summary"
    target_columns: List[str] = Field(default_factory=list)
    group_by_column: Optional[str] = None
    aggregation_func: Optional[str] = None  # "count", "sum", "mean", "median", "min", "max", "distinct_count"
    filters: List[FilterCondition] = Field(default_factory=list)
    sort_by: Optional[str] = None
    sort_ascending: bool = False
    limit: int = 25
    chart_recommendation: Optional[ChartConfig] = None
    reasoning: str = ""


class QueryResultTable(BaseModel):
    columns: List[str] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    total_rows: int = 0


class QueryExecutionResult(BaseModel):
    table: Optional[QueryResultTable] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    chart_data: Optional[List[Dict[str, Any]]] = None
    chart_config: Optional[ChartConfig] = None
    computation_summary: str = ""
    row_count_analyzed: int = 0


class ChatQueryRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatQueryResponse(BaseModel):
    session_id: str
    message_id: str
    reply: str
    plan: AnalyticalQueryPlan
    result: QueryExecutionResult
    dataset_version: int


class AnalysisMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    role: str
    content: str
    analytical_plan: Optional[Dict[str, Any]] = None
    execution_result: Optional[Dict[str, Any]] = None
    dataset_version: int
    created_at: datetime


class AnalysisSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    project_id: str
    dataset_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[AnalysisMessageRead] = Field(default_factory=list)


class AnalysisSessionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    dataset_id: str
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class InsightItem(BaseModel):
    title: str
    category: str  # "overview", "numeric_pattern", "extremes", "categorical", "outlier", "correlation", "quality"
    explanation: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    columns: List[str] = Field(default_factory=list)
    method: str = ""
    suggested_followup: Optional[str] = None
    chart_data: Optional[List[Dict[str, Any]]] = None
    chart_config: Optional[ChartConfig] = None


class AutoInsightsResponse(BaseModel):
    dataset_id: str
    dataset_name: str
    dataset_version: int
    record_count: int
    insights: List[InsightItem]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DescriptiveStat(BaseModel):
    column: str
    count: int
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    q25: Optional[float] = None
    median: Optional[float] = None
    q75: Optional[float] = None
    max: Optional[float] = None
    null_count: int = 0


class CorrelationPair(BaseModel):
    column_a: str
    column_b: str
    coefficient: float
    strength: str  # "strong_positive", "moderate_positive", "strong_negative", "moderate_negative", "weak"


class OutlierReport(BaseModel):
    column: str
    lower_bound: float
    upper_bound: float
    outlier_count: int
    sample_outlier_values: List[Any] = Field(default_factory=list)


class StatisticalAnalysisResponse(BaseModel):
    dataset_id: str
    dataset_version: int
    record_count: int
    descriptive_stats: List[DescriptiveStat]
    correlation_matrix: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    top_correlations: List[CorrelationPair] = Field(default_factory=list)
    outliers: List[OutlierReport] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReportCreateRequest(BaseModel):
    title: str
    format: str = "html"  # "html", "json"
    include_insights: bool = True
    include_statistics: bool = True
    include_chat_highlights: bool = True
    custom_notes: Optional[str] = None


class AnalysisReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    dataset_id: str
    user_id: str
    title: str
    format: str
    report_data: Dict[str, Any]
    file_path: Optional[str] = None
    dataset_version: int
    created_at: datetime
