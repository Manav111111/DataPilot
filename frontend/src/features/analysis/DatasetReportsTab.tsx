import React, { useState } from 'react';
import { useDatasetReports, useCreateReportMutation } from '../../hooks/useAnalysis';
import { analysisService } from '../../services/analysisService';
import { Spinner } from '../../components/ui/Spinner';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import { useToast } from '../../components/ui/Toast';
import { formatDate } from '../../lib/utils';
import {
  FileText,
  Download,
  Plus,
  Layers,
  Calendar,
  Sparkles,
  ExternalLink,
} from 'lucide-react';

interface DatasetReportsTabProps {
  datasetId: string;
}

export function DatasetReportsTab({ datasetId }: DatasetReportsTabProps) {
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [title, setTitle] = useState('Dataset Intelligence Report');
  const [notes, setNotes] = useState('');
  const [isDownloading, setIsDownloading] = useState<string | null>(null);

  const { success, error: showError } = useToast();
  const { data: reports, isLoading } = useDatasetReports(datasetId);
  const { mutateAsync: createReport, isPending: isCreating } = useCreateReportMutation(datasetId);

  const handleDownload = async (reportId: string, reportTitle: string) => {
    try {
      setIsDownloading(reportId);
      await analysisService.downloadReport(reportId, reportTitle);
      success('Report downloaded successfully.');
    } catch (err: any) {
      showError(err.response?.data?.detail || 'Failed to download report');
    } finally {
      setIsDownloading(null);
    }
  };

  const handleCreate = async () => {
    if (!title.trim()) return;
    try {
      await createReport({
        title,
        format: 'html',
        custom_notes: notes || undefined,
      });
      setIsCreateOpen(false);
      setTitle('Dataset Intelligence Report');
      setNotes('');
      success('Report generated successfully!');
    } catch (err: any) {
      showError(err.response?.data?.detail || 'Failed to generate report');
    }
  };

  return (
    <div className="space-y-4">
      {/* Header bar */}
      <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200">
        <div>
          <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Analysis & Intelligence Reports
          </h4>
          <p className="text-[11px] text-slate-500">
            Export standalone HTML/PDF analysis documents with executive findings and verified stats.
          </p>
        </div>
        <Button
          variant="primary"
          size="sm"
          onClick={() => setIsCreateOpen(true)}
          className="text-xs font-semibold gap-1.5 h-8 bg-indigo-600 hover:bg-indigo-700"
        >
          <Plus className="w-3.5 h-3.5" />
          Generate New Report
        </Button>
      </div>

      {/* Reports List Container */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-card overflow-hidden">
        {isLoading ? (
          <div className="py-16 flex justify-center">
            <Spinner size="lg" />
          </div>
        ) : !reports || reports.length === 0 ? (
          <div className="py-16 text-center space-y-3">
            <FileText className="w-8 h-8 text-slate-300 mx-auto" />
            <h4 className="text-sm font-bold text-slate-900">No reports generated yet</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Generate a standalone intelligence report combining automated insights,
              descriptive statistics, and custom annotations.
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsCreateOpen(true)}
              className="text-xs font-semibold gap-1.5"
            >
              <Plus className="w-3.5 h-3.5 text-indigo-600" />
              Generate First Report
            </Button>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {reports.map((report) => (
              <div
                key={report.id}
                className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50/70 transition-colors"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h5 className="font-bold text-slate-900 text-xs">{report.title}</h5>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-indigo-50 text-indigo-700 border border-indigo-100">
                      {report.format}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-100 text-slate-600">
                      v{report.dataset_version}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-[11px] text-slate-400">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {formatDate(report.created_at)}
                    </span>
                    <span>&bull;</span>
                    <span>
                      {report.report_data?.insights_summary || 0} Insights Included
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDownload(report.id, report.title)}
                    disabled={isDownloading === report.id}
                    className="text-xs font-semibold gap-1.5 h-8 bg-white border-slate-200 hover:border-indigo-300 hover:text-indigo-600"
                  >
                    {isDownloading === report.id ? (
                      <Spinner size="sm" />
                    ) : (
                      <Download className="w-3.5 h-3.5" />
                    )}
                    Download Standalone HTML
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Generate Analysis Report"
        description="Creates a verified analysis document combining insights, descriptive statistics, and custom findings."
        maxWidth="lg"
      >
        <div className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">
              Report Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full text-xs rounded-lg border border-slate-300 bg-white p-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">
              Custom Executive Summary / Notes
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add findings, caveats, or executive summary remarks..."
              className="w-full text-xs rounded-lg border border-slate-300 bg-white p-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsCreateOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleCreate}
              disabled={isCreating || !title.trim()}
              className="gap-1.5"
            >
              {isCreating ? <Spinner size="sm" /> : <FileText className="w-3.5 h-3.5" />}
              Generate Report
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
