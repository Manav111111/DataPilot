import React, { useState } from 'react';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Dataset } from '../../types/dataset';
import { formatDate, formatNumber } from '../../lib/utils';
import { DatasetRecordsTable } from '../collection/DatasetRecordsTable';
import { DatasetSourcesList } from '../collection/DatasetSourcesList';
import { DatasetOverviewCard } from '../collection/DatasetOverviewCard';
import { DatasetQualityTab } from './DatasetQualityTab';
import { DataCleaningTab } from './DataCleaningTab';
import { DataTransformationsTab } from './DataTransformationsTab';
import { DuplicateResolverTab } from './DuplicateResolverTab';
import { DatasetAnalyticsTab } from './DatasetAnalyticsTab';
import { VersionHistoryTab } from './VersionHistoryTab';
import { DatasetInsightsTab } from '../analysis/DatasetInsightsTab';
import { DatasetReportsTab } from '../analysis/DatasetReportsTab';
import { ExportCenterModal } from './ExportCenterModal';
import { DatasetComparisonModal } from './DatasetComparisonModal';
import {
  Database,
  Folder,
  Calendar,
  Hash,
  Globe,
  Table,
  Info,
  ShieldCheck,
  Wand2,
  Sparkles,
  BarChart3,
  Copy,
  History,
  Download,
  GitCompare,
  Bot,
  FileText,
  Layers,
} from 'lucide-react';

interface DatasetDetailsModalProps {
  dataset: Dataset | null;
  isOpen: boolean;
  onClose: () => void;
  onEdit?: (dataset: Dataset) => void;
}

type TabType =
  | 'records'
  | 'insights'
  | 'quality'
  | 'cleaning'
  | 'transformations'
  | 'analytics'
  | 'reports'
  | 'duplicates'
  | 'versions'
  | 'sources'
  | 'metadata';

export function DatasetDetailsModal({
  dataset,
  isOpen,
  onClose,
  onEdit,
}: DatasetDetailsModalProps) {
  const [activeTab, setActiveTab] = useState<TabType>('records');
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [isCompareOpen, setIsCompareOpen] = useState(false);

  if (!dataset) return null;

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        title={dataset.name}
        description={dataset.description || 'Verified structured dataset extracted from permitted sources.'}
        maxWidth="6xl"
      >
        <div className="space-y-5">
          {/* Header Action Toolbar */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-slate-50 border border-slate-200/80 rounded-xl">
            <div className="flex items-center gap-3">
              <span className="text-xs font-semibold text-slate-600">
                Dataset ID: <code className="text-slate-900 bg-white px-1.5 py-0.5 rounded border border-slate-200 text-[11px]">{dataset.id.slice(0, 8)}...</code>
              </span>
              <StatusBadge status={dataset.status} />
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsCompareOpen(true)}
                className="text-xs font-semibold gap-1.5 h-8 bg-white hover:bg-slate-50"
              >
                <GitCompare className="w-3.5 h-3.5 text-indigo-600" />
                Compare Datasets
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => setIsExportOpen(true)}
                className="text-xs font-semibold gap-1.5 h-8 bg-indigo-600 hover:bg-indigo-700 text-white"
              >
                <Download className="w-3.5 h-3.5" />
                Export Center
              </Button>
            </div>
          </div>

          {/* Quality Metrics Summary Cards */}
          <DatasetOverviewCard datasetId={dataset.id} />

          {/* Navigation Tabs */}
          <div className="border-b border-slate-200 overflow-x-auto">
            <nav className="flex space-x-2 min-w-max pb-px">
              <button
                onClick={() => setActiveTab('records')}
                className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition-colors flex items-center gap-1.5 ${
                  activeTab === 'records'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <Table className="w-3.5 h-3.5" />
                Records ({formatNumber(dataset.row_count)})
              </button>

              <button
                onClick={() => setActiveTab('insights')}
                className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition-colors flex items-center gap-1.5 ${
                  activeTab === 'insights'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                AI Insights
              </button>

              <button
                onClick={() => setActiveTab('quality')}
                className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition-colors flex items-center gap-1.5 ${
                  activeTab === 'quality'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                Data Quality
              </button>

              <button
                onClick={() => setActiveTab('cleaning')}
                className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition-colors flex items-center gap-1.5 ${
                  activeTab === 'cleaning'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <Wand2 className="w-3.5 h-3.5 text-amber-600" />
                Cleaning
              </button>

              <button
                onClick={() => setActiveTab('transformations')}
                className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition-colors flex items-center gap-1.5 ${
                  activeTab === 'transformations'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <Layers className="w-3.5 h-3.5 text-violet-600" />
                Transformations
              </button>

              <button
                onClick={() => setActiveTab('analytics')}
                className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition-colors flex items-center gap-1.5 ${
                  activeTab === 'analytics'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <BarChart3 className="w-3.5 h-3.5 text-blue-600" />
                Visual Analytics
              </button>

              <button
                onClick={() => setActiveTab('reports')}
                className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition-colors flex items-center gap-1.5 ${
                  activeTab === 'reports'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <FileText className="w-3.5 h-3.5 text-rose-600" />
                Reports
              </button>

              <button
                onClick={() => setActiveTab('duplicates')}
                className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition-colors flex items-center gap-1.5 ${
                  activeTab === 'duplicates'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <Copy className="w-3.5 h-3.5 text-orange-600" />
                Duplicates
              </button>

              <button
                onClick={() => setActiveTab('versions')}
                className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition-colors flex items-center gap-1.5 ${
                  activeTab === 'versions'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <History className="w-3.5 h-3.5 text-teal-600" />
                Version History
              </button>

              <button
                onClick={() => setActiveTab('sources')}
                className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition-colors flex items-center gap-1.5 ${
                  activeTab === 'sources'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <Globe className="w-3.5 h-3.5 text-cyan-600" />
                Sources
              </button>

              <button
                onClick={() => setActiveTab('metadata')}
                className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition-colors flex items-center gap-1.5 ${
                  activeTab === 'metadata'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <Info className="w-3.5 h-3.5 text-slate-600" />
                Metadata
              </button>
            </nav>
          </div>

          {/* Tab 1: Records Table */}
          {activeTab === 'records' && (
            <div className="space-y-3">
              <DatasetRecordsTable datasetId={dataset.id} />
            </div>
          )}

          {/* Tab 2: AI Insights Chat */}
          {activeTab === 'insights' && (
            <div className="space-y-3">
              <DatasetInsightsTab datasetId={dataset.id} />
            </div>
          )}

          {/* Tab 3: Quality Profiler */}
          {activeTab === 'quality' && (
            <div className="space-y-3">
              <DatasetQualityTab datasetId={dataset.id} />
            </div>
          )}

          {/* Tab 4: Data Cleaning */}
          {activeTab === 'cleaning' && (
            <div className="space-y-3">
              <DataCleaningTab datasetId={dataset.id} />
            </div>
          )}

          {/* Tab 5: Safe Transformations */}
          {activeTab === 'transformations' && (
            <div className="space-y-3">
              <DataTransformationsTab datasetId={dataset.id} />
            </div>
          )}

          {/* Tab 6: Analytics */}
          {activeTab === 'analytics' && (
            <div className="space-y-3">
              <DatasetAnalyticsTab datasetId={dataset.id} />
            </div>
          )}

          {/* Tab 7: Reports */}
          {activeTab === 'reports' && (
            <div className="space-y-3">
              <DatasetReportsTab datasetId={dataset.id} />
            </div>
          )}

          {/* Tab 8: Duplicate Resolution */}
          {activeTab === 'duplicates' && (
            <div className="space-y-3">
              <DuplicateResolverTab datasetId={dataset.id} />
            </div>
          )}

          {/* Tab 9: Version History */}
          {activeTab === 'versions' && (
            <div className="space-y-3">
              <VersionHistoryTab datasetId={dataset.id} />
            </div>
          )}

          {/* Tab 10: Sources List */}
          {activeTab === 'sources' && (
            <div className="space-y-3">
              <DatasetSourcesList datasetId={dataset.id} />
            </div>
          )}

          {/* Tab 11: Metadata Details */}
          {activeTab === 'metadata' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="p-3 rounded-lg border border-slate-100 bg-slate-50">
                  <div className="flex items-center text-slate-400 gap-1.5 mb-1">
                    <Folder className="w-3.5 h-3.5" />
                    <span>Project ID</span>
                  </div>
                  <p className="font-semibold text-slate-800 truncate font-mono text-[11px]">
                    {dataset.project_id}
                  </p>
                </div>

                <div className="p-3 rounded-lg border border-slate-100 bg-slate-50">
                  <div className="flex items-center text-slate-400 gap-1.5 mb-1">
                    <Hash className="w-3.5 h-3.5" />
                    <span>Dataset Status</span>
                  </div>
                  <StatusBadge status={dataset.status} />
                </div>

                <div className="p-3 rounded-lg border border-slate-100 bg-slate-50">
                  <div className="flex items-center text-slate-400 gap-1.5 mb-1">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>Created</span>
                  </div>
                  <p className="font-semibold text-slate-800">
                    {formatDate(dataset.created_at)}
                  </p>
                </div>

                <div className="p-3 rounded-lg border border-slate-100 bg-slate-50">
                  <div className="flex items-center text-slate-400 gap-1.5 mb-1">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>Last Modified</span>
                  </div>
                  <p className="font-semibold text-slate-800">
                    {formatDate(dataset.updated_at)}
                  </p>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70 text-xs space-y-1">
                <span className="font-semibold text-slate-700 block">Description</span>
                <p className="text-slate-600">
                  {dataset.description || 'No custom description provided for this dataset.'}
                </p>
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex justify-end space-x-3 pt-4 border-t border-slate-100">
            <Button variant="outline" size="sm" onClick={onClose}>
              Close
            </Button>
            {onEdit && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => {
                  onClose();
                  onEdit(dataset);
                }}
              >
                Edit Dataset Info
              </Button>
            )}
          </div>
        </div>
      </Modal>

      {/* Export Center Modal */}
      <ExportCenterModal
        datasetId={dataset.id}
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
      />

      {/* Dataset Comparison Modal */}
      <DatasetComparisonModal
        initialDatasetId={dataset.id}
        isOpen={isCompareOpen}
        onClose={() => setIsCompareOpen(false)}
      />
    </>
  );
}
