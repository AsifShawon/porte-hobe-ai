/**
 * Goals Page
 * Main goals dashboard - view, create, and manage study goals
 */

'use client';

import React, { useState } from 'react';
import { Target, TrendingUp, CheckCircle, Flame } from 'lucide-react';
import { PageHeader, StatsCard, LoadingState, ErrorState, EmptyState } from '@/components/shared';
import { GoalCard, CreateGoalDialog } from '@/components/goals';
import { useGoals, useGoalStats } from '@/hooks';
import type { CreateGoalRequest, UpdateGoalRequest, GoalStatus } from '@/types';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export default function GoalsPage() {
  const [statusFilter, setStatusFilter] = useState<GoalStatus | 'all'>('all');

  // Fetch goals with filter
  const {
    goals,
    loading: goalsLoading,
    error: goalsError,
    refetch,
    createGoal,
    updateGoal,
    deleteGoal,
  } = useGoals(statusFilter !== 'all' ? { status: statusFilter } : undefined);

  // Fetch stats
  const { stats, loading: statsLoading } = useGoalStats();

  const handleCreateGoal = async (data: CreateGoalRequest) => {
    await createGoal(data);
  };

  const handleUpdateGoal = async (id: string, data: UpdateGoalRequest) => {
    await updateGoal(id, data);
  };

  const handleDeleteGoal = async (id: string) => {
    if (confirm('Are you sure you want to delete this goal?')) {
      await deleteGoal(id);
    }
  };

  // Loading state
  if (goalsLoading && !goals.length) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Study Goals"
          description="Set and track your learning goals"
          icon={Target}
        />
        <LoadingState type="grid" count={3} />
      </div>
    );
  }

  // Error state
  if (goalsError) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Study Goals"
          description="Set and track your learning goals"
          icon={Target}
        />
        <ErrorState error={goalsError} onRetry={refetch} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        title="Study Goals"
        description="Set and track your learning goals"
        icon={Target}
        action={{
          label: 'Create Goal',
          onClick: () => {}, // Handled by dialog
          icon: Target,
        }}
      />

      {/* Stats Cards */}
      {!statsLoading && stats && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <StatsCard
            title="Total Goals"
            value={stats.total_goals}
            subtitle="All time"
            icon={Target}
          />
          <StatsCard
            title="Active Goals"
            value={stats.active_goals}
            subtitle="Currently tracking"
            icon={TrendingUp}
          />
          <StatsCard
            title="Completed"
            value={stats.completed_goals}
            subtitle={`${stats.completion_rate}% completion rate`}
            icon={CheckCircle}
          />
          <StatsCard
            title="Current Streak"
            value={stats.current_streak}
            subtitle={`${stats.longest_streak} days longest`}
            icon={Flame}
          />
        </div>
      )}

      {/* Filters and Create Button */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Select
            value={statusFilter}
            onValueChange={(value) => setStatusFilter(value as GoalStatus | 'all')}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Goals</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
              <SelectItem value="paused">Paused</SelectItem>
            </SelectContent>
          </Select>
          <span className="text-sm text-muted-foreground">
            {goals.length} goal{goals.length !== 1 ? 's' : ''}
          </span>
        </div>

        <CreateGoalDialog onCreateGoal={handleCreateGoal} />
      </div>

      {/* Goals List */}
      {goals.length === 0 ? (
        <EmptyState
          icon={Target}
          title="No goals yet"
          description="Create your first learning goal to start tracking your progress"
          action={{
            label: 'Create Goal',
            onClick: () => {}, // Handled by dialog
          }}
        />
      ) : (
        <div className="grid gap-6 md:grid-cols-2">
          {goals.map((goal) => (
            <GoalCard
              key={goal.id}
              goal={goal}
              onUpdate={handleUpdateGoal}
              onDelete={handleDeleteGoal}
            />
          ))}
        </div>
      )}
    </div>
  );
}
