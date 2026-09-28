import React from 'react';
import { Dataset } from '../../types/dataset';
import { StatusBadge } from '../../components/common/StatusBadge';
import { formatDate, formatNumber } from '../../lib/utils';
import { Eye, Edit2, Trash2, Database } from 'lucide-react';

interface DatasetTableProps {
  datasets: Dataset[];
  onView: (dataset: Dataset) => void;
  onEdit: (dataset: Dataset) => void;
  onDelete: (dataset: Dataset) => void;
}

export function DatasetTable({
  datasets,
  onView,
  onEdit,
  onDelete,
}: DatasetTableProps) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200/80 bg-white shadow-card">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-slate-100 bg-slate-50/75 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            <th className="py-3.5 px-4 sm:px-6">Dataset Name</th>
            <th className="py-3.5 px-4">Project</th>
            <th className="py-3.5 px-4">Status</th>
            <th className="py-3.5 px-4">Rows</th>
            <th className="py-3.5 px-4">Created</th>
            <th className="py-3.5 px-4 sm:px-6 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 text-xs sm:text-sm text-slate-700">
          {datasets.map((d) => (
            <tr
              key={d.id}
              className="hover:bg-slate-50/60 transition-colors group cursor-pointer"
              onClick={() => onView(d)}
            >
              <td className="py-3.5 px-4 sm:px-6 font-medium text-slate-900">
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-indigo-500 flex-shrink-0" />
                  <div>
                    <div className="font-semibold text-slate-900">{d.name}</div>
                    {d.description && (
                      <p className="text-xs text-slate-400 truncate max-w-xs">
                        {d.description}
                      </p>
                    )}
                  </div>
                </div>
              </td>
              <td className="py-3.5 px-4 text-slate-600 font-medium">
                {d.project_name || 'Project'}
              </td>
              <td className="py-3.5 px-4">
                <StatusBadge status={d.status} />
              </td>
              <td className="py-3.5 px-4 font-mono font-medium text-slate-900">
                {formatNumber(d.row_count)}
              </td>
              <td className="py-3.5 px-4 text-slate-500 text-xs">
                {formatDate(d.created_at)}
              </td>
              <td
                className="py-3.5 px-4 sm:px-6 text-right space-x-1"
                onClick={(e) => e.stopPropagation()}
              >
                <button
                  onClick={() => onView(d)}
                  title="View Details"
                  className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
                >
                  <Eye className="w-4 h-4" />
                </button>
                <button
                  onClick={() => onEdit(d)}
                  title="Edit Dataset"
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => onDelete(d)}
                  title="Delete Dataset"
                  className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
