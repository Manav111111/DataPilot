import React from 'react';
import { Link } from 'react-router-dom';
import { Dataset } from '../../types/dataset';
import { StatusBadge } from '../../components/common/StatusBadge';
import { formatDate, formatNumber } from '../../lib/utils';
import { Database, ArrowRight } from 'lucide-react';

interface RecentDatasetsListProps {
  datasets: Dataset[];
  onCreateNew: () => void;
}

export function RecentDatasetsList({
  datasets,
  onCreateNew,
}: RecentDatasetsListProps) {
  if (!datasets || datasets.length === 0) {
    return (
      <div className="p-6 text-center text-xs text-slate-500">
        <Database className="w-8 h-8 text-slate-300 mx-auto mb-2" />
        <p className="font-medium text-slate-700 mb-1">No datasets registered yet</p>
        <p className="text-slate-400 mb-3">Datasets store cleaned tables and schema outputs.</p>
        <button
          onClick={onCreateNew}
          className="text-indigo-600 font-semibold hover:underline"
        >
          + Create First Dataset
        </button>
      </div>
    );
  }

  return (
    <div className="divide-y divide-slate-100">
      {datasets.map((d) => (
        <Link
          key={d.id}
          to="/datasets"
          className="flex items-center justify-between p-3.5 hover:bg-slate-50/80 transition-colors group"
        >
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600 flex-shrink-0">
              <Database className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <p className="text-xs sm:text-sm font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors truncate">
                {d.name}
              </p>
              <p className="text-[11px] text-slate-400">
                {formatNumber(d.row_count)} rows • {formatDate(d.created_at)}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <StatusBadge status={d.status} />
            <ArrowRight className="w-3.5 h-3.5 text-slate-300 group-hover:text-indigo-500 group-hover:translate-x-0.5 transition-all" />
          </div>
        </Link>
      ))}
    </div>
  );
}
