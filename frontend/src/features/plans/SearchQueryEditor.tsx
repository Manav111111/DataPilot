import React, { useState } from 'react';
import { SearchQuery } from '../../types/plan';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Badge } from '../../components/ui/Badge';
import { Search, Plus, Trash2, Edit2, Check, X, Globe } from 'lucide-react';

interface SearchQueryEditorProps {
  queries: SearchQuery[];
  onChange: (queries: SearchQuery[]) => void;
  disabled?: boolean;
}

const CATEGORY_OPTIONS = [
  { value: 'Company Career Pages', label: 'Company Career Pages' },
  { value: 'Public Job Boards', label: 'Public Job Boards' },
  { value: 'Public Directories & Portals', label: 'Public Directories & Portals' },
  { value: 'Government Registries', label: 'Government Registries' },
  { value: 'General Web Search', label: 'General Web Search' },
];

export function SearchQueryEditor({
  queries,
  onChange,
  disabled = false,
}: SearchQueryEditorProps) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<SearchQuery | null>(null);

  const [isAdding, setIsAdding] = useState(false);
  const [newQuery, setNewQuery] = useState<SearchQuery>({
    query: '',
    purpose: '',
    source_category: 'Company Career Pages',
    priority: 1,
  });

  const handleStartEdit = (index: number) => {
    if (disabled) return;
    setEditingIndex(index);
    setEditForm({ ...queries[index] });
  };

  const handleSaveEdit = () => {
    if (editingIndex === null || !editForm) return;
    if (!editForm.query.trim()) return;

    const updated = [...queries];
    updated[editingIndex] = editForm;
    onChange(updated);
    setEditingIndex(null);
    setEditForm(null);
  };

  const handleDelete = (index: number) => {
    if (disabled) return;
    const updated = queries.filter((_, i) => i !== index);
    onChange(updated);
    if (editingIndex === index) {
      setEditingIndex(null);
      setEditForm(null);
    }
  };

  const handleAdd = () => {
    if (!newQuery.query.trim()) return;
    onChange([...queries, newQuery]);
    setNewQuery({
      query: '',
      purpose: '',
      source_category: 'Company Career Pages',
      priority: 1,
    });
    setIsAdding(false);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-semibold text-slate-900">
            Proposed Search Queries ({queries.length})
          </h4>
          <p className="text-xs text-slate-500">
            Targeted search queries and categories to be executed in Phase 3.
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
            Add Query
          </Button>
        )}
      </div>

      {/* Add New Query Inline */}
      {isAdding && !disabled && (
        <div className="p-4 rounded-xl border border-indigo-200 bg-indigo-50/40 space-y-3 animate-in fade-in">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-indigo-900">
              New Search Query
            </span>
            <button
              type="button"
              onClick={() => setIsAdding(false)}
              className="text-slate-400 hover:text-slate-600"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <Input
            label="Search Query String"
            placeholder="e.g. site:lever.co/jobs Indian AI startup engineer"
            icon={<Search className="w-4 h-4" />}
            value={newQuery.query}
            onChange={(e) =>
              setNewQuery({ ...newQuery, query: e.target.value })
            }
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Input
              label="Query Purpose"
              placeholder="What specific subset this query finds..."
              value={newQuery.purpose}
              onChange={(e) =>
                setNewQuery({ ...newQuery, purpose: e.target.value })
              }
            />
            <Select
              label="Source Category"
              options={CATEGORY_OPTIONS}
              value={newQuery.source_category}
              onChange={(e) =>
                setNewQuery({ ...newQuery, source_category: e.target.value })
              }
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
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
              onClick={handleAdd}
            >
              Save Query
            </Button>
          </div>
        </div>
      )}

      {/* Queries List */}
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white divide-y divide-slate-100">
        {queries.map((q, index) => {
          const isEditing = editingIndex === index;

          if (isEditing && editForm) {
            return (
              <div key={index} className="p-4 bg-slate-50 space-y-3">
                <Input
                  label="Search Query"
                  value={editForm.query}
                  onChange={(e) =>
                    setEditForm({ ...editForm, query: e.target.value })
                  }
                />
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <Input
                    label="Purpose"
                    value={editForm.purpose}
                    onChange={(e) =>
                      setEditForm({ ...editForm, purpose: e.target.value })
                    }
                  />
                  <Select
                    label="Source Category"
                    options={CATEGORY_OPTIONS}
                    value={editForm.source_category}
                    onChange={(e) =>
                      setEditForm({
                        ...editForm,
                        source_category: e.target.value,
                      })
                    }
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2">
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
            );
          }

          return (
            <div
              key={index}
              className="p-3.5 sm:px-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50/60 transition-colors group"
            >
              <div className="space-y-1 min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-mono text-xs font-semibold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">
                    {q.query}
                  </span>
                  <Badge variant="info" className="text-[10px] py-0 px-1.5">
                    {q.source_category}
                  </Badge>
                  <span className="text-[10px] text-slate-400 font-medium">
                    Priority #{q.priority || 1}
                  </span>
                </div>
                <p className="text-xs text-slate-500">{q.purpose}</p>
              </div>

              {!disabled && (
                <div className="flex items-center gap-1 self-end sm:self-auto">
                  <button
                    type="button"
                    onClick={() => handleStartEdit(index)}
                    title="Edit Query"
                    className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDelete(index)}
                    title="Delete Query"
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
