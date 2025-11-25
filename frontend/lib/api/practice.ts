/**
 * Practice & Exercises API Client
 * Functions for interacting with practice endpoints
 */

import { apiClient } from './client';
import type {
  Exercise,
  ExerciseSubmission,
  Submission,
  PracticeStats,
  CreateExerciseRequest,
  ExerciseFilters,
  SubmissionStatus,
} from '@/types';

export const practiceApi = {
  /**
   * Get all exercises with optional filters
   */
  async getExercises(filters?: ExerciseFilters): Promise<Exercise[]> {
    const params: Record<string, string> = {};
    if (filters?.exercise_type) params.exercise_type = filters.exercise_type;
    if (filters?.difficulty) params.difficulty = filters.difficulty;
    if (filters?.topic_id) params.topic_id = filters.topic_id;
    if (filters?.completed !== undefined) params.completed = String(filters.completed);

    return apiClient.get<Exercise[]>('/api/practice/exercises', params);
  },

  /**
   * Get a specific exercise by ID
   */
  async getExercise(id: string): Promise<Exercise> {
    return apiClient.get<Exercise>(`/api/practice/exercises/${id}`);
  },

  /**
   * Submit an exercise solution
   */
  async submit(submission: ExerciseSubmission): Promise<Submission> {
    return apiClient.post<Submission>('/api/practice/submit', submission);
  },

  /**
   * Get user's submissions
   */
  async getSubmissions(
    exerciseId?: string,
    status?: SubmissionStatus,
    limit: number = 20
  ): Promise<Submission[]> {
    const params: Record<string, string> = { limit: String(limit) };
    if (exerciseId) params.exercise_id = exerciseId;
    if (status) params.status = status;

    return apiClient.get<Submission[]>('/api/practice/submissions', params);
  },

  /**
   * Get practice statistics
   */
  async getStats(): Promise<PracticeStats> {
    return apiClient.get<PracticeStats>('/api/practice/stats');
  },

  /**
   * Create a new exercise (admin/teacher)
   */
  async createExercise(data: CreateExerciseRequest): Promise<Exercise> {
    return apiClient.post<Exercise>('/api/practice/exercises', data);
  },
};
