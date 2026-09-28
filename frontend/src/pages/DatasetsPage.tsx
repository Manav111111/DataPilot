import React, { useState } from 'react';
import { useDatasets, useDeleteDataset } from '../hooks/useDatasets';
import { useProjects } from '../hooks/useProjects';
import { DatasetTable } from '../features/datasets/DatasetTable';
import { CreateDatasetModal } from '../features/datasets/CreateDatasetModal';
import { EditDatasetModal } from '../features/datasets/EditDatasetModal';
import { DatasetDetailsModal } from '../features/datasets/DatasetDetailsModal';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { SearchBar } from '../components/common/SearchBar';
import { Pagination } from '../components/common/Pagination';
import { EmptyState } from '../components/ui/EmptyState';
import { Spinner } from '../components/ui/Spinner';
import { Button } from '../components/ui/Button';
import { useToast } from '../components/ui/Toast';
import { Dataset } from '../types/dataset';
import { Database, Plus, Filter } from 'lucide-react';

export function DatasetsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [projectFilter, setProjectFilter] = useState('');

  // Modals state
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [viewingDataset, setViewingDataset] = useState<Dataset | null>(null);
  const [editingDataset, setEditingDataset] = useState<Dataset | null>(null);
  const [deletingDataset, setDeletingDataset] = useState<Dataset | null>(null);

  // Queries
  const { data: projectsData } = useProjects({ size: 100 });
  const { data, isLoading } = useDatasets({
    page,
    size: 15,
    search: search || undefined,
    status: statusFilter || undefined,
    project_id: projectFilter || undefined,
  });

  const { mutateAsync: deleteDataset, isPending: isDeleting } = useDeleteDataset();
  const { success, error: showError } = useToast();

  const handleDeleteConfirm = async () => {
    if (!deletingDataset) return;
    try {
      await deleteDataset(deletingDataset.id);
      success(`Dataset "${deletingDataset.name}" deleted.`);
      setDeletingDataset(null);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to delete dataset';
      showError(msg);
    }
  };

  const handleSearchChange = (val: string) => {
    setSearch(val);
    setPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">
            Datasets
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Unified view of structured tables, rows, and data schemas across projects.
          </p>
        </div>
        <Button
          variant="primary"
          size="md"
          onClick={() => setCreateModalOpen(true)}
        >
          <Plus className="w-4 h-4 mr-1.5" />
          Create Dataset
        </Button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row items-center gap-3">
        <div className="flex-1 w-full">
          <SearchBar
            value={search}
            onChange={handleSearchChange}
            placeholder="Search datasets by name or schema details..."
          />
        </div>

        {/* Project Filter */}
        <div className="w-full md:w-56">
          <select
            value={projectFilter}
            onChange={(e) => {
              setProjectFilter(e.target.value);
              setPage(1);
            }}
            className="flex h-10 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
          >
            <option value="">All Projects</option>
            {projectsData?.items?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        {/* Status Filter */}
        <div className="w-full md:w-44">
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="flex h-10 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="processing">Processing</option>
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
          icon={Database}
          title={search || statusFilter || projectFilter ? 'No matching datasets found' : 'No datasets created yet'}
          description={
            search || statusFilter || projectFilter
              ? 'Try changing or clearing your search and filters.'
              : 'Datasets hold the cleaned records extracted from web sources and workflow pipelines.'
          }
          actionLabel={search || statusFilter || projectFilter ? undefined : 'Create First Dataset'}
          onAction={search || statusFilter || projectFilter ? undefined : () => setCreateModalOpen(true)}
          actionIcon={Plus}
        />
      ) : (
        <div className="space-y-4">
          <DatasetTable
            datasets={data.items}
            onView={(d) => setViewingDataset(d)}
            onEdit={(d) => setEditingDataset(d)}
            onDelete={(d) => setDeletingDataset(d)}
          />

          {/* Pagination */}
          <Pagination
            currentPage={page}
            totalPages={data.pages}
            totalItems={data.total}
            pageSize={15}
            onPageChange={(newPage) => setPage(newPage)}
          />
        </div>
      )}

      {/* Modals & Dialogs */}
      <CreateDatasetModal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
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

      <ConfirmDialog
        isOpen={!!deletingDataset}
        onClose={() => setDeletingDataset(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete Dataset"
        message={`Are you sure you want to delete dataset "${deletingDataset?.name}"?`}
        confirmText="Delete Dataset"
        variant="destructive"
        isLoading={isDeleting}
      />
    </div>
  );
}
