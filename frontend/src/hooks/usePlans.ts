import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { planService } from '../services/planService';
import {
  GeneratePlanPayload,
  UpdatePlanPayload,
  RegeneratePlanPayload,
} from '../types/plan';

export const useProjectPlans = (
  projectId?: string,
  params?: { page?: number; size?: number; status?: string }
) => {
  return useQuery({
    queryKey: ['project-plans', projectId, params],
    queryFn: () =>
      projectId ? planService.listProjectPlans(projectId, params) : null,
    enabled: !!projectId,
  });
};

export const usePlan = (planId?: string) => {
  return useQuery({
    queryKey: ['plan', planId],
    queryFn: () => (planId ? planService.getPlan(planId) : null),
    enabled: !!planId,
  });
};

export const useGeneratePlan = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      projectId,
      payload,
    }: {
      projectId: string;
      payload: GeneratePlanPayload;
    }) => planService.generatePlan(projectId, payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['project-plans', data.project_id] });
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
};

export const useUpdatePlan = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      planId,
      payload,
    }: {
      planId: string;
      payload: UpdatePlanPayload;
    }) => planService.updatePlan(planId, payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['plan', data.id] });
      queryClient.invalidateQueries({ queryKey: ['project-plans', data.project_id] });
    },
  });
};

export const useApprovePlan = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (planId: string) => planService.approvePlan(planId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['plan', data.id] });
      queryClient.invalidateQueries({ queryKey: ['project-plans', data.project_id] });
    },
  });
};

export const useRejectPlan = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (planId: string) => planService.rejectPlan(planId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['plan', data.id] });
      queryClient.invalidateQueries({ queryKey: ['project-plans', data.project_id] });
    },
  });
};

export const useRegeneratePlan = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      planId,
      payload,
    }: {
      planId: string;
      payload: RegeneratePlanPayload;
    }) => planService.regeneratePlan(planId, payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['plan', data.id] });
      queryClient.invalidateQueries({ queryKey: ['project-plans', data.project_id] });
    },
  });
};
