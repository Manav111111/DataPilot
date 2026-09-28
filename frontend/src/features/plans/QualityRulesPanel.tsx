import React from 'react';
import { QualityRule } from '../../types/plan';
import { ShieldCheck, CheckCircle, Copy, MapPin, FileCheck } from 'lucide-react';
import { Badge } from '../../components/ui/Badge';

interface QualityRulesPanelProps {
  rules: QualityRule[];
}

export function QualityRulesPanel({ rules }: QualityRulesPanelProps) {
  const getRuleIcon = (type: string) => {
    switch (type) {
      case 'duplicate_check':
        return <Copy className="w-4 h-4 text-purple-600" />;
      case 'geo_normalization':
        return <MapPin className="w-4 h-4 text-emerald-600" />;
      case 'valid_url':
      case 'valid_email':
        return <CheckCircle className="w-4 h-4 text-sky-600" />;
      default:
        return <ShieldCheck className="w-4 h-4 text-indigo-600" />;
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h4 className="text-sm font-semibold text-slate-900">
          Data Quality & Deduplication Rules ({rules.length})
        </h4>
        <p className="text-xs text-slate-500">
          Validation rules to ensure completeness, deduplication, and format standardization.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {rules.map((rule, idx) => (
          <div
            key={idx}
            className="p-3.5 rounded-xl border border-slate-200 bg-white space-y-1.5"
          >
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-slate-50 border border-slate-100">
                  {getRuleIcon(rule.rule_type)}
                </div>
                <span className="text-xs sm:text-sm font-bold text-slate-900">
                  {rule.name}
                </span>
              </div>
              <Badge variant="secondary" className="text-[10px]">
                {rule.rule_type}
              </Badge>
            </div>
            <p className="text-xs text-slate-600 pl-8">{rule.description}</p>
            {rule.field && (
              <p className="text-[11px] text-slate-400 pl-8">
                Target Field:{' '}
                <code className="font-mono text-slate-700 bg-slate-100 px-1 py-0.5 rounded">
                  {rule.field}
                </code>
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
