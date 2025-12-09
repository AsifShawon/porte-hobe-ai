/**
 * Goals API Client
 * Functions for interacting with goals endpoints
 */

import { apiClient } from './client';
import type {
  Goal,
  CreateGoalRequest,
  UpdateGoalRequest,
  GoalStats,
  GoalFilters,
} from '@/types';

export const goalsApi = {
  /**
   * Get all goals with optional filters
   */
  async getAll(filters?: GoalFilters): Promise<Goal[]> {
    const params: Record<string, string> = {};
    if (filters?.status) params.status = filters.status;
    if (filters?.goal_type) params.goal_type = filters.goal_type;

    return apiClient.get<Goal[]>('/api/goals', params);
  },

  /**
   * Get a specific goal by ID
   */
  async getById(id: string): Promise<Goal> {
    return apiClient.get<Goal>(`/api/goals/${id}`);
  },

  /**
   * Create a new goal
   */
  async create(data: CreateGoalRequest): Promise<Goal> {
    return apiClient.post<Goal>('/api/goals', data);
  },

  /**
   * Update a goal
   */
  async update(id: string, data: UpdateGoalRequest): Promise<Goal> {
    return apiClient.patch<Goal>(`/api/goals/${id}`, data);
  },

  /**
   * Delete a goal
   */
  async delete(id: string): Promise<{ message: string; goal_id: string }> {
    return apiClient.delete(`/api/goals/${id}`);
  },

  /**
   * Get goal statistics
   */
  async getStats(): Promise<GoalStats> {
    return apiClient.get<GoalStats>('/api/goals/stats/summary');
  },
};
