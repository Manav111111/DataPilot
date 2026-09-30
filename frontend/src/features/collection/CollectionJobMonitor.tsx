import React from 'react';
import {
  useCollectionJob,
  useJobEvents,
  useCancelCollectionJob,
  useRetryCollectionJob,
} from '../../hooks/useCollection';
import { CollectionStage, CollectionJobStatus } from '../../types/collection';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Button } from '../../components/ui/Button';
import { Spinner } from '../../components/ui/Spinner';
import { useToast } from '../../components/ui/Toast';
import { formatDate, formatNumber } from '../../lib/utils';
import {
  Search,
  Globe,
  Sparkles,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCcw,
  StopCircle,
  ArrowRight,
  Database,
  Layers,
  Clock,
  Terminal,
  FileCheck,
} from 'lucide-react';

interface CollectionJobMonitorProps {
  jobId: string;
  onViewDataset?: (datasetId: string) => void;
  onClose?: () => void;
}

const STAGES: { key: CollectionStage; label: string; icon: any }[] = [
  { key: 'initializing', label: '1. Initializing', icon: Sparkles },
  { key: 'searching', label: '2. Searching Sources', icon: Search },
  { key: 'extracting', label: '3. Extracting Pages', icon: Globe },
  { key: 'structuring', label: '4. Structuring Records', icon: Layers },
  { key: 'validating', label: '5. Validating Schema', icon: FileCheck },
  { key: 'deduplicating', label: '6. Deduplicating', icon: RotateCcw },
  { key: 'saving', label: '7. Saving Results', icon: Database },
  { key: 'completed', label: '8. Completed', icon: CheckCircle2 },
];

export function CollectionJobMonitor({
  jobId,
  onViewDataset,
  onClose,
}: CollectionJobMonitorProps) {
  const { data: job, isLoading, error } = useCollectionJob(jobId);
  const { data: eventsData } = useJobEvents(jobId);
  const { mutateAsync: cancelMutation, isPending: isCancelling } = useCancelCollectionJob();
  const { mutateAsync: retryMutation, isPending: isRetrying } = useRetryCollectionJob();
  const { success, error: showError } = useToast();

  if (isLoading) {
    return (
      <div className="py-20 flex flex-col items-center justify-center space-y-3">
        <Spinner size="lg" />
        <p className="text-xs text-slate-500">Connecting to collection worker...</p>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="p-6 rounded-xl bg-red-50 border border-red-200 text-center space-y-2">
        <AlertTriangle className="w-8 h-8 text-red-500 mx-auto" />
        <h4 className="text-sm font-bold text-red-900">Failed to load collection job</h4>
        <p className="text-xs text-red-600">The job may have been deleted or is inaccessible.</p>
      </div>
    );
  }

  const isTerminal = ['completed', 'completed_with_errors', 'failed', 'cancelled'].includes(
    job.status
  );
  const isRunning = job.status === 'running' || job.status === 'queued';
  const stageIndex = STAGES.findIndex((s) => s.key === job.current_stage);

  const handleCancel = async () => {
    try {
      await cancelMutation(job.id);
      success('Collection job cancelled.');
    } catch (err: any) {
      showError(err.response?.data?.detail || 'Failed to cancel job');
    }
  };

  const handleRetry = async () => {
    try {
      await retryMutation(job.id);
      success('Collection job retry initiated.');
    } catch (err: any) {
      showError(err.response?.data?.detail || 'Failed to retry job');
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-card space-y-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <h3 className="text-lg font-bold text-slate-900">Data Collection Job</h3>
              <StatusBadge status={job.status} />
            </div>
            <p className="text-xs text-slate-500">
              Job ID: <code className="bg-slate-100 px-1.5 py-0.5 rounded text-slate-700">{job.id}</code>
              <span className="mx-2">•</span>
              Started {job.started_at ? formatDate(job.started_at) : formatDate(job.created_at)}
            </p>
          </div>

          <div className="flex items-center gap-2">
            {isRunning && (
              <Button
                variant="destructive"
                size="sm"
                onClick={handleCancel}
                disabled={isCancelling}
                className="gap-1.5"
              >
                <StopCircle className="w-4 h-4" />
                Cancel Job
              </Button>
            )}

            {(job.status === 'failed' || job.status === 'cancelled' || job.status === 'completed_with_errors') && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleRetry}
                disabled={isRetrying}
                className="gap-1.5"
              >
                <RotateCcw className="w-4 h-4" />
                Retry Job {job.retry_count > 0 ? `(#${job.retry_count + 1})` : ''}
              </Button>
            )}

            {job.dataset_id && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => onViewDataset?.(job.dataset_id)}
                className="gap-1.5 bg-indigo-600 hover:bg-indigo-700"
              >
                <Database className="w-4 h-4" />
                View Dataset Records
                <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-1.5 pt-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-slate-700 flex items-center gap-1.5">
              {isRunning && <Spinner size="sm" />}
              Stage: {STAGES.find((s) => s.key === job.current_stage)?.label || job.current_stage}
            </span>
            <span className="font-bold text-indigo-600">{job.progress_percentage}%</span>
          </div>
          <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                job.status === 'failed'
                  ? 'bg-red-500'
                  : job.status === 'cancelled'
                  ? 'bg-amber-500'
                  : 'bg-gradient-to-r from-indigo-500 to-emerald-500'
              }`}
              style={{ width: `${Math.max(job.progress_percentage, 4)}%` }}
            />
          </div>
        </div>

        {/* Stage Timeline Steps */}
        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-8 gap-2 pt-3 border-t border-slate-100">
          {STAGES.map((st, idx) => {
            const isDone = isTerminal
              ? job.status === 'completed' || idx < stageIndex
              : idx < stageIndex;
            const isCurrent = job.current_stage === st.key && isRunning;
            const isPending = idx > stageIndex;

            return (
              <div
                key={st.key}
                className={`p-2.5 rounded-xl border text-center transition-all ${
                  isCurrent
                    ? 'bg-indigo-50/80 border-indigo-300 shadow-sm'
                    : isDone
                    ? 'bg-emerald-50/60 border-emerald-200 text-emerald-900'
                    : 'bg-slate-50/60 border-slate-100 text-slate-400'
                }`}
              >
                <div className="flex justify-center mb-1">
                  {isCurrent ? (
                    <Spinner size="sm" />
                  ) : isDone ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : (
                    <st.icon className="w-4 h-4 text-slate-300" />
                  )}
                </div>
                <div className="text-[11px] font-bold truncate">{st.label}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Error callout if present */}
      {job.error_message && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-xs font-bold text-red-900">Job Execution Notice</h4>
            <p className="text-xs text-red-700">{job.error_message}</p>
          </div>
        </div>
      )}

      {/* Real-Time Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm space-y-1">
          <span className="text-xs text-slate-400 block font-medium">Search Queries</span>
          <div className="flex items-baseline gap-1">
            <span className="text-xl font-bold text-slate-900">{job.completed_queries}</span>
            <span className="text-xs text-slate-400">/ {job.total_queries} queries</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm space-y-1">
          <span className="text-xs text-slate-400 block font-medium">Sources Crawled</span>
          <div className="flex items-baseline gap-1">
            <span className="text-xl font-bold text-blue-600">{job.processed_sources}</span>
            <span className="text-xs text-slate-400">/ {job.total_sources} found</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm space-y-1">
          <span className="text-xs text-slate-400 block font-medium">Raw Extracted</span>
          <span className="text-xl font-bold text-indigo-600">
            {formatNumber(job.records_extracted)}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm space-y-1">
          <span className="text-xs text-slate-400 block font-medium">Saved Records</span>
          <span className="text-xl font-bold text-emerald-600">
            {formatNumber(job.records_saved)}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm space-y-1">
          <span className="text-xs text-slate-400 block font-medium">Rejected / Errors</span>
          <span className="text-xl font-bold text-rose-600">
            {formatNumber(job.records_rejected)}
          </span>
        </div>
      </div>

      {/* Activity Log Events Stream */}
      <Card>
        <CardHeader className="pb-3 border-b border-slate-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-slate-500" />
              <CardTitle className="text-sm font-bold text-slate-900">
                Activity Stream & Audit Log
              </CardTitle>
            </div>
            <span className="text-xs text-slate-400">
              {eventsData?.items?.length || 0} events recorded
            </span>
          </div>
        </CardHeader>
        <CardContent className="pt-3">
          <div className="max-h-72 overflow-y-auto space-y-2 font-mono text-xs pr-2">
            {!eventsData?.items || eventsData.items.length === 0 ? (
              <p className="text-slate-400 italic py-4 text-center">No log events recorded yet.</p>
            ) : (
              eventsData.items.map((ev) => (
                <div
                  key={ev.id}
                  className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 flex items-start gap-2.5"
                >
                  <span className="text-slate-400 text-[10px] whitespace-nowrap pt-0.5">
                    {new Date(ev.created_at).toLocaleTimeString()}
                  </span>
                  <div className="space-y-0.5 min-w-0 flex-1">
                    <span
                      className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-bold mr-2 uppercase ${
                        ev.event_type === 'stage_change'
                          ? 'bg-indigo-100 text-indigo-700'
                          : ev.event_type === 'error'
                          ? 'bg-red-100 text-red-700'
                          : ev.event_type === 'completed'
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-slate-200 text-slate-700'
                      }`}
                    >
                      {ev.event_type}
                    </span>
                    <span className="text-slate-700 break-words">{ev.message}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
