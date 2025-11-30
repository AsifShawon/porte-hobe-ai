/**
 * Achievements Data Fetching Hook
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { achievementsApi } from '@/lib/api';
import type {
  Achievement,
  AchievementProgress,
  AchievementStats,
  AchievementCategory,
  ApiError,
} from '@/types';

export function useAchievements(category?: AchievementCategory) {
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchAchievements = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await achievementsApi.getUnlocked(category);
      setAchievements(data);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setLoading(false);
    }
  }, [category]);

  useEffect(() => {
    fetchAchievements();
  }, [fetchAchievements]);

  return {
    achievements,
    loading,
    error,
    refetch: fetchAchievements,
  };
}

export function useAchievementProgress() {
  const [progress, setProgress] = useState<AchievementProgress[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchProgress = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await achievementsApi.getAvailable();
      setProgress(data);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProgress();
  }, [fetchProgress]);

  return {
    progress,
    loading,
    error,
    refetch: fetchProgress,
  };
}

export function useAchievementStats() {
  const [stats, setStats] = useState<AchievementStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await achievementsApi.getStats();
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

  const checkForNew = async () => {
    const result = await achievementsApi.check();
    if (result.count > 0) {
      // Refetch stats after new achievements
      await fetchStats();
    }
    return result;
  };

  return {
    stats,
    loading,
    error,
    refetch: fetchStats,
    checkForNew,
  };
}
