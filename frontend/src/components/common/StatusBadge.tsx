import React from 'react';
import { Badge } from '../ui/Badge';
import { CheckCircle2, Clock, AlertTriangle, XCircle, PlayCircle } from 'lucide-react';

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const normalized = (status || '').toLowerCase();

  switch (normalized) {
    case 'active':
      return (
        <Badge variant="default" className={className}>
          <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 mr-1.5 animate-pulse" />
          Active
        </Badge>
      );
    case 'completed':
      return (
        <Badge variant="success" className={className}>
          <CheckCircle2 className="w-3 h-3 mr-1 text-emerald-600" />
          Completed
        </Badge>
      );
    case 'failed':
      return (
        <Badge variant="destructive" className={className}>
          <XCircle className="w-3 h-3 mr-1 text-rose-600" />
          Failed
        </Badge>
      );
    case 'draft':
      return (
        <Badge variant="secondary" className={className}>
          Draft
        </Badge>
      );
    case 'pending':
      return (
        <Badge variant="warning" className={className}>
          <Clock className="w-3 h-3 mr-1 text-amber-600" />
          Pending
        </Badge>
      );
    case 'processing':
    case 'running':
      return (
        <Badge variant="info" className={className}>
          <PlayCircle className="w-3 h-3 mr-1 text-sky-600 animate-spin" />
          {normalized === 'running' ? 'Running' : 'Processing'}
        </Badge>
      );
    case 'cancelled':
      return (
        <Badge variant="secondary" className={className}>
          Cancelled
        </Badge>
      );
    default:
      return (
        <Badge variant="outline" className={className}>
          {status}
        </Badge>
      );
  }
}
