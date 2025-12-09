/**
 * Quiz Page - Question-by-Question Flow
 * /dashboard/quiz/[quizId]/page.tsx
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { quizApi } from '@/lib/api/quizzes';
import type { ConversationQuiz, QuizAttempt, QuizQuestion, AnswerResult } from '@/types/quiz';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  XCircle,
  Clock,
  Award,
  BookOpen,
  Brain,
  Loader2,
} from 'lucide-react';
import { QuestionForm } from '@/components/quiz/QuestionForm';
import { LoadingState } from '@/components/shared/LoadingState';
import { ErrorState } from '@/components/shared/ErrorState';

export default function QuizPage() {
  const params = useParams();
  const router = useRouter();
  const quizId = params?.quizId as string;

  // Quiz state
  const [quiz, setQuiz] = useState<ConversationQuiz | null>(null);
  const [attempt, setAttempt] = useState<QuizAttempt | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Navigation state
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<Record<string, AnswerResult>>({});
  const [submittedQuestions, setSubmittedQuestions] = useState<Set<string>>(new Set());

  // Timing
  const [startTime, setStartTime] = useState<number>(Date.now());
  const [questionStartTime, setQuestionStartTime] = useState<number>(Date.now());

  // Loading states
  const [submitting, setSubmitting] = useState(false);
  const [completing, setCompleting] = useState(false);

  useEffect(() => {
    if (quizId) {
      loadQuiz();
    }
  }, [quizId]);

  const loadQuiz = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get quiz details
      const { quiz: quizData, attempts } = await quizApi.getQuiz(quizId);
      setQuiz(quizData);

      // Check for existing in-progress attempt
      const inProgressAttempt = attempts.find((a) => a.status === 'in_progress');

      if (inProgressAttempt) {
        // Resume existing attempt
        setAttempt(inProgressAttempt);
        setAnswers(inProgressAttempt.answers || {});

        // Reconstruct feedback from existing answers
        const existingFeedback: Record<string, AnswerResult> = {};
        Object.entries(inProgressAttempt.answers || {}).forEach(([qId, result]) => {
          existingFeedback[qId] = result as AnswerResult;
          setSubmittedQuestions((prev) => new Set([...prev, qId]));
        });
        setFeedback(existingFeedback);
      } else {
        // Start new attempt
        const { attempt: newAttempt } = await quizApi.startAttempt({ quiz_id: quizId });
        setAttempt(newAttempt);
        setStartTime(Date.now());
      }

      setQuestionStartTime(Date.now());
    } catch (err: any) {
      console.error('Error loading quiz:', err);
      setError(err.message || 'Failed to load quiz');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (questionId: string, answer: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: answer }));
  };

  const handleSubmitAnswer = async () => {
    if (!attempt || !quiz) return;

    const currentQuestion = quiz.questions[currentQuestionIndex];
    const answer = answers[currentQuestion.id];

    if (!answer || answer.trim() === '') {
      return; // Don't submit empty answers
    }

    setSubmitting(true);

    try {
      const timeSpent = Math.floor((Date.now() - questionStartTime) / 1000);

      const response = await quizApi.submitAnswer(attempt.id, {
        question_id: currentQuestion.id,
        answer,
        time_spent: timeSpent,
      });

      // Store feedback
      setFeedback((prev) => ({
        ...prev,
        [currentQuestion.id]: {
          answer,
          correct: response.grading_result.correct,
          points_earned: response.grading_result.points_earned,
          feedback: response.grading_result.feedback,
          time_spent: timeSpent,
          partial_credit: response.grading_result.partial_credit,
        },
      }));

      setSubmittedQuestions((prev) => new Set([...prev, currentQuestion.id]));

      // Auto-advance to next question after 2 seconds
      setTimeout(() => {
        if (currentQuestionIndex < quiz.questions.length - 1) {
          handleNextQuestion();
        }
      }, 2000);
    } catch (err: any) {
      console.error('Error submitting answer:', err);
      setError(err.message || 'Failed to submit answer');
    } finally {
      setSubmitting(false);
    }
  };

  const handleNextQuestion = () => {
    if (currentQuestionIndex < quiz!.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
      setQuestionStartTime(Date.now());
    }
  };

  const handlePreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
      setQuestionStartTime(Date.now());
    }
  };

  const handleCompleteQuiz = async () => {
    if (!attempt) return;

    setCompleting(true);

    try {
      const response = await quizApi.completeAttempt(attempt.id);

      // Navigate to results page
      router.push(`/dashboard/quiz/${quizId}/results?attempt=${attempt.id}`);
    } catch (err: any) {
      console.error('Error completing quiz:', err);
      setError(err.message || 'Failed to complete quiz');
    } finally {
      setCompleting(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <LoadingState />
      </div>
    );
  }

  if (error || !quiz || !attempt) {
    return (
      <div className="container mx-auto p-6">
        <ErrorState
          title="Failed to load quiz"
          message={error || 'Quiz not found'}
          onRetry={() => router.back()}
        />
      </div>
    );
  }

  const currentQuestion = quiz.questions[currentQuestionIndex];
  const isQuestionSubmitted = submittedQuestions.has(currentQuestion.id);
  const currentFeedback = feedback[currentQuestion.id];
  const progressPercentage = (submittedQuestions.size / quiz.questions.length) * 100;
  const allQuestionsAnswered = submittedQuestions.size === quiz.questions.length;

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      {/* Header */}
      <div className="mb-6">
        <Button variant="ghost" size="sm" onClick={() => router.back()} className="mb-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Roadmap
        </Button>

        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">{quiz.title}</h1>
            {quiz.description && (
              <p className="text-muted-foreground">{quiz.description}</p>
            )}
          </div>

          <div className="flex gap-2">
            <Badge variant="outline" className="flex items-center gap-1">
              <Brain className="h-3 w-3" />
              {quiz.difficulty}
            </Badge>
            <Badge variant="outline" className="flex items-center gap-1">
              <BookOpen className="h-3 w-3" />
              {quiz.topic}
            </Badge>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <Card className="p-4 mb-6">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Progress</span>
            <span className="font-medium">
              {submittedQuestions.size}/{quiz.questions.length} questions
            </span>
          </div>
          <Progress value={progressPercentage} className="h-2" />
        </div>
      </Card>

      {/* Question Card */}
      <Card className="p-6 mb-6">
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-muted-foreground">
                Question {currentQuestionIndex + 1} of {quiz.questions.length}
              </span>
              <Badge variant="secondary">{currentQuestion.type.replace('_', ' ')}</Badge>
            </div>
            <div className="flex items-center gap-1 text-sm text-muted-foreground">
              <Award className="h-4 w-4" />
              <span>{currentQuestion.points} points</span>
            </div>
          </div>
        </div>

        {/* Question Form */}
        <QuestionForm
          question={currentQuestion}
          answer={answers[currentQuestion.id]}
          onChange={(answer) => handleAnswerChange(currentQuestion.id, answer)}
          disabled={isQuestionSubmitted}
          showFeedback={isQuestionSubmitted}
          feedback={currentFeedback}
        />

        {/* Feedback Display */}
        {isQuestionSubmitted && currentFeedback && (
          <div className={`mt-4 p-4 rounded-lg border ${
            currentFeedback.correct
              ? 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-900'
              : 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900'
          }`}>
            <div className="flex items-start gap-2">
              {currentFeedback.correct ? (
                <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
              ) : (
                <XCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
              )}
              <div className="flex-1">
                <p className={`font-medium mb-1 ${
                  currentFeedback.correct
                    ? 'text-green-900 dark:text-green-100'
                    : 'text-red-900 dark:text-red-100'
                }`}>
                  {currentFeedback.correct ? 'Correct!' : 'Incorrect'}
                  {currentFeedback.partial_credit && ' (Partial Credit)'}
                </p>
                <p className={`text-sm ${
                  currentFeedback.correct
                    ? 'text-green-700 dark:text-green-300'
                    : 'text-red-700 dark:text-red-300'
                }`}>
                  {currentFeedback.feedback}
                </p>
                <p className="text-xs text-muted-foreground mt-2">
                  Points earned: {currentFeedback.points_earned}/{currentQuestion.points}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-between mt-6 pt-6 border-t">
          <Button
            variant="outline"
            onClick={handlePreviousQuestion}
            disabled={currentQuestionIndex === 0}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Previous
          </Button>

          <div className="flex gap-2">
            {!isQuestionSubmitted && (
              <Button onClick={handleSubmitAnswer} disabled={!answers[currentQuestion.id] || submitting}>
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  'Submit Answer'
                )}
              </Button>
            )}

            {isQuestionSubmitted && currentQuestionIndex < quiz.questions.length - 1 && (
              <Button onClick={handleNextQuestion}>
                Next Question
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            )}

            {allQuestionsAnswered && (
              <Button onClick={handleCompleteQuiz} disabled={completing} size="lg">
                {completing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Finishing...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    Complete Quiz
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
      </Card>

      {/* Question Navigator */}
      <Card className="p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium">Question Navigator</span>
          <span className="text-xs text-muted-foreground">
            {submittedQuestions.size} answered
          </span>
        </div>
        <div className="grid grid-cols-10 gap-2">
          {quiz.questions.map((q, index) => {
            const isAnswered = submittedQuestions.has(q.id);
            const isCurrent = index === currentQuestionIndex;
            const qFeedback = feedback[q.id];

            return (
              <button
                key={q.id}
                onClick={() => {
                  setCurrentQuestionIndex(index);
                  setQuestionStartTime(Date.now());
                }}
                className={`
                  aspect-square rounded-md border-2 font-medium text-sm
                  transition-all hover:scale-110
                  ${isCurrent ? 'border-primary bg-primary text-primary-foreground' : ''}
                  ${!isCurrent && isAnswered && qFeedback?.correct ? 'border-green-500 bg-green-50 dark:bg-green-950/20 text-green-700' : ''}
                  ${!isCurrent && isAnswered && !qFeedback?.correct ? 'border-red-500 bg-red-50 dark:bg-red-950/20 text-red-700' : ''}
                  ${!isCurrent && !isAnswered ? 'border-muted bg-muted/50 text-muted-foreground' : ''}
                `}
              >
                {index + 1}
              </button>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
