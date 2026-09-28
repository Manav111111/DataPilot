import React, { useState } from 'react';
import { useProjects, useDeleteProject } from '../hooks/useProjects';
import { ProjectCard } from '../features/projects/ProjectCard';
import { CreateProjectModal } from '../features/projects/CreateProjectModal';
import { EditProjectModal } from '../features/projects/EditProjectModal';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { SearchBar } from '../components/common/SearchBar';
import { Pagination } from '../components/common/Pagination';
import { EmptyState } from '../components/ui/EmptyState';
import { Spinner } from '../components/ui/Spinner';
import { Button } from '../components/ui/Button';
import { Select } from '../components/ui/Select';
import { useToast } from '../components/ui/Toast';
import { Project } from '../types/project';
import { FolderKanban, Plus, Filter } from 'lucide-react';

export function ProjectsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [deletingProject, setDeletingProject] = useState<Project | null>(null);

  const { data, isLoading } = useProjects({
    page,
    size: 12,
    search: search || undefined,
    status: statusFilter || undefined,
  });

  const { mutateAsync: deleteProject, isPending: isDeleting } = useDeleteProject();
  const { success, error: showError } = useToast();

  const handleDeleteConfirm = async () => {
    if (!deletingProject) return;
    try {
      await deleteProject(deletingProject.id);
      success(`Project "${deletingProject.name}" deleted.`);
      setDeletingProject(null);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to delete project';
      showError(msg);
    }
  };

  const handleSearchChange = (val: string) => {
    setSearch(val);
    setPage(1);
  };

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setStatusFilter(e.target.value);
    setPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">
            Projects
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Manage your structured data intelligence projects and workflows.
          </p>
        </div>
        <Button
          variant="primary"
          size="md"
          onClick={() => setCreateModalOpen(true)}
        >
          <Plus className="w-4 h-4 mr-1.5" />
          Create Project
        </Button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="flex-1 w-full">
          <SearchBar
            value={search}
            onChange={handleSearchChange}
            placeholder="Search projects by name or description..."
          />
        </div>
        <div className="w-full sm:w-48">
          <select
            value={statusFilter}
            onChange={handleStatusChange}
            className="flex h-10 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
          >
            <option value="">All Statuses</option>
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {/* Main Content */}
      {isLoading ? (
        <div className="py-20 flex justify-center">
          <Spinner size="lg" />
        </div>
      ) : !data?.items || data.items.length === 0 ? (
        <EmptyState
          icon={FolderKanban}
          title={search || statusFilter ? 'No matching projects found' : 'No projects created yet'}
          description={
            search || statusFilter
              ? 'Try changing your search terms or clearing the status filter.'
              : 'Create your first project to start organizing data schemas and autonomous workflows.'
          }
          actionLabel={search || statusFilter ? undefined : 'Create First Project'}
          onAction={search || statusFilter ? undefined : () => setCreateModalOpen(true)}
          actionIcon={Plus}
        />
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {data.items.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onEdit={(p) => setEditingProject(p)}
                onDelete={(p) => setDeletingProject(p)}
              />
            ))}
          </div>

          {/* Pagination */}
          <Pagination
            currentPage={page}
            totalPages={data.pages}
            totalItems={data.total}
            pageSize={12}
            onPageChange={(newPage) => setPage(newPage)}
          />
        </div>
      )}

      {/* Modals & Dialogs */}
      <CreateProjectModal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
      />

      <EditProjectModal
        project={editingProject}
        isOpen={!!editingProject}
        onClose={() => setEditingProject(null)}
      />

      <ConfirmDialog
        isOpen={!!deletingProject}
        onClose={() => setDeletingProject(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete Project"
        message={`Are you sure you want to delete "${deletingProject?.name}"? All associated datasets and workflow history will be permanently removed.`}
        confirmText="Delete Project"
        variant="destructive"
        isLoading={isDeleting}
      />
    </div>
  );
}
