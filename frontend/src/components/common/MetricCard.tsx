import React from 'react';
import { LucideIcon } from 'lucide-react';
import { Card } from '../ui/Card';
import { cn } from '../../lib/utils';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: {
    value: string;
    isPositive?: boolean;
  };
  iconColorClass?: string;
  bgColorClass?: string;
}

export function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  iconColorClass = 'text-indigo-600',
  bgColorClass = 'bg-indigo-50',
}: MetricCardProps) {
  return (
    <Card className="p-5 hover:shadow-hover transition-all duration-200">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          {title}
        </span>
        <div className={cn('p-2.5 rounded-lg flex items-center justify-center', bgColorClass)}>
          <Icon className={cn('w-5 h-5', iconColorClass)} />
        </div>
      </div>
      <div className="mt-3">
        <div className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
          {value}
        </div>
        {subtitle && (
          <p className="mt-1 text-xs text-slate-500 flex items-center">
            {subtitle}
          </p>
        )}
      </div>
    </Card>
  );
}
