import React, { useState } from 'react';
import { useDatasetProfile, useDatasetExports } from '../../hooks/useDatasetManagement';
import { datasetManagementService } from '../../services/datasetManagementService';
import { Spinner } from '../../components/ui/Spinner';
import { Button } from '../../components/ui/Button';
import {
  Download,
  FileSpreadsheet,
  FileText,
  Code2,
  CheckCircle2,
  ExternalLink,
  ShieldCheck,
  History,
  X,
} from 'lucide-react';

interface ExportCenterModalProps {
  datasetId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function ExportCenterModal({ datasetId, isOpen, onClose }: ExportCenterModalProps) {
  const { data: profile } = useDatasetProfile(datasetId);
  const { data: exportsList, refetch: refetchExports, isLoading: loadingExports } = useDatasetExports(datasetId);

  const [format, setFormat] = useState<'csv' | 'xlsx' | 'json'>('csv');
  const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
  const [includeProvenance, setIncludeProvenance] = useState<boolean>(true);
  const [includeWarnings, setIncludeWarnings] = useState<boolean>(false);
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [downloadSuccess, setDownloadSuccess] = useState<string | null>(null);

  if (!isOpen) return null;

  const columns = profile?.columns || [];

  const handleToggleColumn = (col: string) => {
    if (selectedColumns.includes(col)) {
      setSelectedColumns(selectedColumns.filter((c) => c !== col));
    } else {
      setSelectedColumns([...selectedColumns, col]);
    }
  };

  const handleExport = async () => {
    setIsExporting(true);
    setDownloadSuccess(null);
    try {
      const res = await datasetManagementService.createExport(
        datasetId,
        format,
        selectedColumns.length > 0 ? selectedColumns : undefined,
        includeProvenance,
        includeWarnings
      );

      // Trigger browser download
      const downloadUrl = datasetManagementService.getExportDownloadUrl(res.id);
      window.open(downloadUrl, '_blank');

      setDownloadSuccess(`Export generated successfully (${(res.file_size_bytes || 0) / 1024} KB).`);
      refetchExports();
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="px-6 py-5 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2 text-indigo-600 font-bold text-sm">
            <Download className="w-5 h-5" />
            <span>Dataset Export Center</span>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Format Picker */}
          <div>
            <label className="block text-xs font-bold text-slate-900 mb-2">1. Select Export Format</label>
            <div className="grid grid-cols-3 gap-3">
              <div
                onClick={() => setFormat('csv')}
                className={`p-3.5 rounded-xl border cursor-pointer transition-all text-center space-y-1 ${
                  format === 'csv'
                    ? 'border-indigo-600 bg-indigo-50/70 ring-1 ring-indigo-500/30'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <FileText className="w-5 h-5 mx-auto text-indigo-600" />
                <div className="text-xs font-bold text-slate-900">CSV Format</div>
                <p className="text-[10px] text-slate-500">UTF-8 with formula injection defense</p>
              </div>

              <div
                onClick={() => setFormat('xlsx')}
                className={`p-3.5 rounded-xl border cursor-pointer transition-all text-center space-y-1 ${
                  format === 'xlsx'
                    ? 'border-indigo-600 bg-indigo-50/70 ring-1 ring-indigo-500/30'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <FileSpreadsheet className="w-5 h-5 mx-auto text-emerald-600" />
                <div className="text-xs font-bold text-slate-900">Excel (.xlsx)</div>
                <p className="text-[10px] text-slate-500">Styled workbook + Quality Sheet</p>
              </div>

              <div
                onClick={() => setFormat('json')}
                className={`p-3.5 rounded-xl border cursor-pointer transition-all text-center space-y-1 ${
                  format === 'json'
                    ? 'border-indigo-600 bg-indigo-50/70 ring-1 ring-indigo-500/30'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <Code2 className="w-5 h-5 mx-auto text-amber-600" />
                <div className="text-xs font-bold text-slate-900">JSON Format</div>
                <p className="text-[10px] text-slate-500">Structured array with typed fields</p>
              </div>
            </div>
          </div>

          {/* Column Picker */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-bold text-slate-900">2. Select Columns</label>
              <button
                onClick={() =>
                  setSelectedColumns(
                    selectedColumns.length === columns.length ? [] : columns.map((c) => c.column_name)
                  )
                }
                className="text-[11px] text-indigo-600 font-semibold hover:underline"
              >
                {selectedColumns.length === columns.length ? 'Deselect All' : 'Select All'}
              </button>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-36 overflow-y-auto p-2 border border-slate-200 rounded-xl bg-slate-50/50">
              {columns.map((c) => {
                const isSelected = selectedColumns.length === 0 || selectedColumns.includes(c.column_name);
                return (
                  <label
                    key={c.column_name}
                    className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer select-none"
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleToggleColumn(c.column_name)}
                      className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span className="truncate">{c.column_name}</span>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Options */}
          <div className="space-y-2 pt-1 border-t border-slate-100">
            <label className="text-xs font-bold text-slate-900 block">3. Metadata & Provenance Options</label>
            <div className="space-y-1.5">
              <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeProvenance}
                  onChange={(e) => setIncludeProvenance(e.target.checked)}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span>Include Source Provenance Count & Verification URLs</span>
              </label>
              <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeWarnings}
                  onChange={(e) => setIncludeWarnings(e.target.checked)}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span>Include Validation Status Column (`valid`, `valid_with_warnings`)</span>
              </label>
            </div>
          </div>

          {downloadSuccess && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs font-semibold text-emerald-800 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{downloadSuccess}</span>
            </div>
          )}

          {/* Past Exports */}
          {exportsList && exportsList.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-slate-100">
              <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                <History className="w-3.5 h-3.5 text-slate-500" />
                Recent Export Downloads
              </span>
              <div className="divide-y divide-slate-100 max-h-32 overflow-y-auto">
                {exportsList.slice(0, 3).map((exp) => (
                  <div key={exp.id} className="py-2 flex items-center justify-between text-xs">
                    <div>
                      <span className="font-bold uppercase text-slate-800">{exp.format}</span>
                      <span className="text-slate-400 text-[11px] ml-2">
                        {new Date(exp.created_at).toLocaleTimeString()} · {exp.record_count} records
                      </span>
                    </div>
                    <a
                      href={datasetManagementService.getExportDownloadUrl(exp.id)}
                      target="_blank"
                      rel="noreferrer"
                      className="text-indigo-600 hover:text-indigo-800 font-semibold inline-flex items-center gap-1 text-[11px]"
                    >
                      Download <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex items-center justify-end gap-3 rounded-b-2xl">
          <button
            onClick={onClose}
            className="text-xs font-semibold px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-600"
          >
            Close
          </button>
          <Button
            onClick={handleExport}
            disabled={isExporting}
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs px-5 py-2 gap-1.5"
          >
            {isExporting ? <Spinner size="sm" /> : <Download className="w-4 h-4" />}
            Generate & Download {format.toUpperCase()}
          </Button>
        </div>
      </div>
    </div>
  );
}
