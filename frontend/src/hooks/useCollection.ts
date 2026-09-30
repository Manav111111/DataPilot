import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { collectionService } from '../services/collectionService';
import { StartCollectionRequest } from '../types/collection';

export function useStartCollection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      planId,
      payload,
    }: {
      planId: string;
      payload?: StartCollectionRequest;
    }) => collectionService.startCollection(planId, payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['collection_jobs'] });
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
      queryClient.invalidateQueries({ queryKey: ['plans'] });
    },
  });
}

export function useCollectionJob(jobId?: string) {
  return useQuery({
    queryKey: ['collection_job', jobId],
    queryFn: () => collectionService.getCollectionJob(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 2000;
      // Stop polling when terminal status is reached
      if (['completed', 'completed_with_errors', 'failed', 'cancelled'].includes(data.status)) {
        return false;
      }
      return 2000; // Poll every 2s while running/queued
    },
  });
}

export function useProjectCollectionJobs(
  projectId?: string,
  params?: { page?: number; size?: number; status?: string }
) {
  return useQuery({
    queryKey: ['collection_jobs', projectId, params],
    queryFn: () => collectionService.listProjectJobs(projectId!, params),
    enabled: !!projectId,
    refetchInterval: 5000,
  });
}

export function useCancelCollectionJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => collectionService.cancelJob(jobId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['collection_job', data.id] });
      queryClient.invalidateQueries({ queryKey: ['collection_jobs'] });
    },
  });
}

export function useRetryCollectionJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => collectionService.retryJob(jobId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['collection_job', data.id] });
      queryClient.invalidateQueries({ queryKey: ['collection_jobs'] });
    },
  });
}

export function useJobEvents(jobId?: string, enabled = true) {
  return useQuery({
    queryKey: ['job_events', jobId],
    queryFn: () => collectionService.getJobEvents(jobId!),
    enabled: !!jobId && enabled,
    refetchInterval: 3000,
  });
}

export function useDatasetRecords(
  datasetId?: string,
  params?: {
    page?: number;
    size?: number;
    search?: string;
    validation_status?: string;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
  }
) {
  return useQuery({
    queryKey: ['dataset_records', datasetId, params],
    queryFn: () => collectionService.listDatasetRecords(datasetId!, params),
    enabled: !!datasetId,
  });
}

export function useRecordProvenance(recordId?: string, enabled = true) {
  return useQuery({
    queryKey: ['record_provenance', recordId],
    queryFn: () => collectionService.getRecordProvenance(recordId!),
    enabled: !!recordId && enabled,
  });
}

export function useDatasetSources(
  datasetId?: string,
  params?: { page?: number; size?: number; domain?: string; retrieval_status?: string }
) {
  return useQuery({
    queryKey: ['dataset_sources', datasetId, params],
    queryFn: () => collectionService.listDatasetSources(datasetId!, params),
    enabled: !!datasetId,
  });
}

export function useDatasetOverview(datasetId?: string) {
  return useQuery({
    queryKey: ['dataset_overview', datasetId],
    queryFn: () => collectionService.getDatasetOverview(datasetId!),
    enabled: !!datasetId,
  });
}
