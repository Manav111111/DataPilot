import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Modal } from '../../components/ui/Modal';
import { Input } from '../../components/ui/Input';
import { Textarea } from '../../components/ui/Textarea';
import { Select } from '../../components/ui/Select';
import { Button } from '../../components/ui/Button';
import { useCreateDataset } from '../../hooks/useDatasets';
import { useProjects } from '../../hooks/useProjects';
import { useToast } from '../../components/ui/Toast';
import { DatasetStatus } from '../../types/dataset';

const datasetSchema = z.object({
  project_id: z.string().min(1, 'Please select a project'),
  name: z.string().min(1, 'Dataset name is required').max(255),
  description: z.string().optional(),
  status: z.enum(['pending', 'processing', 'completed', 'failed'] as const),
  row_count: z.coerce.number().min(0, 'Row count must be 0 or greater'),
});

type DatasetFormValues = z.infer<typeof datasetSchema>;

interface CreateDatasetModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultProjectId?: string;
}

export function CreateDatasetModal({
  isOpen,
  onClose,
  defaultProjectId,
}: CreateDatasetModalProps) {
  const { mutateAsync: createDataset, isPending } = useCreateDataset();
  const { data: projectsData } = useProjects({ size: 100 });
  const { success, error: showError } = useToast();

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors },
  } = useForm<DatasetFormValues>({
    resolver: zodResolver(datasetSchema),
    defaultValues: {
      project_id: defaultProjectId || '',
      name: '',
      description: '',
      status: 'pending',
      row_count: 0,
    },
  });

  useEffect(() => {
    if (defaultProjectId) {
      setValue('project_id', defaultProjectId);
    } else if (projectsData?.items?.length) {
      setValue('project_id', projectsData.items[0].id);
    }
  }, [defaultProjectId, projectsData, setValue]);

  const onSubmit = async (values: DatasetFormValues) => {
    try {
      await createDataset({
        project_id: values.project_id,
        name: values.name,
        description: values.description || undefined,
        status: values.status as DatasetStatus,
        row_count: values.row_count,
      });
      success('Dataset created successfully!');
      reset();
      onClose();
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to create dataset';
      showError(msg);
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const projectOptions =
    projectsData?.items?.map((p) => ({
      value: p.id,
      label: p.name,
    })) || [];

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Create Dataset"
      description="Define a structured dataset entity inside your project."
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {!defaultProjectId && (
          <Select
            label="Associated Project"
            options={
              projectOptions.length > 0
                ? projectOptions
                : [{ value: '', label: 'No projects available (Create one first)' }]
            }
            error={errors.project_id?.message}
            {...register('project_id')}
          />
        )}

        <Input
          label="Dataset Name"
          placeholder="e.g. Q3 Verified Leads"
          error={errors.name?.message}
          {...register('name')}
        />

        <Textarea
          label="Description (Optional)"
          placeholder="Describe the schema, columns, and target source..."
          error={errors.description?.message}
          {...register('description')}
        />

        <div className="grid grid-cols-2 gap-3">
          <Select
            label="Initial Status"
            options={[
              { value: 'pending', label: 'Pending' },
              { value: 'processing', label: 'Processing' },
              { value: 'completed', label: 'Completed' },
              { value: 'failed', label: 'Failed' },
            ]}
            error={errors.status?.message}
            {...register('status')}
          />

          <Input
            label="Initial Row Count"
            type="number"
            min="0"
            error={errors.row_count?.message}
            {...register('row_count')}
          />
        </div>

        <div className="flex justify-end space-x-3 pt-4 border-t border-slate-100">
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={isPending}
          >
            Cancel
          </Button>
          <Button type="submit" variant="primary" isLoading={isPending}>
            Create Dataset
          </Button>
        </div>
      </form>
    </Modal>
  );
}
