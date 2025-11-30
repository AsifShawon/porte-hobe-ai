/**
 * PhaseCard Component
 * Displays a single phase with its milestones in an expandable card
 */

'use client';

import { useState } from 'react';
import { Phase } from '@/types/roadmap';
import { MilestoneItem } from './MilestoneItem';
import { ChevronDown, ChevronRight, BookOpen } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface PhaseCardProps {
  phase: Phase;
  phaseNumber: number;
  roadmapId?: string;
  isCompleted: boolean;
  isActive: boolean;
  isLocked: boolean;
  onMilestoneClick?: (phaseId: string, milestoneId: string) => void;
  onMilestoneComplete?: (phaseId: string, milestoneId: string) => void;
}

export function PhaseCard({
  phase,
  phaseNumber,
  roadmapId,
  isCompleted,
  isActive,
  isLocked,
  onMilestoneClick,
  onMilestoneComplete,
}: PhaseCardProps) {
  const [isExpanded, setIsExpanded] = useState(isActive || false);

  const totalMilestones = phase.milestones.length;
  const completedMilestones = phase.milestones.filter((m) => m.status === 'completed').length;
  const progressPercentage = (completedMilestones / totalMilestones) * 100;

  // Calculate total estimated time
  const totalTime = phase.milestones.reduce((sum, m) => sum + (m.estimated_time || 0), 0);

  return (
    <div
      className={cn(
        'bg-card rounded-lg border transition-all',
        isCompleted && 'border-green-500/50',
        isActive && 'border-primary/50 shadow-sm',
        isLocked && 'opacity-60'
      )}
    >
      {/* Phase Header - Clickable to expand/collapse */}
      <button
        onClick={() => !isLocked && setIsExpanded(!isExpanded)}
        disabled={isLocked}
        className="w-full p-6 text-left hover:bg-accent/50 transition-colors disabled:cursor-not-allowed rounded-t-lg"
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <div className="flex items-center gap-2">
                {isExpanded ? (
                  <ChevronDown className="h-5 w-5 text-muted-foreground" />
                ) : (
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                )}
                <h3 className="text-lg font-semibold">
                  Phase {phaseNumber}: {phase.title}
                </h3>
              </div>

              {/* Status badges */}
              <div className="flex gap-2">
                {isCompleted && (
                  <Badge variant="default" className="bg-green-500">
                    Completed
                  </Badge>
                )}
                {isActive && !isCompleted && (
                  <Badge variant="default">In Progress</Badge>
                )}
                {isLocked && (
                  <Badge variant="secondary">Locked</Badge>
                )}
              </div>
            </div>

            {phase.description && (
              <p className="text-sm text-muted-foreground mb-3">{phase.description}</p>
            )}

            {/* Progress bar */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">
                  {completedMilestones}/{totalMilestones} milestones
                </span>
                <span className="font-medium">{Math.round(progressPercentage)}%</span>
              </div>
              <Progress value={progressPercentage} className="h-2" />
            </div>
          </div>

          {/* Estimated time */}
          <div className="ml-4 text-right">
            <div className="flex items-center gap-1 text-sm text-muted-foreground">
              <BookOpen className="h-4 w-4" />
              <span>{totalTime} min</span>
            </div>
          </div>
        </div>
      </button>

      {/* Milestones List - Expandable */}
      {isExpanded && !isLocked && (
        <div className="border-t">
          <div className="p-6 pt-4 space-y-3">
            {phase.milestones.map((milestone, index) => (
              <MilestoneItem
                key={milestone.id}
                milestone={milestone}
                phaseId={phase.id}
                roadmapId={roadmapId}
                milestoneNumber={index + 1}
                onClick={() => onMilestoneClick?.(phase.id, milestone.id)}
                onComplete={() => onMilestoneComplete?.(phase.id, milestone.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Locked message */}
      {isExpanded && isLocked && (
        <div className="border-t p-6 pt-4 text-center text-muted-foreground">
          <p className="text-sm">
            Complete previous phases to unlock this content
          </p>
        </div>
      )}
    </div>
  );
}
