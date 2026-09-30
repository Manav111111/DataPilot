import React, { useState } from 'react';
import { CollectionPlan } from '../../types/plan';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useStartCollection } from '../../hooks/useCollection';
import { useToast } from '../../components/ui/Toast';
import { formatNumber } from '../../lib/utils';
import {
  Play,
  Database,
  Search,
  Globe,
  ShieldCheck,
  Sparkles,
  Info,
  Loader2,
} from 'lucide-react';

interface StartCollectionModalProps {
  plan: CollectionPlan;
  isOpen: boolean;
  onClose: () => void;
  onJobStarted: (jobId: string, datasetId: string) => void;
}

export function StartCollectionModal({
  plan,
  isOpen,
  onClose,
  onJobStarted,
}: StartCollectionModalProps) {
  const planData = plan.plan_data;
  const { success, error: showError } = useToast();
  const { mutateAsync: startCollectionMutation, isPending } = useStartCollection();

  const [datasetName, setDatasetName] = useState(
    `${planData.goal?.slice(0, 45) || 'Collected Dataset'}`
  );
  const [maxRecords, setMaxRecords] = useState<number>(
    planData.target_record_count || 100
  );
  const [maxQueries, setMaxQueries] = useState<number>(
    planData.search_queries?.length || 10
  );

  const handleStart = async () => {
    try {
      const response = await startCollectionMutation({
        planId: plan.id,
        payload: {
          dataset_name: datasetName || undefined,
          max_records: maxRecords,
          max_queries: maxQueries,
        },
      });
      success('Data collection job started successfully!');
      onClose();
      onJobStarted(response.job_id, response.dataset_id);
    } catch (err: any) {
      showError(err.response?.data?.detail || 'Failed to start collection job');
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Start Autonomous Data Collection"
      description="Launch background search and structured data extraction based on your approved plan."
      maxWidth="2xl"
    >
      <div className="space-y-5">
        {/* Plan Summary Card */}
        <div className="p-4 rounded-xl bg-indigo-50/70 border border-indigo-100 text-xs space-y-2">
          <div className="flex items-center gap-2 text-indigo-900 font-bold text-sm">
            <Sparkles className="w-4 h-4 text-indigo-600" />
            <span>Target Blueprint: {planData.goal}</span>
          </div>
          <div className="grid grid-cols-3 gap-2 pt-2 border-t border-indigo-100 text-indigo-800">
            <div>
              <span className="text-indigo-400 block font-medium">Entity Type</span>
              <strong className="text-xs">{planData.entity_type}</strong>
            </div>
            <div>
              <span className="text-indigo-400 block font-medium">Geography</span>
              <strong className="text-xs">{planData.geography}</strong>
            </div>
            <div>
              <span className="text-indigo-400 block font-medium">Target Rows</span>
              <strong className="text-xs">{formatNumber(maxRecords)} records</strong>
            </div>
          </div>
        </div>

        {/* Configuration inputs */}
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Dataset Name
            </label>
            <Input
              value={datasetName}
              onChange={(e) => setDatasetName(e.target.value)}
              placeholder="e.g. Indian AI Startups Hiring Dataset"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Target Record Count
              </label>
              <Input
                type="number"
                min={1}
                max={5000}
                value={maxRecords}
                onChange={(e) => setMaxRecords(parseInt(e.target.value) || 50)}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Max Search Queries
              </label>
              <Input
                type="number"
                min={1}
                max={30}
                value={maxQueries}
                onChange={(e) => setMaxQueries(parseInt(e.target.value) || 5)}
              />
            </div>
          </div>
        </div>

        {/* Execution Pipeline Steps Preview */}
        <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 text-xs space-y-1.5">
          <div className="font-semibold text-slate-800 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            Execution Workflow:
          </div>
          <ol className="list-decimal list-inside text-slate-600 space-y-1 pl-1">
            <li>Tavily Search discovers verified public URLs from approved queries.</li>
            <li>Firecrawl extracts clean, readable page contents with SSRF checks.</li>
            <li>Configured LLM extracts structured records matching field schemas.</li>
            <li>Validator normalizes data and checks type and required constraints.</li>
            <li>Deduplication engine merges multi-source provenance and saves results.</li>
          </ol>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
          <Button variant="outline" size="sm" onClick={onClose} disabled={isPending}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white shadow-sm gap-1.5"
            onClick={handleStart}
            disabled={isPending}
          >
            {isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Dispatching Job...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                Start Data Collection
              </>
            )}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
