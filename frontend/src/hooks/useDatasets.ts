import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { datasetService } from '../services/datasetService';
import { CreateDatasetPayload, UpdateDatasetPayload } from '../types/dataset';

export const useDatasets = (params?: {
  page?: number;
  size?: number;
  project_id?: string;
  search?: string;
  status?: string;
}) => {
  return useQuery({
    queryKey: ['datasets', params],
    queryFn: () => datasetService.getDatasets(params),
  });
};

export const useDataset = (id?: string) => {
  return useQuery({
    queryKey: ['dataset', id],
    queryFn: () => (id ? datasetService.getDataset(id) : null),
    enabled: !!id,
  });
};

export const useCreateDataset = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateDatasetPayload) => datasetService.createDataset(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['project', variables.project_id] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
  });
};

export const useUpdateDataset = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateDatasetPayload }) =>
      datasetService.updateDataset(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
      queryClient.invalidateQueries({ queryKey: ['dataset', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
  });
};

export const useDeleteDataset = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => datasetService.deleteDataset(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
  });
};
