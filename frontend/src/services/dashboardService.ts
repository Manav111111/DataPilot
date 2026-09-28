import { apiClient } from '../lib/axios';
import { DashboardStats } from '../types/api';

export const dashboardService = {
  async getStats(): Promise<DashboardStats> {
    const res = await apiClient.get<DashboardStats>('/dashboard/stats');
    return res.data;
  },
};
