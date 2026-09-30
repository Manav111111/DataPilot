export type CollectionJobStatus =
  | 'queued'
  | 'running'
  | 'completed'
  | 'completed_with_errors'
  | 'failed'
  | 'cancelled';

export type CollectionStage =
  | 'initializing'
  | 'searching'
  | 'extracting'
  | 'structuring'
  | 'validating'
  | 'deduplicating'
  | 'saving'
  | 'completed';

export type ValidationStatus = 'valid' | 'valid_with_warnings' | 'invalid';

export interface CollectionJob {
  id: string;
  user_id: string;
  project_id: string;
  plan_id: string;
  dataset_id: string;
  status: CollectionJobStatus;
  current_stage: CollectionStage;
  progress_percentage: number;
  total_queries: number;
  completed_queries: number;
  total_sources: number;
  processed_sources: number;
  records_extracted: number;
  records_saved: number;
  records_rejected: number;
  error_message?: string | null;
  retry_count: number;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CollectionJobEvent {
  id: string;
  collection_job_id: string;
  event_type: string;
  message: string;
  event_metadata?: Record<string, any> | null;
  created_at: string;
}

export interface DataSource {
  id: string;
  dataset_id: string;
  collection_job_id: string;
  source_url: string;
  canonical_url?: string | null;
  domain?: string | null;
  page_title?: string | null;
  source_type: string;
  retrieval_status: string;
  retrieved_at?: string | null;
  content_hash?: string | null;
  error_message?: string | null;
  search_query?: string | null;
  created_at: string;
}

export interface RecordSource {
  id: string;
  dataset_record_id: string;
  data_source_id: string;
  evidence_excerpt?: string | null;
  evidence_field?: string | null;
  source_url?: string | null;
  domain?: string | null;
  page_title?: string | null;
  created_at: string;
}

export interface ValidationErrorDetail {
  field_name: string;
  error_type: string;
  message: string;
  severity: 'error' | 'warning';
}

export interface DatasetRecord {
  id: string;
  dataset_id: string;
  record_data: Record<string, any>;
  normalized_data: Record<string, any>;
  record_hash?: string | null;
  validation_status: ValidationStatus;
  validation_errors?: ValidationErrorDetail[] | null;
  source_count: number;
  created_at: string;
  updated_at: string;
  sources?: RecordSource[] | null;
}

export interface DatasetOverviewStats {
  total_records: number;
  valid_records: number;
  records_with_warnings: number;
  rejected_records: number;
  duplicate_count: number;
  source_count: number;
  latest_job_status?: string | null;
}

export interface StartCollectionRequest {
  dataset_name?: string;
  max_records?: number;
  max_queries?: number;
}

export interface StartCollectionResponse {
  job_id: string;
  dataset_id: string;
  status: string;
  message: string;
}
