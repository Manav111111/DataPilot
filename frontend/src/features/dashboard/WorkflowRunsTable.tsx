import React from 'react';
import { WorkflowRun } from '../../types/workflow';
import { StatusBadge } from '../../components/common/StatusBadge';
import { formatDate } from '../../lib/utils';
import { PlayCircle, Clock } from 'lucide-react';

interface WorkflowRunsTableProps {
  workflows: WorkflowRun[];
}

export function WorkflowRunsTable({ workflows }: WorkflowRunsTableProps) {
  if (!workflows || workflows.length === 0) {
    return (
      <div className="p-8 text-center text-xs text-slate-500 rounded-xl border border-dashed border-slate-200 bg-slate-50/50">
        <Clock className="w-8 h-8 text-slate-300 mx-auto mb-2" />
        <p className="font-semibold text-slate-700 mb-1">No workflow runs yet</p>
        <p className="text-slate-400 max-w-sm mx-auto">
          AI data collection and processing runs will appear here in Phase 2 when the autonomous scraping agent is triggered.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200/80 bg-white">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-slate-100 bg-slate-50 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            <th className="py-3 px-4">Run ID</th>
            <th className="py-3 px-4">Project</th>
            <th className="py-3 px-4">Status</th>
            <th className="py-3 px-4">Started</th>
            <th className="py-3 px-4">Completed</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
          {workflows.map((w) => (
            <tr key={w.id} className="hover:bg-slate-50/60 transition-colors">
              <td className="py-3 px-4 font-mono font-medium text-slate-900">
                {w.id.substring(0, 8)}...
              </td>
              <td className="py-3 px-4 font-medium text-slate-800">
                {w.project_name || 'Project'}
              </td>
              <td className="py-3 px-4">
                <StatusBadge status={w.status} />
              </td>
              <td className="py-3 px-4 text-slate-500">
                {formatDate(w.started_at)}
              </td>
              <td className="py-3 px-4 text-slate-500">
                {formatDate(w.completed_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
