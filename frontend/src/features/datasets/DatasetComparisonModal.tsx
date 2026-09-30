import React, { useState } from 'react';
import { useDatasets } from '../../hooks/useDatasets';
import { datasetManagementService } from '../../services/datasetManagementService';
import { DatasetCompareResponse } from '../../types/dataset_management';
import { Spinner } from '../../components/ui/Spinner';
import { Button } from '../../components/ui/Button';
import { GitCompare, ArrowRight, CheckCircle2, AlertTriangle, Layers, X } from 'lucide-react';

interface DatasetComparisonModalProps {
  initialDatasetId?: string;
  isOpen: boolean;
  onClose: () => void;
}

export function DatasetComparisonModal({ initialDatasetId, isOpen, onClose }: DatasetComparisonModalProps) {
  const { data: datasetsData } = useDatasets({});
  const allDatasets = datasetsData?.items || [];

  const [datasetAId, setDatasetAId] = useState<string>(initialDatasetId || allDatasets[0]?.id || '');
  const [datasetBId, setDatasetBId] = useState<string>(allDatasets[1]?.id || allDatasets[0]?.id || '');
  const [matchingKey, setMatchingKey] = useState<string>('');
  const [result, setResult] = useState<DatasetCompareResponse | null>(null);
  const [isComparing, setIsComparing] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleCompare = async () => {
    if (!datasetAId || !datasetBId) return;
    setIsComparing(true);
    try {
      const res = await datasetManagementService.compareDatasets(
        datasetAId,
        datasetBId,
        matchingKey || undefined
      );
      setResult(res);
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsComparing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="px-6 py-5 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2 text-indigo-600 font-bold text-sm">
            <GitCompare className="w-5 h-5" />
            <span>Dataset Comparison & Drift Inspector</span>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Dataset Pickers */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Dataset A (Baseline)</label>
              <select
                value={datasetAId}
                onChange={(e) => setDatasetAId(e.target.value)}
                className="w-full text-xs border border-slate-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-indigo-500"
              >
                {allDatasets.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.row_count} records)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Dataset B (Target / Comparison)</label>
              <select
                value={datasetBId}
                onChange={(e) => setDatasetBId(e.target.value)}
                className="w-full text-xs border border-slate-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-indigo-500"
              >
                {allDatasets.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.row_count} records)
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex justify-end">
            <Button
              onClick={handleCompare}
              disabled={isComparing || !datasetAId || !datasetBId}
              size="sm"
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs gap-1.5"
            >
              {isComparing ? <Spinner size="sm" /> : <GitCompare className="w-4 h-4" />}
              Compare Datasets
            </Button>
          </div>

          {/* Comparison Results */}
          {result && (
            <div className="space-y-6 pt-4 border-t border-slate-200">
              {/* Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <div className="text-[11px] font-semibold text-slate-500">Record Delta</div>
                  <div className="text-lg font-bold text-slate-900 mt-0.5">
                    {result.comparison.record_count_delta >= 0 ? `+${result.comparison.record_count_delta}` : result.comparison.record_count_delta}
                  </div>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <div className="text-[11px] font-semibold text-slate-500">Quality Score Delta</div>
                  <div className="text-lg font-bold text-slate-900 mt-0.5">
                    {result.comparison.quality_score_delta >= 0 ? `+${result.comparison.quality_score_delta}` : result.comparison.quality_score_delta}%
                  </div>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <div className="text-[11px] font-semibold text-slate-500">Common Records</div>
                  <div className="text-lg font-bold text-indigo-600 mt-0.5">
                    {result.comparison.common_records_count}
                  </div>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <div className="text-[11px] font-semibold text-slate-500">Schema Similarity</div>
                  <div className="text-lg font-bold text-emerald-600 mt-0.5">
                    {result.schema_diff.similarity_score}%
                  </div>
                </div>
              </div>

              {/* Schema Diff */}
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 space-y-3 text-xs">
                <div className="font-bold text-slate-900">Schema Field Breakdown</div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div>
                    <span className="text-[11px] font-semibold text-emerald-700">Common Columns ({result.schema_diff.common_columns.length}):</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {result.schema_diff.common_columns.map((c) => (
                        <span key={c} className="px-2 py-0.5 rounded bg-white text-slate-700 border border-slate-200 text-[10px]">
                          {c}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div>
                    <span className="text-[11px] font-semibold text-amber-700">Only in Dataset A ({result.schema_diff.dataset_a_only_columns.length}):</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {result.schema_diff.dataset_a_only_columns.length === 0 ? (
                        <span className="text-slate-400 italic text-[11px]">None</span>
                      ) : (
                        result.schema_diff.dataset_a_only_columns.map((c) => (
                          <span key={c} className="px-2 py-0.5 rounded bg-white text-slate-700 border border-slate-200 text-[10px]">
                            {c}
                          </span>
                        ))
                      )}
                    </div>
                  </div>

                  <div>
                    <span className="text-[11px] font-semibold text-indigo-700">Only in Dataset B ({result.schema_diff.dataset_b_only_columns.length}):</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {result.schema_diff.dataset_b_only_columns.length === 0 ? (
                        <span className="text-slate-400 italic text-[11px]">None</span>
                      ) : (
                        result.schema_diff.dataset_b_only_columns.map((c) => (
                          <span key={c} className="px-2 py-0.5 rounded bg-white text-slate-700 border border-slate-200 text-[10px]">
                            {c}
                          </span>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex justify-end rounded-b-2xl">
          <button
            onClick={onClose}
            className="text-xs font-semibold px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-600"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
