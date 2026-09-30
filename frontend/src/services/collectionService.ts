import { apiClient } from '../lib/axios';
import {
  CollectionJob,
  CollectionJobEvent,
  DataSource,
  RecordSource,
  DatasetRecord,
  DatasetOverviewStats,
  StartCollectionRequest,
  StartCollectionResponse,
} from '../types/collection';
import { PaginatedResponse } from '../types/api';

export const collectionService = {
  async startCollection(
    planId: string,
    payload: StartCollectionRequest = {}
  ): Promise<StartCollectionResponse> {
    const { data } = await apiClient.post<StartCollectionResponse>(
      `/plans/${planId}/collect`,
      payload
    );
    return data;
  },

  async getCollectionJob(jobId: string): Promise<CollectionJob> {
    const { data } = await apiClient.get<CollectionJob>(`/collection-jobs/${jobId}`);
    return data;
  },

  async listProjectJobs(
    projectId: string,
    params?: { page?: number; size?: number; status?: string }
  ): Promise<PaginatedResponse<CollectionJob>> {
    const { data } = await apiClient.get<PaginatedResponse<CollectionJob>>(
      `/projects/${projectId}/collection-jobs`,
      { params }
    );
    return data;
  },

  async cancelJob(jobId: string): Promise<CollectionJob> {
    const { data } = await apiClient.post<CollectionJob>(`/collection-jobs/${jobId}/cancel`);
    return data;
  },

  async retryJob(jobId: string): Promise<CollectionJob> {
    const { data } = await apiClient.post<CollectionJob>(`/collection-jobs/${jobId}/retry`);
    return data;
  },

  async getJobEvents(jobId: string): Promise<{ items: CollectionJobEvent[]; total: number }> {
    const { data } = await apiClient.get<{ items: CollectionJobEvent[]; total: number }>(
      `/collection-jobs/${jobId}/events`
    );
    return data;
  },

  async listDatasetRecords(
    datasetId: string,
    params?: {
      page?: number;
      size?: number;
      search?: string;
      validation_status?: string;
      sort_by?: string;
      sort_order?: 'asc' | 'desc';
    }
  ): Promise<PaginatedResponse<DatasetRecord>> {
    const { data } = await apiClient.get<PaginatedResponse<DatasetRecord>>(
      `/datasets/${datasetId}/records`,
      { params }
    );
    return data;
  },

  async getRecordProvenance(recordId: string): Promise<RecordSource[]> {
    const { data } = await apiClient.get<RecordSource[]>(`/dataset-records/${recordId}/sources`);
    return data;
  },

  async listDatasetSources(
    datasetId: string,
    params?: { page?: number; size?: number; domain?: string; retrieval_status?: string }
  ): Promise<PaginatedResponse<DataSource>> {
    const { data } = await apiClient.get<PaginatedResponse<DataSource>>(
      `/datasets/${datasetId}/sources`,
      { params }
    );
    return data;
  },

  async getDatasetOverview(datasetId: string): Promise<DatasetOverviewStats> {
    const { data } = await apiClient.get<DatasetOverviewStats>(`/datasets/${datasetId}/overview`);
    return data;
  },

  async downloadExport(datasetId: string, format: 'json' | 'csv' = 'json'): Promise<void> {
    const response = await apiClient.get(`/datasets/${datasetId}/export`, {
      params: { format },
      responseType: 'blob',
    });

    const blob = new Blob([response.data], {
      type: format === 'csv' ? 'text/csv' : 'application/json',
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `dataset_${datasetId.slice(0, 8)}.${format}`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};
