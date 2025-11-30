/**
 * Custom React Hooks for Quizzes and Quiz Attempts
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { quizApi } from '@/lib/api/quizzes';
import type {
  ConversationQuiz,
  QuizAttempt,
  GenerateQuizRequest,
  SubmitAnswerRequest,
  QuizFilters,
  QuizStats,
  QuizResults,
} from '@/types/quiz';
import type { ApiError } from '@/types/common';

/**
 * Hook to fetch and manage quizzes (quiz library)
 */
export function useQuizzes(filters?: QuizFilters, options: { enabled?: boolean } = { enabled: true }) {
  const [quizzes, setQuizzes] = useState<ConversationQuiz[]>([]);
  const [loading, setLoading] = useState(options.enabled);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchQuizzes = useCallback(async () => {
    if (!options.enabled) return;

    try {
      setLoading(true);
      setError(null);

      const response = await quizApi.getQuizzes(filters);
      setQuizzes(response.quizzes);
    } catch (err: any) {
      console.error('Error fetching quizzes:', err);
      setError({
        message: err.message || 'Failed to fetch quizzes',
        code: err.code,
      });
    } finally {
      setLoading(false);
    }
  }, [filters, options.enabled]);

  useEffect(() => {
    fetchQuizzes();
  }, [fetchQuizzes]);

  const generateQuiz = async (request: GenerateQuizRequest): Promise<ConversationQuiz | null> => {
    try {
      setError(null);
      const response = await quizApi.generateQuiz(request);

      // Add new quiz to the list
      setQuizzes((prev) => [response.quiz, ...prev]);

      return response.quiz;
    } catch (err: any) {
      console.error('Error generating quiz:', err);
      setError({
        message: err.message || 'Failed to generate quiz',
        code: err.code,
      });
      return null;
    }
  };

  return {
    quizzes,
    loading,
    error,
    refetch: fetchQuizzes,
    generateQuiz,
  };
}

/**
 * Hook to fetch and manage a single quiz
 */
export function useQuiz(quizId: string | null) {
  const [quiz, setQuiz] = useState<ConversationQuiz | null>(null);
  const [attempts, setAttempts] = useState<QuizAttempt[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchQuiz = useCallback(async () => {
    if (!quizId) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await quizApi.getQuiz(quizId);
      setQuiz(response.quiz);
      setAttempts(response.attempts);
    } catch (err: any) {
      console.error('Error fetching quiz:', err);
      setError({
        message: err.message || 'Failed to fetch quiz',
        code: err.code,
      });
    } finally {
      setLoading(false);
    }
  }, [quizId]);

  useEffect(() => {
    fetchQuiz();
  }, [fetchQuiz]);

  const canAttempt = quiz ? attempts.length < quiz.attempts_allowed : false;

  const bestScore = attempts.length > 0
    ? Math.max(...attempts.filter(a => a.status === 'completed').map((a) => a.percentage_score))
    : 0;

  return {
    quiz,
    attempts,
    loading,
    error,
    canAttempt,
    bestScore,
    refetch: fetchQuiz,
  };
}

/**
 * Hook to manage a quiz attempt (take a quiz)
 */
export function useQuizAttempt(quizId: string | null) {
  const [attempt, setAttempt] = useState<QuizAttempt | null>(null);
  const [quiz, setQuiz] = useState<ConversationQuiz | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const startAttempt = async () => {
    if (!quizId) return null;

    try {
      setLoading(true);
      setError(null);

      const response = await quizApi.startAttempt({ quiz_id: quizId });
      setAttempt(response.attempt);
      setQuiz(response.quiz);
      setCurrentQuestionIndex(0);
      setAnswers({});

      return response.attempt;
    } catch (err: any) {
      console.error('Error starting attempt:', err);
      setError({
        message: err.message || 'Failed to start quiz attempt',
        code: err.code,
      });
      return null;
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async (questionId: string, answer: string, timeSpent: number = 0) => {
    if (!attempt) return null;

    try {
      setSubmitting(true);
      setError(null);

      const response = await quizApi.submitAnswer(attempt.id, {
        question_id: questionId,
        answer,
        time_spent: timeSpent,
      });

      // Update local answers state
      setAnswers((prev) => ({ ...prev, [questionId]: answer }));

      return response.grading_result;
    } catch (err: any) {
      console.error('Error submitting answer:', err);
      setError({
        message: err.message || 'Failed to submit answer',
        code: err.code,
      });
      return null;
    } finally {
      setSubmitting(false);
    }
  };

  const completeAttempt = async (): Promise<QuizResults | null> => {
    if (!attempt) return null;

    try {
      setLoading(true);
      setError(null);

      const response = await quizApi.completeAttempt(attempt.id);
      return response.results;
    } catch (err: any) {
      console.error('Error completing attempt:', err);
      setError({
        message: err.message || 'Failed to complete quiz',
        code: err.code,
      });
      return null;
    } finally {
      setLoading(false);
    }
  };

  const nextQuestion = () => {
    if (quiz && currentQuestionIndex < quiz.questions.length - 1) {
      setCurrentQuestionIndex((prev) => prev + 1);
    }
  };

  const previousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex((prev) => prev - 1);
    }
  };

  const goToQuestion = (index: number) => {
    if (quiz && index >= 0 && index < quiz.questions.length) {
      setCurrentQuestionIndex(index);
    }
  };

  const currentQuestion = quiz?.questions[currentQuestionIndex] || null;
  const isLastQuestion = quiz ? currentQuestionIndex === quiz.questions.length - 1 : false;
  const isFirstQuestion = currentQuestionIndex === 0;
  const answeredQuestions = Object.keys(answers).length;
  const totalQuestions = quiz?.questions.length || 0;
  const allAnswered = answeredQuestions === totalQuestions;

  return {
    attempt,
    quiz,
    currentQuestion,
    currentQuestionIndex,
    answers,
    loading,
    error,
    submitting,
    isLastQuestion,
    isFirstQuestion,
    answeredQuestions,
    totalQuestions,
    allAnswered,
    startAttempt,
    submitAnswer,
    completeAttempt,
    nextQuestion,
    previousQuestion,
    goToQuestion,
  };
}

/**
 * Hook to get quiz statistics
 */
export function useQuizStats() {
  const [stats, setStats] = useState<QuizStats>({
    total_quizzes: 0,
    completed_quizzes: 0,
    passed_quizzes: 0,
    average_score: 0,
    total_time_spent: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await quizApi.getStats();
      setStats(response.stats);
    } catch (err: any) {
      console.error('Error fetching quiz stats:', err);
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

/**
 * Hook to get recent quizzes
 */
export function useRecentQuizzes(limit = 5) {
  const [quizzes, setQuizzes] = useState<ConversationQuiz[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchRecentQuizzes = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const recentQuizzes = await quizApi.getRecentQuizzes();
      setQuizzes(recentQuizzes.slice(0, limit));
    } catch (err: any) {
      console.error('Error fetching recent quizzes:', err);
      setError({
        message: err.message || 'Failed to fetch recent quizzes',
        code: err.code,
      });
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    fetchRecentQuizzes();
  }, [fetchRecentQuizzes]);

  return {
    quizzes,
    loading,
    error,
    refetch: fetchRecentQuizzes,
  };
}
