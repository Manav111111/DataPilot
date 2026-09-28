import { apiClient } from '../lib/axios';
import { Project, CreateProjectPayload, UpdateProjectPayload } from '../types/project';
import { PaginatedResponse } from '../types/api';

export const projectService = {
  async getProjects(params?: {
    page?: number;
    size?: number;
    search?: string;
    status?: string;
  }): Promise<PaginatedResponse<Project>> {
    const res = await apiClient.get<PaginatedResponse<Project>>('/projects', { params });
    return res.data;
  },

  async getProject(id: string): Promise<Project> {
    const res = await apiClient.get<Project>(`/projects/${id}`);
    return res.data;
  },

  async createProject(data: CreateProjectPayload): Promise<Project> {
    const res = await apiClient.post<Project>('/projects', data);
    return res.data;
  },

  async updateProject(id: string, data: UpdateProjectPayload): Promise<Project> {
    const res = await apiClient.patch<Project>(`/projects/${id}`, data);
    return res.data;
  },

  async deleteProject(id: string): Promise<void> {
    await apiClient.delete(`/projects/${id}`);
  },
};
