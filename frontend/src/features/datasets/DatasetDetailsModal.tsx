import React from 'react';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Dataset } from '../../types/dataset';
import { formatDate, formatNumber } from '../../lib/utils';
import { Database, Folder, Calendar, Hash, Tag } from 'lucide-react';

interface DatasetDetailsModalProps {
  dataset: Dataset | null;
  isOpen: boolean;
  onClose: () => void;
  onEdit?: (dataset: Dataset) => void;
}

export function DatasetDetailsModal({
  dataset,
  isOpen,
  onClose,
  onEdit,
}: DatasetDetailsModalProps) {
  if (!dataset) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Dataset Details"
      description="Detailed schema metadata and operational summary."
      maxWidth="lg"
    >
      <div className="space-y-4">
        {/* Header Info */}
        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200/60">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Database className="w-4 h-4 text-indigo-600" />
              {dataset.name}
            </h4>
            <StatusBadge status={dataset.status} />
          </div>
          <p className="text-xs text-slate-600">
            {dataset.description || 'No description specified for this dataset.'}
          </p>
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="p-3 rounded-lg border border-slate-100 bg-white">
            <div className="flex items-center text-slate-400 gap-1.5 mb-1">
              <Folder className="w-3.5 h-3.5" />
              <span>Project</span>
            </div>
            <p className="font-semibold text-slate-800">
              {dataset.project_name || 'Associated Project'}
            </p>
          </div>

          <div className="p-3 rounded-lg border border-slate-100 bg-white">
            <div className="flex items-center text-slate-400 gap-1.5 mb-1">
              <Hash className="w-3.5 h-3.5" />
              <span>Total Rows</span>
            </div>
            <p className="font-semibold text-slate-800">
              {formatNumber(dataset.row_count)} records
            </p>
          </div>

          <div className="p-3 rounded-lg border border-slate-100 bg-white">
            <div className="flex items-center text-slate-400 gap-1.5 mb-1">
              <Calendar className="w-3.5 h-3.5" />
              <span>Created</span>
            </div>
            <p className="font-semibold text-slate-800">
              {formatDate(dataset.created_at)}
            </p>
          </div>

          <div className="p-3 rounded-lg border border-slate-100 bg-white">
            <div className="flex items-center text-slate-400 gap-1.5 mb-1">
              <Calendar className="w-3.5 h-3.5" />
              <span>Last Modified</span>
            </div>
            <p className="font-semibold text-slate-800">
              {formatDate(dataset.updated_at)}
            </p>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex justify-end space-x-3 pt-4 border-t border-slate-100">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
          {onEdit && (
            <Button
              variant="primary"
              onClick={() => {
                onClose();
                onEdit(dataset);
              }}
            >
              Edit Dataset
            </Button>
          )}
        </div>
      </div>
    </Modal>
  );
}
