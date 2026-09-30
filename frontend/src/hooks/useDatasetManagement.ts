import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { datasetManagementService } from '../services/datasetManagementService';

export function useDatasetProfile(datasetId?: string) {
  return useQuery({
    queryKey: ['dataset-profile', datasetId],
    queryFn: () => datasetManagementService.getDatasetProfile(datasetId!),
    enabled: !!datasetId,
  });
}

export function useDatasetTransformations(datasetId?: string) {
  return useQuery({
    queryKey: ['dataset-transformations', datasetId],
    queryFn: () => datasetManagementService.listTransformations(datasetId!),
    enabled: !!datasetId,
  });
}

export function useDatasetDuplicates(datasetId?: string, keyFields?: string[]) {
  return useQuery({
    queryKey: ['dataset-duplicates', datasetId, keyFields],
    queryFn: () => datasetManagementService.getDuplicateGroups(datasetId!, keyFields),
    enabled: !!datasetId,
  });
}

export function useDatasetCharts(datasetId?: string) {
  return useQuery({
    queryKey: ['dataset-charts', datasetId],
    queryFn: () => datasetManagementService.listCharts(datasetId!),
    enabled: !!datasetId,
  });
}

export function useDatasetDistributions(datasetId?: string, fields?: string[]) {
  return useQuery({
    queryKey: ['dataset-distributions', datasetId, fields],
    queryFn: () => datasetManagementService.getFieldDistributions(datasetId!, fields),
    enabled: !!datasetId,
  });
}

export function useDatasetExports(datasetId?: string) {
  return useQuery({
    queryKey: ['dataset-exports', datasetId],
    queryFn: () => datasetManagementService.listExports(datasetId!),
    enabled: !!datasetId,
  });
}

export function useDatasetVersions(datasetId?: string) {
  return useQuery({
    queryKey: ['dataset-versions', datasetId],
    queryFn: () => datasetManagementService.listVersions(datasetId!),
    enabled: !!datasetId,
  });
}

export function useDatasetManagementMutations(datasetId?: string) {
  const queryClient = useQueryClient();

  const invalidateDataset = () => {
    if (datasetId) {
      queryClient.invalidateQueries({ queryKey: ['dataset-profile', datasetId] });
      queryClient.invalidateQueries({ queryKey: ['dataset-records', datasetId] });
      queryClient.invalidateQueries({ queryKey: ['dataset-overview', datasetId] });
      queryClient.invalidateQueries({ queryKey: ['dataset-duplicates', datasetId] });
      queryClient.invalidateQueries({ queryKey: ['dataset-charts', datasetId] });
      queryClient.invalidateQueries({ queryKey: ['dataset-versions', datasetId] });
      queryClient.invalidateQueries({ queryKey: ['dataset-transformations', datasetId] });
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
    }
  };

  const cleanApplyMutation = useMutation({
    mutationFn: ({
      operationType,
      configuration,
      createVersion,
      changeSummary,
    }: {
      operationType: string;
      configuration: Record<string, any>;
      createVersion?: boolean;
      changeSummary?: string;
    }) =>
      datasetManagementService.applyClean(
        datasetId!,
        operationType,
        configuration,
        createVersion,
        changeSummary
      ),
    onSuccess: invalidateDataset,
  });

  const transformApplyMutation = useMutation({
    mutationFn: ({
      operationType,
      configuration,
      createVersion,
      changeSummary,
    }: {
      operationType: string;
      configuration: Record<string, any>;
      createVersion?: boolean;
      changeSummary?: string;
    }) =>
      datasetManagementService.applyTransform(
        datasetId!,
        operationType,
        configuration,
        createVersion,
        changeSummary
      ),
    onSuccess: invalidateDataset,
  });

  const mergeDuplicatesMutation = useMutation({
    mutationFn: ({
      retainedRecordId,
      mergedRecordIds,
      fieldOverrides,
    }: {
      retainedRecordId: string;
      mergedRecordIds: string[];
      fieldOverrides?: Record<string, any>;
    }) =>
      datasetManagementService.mergeDuplicates(
        datasetId!,
        retainedRecordId,
        mergedRecordIds,
        fieldOverrides
      ),
    onSuccess: invalidateDataset,
  });

  const createChartMutation = useMutation({
    mutationFn: ({
      chartName,
      chartType,
      configuration,
    }: {
      chartName: string;
      chartType: string;
      configuration: Record<string, any>;
    }) =>
      datasetManagementService.createChart(
        datasetId!,
        chartName,
        chartType,
        configuration
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataset-charts', datasetId] });
    },
  });

  const deleteChartMutation = useMutation({
    mutationFn: (chartId: string) => datasetManagementService.deleteChart(chartId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataset-charts', datasetId] });
    },
  });

  const restoreVersionMutation = useMutation({
    mutationFn: (versionId: string) =>
      datasetManagementService.restoreVersion(datasetId!, versionId),
    onSuccess: invalidateDataset,
  });

  return {
    cleanApplyMutation,
    transformApplyMutation,
    mergeDuplicatesMutation,
    createChartMutation,
    deleteChartMutation,
    restoreVersionMutation,
  };
}
