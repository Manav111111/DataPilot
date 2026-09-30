import { apiClient as api } from '../lib/axios';
import {
  DatasetProfileResponse,
  CleanPreviewResponse,
  TransformPreviewResponse,
  TransformationResponse,
  DuplicateGroup,
  ChartResponse,
  DatasetCompareResponse,
  ExportResponse,
  VersionResponse,
} from '../types/dataset_management';

export const datasetManagementService = {
  // Profiling & Quality
  async profileDataset(datasetId: string): Promise<DatasetProfileResponse> {
    const res = await api.post<DatasetProfileResponse>(`/datasets/${datasetId}/profile`);
    return res.data;
  },

  async getDatasetProfile(datasetId: string): Promise<DatasetProfileResponse> {
    const res = await api.get<DatasetProfileResponse>(`/datasets/${datasetId}/profile`);
    return res.data;
  },

  // Cleaning
  async previewClean(
    datasetId: string,
    operationType: string,
    configuration: Record<string, any>
  ): Promise<CleanPreviewResponse> {
    const res = await api.post<CleanPreviewResponse>(`/datasets/${datasetId}/clean/preview`, {
      operation_type: operationType,
      configuration,
    });
    return res.data;
  },

  async applyClean(
    datasetId: string,
    operationType: string,
    configuration: Record<string, any>,
    createVersion: boolean = true,
    changeSummary?: string
  ): Promise<{ message: string; records_affected: number; transformation_id: string }> {
    const res = await api.post(`/datasets/${datasetId}/clean/apply`, {
      operation_type: operationType,
      configuration,
      create_version: createVersion,
      change_summary: changeSummary,
    });
    return res.data;
  },

  // Transformations
  async previewTransform(
    datasetId: string,
    operationType: string,
    configuration: Record<string, any>
  ): Promise<TransformPreviewResponse> {
    const res = await api.post<TransformPreviewResponse>(`/datasets/${datasetId}/transformations/preview`, {
      operation_type: operationType,
      configuration,
    });
    return res.data;
  },

  async applyTransform(
    datasetId: string,
    operationType: string,
    configuration: Record<string, any>,
    createVersion: boolean = true,
    changeSummary?: string
  ): Promise<{ message: string; records_affected: number; transformation_id: string }> {
    const res = await api.post(`/datasets/${datasetId}/transformations`, {
      operation_type: operationType,
      configuration,
      create_version: createVersion,
      change_summary: changeSummary,
    });
    return res.data;
  },

  async listTransformations(datasetId: string): Promise<TransformationResponse[]> {
    const res = await api.get<TransformationResponse[]>(`/datasets/${datasetId}/transformations`);
    return res.data;
  },

  // Records Editing
  async updateRecord(
    recordId: string,
    recordData: Record<string, any>,
    validationStatus?: string
  ): Promise<any> {
    const res = await api.patch(`/dataset-records/${recordId}`, {
      record_data: recordData,
      validation_status: validationStatus,
    });
    return res.data;
  },

  async deleteRecord(recordId: string): Promise<any> {
    const res = await api.delete(`/dataset-records/${recordId}`);
    return res.data;
  },

  async bulkUpdateRecords(
    datasetId: string,
    recordIds: string[],
    updates: Record<string, any>
  ): Promise<any> {
    const res = await api.post(`/datasets/${datasetId}/records/bulk-update`, {
      record_ids: recordIds,
      updates,
    });
    return res.data;
  },

  async bulkDeleteRecords(datasetId: string, recordIds: string[]): Promise<any> {
    const res = await api.post(`/datasets/${datasetId}/records/bulk-delete`, {
      record_ids: recordIds,
    });
    return res.data;
  },

  // Duplicates
  async getDuplicateGroups(datasetId: string, keyFields?: string[]): Promise<DuplicateGroup[]> {
    const params = keyFields && keyFields.length > 0 ? { key_fields: keyFields } : {};
    const res = await api.get<DuplicateGroup[]>(`/datasets/${datasetId}/duplicates`, { params });
    return res.data;
  },

  async mergeDuplicates(
    datasetId: string,
    retainedRecordId: string,
    mergedRecordIds: string[],
    fieldOverrides?: Record<string, any>,
    createVersion: boolean = true
  ): Promise<any> {
    const res = await api.post(`/datasets/${datasetId}/duplicates/merge`, {
      retained_record_id: retainedRecordId,
      merged_record_ids: mergedRecordIds,
      field_overrides: fieldOverrides,
      create_version: createVersion,
    });
    return res.data;
  },

  // Analytics & Charts
  async getFieldDistributions(datasetId: string, fields?: string[]): Promise<any> {
    const params = fields && fields.length > 0 ? { fields } : {};
    const res = await api.get(`/datasets/${datasetId}/analytics/distributions`, { params });
    return res.data;
  },

  async createChart(
    datasetId: string,
    chartName: string,
    chartType: string,
    configuration: Record<string, any>
  ): Promise<ChartResponse> {
    const res = await api.post<ChartResponse>(`/datasets/${datasetId}/analytics/charts`, {
      chart_name: chartName,
      chart_type: chartType,
      configuration,
    });
    return res.data;
  },

  async listCharts(datasetId: string): Promise<ChartResponse[]> {
    const res = await api.get<ChartResponse[]>(`/datasets/${datasetId}/analytics/charts`);
    return res.data;
  },

  async deleteChart(chartId: string): Promise<any> {
    const res = await api.delete(`/analytics/charts/${chartId}`);
    return res.data;
  },

  // Dataset Comparison
  async compareDatasets(
    datasetIdA: string,
    datasetIdB: string,
    matchingKey?: string
  ): Promise<DatasetCompareResponse> {
    const res = await api.post<DatasetCompareResponse>('/datasets/compare', {
      dataset_id_a: datasetIdA,
      dataset_id_b: datasetIdB,
      matching_key: matchingKey,
    });
    return res.data;
  },

  // Exports
  async createExport(
    datasetId: string,
    format: string,
    columns?: string[],
    includeProvenance: boolean = true,
    includeWarnings: boolean = false,
    filters?: Record<string, any>
  ): Promise<ExportResponse> {
    const res = await api.post<ExportResponse>(`/datasets/${datasetId}/exports`, {
      format,
      columns,
      include_provenance: includeProvenance,
      include_warnings: includeWarnings,
      filters,
    });
    return res.data;
  },

  async listExports(datasetId: string): Promise<ExportResponse[]> {
    const res = await api.get<ExportResponse[]>(`/datasets/${datasetId}/exports`);
    return res.data;
  },

  getExportDownloadUrl(exportId: string): string {
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    return `${baseURL}/api/v1/exports/${exportId}/download`;
  },

  // Versioning
  async listVersions(datasetId: string): Promise<VersionResponse[]> {
    const res = await api.get<VersionResponse[]>(`/datasets/${datasetId}/versions`);
    return res.data;
  },

  async getVersion(versionId: string): Promise<VersionResponse & { snapshot_data: any[] }> {
    const res = await api.get(`/datasets/${versionId}/versions/${versionId}`);
    return res.data;
  },

  async restoreVersion(datasetId: string, versionId: string): Promise<any> {
    const res = await api.post(`/datasets/${datasetId}/versions/${versionId}/restore`);
    return res.data;
  },
};
