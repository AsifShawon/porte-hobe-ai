/**
 * API Client for Learning Roadmaps
 */

import { ApiClient } from './client';
import type {
  LearningRoadmap,
  CreateRoadmapRequest,
  CreateRoadmapResponse,
  UpdateMilestoneRequest,
  AdaptRoadmapRequest,
  RoadmapFilters,
  MilestoneProgress,
} from '@/types/roadmap';

class RoadmapApiClient extends ApiClient {
  /**
   * Generate a new learning roadmap based on user goals
   */
  async generateRoadmap(request: CreateRoadmapRequest): Promise<CreateRoadmapResponse> {
    return this.request<CreateRoadmapResponse>('/api/roadmaps/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Get all roadmaps for the current user
   */
  async getRoadmaps(filters?: RoadmapFilters): Promise<{ roadmaps: LearningRoadmap[]; count: number }> {
    const params = new URLSearchParams();

    if (filters?.status) params.append('status', filters.status);
    if (filters?.domain) params.append('domain', filters.domain);
    if (filters?.limit) params.append('limit', filters.limit.toString());

    const query = params.toString();
    const endpoint = query ? `/api/roadmaps?${query}` : '/api/roadmaps';

    return this.request<{ roadmaps: LearningRoadmap[]; count: number }>(endpoint);
  }

  /**
   * Get a specific roadmap with progress details
   */
  async getRoadmap(roadmapId: string): Promise<{
    roadmap: LearningRoadmap;
    milestone_progress: MilestoneProgress[];
  }> {
    return this.request<{
      roadmap: LearningRoadmap;
      milestone_progress: MilestoneProgress[];
    }>(`/api/roadmaps/${roadmapId}`);
  }

  /**
   * Update progress on a specific milestone
   */
  async updateMilestone(
    roadmapId: string,
    phaseId: string,
    milestoneId: string,
    request: UpdateMilestoneRequest
  ): Promise<{ status: string; milestone_progress: MilestoneProgress }> {
    return this.request<{ status: string; milestone_progress: MilestoneProgress }>(
      `/api/roadmaps/${roadmapId}/milestone/${phaseId}/${milestoneId}`,
      {
        method: 'PUT',
        body: JSON.stringify(request),
      }
    );
  }

  /**
   * Mark a milestone as started
   */
  async startMilestone(
    roadmapId: string,
    phaseId: string,
    milestoneId: string
  ): Promise<{ status: string; milestone_progress: MilestoneProgress }> {
    return this.updateMilestone(roadmapId, phaseId, milestoneId, {
      status: 'in_progress',
      progress_percentage: 0,
    });
  }

  /**
   * Mark a milestone as completed
   */
  async completeMilestone(
    roadmapId: string,
    phaseId: string,
    milestoneId: string,
    notes?: string
  ): Promise<{ status: string; milestone_progress: MilestoneProgress }> {
    return this.updateMilestone(roadmapId, phaseId, milestoneId, {
      status: 'completed',
      progress_percentage: 100,
      notes,
    });
  }

  /**
   * Adapt roadmap based on user performance (AI-powered)
   */
  async adaptRoadmap(
    roadmapId: string,
    request: AdaptRoadmapRequest
  ): Promise<{ status: string; message: string; roadmap: LearningRoadmap }> {
    return this.request<{ status: string; message: string; roadmap: LearningRoadmap }>(
      `/api/roadmaps/${roadmapId}/adapt`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );
  }

  /**
   * Delete (abandon) a roadmap
   */
  async deleteRoadmap(roadmapId: string): Promise<{ status: string; message: string }> {
    return this.request<{ status: string; message: string }>(
      `/api/roadmaps/${roadmapId}`,
      {
        method: 'DELETE',
      }
    );
  }

  /**
   * Get the active roadmap for the user (most recent active roadmap)
   */
  async getActiveRoadmap(): Promise<LearningRoadmap | null> {
    const response = await this.getRoadmaps({ status: 'active', limit: 1 });
    return response.roadmaps.length > 0 ? response.roadmaps[0] : null;
  }

  /**
   * Calculate overall progress across all active roadmaps
   */
  async getOverallProgress(): Promise<{
    total_roadmaps: number;
    active_roadmaps: number;
    completed_roadmaps: number;
    total_milestones: number;
    completed_milestones: number;
    average_progress: number;
  }> {
    const allRoadmaps = await this.getRoadmaps({ limit: 100 });

    const stats = {
      total_roadmaps: allRoadmaps.count,
      active_roadmaps: allRoadmaps.roadmaps.filter((r) => r.status === 'active').length,
      completed_roadmaps: allRoadmaps.roadmaps.filter((r) => r.status === 'completed').length,
      total_milestones: allRoadmaps.roadmaps.reduce((sum, r) => sum + r.total_milestones, 0),
      completed_milestones: allRoadmaps.roadmaps.reduce((sum, r) => sum + r.completed_milestones, 0),
      average_progress: 0,
    };

    stats.average_progress =
      stats.total_roadmaps > 0
        ? allRoadmaps.roadmaps.reduce((sum, r) => sum + r.progress_percentage, 0) / stats.total_roadmaps
        : 0;

    return stats;
  }
}

// Export singleton instance
export const roadmapApi = new RoadmapApiClient();
