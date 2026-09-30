import React, { useState } from 'react';
import { useDatasetDuplicates, useDatasetManagementMutations } from '../../hooks/useDatasetManagement';
import { DuplicateGroup } from '../../types/dataset_management';
import { Spinner } from '../../components/ui/Spinner';
import {
  Copy,
  CheckCircle2,
  GitMerge,
  EyeOff,
  Layers,
  ArrowRight,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { Button } from '../../components/ui/Button';

interface DuplicateResolverTabProps {
  datasetId: string;
}

export function DuplicateResolverTab({ datasetId }: DuplicateResolverTabProps) {
  const { data: duplicateGroups, isLoading, refetch } = useDatasetDuplicates(datasetId);
  const { mergeDuplicatesMutation } = useDatasetManagementMutations(datasetId);

  const [selectedGroup, setSelectedGroup] = useState<DuplicateGroup | null>(null);
  const [retainedId, setRetainedId] = useState<string>('');
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const groups = duplicateGroups || [];

  const handleSelectGroup = (g: DuplicateGroup) => {
    setSelectedGroup(g);
    if (g.records.length > 0) {
      setRetainedId(g.records[0].id);
    }
  };

  const handleMerge = async () => {
    if (!selectedGroup || !retainedId) return;
    const mergedIds = selectedGroup.records.map((r) => r.id).filter((id) => id !== retainedId);
    try {
      const res = await mergeDuplicatesMutation.mutateAsync({
        retainedRecordId: retainedId,
        mergedRecordIds: mergedIds,
      });
      setSuccessMsg(res.message);
      setSelectedGroup(null);
      refetch();
    } catch (err: any) {
      console.error(err);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-3">
        <Spinner size="lg" />
        <p className="text-sm font-medium text-slate-500">Scanning dataset for duplicate clusters...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-indigo-600 font-bold text-sm">
            <Copy className="w-4 h-4" />
            <span>Duplicate Detection & Resolution Center</span>
          </div>
          <h3 className="text-lg font-bold text-slate-900 mt-1">
            {groups.length > 0 ? `${groups.length} Duplicate Groups Detected` : 'Zero Duplicates Detected'}
          </h3>
          <p className="text-xs text-slate-500">
            Compare matching duplicate entities side by side, select the primary record to retain, and merge source links seamlessly.
          </p>
        </div>

        <button
          onClick={() => refetch()}
          className="text-xs font-semibold px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 shrink-0"
        >
          Rescan Duplicates
        </button>
      </div>

      {successMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs font-semibold text-emerald-800 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {groups.length === 0 ? (
        <div className="text-center p-12 bg-white rounded-xl border border-slate-200 space-y-2">
          <ShieldCheck className="w-10 h-10 text-emerald-500 mx-auto" />
          <h4 className="text-sm font-bold text-slate-900">Clean Uniqueness Profile</h4>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            All records in this dataset have distinct content fingerprints, URLs, and entity composite identifiers.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Groups List */}
          <div className="space-y-2">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Duplicate Clusters</span>
            <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
              {groups.map((g) => {
                const isSelected = selectedGroup?.group_id === g.group_id;
                return (
                  <div
                    key={g.group_id}
                    onClick={() => handleSelectGroup(g)}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                      isSelected
                        ? 'border-indigo-600 bg-indigo-50/70 shadow-sm'
                        : 'border-slate-200 bg-white hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900 truncate max-w-[160px]">
                        Match: {g.match_field}
                      </span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                        {g.record_count} records
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-500 truncate mt-1">
                      {g.match_value}
                    </div>
                    <div className="text-[10px] text-indigo-600 font-semibold mt-2">
                      Confidence: {(g.confidence * 100).toFixed(0)}% · Rule: {g.rule_type}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Side-by-Side Reviewer */}
          <div className="lg:col-span-2">
            {selectedGroup ? (
              <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">
                      Side-by-Side Cluster Review ({selectedGroup.records.length} records)
                    </h4>
                    <p className="text-xs text-slate-500">
                      Select which record should be retained as the primary winner. Other records will be merged into it with all source provenance links preserved.
                    </p>
                  </div>
                </div>

                {/* Record cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {selectedGroup.records.map((r, idx) => {
                    const isRetained = retainedId === r.id;
                    return (
                      <div
                        key={r.id}
                        onClick={() => setRetainedId(r.id)}
                        className={`p-4 rounded-xl border cursor-pointer transition-all relative ${
                          isRetained
                            ? 'border-emerald-600 bg-emerald-50/40 ring-2 ring-emerald-500/20'
                            : 'border-slate-200 hover:border-slate-300 bg-slate-50/50'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-[10px] font-bold text-slate-400 uppercase">
                            Record #{idx + 1}
                          </span>
                          {isRetained ? (
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-600 text-white flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3" />
                              Retain as Primary
                            </span>
                          ) : (
                            <span className="text-[10px] font-semibold text-slate-500 hover:text-slate-800">
                              Click to Retain
                            </span>
                          )}
                        </div>

                        <div className="space-y-1.5 text-xs">
                          {Object.entries(r.record_data).map(([k, v]) => (
                            <div key={k} className="flex justify-between gap-2 border-b border-slate-100 pb-1">
                              <span className="text-slate-400 font-medium text-[11px]">{k}:</span>
                              <span className="text-slate-800 font-semibold truncate max-w-[160px]" title={String(v)}>
                                {String(v || '-')}
                              </span>
                            </div>
                          ))}
                        </div>

                        <div className="mt-3 text-[11px] text-slate-500 flex items-center gap-1">
                          <ShieldCheck className="w-3.5 h-3.5 text-indigo-500" />
                          <span>{r.source_count || 1} verified source links</span>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Actions */}
                <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                  <Button
                    onClick={handleMerge}
                    disabled={mergeDuplicatesMutation.isPending || !retainedId}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs gap-1.5"
                  >
                    {mergeDuplicatesMutation.isPending ? <Spinner size="sm" /> : <GitMerge className="w-4 h-4" />}
                    Merge Selected Duplicates & Re-link Sources
                  </Button>
                </div>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center p-12 bg-slate-50 rounded-xl border border-dashed border-slate-200 text-center text-slate-500 text-xs">
                <Copy className="w-8 h-8 text-slate-400 mb-2" />
                <p>Select a duplicate cluster on the left to inspect records side-by-side.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
