/**
 * ChatMilestoneQuiz Component
 * A form-based quiz dialog that appears when a user completes a milestone
 * Supports multiple choice and text input questions
 */

'use client';

import { useState, useEffect, useCallback, ChangeEvent } from 'react';
import { Milestone } from '@/types/roadmap';
import { ConversationQuiz } from '@/types/quiz';
import { useQuizzes } from '@/hooks/useQuiz';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  CheckCircle2,
  XCircle,
  Loader2,
  Trophy,
  Target,
  AlertTriangle,
  ChevronRight,
  ChevronLeft,
  FileQuestion,
  SkipForward,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatMilestoneQuizProps {
  open: boolean;
  milestone: Milestone;
  phaseId: string;
  roadmapId: string | null;
  onComplete: (passed: boolean) => void;
  onSkip: () => void;
  onClose: () => void;
}

export function ChatMilestoneQuiz({
  open,
  milestone,
  phaseId,
  roadmapId,
  onComplete,
  onSkip,
  onClose,
}: ChatMilestoneQuizProps) {
  const [stage, setStage] = useState<'prompt' | 'quiz' | 'results'>('prompt');
  const [quiz, setQuiz] = useState<ConversationQuiz | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [results, setResults] = useState<{
    score: number;
    total: number;
    passed: boolean;
    feedback: Record<string, { correct: boolean; feedback: string }>;
  } | null>(null);

  const { generateQuiz } = useQuizzes(undefined, { enabled: false });

  // Reset state when dialog opens
  useEffect(() => {
    if (open) {
      setStage('prompt');
      setQuiz(null);
      setCurrentQuestionIndex(0);
      setAnswers({});
      setResults(null);
    }
  }, [open]);

  // Handle quiz generation
  const handleStartQuiz = useCallback(async () => {
    setIsLoading(true);
    try {
      const topics = milestone.topics || [milestone.title];
      const generatedQuiz = await generateQuiz({
        topics,
        num_questions: 3, // Keep it short for inline quiz
        difficulty: milestone.difficulty || 'beginner',
        roadmap_id: roadmapId || undefined,
        phase_id: phaseId,
        milestone_id: milestone.id,
      });

      if (generatedQuiz) {
        setQuiz(generatedQuiz);
        setStage('quiz');
      }
    } catch (err) {
      console.error('Failed to generate quiz:', err);
      // On error, allow skipping
      onSkip();
    } finally {
      setIsLoading(false);
    }
  }, [generateQuiz, milestone, phaseId, roadmapId, onSkip]);

  // Handle answer change
  const handleAnswerChange = useCallback((questionId: string, answer: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: answer }));
  }, []);

  // Navigate questions
  const goToNextQuestion = useCallback(() => {
    if (quiz && currentQuestionIndex < quiz.questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    }
  }, [quiz, currentQuestionIndex]);

  const goToPreviousQuestion = useCallback(() => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  }, [currentQuestionIndex]);

  // Submit quiz
  const handleSubmitQuiz = useCallback(async () => {
    if (!quiz) return;

    setIsSubmitting(true);
    try {
      // Calculate results locally for quick feedback
      let correctCount = 0;
      const feedback: Record<string, { correct: boolean; feedback: string }> = {};

      quiz.questions.forEach(question => {
        const userAnswer = answers[question.id]?.trim().toLowerCase() || '';
        let isCorrect = false;

        if (question.type === 'multiple_choice' || question.type === 'true_false') {
          isCorrect = userAnswer === question.correct_answer?.toLowerCase();
        } else if (question.type === 'short_answer') {
          // For short answer, check if any keyword is present
          const keywords = question.keywords || [];
          isCorrect = keywords.some(kw => 
            userAnswer.includes(kw.toLowerCase())
          ) || userAnswer === question.correct_answer?.toLowerCase();
        }

        if (isCorrect) correctCount++;

        feedback[question.id] = {
          correct: isCorrect,
          feedback: isCorrect 
            ? 'Correct! Great job!' 
            : `The correct answer was: ${question.correct_answer || 'See explanation'}`,
        };
      });

      const score = Math.round((correctCount / quiz.questions.length) * 100);
      const passed = score >= (quiz.passing_score || 70);

      setResults({
        score,
        total: quiz.questions.length,
        passed,
        feedback,
      });
      setStage('results');
    } catch (err) {
      console.error('Failed to submit quiz:', err);
    } finally {
      setIsSubmitting(false);
    }
  }, [quiz, answers]);

  // Handle completion
  const handleComplete = useCallback(() => {
    if (results) {
      onComplete(results.passed);
    }
  }, [results, onComplete]);

  const currentQuestion = quiz?.questions[currentQuestionIndex];
  const isLastQuestion = quiz && currentQuestionIndex === quiz.questions.length - 1;
  const allAnswered = quiz && quiz.questions.every(q => answers[q.id]?.trim());

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-hidden flex flex-col">
        {/* Prompt Stage - Ask if user wants to take quiz */}
        {stage === 'prompt' && (
          <>
            <DialogHeader>
              <div className="flex items-center gap-3">
                <div className="rounded-full bg-green-100 dark:bg-green-900 p-2">
                  <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <DialogTitle>Mark as Complete?</DialogTitle>
                  <DialogDescription>
                    {milestone.title}
                  </DialogDescription>
                </div>
              </div>
            </DialogHeader>

            <div className="py-4">
              <Card className="border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-950/20">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <FileQuestion className="h-4 w-4" />
                    Quick Knowledge Check
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Take a short quiz to reinforce your learning and track your understanding.
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <ul className="text-xs text-muted-foreground space-y-1">
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-3 w-3 text-green-500" />
                      3 quick questions
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-3 w-3 text-green-500" />
                      Multiple choice & short answer
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-3 w-3 text-green-500" />
                      Instant feedback
                    </li>
                  </ul>
                </CardContent>
              </Card>
            </div>

            <DialogFooter className="flex-col sm:flex-row gap-2">
              <Button
                variant="outline"
                onClick={onSkip}
                className="w-full sm:w-auto"
              >
                <SkipForward className="h-4 w-4 mr-2" />
                Skip Quiz
              </Button>
              <Button
                onClick={handleStartQuiz}
                disabled={isLoading}
                className="w-full sm:w-auto bg-green-600 hover:bg-green-700"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Generating Quiz...
                  </>
                ) : (
                  <>
                    <Target className="h-4 w-4 mr-2" />
                    Take Quiz
                  </>
                )}
              </Button>
            </DialogFooter>
          </>
        )}

        {/* Quiz Stage */}
        {stage === 'quiz' && quiz && currentQuestion && (
          <>
            <DialogHeader>
              <div className="flex items-center justify-between">
                <DialogTitle className="text-lg">Knowledge Check</DialogTitle>
                <Badge variant="outline">
                  {currentQuestionIndex + 1} / {quiz.questions.length}
                </Badge>
              </div>
              <Progress
                value={((currentQuestionIndex + 1) / quiz.questions.length) * 100}
                className="h-2 mt-2"
              />
            </DialogHeader>

            <div className="flex-1 overflow-y-auto py-4">
              <div className="space-y-4">
                {/* Question */}
                <div className="space-y-3">
                  <Label className="text-base font-medium">
                    {currentQuestion.question}
                  </Label>

                  {/* Multiple Choice */}
                  {(currentQuestion.type === 'multiple_choice' || currentQuestion.type === 'true_false') && (
                    <div className="space-y-2">
                      {currentQuestion.options?.map((option, index) => {
                        const isSelected = answers[currentQuestion.id] === option;
                        return (
                          <div
                            key={index}
                            className={cn(
                              "flex items-center space-x-3 p-3 rounded-lg border transition-all cursor-pointer",
                              isSelected
                                ? "border-primary bg-primary/5"
                                : "hover:border-primary/50"
                            )}
                            onClick={() => handleAnswerChange(currentQuestion.id, option)}
                          >
                            <div className={cn(
                              "w-4 h-4 rounded-full border-2 flex items-center justify-center",
                              isSelected ? "border-primary bg-primary" : "border-muted-foreground"
                            )}>
                              {isSelected && <div className="w-2 h-2 rounded-full bg-white" />}
                            </div>
                            <Label className="flex-1 cursor-pointer text-sm">
                              {option}
                            </Label>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {/* Short Answer / Code */}
                  {(currentQuestion.type === 'short_answer' || currentQuestion.type === 'code') && (
                    <textarea
                      placeholder={currentQuestion.type === 'code' ? "Write your code here..." : "Type your answer here..."}
                      value={answers[currentQuestion.id] || ''}
                      onChange={(e: ChangeEvent<HTMLTextAreaElement>) => handleAnswerChange(currentQuestion.id, e.target.value)}
                      className={cn(
                        "w-full min-h-[100px] rounded-md border border-input bg-background px-3 py-2 text-sm",
                        "ring-offset-background placeholder:text-muted-foreground",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                        currentQuestion.type === 'code' && "font-mono"
                      )}
                    />
                  )}
                </div>
              </div>
            </div>

            <DialogFooter className="flex-row justify-between mt-4">
              <Button
                variant="outline"
                onClick={goToPreviousQuestion}
                disabled={currentQuestionIndex === 0}
              >
                <ChevronLeft className="h-4 w-4 mr-1" />
                Previous
              </Button>

              <div className="flex gap-2">
                {isLastQuestion ? (
                  <Button
                    onClick={handleSubmitQuiz}
                    disabled={!allAnswered || isSubmitting}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Submitting...
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="h-4 w-4 mr-2" />
                        Submit Quiz
                      </>
                    )}
                  </Button>
                ) : (
                  <Button onClick={goToNextQuestion}>
                    Next
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                )}
              </div>
            </DialogFooter>
          </>
        )}

        {/* Results Stage */}
        {stage === 'results' && results && (
          <>
            <DialogHeader>
              <div className="flex items-center gap-3">
                <div className={cn(
                  "rounded-full p-3",
                  results.passed
                    ? "bg-green-100 dark:bg-green-900"
                    : "bg-amber-100 dark:bg-amber-900"
                )}>
                  {results.passed ? (
                    <Trophy className="h-6 w-6 text-green-600 dark:text-green-400" />
                  ) : (
                    <AlertTriangle className="h-6 w-6 text-amber-600 dark:text-amber-400" />
                  )}
                </div>
                <div>
                  <DialogTitle>
                    {results.passed ? 'Quiz Passed! 🎉' : 'Keep Learning!'}
                  </DialogTitle>
                  <DialogDescription>
                    You scored {results.score}% ({Object.values(results.feedback).filter(f => f.correct).length}/{results.total} correct)
                  </DialogDescription>
                </div>
              </div>
            </DialogHeader>

            <div className="flex-1 overflow-y-auto max-h-[300px] py-4">
              <div className="space-y-3">
                {quiz?.questions.map((question, index) => {
                  const feedback = results.feedback[question.id];
                  return (
                    <div
                      key={question.id}
                      className={cn(
                        "p-3 rounded-lg border",
                        feedback?.correct
                          ? "bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-900"
                          : "bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900"
                      )}
                    >
                      <div className="flex items-start gap-2">
                        {feedback?.correct ? (
                          <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
                        ) : (
                          <XCircle className="h-4 w-4 text-red-600 mt-0.5 shrink-0" />
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium">Q{index + 1}: {question.question}</p>
                          <p className="text-xs text-muted-foreground mt-1">
                            Your answer: {answers[question.id] || '(no answer)'}
                          </p>
                          {!feedback?.correct && (
                            <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                              {feedback?.feedback}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <DialogFooter className="mt-4">
              <Button
                onClick={handleComplete}
                className={cn(
                  "w-full",
                  results.passed
                    ? "bg-green-600 hover:bg-green-700"
                    : "bg-amber-600 hover:bg-amber-700"
                )}
              >
                {results.passed ? (
                  <>
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    Complete Milestone
                  </>
                ) : (
                  <>
                    <Target className="h-4 w-4 mr-2" />
                    Mark Complete Anyway
                  </>
                )}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
