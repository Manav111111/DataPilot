export type WorkflowStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface WorkflowRun {
  id: string;
  project_id: string;
  user_id: string;
  status: WorkflowStatus;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  created_at: string;
  project_name?: string;
}
