import React from 'react';
import { useDatasetOverview } from '../../hooks/useCollection';
import { formatNumber } from '../../lib/utils';
import { Database, CheckCircle2, AlertTriangle, XCircle, RotateCcw, Globe } from 'lucide-react';

interface DatasetOverviewCardProps {
  datasetId: string;
}

export function DatasetOverviewCard({ datasetId }: DatasetOverviewCardProps) {
  const { data: stats, isLoading } = useDatasetOverview(datasetId);

  if (isLoading || !stats) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3 animate-pulse">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="h-20 rounded-xl bg-slate-100" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
      <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-card space-y-1">
        <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium">
          <Database className="w-3.5 h-3.5 text-indigo-500" />
          Total Records
        </div>
        <span className="text-xl font-bold text-slate-900 block">
          {formatNumber(stats.total_records)}
        </span>
      </div>

      <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-card space-y-1">
        <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
          Valid
        </div>
        <span className="text-xl font-bold text-emerald-600 block">
          {formatNumber(stats.valid_records)}
        </span>
      </div>

      <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-card space-y-1">
        <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
          With Warnings
        </div>
        <span className="text-xl font-bold text-amber-600 block">
          {formatNumber(stats.records_with_warnings)}
        </span>
      </div>

      <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-card space-y-1">
        <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium">
          <XCircle className="w-3.5 h-3.5 text-rose-500" />
          Rejected
        </div>
        <span className="text-xl font-bold text-rose-600 block">
          {formatNumber(stats.rejected_records)}
        </span>
      </div>

      <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-card space-y-1">
        <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium">
          <RotateCcw className="w-3.5 h-3.5 text-purple-500" />
          Duplicates Merged
        </div>
        <span className="text-xl font-bold text-purple-600 block">
          {formatNumber(stats.duplicate_count)}
        </span>
      </div>

      <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-card space-y-1">
        <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium">
          <Globe className="w-3.5 h-3.5 text-blue-500" />
          Sources Crawled
        </div>
        <span className="text-xl font-bold text-blue-600 block">
          {formatNumber(stats.source_count)}
        </span>
      </div>
    </div>
  );
}
