import React from 'react';
import { SourceRecommendation } from '../../types/plan';
import { Globe, ShieldAlert, CheckCircle2, Lock, ExternalLink } from 'lucide-react';
import { Badge } from '../../components/ui/Badge';

interface SourceRecommendationPanelProps {
  sources: SourceRecommendation[];
}

export function SourceRecommendationPanel({
  sources,
}: SourceRecommendationPanelProps) {
  return (
    <div className="space-y-4">
      <div>
        <h4 className="text-sm font-semibold text-slate-900">
          Suggested Data Sources ({sources.length})
        </h4>
        <p className="text-xs text-slate-500">
          Recommended permitted source categories. Sources have not been accessed or scraped yet.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {sources.map((src, idx) => (
          <div
            key={idx}
            className="p-4 rounded-xl border border-slate-200 bg-white hover:border-slate-300 transition-all space-y-2.5"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-indigo-50 text-indigo-600 flex-shrink-0">
                  <Globe className="w-4 h-4" />
                </div>
                <h5 className="text-xs sm:text-sm font-bold text-slate-900">
                  {src.source_category}
                </h5>
              </div>
              <Badge variant="outline" className="text-[10px]">
                {src.access_requirements || 'Public Web'}
              </Badge>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              {src.rationale}
            </p>

            {src.expected_fields && src.expected_fields.length > 0 && (
              <div className="pt-1.5 border-t border-slate-100">
                <span className="text-[11px] font-semibold text-slate-400 block mb-1">
                  Expected Extractable Fields:
                </span>
                <div className="flex flex-wrap gap-1">
                  {src.expected_fields.map((f, i) => (
                    <span
                      key={i}
                      className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-700"
                    >
                      {f}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {src.limitations && (
              <div className="flex items-start gap-1.5 p-2 rounded-lg bg-amber-50/70 border border-amber-200/60 text-[11px] text-amber-800">
                <ShieldAlert className="w-3.5 h-3.5 text-amber-600 flex-shrink-0 mt-0.5" />
                <span>{src.limitations}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
