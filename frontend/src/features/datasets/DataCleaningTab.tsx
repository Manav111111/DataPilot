import React, { useState } from 'react';
import { useDatasetProfile, useDatasetTransformations, useDatasetManagementMutations } from '../../hooks/useDatasetManagement';
import { datasetManagementService } from '../../services/datasetManagementService';
import { CleanPreviewResponse } from '../../types/dataset_management';
import { Spinner } from '../../components/ui/Spinner';
import {
  Wand2,
  AlertTriangle,
  CheckCircle2,
  History,
  ArrowRight,
  Filter,
  Layers,
  Sparkles,
  RefreshCw,
} from 'lucide-react';
import { Button } from '../../components/ui/Button';

interface DataCleaningTabProps {
  datasetId: string;
}

const CLEANING_OPERATIONS = [
  { id: 'trim_whitespace', name: 'Trim Whitespace', desc: 'Remove leading, trailing, and double whitespace in text fields' },
  { id: 'normalize_blanks', name: 'Normalize Blank Values', desc: 'Convert empty strings, "N/A", "null", and "-" to null' },
  { id: 'normalize_urls', name: 'Normalize URLs', desc: 'Ensure https:// prefix, clean trailing slashes, and strip tracking params' },
  { id: 'standardize_dates', name: 'Standardize Date Formats', desc: 'Convert varied date strings into uniform ISO 8601 (YYYY-MM-DD)' },
  { id: 'normalize_geo', name: 'Normalize Geographical Labels', desc: 'Standardize common city and country variations (e.g. Bengaluru → Bangalore)' },
  { id: 'normalize_case', name: 'Normalize Casing', desc: 'Convert text fields to Title Case, lowercase, or UPPERCASE' },
  { id: 'remove_duplicates', name: 'Remove Exact Duplicates', desc: 'Identify and drop exact identical duplicate records' },
  { id: 'fill_missing_constant', name: 'Fill Missing with Constant', desc: 'Fill null/blank values with a specific default value' },
  { id: 'drop_missing_required', name: 'Drop Missing Required Rows', desc: 'Remove records that are missing values in required fields' },
];

export function DataCleaningTab({ datasetId }: DataCleaningTabProps) {
  const { data: profile } = useDatasetProfile(datasetId);
  const { data: transformations, isLoading: loadingTransforms } = useDatasetTransformations(datasetId);
  const { cleanApplyMutation } = useDatasetManagementMutations(datasetId);

  const [selectedOp, setSelectedOp] = useState<string>('trim_whitespace');
  const [targetField, setTargetField] = useState<string>('');
  const [constantVal, setConstantVal] = useState<string>('');
  const [caseType, setCaseType] = useState<string>('title');
  const [preview, setPreview] = useState<CleanPreviewResponse | null>(null);
  const [isPreviewing, setIsPreviewing] = useState<boolean>(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const columns = profile?.columns || [];

  const handlePreview = async () => {
    setIsPreviewing(true);
    setSuccessMsg(null);
    try {
      const config: Record<string, any> = {};
      if (targetField) config.field_name = targetField;
      if (selectedOp === 'fill_missing_constant') config.constant_value = constantVal;
      if (selectedOp === 'normalize_case') config.case_type = caseType;
      if (selectedOp === 'drop_missing_required' && targetField) config.required_fields = [targetField];

      const res = await datasetManagementService.previewClean(datasetId, selectedOp, config);
      setPreview(res);
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsPreviewing(false);
    }
  };

  const handleApply = async () => {
    if (!preview) return;
    try {
      const res = await cleanApplyMutation.mutateAsync({
        operationType: selectedOp,
        configuration: preview.configuration,
        createVersion: true,
        changeSummary: `Applied cleaning: ${CLEANING_OPERATIONS.find((o) => o.id === selectedOp)?.name}`,
      });
      setSuccessMsg(res.message);
      setPreview(null);
    } catch (err: any) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Cleaning Configurator Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-5">
        <div>
          <div className="flex items-center gap-2 text-indigo-600 font-bold text-sm">
            <Wand2 className="w-4 h-4" />
            <span>Automated Data Cleaning Workspace</span>
          </div>
          <h3 className="text-lg font-bold text-slate-900 mt-1">Select and Preview Cleaning Strategies</h3>
          <p className="text-xs text-slate-500">
            Clean and normalize messy data fields with safe previews before applying. Every cleaning step creates an auditable version snapshot.
          </p>
        </div>

        {/* Operation Selection Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {CLEANING_OPERATIONS.map((op) => (
            <div
              key={op.id}
              onClick={() => {
                setSelectedOp(op.id);
                setPreview(null);
              }}
              className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                selectedOp === op.id
                  ? 'border-indigo-600 bg-indigo-50/50 shadow-sm'
                  : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-900">{op.name}</span>
                {selectedOp === op.id && <CheckCircle2 className="w-4 h-4 text-indigo-600" />}
              </div>
              <p className="text-[11px] text-slate-500 mt-1 leading-snug">{op.desc}</p>
            </div>
          ))}
        </div>

        {/* Additional Parameters for specific operations */}
        <div className="flex flex-wrap gap-4 items-center pt-2">
          {['normalize_case', 'fill_missing_constant', 'drop_missing_required', 'normalize_geo', 'standardize_dates'].includes(selectedOp) && (
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                Target Column {['fill_missing_constant', 'drop_missing_required'].includes(selectedOp) ? '(Required)' : '(Optional - all if empty)'}
              </label>
              <select
                value={targetField}
                onChange={(e) => setTargetField(e.target.value)}
                className="text-xs border border-slate-300 rounded-lg px-3 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All Applicable Columns</option>
                {columns.map((c) => (
                  <option key={c.column_name} value={c.column_name}>
                    {c.column_name} ({c.inferred_type})
                  </option>
                ))}
              </select>
            </div>
          )}

          {selectedOp === 'normalize_case' && (
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">Casing Style</label>
              <select
                value={caseType}
                onChange={(e) => setCaseType(e.target.value)}
                className="text-xs border border-slate-300 rounded-lg px-3 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="title">Title Case (e.g. Senior Ml Engineer)</option>
                <option value="lower">lowercase (e.g. senior ml engineer)</option>
                <option value="upper">UPPERCASE (e.g. SENIOR ML ENGINEER)</option>
              </select>
            </div>
          )}

          {selectedOp === 'fill_missing_constant' && (
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">Default Constant Value</label>
              <input
                type="text"
                value={constantVal}
                onChange={(e) => setConstantVal(e.target.value)}
                placeholder="e.g. Unknown or N/A"
                className="text-xs border border-slate-300 rounded-lg px-3 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          )}

          <div className="pt-4 sm:pt-0 sm:self-end">
            <Button
              onClick={handlePreview}
              disabled={isPreviewing}
              size="sm"
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs gap-1.5"
            >
              {isPreviewing ? <Spinner size="sm" /> : <Sparkles className="w-3.5 h-3.5" />}
              Generate Cleaning Preview
            </Button>
          </div>
        </div>

        {/* Success alert */}
        {successMsg && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs font-semibold text-emerald-800 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}
      </div>

      {/* Cleaning Preview Result Card */}
      {preview && (
        <div className="bg-white rounded-xl border border-indigo-200 p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-600" />
              <h4 className="text-sm font-bold text-slate-900">Cleaning Preview Summary</h4>
            </div>
            <span className="text-xs font-bold px-3 py-1 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
              {preview.records_affected} Records Affected
            </span>
          </div>

          {preview.warnings && preview.warnings.length > 0 && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 space-y-1">
              <div className="flex items-center gap-1.5 font-bold">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span>Notice</span>
              </div>
              <ul className="list-disc list-inside text-[11px] text-amber-700">
                {preview.warnings.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Sample Diffs */}
          {preview.samples && preview.samples.length > 0 ? (
            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-700">Sample Proposed Changes (Top 5):</span>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {preview.samples.map((s, idx) => (
                  <div key={idx} className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-2">
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                      Record #{idx + 1} ({s.action || 'update'})
                    </div>
                    <div className="space-y-1">
                      <div className="text-rose-700 font-medium">
                        <span className="text-[10px] text-rose-500 uppercase font-bold mr-1">Before:</span>
                        <code className="text-[11px] bg-rose-50 px-1 py-0.5 rounded border border-rose-100">
                          {JSON.stringify(s.original)}
                        </code>
                      </div>
                      {s.cleaned && (
                        <div className="text-emerald-700 font-medium">
                          <span className="text-[10px] text-emerald-500 uppercase font-bold mr-1">After:</span>
                          <code className="text-[11px] bg-emerald-50 px-1 py-0.5 rounded border border-emerald-100">
                            {JSON.stringify(s.cleaned)}
                          </code>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic">No records required modification under this rule.</p>
          )}

          {/* Apply Button */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              onClick={() => setPreview(null)}
              className="text-xs font-semibold px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-600"
            >
              Cancel
            </button>
            <Button
              onClick={handleApply}
              disabled={cleanApplyMutation.isPending || preview.records_affected === 0}
              className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs px-5 py-2"
            >
              {cleanApplyMutation.isPending ? <Spinner size="sm" /> : <CheckCircle2 className="w-4 h-4 mr-1" />}
              Apply Cleaning & Create Version Snapshot
            </Button>
          </div>
        </div>
      )}

      {/* Transformation History Audit Log */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-slate-600" />
          <h4 className="text-sm font-bold text-slate-900">Transformation & Cleaning History</h4>
        </div>

        {loadingTransforms ? (
          <div className="flex justify-center p-6">
            <Spinner size="md" />
          </div>
        ) : transformations && transformations.length > 0 ? (
          <div className="divide-y divide-slate-100">
            {transformations.map((t) => (
              <div key={t.id} className="py-3 flex items-center justify-between text-xs">
                <div>
                  <span className="font-bold text-slate-800">{t.operation_type.replace('_', ' ').toUpperCase()}</span>
                  <div className="text-[11px] text-slate-500">
                    Affected <b className="text-slate-700">{t.records_affected}</b> records · {new Date(t.created_at).toLocaleString()}
                  </div>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  {t.status}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-500 italic">No previous cleaning operations applied to this dataset.</p>
        )}
      </div>
    </div>
  );
}
