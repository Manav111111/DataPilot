export interface FilterCondition {
  column: string;
  operator: string;
  value?: any;
}

export interface ChartConfig {
  chart_type: 'bar' | 'line' | 'pie' | 'area' | 'histogram' | 'scatter';
  x_axis: string;
  y_axis?: string;
  title: string;
  series_keys?: string[];
}

export interface AnalyticalQueryPlan {
  operation: string;
  target_columns: string[];
  group_by_column?: string;
  aggregation_func?: string;
  filters: FilterCondition[];
  sort_by?: string;
  sort_ascending: boolean;
  limit: number;
  chart_recommendation?: ChartConfig;
  reasoning: string;
}

export interface QueryResultTable {
  columns: string[];
  rows: Record<string, any>[];
  total_rows: number;
}

export interface QueryExecutionResult {
  table?: QueryResultTable;
  metrics: Record<string, any>;
  chart_data?: Record<string, any>[];
  chart_config?: ChartConfig;
  computation_summary: string;
  row_count_analyzed: number;
}

export interface AnalysisMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  analytical_plan?: AnalyticalQueryPlan;
  execution_result?: QueryExecutionResult;
  dataset_version: number;
  created_at: string;
}

export interface AnalysisSession {
  id: string;
  user_id: string;
  project_id: string;
  dataset_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: AnalysisMessage[];
}

export interface ChatQueryResponse {
  session_id: string;
  message_id: string;
  reply: string;
  plan: AnalyticalQueryPlan;
  result: QueryExecutionResult;
  dataset_version: number;
}

export interface InsightItem {
  title: string;
  category: 'overview' | 'numeric_pattern' | 'extremes' | 'categorical' | 'outlier' | 'correlation' | 'quality';
  explanation: string;
  evidence: Record<string, any>;
  columns: string[];
  method: string;
  suggested_followup?: string;
  chart_data?: Record<string, any>[];
  chart_config?: ChartConfig;
}

export interface AutoInsightsResponse {
  dataset_id: string;
  dataset_name: string;
  dataset_version: number;
  record_count: number;
  insights: InsightItem[];
  generated_at: string;
}

export interface DescriptiveStat {
  column: string;
  count: number;
  mean?: number;
  std?: number;
  min?: number;
  q25?: number;
  median?: number;
  q75?: number;
  max?: number;
  null_count: number;
}

export interface CorrelationPair {
  column_a: string;
  column_b: string;
  coefficient: number;
  strength: string;
}

export interface OutlierReport {
  column: string;
  lower_bound: number;
  upper_bound: number;
  outlier_count: number;
  sample_outlier_values: any[];
}

export interface StatisticalAnalysisResponse {
  dataset_id: string;
  dataset_version: number;
  record_count: number;
  descriptive_stats: DescriptiveStat[];
  correlation_matrix: Record<string, Record<string, number | null>>;
  top_correlations: CorrelationPair[];
  outliers: OutlierReport[];
  generated_at: string;
}

export interface ReportCreateRequest {
  title: string;
  format?: 'html' | 'json';
  include_insights?: boolean;
  include_statistics?: boolean;
  include_chat_highlights?: boolean;
  custom_notes?: string;
}

export interface AnalysisReport {
  id: string;
  dataset_id: string;
  user_id: string;
  title: string;
  format: string;
  report_data: Record<string, any>;
  file_path?: string;
  dataset_version: number;
  created_at: string;
}
