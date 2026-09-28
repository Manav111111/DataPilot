import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useDashboardStats } from '../hooks/useDashboard';
import { MetricCard } from '../components/common/MetricCard';
import { RecentProjectsList } from '../features/dashboard/RecentProjectsList';
import { RecentDatasetsList } from '../features/dashboard/RecentDatasetsList';
import { WorkflowRunsTable } from '../features/dashboard/WorkflowRunsTable';
import { CreateProjectModal } from '../features/projects/CreateProjectModal';
import { CreateDatasetModal } from '../features/datasets/CreateDatasetModal';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Spinner } from '../components/ui/Spinner';
import {
  FolderKanban,
  Database,
  CheckCircle2,
  XCircle,
  Plus,
  ArrowUpRight,
  Sparkles,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export function DashboardPage() {
  const { user } = useAuth();
  const { data: stats, isLoading } = useDashboardStats();

  const [createProjectOpen, setCreateProjectOpen] = useState(false);
  const [createDatasetOpen, setCreateDatasetOpen] = useState(false);

  if (isLoading && !stats) {
    return (
      <div className="py-20 flex justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome & Quick Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-200/80">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">
            Welcome back, {user?.name || 'Engineer'}
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Here is the current state of your data intelligence environment.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCreateDatasetOpen(true)}
          >
            <Plus className="w-4 h-4 mr-1.5 text-slate-500" />
            New Dataset
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setCreateProjectOpen(true)}
          >
            <Plus className="w-4 h-4 mr-1.5" />
            New Project
          </Button>
        </div>
      </div>

      {/* KPI Overview Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Projects"
          value={stats?.total_projects ?? 0}
          subtitle={`${stats?.active_projects ?? 0} actively configured`}
          icon={FolderKanban}
          iconColorClass="text-indigo-600"
          bgColorClass="bg-indigo-50"
        />
        <MetricCard
          title="Total Datasets"
          value={stats?.total_datasets ?? 0}
          subtitle={`${stats?.total_rows ?? 0} total rows collected`}
          icon={Database}
          iconColorClass="text-sky-600"
          bgColorClass="bg-sky-50"
        />
        <MetricCard
          title="Completed Workflows"
          value={stats?.completed_workflows ?? 0}
          subtitle="Successful collection pipelines"
          icon={CheckCircle2}
          iconColorClass="text-emerald-600"
          bgColorClass="bg-emerald-50"
        />
        <MetricCard
          title="Failed Workflows"
          value={stats?.failed_workflows ?? 0}
          subtitle="Pipeline error alerts"
          icon={XCircle}
          iconColorClass="text-rose-600"
          bgColorClass="bg-rose-50"
        />
      </div>

      {/* Activity Grid (Recent Projects + Recent Datasets) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Projects */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <CardTitle>Recent Projects</CardTitle>
              <CardDescription>Latest data projects and structures</CardDescription>
            </div>
            <Link
              to="/projects"
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
            >
              View all <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            <RecentProjectsList
              projects={stats?.recent_projects || []}
              onCreateNew={() => setCreateProjectOpen(true)}
            />
          </CardContent>
        </Card>

        {/* Recent Datasets */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <CardTitle>Recent Datasets</CardTitle>
              <CardDescription>Structured dataset tables and records</CardDescription>
            </div>
            <Link
              to="/datasets"
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
            >
              View all <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            <RecentDatasetsList
              datasets={stats?.recent_datasets || []}
              onCreateNew={() => setCreateDatasetOpen(true)}
            />
          </CardContent>
        </Card>
      </div>

      {/* Workflow Runs Section */}
      <Card>
        <CardHeader className="pb-3 border-b border-slate-100">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Workflow Execution History</CardTitle>
              <CardDescription>
                Autonomous extraction runs, status, and completion timestamps
              </CardDescription>
            </div>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 text-[11px] font-medium text-slate-600">
              <Sparkles className="w-3 h-3 text-indigo-600" />
              <span>Phase 1 Baseline</span>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-4 sm:p-6">
          <WorkflowRunsTable workflows={stats?.recent_workflows || []} />
        </CardContent>
      </Card>

      {/* Modals */}
      <CreateProjectModal
        isOpen={createProjectOpen}
        onClose={() => setCreateProjectOpen(false)}
      />
      <CreateDatasetModal
        isOpen={createDatasetOpen}
        onClose={() => setCreateDatasetOpen(false)}
      />
    </div>
  );
}
