import React, { useState } from 'react';
import {
  useDatasetProfile,
  useDatasetCharts,
  useDatasetDistributions,
  useDatasetManagementMutations,
} from '../../hooks/useDatasetManagement';
import { Spinner } from '../../components/ui/Spinner';
import { Button } from '../../components/ui/Button';
import {
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
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';
import {
  BarChart2,
  PieChart as PieIcon,
  Plus,
  Trash2,
  Sliders,
  TrendingUp,
  Layers,
  Sparkles,
  Info,
} from 'lucide-react';

interface DatasetAnalyticsTabProps {
  datasetId: string;
}

const COLORS = ['#4F46E5', '#06B6D4', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#6366F1'];

export function DatasetAnalyticsTab({ datasetId }: DatasetAnalyticsTabProps) {
  const { data: profile } = useDatasetProfile(datasetId);
  const { data: savedCharts, isLoading: loadingCharts } = useDatasetCharts(datasetId);
  const { data: distributionsData, isLoading: loadingDist } = useDatasetDistributions(datasetId);
  const { createChartMutation, deleteChartMutation } = useDatasetManagementMutations(datasetId);

  const [showBuilder, setShowBuilder] = useState<boolean>(false);
  const [chartName, setChartName] = useState<string>('');
  const [chartType, setChartType] = useState<string>('bar');
  const [xField, setXField] = useState<string>('');
  const [yField, setYField] = useState<string>('');
  const [aggregation, setAggregation] = useState<string>('count');

  const columns = profile?.columns || [];
  const distributions = distributionsData?.distributions || {};

  const handleCreateChart = async () => {
    if (!xField) return;
    try {
      await createChartMutation.mutateAsync({
        chartName: chartName || `${xField.replace('_', ' ').toUpperCase()} Distribution`,
        chartType,
        configuration: {
          x_field: xField,
          y_field: yField || undefined,
          aggregation,
        },
      });
      setShowBuilder(false);
      setChartName('');
      setXField('');
      setYField('');
    } catch (err: any) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Create Chart CTA */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-indigo-600 font-bold text-sm">
            <TrendingUp className="w-4 h-4" />
            <span>Interactive Visual Analytics</span>
          </div>
          <h3 className="text-lg font-bold text-slate-900 mt-1">Explore Real-World Dataset Insights</h3>
          <p className="text-xs text-slate-500">
            Real distributions, categorical breakdowns, and customized aggregation charts powered by Recharts.
          </p>
        </div>

        <Button
          onClick={() => setShowBuilder(!showBuilder)}
          size="sm"
          className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs gap-1.5 shrink-0"
        >
          <Plus className="w-4 h-4" />
          Create Custom Chart
        </Button>
      </div>

      {/* Dynamic Chart Builder Form Modal/Panel */}
      {showBuilder && (
        <div className="bg-indigo-50/50 border border-indigo-200 rounded-xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-indigo-600" />
              Dynamic Chart Builder
            </h4>
            <button
              onClick={() => setShowBuilder(false)}
              className="text-xs text-slate-500 hover:text-slate-700 font-medium"
            >
              Close
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">Chart Title</label>
              <input
                type="text"
                value={chartName}
                onChange={(e) => setChartName(e.target.value)}
                placeholder="e.g. Job Postings by City"
                className="w-full text-xs border border-slate-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">Chart Type</label>
              <select
                value={chartType}
                onChange={(e) => setChartType(e.target.value)}
                className="w-full text-xs border border-slate-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-indigo-500"
              >
                <option value="bar">Bar Chart</option>
                <option value="line">Line Chart</option>
                <option value="pie">Pie / Donut Chart</option>
                <option value="area">Area Chart</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">Group By / X-Axis</label>
              <select
                value={xField}
                onChange={(e) => setXField(e.target.value)}
                className="w-full text-xs border border-slate-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Select column...</option>
                {columns.map((c) => (
                  <option key={c.column_name} value={c.column_name}>
                    {c.column_name} ({c.inferred_type})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">Aggregation</label>
              <select
                value={aggregation}
                onChange={(e) => setAggregation(e.target.value)}
                className="w-full text-xs border border-slate-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-indigo-500"
              >
                <option value="count">Count Records</option>
                <option value="avg">Average of Y-Axis</option>
                <option value="sum">Sum of Y-Axis</option>
                <option value="distinct_count">Distinct Count</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <Button
              onClick={handleCreateChart}
              disabled={createChartMutation.isPending || !xField}
              size="sm"
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs"
            >
              {createChartMutation.isPending ? <Spinner size="sm" /> : <Sparkles className="w-3.5 h-3.5 mr-1" />}
              Save & Render Chart
            </Button>
          </div>
        </div>
      )}

      {/* Saved Custom Charts */}
      {savedCharts && savedCharts.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {savedCharts.map((chart) => {
            const data = chart.computed_data || [];
            return (
              <div key={chart.id} className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">{chart.chart_name}</h4>
                    <span className="text-[11px] text-slate-400">
                      Type: {chart.chart_type.toUpperCase()} · X: {chart.configuration.x_field}
                    </span>
                  </div>
                  <button
                    onClick={() => deleteChartMutation.mutate(chart.id)}
                    className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-slate-50 transition-colors"
                    title="Delete Chart"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <div className="h-64 w-full pt-2">
                  {data.length === 0 ? (
                    <div className="h-full flex items-center justify-center text-xs text-slate-400 italic">
                      No data points available for this configuration.
                    </div>
                  ) : chart.chart_type === 'pie' ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={data}
                          cx="50%"
                          cy="50%"
                          innerRadius={50}
                          outerRadius={80}
                          paddingAngle={3}
                          dataKey="value"
                          nameKey="name"
                          label
                        >
                          {data.map((_, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : chart.chart_type === 'line' ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={data} margin={{ top: 5, right: 20, left: -20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                        <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748B' }} />
                        <YAxis tick={{ fontSize: 10, fill: '#64748B' }} />
                        <Tooltip />
                        <Line type="monotone" dataKey="value" stroke="#4F46E5" strokeWidth={2} dot={{ r: 3 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : chart.chart_type === 'area' ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={data} margin={{ top: 5, right: 20, left: -20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                        <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748B' }} />
                        <YAxis tick={{ fontSize: 10, fill: '#64748B' }} />
                        <Tooltip />
                        <Area type="monotone" dataKey="value" stroke="#06B6D4" fill="#E0F2FE" />
                      </AreaChart>
                    </ResponsiveContainer>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={data} margin={{ top: 5, right: 20, left: -20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                        <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748B' }} />
                        <YAxis tick={{ fontSize: 10, fill: '#64748B' }} />
                        <Tooltip />
                        <Bar dataKey="value" fill="#4F46E5" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Automated Distribution Breakdown Section */}
      <div className="space-y-4">
        <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <Layers className="w-4 h-4 text-slate-600" />
          Automated Field Distribution Histograms
        </h4>

        {loadingDist ? (
          <div className="flex justify-center p-8">
            <Spinner size="md" />
          </div>
        ) : Object.keys(distributions).length === 0 ? (
          <p className="text-xs text-slate-400 italic">No distribution data calculated.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(distributions).map(([colName, dist]: [string, any]) => {
              if (!dist || !dist.data || dist.data.length === 0) return null;
              const isNumeric = dist.type === 'numeric';
              const chartData = dist.data.map((d: any) => ({
                label: isNumeric ? d.bin : d.category,
                count: d.count,
              }));

              return (
                <div key={colName} className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-800">{colName}</span>
                    <span className="text-[10px] font-semibold text-slate-400 uppercase">
                      {dist.type}
                    </span>
                  </div>

                  <div className="h-36 w-full pt-1">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={chartData} margin={{ top: 5, right: 5, left: -25, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F8FAFC" />
                        <XAxis dataKey="label" tick={{ fontSize: 9, fill: '#94A3B8' }} />
                        <YAxis tick={{ fontSize: 9, fill: '#94A3B8' }} />
                        <Tooltip />
                        <Bar dataKey="count" fill="#6366F1" radius={[3, 3, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
