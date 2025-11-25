/**
 * Progress API Client
 * Functions for interacting with progress endpoints
 */

import { apiClient } from './client';
import type {
  TopicProgress,
  UpdateProgressRequest,
  OverallStats,
  ProgressFilters,
} from '@/types';

export const progressApi = {
  /**
   * Get all progress records
   */
  async getAll(filters?: ProgressFilters): Promise<TopicProgress[]> {
    const params: Record<string, string> = {};
    if (filters?.status) params.status = filters.status;

    return apiClient.get<TopicProgress[]>('/api/progress', params);
  },

  /**
   * Get progress for a specific topic
   */
  async getByTopic(topicId: string): Promise<TopicProgress> {
    return apiClient.get<TopicProgress>(`/api/progress/topic/${topicId}`);
  },

  /**
   * Update progress for a topic
   */
  async update(data: UpdateProgressRequest): Promise<TopicProgress> {
    return apiClient.post<TopicProgress>('/api/progress/update', data);
  },

  /**
   * Get overall learning statistics
   */
  async getStats(): Promise<OverallStats> {
    return apiClient.get<OverallStats>('/api/progress/stats');
  },

  /**
   * Reset progress for a topic
   */
  async resetTopic(topicId: string): Promise<{ message: string; topic_id: string }> {
    return apiClient.delete(`/api/progress/topic/${topicId}`);
  },
};
