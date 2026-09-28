import React from 'react';
import { CollectionPlan } from '../../types/plan';
import { Card, CardHeader, CardContent, CardFooter } from '../../components/ui/Card';
import { StatusBadge } from '../../components/common/StatusBadge';
import { formatDate, formatNumber } from '../../lib/utils';
import { Sparkles, Database, Search, ArrowRight, CheckCircle2, XCircle } from 'lucide-react';
import { Button } from '../../components/ui/Button';

interface PlanCardProps {
  plan: CollectionPlan;
  onOpenPlan: (plan: CollectionPlan) => void;
}

export function PlanCard({ plan, onOpenPlan }: PlanCardProps) {
  const planData = plan.plan_data;

  return (
    <Card className="hover:shadow-hover hover:border-slate-300 transition-all duration-200 flex flex-col justify-between">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1">
              <Sparkles className="w-4 h-4 text-indigo-600 flex-shrink-0" />
              <h4 className="text-sm font-bold text-slate-900 line-clamp-1">
                {planData.goal || plan.original_request}
              </h4>
            </div>
            <p className="text-xs text-slate-500 line-clamp-2">
              "{plan.original_request}"
            </p>
          </div>
          <StatusBadge status={plan.status} />
        </div>
      </CardHeader>

      <CardContent className="py-2">
        <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-100 text-[11px] text-slate-600">
          <div className="p-2 rounded-lg bg-slate-50">
            <span className="text-slate-400 block">Target Records</span>
            <span className="font-bold text-slate-900 text-xs">
              {formatNumber(planData.target_record_count)}
            </span>
          </div>
          <div className="p-2 rounded-lg bg-slate-50">
            <span className="text-slate-400 block">Fields</span>
            <span className="font-bold text-slate-900 text-xs">
              {planData.fields?.length || 0} columns
            </span>
          </div>
          <div className="p-2 rounded-lg bg-slate-50">
            <span className="text-slate-400 block">Queries</span>
            <span className="font-bold text-slate-900 text-xs">
              {planData.search_queries?.length || 0} queries
            </span>
          </div>
        </div>
      </CardContent>

      <CardFooter className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
        <span>Created {formatDate(plan.created_at)}</span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onOpenPlan(plan)}
          className="gap-1 text-xs"
        >
          Review Plan
          <ArrowRight className="w-3 h-3" />
        </Button>
      </CardFooter>
    </Card>
  );
}
