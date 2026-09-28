import React, { useState } from 'react';
import { FieldDefinition, FieldType } from '../../types/plan';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Badge } from '../../components/ui/Badge';
import { Plus, Trash2, Edit2, Check, X, ShieldAlert, Sparkles } from 'lucide-react';

interface EditableFieldBuilderProps {
  fields: FieldDefinition[];
  onChange: (fields: FieldDefinition[]) => void;
  disabled?: boolean;
}

const FIELD_TYPES: { value: FieldType; label: string }[] = [
  { value: 'string', label: 'String / Text' },
  { value: 'number', label: 'Number / Decimal' },
  { value: 'url', label: 'URL / Link' },
  { value: 'email', label: 'Email Address' },
  { value: 'phone', label: 'Phone Number' },
  { value: 'date', label: 'Date / Timestamp' },
  { value: 'boolean', label: 'Boolean (Yes/No)' },
  { value: 'array', label: 'Array / List' },
  { value: 'object', label: 'Nested Object' },
];

export function EditableFieldBuilder({
  fields,
  onChange,
  disabled = false,
}: EditableFieldBuilderProps) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<FieldDefinition | null>(null);

  // New field state
  const [isAdding, setIsAdding] = useState(false);
  const [newField, setNewField] = useState<FieldDefinition>({
    name: '',
    label: '',
    type: 'string',
    required: true,
    description: '',
  });

  const handleStartEdit = (index: number) => {
    if (disabled) return;
    setEditingIndex(index);
    setEditForm({ ...fields[index] });
  };

  const handleSaveEdit = () => {
    if (editingIndex === null || !editForm) return;
    if (!editForm.name.trim() || !editForm.label.trim()) return;

    // Check duplicate names (excluding current index)
    const duplicate = fields.some(
      (f, i) =>
        i !== editingIndex &&
        f.name.toLowerCase() === editForm.name.trim().toLowerCase()
    );
    if (duplicate) {
      alert(`Field name '${editForm.name}' already exists.`);
      return;
    }

    const updated = [...fields];
    updated[editingIndex] = {
      ...editForm,
      name: editForm.name.trim().toLowerCase().replace(/\s+/g, '_'),
    };
    onChange(updated);
    setEditingIndex(null);
    setEditForm(null);
  };

  const handleDelete = (index: number) => {
    if (disabled) return;
    if (fields.length <= 1) {
      alert('Plan must have at least one field definition.');
      return;
    }
    const updated = fields.filter((_, i) => i !== index);
    onChange(updated);
    if (editingIndex === index) {
      setEditingIndex(null);
      setEditForm(null);
    }
  };

  const handleAddField = () => {
    if (!newField.name.trim() || !newField.label.trim()) {
      alert('Please provide both field name and display label.');
      return;
    }
    const cleanName = newField.name.trim().toLowerCase().replace(/\s+/g, '_');
    const duplicate = fields.some((f) => f.name.toLowerCase() === cleanName);
    if (duplicate) {
      alert(`Field name '${cleanName}' already exists.`);
      return;
    }

    const updated = [...fields, { ...newField, name: cleanName }];
    onChange(updated);
    setNewField({
      name: '',
      label: '',
      type: 'string',
      required: true,
      description: '',
    });
    setIsAdding(false);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-semibold text-slate-900">
            Dataset Schema Fields ({fields.length})
          </h4>
          <p className="text-xs text-slate-500">
            Customize the columns, types, and constraints extracted for each record.
          </p>
        </div>
        {!disabled && !isAdding && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setIsAdding(true)}
          >
            <Plus className="w-3.5 h-3.5 mr-1" />
            Add Field
          </Button>
        )}
      </div>

      {/* Add New Field Inline Card */}
      {isAdding && !disabled && (
        <div className="p-4 rounded-xl border border-indigo-200 bg-indigo-50/40 space-y-3 animate-in fade-in">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-indigo-900">
              New Field Definition
            </span>
            <button
              type="button"
              onClick={() => setIsAdding(false)}
              className="text-slate-400 hover:text-slate-600"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <Input
              label="Field Name (snake_case)"
              placeholder="e.g. founder_email"
              value={newField.name}
              onChange={(e) =>
                setNewField({ ...newField, name: e.target.value })
              }
            />
            <Input
              label="Display Label"
              placeholder="e.g. Founder Email"
              value={newField.label}
              onChange={(e) =>
                setNewField({ ...newField, label: e.target.value })
              }
            />
            <Select
              label="Data Type"
              options={FIELD_TYPES}
              value={newField.type}
              onChange={(e) =>
                setNewField({ ...newField, type: e.target.value as FieldType })
              }
            />
          </div>
          <Input
            label="Description (Optional)"
            placeholder="Describe what data this field extracts..."
            value={newField.description || ''}
            onChange={(e) =>
              setNewField({ ...newField, description: e.target.value })
            }
          />
          <div className="flex items-center justify-between pt-2">
            <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                checked={newField.required}
                onChange={(e) =>
                  setNewField({ ...newField, required: e.target.checked })
                }
                className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
              />
              <span className="font-medium">Mandatory Required Field</span>
            </label>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setIsAdding(false)}
              >
                Cancel
              </Button>
              <Button
                type="button"
                variant="primary"
                size="sm"
                onClick={handleAddField}
              >
                Save Field
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Fields List */}
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white divide-y divide-slate-100">
        {fields.map((field, index) => {
          const isEditing = editingIndex === index;

          if (isEditing && editForm) {
            return (
              <div key={index} className="p-4 bg-slate-50 space-y-3">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <Input
                    label="Field Name (snake_case)"
                    value={editForm.name}
                    onChange={(e) =>
                      setEditForm({ ...editForm, name: e.target.value })
                    }
                  />
                  <Input
                    label="Display Label"
                    value={editForm.label}
                    onChange={(e) =>
                      setEditForm({ ...editForm, label: e.target.value })
                    }
                  />
                  <Select
                    label="Data Type"
                    options={FIELD_TYPES}
                    value={editForm.type}
                    onChange={(e) =>
                      setEditForm({
                        ...editForm,
                        type: e.target.value as FieldType,
                      })
                    }
                  />
                </div>
                <Input
                  label="Description"
                  value={editForm.description || ''}
                  onChange={(e) =>
                    setEditForm({ ...editForm, description: e.target.value })
                  }
                />
                <div className="flex items-center justify-between pt-2">
                  <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={editForm.required}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          required: e.target.checked,
                        })
                      }
                      className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span className="font-medium">Mandatory Required Field</span>
                  </label>
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setEditingIndex(null)}
                    >
                      Cancel
                    </Button>
                    <Button
                      type="button"
                      variant="primary"
                      size="sm"
                      onClick={handleSaveEdit}
                    >
                      <Check className="w-3.5 h-3.5 mr-1" />
                      Save
                    </Button>
                  </div>
                </div>
              </div>
            );
          }

          return (
            <div
              key={index}
              className="p-3.5 sm:px-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50/60 transition-colors group"
            >
              <div className="space-y-1 min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs sm:text-sm font-semibold text-slate-900">
                    {field.label}
                  </span>
                  <code className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                    {field.name}
                  </code>
                  <Badge variant="outline" className="text-[10px] py-0 px-1.5">
                    {field.type}
                  </Badge>
                  {field.required ? (
                    <Badge variant="default" className="text-[10px] py-0 px-1.5">
                      Required
                    </Badge>
                  ) : (
                    <Badge variant="secondary" className="text-[10px] py-0 px-1.5">
                      Optional
                    </Badge>
                  )}
                </div>
                {field.description && (
                  <p className="text-xs text-slate-500 line-clamp-1">
                    {field.description}
                  </p>
                )}
              </div>

              {!disabled && (
                <div className="flex items-center gap-1 self-end sm:self-auto">
                  <button
                    type="button"
                    onClick={() => handleStartEdit(index)}
                    title="Edit Field"
                    className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDelete(index)}
                    title="Delete Field"
                    className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
