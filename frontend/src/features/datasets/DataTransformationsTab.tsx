import React, { useState } from 'react';
import { useDatasetProfile, useDatasetManagementMutations } from '../../hooks/useDatasetManagement';
import { datasetManagementService } from '../../services/datasetManagementService';
import { TransformPreviewResponse } from '../../types/dataset_management';
import { Spinner } from '../../components/ui/Spinner';
import {
  Sparkles,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Code2,
  Plus,
} from 'lucide-react';
import { Button } from '../../components/ui/Button';

interface DataTransformationsTabProps {
  datasetId: string;
}

export function DataTransformationsTab({ datasetId }: DataTransformationsTabProps) {
  const { data: profile } = useDatasetProfile(datasetId);
  const { transformApplyMutation } = useDatasetManagementMutations(datasetId);

  const [operationType, setOperationType] = useState<'derive_column' | 'rename_column' | 'filter_records'>('derive_column');
  const [exprType, setExprType] = useState<string>('extract_domain');
  const [targetColumn, setTargetColumn] = useState<string>('company_domain');
  const [sourceColumn, setSourceColumn] = useState<string>('');
  const [sourceColumnsMulti, setSourceColumnsMulti] = useState<string[]>([]);
  const [delimiter, setDelimiter] = useState<string>(' at ');
  const [oldName, setOldName] = useState<string>('');
  const [newName, setNewName] = useState<string>('');
  const [filterField, setFilterField] = useState<string>('');
  const [filterOp, setFilterOp] = useState<string>('>=');
  const [filterVal, setFilterVal] = useState<string>('');

  const [preview, setPreview] = useState<TransformPreviewResponse | null>(null);
  const [isPreviewing, setIsPreviewing] = useState<boolean>(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const columns = profile?.columns || [];

  const handlePreview = async () => {
    setIsPreviewing(true);
    setSuccessMsg(null);
    try {
      let config: Record<string, any> = {};

      if (operationType === 'derive_column') {
        config = {
          target_column: targetColumn,
          expression_type: exprType,
          source_column: sourceColumn,
          source_columns: sourceColumnsMulti,
          delimiter,
        };
      } else if (operationType === 'rename_column') {
        config = {
          old_name: oldName,
          new_name: newName,
        };
      } else if (operationType === 'filter_records') {
        config = {
          filter_field: filterField,
          operator: filterOp,
          value: filterVal,
          action: 'keep',
        };
      }

      const res = await datasetManagementService.previewTransform(datasetId, operationType, config);
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
      const res = await transformApplyMutation.mutateAsync({
        operationType,
        configuration: preview.configuration,
        createVersion: true,
        changeSummary: `Applied transformation: ${operationType.replace('_', ' ').toUpperCase()}`,
      });
      setSuccessMsg(res.message);
      setPreview(null);
    } catch (err: any) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Transformation Builder Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-5">
        <div>
          <div className="flex items-center gap-2 text-indigo-600 font-bold text-sm">
            <Sliders className="w-4 h-4" />
            <span>Deterministic Transformation Builder</span>
          </div>
          <h3 className="text-lg font-bold text-slate-900 mt-1">Create Derived Columns & Dataset Transformations</h3>
          <p className="text-xs text-slate-500">
            Apply safe allowlist transformations to enrich records without arbitrary code execution risk.
          </p>
        </div>

        {/* Operation Type Switcher */}
        <div className="flex gap-2 border-b border-slate-200 pb-3">
          <button
            onClick={() => {
              setOperationType('derive_column');
              setPreview(null);
            }}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
              operationType === 'derive_column'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            Create Derived Column
          </button>
          <button
            onClick={() => {
              setOperationType('rename_column');
              setPreview(null);
            }}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
              operationType === 'rename_column'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            Rename Column
          </button>
          <button
            onClick={() => {
              setOperationType('filter_records');
              setPreview(null);
            }}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
              operationType === 'filter_records'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            Filter Records
          </button>
        </div>

        {/* Form Fields according to operation */}
        {operationType === 'derive_column' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">New Target Column Name</label>
              <input
                type="text"
                value={targetColumn}
                onChange={(e) => setTargetColumn(e.target.value)}
                placeholder="e.g. company_domain"
                className="w-full text-xs border border-slate-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">Transformation Strategy</label>
              <select
                value={exprType}
                onChange={(e) => setExprType(e.target.value)}
                className="w-full text-xs border border-slate-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-indigo-500"
              >
                <option value="extract_domain">Extract Domain from URL</option>
                <option value="combine_text">Combine Multiple Columns</option>
                <option value="split_text">Split Text Column</option>
                <option value="math_op">Math Operation (e.g. x 12)</option>
              </select>
            </div>

            {exprType === 'extract_domain' && (
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 mb-1">Source URL Column</label>
                <select
                  value={sourceColumn}
                  onChange={(e) => setSourceColumn(e.target.value)}
                  className="w-full text-xs border border-slate-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Select column...</option>
                  {columns.map((c) => (
                    <option key={c.column_name} value={c.column_name}>
                      {c.column_name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {exprType === 'combine_text' && (
              <div className="col-span-1 md:col-span-2 grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 mb-1">Source Columns (comma-separated)</label>
                  <input
                    type="text"
                    placeholder="e.g. job_title, company_name"
                    value={sourceColumnsMulti.join(', ')}
                    onChange={(e) => setSourceColumnsMulti(e.target.value.split(',').map((s) => s.trim()))}
                    className="w-full text-xs border border-slate-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 mb-1">Delimiter</label>
                  <input
                    type="text"
                    value={delimiter}
                    onChange={(e) => setDelimiter(e.target.value)}
                    placeholder="e.g. ' at ' or ' - '"
                    className="w-full text-xs border border-slate-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {operationType === 'rename_column' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">Select Column to Rename</label>
              <select
                value={oldName}
                onChange={(e) => setOldName(e.target.value)}
                className="w-full text-xs border border-slate-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Select column...</option>
                {columns.map((c) => (
                  <option key={c.column_name} value={c.column_name}>
                    {c.column_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">New Column Name</label>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="e.g. location_normalized"
                className="w-full text-xs border border-slate-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
        )}

        {operationType === 'filter_records' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">Filter Field</label>
              <select
                value={filterField}
                onChange={(e) => setFilterField(e.target.value)}
                className="w-full text-xs border border-slate-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Select field...</option>
                {columns.map((c) => (
                  <option key={c.column_name} value={c.column_name}>
                    {c.column_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">Operator</label>
              <select
                value={filterOp}
                onChange={(e) => setFilterOp(e.target.value)}
                className="w-full text-xs border border-slate-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-indigo-500"
              >
                <option value="==">Equals (==)</option>
                <option value="!=">Not Equals (!=)</option>
                <option value="contains">Contains Substring</option>
                <option value=">=">Greater Than or Equal (&gt;=)</option>
                <option value="<=">Less Than or Equal (&lt;=)</option>
                <option value="not_null">Is Not Null</option>
              </select>
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">Target Value</label>
              <input
                type="text"
                value={filterVal}
                onChange={(e) => setFilterVal(e.target.value)}
                placeholder="Value to compare..."
                className="w-full text-xs border border-slate-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
        )}

        <div>
          <Button
            onClick={handlePreview}
            disabled={isPreviewing}
            size="sm"
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs gap-1.5"
          >
            {isPreviewing ? <Spinner size="sm" /> : <Sparkles className="w-3.5 h-3.5" />}
            Preview Transformation
          </Button>
        </div>

        {successMsg && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs font-semibold text-emerald-800 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}
      </div>

      {/* Preview Card */}
      {preview && (
        <div className="bg-white rounded-xl border border-indigo-200 p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-slate-900">Transformation Preview</h4>
            <span className="text-xs font-bold px-3 py-1 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
              {preview.records_affected} Records Affected
            </span>
          </div>

          {/* Sample Diffs */}
          {preview.samples && preview.samples.length > 0 && (
            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-700">Sample Results:</span>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {preview.samples.map((s, idx) => (
                  <div key={idx} className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-1.5">
                    <div className="text-[10px] font-bold text-slate-400">Sample #{idx + 1}</div>
                    {s.transformed && (
                      <div className="text-emerald-700 font-medium">
                        <span className="text-[10px] text-emerald-600 uppercase font-bold mr-1">Generated:</span>
                        <code className="text-[11px] bg-emerald-50 px-1 py-0.5 rounded border border-emerald-100">
                          {JSON.stringify(s.transformed)}
                        </code>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              onClick={() => setPreview(null)}
              className="text-xs font-semibold px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-600"
            >
              Cancel
            </button>
            <Button
              onClick={handleApply}
              disabled={transformApplyMutation.isPending}
              className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs px-5 py-2"
            >
              {transformApplyMutation.isPending ? <Spinner size="sm" /> : <CheckCircle2 className="w-4 h-4 mr-1" />}
              Apply Transformation & Save Version
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
