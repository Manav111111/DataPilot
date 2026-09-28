import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useProject, useDeleteProject } from '../hooks/useProjects';
import { useDatasets, useDeleteDataset } from '../hooks/useDatasets';
import { useWorkflows } from '../hooks/useWorkflows';
import { useProjectPlans } from '../hooks/usePlans';
import { StatusBadge } from '../components/common/StatusBadge';
import { DatasetTable } from '../features/datasets/DatasetTable';
import { CreateDatasetModal } from '../features/datasets/CreateDatasetModal';
import { EditDatasetModal } from '../features/datasets/EditDatasetModal';
import { DatasetDetailsModal } from '../features/datasets/DatasetDetailsModal';
import { EditProjectModal } from '../features/projects/EditProjectModal';
import { CreatePlanModal } from '../features/plans/CreatePlanModal';
import { PlanCard } from '../features/plans/PlanCard';
import { PlanViewer } from '../features/plans/PlanViewer';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { WorkflowRunsTable } from '../features/dashboard/WorkflowRunsTable';
import { Button } from '../components/ui/Button';
import { Spinner } from '../components/ui/Spinner';
import { EmptyState } from '../components/ui/EmptyState';
import { useToast } from '../components/ui/Toast';
import { formatDate } from '../lib/utils';
import { Project } from '../types/project';
import { Dataset } from '../types/dataset';
import { CollectionPlan } from '../types/plan';
import {
  ArrowLeft,
  Database,
  Workflow,
  Plus,
  Edit2,
  Trash2,
  Calendar,
  Sparkles,
} from 'lucide-react';

export function ProjectDetailsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { success, error: showError } = useToast();

  const [activeTab, setActiveTab] = useState<'plans' | 'datasets' | 'workflows'>('plans');

  // Modals & review state
  const [createDatasetOpen, setCreateDatasetOpen] = useState(false);
  const [createPlanOpen, setCreatePlanOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<CollectionPlan | null>(null);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [deletingProject, setDeletingProject] = useState<Project | null>(null);
  const [viewingDataset, setViewingDataset] = useState<Dataset | null>(null);
  const [editingDataset, setEditingDataset] = useState<Dataset | null>(null);
  const [deletingDataset, setDeletingDataset] = useState<Dataset | null>(null);

  // Queries
  const { data: project, isLoading: projectLoading } = useProject(projectId);
  const { data: plansData, isLoading: plansLoading, refetch: refetchPlans } = useProjectPlans(projectId);
  const { data: datasetsData, isLoading: datasetsLoading } = useDatasets({
    project_id: projectId,
    size: 50,
  });
  const { data: workflowsData, isLoading: workflowsLoading } = useWorkflows({
    project_id: projectId,
    size: 50,
  });

  // Mutations
  const { mutateAsync: deleteProjectMutation, isPending: isDeletingProj } = useDeleteProject();
  const { mutateAsync: deleteDatasetMutation, isPending: isDeletingDs } = useDeleteDataset();

  const handleDeleteProject = async () => {
    if (!project) return;
    try {
      await deleteProjectMutation(project.id);
      success('Project deleted successfully.');
      navigate('/projects');
    } catch (err: any) {
      showError(err.response?.data?.detail || 'Failed to delete project');
    }
  };

  const handleDeleteDataset = async () => {
    if (!deletingDataset) return;
    try {
      await deleteDatasetMutation(deletingDataset.id);
      success(`Dataset "${deletingDataset.name}" deleted.`);
      setDeletingDataset(null);
    } catch (err: any) {
      showError(err.response?.data?.detail || 'Failed to delete dataset');
    }
  };

  const handlePlanGenerated = (newPlan: CollectionPlan) => {
    refetchPlans();
    setSelectedPlan(newPlan);
    setActiveTab('plans');
  };

  if (projectLoading) {
    return (
      <div className="py-20 flex justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="py-12 text-center">
        <h3 className="text-lg font-bold text-slate-900">Project Not Found</h3>
        <p className="text-xs text-slate-500 mt-1 mb-4">
          The requested project does not exist or has been deleted.
        </p>
        <Link to="/projects">
          <Button variant="primary" size="sm">
            Back to Projects
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div>
        <Link
          to="/projects"
          className="inline-flex items-center text-xs font-medium text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5 mr-1" />
          Back to Projects
        </Link>
      </div>

      {/* Project Banner & Details */}
      <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-card">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-1.5 flex-1 min-w-0">
            <div className="flex items-center gap-3">
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 truncate">
                {project.name}
              </h2>
              <StatusBadge status={project.status} />
            </div>
            <p className="text-xs sm:text-sm text-slate-600 max-w-3xl">
              {project.description || 'No description added for this project.'}
            </p>
            <div className="flex items-center gap-4 text-xs text-slate-400 pt-2">
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5" />
                Created {formatDate(project.created_at)}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
                {plansData?.total ?? 0} AI Plans
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Database className="w-3.5 h-3.5 text-blue-500" />
                {project.dataset_count ?? 0} Datasets
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Workflow className="w-3.5 h-3.5 text-purple-500" />
                {project.workflow_count ?? 0} Runs
              </span>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2 flex-shrink-0 flex-wrap">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setEditingProject(project)}
            >
              <Edit2 className="w-3.5 h-3.5 mr-1.5" />
              Edit
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => setDeletingProject(project)}
            >
              <Trash2 className="w-3.5 h-3.5 mr-1.5" />
              Delete
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCreateDatasetOpen(true)}
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Add Dataset
            </Button>
            <Button
              variant="primary"
              size="sm"
              className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white shadow-sm"
              onClick={() => setCreatePlanOpen(true)}
            >
              <Sparkles className="w-3.5 h-3.5 mr-1.5" />
              Create AI Plan
            </Button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-6">
          <button
            onClick={() => {
              setActiveTab('plans');
              setSelectedPlan(null);
            }}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === 'plans'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            AI Data Plans ({plansData?.total ?? 0})
          </button>
          <button
            onClick={() => {
              setActiveTab('datasets');
              setSelectedPlan(null);
            }}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === 'datasets'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Database className="w-4 h-4" />
            Datasets ({datasetsData?.total ?? 0})
          </button>
          <button
            onClick={() => {
              setActiveTab('workflows');
              setSelectedPlan(null);
            }}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === 'workflows'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Workflow className="w-4 h-4" />
            Workflow Runs ({workflowsData?.total ?? 0})
          </button>
        </nav>
      </div>

      {/* Tab Contents: AI Plans */}
      {activeTab === 'plans' && (
        <div className="space-y-4">
          {selectedPlan ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <button
                  onClick={() => setSelectedPlan(null)}
                  className="inline-flex items-center text-xs font-semibold text-slate-600 hover:text-indigo-600 transition-colors"
                >
                  <ArrowLeft className="w-3.5 h-3.5 mr-1" />
                  Back to all AI Plans
                </button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCreatePlanOpen(true)}
                >
                  <Plus className="w-3.5 h-3.5 mr-1" />
                  New Plan
                </Button>
              </div>
              <PlanViewer
                plan={selectedPlan}
                onClose={() => setSelectedPlan(null)}
                onPlanUpdated={(updated) => setSelectedPlan(updated)}
              />
            </div>
          ) : plansLoading ? (
            <div className="py-12 flex justify-center">
              <Spinner size="md" />
            </div>
          ) : !plansData?.items || plansData.items.length === 0 ? (
            <EmptyState
              icon={Sparkles}
              title="No AI Data Plans created yet"
              description="Describe what data you need in natural language. Our AI planner will construct structured schemas, queries, and extraction rules."
              actionLabel="Create AI Data Plan"
              onAction={() => setCreatePlanOpen(true)}
              actionIcon={Plus}
            />
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-xs text-slate-500">
                  Showing <strong>{plansData.items.length}</strong> collection plan{plansData.items.length === 1 ? '' : 's'}
                </p>
                <Button
                  variant="primary"
                  size="sm"
                  className="bg-indigo-600 hover:bg-indigo-700"
                  onClick={() => setCreatePlanOpen(true)}
                >
                  <Plus className="w-3.5 h-3.5 mr-1" />
                  Create AI Plan
                </Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {plansData.items.map((plan) => (
                  <PlanCard
                    key={plan.id}
                    plan={plan}
                    onOpenPlan={(p) => setSelectedPlan(p)}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab Contents: Datasets */}
      {activeTab === 'datasets' && (
        <div className="space-y-4">
          {datasetsLoading ? (
            <div className="py-12 flex justify-center">
              <Spinner size="md" />
            </div>
          ) : !datasetsData?.items || datasetsData.items.length === 0 ? (
            <EmptyState
              icon={Database}
              title="No datasets in this project yet"
              description="Datasets contain the structured entities, records, and extracted schemas."
              actionLabel="Create Dataset"
              onAction={() => setCreateDatasetOpen(true)}
              actionIcon={Plus}
            />
          ) : (
            <DatasetTable
              datasets={datasetsData.items}
              onView={(d) => setViewingDataset(d)}
              onEdit={(d) => setEditingDataset(d)}
              onDelete={(d) => setDeletingDataset(d)}
            />
          )}
        </div>
      )}

      {/* Tab Contents: Workflow Runs */}
      {activeTab === 'workflows' && (
        <div className="space-y-4">
          {workflowsLoading ? (
            <div className="py-12 flex justify-center">
              <Spinner size="md" />
            </div>
          ) : (
            <WorkflowRunsTable workflows={workflowsData?.items || []} />
          )}
        </div>
      )}

      {/* Modals */}
      <CreatePlanModal
        isOpen={createPlanOpen}
        onClose={() => setCreatePlanOpen(false)}
        projectId={project.id}
        onPlanGenerated={handlePlanGenerated}
      />

      <CreateDatasetModal
        isOpen={createDatasetOpen}
        onClose={() => setCreateDatasetOpen(false)}
        defaultProjectId={project.id}
      />

      <EditDatasetModal
        dataset={editingDataset}
        isOpen={!!editingDataset}
        onClose={() => setEditingDataset(null)}
      />

      <DatasetDetailsModal
        dataset={viewingDataset}
        isOpen={!!viewingDataset}
        onClose={() => setViewingDataset(null)}
        onEdit={(d) => setEditingDataset(d)}
      />

      <EditProjectModal
        project={editingProject}
        isOpen={!!editingProject}
        onClose={() => setEditingProject(null)}
      />

      <ConfirmDialog
        isOpen={!!deletingProject}
        onClose={() => setDeletingProject(null)}
        onConfirm={handleDeleteProject}
        title="Delete Project"
        message={`Are you sure you want to delete "${project.name}"? This action cannot be undone.`}
        confirmText="Delete Project"
        variant="destructive"
        isLoading={isDeletingProj}
      />

      <ConfirmDialog
        isOpen={!!deletingDataset}
        onClose={() => setDeletingDataset(null)}
        onConfirm={handleDeleteDataset}
        title="Delete Dataset"
        message={`Are you sure you want to delete dataset "${deletingDataset?.name}"?`}
        confirmText="Delete Dataset"
        variant="destructive"
        isLoading={isDeletingDs}
      />
    </div>
  );
}
