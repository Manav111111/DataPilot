export type PlanStatus =
  | 'draft'
  | 'needs_clarification'
  | 'ready_for_review'
  | 'approved'
  | 'rejected';

export type FieldType =
  | 'string'
  | 'number'
  | 'url'
  | 'email'
  | 'phone'
  | 'date'
  | 'boolean'
  | 'array'
  | 'object';

export type RuleType =
  | 'required'
  | 'valid_url'
  | 'valid_email'
  | 'geo_normalization'
  | 'duplicate_check'
  | 'completeness'
  | 'source_attribution'
  | 'custom';

export interface FieldDefinition {
  name: string;
  label: string;
  type: FieldType;
  required: boolean;
  description?: string;
  validation_rules?: string[];
  allow_missing?: boolean;
  requires_source_evidence?: boolean;
}

export interface SearchQuery {
  query: string;
  purpose: string;
  source_category: string;
  geography?: string;
  priority: number;
}

export interface SourceRecommendation {
  source_category: string;
  rationale: string;
  expected_fields: string[];
  limitations?: string;
  access_requirements?: string;
}

export interface QualityRule {
  name: string;
  description: string;
  rule_type: RuleType;
  field?: string;
  configuration?: Record<string, any>;
}

export interface CollectionPlanData {
  goal: string;
  entity_type: string;
  geography?: string;
  target_record_count: number;
  fields: FieldDefinition[];
  search_queries: SearchQuery[];
  source_recommendations: SourceRecommendation[];
  filters: string[];
  quality_rules: QualityRule[];
  execution_steps: string[];
  assumptions: string[];
  limitations: string[];
  clarification_questions: string[];
}

export interface CollectionPlan {
  id: string;
  user_id: string;
  project_id: string;
  original_request: string;
  status: PlanStatus;
  plan_data: CollectionPlanData;
  provider_metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
  project_name?: string;
}

export interface GeneratePlanPayload {
  request: string;
  target_record_count?: number;
  clarification_answers?: Record<string, string>;
}

export interface UpdatePlanPayload {
  goal?: string;
  entity_type?: string;
  geography?: string;
  target_record_count?: number;
  fields?: FieldDefinition[];
  search_queries?: SearchQuery[];
  source_recommendations?: SourceRecommendation[];
  filters?: string[];
  quality_rules?: QualityRule[];
  assumptions?: string[];
  limitations?: string[];
}

export interface RegeneratePlanPayload {
  feedback?: string;
  clarification_answers?: Record<string, string>;
}
