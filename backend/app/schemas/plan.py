from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class PlanStatus(str, Enum):
    DRAFT = "draft"
    NEEDS_CLARIFICATION = "needs_clarification"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class FieldType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    URL = "url"
    EMAIL = "email"
    PHONE = "phone"
    DATE = "date"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class RuleType(str, Enum):
    REQUIRED = "required"
    VALID_URL = "valid_url"
    VALID_EMAIL = "valid_email"
    GEO_NORMALIZATION = "geo_normalization"
    DUPLICATE_CHECK = "duplicate_check"
    COMPLETENESS = "completeness"
    SOURCE_ATTRIBUTION = "source_attribution"
    CUSTOM = "custom"


class FieldDefinition(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    label: str = Field(..., min_length=1, max_length=150)
    type: FieldType = Field(default=FieldType.STRING)
    required: bool = Field(default=True)
    description: Optional[str] = None
    validation_rules: List[str] = Field(default_factory=list)
    allow_missing: bool = Field(default=False)
    requires_source_evidence: bool = Field(default=True)

    model_config = ConfigDict(from_attributes=True)


class SearchQuery(BaseModel):
    query: str = Field(..., min_length=2, max_length=300)
    purpose: str = Field(..., min_length=2, max_length=300)
    source_category: str = Field(..., min_length=2, max_length=100)
    geography: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=5)

    model_config = ConfigDict(from_attributes=True)


class SourceRecommendation(BaseModel):
    source_category: str = Field(..., min_length=2, max_length=100)
    rationale: str
    expected_fields: List[str] = Field(default_factory=list)
    limitations: Optional[str] = None
    access_requirements: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class QualityRule(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    description: str
    rule_type: RuleType = Field(default=RuleType.CUSTOM)
    field: Optional[str] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class CollectionPlanData(BaseModel):
    goal: str = Field(..., description="Clear summary of user's data goal")
    entity_type: str = Field(..., description="Target entity type e.g. Job Posting, Startup, Company")
    geography: Optional[str] = None
    target_record_count: int = Field(default=100, ge=1, le=10000)
    fields: List[FieldDefinition] = Field(default_factory=list)
    search_queries: List[SearchQuery] = Field(default_factory=list)
    source_recommendations: List[SourceRecommendation] = Field(default_factory=list)
    filters: List[str] = Field(default_factory=list)
    quality_rules: List[QualityRule] = Field(default_factory=list)
    execution_steps: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    clarification_questions: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class GeneratePlanRequest(BaseModel):
    request: str = Field(..., min_length=5, max_length=2000, description="Natural language data requirement")
    target_record_count: Optional[int] = Field(None, ge=1, le=10000)
    clarification_answers: Optional[Dict[str, str]] = None


class UpdatePlanRequest(BaseModel):
    goal: Optional[str] = None
    entity_type: Optional[str] = None
    geography: Optional[str] = None
    target_record_count: Optional[int] = Field(None, ge=1, le=10000)
    fields: Optional[List[FieldDefinition]] = None
    search_queries: Optional[List[SearchQuery]] = None
    source_recommendations: Optional[List[SourceRecommendation]] = None
    filters: Optional[List[str]] = None
    quality_rules: Optional[List[QualityRule]] = None
    assumptions: Optional[List[str]] = None
    limitations: Optional[List[str]] = None


class RegeneratePlanRequest(BaseModel):
    feedback: Optional[str] = Field(None, max_length=2000)
    clarification_answers: Optional[Dict[str, str]] = None


class CollectionPlanResponse(BaseModel):
    id: str
    user_id: str
    project_id: str
    original_request: str
    status: PlanStatus
    plan_data: CollectionPlanData
    provider_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    project_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
