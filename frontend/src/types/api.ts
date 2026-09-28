import { Project } from './project';
import { Dataset } from './dataset';
import { WorkflowRun } from './workflow';

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface DashboardStats {
  total_projects: number;
  total_datasets: number;
  completed_workflows: number;
  failed_workflows: number;
  active_projects: number;
  total_rows: number;
  recent_projects: Project[];
  recent_datasets: Dataset[];
  recent_workflows: WorkflowRun[];
}

export interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  detail?: string;
  success?: boolean;
}
