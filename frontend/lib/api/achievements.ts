/**
 * Achievements API Client
 * Functions for interacting with achievements endpoints
 */

import { apiClient } from './client';
import type {
  Achievement,
  AchievementProgress,
  AchievementStats,
  CheckAchievementsResponse,
  AchievementCategory,
} from '@/types';

export const achievementsApi = {
  /**
   * Get all available achievements with progress
   */
  async getAvailable(): Promise<AchievementProgress[]> {
    return apiClient.get<AchievementProgress[]>('/api/achievements/available');
  },

  /**
   * Get unlocked achievements
   */
  async getUnlocked(category?: AchievementCategory): Promise<Achievement[]> {
    const params: Record<string, string> = {};
    if (category) params.category = category;

    return apiClient.get<Achievement[]>('/api/achievements/unlocked', params);
  },

  /**
   * Check and unlock new achievements
   */
  async check(): Promise<CheckAchievementsResponse> {
    return apiClient.post<CheckAchievementsResponse>('/api/achievements/check');
  },

  /**
   * Get achievement statistics
   */
  async getStats(): Promise<AchievementStats> {
    return apiClient.get<AchievementStats>('/api/achievements/stats');
  },

  /**
   * Get leaderboard
   */
  async getLeaderboard(limit: number = 10): Promise<any> {
    return apiClient.get(`/api/achievements/leaderboard?limit=${limit}`);
  },
};
