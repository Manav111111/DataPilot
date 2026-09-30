import React, { useState } from 'react';
import { useDatasetSources } from '../../hooks/useCollection';
import { StatusBadge } from '../../components/common/StatusBadge';
import { SearchBar } from '../../components/common/SearchBar';
import { Pagination } from '../../components/common/Pagination';
import { Spinner } from '../../components/ui/Spinner';
import { formatDate } from '../../lib/utils';
import { Globe, ExternalLink, Hash, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';

interface DatasetSourcesListProps {
  datasetId: string;
}

export function DatasetSourcesList({ datasetId }: DatasetSourcesListProps) {
  const [page, setPage] = useState(1);
  const [domainFilter, setDomainFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const { data: sourcesData, isLoading } = useDatasetSources(datasetId, {
    page,
    size: 25,
    domain: domainFilter || undefined,
    retrieval_status: statusFilter || undefined,
  });

  const sources = sourcesData?.items || [];
  const totalPages = sourcesData?.pages || 1;

  return (
    <div className="space-y-4">
      {/* Top Filter Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3 flex-1 max-w-md">
          <SearchBar
            value={domainFilter}
            onChange={(val) => {
              setDomainFilter(val);
              setPage(1);
            }}
            placeholder="Filter by domain (e.g. techcrunch.com)..."
          />

          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="text-xs font-semibold rounded-lg border border-slate-200 bg-white px-3 py-2 text-slate-700 hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Statuses</option>
            <option value="retrieved">Retrieved</option>
            <option value="failed">Failed</option>
            <option value="blocked">Blocked</option>
          </select>
        </div>

        <span className="text-xs text-slate-500">
          Showing <strong>{sources.length}</strong> of <strong>{sourcesData?.total || 0}</strong> discovered sources
        </span>
      </div>

      {/* Sources Table */}
      <div className="rounded-xl border border-slate-200/80 bg-white shadow-card overflow-hidden">
        {isLoading ? (
          <div className="py-16 flex justify-center">
            <Spinner size="lg" />
          </div>
        ) : sources.length === 0 ? (
          <div className="py-16 text-center space-y-2">
            <Globe className="w-8 h-8 text-slate-300 mx-auto" />
            <h4 className="text-sm font-bold text-slate-900">No data sources found</h4>
            <p className="text-xs text-slate-500">
              No web pages match the current filter criteria.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-200/80 bg-slate-50/70 text-slate-600 font-semibold text-[11px] uppercase tracking-wider">
                  <th className="py-3 px-4">Domain</th>
                  <th className="py-3 px-4">Page Title & URL</th>
                  <th className="py-3 px-4">Search Query</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Retrieved</th>
                  <th className="py-3 px-4 text-right">Link</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {sources.map((src) => (
                  <tr key={src.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-800 font-semibold text-[11px]">
                        {src.domain || 'unknown'}
                      </span>
                    </td>
                    <td className="py-3 px-4 max-w-sm">
                      <div className="font-semibold text-slate-900 truncate">
                        {src.page_title || 'Untitled Document'}
                      </div>
                      <div className="text-[11px] text-slate-400 truncate">{src.source_url}</div>
                    </td>
                    <td className="py-3 px-4 max-w-xs truncate text-[11px] text-slate-600">
                      {src.search_query ? `"${src.search_query}"` : '—'}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <StatusBadge status={src.retrieval_status} />
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap text-slate-400 text-[11px]">
                      {src.retrieved_at ? formatDate(src.retrieved_at) : formatDate(src.created_at)}
                    </td>
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      <a
                        href={src.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800"
                      >
                        Open
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {totalPages > 1 && (
        <Pagination
          currentPage={page}
          totalPages={totalPages}
          totalItems={sourcesData?.total || 0}
          pageSize={25}
          onPageChange={setPage}
        />
      )}
    </div>
  );
}
