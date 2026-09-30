import React, { useState, useRef, useEffect } from 'react';
import {
  useAnalysisSessions,
  useAnalysisSession,
  useChatMutation,
  useAutoInsights,
  useDatasetStatistics,
  useCreateReportMutation,
  useDeleteSessionMutation,
} from '../../hooks/useAnalysis';
import { useDatasetProfile } from '../../hooks/useDatasetManagement';
import { Spinner } from '../../components/ui/Spinner';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import { useToast } from '../../components/ui/Toast';
import {
  Send,
  Sparkles,
  Bot,
  User as UserIcon,
  BarChart3,
  Table as TableIcon,
  Layers,
  Plus,
  Trash2,
  FileText,
  Activity,
  Lightbulb,
  AlertTriangle,
  ChevronRight,
  TrendingUp,
  Cpu,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

const CHART_COLORS = [
  '#4f46e5',
  '#06b6d4',
  '#10b981',
  '#f59e0b',
  '#ec4899',
  '#8b5cf6',
  '#3b82f6',
];

interface DatasetInsightsTabProps {
  datasetId: string;
}

export function DatasetInsightsTab({ datasetId }: DatasetInsightsTabProps) {
  const [selectedSessionId, setSelectedSessionId] = useState<string | undefined>(undefined);
  const [inputQuery, setInputQuery] = useState('');
  const [isAutoInsightsOpen, setIsAutoInsightsOpen] = useState(false);
  const [isStatsOpen, setIsStatsOpen] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [reportTitle, setReportTitle] = useState('Executive Data Insights Report');
  const [reportNotes, setReportNotes] = useState('');

  const chatBottomRef = useRef<HTMLDivElement>(null);
  const { success, error: showError } = useToast();

  const { data: profile } = useDatasetProfile(datasetId);
  const { data: sessions, isLoading: loadingSessions } = useAnalysisSessions(datasetId);
  const { data: currentSession, isLoading: loadingSession } = useAnalysisSession(
    datasetId,
    selectedSessionId || sessions?.[0]?.id
  );

  const { mutateAsync: sendMessage, isPending: isSending } = useChatMutation(datasetId);
  const { mutateAsync: deleteSession, isPending: isDeletingSession } = useDeleteSessionMutation(datasetId);
  const { mutateAsync: createReport, isPending: isCreatingReport } = useCreateReportMutation(datasetId);

  const { data: autoInsightsData, isLoading: loadingAutoInsights, refetch: refetchInsights } =
    useAutoInsights(datasetId, isAutoInsightsOpen);
  const { data: statsData, isLoading: loadingStats, refetch: refetchStats } =
    useDatasetStatistics(datasetId, isStatsOpen);

  useEffect(() => {
    if (!selectedSessionId && sessions && sessions.length > 0) {
      setSelectedSessionId(sessions[0].id);
    }
  }, [sessions, selectedSessionId]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentSession?.messages, isSending]);

  const activeSessionId = selectedSessionId || sessions?.[0]?.id;

  const handleSend = async (queryText?: string) => {
    const textToSend = queryText || inputQuery;
    if (!textToSend.trim() || isSending) return;

    try {
      setInputQuery('');
      const res = await sendMessage({
        message: textToSend,
        sessionId: activeSessionId,
      });
      if (!selectedSessionId) {
        setSelectedSessionId(res.session_id);
      }
    } catch (err: any) {
      showError(err.response?.data?.detail || 'Failed to process query');
    }
  };

  const handleNewChat = () => {
    setSelectedSessionId(undefined);
  };

  const handleDeleteSession = async () => {
    if (!activeSessionId) return;
    try {
      await deleteSession(activeSessionId);
      setSelectedSessionId(undefined);
      success('Conversation session deleted.');
    } catch (err: any) {
      showError(err.response?.data?.detail || 'Failed to delete session');
    }
  };

  const handleSaveReport = async () => {
    if (!reportTitle.trim()) return;
    try {
      await createReport({
        title: reportTitle,
        format: 'html',
        custom_notes: reportNotes || undefined,
      });
      setIsReportModalOpen(false);
      success('Analysis report generated successfully! View in the Reports tab.');
    } catch (err: any) {
      showError(err.response?.data?.detail || 'Failed to generate report');
    }
  };

  // Generate dynamic suggested questions based on dataset columns
  const suggestedQuestions = React.useMemo(() => {
    const cols = profile?.columns?.map((c) => c.column_name) || [];
    if (cols.length === 0) {
      return [
        'Summarize key metrics and distribution in this dataset',
        'Find top 5 records with the highest numerical values',
        'Which records contain missing or incomplete fields?',
      ];
    }
    const numCol = profile?.columns?.find((c) =>
      ['integer', 'number', 'float'].includes(c.inferred_type)
    )?.column_name;
    const catCol = profile?.columns?.find((c) =>
      ['string', 'category'].includes(c.inferred_type)
    )?.column_name;

    const suggestions = [];
    if (numCol) {
      suggestions.push(`Which 5 records have the highest ${numCol.replace(/_/g, ' ')}?`);
      if (catCol) {
        suggestions.push(`Calculate average ${numCol.replace(/_/g, ' ')} grouped by ${catCol.replace(/_/g, ' ')}`);
      }
      suggestions.push(`Identify statistical outliers and anomalies in ${numCol.replace(/_/g, ' ')}`);
    }
    if (catCol) {
      suggestions.push(`Show category distribution breakdown for ${catCol.replace(/_/g, ' ')}`);
    }
    suggestions.push('Summarize overall data completeness and missing values');
    return suggestions.slice(0, 4);
  }, [profile]);

  return (
    <div className="space-y-4">
      {/* Top Controls Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-slate-50 border border-slate-200">
        <div className="flex items-center gap-2">
          {sessions && sessions.length > 0 ? (
            <select
              value={activeSessionId || ''}
              onChange={(e) => setSelectedSessionId(e.target.value)}
              className="text-xs font-semibold rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 max-w-xs truncate"
            >
              {sessions.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.title || 'Conversation'}
                </option>
              ))}
            </select>
          ) : null}

          <Button
            variant="outline"
            size="sm"
            onClick={handleNewChat}
            className="text-xs font-semibold gap-1.5 h-8 bg-white"
          >
            <Plus className="w-3.5 h-3.5 text-indigo-600" />
            New Chat
          </Button>

          {activeSessionId && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleDeleteSession}
              disabled={isDeletingSession}
              className="text-xs font-semibold text-red-600 hover:text-red-700 hover:bg-red-50 border-slate-200 h-8"
              title="Delete current conversation"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </Button>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setIsAutoInsightsOpen(true);
              refetchInsights();
            }}
            className="text-xs font-semibold gap-1.5 h-8 bg-white text-indigo-700 hover:bg-indigo-50 border-indigo-200"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            Auto Insights
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setIsStatsOpen(true);
              refetchStats();
            }}
            className="text-xs font-semibold gap-1.5 h-8 bg-white text-emerald-700 hover:bg-emerald-50 border-emerald-200"
          >
            <Activity className="w-3.5 h-3.5 text-emerald-600" />
            Statistical Profile
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsReportModalOpen(true)}
            className="text-xs font-semibold gap-1.5 h-8 bg-indigo-600 hover:bg-indigo-700 text-white"
          >
            <FileText className="w-3.5 h-3.5" />
            Generate Report
          </Button>
        </div>
      </div>

      {/* Main Chat Stream Container */}
      <div className="rounded-xl border border-slate-200/80 bg-white shadow-card flex flex-col h-[520px]">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {(!currentSession || currentSession.messages.length === 0) && (
            <div className="py-12 px-4 text-center max-w-lg mx-auto space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center mx-auto text-indigo-600">
                <Bot className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-bold text-slate-900">
                Ask anything about your dataset
              </h3>
              <p className="text-xs text-slate-500">
                Natural-language questions are translated into safe, validated Pandas operations.
                All numerical results are computed strictly from real records with zero hallucination.
              </p>

              {/* Suggested Questions */}
              <div className="pt-3 space-y-2 text-left">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block text-center">
                  Suggested Questions
                </span>
                <div className="flex flex-col gap-1.5">
                  {suggestedQuestions.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSend(q)}
                      className="text-xs text-left p-2.5 rounded-lg bg-slate-50 hover:bg-indigo-50/80 border border-slate-200/60 hover:border-indigo-200 text-slate-700 hover:text-indigo-900 transition-colors flex items-center justify-between group"
                    >
                      <span className="truncate">{q}</span>
                      <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-indigo-600 flex-shrink-0" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {currentSession?.messages.map((msg) => {
            const isUser = msg.role === 'user';
            const plan = msg.analytical_plan;
            const res = msg.execution_result;
            const table = res?.table;
            const chartData = res?.chart_data;
            const chartConfig = res?.chart_config;

            return (
              <div
                key={msg.id}
                className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
              >
                {!isUser && (
                  <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={`max-w-2xl rounded-xl p-3.5 text-xs space-y-2.5 ${
                    isUser
                      ? 'bg-indigo-600 text-white ml-12'
                      : 'bg-slate-50 border border-slate-200 text-slate-800 mr-8'
                  }`}
                >
                  {/* Content / Explanation */}
                  <div className="whitespace-pre-wrap leading-relaxed font-sans">
                    {msg.content}
                  </div>

                  {/* Operational Badge */}
                  {!isUser && plan && (
                    <div className="flex items-center gap-2 pt-1 border-t border-slate-200/70 text-[10px] text-slate-500 font-mono">
                      <Cpu className="w-3 h-3 text-indigo-500" />
                      <span>
                        Operation: <strong>{plan.operation}</strong> &bull; Target:{' '}
                        {plan.target_columns?.join(', ') || 'all'}
                      </span>
                    </div>
                  )}

                  {/* Inline Chart Display */}
                  {!isUser && chartData && chartData.length > 0 && chartConfig && (
                    <div className="p-3 bg-white rounded-lg border border-slate-200 space-y-1 mt-2">
                      <span className="text-[11px] font-bold text-slate-800 block">
                        {chartConfig.title}
                      </span>
                      <div className="h-48 w-full pt-1">
                        <ResponsiveContainer width="100%" height="100%">
                          {chartConfig.chart_type === 'pie' ? (
                            <PieChart>
                              <Pie
                                data={chartData}
                                dataKey="value"
                                nameKey="name"
                                cx="50%"
                                cy="50%"
                                outerRadius={60}
                                label={({ name, percent }) =>
                                  `${name} (${(percent * 100).toFixed(0)}%)`
                                }
                              >
                                {chartData.map((_, i) => (
                                  <Cell
                                    key={i}
                                    fill={CHART_COLORS[i % CHART_COLORS.length]}
                                  />
                                ))}
                              </Pie>
                              <Tooltip />
                            </PieChart>
                          ) : chartConfig.chart_type === 'line' ? (
                            <LineChart data={chartData}>
                              <CartesianGrid strokeDasharray="3 3" vertical={false} />
                              <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                              <YAxis tick={{ fontSize: 10 }} />
                              <Tooltip />
                              <Line
                                type="monotone"
                                dataKey="value"
                                stroke="#4f46e5"
                                strokeWidth={2}
                              />
                            </LineChart>
                          ) : (
                            <BarChart data={chartData}>
                              <CartesianGrid strokeDasharray="3 3" vertical={false} />
                              <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                              <YAxis tick={{ fontSize: 10 }} />
                              <Tooltip />
                              <Bar dataKey="value" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                            </BarChart>
                          )}
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )}

                  {/* Inline Table Display */}
                  {!isUser && table && table.rows && table.rows.length > 0 && (
                    <div className="bg-white rounded-lg border border-slate-200 overflow-hidden mt-2">
                      <div className="max-h-48 overflow-auto">
                        <table className="w-full text-left border-collapse text-[11px]">
                          <thead>
                            <tr className="bg-slate-100 border-b border-slate-200 font-semibold text-slate-700">
                              {table.columns.map((col) => (
                                <th key={col} className="p-2 whitespace-nowrap">
                                  {col.replace(/_/g, ' ')}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                            {table.rows.slice(0, 10).map((row, rIdx) => (
                              <tr key={rIdx} className="hover:bg-slate-50">
                                {table.columns.map((col) => (
                                  <td key={col} className="p-2 truncate max-w-xs">
                                    {row[col] === null || row[col] === undefined
                                      ? '—'
                                      : String(row[col])}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>

                {isUser && (
                  <div className="w-7 h-7 rounded-lg bg-slate-800 text-white flex items-center justify-center flex-shrink-0 mt-0.5">
                    <UserIcon className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })}

          {isSending && (
            <div className="flex gap-3 justify-start items-center">
              <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center gap-2 text-xs text-slate-500">
                <Spinner size="sm" />
                <span>Executing analytical query plan...</span>
              </div>
            </div>
          )}

          <div ref={chatBottomRef} />
        </div>

        {/* Bottom Input Area */}
        <div className="p-3 border-t border-slate-200 bg-slate-50/50 rounded-b-xl">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder="Ask a question about this dataset (e.g. top 5 by revenue, average price by category)..."
              disabled={isSending}
              className="flex-1 text-xs rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={!inputQuery.trim() || isSending}
              className="h-9 px-4 text-xs font-semibold gap-1.5"
            >
              <Send className="w-3.5 h-3.5" />
              Ask AI
            </Button>
          </form>
        </div>
      </div>

      {/* Auto Insights Modal */}
      <Modal
        isOpen={isAutoInsightsOpen}
        onClose={() => setIsAutoInsightsOpen(false)}
        title="Automated Multi-Dimensional Insights"
        description="Comprehensive dataset scan computing key patterns, extremes, distributions, and outliers."
        maxWidth="4xl"
      >
        <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
          {loadingAutoInsights ? (
            <div className="py-16 flex justify-center">
              <Spinner size="lg" />
            </div>
          ) : !autoInsightsData || autoInsightsData.insights.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-500">
              No automated insights generated for this dataset.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {autoInsightsData.insights.map((insight, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-slate-200 bg-white shadow-sm space-y-2 hover:border-indigo-300 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-indigo-50 text-indigo-700">
                      {insight.category}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">
                      {insight.method}
                    </span>
                  </div>

                  <h4 className="text-xs font-bold text-slate-900">
                    {insight.title}
                  </h4>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {insight.explanation}
                  </p>

                  {/* Insight Chart if present */}
                  {insight.chart_data && insight.chart_config && (
                    <div className="h-36 w-full pt-1">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={insight.chart_data}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} />
                          <XAxis dataKey="name" tick={{ fontSize: 9 }} />
                          <YAxis tick={{ fontSize: 9 }} />
                          <Tooltip />
                          <Bar dataKey="value" fill="#4f46e5" radius={[3, 3, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {insight.suggested_followup && (
                    <button
                      onClick={() => {
                        setIsAutoInsightsOpen(false);
                        handleSend(insight.suggested_followup);
                      }}
                      className="text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1 pt-1"
                    >
                      <Lightbulb className="w-3 h-3" />
                      Ask: "{insight.suggested_followup}"
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </Modal>

      {/* Statistical Profile Modal */}
      <Modal
        isOpen={isStatsOpen}
        onClose={() => setIsStatsOpen(false)}
        title="Statistical Profile & Correlation Analysis"
        description="Comprehensive descriptive statistics, numeric distributions, and Pearson correlation pairs."
        maxWidth="4xl"
      >
        <div className="space-y-5 max-h-[70vh] overflow-y-auto pr-1">
          {loadingStats ? (
            <div className="py-16 flex justify-center">
              <Spinner size="lg" />
            </div>
          ) : !statsData ? (
            <div className="py-12 text-center text-xs text-slate-500">
              No statistical metrics available.
            </div>
          ) : (
            <>
              {/* Descriptive Stats Table */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Descriptive Statistics (Numeric Columns)
                </h4>
                <div className="rounded-xl border border-slate-200 overflow-hidden">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200 font-semibold text-slate-600 text-[11px]">
                        <th className="p-2.5">Column</th>
                        <th className="p-2.5">Count</th>
                        <th className="p-2.5">Mean</th>
                        <th className="p-2.5">Std Dev</th>
                        <th className="p-2.5">Min</th>
                        <th className="p-2.5">Median</th>
                        <th className="p-2.5">Max</th>
                        <th className="p-2.5">Missing</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-700">
                      {statsData.descriptive_stats.map((s) => (
                        <tr key={s.column} className="hover:bg-slate-50/50">
                          <td className="p-2.5 font-semibold text-slate-900">{s.column}</td>
                          <td className="p-2.5">{s.count}</td>
                          <td className="p-2.5">{s.mean ?? '—'}</td>
                          <td className="p-2.5">{s.std ?? '—'}</td>
                          <td className="p-2.5">{s.min ?? '—'}</td>
                          <td className="p-2.5">{s.median ?? '—'}</td>
                          <td className="p-2.5">{s.max ?? '—'}</td>
                          <td className="p-2.5 text-red-600">{s.null_count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Correlations & Outliers Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Top Correlations */}
                <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-2.5">
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                    <TrendingUp className="w-4 h-4 text-indigo-600" />
                    Top Correlation Relationships
                  </h4>
                  {statsData.top_correlations.length === 0 ? (
                    <p className="text-xs text-slate-400">
                      Insufficient numeric pairs to compute correlations.
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {statsData.top_correlations.map((c, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100 text-xs"
                        >
                          <span className="font-semibold text-slate-800">
                            {c.column_a} &harr; {c.column_b}
                          </span>
                          <span className="font-mono px-2 py-0.5 rounded bg-white border border-slate-200 text-indigo-700 font-bold">
                            r = {c.coefficient}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Outliers */}
                <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-2.5">
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    Detected Outliers (IQR Method)
                  </h4>
                  {statsData.outliers.length === 0 ? (
                    <p className="text-xs text-slate-400">No outliers detected.</p>
                  ) : (
                    <div className="space-y-2">
                      {statsData.outliers.map((o, i) => (
                        <div
                          key={i}
                          className="p-2 rounded-lg bg-slate-50 border border-slate-100 text-xs space-y-1"
                        >
                          <div className="flex justify-between">
                            <span className="font-semibold text-slate-800">{o.column}</span>
                            <span className="font-bold text-amber-700">
                              {o.outlier_count} Outlier(s)
                            </span>
                          </div>
                          <span className="text-[10px] text-slate-500 block font-mono">
                            Bounds: [{o.lower_bound} to {o.upper_bound}]
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </Modal>

      {/* Generate Report Modal */}
      <Modal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        title="Generate Standalone Analysis Report"
        description="Creates a styled HTML report compiling all insights, descriptive stats, correlations, and audit notes."
        maxWidth="lg"
      >
        <div className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">
              Report Title
            </label>
            <input
              type="text"
              value={reportTitle}
              onChange={(e) => setReportTitle(e.target.value)}
              className="w-full text-xs rounded-lg border border-slate-300 bg-white p-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">
              Custom Executive Notes / Findings
            </label>
            <textarea
              rows={3}
              value={reportNotes}
              onChange={(e) => setReportNotes(e.target.value)}
              placeholder="Add custom annotations or conclusions to include in the executive summary..."
              className="w-full text-xs rounded-lg border border-slate-300 bg-white p-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsReportModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleSaveReport}
              disabled={isCreatingReport || !reportTitle.trim()}
              className="gap-1.5"
            >
              {isCreatingReport ? <Spinner size="sm" /> : <FileText className="w-3.5 h-3.5" />}
              Build & Save Report
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
