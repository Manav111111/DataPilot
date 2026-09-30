import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { analysisService } from '../services/analysisService';
import { ReportCreateRequest } from '../types/analysis';

export function useAnalysisSessions(datasetId: string) {
  return useQuery({
    queryKey: ['analysisSessions', datasetId],
    queryFn: () => analysisService.listSessions(datasetId),
    enabled: !!datasetId,
  });
}

export function useAnalysisSession(datasetId: string, sessionId?: string) {
  return useQuery({
    queryKey: ['analysisSession', datasetId, sessionId],
    queryFn: () => analysisService.getSession(datasetId, sessionId!),
    enabled: !!datasetId && !!sessionId,
  });
}

export function useChatMutation(datasetId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ message, sessionId }: { message: string; sessionId?: string }) =>
      analysisService.chatWithDataset(datasetId, message, sessionId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['analysisSessions', datasetId] });
      queryClient.invalidateQueries({
        queryKey: ['analysisSession', datasetId, data.session_id],
      });
    },
  });
}

export function useAutoInsights(datasetId: string, enabled: boolean = false) {
  return useQuery({
    queryKey: ['autoInsights', datasetId],
    queryFn: () => analysisService.generateInsights(datasetId),
    enabled: !!datasetId && enabled,
    staleTime: 5 * 60 * 1000,
  });
}

export function useDatasetStatistics(datasetId: string, enabled: boolean = false) {
  return useQuery({
    queryKey: ['datasetStatistics', datasetId],
    queryFn: () => analysisService.generateStatistics(datasetId),
    enabled: !!datasetId && enabled,
    staleTime: 5 * 60 * 1000,
  });
}

export function useDatasetReports(datasetId: string) {
  return useQuery({
    queryKey: ['datasetReports', datasetId],
    queryFn: () => analysisService.listReports(datasetId),
    enabled: !!datasetId,
  });
}

export function useCreateReportMutation(datasetId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (req: ReportCreateRequest) => analysisService.createReport(datasetId, req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasetReports', datasetId] });
    },
  });
}

export function useDeleteSessionMutation(datasetId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) => analysisService.deleteSession(datasetId, sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analysisSessions', datasetId] });
    },
  });
}
