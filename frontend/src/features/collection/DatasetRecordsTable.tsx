import React, { useState, useMemo } from 'react';
import { useDatasetRecords } from '../../hooks/useCollection';
import { DatasetRecord, ValidationStatus } from '../../types/collection';
import { RecordProvenanceDrawer } from './RecordProvenanceDrawer';
import { StatusBadge } from '../../components/common/StatusBadge';
import { SearchBar } from '../../components/common/SearchBar';
import { Pagination } from '../../components/common/Pagination';
import { Spinner } from '../../components/ui/Spinner';
import { Button } from '../../components/ui/Button';
import { collectionService } from '../../services/collectionService';
import { useToast } from '../../components/ui/Toast';
import {
  Database,
  Search,
  Download,
  ShieldCheck,
  Globe,
  Filter,
  FileSpreadsheet,
  FileCode,
  ExternalLink,
} from 'lucide-react';

interface DatasetRecordsTableProps {
  datasetId: string;
}

export function DatasetRecordsTable({ datasetId }: DatasetRecordsTableProps) {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [selectedRecord, setSelectedRecord] = useState<DatasetRecord | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  const { success, error: showError } = useToast();

  const { data: recordsData, isLoading, isError } = useDatasetRecords(datasetId, {
    page,
    size: pageSize,
    search: search || undefined,
    validation_status: statusFilter || undefined,
  });

  const records = recordsData?.items || [];
  const total = recordsData?.total || 0;
  const totalPages = recordsData?.pages || 1;

  // Infer dynamic columns from the keys in records
  const dynamicColumns = useMemo(() => {
    if (!records || records.length === 0) return [];
    const keysSet = new Set<string>();
    records.slice(0, 10).forEach((r) => {
      const data = r.record_data || r.normalized_data || {};
      Object.keys(data).forEach((k) => keysSet.add(k));
    });
    return Array.from(keysSet);
  }, [records]);

  const handleExport = async (format: 'json' | 'csv') => {
    try {
      setIsExporting(true);
      await collectionService.downloadExport(datasetId, format);
      success(`Exported dataset as ${format.toUpperCase()}`);
    } catch (err: any) {
      showError(err.response?.data?.detail || 'Failed to export dataset');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Top Controls Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3 flex-1 max-w-lg">
          <SearchBar
            value={search}
            onChange={(val) => {
              setSearch(val);
              setPage(1);
            }}
            placeholder="Search records by keyword, entity, location..."
          />

          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="text-xs font-semibold rounded-lg border border-slate-200 bg-white px-3 py-2 text-slate-700 hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Statuses</option>
            <option value="valid">Valid Only</option>
            <option value="valid_with_warnings">With Warnings</option>
            <option value="invalid">Invalid</option>
          </select>
        </div>

        {/* Export Buttons */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport('csv')}
            disabled={isExporting || total === 0}
            className="gap-1.5 text-xs font-medium"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
            CSV Export
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport('json')}
            disabled={isExporting || total === 0}
            className="gap-1.5 text-xs font-medium"
          >
            <FileCode className="w-3.5 h-3.5 text-blue-600" />
            JSON Export
          </Button>
        </div>
      </div>

      {/* Table Container */}
      <div className="rounded-xl border border-slate-200/80 bg-white shadow-card overflow-hidden">
        {isLoading ? (
          <div className="py-20 flex justify-center">
            <Spinner size="lg" />
          </div>
        ) : isError ? (
          <div className="py-12 text-center text-xs text-red-600">
            Failed to load dataset records.
          </div>
        ) : records.length === 0 ? (
          <div className="py-16 text-center space-y-2">
            <Database className="w-8 h-8 text-slate-300 mx-auto" />
            <h4 className="text-sm font-bold text-slate-900">No records found</h4>
            <p className="text-xs text-slate-500">
              {search || statusFilter
                ? 'Try adjusting your search query or status filter.'
                : 'No records have been extracted for this dataset yet.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-200/80 bg-slate-50/70 text-slate-600 font-semibold text-[11px] uppercase tracking-wider">
                  <th className="py-3 px-4 w-12 text-center">#</th>
                  <th className="py-3 px-4">Status</th>
                  {dynamicColumns.map((col) => (
                    <th key={col} className="py-3 px-4 whitespace-nowrap">
                      {col.replace(/_/g, ' ')}
                    </th>
                  ))}
                  <th className="py-3 px-4 text-right whitespace-nowrap">Provenance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {records.map((rec, idx) => {
                  const data = rec.record_data || rec.normalized_data || {};
                  return (
                    <tr
                      key={rec.id}
                      className="hover:bg-slate-50/70 transition-colors"
                    >
                      <td className="py-3 px-4 text-center font-mono text-slate-400 text-[11px]">
                        {(page - 1) * pageSize + idx + 1}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <StatusBadge status={rec.validation_status} />
                      </td>

                      {dynamicColumns.map((col) => {
                        const val = data[col];
                        const isUrl =
                          typeof val === 'string' &&
                          (val.startsWith('http://') || val.startsWith('https://'));

                        return (
                          <td
                            key={col}
                            className="py-3 px-4 max-w-xs truncate text-xs"
                            title={String(val ?? '')}
                          >
                            {val === null || val === undefined || val === '' ? (
                              <span className="text-slate-300 font-mono text-xs">—</span>
                            ) : isUrl ? (
                              <a
                                href={val}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-800 hover:underline"
                              >
                                Link
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            ) : typeof val === 'object' ? (
                              JSON.stringify(val)
                            ) : (
                              String(val)
                            )}
                          </td>
                        );
                      })}

                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedRecord(rec)}
                          className="text-[11px] font-semibold gap-1 px-2.5 py-1 h-7 border-slate-200 hover:bg-indigo-50 hover:text-indigo-600 hover:border-indigo-200"
                        >
                          <ShieldCheck className="w-3 h-3 text-indigo-500" />
                          View Sources ({rec.source_count || 1})
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination Bar */}
      {totalPages > 1 && (
        <Pagination
          currentPage={page}
          totalPages={totalPages}
          totalItems={total}
          pageSize={pageSize}
          onPageChange={setPage}
        />
      )}

      {/* Source Provenance Drawer */}
      <RecordProvenanceDrawer
        record={selectedRecord}
        isOpen={!!selectedRecord}
        onClose={() => setSelectedRecord(null)}
      />
    </div>
  );
}
