/**
 * Quiz Results Page
 * Shows comprehensive results with AI evaluation
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { quizApi } from '@/lib/api/quizzes';
import type { QuizAttempt, ConversationQuiz, QuizQuestion, AnswerResult } from '@/types/quiz';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  CheckCircle2,
  XCircle,
  Award,
  TrendingUp,
  TrendingDown,
  Target,
  Lightbulb,
  RefreshCw,
  ArrowLeft,
  Clock,
  Trophy,
  BookOpen,
} from 'lucide-react';
import { LoadingState } from '@/components/shared/LoadingState';
import { ErrorState } from '@/components/shared/ErrorState';

export default function QuizResultsPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();

  const quizId = params?.quizId as string;
  const attemptId = searchParams?.get('attempt');

  const [attempt, setAttempt] = useState<QuizAttempt | null>(null);
  const [quiz, setQuiz] = useState<ConversationQuiz | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (quizId && attemptId) {
      loadResults();
    }
  }, [quizId, attemptId]);

  const loadResults = async () => {
    try {
      setLoading(true);
      setError(null);

      const { attempt: attemptData, quiz: quizData } = await quizApi.getAttempt(attemptId!);
      setAttempt(attemptData);
      setQuiz(quizData);
    } catch (err: any) {
      console.error('Error loading results:', err);
      setError(err.message || 'Failed to load results');
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = async () => {
    if (!quiz) return;

    try {
      const { attempt: newAttempt } = await quizApi.retryQuiz(quiz.id);
      router.push(`/dashboard/quiz/${quiz.id}?attempt=${newAttempt.id}`);
    } catch (err: any) {
      console.error('Error retrying quiz:', err);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <LoadingState />
      </div>
    );
  }

  if (error || !attempt || !quiz) {
    return (
      <div className="container mx-auto p-6">
        <ErrorState
          title="Failed to load results"
          message={error || 'Results not found'}
          onRetry={() => router.back()}
        />
      </div>
    );
  }

  const timeSpentMinutes = Math.floor(attempt.time_spent / 60);
  const timeSpentSeconds = attempt.time_spent % 60;

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      {/* Header */}
      <div className="mb-6">
        <Button variant="ghost" size="sm" onClick={() => router.back()} className="mb-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Roadmap
        </Button>

        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-primary/10 mb-4">
            {attempt.passed ? (
              <Trophy className="h-10 w-10 text-primary" />
            ) : (
              <Target className="h-10 w-10 text-muted-foreground" />
            )}
          </div>
          <h1 className="text-3xl font-bold mb-2">
            {attempt.passed ? 'Congratulations! 🎉' : 'Quiz Complete'}
          </h1>
          <p className="text-muted-foreground">
            {attempt.passed
              ? "You've passed the quiz!"
              : 'Keep practicing and try again!'}
          </p>
        </div>
      </div>

      {/* Score Card */}
      <Card className="p-8 mb-6 text-center">
        <div className="mb-4">
          <div className="text-6xl font-bold text-primary mb-2">
            {Math.round(attempt.percentage_score)}%
          </div>
          <p className="text-muted-foreground">
            {attempt.points_earned} / {attempt.total_points} points
          </p>
        </div>

        <div className="flex justify-center gap-4 mb-6">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600" />
            <span className="font-medium">{attempt.correct_answers} correct</span>
          </div>
          <div className="flex items-center gap-2">
            <XCircle className="h-5 w-5 text-red-600" />
            <span className="font-medium">
              {attempt.total_questions - attempt.correct_answers} incorrect
            </span>
          </div>
          {attempt.partial_credit_answers > 0 && (
            <div className="flex items-center gap-2">
              <Award className="h-5 w-5 text-orange-600" />
              <span className="font-medium">{attempt.partial_credit_answers} partial</span>
            </div>
          )}
        </div>

        <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground mb-4">
          <Clock className="h-4 w-4" />
          <span>
            Time: {timeSpentMinutes}m {timeSpentSeconds}s
          </span>
        </div>

        <Badge
          variant={attempt.passed ? 'default' : 'secondary'}
          className={`text-lg px-4 py-2 ${
            attempt.passed ? 'bg-green-600' : ''
          }`}
        >
          {attempt.passed ? 'PASSED' : 'NOT PASSED'}
        </Badge>
      </Card>

      {/* AI Feedback */}
      {attempt.overall_feedback && (
        <Card className="p-6 mb-6">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-primary" />
            AI Feedback
          </h2>
          <p className="text-muted-foreground leading-relaxed">
            {attempt.overall_feedback}
          </p>
        </Card>
      )}

      {/* Strengths & Weaknesses */}
      <div className="grid md:grid-cols-2 gap-6 mb-6">
        {/* Strengths */}
        {attempt.strengths && attempt.strengths.length > 0 && (
          <Card className="p-6">
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-green-600">
              <TrendingUp className="h-5 w-5" />
              Strengths
            </h3>
            <ul className="space-y-2">
              {attempt.strengths.map((strength, index) => (
                <li key={index} className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600 mt-1 flex-shrink-0" />
                  <span className="text-sm">{strength}</span>
                </li>
              ))}
            </ul>
          </Card>
        )}

        {/* Weaknesses */}
        {attempt.weaknesses && attempt.weaknesses.length > 0 && (
          <Card className="p-6">
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-orange-600">
              <TrendingDown className="h-5 w-5" />
              Areas to Improve
            </h3>
            <ul className="space-y-2">
              {attempt.weaknesses.map((weakness, index) => (
                <li key={index} className="flex items-start gap-2">
                  <Target className="h-4 w-4 text-orange-600 mt-1 flex-shrink-0" />
                  <span className="text-sm">{weakness}</span>
                </li>
              ))}
            </ul>
          </Card>
        )}
      </div>

      {/* Recommendations */}
      {attempt.recommendations && attempt.recommendations.length > 0 && (
        <Card className="p-6 mb-6">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-primary" />
            Recommendations
          </h2>
          <ul className="space-y-3">
            {attempt.recommendations.map((recommendation, index) => (
              <li key={index} className="flex items-start gap-3">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary/10 text-primary font-medium text-sm flex-shrink-0">
                  {index + 1}
                </span>
                <span className="text-sm text-muted-foreground pt-0.5">
                  {recommendation}
                </span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {/* Question Review */}
      <Card className="p-6 mb-6">
        <h2 className="text-xl font-bold mb-4">Question Review</h2>
        <div className="space-y-4">
          {quiz.questions.map((question, index) => {
            const answerResult = attempt.answers[question.id];
            if (!answerResult) return null;

            return (
              <div
                key={question.id}
                className={`p-4 rounded-lg border ${
                  answerResult.correct
                    ? 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-900'
                    : 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900'
                }`}
              >
                <div className="flex items-start gap-3 mb-2">
                  {answerResult.correct ? (
                    <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <p className="font-medium mb-1">
                      Question {index + 1}: {question.question}
                    </p>
                    <p className="text-sm text-muted-foreground mb-2">
                      Your answer: <span className="font-medium">{answerResult.answer}</span>
                    </p>
                    {answerResult.feedback && (
                      <p className="text-sm">{answerResult.feedback}</p>
                    )}
                    <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                      <span>
                        Points: {answerResult.points_earned}/{question.points}
                      </span>
                      <span>
                        Time: {answerResult.time_spent}s
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Actions */}
      <div className="flex gap-4 justify-center">
        <Button variant="outline" asChild>
          <Link href="/dashboard/progress">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Roadmap
          </Link>
        </Button>

        {!attempt.passed && quiz.attempts_used < quiz.attempts_allowed && (
          <Button onClick={handleRetry}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again ({quiz.attempts_allowed - quiz.attempts_used} attempts left)
          </Button>
        )}

        {attempt.passed && (
          <Button asChild>
            <Link href="/dashboard/progress">
              Continue Learning
            </Link>
          </Button>
        )}
      </div>
    </div>
  );
}
