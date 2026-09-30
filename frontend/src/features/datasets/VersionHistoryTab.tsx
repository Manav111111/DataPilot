import React, { useState } from 'react';
import { useDatasetVersions, useDatasetManagementMutations } from '../../hooks/useDatasetManagement';
import { Spinner } from '../../components/ui/Spinner';
import { History, RotateCcw, CheckCircle2, ShieldCheck, Layers } from 'lucide-react';
import { Button } from '../../components/ui/Button';

interface VersionHistoryTabProps {
  datasetId: string;
}

export function VersionHistoryTab({ datasetId }: VersionHistoryTabProps) {
  const { data: versions, isLoading, refetch } = useDatasetVersions(datasetId);
  const { restoreVersionMutation } = useDatasetManagementMutations(datasetId);

  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleRestore = async (versionId: string) => {
    try {
      const res = await restoreVersionMutation.mutateAsync(versionId);
      setSuccessMsg(res.message);
      setSelectedVersionId(null);
      refetch();
    } catch (err: any) {
      console.error(err);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-3">
        <Spinner size="lg" />
        <p className="text-sm font-medium text-slate-500">Loading dataset version history...</p>
      </div>
    );
  }

  const verList = versions || [];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-indigo-600 font-bold text-sm">
            <History className="w-4 h-4" />
            <span>Dataset Versioning & Rollback Ledger</span>
          </div>
          <h3 className="text-lg font-bold text-slate-900 mt-1">Audit Trail & Safe Version Restoration</h3>
          <p className="text-xs text-slate-500">
            Immutable snapshots captured automatically upon cleaning, column transforms, and duplicate merges.
          </p>
        </div>

        <button
          onClick={() => refetch()}
          className="text-xs font-semibold px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700"
        >
          Refresh Versions
        </button>
      </div>

      {successMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs font-semibold text-emerald-800 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {verList.length === 0 ? (
        <div className="text-center p-12 bg-white rounded-xl border border-slate-200 space-y-2">
          <Layers className="w-10 h-10 text-slate-400 mx-auto" />
          <h4 className="text-sm font-bold text-slate-900">No Prior Version Snapshots</h4>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Version snapshots will be automatically created whenever you clean, transform, or merge records.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {verList.map((ver, idx) => {
            const isLatest = idx === 0;
            return (
              <div
                key={ver.id}
                className={`p-5 rounded-xl border transition-all bg-white flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 ${
                  isLatest ? 'border-indigo-200 ring-1 ring-indigo-500/20' : 'border-slate-200'
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-extrabold text-sm text-slate-900">Version #{ver.version_number}</span>
                    {isLatest && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                        Current Active State
                      </span>
                    )}
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600 uppercase">
                      {ver.change_type}
                    </span>
                  </div>
                  <p className="text-xs font-medium text-slate-700">{ver.change_summary || 'Manual snapshot'}</p>
                  <div className="text-[11px] text-slate-400">
                    <span>{ver.record_count} records</span> ·{' '}
                    <span>{new Date(ver.created_at).toLocaleString()}</span>
                  </div>
                </div>

                {!isLatest && (
                  <Button
                    onClick={() => handleRestore(ver.id)}
                    disabled={restoreVersionMutation.isPending}
                    variant="outline"
                    size="sm"
                    className="text-xs font-semibold text-slate-700 hover:text-indigo-600 hover:border-indigo-200 shrink-0 gap-1.5"
                  >
                    {restoreVersionMutation.isPending && selectedVersionId === ver.id ? (
                      <Spinner size="sm" />
                    ) : (
                      <RotateCcw className="w-3.5 h-3.5" />
                    )}
                    Restore This Version
                  </Button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
