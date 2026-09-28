import React from 'react';
import { Link } from 'react-router-dom';
import { Project } from '../../types/project';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/Card';
import { StatusBadge } from '../../components/common/StatusBadge';
import { formatDate } from '../../lib/utils';
import { Database, Workflow, MoreVertical, Edit2, Trash2, ArrowRight } from 'lucide-react';

interface ProjectCardProps {
  project: Project;
  onEdit: (project: Project) => void;
  onDelete: (project: Project) => void;
}

export function ProjectCard({ project, onEdit, onDelete }: ProjectCardProps) {
  return (
    <Card className="hover:shadow-hover hover:border-slate-300 transition-all duration-200 flex flex-col justify-between group">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <Link
              to={`/projects/${project.id}`}
              className="text-base font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors line-clamp-1"
            >
              {project.name}
            </Link>
            <p className="mt-1 text-xs text-slate-500 line-clamp-2 min-h-[32px]">
              {project.description || 'No description provided.'}
            </p>
          </div>
          <StatusBadge status={project.status} />
        </div>
      </CardHeader>

      <CardContent className="py-2">
        <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100 text-xs text-slate-600">
          <div className="flex items-center gap-1.5 p-2 rounded-lg bg-slate-50">
            <Database className="w-3.5 h-3.5 text-indigo-500" />
            <span>
              <strong className="text-slate-900 font-semibold">
                {project.dataset_count ?? 0}
              </strong>{' '}
              Datasets
            </span>
          </div>
          <div className="flex items-center gap-1.5 p-2 rounded-lg bg-slate-50">
            <Workflow className="w-3.5 h-3.5 text-purple-500" />
            <span>
              <strong className="text-slate-900 font-semibold">
                {project.workflow_count ?? 0}
              </strong>{' '}
              Runs
            </span>
          </div>
        </div>
      </CardContent>

      <CardFooter className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
        <span>Created {formatDate(project.created_at)}</span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => onEdit(project)}
            title="Edit Project"
            className="p-1.5 rounded-md hover:bg-slate-100 text-slate-500 hover:text-slate-700 transition-colors"
          >
            <Edit2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => onDelete(project)}
            title="Delete Project"
            className="p-1.5 rounded-md hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
          <Link
            to={`/projects/${project.id}`}
            className="p-1.5 rounded-md hover:bg-indigo-50 text-indigo-600 transition-colors"
            title="Open Details"
          >
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </CardFooter>
    </Card>
  );
}
