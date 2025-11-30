/**
 * Practice & Exercises Data Fetching Hook
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { practiceApi } from '@/lib/api';
import type {
  Exercise,
  ExerciseFilters,
  Submission,
  PracticeStats,
  ExerciseSubmission,
  ApiError,
} from '@/types';

export function useExercises(filters?: ExerciseFilters) {
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchExercises = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await practiceApi.getExercises(filters);
      setExercises(data);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchExercises();
  }, [fetchExercises]);

  return {
    exercises,
    loading,
    error,
    refetch: fetchExercises,
  };
}

export function useExercise(id: string) {
  const [exercise, setExercise] = useState<Exercise | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchExercise = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await practiceApi.getExercise(id);
      setExercise(data);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (id) {
      fetchExercise();
    }
  }, [fetchExercise, id]);

  const submitAnswer = async (submission: ExerciseSubmission) => {
    const result = await practiceApi.submit(submission);
    // Refetch exercise to update attempts and completion status
    await fetchExercise();
    return result;
  };

  return {
    exercise,
    loading,
    error,
    refetch: fetchExercise,
    submitAnswer,
  };
}

export function useSubmissions(exerciseId?: string, limit: number = 20) {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchSubmissions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await practiceApi.getSubmissions(exerciseId, undefined, limit);
      setSubmissions(data);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setLoading(false);
    }
  }, [exerciseId, limit]);

  useEffect(() => {
    fetchSubmissions();
  }, [fetchSubmissions]);

  return {
    submissions,
    loading,
    error,
    refetch: fetchSubmissions,
  };
}

export function usePracticeStats() {
  const [stats, setStats] = useState<PracticeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await practiceApi.getStats();
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
