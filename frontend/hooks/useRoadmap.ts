/**
 * Custom React Hooks for Learning Roadmaps
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { roadmapApi } from '@/lib/api/roadmaps';
import type {
  LearningRoadmap,
  CreateRoadmapRequest,
  UpdateMilestoneRequest,
  AdaptRoadmapRequest,
  RoadmapFilters,
  MilestoneProgress,
} from '@/types/roadmap';
import type { ApiError } from '@/types/common';

/**
 * Hook to fetch and manage roadmaps
 */
export function useRoadmaps(filters?: RoadmapFilters) {
  const [roadmaps, setRoadmaps] = useState<LearningRoadmap[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchRoadmaps = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await roadmapApi.getRoadmaps(filters);
      setRoadmaps(response.roadmaps);
    } catch (err: any) {
      console.error('Error fetching roadmaps:', err);
      setError({
        message: err.message || 'Failed to fetch roadmaps',
        code: err.code,
      });
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchRoadmaps();
  }, [fetchRoadmaps]);

  const createRoadmap = async (request: CreateRoadmapRequest): Promise<LearningRoadmap | null> => {
    try {
      setError(null);
      const response = await roadmapApi.generateRoadmap(request);

      // Add new roadmap to the list
      setRoadmaps((prev) => [response.roadmap, ...prev]);

      return response.roadmap;
    } catch (err: any) {
      console.error('Error creating roadmap:', err);
      setError({
        message: err.message || 'Failed to create roadmap',
        code: err.code,
      });
      return null;
    }
  };

  const deleteRoadmap = async (roadmapId: string): Promise<boolean> => {
    try {
      setError(null);
      await roadmapApi.deleteRoadmap(roadmapId);

      // Remove from list
      setRoadmaps((prev) => prev.filter((r) => r.id !== roadmapId));

      return true;
    } catch (err: any) {
      console.error('Error deleting roadmap:', err);
      setError({
        message: err.message || 'Failed to delete roadmap',
        code: err.code,
      });
      return false;
    }
  };

  return {
    roadmaps,
    loading,
    error,
    refetch: fetchRoadmaps,
    createRoadmap,
    deleteRoadmap,
  };
}

/**
 * Hook to fetch and manage a single roadmap with progress
 */
export function useRoadmap(roadmapId: string | null) {
  const [roadmap, setRoadmap] = useState<LearningRoadmap | null>(null);
  const [milestoneProgress, setMilestoneProgress] = useState<MilestoneProgress[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchRoadmap = useCallback(async () => {
    if (!roadmapId) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await roadmapApi.getRoadmap(roadmapId);
      setRoadmap(response.roadmap);
      setMilestoneProgress(response.milestone_progress);
    } catch (err: any) {
      console.error('Error fetching roadmap:', err);
      setError({
        message: err.message || 'Failed to fetch roadmap',
        code: err.code,
      });
    } finally {
      setLoading(false);
    }
  }, [roadmapId]);

  useEffect(() => {
    fetchRoadmap();
  }, [fetchRoadmap]);

  const updateMilestone = async (
    phaseId: string,
    milestoneId: string,
    request: UpdateMilestoneRequest
  ): Promise<boolean> => {
    if (!roadmapId) return false;

    try {
      setError(null);
      const response = await roadmapApi.updateMilestone(roadmapId, phaseId, milestoneId, request);

      // Update milestone progress in state
      setMilestoneProgress((prev) =>
        prev.map((mp) =>
          mp.phase_id === phaseId && mp.milestone_id === milestoneId
            ? response.milestone_progress
            : mp
        )
      );

      // Refresh roadmap to get updated progress percentages
      await fetchRoadmap();

      return true;
    } catch (err: any) {
      console.error('Error updating milestone:', err);
      setError({
        message: err.message || 'Failed to update milestone',
        code: err.code,
      });
      return false;
    }
  };

  const startMilestone = async (phaseId: string, milestoneId: string): Promise<boolean> => {
    return updateMilestone(phaseId, milestoneId, {
      status: 'in_progress',
      progress_percentage: 0,
    });
  };

  const completeMilestone = async (
    phaseId: string,
    milestoneId: string,
    notes?: string
  ): Promise<boolean> => {
    return updateMilestone(phaseId, milestoneId, {
      status: 'completed',
      progress_percentage: 100,
      notes,
    });
  };

  const adaptRoadmap = async (request: AdaptRoadmapRequest): Promise<boolean> => {
    if (!roadmapId) return false;

    try {
      setError(null);
      const response = await roadmapApi.adaptRoadmap(roadmapId, request);

      // Update roadmap with adapted version
      setRoadmap(response.roadmap);

      return true;
    } catch (err: any) {
      console.error('Error adapting roadmap:', err);
      setError({
        message: err.message || 'Failed to adapt roadmap',
        code: err.code,
      });
      return false;
    }
  };

  return {
    roadmap,
    milestoneProgress,
    loading,
    error,
    refetch: fetchRoadmap,
    updateMilestone,
    startMilestone,
    completeMilestone,
    adaptRoadmap,
  };
}

/**
 * Hook to get the active roadmap for the user
 */
export function useActiveRoadmap() {
  const [roadmap, setRoadmap] = useState<LearningRoadmap | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchActiveRoadmap = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const activeRoadmap = await roadmapApi.getActiveRoadmap();
      setRoadmap(activeRoadmap);
    } catch (err: any) {
      console.error('Error fetching active roadmap:', err);
      setError({
        message: err.message || 'Failed to fetch active roadmap',
        code: err.code,
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchActiveRoadmap();
  }, [fetchActiveRoadmap]);

  return {
    roadmap,
    loading,
    error,
    refetch: fetchActiveRoadmap,
  };
}

/**
 * Hook to get overall progress statistics
 */
export function useRoadmapStats() {
  const [stats, setStats] = useState({
    total_roadmaps: 0,
    active_roadmaps: 0,
    completed_roadmaps: 0,
    total_milestones: 0,
    completed_milestones: 0,
    average_progress: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const progressStats = await roadmapApi.getOverallProgress();
      setStats(progressStats);
    } catch (err: any) {
      console.error('Error fetching roadmap stats:', err);
      setError({
        message: err.message || 'Failed to fetch statistics',
        code: err.code,
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return {
    stats,
    loading,
    error,
    refetch: fetchStats,
  };
}
