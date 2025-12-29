/**
 * AnalyticsDashboard - Main writing analytics dashboard
 * Shows comprehensive stats, trends, and visualizations
 */

import { useState, useEffect } from 'react';
import { analyticsApi, type WritingAnalytics } from '@/lib/api';
import { toast } from '@/stores/toastStore';
import WritingStreakCalendar from './WritingStreakCalendar';

interface AnalyticsDashboardProps {
  manuscriptId: string;
}

export default function AnalyticsDashboard({ manuscriptId }: AnalyticsDashboardProps) {
  const [analytics, setAnalytics] = useState<WritingAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState<number>(30);

  useEffect(() => {
    loadAnalytics();
  }, [manuscriptId, timeframe]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const data = await analyticsApi.getAnalytics(manuscriptId, timeframe);
      setAnalytics(data);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to load analytics';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-16 h-16 border-4 border-bronze border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="text-center py-20">
        <p className="text-faded-ink font-sans">No analytics data available</p>
      </div>
    );
  }

  return (
    <div className="analytics-dashboard p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="font-garamond text-4xl font-semibold text-midnight">
          Writing Analytics
        </h1>

        {/* Timeframe selector */}
        <div className="flex gap-2">
          {[
            { value: 7, label: '7 Days' },
            { value: 30, label: '30 Days' },
            { value: 90, label: '90 Days' },
            { value: 365, label: 'Year' },
          ].map((option) => (
            <button
              key={option.value}
              onClick={() => setTimeframe(option.value)}
              className={`px-4 py-2 rounded-sm font-sans text-sm transition-colors ${
                timeframe === option.value
                  ? 'bg-bronze text-white'
                  : 'bg-slate-ui text-midnight hover:bg-slate-ui/70'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Overview Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon="📝"
          label="Total Words"
          value={analytics.overview.total_words.toLocaleString()}
          subtitle={`${analytics.overview.total_chapters} chapters`}
        />
        <StatCard
          icon="✍️"
          label="Words This Period"
          value={analytics.overview.words_this_period.toLocaleString()}
          subtitle={`${analytics.overview.days_active} active days`}
        />
        <StatCard
          icon="🔥"
          label="Current Streak"
          value={`${analytics.overview.current_streak} ${analytics.overview.current_streak === 1 ? 'day' : 'days'}`}
          subtitle={`Best: ${analytics.overview.longest_streak} days`}
          highlight={analytics.overview.current_streak > 0}
        />
        <StatCard
          icon="⚡"
          label="Writing Sessions"
          value={analytics.overview.total_sessions.toString()}
          subtitle={`${timeframe} day period`}
        />
      </div>

      {/* Writing Streak Calendar */}
      <div className="bg-white border-2 border-slate-ui/30 rounded-sm shadow-sm p-6">
        <h2 className="font-garamond text-2xl font-semibold text-midnight mb-4">
          Writing Activity
        </h2>
        <WritingStreakCalendar dailyStats={analytics.daily_stats} days={timeframe} />
      </div>

      {/* Daily Progress Chart */}
      {analytics.daily_stats.length > 0 && (
        <div className="bg-white border-2 border-slate-ui/30 rounded-sm shadow-sm p-6">
          <h2 className="font-garamond text-2xl font-semibold text-midnight mb-4">
            Word Count Progress
          </h2>
          <SimpleBarChart data={analytics.daily_stats} />
        </div>
      )}

      {/* Recent Sessions */}
      {analytics.recent_sessions.length > 0 && (
        <div className="bg-white border-2 border-slate-ui/30 rounded-sm shadow-sm p-6">
          <h2 className="font-garamond text-2xl font-semibold text-midnight mb-4">
            Recent Sessions
          </h2>
          <div className="space-y-2">
            {analytics.recent_sessions.slice().reverse().map((session) => (
              <div
                key={session.id}
                className="flex items-center justify-between py-3 px-4 bg-vellum/50 rounded-sm border border-slate-ui/20"
              >
                <div className="flex-1">
                  <div className="font-sans text-sm text-midnight font-medium">
                    {session.label || 'Writing Session'}
                  </div>
                  <div className="font-sans text-xs text-faded-ink">
                    {new Date(session.date).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-sans text-lg font-semibold text-bronze">
                    {session.word_count.toLocaleString()}
                  </div>
                  <div className="font-sans text-xs text-faded-ink">words</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Stat Card Component
interface StatCardProps {
  icon: string;
  label: string;
  value: string;
  subtitle?: string;
  highlight?: boolean;
}

function StatCard({ icon, label, value, subtitle, highlight = false }: StatCardProps) {
  return (
    <div
      className={`bg-white border-2 rounded-sm shadow-sm p-6 transition-all ${
        highlight
          ? 'border-bronze bg-bronze/5'
          : 'border-slate-ui/30 hover:border-bronze/30'
      }`}
    >
      <div className="flex items-center gap-3 mb-2">
        <span className="text-3xl">{icon}</span>
        <h3 className="font-sans text-sm text-faded-ink uppercase tracking-wide">{label}</h3>
      </div>
      <div className="font-garamond text-3xl font-bold text-midnight mb-1">{value}</div>
      {subtitle && <div className="font-sans text-xs text-faded-ink">{subtitle}</div>}
    </div>
  );
}

// Simple Bar Chart Component
interface SimpleBarChartProps {
  data: Array<{
    date: string;
    word_count: number;
  }>;
}

function SimpleBarChart({ data }: SimpleBarChartProps) {
  const maxWords = Math.max(...data.map((d) => d.word_count), 1);

  return (
    <div className="space-y-1">
      {data.slice(-14).map((day) => {
        const percentage = (day.word_count / maxWords) * 100;

        return (
          <div key={day.date} className="flex items-center gap-2">
            <div className="w-20 text-xs text-faded-ink font-sans">
              {new Date(day.date).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
              })}
            </div>
            <div className="flex-1 flex items-center gap-2">
              <div className="flex-1 bg-slate-ui/20 rounded-sm h-8 relative overflow-hidden">
                <div
                  className="bg-bronze h-full rounded-sm transition-all duration-300"
                  style={{ width: `${percentage}%` }}
                ></div>
              </div>
              <div className="w-16 text-sm font-sans font-semibold text-midnight text-right">
                {day.word_count.toLocaleString()}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
