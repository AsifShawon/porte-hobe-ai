/**
 * Quiz Library Page
 * Browse, filter, and take quizzes
 */

'use client';

import { useState } from 'react';
import { useQuizzes, useQuiz, useQuizStats, useRecentQuizzes } from '@/hooks/useQuiz';
import { PageHeader } from '@/components/shared/PageHeader';
import { StatsCard } from '@/components/shared/StatsCard';
import { LoadingState } from '@/components/shared/LoadingState';
import { ErrorState } from '@/components/shared/ErrorState';
import { EmptyState } from '@/components/shared/EmptyState';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  FileQuestion,
  Trophy,
  CheckCircle2,
  Clock,
  Play,
  RotateCcw,
  TrendingUp,
} from 'lucide-react';
import type { QuizStatus, QuizDifficulty } from '@/types/quiz';

export default function QuizPage() {
  const [selectedStatus, setSelectedStatus] = useState<QuizStatus | 'all'>('all');
  const [selectedDifficulty, setSelectedDifficulty] = useState<QuizDifficulty | 'all'>('all');

  const { stats, loading: statsLoading } = useQuizStats();
  const { quizzes: recentQuizzes, loading: recentLoading } = useRecentQuizzes(3);
  const {
    quizzes,
    loading: quizzesLoading,
    error: quizzesError,
    refetch,
  } = useQuizzes({
    status: selectedStatus !== 'all' ? selectedStatus : undefined,
    difficulty: selectedDifficulty !== 'all' ? selectedDifficulty : undefined,
    limit: 50,
  });

  const handleTakeQuiz = (quizId: string) => {
    console.log('Start quiz:', quizId);
    // TODO: Navigate to quiz taking page or open popup
  };

  const handleRetryQuiz = (quizId: string) => {
    console.log('Retry quiz:', quizId);
    // TODO: Start new attempt
  };

  if (statsLoading || recentLoading) {
    return (
      <div className="container mx-auto p-6">
        <PageHeader title="Quiz Library" icon={FileQuestion} />
        <LoadingState layout="grid" />
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Page Header */}
      <PageHeader
        title="Quiz Library"
        description="Test your knowledge and track your performance"
        icon={FileQuestion}
      />

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Total Quizzes"
          value={stats.total_quizzes}
          subtitle={`${stats.completed_quizzes} completed`}
          icon={FileQuestion}
        />

        <StatsCard
          title="Passed Quizzes"
          value={stats.passed_quizzes}
          subtitle={`${Math.round((stats.passed_quizzes / stats.completed_quizzes) * 100 || 0)}% pass rate`}
          icon={Trophy}
          trend={{
            value: stats.passed_quizzes,
            isPositive: true,
          }}
        />

        <StatsCard
          title="Average Score"
          value={`${Math.round(stats.average_score)}%`}
          subtitle="Across all quizzes"
          icon={TrendingUp}
          trend={{
            value: stats.average_score,
            isPositive: stats.average_score >= 70,
          }}
        />

        <StatsCard
          title="Time Spent"
          value={formatTime(stats.total_time_spent)}
          subtitle="Total quiz time"
          icon={Clock}
        />
      </div>

      {/* Recent Quizzes */}
      {recentQuizzes.length > 0 && (
        <div>
          <h2 className="text-2xl font-bold mb-4">Recent Activity</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {recentQuizzes.map((quiz) => (
              <Card key={quiz.id} className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold line-clamp-2">{quiz.title}</h3>
                  <Badge variant="outline">{quiz.difficulty}</Badge>
                </div>
                <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                  {quiz.description}
                </p>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">{quiz.total_points} points</span>
                  <Button size="sm" variant="outline" onClick={() => handleTakeQuiz(quiz.id)}>
                    {quiz.status === 'completed' ? (
                      <>
                        <RotateCcw className="h-3 w-3 mr-1" />
                        Retry
                      </>
                    ) : (
                      <>
                        <Play className="h-3 w-3 mr-1" />
                        Start
                      </>
                    )}
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* All Quizzes Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">All Quizzes</h2>
          <div className="flex gap-2">
            <Select
              value={selectedDifficulty}
              onValueChange={(v) => setSelectedDifficulty(v as any)}
            >
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Difficulty" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Levels</SelectItem>
                <SelectItem value="beginner">Beginner</SelectItem>
                <SelectItem value="intermediate">Intermediate</SelectItem>
                <SelectItem value="advanced">Advanced</SelectItem>
              </SelectContent>
            </Select>

            <Select value={selectedStatus} onValueChange={(v) => setSelectedStatus(v as any)}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="not_started">Not Started</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
              </SelectContent>
            </Select>

            <Button onClick={refetch} variant="outline" size="sm">
              Refresh
            </Button>
          </div>
        </div>

        {quizzesLoading ? (
          <LoadingState layout="grid" />
        ) : quizzesError ? (
          <ErrorState
            title="Failed to load quizzes"
            message={quizzesError.message}
            onRetry={refetch}
          />
        ) : quizzes.length === 0 ? (
          <EmptyState
            icon={FileQuestion}
            title="No Quizzes Found"
            description={
              selectedStatus === 'all' && selectedDifficulty === 'all'
                ? 'No quizzes available yet. They will appear as you progress through your roadmap.'
                : 'No quizzes match your filters. Try adjusting your selections.'
            }
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {quizzes.map((quiz) => (
              <Card key={quiz.id} className="p-6 hover:shadow-md transition-shadow">
                <div className="space-y-4">
                  {/* Header */}
                  <div>
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-semibold line-clamp-2">{quiz.title}</h3>
                      <Badge variant={getDifficultyVariant(quiz.difficulty)}>
                        {quiz.difficulty}
                      </Badge>
                    </div>
                    {quiz.description && (
                      <p className="text-sm text-muted-foreground line-clamp-2">
                        {quiz.description}
                      </p>
                    )}
                  </div>

                  {/* Metadata */}
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="outline" className="text-xs">
                      {quiz.questions?.length || 0} questions
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      {quiz.total_points} points
                    </Badge>
                    {quiz.time_limit && (
                      <Badge variant="outline" className="text-xs">
                        {quiz.time_limit} min
                      </Badge>
                    )}
                  </div>

                  {/* Stats (if quiz has been attempted) */}
                  {quiz.attempt_count !== undefined && quiz.attempt_count > 0 && (
                    <div className="pt-3 border-t space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Attempts</span>
                        <span className="font-medium">
                          {quiz.attempt_count}/{quiz.attempts_allowed}
                        </span>
                      </div>
                      {quiz.best_score !== undefined && quiz.best_score > 0 && (
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Best Score</span>
                          <span className="font-medium text-primary">
                            {Math.round(quiz.best_score)}%
                          </span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-2">
                    {quiz.status === 'completed' ? (
                      <>
                        <Button
                          variant="outline"
                          size="sm"
                          className="flex-1"
                          onClick={() => console.log('View results:', quiz.id)}
                        >
                          <CheckCircle2 className="h-4 w-4 mr-1" />
                          View Results
                        </Button>
                        {quiz.attempt_count !== undefined &&
                          quiz.attempt_count < quiz.attempts_allowed && (
                            <Button
                              size="sm"
                              className="flex-1"
                              onClick={() => handleRetryQuiz(quiz.id)}
                            >
                              <RotateCcw className="h-4 w-4 mr-1" />
                              Retry
                            </Button>
                          )}
                      </>
                    ) : (
                      <Button className="w-full" onClick={() => handleTakeQuiz(quiz.id)}>
                        <Play className="h-4 w-4 mr-1" />
                        {quiz.status === 'in_progress' ? 'Continue' : 'Start Quiz'}
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Get badge variant based on difficulty
 */
function getDifficultyVariant(difficulty: string) {
  switch (difficulty) {
    case 'beginner':
      return 'default';
    case 'intermediate':
      return 'secondary';
    case 'advanced':
    case 'expert':
      return 'destructive';
    default:
      return 'outline';
  }
}

/**
 * Format time in seconds to readable format
 */
function formatTime(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);

  if (hours > 0) return `${hours}h ${mins}m`;
  if (mins > 0) return `${mins}m`;
  return `${seconds}s`;
}
