/**
 * MilestoneItem Component
 * Displays a single milestone (lesson or quiz) with status and actions
 */

'use client';

import { Milestone } from '@/types/roadmap';
import {
  CheckCircle2,
  Circle,
  Lock,
  BookOpen,
  FileQuestion,
  Clock,
  Play,
  Check,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { useStartLearning } from '@/hooks/useStartLearning';

interface MilestoneItemProps {
  milestone: Milestone;
  phaseId: string;
  roadmapId?: string;
  milestoneNumber: number;
  onClick?: () => void;
  onComplete?: () => void;
}

export function MilestoneItem({
  milestone,
  phaseId,
  roadmapId,
  milestoneNumber,
  onClick,
  onComplete,
}: MilestoneItemProps) {
  const isCompleted = milestone.status === 'completed';
  const isInProgress = milestone.status === 'in_progress';
  const isLocked = milestone.status === 'locked';
  const isNotStarted = milestone.status === 'not_started';

  const isLesson = milestone.type === 'lesson';
  const isQuiz = milestone.type === 'quiz';

  const { startLearning, isStarting } = useStartLearning();

  const handleStartLearning = async () => {
    if (!roadmapId) {
      console.error('Roadmap ID is required to start learning');
      return;
    }

    await startLearning({
      roadmapId,
      phaseId,
      milestoneId: milestone.id,
    });
  };

  const handleButtonClick = isNotStarted || isInProgress ? handleStartLearning : onClick;

  return (
    <div
      className={cn(
        'flex items-center gap-4 p-4 rounded-lg border transition-all hover:shadow-sm',
        isCompleted && 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-900',
        isInProgress && 'bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-900',
        isLocked && 'opacity-60 cursor-not-allowed',
        !isLocked && 'hover:border-primary/50 cursor-pointer'
      )}
      onClick={!isLocked ? onClick : undefined}
    >
      {/* Status Icon */}
      <div className="flex-shrink-0">
        {isCompleted ? (
          <CheckCircle2 className="h-6 w-6 text-green-500" />
        ) : isInProgress ? (
          <Circle className="h-6 w-6 text-blue-500 fill-blue-500" />
        ) : isLocked ? (
          <Lock className="h-6 w-6 text-muted-foreground" />
        ) : (
          <Circle className="h-6 w-6 text-muted-foreground" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          {/* Type icon */}
          {isLesson ? (
            <BookOpen className="h-4 w-4 text-muted-foreground flex-shrink-0" />
          ) : (
            <FileQuestion className="h-4 w-4 text-muted-foreground flex-shrink-0" />
          )}

          {/* Title */}
          <h4 className="font-medium truncate">
            {milestoneNumber}. {milestone.title}
          </h4>

          {/* Type badge */}
          {isQuiz && (
            <Badge variant="outline" className="flex-shrink-0">
              Quiz
            </Badge>
          )}
        </div>

        {/* Description */}
        {milestone.description && (
          <p className="text-sm text-muted-foreground line-clamp-1">
            {milestone.description}
          </p>
        )}

        {/* Topics */}
        {milestone.topics && milestone.topics.length > 0 && (
          <div className="flex gap-1 mt-2 flex-wrap">
            {milestone.topics.slice(0, 3).map((topic, index) => (
              <Badge key={index} variant="secondary" className="text-xs">
                {topic}
              </Badge>
            ))}
            {milestone.topics.length > 3 && (
              <Badge variant="secondary" className="text-xs">
                +{milestone.topics.length - 3}
              </Badge>
            )}
          </div>
        )}
      </div>

      {/* Metadata & Actions */}
      <div className="flex items-center gap-3 flex-shrink-0">
        {/* Estimated time */}
        <div className="flex items-center gap-1 text-sm text-muted-foreground">
          <Clock className="h-4 w-4" />
          <span>{milestone.estimated_time}m</span>
        </div>

        {/* Progress percentage (if available) */}
        {milestone.progress !== undefined && milestone.progress > 0 && milestone.progress < 100 && (
          <span className="text-sm font-medium text-primary">{milestone.progress}%</span>
        )}

        {/* Action buttons */}
        {!isLocked && (
          <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
            {isCompleted ? (
              <Button
                variant="ghost"
                size="sm"
                className="text-green-600 hover:text-green-700"
                disabled
              >
                <Check className="h-4 w-4 mr-1" />
                Done
              </Button>
            ) : isInProgress ? (
              <>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleButtonClick}
                  disabled={isStarting}
                >
                  {isStarting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                      Loading...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-1" />
                      Continue
                    </>
                  )}
                </Button>
                <Button variant="default" size="sm" onClick={onComplete}>
                  <Check className="h-4 w-4 mr-1" />
                  Complete
                </Button>
              </>
            ) : (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleButtonClick}
                disabled={isStarting}
              >
                {isStarting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                    Starting...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-1" />
                    Start
                  </>
                )}
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
