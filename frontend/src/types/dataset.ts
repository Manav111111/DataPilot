export type DatasetStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface Dataset {
  id: string;
  project_id: string;
  user_id: string;
  name: string;
  description: string | null;
  status: DatasetStatus;
  row_count: number;
  created_at: string;
  updated_at: string;
  project_name?: string;
}

export interface CreateDatasetPayload {
  project_id: string;
  name: string;
  description?: string;
  status?: DatasetStatus;
  row_count?: number;
}

export interface UpdateDatasetPayload {
  name?: string;
  description?: string;
  status?: DatasetStatus;
  row_count?: number;
}
