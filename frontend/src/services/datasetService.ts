import { apiClient } from '../lib/axios';
import { Dataset, CreateDatasetPayload, UpdateDatasetPayload } from '../types/dataset';
import { PaginatedResponse } from '../types/api';

export const datasetService = {
  async getDatasets(params?: {
    page?: number;
    size?: number;
    project_id?: string;
    search?: string;
    status?: string;
  }): Promise<PaginatedResponse<Dataset>> {
    const res = await apiClient.get<PaginatedResponse<Dataset>>('/datasets', { params });
    return res.data;
  },

  async getDataset(id: string): Promise<Dataset> {
    const res = await apiClient.get<Dataset>(`/datasets/${id}`);
    return res.data;
  },

  async createDataset(data: CreateDatasetPayload): Promise<Dataset> {
    const res = await apiClient.post<Dataset>('/datasets', data);
    return res.data;
  },

  async updateDataset(id: string, data: UpdateDatasetPayload): Promise<Dataset> {
    const res = await apiClient.patch<Dataset>(`/datasets/${id}`, data);
    return res.data;
  },

  async deleteDataset(id: string): Promise<void> {
    await apiClient.delete(`/datasets/${id}`);
  },
};
