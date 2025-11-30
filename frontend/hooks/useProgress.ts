/**
 * Progress Data Fetching Hook
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { progressApi } from '@/lib/api';
import type {
  TopicProgress,
  OverallStats,
  ProgressFilters,
  UpdateProgressRequest,
  ApiError,
} from '@/types';

export function useProgress(filters?: ProgressFilters) {
  const [progress, setProgress] = useState<TopicProgress[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchProgress = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await progressApi.getAll(filters);
      setProgress(data);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchProgress();
  }, [fetchProgress]);

  const updateProgress = async (data: UpdateProgressRequest) => {
    const updated = await progressApi.update(data);
    setProgress((prev) =>
      prev.map((p) => (p.topic_id === data.topic_id ? updated : p))
    );
    return updated;
  };

  return {
    progress,
    loading,
    error,
    refetch: fetchProgress,
    updateProgress,
  };
}

export function useProgressStats() {
  const [stats, setStats] = useState<OverallStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await progressApi.getStats();
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
