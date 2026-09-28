import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Modal } from '../../components/ui/Modal';
import { Textarea } from '../../components/ui/Textarea';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { useGeneratePlan } from '../../hooks/usePlans';
import { useToast } from '../../components/ui/Toast';
import { CollectionPlan } from '../../types/plan';
import { Sparkles, Bot, Layers, CheckCircle2, Loader2, ArrowRight } from 'lucide-react';

const planSchema = z.object({
  request: z
    .string()
    .min(5, 'Please describe your data requirement with at least 5 characters')
    .max(2000),
  target_record_count: z.coerce.number().min(1).max(10000).default(100),
});

type PlanFormValues = z.infer<typeof planSchema>;

interface CreatePlanModalProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
  onPlanGenerated: (plan: CollectionPlan) => void;
}

const EXAMPLE_PROMPTS = [
  'Find 100 Indian startups that are hiring AI/ML engineers. Include company name, job title, location, salary if available, job posting URL, company website, and source.',
  'Collect 50 B2B fintech startups in Bangalore with company name, founders, funding stage, website, and employee headcount.',
  'Gather 200 luxury apartment listings in Mumbai with property title, price, carpet area, BHK, locality, and broker contact URL.',
];

export function CreatePlanModal({
  projectId,
  isOpen,
  onClose,
  onPlanGenerated,
}: CreatePlanModalProps) {
  const { mutateAsync: generatePlan, isPending } = useGeneratePlan();
  const { success, error: showError } = useToast();

  const {
    register,
    handleSubmit,
    setValue,
    reset,
    formState: { errors },
  } = useForm<PlanFormValues>({
    resolver: zodResolver(planSchema),
    defaultValues: {
      request: '',
      target_record_count: 100,
    },
  });

  const onSubmit = async (values: PlanFormValues) => {
    try {
      const plan = await generatePlan({
        projectId,
        payload: {
          request: values.request,
          target_record_count: values.target_record_count,
        },
      });

      if (plan.status === 'needs_clarification') {
        success('AI generated a draft plan and has clarification questions for you.');
      } else {
        success('AI Data Plan generated successfully! Ready for review.');
      }

      reset();
      onClose();
      onPlanGenerated(plan);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to generate AI data plan';
      showError(msg);
    }
  };

  const handleClose = () => {
    if (!isPending) {
      reset();
      onClose();
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="AI Data Planner"
      description="Describe the dataset you want to build in natural language. Our AI engine will formulate fields, search queries, sources, and validation rules."
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <Textarea
            label="Natural Language Data Requirement"
            placeholder="Describe the data you want to collect. For example, find 100 Indian startups hiring AI engineers and include company name, job title, location, and job URL."
            className="min-h-[120px]"
            error={errors.request?.message}
            disabled={isPending}
            {...register('request')}
          />

          {/* Quick example chips */}
          <div className="mt-2 space-y-1.5">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Try an example prompt:
            </span>
            <div className="space-y-1">
              {EXAMPLE_PROMPTS.map((example, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setValue('request', example)}
                  disabled={isPending}
                  className="w-full text-left p-2 rounded-lg border border-slate-200/70 bg-slate-50/70 hover:bg-indigo-50/70 hover:border-indigo-200 text-xs text-slate-700 transition-colors flex items-start gap-2 group"
                >
                  <Sparkles className="w-3.5 h-3.5 text-indigo-500 mt-0.5 flex-shrink-0" />
                  <span className="line-clamp-1 flex-1 group-hover:text-indigo-900">
                    {example}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="w-full sm:w-1/2">
          <Input
            label="Target Record Count"
            type="number"
            min="1"
            max="10000"
            disabled={isPending}
            error={errors.target_record_count?.message}
            helperText="Maximum number of records to target (1 - 10,000)"
            {...register('target_record_count')}
          />
        </div>

        {/* Loading animation state */}
        {isPending && (
          <div className="p-4 rounded-xl bg-indigo-50/70 border border-indigo-100 text-xs text-indigo-900 space-y-2 animate-in fade-in">
            <div className="flex items-center gap-2 font-semibold">
              <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
              <span>LangGraph AI Planning Engine Running...</span>
            </div>
            <p className="text-[11px] text-indigo-700">
              Decomposing intent, generating schemas, recommending data sources, and building validation rules.
            </p>
          </div>
        )}

        <div className="flex justify-end space-x-3 pt-4 border-t border-slate-100">
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={isPending}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            isLoading={isPending}
          >
            <Sparkles className="w-4 h-4 mr-1.5" />
            Generate Data Plan
          </Button>
        </div>
      </form>
    </Modal>
  );
}
