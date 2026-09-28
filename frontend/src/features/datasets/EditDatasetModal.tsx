import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Modal } from '../../components/ui/Modal';
import { Input } from '../../components/ui/Input';
import { Textarea } from '../../components/ui/Textarea';
import { Select } from '../../components/ui/Select';
import { Button } from '../../components/ui/Button';
import { useUpdateDataset } from '../../hooks/useDatasets';
import { useToast } from '../../components/ui/Toast';
import { Dataset, DatasetStatus } from '../../types/dataset';

const datasetSchema = z.object({
  name: z.string().min(1, 'Dataset name is required').max(255),
  description: z.string().optional(),
  status: z.enum(['pending', 'processing', 'completed', 'failed'] as const),
  row_count: z.coerce.number().min(0, 'Row count must be 0 or greater'),
});

type DatasetFormValues = z.infer<typeof datasetSchema>;

interface EditDatasetModalProps {
  dataset: Dataset | null;
  isOpen: boolean;
  onClose: () => void;
}

export function EditDatasetModal({
  dataset,
  isOpen,
  onClose,
}: EditDatasetModalProps) {
  const { mutateAsync: updateDataset, isPending } = useUpdateDataset();
  const { success, error: showError } = useToast();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<DatasetFormValues>({
    resolver: zodResolver(datasetSchema),
  });

  useEffect(() => {
    if (dataset) {
      reset({
        name: dataset.name,
        description: dataset.description || '',
        status: dataset.status,
        row_count: dataset.row_count,
      });
    }
  }, [dataset, reset]);

  const onSubmit = async (values: DatasetFormValues) => {
    if (!dataset) return;
    try {
      await updateDataset({
        id: dataset.id,
        data: {
          name: values.name,
          description: values.description || undefined,
          status: values.status as DatasetStatus,
          row_count: values.row_count,
        },
      });
      success('Dataset updated successfully!');
      onClose();
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to update dataset';
      showError(msg);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Edit Dataset"
      description="Update dataset name, description, status or row count."
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Input
          label="Dataset Name"
          error={errors.name?.message}
          {...register('name')}
        />

        <Textarea
          label="Description (Optional)"
          error={errors.description?.message}
          {...register('description')}
        />

        <div className="grid grid-cols-2 gap-3">
          <Select
            label="Status"
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
            label="Row Count"
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
            onClick={onClose}
            disabled={isPending}
          >
            Cancel
          </Button>
          <Button type="submit" variant="primary" isLoading={isPending}>
            Save Changes
          </Button>
        </div>
      </form>
    </Modal>
  );
}
