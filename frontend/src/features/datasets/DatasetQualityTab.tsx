import React from 'react';
import { useDatasetProfile } from '../../hooks/useDatasetManagement';
import { Spinner } from '../../components/ui/Spinner';
import {
  ShieldCheck,
  AlertTriangle,
  Sparkles,
  BarChart2,
  CheckCircle2,
  HelpCircle,
  TrendingUp,
  Info,
  Layers,
} from 'lucide-react';
import { Badge } from '../../components/ui/Badge';

interface DatasetQualityTabProps {
  datasetId: string;
}

export function DatasetQualityTab({ datasetId }: DatasetQualityTabProps) {
  const { data: profile, isLoading, refetch, isFetching } = useDatasetProfile(datasetId);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-3">
        <Spinner size="lg" />
        <p className="text-sm font-medium text-slate-500">Profiling dataset and analyzing quality dimensions...</p>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="text-center p-12 bg-white rounded-xl border border-slate-200">
        <AlertTriangle className="w-10 h-10 text-amber-500 mx-auto mb-3" />
        <p className="text-sm text-slate-600 font-semibold">No quality report available for this dataset.</p>
        <button
          onClick={() => refetch()}
          className="mt-3 px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-semibold hover:bg-indigo-700"
        >
          Generate Quality Report
        </button>
      </div>
    );
  }

  const { quality, overview, columns } = profile;
  const { dimension_scores, dimensions, overall_score } = quality;

  const getScoreColor = (score: number) => {
    if (score >= 85) return 'text-emerald-600 bg-emerald-50 border-emerald-200';
    if (score >= 65) return 'text-amber-600 bg-amber-50 border-amber-200';
    return 'text-rose-600 bg-rose-50 border-rose-200';
  };

  const getProgressColor = (score: number) => {
    if (score >= 85) return 'bg-emerald-500';
    if (score >= 65) return 'bg-amber-500';
    return 'bg-rose-500';
  };

  return (
    <div className="space-y-6">
      {/* Overall Score Header Banner */}
      <div className="bg-gradient-to-r from-indigo-900 via-indigo-800 to-slate-900 rounded-2xl p-6 text-white shadow-sm flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold tracking-wider bg-indigo-500/30 text-indigo-200 uppercase border border-indigo-400/30">
              Scoring Model {quality.scoring_method_version}
            </span>
            <span className="text-xs text-slate-400">
              Profiled {new Date(profile.profiled_at).toLocaleTimeString()}
            </span>
          </div>
          <h3 className="text-xl font-bold tracking-tight">Dataset Quality & Health Score</h3>
          <p className="text-xs text-indigo-200/80 max-w-xl">
            Calculated across 5 technical quality dimensions (Completeness, Validity, Uniqueness, Consistency, and Provenance). This score measures technical structural integrity and source traceability.
          </p>
        </div>

        <div className="flex items-center gap-4 bg-white/10 backdrop-blur-md rounded-xl p-4 border border-white/10">
          <div className="text-right">
            <span className="text-3xl font-extrabold text-white">{overall_score.toFixed(1)}</span>
            <span className="text-indigo-200 text-sm font-semibold"> / 100</span>
            <div className="text-[11px] font-medium text-indigo-300">Overall Quality</div>
          </div>
          <div className={`w-12 h-12 rounded-full border-4 flex items-center justify-center font-bold text-sm ${
            overall_score >= 85 ? 'border-emerald-400 text-emerald-300' : (overall_score >= 65 ? 'border-amber-400 text-amber-300' : 'border-rose-400 text-rose-300')
          }`}>
            {overall_score >= 85 ? 'A' : (overall_score >= 65 ? 'B' : 'C')}
          </div>
        </div>
      </div>

      {/* 5 Quality Dimension Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(dimensions).map(([dimKey, dim]) => {
          const score = dim.score;
          return (
            <div
              key={dimKey}
              className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm space-y-3 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                    {dimKey}
                  </span>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${getScoreColor(score)}`}>
                    {score.toFixed(1)}%
                  </span>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-slate-100 rounded-full h-1.5 mt-2 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${getProgressColor(score)}`}
                    style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
                  />
                </div>

                <p className="text-xs font-semibold text-slate-800 mt-2.5">{dim.explanation}</p>
                <p className="text-[11px] text-slate-500 mt-1 italic leading-snug">{dim.rule}</p>
              </div>

              {dim.suggestions && dim.suggestions.length > 0 && (
                <div className="pt-2 border-t border-slate-100 mt-2">
                  <div className="flex items-center gap-1 text-[11px] font-bold text-indigo-700">
                    <Sparkles className="w-3 h-3" />
                    <span>Improvement Action</span>
                  </div>
                  <ul className="text-[11px] text-slate-600 mt-1 space-y-1 list-disc list-inside">
                    {dim.suggestions.map((s, idx) => (
                      <li key={idx}>{s}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Column Level Profiling Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h4 className="text-sm font-bold text-slate-900">Column Profiling & Value Distributions</h4>
            <p className="text-xs text-slate-500">
              Detailed breakdown of non-null counts, distinct cardinality, and value summaries across {columns.length} columns.
            </p>
          </div>
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 flex items-center gap-1.5"
          >
            {isFetching ? <Spinner size="sm" /> : <Layers className="w-3.5 h-3.5 text-slate-500" />}
            Refresh Profile
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-[11px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Column Name</th>
                <th className="py-3 px-4">Inferred Type</th>
                <th className="py-3 px-4">Populated %</th>
                <th className="py-3 px-4">Missing / Null</th>
                <th className="py-3 px-4">Unique Values</th>
                <th className="py-3 px-4">Stats & Top Values</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {columns.map((col) => {
                const populatedPct = 100 - col.missing_percentage;
                return (
                  <tr key={col.column_name} className="hover:bg-slate-50/70">
                    <td className="py-3 px-4 font-semibold text-slate-900">
                      <div>{col.column_name}</div>
                      <div className="text-[11px] text-slate-400 font-normal">{col.display_label}</div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
                        {col.inferred_type}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${getProgressColor(populatedPct)}`}
                            style={{ width: `${populatedPct}%` }}
                          />
                        </div>
                        <span className="text-[11px] font-semibold text-slate-700">
                          {populatedPct.toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-slate-600">
                      {col.null_count > 0 ? (
                        <span className="text-amber-600 font-semibold">{col.null_count} nulls</span>
                      ) : (
                        <span className="text-emerald-600 font-medium">0 (Full)</span>
                      )}
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-700">
                      {col.unique_count} distinct
                    </td>
                    <td className="py-3 px-4">
                      {col.inferred_type === 'number' && col.min_value !== null ? (
                        <div className="text-[11px] text-slate-600">
                          <span>Min: <b className="text-slate-800">{col.min_value}</b></span> ·{' '}
                          <span>Max: <b className="text-slate-800">{col.max_value}</b></span> ·{' '}
                          <span>Mean: <b className="text-slate-800">{col.mean}</b></span>
                        </div>
                      ) : col.top_values && col.top_values.length > 0 ? (
                        <div className="flex flex-wrap gap-1 max-w-xs">
                          {col.top_values.slice(0, 3).map((tv, idx) => (
                            <span
                              key={idx}
                              className="text-[10px] bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded border border-slate-200 truncate max-w-[120px]"
                              title={`${tv.value} (${tv.count})`}
                            >
                              {tv.value} ({tv.count})
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-slate-400 italic text-[11px]">No sample data</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
