/**
 * Goals Data Fetching Hook
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { goalsApi } from '@/lib/api';
import type {
  Goal,
  GoalFilters,
  GoalStats,
  CreateGoalRequest,
  UpdateGoalRequest,
  ApiError,
} from '@/types';

export function useGoals(filters?: GoalFilters) {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchGoals = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await goalsApi.getAll(filters);
      setGoals(data);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchGoals();
  }, [fetchGoals]);

  const createGoal = async (data: CreateGoalRequest) => {
    const newGoal = await goalsApi.create(data);
    setGoals((prev) => [newGoal, ...prev]);
    return newGoal;
  };

  const updateGoal = async (id: string, data: UpdateGoalRequest) => {
    const updated = await goalsApi.update(id, data);
    setGoals((prev) => prev.map((g) => (g.id === id ? updated : g)));
    return updated;
  };

  const deleteGoal = async (id: string) => {
    await goalsApi.delete(id);
    setGoals((prev) => prev.filter((g) => g.id !== id));
  };

  return {
    goals,
    loading,
    error,
    refetch: fetchGoals,
    createGoal,
    updateGoal,
    deleteGoal,
  };
}

export function useGoalStats() {
  const [stats, setStats] = useState<GoalStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await goalsApi.getStats();
      setStats(data);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return { stats, loading, error, refetch: fetchStats };
}
