import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useProject, useDeleteProject } from '../hooks/useProjects';
import { useDatasets, useDeleteDataset } from '../hooks/useDatasets';
import { useWorkflows } from '../hooks/useWorkflows';
import { StatusBadge } from '../components/common/StatusBadge';
import { DatasetTable } from '../features/datasets/DatasetTable';
import { CreateDatasetModal } from '../features/datasets/CreateDatasetModal';
import { EditDatasetModal } from '../features/datasets/EditDatasetModal';
import { DatasetDetailsModal } from '../features/datasets/DatasetDetailsModal';
import { EditProjectModal } from '../features/projects/EditProjectModal';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { WorkflowRunsTable } from '../features/dashboard/WorkflowRunsTable';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Spinner } from '../components/ui/Spinner';
import { EmptyState } from '../components/ui/EmptyState';
import { useToast } from '../components/ui/Toast';
import { formatDate } from '../../lib/utils';
import { Project } from '../types/project';
import { Dataset } from '../types/dataset';
import {
  ArrowLeft,
  Database,
  Workflow,
  Plus,
  Edit2,
  Trash2,
  Calendar,
  Layers,
} from 'lucide-react';

export function ProjectDetailsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { success, error: showError } = useToast();

  const [activeTab, setActiveTab] = useState<'datasets' | 'workflows'>('datasets');

  // Modals state
  const [createDatasetOpen, setCreateDatasetOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [deletingProject, setDeletingProject] = useState<Project | null>(null);
  const [viewingDataset, setViewingDataset] = useState<Dataset | null>(null);
  const [editingDataset, setEditingDataset] = useState<Dataset | null>(null);
  const [deletingDataset, setDeletingDataset] = useState<Dataset | null>(null);

  // Queries
  const { data: project, isLoading: projectLoading } = useProject(projectId);
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
                <Database className="w-3.5 h-3.5 text-indigo-500" />
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
          <div className="flex items-center gap-2 flex-shrink-0">
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
              variant="primary"
              size="sm"
              onClick={() => setCreateDatasetOpen(true)}
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Add Dataset
            </Button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-6">
          <button
            onClick={() => setActiveTab('datasets')}
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
            onClick={() => setActiveTab('workflows')}
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

      {/* Tab Contents */}
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
