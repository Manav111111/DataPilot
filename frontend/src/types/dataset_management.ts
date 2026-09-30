export interface ColumnProfile {
  column_name: string;
  display_label: string;
  inferred_type: string;
  non_null_count: number;
  null_count: number;
  missing_percentage: number;
  unique_count: number;
  duplicate_count: number;
  min_value?: any;
  max_value?: any;
  mean?: number;
  median?: number;
  top_values: Array<{ value: string; count: number; percentage: number }>;
  string_length_stats?: { min_len: number; max_len: number; avg_len: number };
  valid_format_percentage: number;
  sample_values: any[];
}

export interface QualityDimensionDetail {
  score: number;
  affected_count: number;
  rule: string;
  explanation: string;
  suggestions: string[];
}

export interface QualityReportData {
  overall_score: number;
  dimension_scores: {
    completeness: number;
    validity: number;
    uniqueness: number;
    consistency: number;
    provenance: number;
  };
  dimensions: {
    completeness: QualityDimensionDetail;
    validity: QualityDimensionDetail;
    uniqueness: QualityDimensionDetail;
    consistency: QualityDimensionDetail;
    provenance: QualityDimensionDetail;
  };
  scoring_method_version: string;
}

export interface DatasetProfileResponse {
  dataset_id: string;
  dataset_name: string;
  overview: {
    total_records: number;
    total_columns: number;
    total_sources: number;
    valid_records: number;
    records_with_warnings: number;
    invalid_records: number;
    duplicate_records: number;
    unique_records: number;
    created_at: string;
    updated_at: string;
  };
  columns: ColumnProfile[];
  quality: QualityReportData;
  profiled_at: string;
}

export interface CleanPreviewResponse {
  operation_type: string;
  configuration: Record<string, any>;
  records_affected: number;
  fields_affected: string[];
  samples: Array<{
    record_id: string;
    original: Record<string, any>;
    cleaned?: Record<string, any>;
    action?: string;
  }>;
  potential_info_loss: boolean;
  warnings: string[];
}

export interface TransformPreviewResponse {
  operation_type: string;
  configuration: Record<string, any>;
  records_affected: number;
  fields_affected: string[];
  samples: Array<{
    record_id: string;
    original: Record<string, any>;
    transformed?: Record<string, any>;
    action?: string;
  }>;
  warnings: string[];
}

export interface TransformationResponse {
  id: string;
  dataset_id: string;
  operation_type: string;
  configuration: Record<string, any>;
  status: string;
  records_affected: number;
  created_at: string;
  completed_at?: string;
}

export interface DuplicateGroup {
  group_id: string;
  rule_type: string;
  match_field: string;
  match_value: string;
  confidence: number;
  record_count: number;
  records: Array<{
    id: string;
    record_data: Record<string, any>;
    source_count?: number;
    validation_status?: string;
  }>;
}

export interface ChartResponse {
  id: string;
  dataset_id: string;
  chart_name: string;
  chart_type: string;
  configuration: Record<string, any>;
  computed_data?: Array<Record<string, any>>;
  created_at: string;
  updated_at: string;
}

export interface DatasetCompareResponse {
  dataset_a: {
    id: string;
    name: string;
    record_count: number;
    quality_score: number;
  };
  dataset_b: {
    id: string;
    name: string;
    record_count: number;
    quality_score: number;
  };
  comparison: {
    record_count_delta: number;
    quality_score_delta: number;
    common_records_count: number;
    dataset_a_unique_count: number;
    dataset_b_new_count: number;
    matching_key_used: string;
  };
  schema_diff: {
    common_columns: string[];
    dataset_a_only_columns: string[];
    dataset_b_only_columns: string[];
    similarity_score: number;
  };
  field_comparisons: Record<string, any>;
}

export interface ExportResponse {
  id: string;
  dataset_id: string;
  format: string;
  export_configuration: Record<string, any>;
  status: string;
  file_reference?: string;
  file_size_bytes?: number;
  record_count?: number;
  download_url?: string;
  created_at: string;
  completed_at?: string;
}

export interface VersionResponse {
  id: string;
  dataset_id: string;
  version_number: number;
  change_type: string;
  change_summary: string;
  record_count: number;
  schema_snapshot: Record<string, any>;
  created_at: string;
}
