/**
 * RoadmapTimeline Component
 * Displays the learning roadmap as a visual timeline with phases and milestones
 */

'use client';

import { LearningRoadmap } from '@/types/roadmap';
import { PhaseCard } from './PhaseCard';
import { CheckCircle2, Circle, Lock, MessageSquare } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

interface RoadmapTimelineProps {
  roadmap: LearningRoadmap;
  onMilestoneClick?: (phaseId: string, milestoneId: string) => void;
  onMilestoneComplete?: (phaseId: string, milestoneId: string) => void;
}

export function RoadmapTimeline({
  roadmap,
  onMilestoneClick,
  onMilestoneComplete,
}: RoadmapTimelineProps) {
  const { roadmap_data, progress_percentage, completed_milestones, total_milestones } = roadmap;

  return (
    <div className="space-y-6">
      {/* Overall Progress Header */}
      <div className="bg-card rounded-lg border p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex-1">
            <h2 className="text-2xl font-bold">{roadmap.title}</h2>
            {roadmap.description && (
              <p className="text-muted-foreground mt-1">{roadmap.description}</p>
            )}
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-3xl font-bold text-primary">
                {Math.round(progress_percentage)}%
              </div>
              <p className="text-sm text-muted-foreground">
                {completed_milestones} of {total_milestones} milestones
              </p>
            </div>
            {/* Continue Learning Button - links back to chat */}
            {roadmap.conversation_id && (
              <Link href={`/dashboard/chat?roadmap=${roadmap.id}&conversation_id=${roadmap.conversation_id}`}>
                <Button variant="default" size="sm" className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  Continue Learning
                </Button>
              </Link>
            )}
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Overall Progress</span>
            <span className="font-medium">{completed_milestones}/{total_milestones}</span>
          </div>
          <Progress value={progress_percentage} className="h-3" />
        </div>
      </div>

      {/* Phase Timeline */}
      <div className="relative">
        {/* Vertical connecting line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-border hidden md:block" />

        {/* Phases */}
        <div className="space-y-8">
          {roadmap_data.phases.map((phase, index) => {
            const phaseProgress = calculatePhaseProgress(phase);
            const isCompleted = phaseProgress === 100;
            const isActive = phaseProgress > 0 && phaseProgress < 100;
            const isLocked = phaseProgress === 0 && index > 0;

            return (
              <div key={phase.id} className="relative">
                {/* Phase indicator (circle on timeline) */}
                <div className="absolute left-0 -translate-x-1/2 hidden md:flex items-center justify-center w-12 h-12 rounded-full border-2 bg-background z-10">
                  {isCompleted ? (
                    <CheckCircle2 className="h-6 w-6 text-green-500" />
                  ) : isActive ? (
                    <Circle className="h-6 w-6 text-primary fill-primary" />
                  ) : (
                    <Lock className="h-6 w-6 text-muted-foreground" />
                  )}
                </div>

                {/* Phase Card */}
                <div className="md:ml-16">
                  <PhaseCard
                    phase={phase}
                    phaseNumber={index + 1}
                    roadmapId={roadmap.id}
                    isCompleted={isCompleted}
                    isActive={isActive}
                    isLocked={isLocked}
                    onMilestoneClick={onMilestoneClick}
                    onMilestoneComplete={onMilestoneComplete}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Completion Badge */}
      {progress_percentage === 100 && (
        <div className="bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-lg p-6 text-center">
          <CheckCircle2 className="h-12 w-12 mx-auto mb-3" />
          <h3 className="text-xl font-bold mb-1">Roadmap Completed! 🎉</h3>
          <p className="text-green-50">
            Congratulations! You've completed all milestones in this learning path.
          </p>
        </div>
      )}
    </div>
  );
}

/**
 * Calculate progress percentage for a phase
 */
function calculatePhaseProgress(phase: any): number {
  const milestones = phase.milestones || [];
  if (milestones.length === 0) return 0;

  const completedCount = milestones.filter((m: any) => m.status === 'completed').length;
  return (completedCount / milestones.length) * 100;
}
