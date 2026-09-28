import { useQuery } from '@tanstack/react-query';
import { workflowService } from '../services/workflowService';

export const useWorkflows = (params?: {
  page?: number;
  size?: number;
  project_id?: string;
}) => {
  return useQuery({
    queryKey: ['workflows', params],
    queryFn: () => workflowService.getWorkflows(params),
  });
};

export const useWorkflow = (id?: string) => {
  return useQuery({
    queryKey: ['workflow', id],
    queryFn: () => (id ? workflowService.getWorkflow(id) : null),
    enabled: !!id,
  });
};
