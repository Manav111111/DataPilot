import { apiClient } from '../lib/axios';
import {
  CollectionPlan,
  GeneratePlanPayload,
  UpdatePlanPayload,
  RegeneratePlanPayload,
} from '../types/plan';
import { PaginatedResponse } from '../types/api';

export const planService = {
  async generatePlan(
    projectId: string,
    payload: GeneratePlanPayload
  ): Promise<CollectionPlan> {
    const res = await apiClient.post<CollectionPlan>(
      `/projects/${projectId}/plans/generate`,
      payload
    );
    return res.data;
  },

  async getPlan(planId: string): Promise<CollectionPlan> {
    const res = await apiClient.get<CollectionPlan>(`/plans/${planId}`);
    return res.data;
  },

  async listProjectPlans(
    projectId: string,
    params?: { page?: number; size?: number; status?: string }
  ): Promise<PaginatedResponse<CollectionPlan>> {
    const res = await apiClient.get<PaginatedResponse<CollectionPlan>>(
      `/projects/${projectId}/plans`,
      { params }
    );
    return res.data;
  },

  async updatePlan(
    planId: string,
    payload: UpdatePlanPayload
  ): Promise<CollectionPlan> {
    const res = await apiClient.patch<CollectionPlan>(`/plans/${planId}`, payload);
    return res.data;
  },

  async approvePlan(planId: string): Promise<CollectionPlan> {
    const res = await apiClient.post<CollectionPlan>(`/plans/${planId}/approve`);
    return res.data;
  },

  async rejectPlan(planId: string): Promise<CollectionPlan> {
    const res = await apiClient.post<CollectionPlan>(`/plans/${planId}/reject`);
    return res.data;
  },

  async regeneratePlan(
    planId: string,
    payload: RegeneratePlanPayload
  ): Promise<CollectionPlan> {
    const res = await apiClient.post<CollectionPlan>(
      `/plans/${planId}/regenerate`,
      payload
    );
    return res.data;
  },
};
