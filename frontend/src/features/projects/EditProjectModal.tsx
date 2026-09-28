import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Modal } from '../../components/ui/Modal';
import { Input } from '../../components/ui/Input';
import { Textarea } from '../../components/ui/Textarea';
import { Select } from '../../components/ui/Select';
import { Button } from '../../components/ui/Button';
import { useUpdateProject } from '../../hooks/useProjects';
import { useToast } from '../../components/ui/Toast';
import { Project, ProjectStatus } from '../../types/project';

const projectSchema = z.object({
  name: z.string().min(1, 'Project name is required').max(255),
  description: z.string().optional(),
  status: z.enum(['draft', 'active', 'completed', 'failed'] as const),
});

type ProjectFormValues = z.infer<typeof projectSchema>;

interface EditProjectModalProps {
  project: Project | null;
  isOpen: boolean;
  onClose: () => void;
}

export function EditProjectModal({
  project,
  isOpen,
  onClose,
}: EditProjectModalProps) {
  const { mutateAsync: updateProject, isPending } = useUpdateProject();
  const { success, error: showError } = useToast();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProjectFormValues>({
    resolver: zodResolver(projectSchema),
  });

  useEffect(() => {
    if (project) {
      reset({
        name: project.name,
        description: project.description || '',
        status: project.status,
      });
    }
  }, [project, reset]);

  const onSubmit = async (values: ProjectFormValues) => {
    if (!project) return;
    try {
      await updateProject({
        id: project.id,
        data: {
          name: values.name,
          description: values.description || undefined,
          status: values.status as ProjectStatus,
        },
      });
      success('Project updated successfully!');
      onClose();
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to update project';
      showError(msg);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Edit Project"
      description="Update project details, metadata and operational status."
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Input
          label="Project Name"
          error={errors.name?.message}
          {...register('name')}
        />

        <Textarea
          label="Description (Optional)"
          error={errors.description?.message}
          {...register('description')}
        />

        <Select
          label="Status"
          options={[
            { value: 'draft', label: 'Draft' },
            { value: 'active', label: 'Active' },
            { value: 'completed', label: 'Completed' },
            { value: 'failed', label: 'Failed' },
          ]}
          error={errors.status?.message}
          {...register('status')}
        />

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
