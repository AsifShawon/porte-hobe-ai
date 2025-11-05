"use client";

import React, { useEffect, useState } from 'react';
import { TrendingUp, Target, Clock, Flame, Trophy, BookOpen, Award } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { cn } from '@/lib/utils';

interface Achievement {
  title: string;
  description: string;
  icon: string;
}

interface ProgressStats {
  total_topics: number;
  completed_topics: number;
  in_progress_topics: number;
  average_score: number;
  total_time_spent: number;
  streak_days: number;
  achievements: Achievement[];
}

interface ProgressCardProps {
  className?: string;
}

export default function ProgressCard({ className }: ProgressCardProps) {
  const [stats, setStats] = useState<ProgressStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      
      // Use Next.js API route instead of direct backend call
      const response = await fetch('/api/progress/stats', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to fetch stats: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      setStats(data);
      setError(null);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load progress';
      setError(errorMsg);
      console.error('Error fetching stats:', errorMsg);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className={cn("bg-white dark:bg-gray-900 rounded-lg border p-6", className)}>
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 dark:bg-gray-800 rounded w-1/3"></div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-24 bg-gray-200 dark:bg-gray-800 rounded"></div>
            ))}
          </div>
          <div className="h-64 bg-gray-200 dark:bg-gray-800 rounded"></div>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className={cn("bg-white dark:bg-gray-900 rounded-lg border p-6", className)}>
        <div className="text-center py-8">
          <p className="text-red-500 mb-4">{error || 'No data available'}</p>
          {error?.includes('fetch') && (
            <div className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
              <p>💡 Make sure the backend server is running:</p>
              <code className="block bg-gray-100 dark:bg-gray-800 p-2 rounded">
                cd server && python main.py
              </code>
              <p className="mt-2">Check that NEXT_PUBLIC_API_URL is set in .env.local</p>
            </div>
          )}
          <button
            onClick={fetchStats}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Calculate completion percentage
  const completionPercentage = stats.total_topics > 0
    ? Math.round((stats.completed_topics / stats.total_topics) * 100)
    : 0;

  // Prepare chart data
  const topicData = [
    { name: 'Completed', value: stats.completed_topics, fill: '#10b981' },
    { name: 'In Progress', value: stats.in_progress_topics, fill: '#3b82f6' },
    { name: 'Not Started', value: stats.total_topics - stats.completed_topics - stats.in_progress_topics, fill: '#6b7280' },
  ];

  // Mock time series data (you can enhance this with real data)
  const timeSeriesData = [
    { day: 'Mon', score: 75 },
    { day: 'Tue', score: 82 },
    { day: 'Wed', score: 78 },
    { day: 'Thu', score: 85 },
    { day: 'Fri', score: stats.average_score },
  ];

  return (
    <div className={cn("bg-white dark:bg-gray-900 rounded-lg border", className)}>
      {/* Header */}
      <div className="p-6 border-b">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">Learning Progress</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Track your learning journey
            </p>
          </div>
          <button
            onClick={fetchStats}
            className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="p-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Total Topics */}
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <BookOpen className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Topics</span>
          </div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {stats.total_topics}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {stats.completed_topics} completed
          </div>
        </div>

        {/* Average Score */}
        <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Target className="w-5 h-5 text-green-600 dark:text-green-400" />
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Avg Score</span>
          </div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {stats.average_score.toFixed(1)}%
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {stats.average_score >= 80 ? '🎯 Excellent!' : stats.average_score >= 60 ? '👍 Good' : '💪 Keep going'}
          </div>
        </div>

        {/* Time Spent */}
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Time</span>
          </div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {Math.round(stats.total_time_spent / 60)}h
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {stats.total_time_spent} minutes
          </div>
        </div>

        {/* Streak */}
        <div className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Flame className="w-5 h-5 text-orange-600 dark:text-orange-400" />
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Streak</span>
          </div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {stats.streak_days}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            days active
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="p-6 space-y-6">
        {/* Progress Overview */}
        <div>
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            Topic Distribution
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topicData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
                <XAxis 
                  dataKey="name" 
                  className="text-sm"
                  tick={{ fill: 'currentColor' }}
                />
                <YAxis 
                  className="text-sm"
                  tick={{ fill: 'currentColor' }}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'var(--tooltip-bg)',
                    border: '1px solid var(--tooltip-border)',
                    borderRadius: '0.5rem'
                  }}
                />
                <Bar dataKey="value" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Score Trend */}
        {stats.average_score > 0 && (
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Target className="w-5 h-5 text-green-600" />
              Score Trend
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={timeSeriesData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
                  <XAxis 
                    dataKey="day" 
                    className="text-sm"
                    tick={{ fill: 'currentColor' }}
                  />
                  <YAxis 
                    domain={[0, 100]} 
                    className="text-sm"
                    tick={{ fill: 'currentColor' }}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'var(--tooltip-bg)',
                      border: '1px solid var(--tooltip-border)',
                      borderRadius: '0.5rem'
                    }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="score" 
                    stroke="#10b981" 
                    strokeWidth={3}
                    dot={{ fill: '#10b981', r: 6 }}
                    activeDot={{ r: 8 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Completion Progress Bar */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Overall Completion
            </span>
            <span className="text-sm font-bold text-blue-600 dark:text-blue-400">
              {completionPercentage}%
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
            <div
              className="bg-gradient-to-r from-blue-500 to-green-500 h-3 rounded-full transition-all duration-500"
              style={{ width: `${completionPercentage}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
            <span>{stats.completed_topics} completed</span>
            <span>{stats.total_topics} total</span>
          </div>
        </div>
      </div>

      {/* Achievements */}
      {stats.achievements && stats.achievements.length > 0 && (
        <div className="p-6 border-t">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Trophy className="w-5 h-5 text-yellow-600" />
            Achievements
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {stats.achievements.map((achievement, index) => (
              <div
                key={index}
                className="flex items-start gap-3 p-3 bg-gradient-to-r from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800"
              >
                <div className="text-2xl flex-shrink-0">
                  {achievement.icon}
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900 dark:text-white">
                    {achievement.title}
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {achievement.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {stats.total_topics === 0 && (
        <div className="p-12 text-center">
          <Award className="w-16 h-16 text-gray-300 dark:text-gray-700 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
            Start Your Learning Journey
          </h3>
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            Begin learning to track your progress and earn achievements
          </p>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
            Browse Topics
          </button>
        </div>
      )}
    </div>
  );
}

// Separate component for a compact progress summary
export function ProgressSummary({ className }: { className?: string }) {
  const [stats, setStats] = useState<ProgressStats | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const { createSupabaseBrowserClient } = await import('@/lib/supabaseClient');
        const supabase = createSupabaseBrowserClient();
        const { data: { session } } = await supabase.auth.getSession();

        if (!session?.access_token) return;

        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/progress/stats`, {
          headers: { 'Authorization': `Bearer ${session.access_token}` },
        });

        if (response.ok) {
          setStats(await response.json());
        }
      } catch (err) {
        console.error('Error fetching stats:', err);
      }
    };

    fetchStats();
  }, []);

  if (!stats) return null;

  return (
    <div className={cn("flex items-center gap-4 text-sm", className)}>
      <div className="flex items-center gap-1">
        <BookOpen className="w-4 h-4 text-blue-600" />
        <span className="font-medium">{stats.completed_topics}/{stats.total_topics}</span>
      </div>
      <div className="flex items-center gap-1">
        <Target className="w-4 h-4 text-green-600" />
        <span className="font-medium">{stats.average_score.toFixed(0)}%</span>
      </div>
      <div className="flex items-center gap-1">
        <Flame className="w-4 h-4 text-orange-600" />
        <span className="font-medium">{stats.streak_days}d</span>
      </div>
    </div>
  );
}
