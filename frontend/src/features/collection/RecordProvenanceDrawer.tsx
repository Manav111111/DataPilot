import React from 'react';
import { DatasetRecord } from '../../types/collection';
import { useRecordProvenance } from '../../hooks/useCollection';
import { Modal } from '../../components/ui/Modal';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Spinner } from '../../components/ui/Spinner';
import { formatDate } from '../../lib/utils';
import {
  ExternalLink,
  Globe,
  Quote,
  CheckCircle2,
  ShieldCheck,
  Tag,
  Hash,
  AlertCircle,
} from 'lucide-react';

interface RecordProvenanceDrawerProps {
  record: DatasetRecord | null;
  isOpen: boolean;
  onClose: () => void;
}

export function RecordProvenanceDrawer({
  record,
  isOpen,
  onClose,
}: RecordProvenanceDrawerProps) {
  const { data: provenances, isLoading } = useRecordProvenance(record?.id, isOpen && !!record);

  if (!record) return null;

  const displayData = record.record_data || record.normalized_data || {};

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Record Source Provenance & Field Audit"
      description="Inspect verified source links, crawled URLs, and verbatim evidence excerpts supporting this record."
      maxWidth="3xl"
    >
      <div className="space-y-5">
        {/* Record Overview Card */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-900 text-sm">Extracted Record Data</span>
              <StatusBadge status={record.validation_status} />
            </div>
            {record.record_hash && (
              <span className="text-[11px] text-slate-400 font-mono flex items-center gap-1">
                <Hash className="w-3 h-3" />
                Hash: {record.record_hash.slice(0, 12)}...
              </span>
            )}
          </div>

          {/* Fields Preview Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 pt-2 border-t border-slate-200/80">
            {Object.entries(displayData).map(([key, val]) => (
              <div key={key} className="p-2 rounded bg-white border border-slate-200/60">
                <span className="text-slate-400 block text-[10px] font-medium uppercase tracking-wider">
                  {key.replace(/_/g, ' ')}
                </span>
                <span className="font-semibold text-slate-800 break-words text-xs">
                  {val === null || val === undefined || val === '' ? (
                    <em className="text-slate-300 not-italic">None</em>
                  ) : typeof val === 'object' ? (
                    JSON.stringify(val)
                  ) : (
                    String(val)
                  )}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Source Evidence Section */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold text-slate-900 flex items-center gap-1.5 uppercase tracking-wider">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              Verified Source Traceability ({provenances?.length || 0} links)
            </h4>
          </div>

          {isLoading ? (
            <div className="py-10 flex justify-center">
              <Spinner size="md" />
            </div>
          ) : !provenances || provenances.length === 0 ? (
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 text-center text-xs text-slate-500">
              No specific excerpt links recorded for this entry.
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
              {provenances.map((prov, index) => (
                <div
                  key={prov.id || index}
                  className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-sm space-y-2.5"
                >
                  {/* Source URL & Domain */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-0.5 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 font-semibold text-[10px]">
                          {prov.domain || 'web_source'}
                        </span>
                        {prov.evidence_field && (
                          <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-semibold text-[10px]">
                            Field: {prov.evidence_field}
                          </span>
                        )}
                      </div>
                      <h5 className="font-bold text-slate-900 text-xs truncate">
                        {prov.page_title || prov.source_url}
                      </h5>
                    </div>

                    {prov.source_url && (
                      <a
                        href={prov.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex-shrink-0"
                      >
                        Open Public Source
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>

                  {/* Verbatim Excerpt */}
                  {prov.evidence_excerpt && (
                    <div className="p-3 rounded-lg bg-slate-50 border-l-2 border-indigo-500 text-xs text-slate-700 space-y-1">
                      <div className="flex items-center gap-1 text-slate-400 font-semibold text-[10px]">
                        <Quote className="w-3 h-3 text-indigo-500" />
                        Verbatim Source Excerpt:
                      </div>
                      <p className="italic font-sans text-slate-800">
                        "{prov.evidence_excerpt}"
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
}
