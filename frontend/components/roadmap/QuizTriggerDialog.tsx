/**
 * QuizTriggerDialog Component
 * Shown when a quiz milestone is unlocked after completing a lesson
 */

'use client';

import { useRouter } from 'next/navigation';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { FileQuestion, Award, Clock, Brain } from 'lucide-react';

interface QuizTriggerData {
  type: string;
  phase_id: string;
  phase_title: string;
  milestone_id: string;
  milestone_title: string;
  quiz_difficulty: string;
  topics: string[];
  trigger_reason: string;
}

interface QuizTriggerDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  quizData: QuizTriggerData | null;
  roadmapId?: string;
  onStartQuiz?: () => void;
}

export function QuizTriggerDialog({
  open,
  onOpenChange,
  quizData,
  roadmapId,
  onStartQuiz,
}: QuizTriggerDialogProps) {
  const router = useRouter();

  if (!quizData) return null;

  const handleStartQuiz = () => {
    // Close dialog
    onOpenChange(false);

    // Navigate to quiz page or trigger quiz generation
    if (onStartQuiz) {
      onStartQuiz();
    } else {
      // Navigate to quiz page (to be implemented)
      console.log('Starting quiz:', quizData.milestone_id);
      // router.push(`/dashboard/quiz/${quizData.milestone_id}`);
    }
  };

  const handleSkip = () => {
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-3 rounded-full bg-primary/10">
              <FileQuestion className="h-6 w-6 text-primary" />
            </div>
            <div className="flex-1">
              <DialogTitle className="text-xl">Quiz Unlocked! 🎯</DialogTitle>
              <DialogDescription>
                Great progress! You've unlocked a new quiz.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-4">
          {/* Quiz Info */}
          <div className="bg-muted/50 rounded-lg p-4 space-y-3">
            <div>
              <h4 className="font-semibold text-sm text-muted-foreground mb-1">
                Quiz Title
              </h4>
              <p className="font-medium">{quizData.milestone_title}</p>
            </div>

            <div>
              <h4 className="font-semibold text-sm text-muted-foreground mb-1">
                Phase
              </h4>
              <p className="text-sm">{quizData.phase_title}</p>
            </div>

            {/* Difficulty */}
            <div className="flex items-center gap-2">
              <Brain className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Difficulty:</span>
              <Badge
                variant={
                  quizData.quiz_difficulty === 'beginner'
                    ? 'default'
                    : quizData.quiz_difficulty === 'intermediate'
                    ? 'secondary'
                    : 'destructive'
                }
              >
                {quizData.quiz_difficulty}
              </Badge>
            </div>

            {/* Topics */}
            {quizData.topics && quizData.topics.length > 0 && (
              <div>
                <h4 className="font-semibold text-sm text-muted-foreground mb-2">
                  Topics Covered
                </h4>
                <div className="flex flex-wrap gap-2">
                  {quizData.topics.map((topic, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {topic}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Reason for triggering */}
          <div className="bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-900 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <Award className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-green-900 dark:text-green-100">
                  {quizData.trigger_reason}
                </p>
                <p className="text-xs text-green-700 dark:text-green-300 mt-1">
                  Test your knowledge and reinforce what you've learned!
                </p>
              </div>
            </div>
          </div>

          {/* Info note */}
          <div className="flex items-start gap-2 text-sm text-muted-foreground">
            <Clock className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <p>
              You can take this quiz now or come back to it later from your roadmap.
            </p>
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button variant="outline" onClick={handleSkip}>
            Maybe Later
          </Button>
          <Button onClick={handleStartQuiz} className="gap-2">
            <FileQuestion className="h-4 w-4" />
            Start Quiz
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
