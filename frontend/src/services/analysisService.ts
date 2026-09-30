import { apiClient as api } from '../lib/axios';
import {
  ChatQueryResponse,
  AnalysisSession,
  AutoInsightsResponse,
  StatisticalAnalysisResponse,
  ReportCreateRequest,
  AnalysisReport,
} from '../types/analysis';

export const analysisService = {
  // Chat
  async chatWithDataset(
    datasetId: string,
    message: string,
    sessionId?: string
  ): Promise<ChatQueryResponse> {
    const res = await api.post<ChatQueryResponse>(`/datasets/${datasetId}/analysis/chat`, {
      message,
      session_id: sessionId,
    });
    return res.data;
  },

  async listSessions(datasetId: string): Promise<AnalysisSession[]> {
    const res = await api.get<AnalysisSession[]>(`/datasets/${datasetId}/analysis/sessions`);
    return res.data;
  },

  async getSession(datasetId: string, sessionId: string): Promise<AnalysisSession> {
    const res = await api.get<AnalysisSession>(
      `/datasets/${datasetId}/analysis/sessions/${sessionId}`
    );
    return res.data;
  },

  async deleteSession(datasetId: string, sessionId: string): Promise<{ message: string }> {
    const res = await api.delete<{ message: string }>(
      `/datasets/${datasetId}/analysis/sessions/${sessionId}`
    );
    return res.data;
  },

  // Auto Insights
  async generateInsights(datasetId: string): Promise<AutoInsightsResponse> {
    const res = await api.post<AutoInsightsResponse>(
      `/datasets/${datasetId}/analysis/insights`
    );
    return res.data;
  },

  // Statistical Analysis
  async generateStatistics(datasetId: string): Promise<StatisticalAnalysisResponse> {
    const res = await api.post<StatisticalAnalysisResponse>(
      `/datasets/${datasetId}/analysis/statistics`
    );
    return res.data;
  },

  // Reports
  async createReport(datasetId: string, req: ReportCreateRequest): Promise<AnalysisReport> {
    const res = await api.post<AnalysisReport>(
      `/datasets/${datasetId}/analysis/reports`,
      req
    );
    return res.data;
  },

  async listReports(datasetId: string): Promise<AnalysisReport[]> {
    const res = await api.get<AnalysisReport[]>(`/datasets/${datasetId}/analysis/reports`);
    return res.data;
  },

  async downloadReport(reportId: string, title: string): Promise<void> {
    const res = await api.get(`/analysis/reports/${reportId}/download`, {
      responseType: 'blob',
    });
    const blob = new Blob([res.data], { type: 'text/html' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${title.toLowerCase().replace(/\s+/g, '_')}.html`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};
