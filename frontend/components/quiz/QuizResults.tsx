/**
 * QuizResults Component
 * Displays quiz results with feedback, score, and recommendations
 */

'use client';

import { QuizResults as QuizResultsType, ConversationQuiz } from '@/types/quiz';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Trophy,
  CheckCircle2,
  XCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Lightbulb,
  ArrowRight,
  RotateCcw,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface QuizResultsProps {
  results: QuizResultsType;
  quiz: ConversationQuiz;
  onClose: () => void;
  onRetry?: () => void;
}

export function QuizResults({ results, quiz, onClose, onRetry }: QuizResultsProps) {
  const { percentage_score, passed, correct_answers, total_questions, time_spent } = results;

  // Determine result tier for styling
  const isExcellent = percentage_score >= 90;
  const isGood = percentage_score >= 70;
  const isPassed = passed;

  return (
    <div className="space-y-6">
      {/* Header with score */}
      <div
        className={cn(
          'rounded-lg p-8 text-center',
          isExcellent && 'bg-gradient-to-r from-yellow-400 to-orange-400',
          isGood && !isExcellent && 'bg-gradient-to-r from-green-500 to-emerald-500',
          !isGood && isPassed && 'bg-gradient-to-r from-blue-500 to-cyan-500',
          !isPassed && 'bg-gradient-to-r from-gray-500 to-slate-500'
        )}
      >
        <div className="mb-4">
          {isPassed ? (
            <Trophy className="h-16 w-16 mx-auto text-white" />
          ) : (
            <RotateCcw className="h-16 w-16 mx-auto text-white" />
          )}
        </div>

        <h2 className="text-3xl font-bold text-white mb-2">
          {isExcellent
            ? '🎉 Excellent Work!'
            : isGood
            ? '✨ Great Job!'
            : isPassed
            ? '👍 You Passed!'
            : '💪 Keep Practicing!'}
        </h2>

        <p className="text-white/90 mb-4">{quiz.title}</p>

        <div className="bg-white/20 backdrop-blur-sm rounded-lg p-4 inline-block">
          <div className="text-5xl font-bold text-white mb-1">
            {Math.round(percentage_score)}%
          </div>
          <div className="text-white/90 text-sm">
            {correct_answers} of {total_questions} correct
          </div>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          icon={CheckCircle2}
          label="Correct"
          value={correct_answers}
          total={total_questions}
          color="green"
        />
        <StatCard
          icon={XCircle}
          label="Incorrect"
          value={total_questions - correct_answers}
          total={total_questions}
          color="red"
        />
        <StatCard
          icon={Clock}
          label="Time Spent"
          value={formatTime(time_spent)}
          color="blue"
        />
        <StatCard
          icon={Trophy}
          label="Status"
          value={isPassed ? 'Passed' : 'Failed'}
          color={isPassed ? 'green' : 'gray'}
        />
      </div>

      {/* Overall feedback */}
      {results.overall_feedback && (
        <div className="bg-card rounded-lg border p-6">
          <h3 className="font-semibold mb-2">Overall Feedback</h3>
          <p className="text-muted-foreground">{results.overall_feedback}</p>
        </div>
      )}

      {/* Strengths */}
      {results.strengths && results.strengths.length > 0 && (
        <div className="bg-green-50 dark:bg-green-950/20 rounded-lg border border-green-200 dark:border-green-900 p-6">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="h-5 w-5 text-green-600" />
            <h3 className="font-semibold text-green-900 dark:text-green-100">
              Strengths
            </h3>
          </div>
          <ul className="space-y-2">
            {results.strengths.map((strength, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-green-800 dark:text-green-200">
                <CheckCircle2 className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>{strength}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Weaknesses */}
      {results.weaknesses && results.weaknesses.length > 0 && (
        <div className="bg-orange-50 dark:bg-orange-950/20 rounded-lg border border-orange-200 dark:border-orange-900 p-6">
          <div className="flex items-center gap-2 mb-3">
            <TrendingDown className="h-5 w-5 text-orange-600" />
            <h3 className="font-semibold text-orange-900 dark:text-orange-100">
              Areas to Improve
            </h3>
          </div>
          <ul className="space-y-2">
            {results.weaknesses.map((weakness, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-orange-800 dark:text-orange-200">
                <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>{weakness}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendations */}
      {results.recommendations && results.recommendations.length > 0 && (
        <div className="bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-900 p-6">
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb className="h-5 w-5 text-blue-600" />
            <h3 className="font-semibold text-blue-900 dark:text-blue-100">
              Recommendations
            </h3>
          </div>
          <ul className="space-y-2">
            {results.recommendations.map((rec, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-blue-800 dark:text-blue-200">
                <ArrowRight className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Next topics */}
      {results.next_topics && results.next_topics.length > 0 && (
        <div className="bg-card rounded-lg border p-6">
          <h3 className="font-semibold mb-3">What's Next?</h3>
          <div className="flex flex-wrap gap-2">
            {results.next_topics.map((topic, index) => (
              <Badge key={index} variant="secondary" className="text-sm">
                {topic}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-3 pt-4 border-t">
        {onRetry && !isPassed && (
          <Button onClick={onRetry} variant="outline" className="flex-1">
            <RotateCcw className="h-4 w-4 mr-2" />
            Retry Quiz
          </Button>
        )}
        <Button onClick={onClose} className="flex-1">
          {isPassed ? 'Continue Learning' : 'Close'}
        </Button>
      </div>
    </div>
  );
}

/**
 * Stat Card Component
 */
function StatCard({
  icon: Icon,
  label,
  value,
  total,
  color = 'blue',
}: {
  icon: any;
  label: string;
  value: string | number;
  total?: number;
  color?: 'green' | 'red' | 'blue' | 'gray';
}) {
  const colorClasses = {
    green: 'text-green-600 bg-green-50 dark:bg-green-950/20',
    red: 'text-red-600 bg-red-50 dark:bg-red-950/20',
    blue: 'text-blue-600 bg-blue-50 dark:bg-blue-950/20',
    gray: 'text-gray-600 bg-gray-50 dark:bg-gray-950/20',
  };

  return (
    <div className="bg-card rounded-lg border p-4">
      <div className={cn('w-10 h-10 rounded-full flex items-center justify-center mb-3', colorClasses[color])}>
        <Icon className="h-5 w-5" />
      </div>
      <div className="text-2xl font-bold mb-1">{value}</div>
      <div className="text-sm text-muted-foreground">{label}</div>
      {total !== undefined && (
        <Progress value={(Number(value) / total) * 100} className="h-1 mt-2" />
      )}
    </div>
  );
}

/**
 * Format time in seconds to readable format
 */
function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;

  if (mins === 0) return `${secs}s`;
  if (secs === 0) return `${mins}m`;
  return `${mins}m ${secs}s`;
}

// Missing import
import { AlertCircle } from 'lucide-react';
