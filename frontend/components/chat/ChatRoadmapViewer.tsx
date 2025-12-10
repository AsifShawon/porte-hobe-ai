/**
 * ChatRoadmapViewer Component
 * A floating button that opens a scrollable roadmap panel within the chat interface
 * Allows users to view and interact with their learning roadmap phases and milestones
 */

'use client';

import { useState, useCallback } from 'react';
import { Phase, Milestone } from '@/types/roadmap';
import { useRoadmap } from '@/hooks/useRoadmap';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import {
  Map,
  CheckCircle2,
  Lock,
  Play,
  BookOpen,
  FileQuestion,
  Clock,
  Loader2,
  Trophy,
  Target,
  ChevronDown,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ChatMilestoneQuiz } from './ChatMilestoneQuiz';

interface ChatRoadmapViewerProps {
  roadmapId: string | null;
  conversationId?: string | null;
  onMilestoneStart?: (phaseId: string, milestoneId: string) => void;
  onMilestoneComplete?: (phaseId: string, milestoneId: string, quizPassed?: boolean) => void;
}

export function ChatRoadmapViewer({
  roadmapId,
  onMilestoneStart,
  onMilestoneComplete,
}: ChatRoadmapViewerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [completingMilestoneId, setCompletingMilestoneId] = useState<string | null>(null);
  const [quizMilestone, setQuizMilestone] = useState<{
    phaseId: string;
    milestone: Milestone;
  } | null>(null);
  const [expandedPhases, setExpandedPhases] = useState<Set<string>>(new Set());

  const {
    roadmap,
    loading,
    error,
    startMilestone,
    completeMilestone,
    refetch,
  } = useRoadmap(roadmapId);

  // Toggle phase expansion
  const togglePhase = useCallback((phaseId: string) => {
    setExpandedPhases(prev => {
      const next = new Set(prev);
      if (next.has(phaseId)) {
        next.delete(phaseId);
      } else {
        next.add(phaseId);
      }
      return next;
    });
  }, []);

  // Handle milestone start
  const handleStartMilestone = useCallback(async (phaseId: string, milestoneId: string) => {
    try {
      await startMilestone(phaseId, milestoneId);
      onMilestoneStart?.(phaseId, milestoneId);
      await refetch();
    } catch (err) {
      console.error('Failed to start milestone:', err);
    }
  }, [startMilestone, onMilestoneStart, refetch]);

  // Handle milestone completion checkbox
  const handleMarkComplete = useCallback((phase: Phase, milestone: Milestone) => {
    // Show quiz dialog for completion
    setQuizMilestone({ phaseId: phase.id, milestone });
  }, []);

  // Handle quiz completion
  const handleQuizComplete = useCallback(async (passed: boolean) => {
    if (!quizMilestone) return;

    setCompletingMilestoneId(quizMilestone.milestone.id);
    try {
      await completeMilestone(
        quizMilestone.phaseId,
        quizMilestone.milestone.id,
        `Completed with quiz - ${passed ? 'passed' : 'needs review'}`
      );
      onMilestoneComplete?.(quizMilestone.phaseId, quizMilestone.milestone.id, passed);
      await refetch();
    } catch (err) {
      console.error('Failed to complete milestone:', err);
    } finally {
      setCompletingMilestoneId(null);
      setQuizMilestone(null);
    }
  }, [quizMilestone, completeMilestone, onMilestoneComplete, refetch]);

  // Handle skipping quiz (direct completion)
  const handleSkipQuiz = useCallback(async () => {
    if (!quizMilestone) return;

    setCompletingMilestoneId(quizMilestone.milestone.id);
    try {
      await completeMilestone(
        quizMilestone.phaseId,
        quizMilestone.milestone.id,
        'Completed without quiz'
      );
      onMilestoneComplete?.(quizMilestone.phaseId, quizMilestone.milestone.id);
      await refetch();
    } catch (err) {
      console.error('Failed to complete milestone:', err);
    } finally {
      setCompletingMilestoneId(null);
      setQuizMilestone(null);
    }
  }, [quizMilestone, completeMilestone, onMilestoneComplete, refetch]);

  if (!roadmapId) return null;

  return (
    <>
      {/* Floating Button */}
      <Sheet open={isOpen} onOpenChange={setIsOpen}>
        <SheetTrigger asChild>
          <Button
            variant="outline"
            size="icon"
            className={cn(
              "fixed bottom-24 right-6 z-50 h-14 w-14 rounded-full shadow-lg",
              "bg-linear-to-br from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700",
              "text-white border-none transition-all hover:scale-105",
              roadmap && roadmap.progress_percentage === 100 && "from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700"
            )}
          >
            {roadmap && roadmap.progress_percentage === 100 ? (
              <Trophy className="h-6 w-6" />
            ) : (
              <Map className="h-6 w-6" />
            )}
            {roadmap && roadmap.progress_percentage > 0 && roadmap.progress_percentage < 100 && (
              <span className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-amber-500 text-xs flex items-center justify-center font-bold">
                {Math.round(roadmap.progress_percentage)}%
              </span>
            )}
          </Button>
        </SheetTrigger>

        <SheetContent side="right" className="w-full sm:w-[450px] p-0">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center h-full p-6 text-center">
              <p className="text-destructive mb-4">Failed to load roadmap</p>
              <Button onClick={() => refetch()} variant="outline">
                Try Again
              </Button>
            </div>
          ) : roadmap ? (
            <div className="flex flex-col h-full">
              {/* Header */}
              <SheetHeader className="p-6 pb-4 border-b bg-linear-to-br from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30">
                <div className="flex items-start gap-3">
                  <div className="rounded-full bg-blue-100 dark:bg-blue-900 p-2 shrink-0">
                    <Target className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <SheetTitle className="text-lg truncate">{roadmap.title}</SheetTitle>
                    {roadmap.description && (
                      <SheetDescription className="text-sm line-clamp-2 mt-1">
                        {roadmap.description}
                      </SheetDescription>
                    )}
                  </div>
                </div>

                {/* Progress Overview */}
                <div className="mt-4 space-y-2">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Progress</span>
                    <span className="font-semibold text-primary">
                      {roadmap.completed_milestones}/{roadmap.total_milestones} milestones
                    </span>
                  </div>
                  <Progress value={roadmap.progress_percentage} className="h-3" />
                  <p className="text-xs text-muted-foreground text-center">
                    {Math.round(roadmap.progress_percentage)}% complete
                  </p>
                </div>
              </SheetHeader>

              {/* Scrollable Phase List */}
              <div className="flex-1 overflow-y-auto p-4">
                <div className="space-y-3">
                  {roadmap.roadmap_data.phases.map((phase, phaseIndex) => {
                    const phaseProgress = calculatePhaseProgress(phase);
                    const isCompleted = phaseProgress === 100;
                    const isActive = phaseProgress > 0 && phaseProgress < 100;
                    const isLocked = phaseProgress === 0 && phaseIndex > 0 && 
                      calculatePhaseProgress(roadmap.roadmap_data.phases[phaseIndex - 1]) < 100;
                    const isExpanded = expandedPhases.has(phase.id) || isActive;

                    return (
                      <Collapsible
                        key={phase.id}
                        open={isExpanded && !isLocked}
                        onOpenChange={() => !isLocked && togglePhase(phase.id)}
                      >
                        <div
                          className={cn(
                            "border rounded-lg overflow-hidden",
                            isCompleted && "border-green-300 dark:border-green-800",
                            isActive && "border-blue-300 dark:border-blue-800",
                            isLocked && "opacity-60"
                          )}
                        >
                          <CollapsibleTrigger
                            className={cn(
                              "w-full px-4 py-3 text-left hover:bg-accent/50 transition-colors",
                              isCompleted && "bg-green-50 dark:bg-green-950/20",
                              isActive && "bg-blue-50 dark:bg-blue-950/20"
                            )}
                            disabled={isLocked}
                          >
                            <div className="flex items-center gap-3 w-full">
                              <div className={cn(
                                "flex items-center justify-center w-8 h-8 rounded-full shrink-0",
                                isCompleted && "bg-green-500 text-white",
                                isActive && "bg-blue-500 text-white",
                                !isCompleted && !isActive && "bg-muted"
                              )}>
                                {isCompleted ? (
                                  <CheckCircle2 className="h-4 w-4" />
                                ) : isLocked ? (
                                  <Lock className="h-4 w-4" />
                                ) : (
                                  <span className="text-sm font-semibold">{phaseIndex + 1}</span>
                                )}
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="font-medium text-sm truncate">{phase.title}</p>
                                <div className="flex items-center gap-2 mt-1">
                                  <Progress value={phaseProgress} className="h-1.5 flex-1" />
                                  <span className="text-xs text-muted-foreground shrink-0">
                                    {Math.round(phaseProgress)}%
                                  </span>
                                </div>
                              </div>
                              <ChevronDown className={cn(
                                "h-4 w-4 transition-transform shrink-0",
                                isExpanded && "rotate-180"
                              )} />
                            </div>
                          </CollapsibleTrigger>

                          {!isLocked && (
                            <CollapsibleContent>
                              <div className="px-4 pb-4 space-y-2 border-t">
                                {phase.milestones.map((milestone, milestoneIndex) => (
                                  <MilestoneRow
                                    key={milestone.id}
                                    milestone={milestone}
                                    phase={phase}
                                    index={milestoneIndex}
                                    isCompleting={completingMilestoneId === milestone.id}
                                    onStart={() => handleStartMilestone(phase.id, milestone.id)}
                                    onMarkComplete={() => handleMarkComplete(phase, milestone)}
                                  />
                                ))}
                              </div>
                            </CollapsibleContent>
                          )}
                        </div>
                      </Collapsible>
                    );
                  })}
                </div>

                {/* Completion Message */}
                {roadmap.progress_percentage === 100 && (
                  <div className="mt-6 p-4 rounded-lg bg-linear-to-r from-green-500 to-emerald-500 text-white text-center">
                    <Trophy className="h-8 w-8 mx-auto mb-2" />
                    <h3 className="font-bold">Roadmap Completed! 🎉</h3>
                    <p className="text-sm text-green-50 mt-1">
                      Congratulations on completing your learning journey!
                    </p>
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </SheetContent>
      </Sheet>

      {/* Quiz Dialog */}
      {quizMilestone && (
        <ChatMilestoneQuiz
          open={!!quizMilestone}
          milestone={quizMilestone.milestone}
          phaseId={quizMilestone.phaseId}
          roadmapId={roadmapId}
          onComplete={handleQuizComplete}
          onSkip={handleSkipQuiz}
          onClose={() => setQuizMilestone(null)}
        />
      )}
    </>
  );
}

/**
 * Individual milestone row component
 */
interface MilestoneRowProps {
  milestone: Milestone;
  phase: Phase;
  index: number;
  isCompleting: boolean;
  onStart: () => void;
  onMarkComplete: () => void;
}

function MilestoneRow({
  milestone,
  index,
  isCompleting,
  onStart,
  onMarkComplete,
}: MilestoneRowProps) {
  const isCompleted = milestone.status === 'completed';
  const isInProgress = milestone.status === 'in_progress';
  const isLocked = milestone.status === 'locked';
  const isNotStarted = milestone.status === 'not_started';

  return (
    <div
      className={cn(
        "flex items-center gap-3 p-3 rounded-lg border transition-all mt-2",
        isCompleted && "bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-900",
        isInProgress && "bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-900",
        isLocked && "opacity-50",
        !isLocked && !isCompleted && "hover:border-primary/50"
      )}
    >
      {/* Checkbox/Status */}
      <button
        onClick={isCompleted ? undefined : onMarkComplete}
        disabled={isLocked || isCompleting}
        className={cn(
          "w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all shrink-0",
          isCompleted && "bg-green-500 border-green-500 text-white",
          isInProgress && "border-blue-500",
          !isCompleted && !isInProgress && "border-muted-foreground/30 hover:border-primary",
          isLocked && "cursor-not-allowed"
        )}
      >
        {isCompleting ? (
          <Loader2 className="h-3 w-3 animate-spin" />
        ) : isCompleted ? (
          <CheckCircle2 className="h-4 w-4" />
        ) : null}
      </button>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          {milestone.type === 'quiz' ? (
            <FileQuestion className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
          ) : (
            <BookOpen className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
          )}
          <span className={cn(
            "text-sm truncate",
            isCompleted && "line-through text-muted-foreground"
          )}>
            {index + 1}. {milestone.title}
          </span>
        </div>

        {/* Topics */}
        {milestone.topics && milestone.topics.length > 0 && (
          <div className="flex gap-1 mt-1 flex-wrap">
            {milestone.topics.slice(0, 2).map((topic, i) => (
              <Badge key={i} variant="secondary" className="text-[10px] px-1.5 py-0">
                {topic}
              </Badge>
            ))}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 shrink-0">
        {milestone.estimated_time && (
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {milestone.estimated_time}m
          </span>
        )}

        {!isLocked && !isCompleted && (
          <Button
            variant={isInProgress ? "default" : "outline"}
            size="sm"
            className="h-7 text-xs"
            onClick={isNotStarted ? onStart : undefined}
          >
            {isInProgress ? (
              <>
                <Play className="h-3 w-3 mr-1" />
                Continue
              </>
            ) : (
              <>
                <Play className="h-3 w-3 mr-1" />
                Start
              </>
            )}
          </Button>
        )}
      </div>
    </div>
  );
}

/**
 * Calculate progress percentage for a phase
 */
function calculatePhaseProgress(phase: Phase): number {
  const milestones = phase.milestones || [];
  if (milestones.length === 0) return 0;

  const completedCount = milestones.filter((m) => m.status === 'completed').length;
  return (completedCount / milestones.length) * 100;
}
