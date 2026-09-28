import { apiClient } from '../lib/axios';
import { WorkflowRun } from '../types/workflow';
import { PaginatedResponse } from '../types/api';

export const workflowService = {
  async getWorkflows(params?: {
    page?: number;
    size?: number;
    project_id?: string;
  }): Promise<PaginatedResponse<WorkflowRun>> {
    const res = await apiClient.get<PaginatedResponse<WorkflowRun>>('/workflows', { params });
    return res.data;
  },

  async getWorkflow(id: string): Promise<WorkflowRun> {
    const res = await apiClient.get<WorkflowRun>(`/workflows/${id}`);
    return res.data;
  },
};
