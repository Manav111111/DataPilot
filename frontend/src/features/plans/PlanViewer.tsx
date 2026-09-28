import React, { useState } from 'react';
import {
  CollectionPlan,
  CollectionPlanData,
  FieldDefinition,
  SearchQuery,
  PlanStatus,
} from '../../types/plan';
import { StatusBadge } from '../../components/common/StatusBadge';
import { EditableFieldBuilder } from './EditableFieldBuilder';
import { SearchQueryEditor } from './SearchQueryEditor';
import { SourceRecommendationPanel } from './SourceRecommendationPanel';
import { QualityRulesPanel } from './QualityRulesPanel';
import { ClarificationPanel } from './ClarificationPanel';
import { ConfirmDialog } from '../../components/common/ConfirmDialog';
import { Modal } from '../../components/ui/Modal';
import { Textarea } from '../../components/ui/Textarea';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { useUpdatePlan, useApprovePlan, useRejectPlan, useRegeneratePlan } from '../../hooks/usePlans';
import { useToast } from '../../components/ui/Toast';
import { formatDate, formatNumber } from '../../lib/utils';
import {
  Sparkles,
  Bot,
  Save,
  CheckCircle2,
  XCircle,
  RotateCcw,
  Layers,
  AlertTriangle,
  Info,
  Calendar,
  MapPin,
  Tag,
  Hash,
} from 'lucide-react';

interface PlanViewerProps {
  plan: CollectionPlan;
  onClose?: () => void;
  onPlanUpdated?: (plan: CollectionPlan) => void;
}

export function PlanViewer({ plan, onClose, onPlanUpdated }: PlanViewerProps) {
  const [currentPlan, setCurrentPlan] = useState<CollectionPlan>(plan);
  const [activeTab, setActiveTab] = useState<'fields' | 'queries' | 'sources' | 'quality' | 'steps'>('fields');

  // Modal dialog states
  const [approveConfirmOpen, setApproveConfirmOpen] = useState(false);
  const [rejectConfirmOpen, setRejectConfirmOpen] = useState(false);
  const [regenerateModalOpen, setRegenerateModalOpen] = useState(false);
  const [feedbackText, setFeedbackText] = useState('');

  // Mutations
  const { mutateAsync: updatePlanMutation, isPending: isUpdating } = useUpdatePlan();
  const { mutateAsync: approvePlanMutation, isPending: isApproving } = useApprovePlan();
  const { mutateAsync: rejectPlanMutation, isPending: isRejecting } = useRejectPlan();
  const { mutateAsync: regeneratePlanMutation, isPending: isRegenerating } = useRegeneratePlan();

  const { success, error: showError } = useToast();

  const planData: CollectionPlanData = currentPlan.plan_data;
  const isApproved = currentPlan.status === 'approved';
  const isRejected = currentPlan.status === 'rejected';
  const isReadOnly = isApproved || isRejected;

  const handleFieldsChange = (newFields: FieldDefinition[]) => {
    setCurrentPlan((prev) => ({
      ...prev,
      plan_data: {
        ...prev.plan_data,
        fields: newFields,
      },
    }));
  };

  const handleQueriesChange = (newQueries: SearchQuery[]) => {
    setCurrentPlan((prev) => ({
      ...prev,
      plan_data: {
        ...prev.plan_data,
        search_queries: newQueries,
      },
    }));
  };

  const handleSaveChanges = async () => {
    try {
      const updated = await updatePlanMutation({
        planId: currentPlan.id,
        payload: {
          goal: planData.goal,
          entity_type: planData.entity_type,
          geography: planData.geography,
          target_record_count: planData.target_record_count,
          fields: planData.fields,
          search_queries: planData.search_queries,
          quality_rules: planData.quality_rules,
          source_recommendations: planData.source_recommendations,
        },
      });
      setCurrentPlan(updated);
      success('Plan changes saved successfully.');
      onPlanUpdated?.(updated);
    } catch (err: any) {
      showError(err.response?.data?.detail || 'Failed to save changes');
    }
  };

  const handleApprove = async () => {
    try {
      const updated = await approvePlanMutation(currentPlan.id);
      setCurrentPlan(updated);
      setApproveConfirmOpen(false);
      success('Plan approved successfully! Data collection will be available in Phase 3.');
      onPlanUpdated?.(updated);
    } catch (err: any) {
      showError(err.response?.data?.detail || 'Failed to approve plan');
    }
  };

  const handleReject = async () => {
    try {
      const updated = await rejectPlanMutation(currentPlan.id);
      setCurrentPlan(updated);
      setRejectConfirmOpen(false);
      success('Plan rejected.');
      onPlanUpdated?.(updated);
    } catch (err: any) {
      showError(err.response?.data?.detail || 'Failed to reject plan');
    }
  };

  const handleRegenerate = async () => {
    try {
      const updated = await regeneratePlanMutation({
        planId: currentPlan.id,
        payload: {
          feedback: feedbackText || undefined,
        },
      });
      setCurrentPlan(updated);
      setRegenerateModalOpen(false);
      setFeedbackText('');
      success('Plan regenerated with your feedback.');
      onPlanUpdated?.(updated);
    } catch (err: any) {
      showError(err.response?.data?.detail || 'Failed to regenerate plan');
    }
  };

  const handleClarificationAnswers = async (answers: Record<string, string>) => {
    try {
      const updated = await regeneratePlanMutation({
        planId: currentPlan.id,
        payload: {
          clarification_answers: answers,
        },
      });
      setCurrentPlan(updated);
      success('Clarification answers applied and plan regenerated.');
      onPlanUpdated?.(updated);
    } catch (err: any) {
      showError(err.response?.data?.detail || 'Failed to apply clarification answers');
    }
  };

  return (
    <div className="space-y-6">
      {/* Plan Header Card */}
      <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-card space-y-4">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div className="space-y-1.5 flex-1 min-w-0">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-indigo-50 text-indigo-600 flex-shrink-0">
                <Sparkles className="w-5 h-5" />
              </div>
              <h3 className="text-lg sm:text-xl font-bold text-slate-900 truncate">
                {planData.goal || 'Data Collection Plan'}
              </h3>
              <StatusBadge status={currentPlan.status} />
            </div>

            {/* Original user prompt callout */}
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 text-xs text-slate-700 italic mt-2">
              <span className="font-semibold not-italic text-slate-500 mr-1.5">
                Original Request:
              </span>
              "{currentPlan.original_request}"
            </div>

            {/* Metadata badges */}
            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 pt-2">
              <span className="flex items-center gap-1.5 font-medium text-slate-700">
                <Tag className="w-3.5 h-3.5 text-indigo-500" />
                Entity: <strong>{planData.entity_type}</strong>
              </span>
              <span>•</span>
              <span className="flex items-center gap-1.5 font-medium text-slate-700">
                <MapPin className="w-3.5 h-3.5 text-emerald-500" />
                Geography: <strong>{planData.geography || 'Global'}</strong>
              </span>
              <span>•</span>
              <span className="flex items-center gap-1.5 font-medium text-slate-700">
                <Hash className="w-3.5 h-3.5 text-sky-500" />
                Target: <strong>{formatNumber(planData.target_record_count)} records</strong>
              </span>
              <span>•</span>
              <span className="flex items-center gap-1.5 text-slate-400">
                <Calendar className="w-3.5 h-3.5" />
                Created {formatDate(currentPlan.created_at)}
              </span>
            </div>
          </div>

          {/* Action Toolbar */}
          <div className="flex flex-wrap items-center gap-2 flex-shrink-0">
            {!isReadOnly && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSaveChanges}
                  isLoading={isUpdating}
                >
                  <Save className="w-3.5 h-3.5 mr-1" />
                  Save Changes
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setRegenerateModalOpen(true)}
                >
                  <RotateCcw className="w-3.5 h-3.5 mr-1" />
                  Regenerate
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => setRejectConfirmOpen(true)}
                >
                  <XCircle className="w-3.5 h-3.5 mr-1" />
                  Reject
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setApproveConfirmOpen(true)}
                  disabled={currentPlan.status === 'needs_clarification'}
                >
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                  Approve Plan
                </Button>
              </>
            )}
          </div>
        </div>

        {/* Status Callout Banner */}
        {isApproved && (
          <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-900 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
              <div>
                <strong className="block font-semibold">Plan Approved for Pipeline Execution</strong>
                <span>Data collection workflows and autonomous extraction will be executed in Phase 3.</span>
              </div>
            </div>
          </div>
        )}

        {isRejected && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-900 flex items-center gap-2.5">
            <XCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
            <div>
              <strong className="block font-semibold">Plan Rejected</strong>
              <span>You can regenerate or create a new plan with revised criteria.</span>
            </div>
          </div>
        )}
      </div>

      {/* Clarification Questions Panel (if needed) */}
      {currentPlan.status === 'needs_clarification' && planData.clarification_questions?.length > 0 && (
        <ClarificationPanel
          questions={planData.clarification_questions}
          onSubmitAnswers={handleClarificationAnswers}
          isLoading={isRegenerating}
        />
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-6">
          <button
            onClick={() => setActiveTab('fields')}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
              activeTab === 'fields'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Field Schema ({planData.fields?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('queries')}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
              activeTab === 'queries'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Search Queries ({planData.search_queries?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('sources')}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
              activeTab === 'sources'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Recommended Sources ({planData.source_recommendations?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('quality')}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
              activeTab === 'quality'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Quality & Deduplication ({planData.quality_rules?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('steps')}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
              activeTab === 'steps'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Workflow Steps & Limits
          </button>
        </nav>
      </div>

      {/* Tab Panels */}
      <div>
        {activeTab === 'fields' && (
          <EditableFieldBuilder
            fields={planData.fields || []}
            onChange={handleFieldsChange}
            disabled={isReadOnly}
          />
        )}

        {activeTab === 'queries' && (
          <SearchQueryEditor
            queries={planData.search_queries || []}
            onChange={handleQueriesChange}
            disabled={isReadOnly}
          />
        )}

        {activeTab === 'sources' && (
          <SourceRecommendationPanel
            sources={planData.source_recommendations || []}
          />
        )}

        {activeTab === 'quality' && (
          <QualityRulesPanel rules={planData.quality_rules || []} />
        )}

        {activeTab === 'steps' && (
          <div className="space-y-4">
            {/* Execution Steps */}
            <Card>
              <CardHeader className="pb-3 border-b border-slate-100">
                <CardTitle>Phase 3 Pipeline Execution Steps</CardTitle>
              </CardHeader>
              <CardContent className="p-4 space-y-2">
                {planData.execution_steps?.map((step, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-2.5 p-2.5 rounded-lg bg-slate-50 text-xs text-slate-800"
                  >
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-indigo-100 text-indigo-700 font-bold text-[10px] flex-shrink-0">
                      {idx + 1}
                    </span>
                    <span>{step}</span>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Assumptions and Limitations */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader className="pb-2 border-b border-slate-100">
                  <CardTitle className="text-sm font-bold flex items-center gap-1.5 text-slate-900">
                    <Info className="w-4 h-4 text-indigo-500" />
                    Planning Assumptions
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-4 text-xs text-slate-600 space-y-1.5">
                  {planData.assumptions?.map((item, idx) => (
                    <li key={idx} className="list-disc list-inside">
                      {item}
                    </li>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2 border-b border-slate-100">
                  <CardTitle className="text-sm font-bold flex items-center gap-1.5 text-slate-900">
                    <AlertTriangle className="w-4 h-4 text-amber-500" />
                    Data Availability Limitations
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-4 text-xs text-slate-600 space-y-1.5">
                  {planData.limitations?.map((item, idx) => (
                    <li key={idx} className="list-disc list-inside">
                      {item}
                    </li>
                  ))}
                </CardContent>
              </Card>
            </div>
          </div>
        )}
      </div>

      {/* Confirmation & Regenerate Modals */}
      <ConfirmDialog
        isOpen={approveConfirmOpen}
        onClose={() => setApproveConfirmOpen(false)}
        onConfirm={handleApprove}
        title="Approve Data Collection Plan"
        message="Approving this plan locks in the schema and search strategy. Real-world scraping and autonomous collection workflows will be executed in Phase 3."
        confirmText="Approve Plan"
        variant="primary"
        isLoading={isApproving}
      />

      <ConfirmDialog
        isOpen={rejectConfirmOpen}
        onClose={() => setRejectConfirmOpen(false)}
        onConfirm={handleReject}
        title="Reject Plan"
        message="Are you sure you want to reject this plan? You can regenerate a new plan at any time."
        confirmText="Reject Plan"
        variant="destructive"
        isLoading={isRejecting}
      />

      <Modal
        isOpen={regenerateModalOpen}
        onClose={() => setRegenerateModalOpen(false)}
        title="Regenerate Plan with Feedback"
        description="Instruct the AI planner with specific corrections or refinements."
      >
        <div className="space-y-4">
          <Textarea
            label="Feedback or Custom Instructions"
            placeholder="e.g. Please include salary range as required, and add queries for Hyderabad and Chennai."
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            className="min-h-[100px]"
          />
          <div className="flex justify-end space-x-3 pt-3 border-t border-slate-100">
            <Button
              variant="outline"
              onClick={() => setRegenerateModalOpen(false)}
              disabled={isRegenerating}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleRegenerate}
              isLoading={isRegenerating}
            >
              Regenerate Plan
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
