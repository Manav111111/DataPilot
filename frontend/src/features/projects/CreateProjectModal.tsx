import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Modal } from '../../components/ui/Modal';
import { Input } from '../../components/ui/Input';
import { Textarea } from '../../components/ui/Textarea';
import { Select } from '../../components/ui/Select';
import { Button } from '../../components/ui/Button';
import { useCreateProject } from '../../hooks/useProjects';
import { useToast } from '../../components/ui/Toast';
import { ProjectStatus } from '../../types/project';

const projectSchema = z.object({
  name: z.string().min(1, 'Project name is required').max(255),
  description: z.string().optional(),
  status: z.enum(['draft', 'active', 'completed', 'failed'] as const),
});

type ProjectFormValues = z.infer<typeof projectSchema>;

interface CreateProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CreateProjectModal({ isOpen, onClose }: CreateProjectModalProps) {
  const { mutateAsync: createProject, isPending } = useCreateProject();
  const { success, error: showError } = useToast();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProjectFormValues>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      name: '',
      description: '',
      status: 'draft',
    },
  });

  const onSubmit = async (values: ProjectFormValues) => {
    try {
      await createProject({
        name: values.name,
        description: values.description || undefined,
        status: values.status as ProjectStatus,
      });
      success('Project created successfully!');
      reset();
      onClose();
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to create project';
      showError(msg);
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Create New Project"
      description="Initialize a data intelligence project to organize your datasets and automated collection runs."
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Input
          label="Project Name"
          placeholder="e.g. Real Estate Price Tracker"
          error={errors.name?.message}
          {...register('name')}
        />

        <Textarea
          label="Description (Optional)"
          placeholder="Describe what data this project organizes and processes..."
          error={errors.description?.message}
          {...register('description')}
        />

        <Select
          label="Initial Status"
          options={[
            { value: 'draft', label: 'Draft — Setup in progress' },
            { value: 'active', label: 'Active — Live and collecting' },
            { value: 'completed', label: 'Completed — Fully processed' },
          ]}
          error={errors.status?.message}
          {...register('status')}
        />

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
            Create Project
          </Button>
        </div>
      </form>
    </Modal>
  );
}
