/**
 * API Client for Quizzes and Quiz Attempts
 */

import { ApiClient } from './client';
import type {
  ConversationQuiz,
  QuizAttempt,
  GenerateQuizRequest,
  GenerateQuizResponse,
  StartAttemptRequest,
  StartAttemptResponse,
  SubmitAnswerRequest,
  SubmitAnswerResponse,
  CompleteQuizResponse,
  QuizFilters,
  QuizStats,
} from '@/types/quiz';

class QuizApiClient extends ApiClient {
  /**
   * Generate a new quiz based on topics
   * Uses Next.js API route proxy for better error handling
   */
  async generateQuiz(request: GenerateQuizRequest): Promise<GenerateQuizResponse> {
    // Use the Next.js API proxy route instead of direct backend call
    const response = await fetch('/api/quizzes/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw {
        status: response.status,
        message: errorData.error || 'Failed to generate quiz',
        detail: errorData.detail,
      };
    }

    return response.json();
  }

  /**
   * Get all quizzes for the current user (quiz library)
   */
  async getQuizzes(filters?: QuizFilters): Promise<{ quizzes: ConversationQuiz[]; count: number }> {
    const params = new URLSearchParams();

    if (filters?.roadmap_id) params.append('roadmap_id', filters.roadmap_id);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.difficulty) params.append('difficulty', filters.difficulty);
    if (filters?.limit) params.append('limit', filters.limit.toString());

    const query = params.toString();
    const endpoint = query ? `/api/quizzes?${query}` : '/api/quizzes';

    return this.request<{ quizzes: ConversationQuiz[]; count: number }>(endpoint);
  }

  /**
   * Get a specific quiz
   */
  async getQuiz(quizId: string): Promise<{ quiz: ConversationQuiz; attempts: QuizAttempt[] }> {
    return this.request<{ quiz: ConversationQuiz; attempts: QuizAttempt[] }>(
      `/api/quizzes/${quizId}`
    );
  }

  /**
   * Start a new quiz attempt
   */
  async startAttempt(request: StartAttemptRequest): Promise<StartAttemptResponse> {
    return this.request<StartAttemptResponse>('/api/quizzes/attempt', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Submit an answer for grading
   */
  async submitAnswer(
    attemptId: string,
    request: SubmitAnswerRequest
  ): Promise<SubmitAnswerResponse> {
    return this.request<SubmitAnswerResponse>(`/api/quizzes/attempt/${attemptId}/answer`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Complete a quiz attempt and get final results
   */
  async completeAttempt(attemptId: string): Promise<CompleteQuizResponse> {
    return this.request<CompleteQuizResponse>(`/api/quizzes/attempt/${attemptId}/complete`, {
      method: 'POST',
    });
  }

  /**
   * Get details of a specific attempt
   */
  async getAttempt(attemptId: string): Promise<{ attempt: QuizAttempt; quiz: ConversationQuiz }> {
    return this.request<{ attempt: QuizAttempt; quiz: ConversationQuiz }>(
      `/api/quizzes/attempt/${attemptId}`
    );
  }

  /**
   * Get overall quiz statistics for the user
   */
  async getStats(): Promise<{ stats: QuizStats }> {
    return this.request<{ stats: QuizStats }>('/api/quizzes/stats/summary');
  }

  /**
   * Get quizzes for a specific roadmap
   */
  async getQuizzesForRoadmap(roadmapId: string): Promise<ConversationQuiz[]> {
    const response = await this.getQuizzes({ roadmap_id: roadmapId, limit: 50 });
    return response.quizzes;
  }

  /**
   * Get recent quizzes (last 10)
   */
  async getRecentQuizzes(): Promise<ConversationQuiz[]> {
    const response = await this.getQuizzes({ limit: 10 });
    return response.quizzes;
  }

  /**
   * Get completed quizzes
   */
  async getCompletedQuizzes(limit = 20): Promise<ConversationQuiz[]> {
    const response = await this.getQuizzes({ status: 'completed', limit });
    return response.quizzes;
  }

  /**
   * Get in-progress quizzes
   */
  async getInProgressQuizzes(): Promise<ConversationQuiz[]> {
    const response = await this.getQuizzes({ status: 'in_progress', limit: 10 });
    return response.quizzes;
  }

  /**
   * Retry a quiz (start a new attempt on an existing quiz)
   */
  async retryQuiz(quizId: string): Promise<StartAttemptResponse> {
    return this.startAttempt({ quiz_id: quizId });
  }

  /**
   * Get best score for a quiz
   */
  async getBestScore(quizId: string): Promise<number> {
    const { attempts } = await this.getQuiz(quizId);
    const completedAttempts = attempts.filter((a) => a.status === 'completed');

    if (completedAttempts.length === 0) return 0;

    return Math.max(...completedAttempts.map((a) => a.percentage_score));
  }

  /**
   * Check if user can attempt a quiz (based on attempts limit)
   */
  async canAttemptQuiz(quizId: string): Promise<boolean> {
    const { quiz, attempts } = await this.getQuiz(quizId);
    return attempts.length < quiz.attempts_allowed;
  }
}

// Export singleton instance
export const quizApi = new QuizApiClient();
