/**
 * QuizPopup Component
 * Modal popup for taking quizzes during conversations
 */

'use client';

import { useState, useEffect } from 'react';
import { ConversationQuiz, QuizResults } from '@/types/quiz';
import { useQuizAttempt } from '@/hooks/useQuiz';
import { QuizQuestion } from './QuizQuestion';
import { QuizResults as QuizResultsComponent } from './QuizResults';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, ChevronLeft, ChevronRight, X } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface QuizPopupProps {
  quiz: ConversationQuiz;
  open: boolean;
  onClose: () => void;
  onComplete: (results: QuizResults) => void;
  onSkip?: () => void;
}

export function QuizPopup({ quiz, open, onClose, onComplete, onSkip }: QuizPopupProps) {
  const {
    attempt,
    currentQuestion,
    currentQuestionIndex,
    answers,
    loading,
    error,
    submitting,
    isLastQuestion,
    isFirstQuestion,
    answeredQuestions,
    totalQuestions,
    allAnswered,
    startAttempt,
    submitAnswer,
    completeAttempt,
    nextQuestion,
    previousQuestion,
  } = useQuizAttempt(quiz.id);

  const [currentAnswer, setCurrentAnswer] = useState('');
  const [questionStartTime, setQuestionStartTime] = useState(Date.now());
  const [showResults, setShowResults] = useState(false);
  const [results, setResults] = useState<QuizResults | null>(null);

  // Start the attempt when popup opens
  useEffect(() => {
    if (open && !attempt) {
      startAttempt();
    }
  }, [open, attempt, startAttempt]);

  // Reset answer when question changes
  useEffect(() => {
    if (currentQuestion) {
      setCurrentAnswer(answers[currentQuestion.id] || '');
      setQuestionStartTime(Date.now());
    }
  }, [currentQuestion, answers]);

  const handleAnswerChange = (answer: string) => {
    setCurrentAnswer(answer);
  };

  const handleSubmitAnswer = async () => {
    if (!currentQuestion || !currentAnswer.trim()) return;

    const timeSpent = Math.floor((Date.now() - questionStartTime) / 1000);

    await submitAnswer(currentQuestion.id, currentAnswer, timeSpent);

    // Auto-advance to next question after submitting
    if (!isLastQuestion) {
      setTimeout(() => {
        nextQuestion();
      }, 500);
    }
  };

  const handleCompleteQuiz = async () => {
    const quizResults = await completeAttempt();
    if (quizResults) {
      setResults(quizResults);
      setShowResults(true);
    }
  };

  const handleFinish = () => {
    if (results) {
      onComplete(results);
    }
    onClose();
  };

  const progressPercentage = (answeredQuestions / totalQuestions) * 100;

  // Show results screen
  if (showResults && results) {
    return (
      <Dialog open={open} onOpenChange={onClose}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <QuizResultsComponent
            results={results}
            quiz={quiz}
            onClose={handleFinish}
          />
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <DialogTitle className="text-2xl">{quiz.title}</DialogTitle>
              {quiz.description && (
                <DialogDescription className="mt-2">{quiz.description}</DialogDescription>
              )}
            </div>
            {onSkip && (
              <Button variant="ghost" size="sm" onClick={onSkip} className="ml-2">
                <X className="h-4 w-4 mr-1" />
                Skip
              </Button>
            )}
          </div>

          {/* Quiz metadata */}
          <div className="flex gap-2 mt-3">
            <Badge variant="outline">{quiz.difficulty}</Badge>
            <Badge variant="outline">{quiz.total_points} points</Badge>
            {quiz.time_limit && <Badge variant="outline">{quiz.time_limit} min</Badge>}
          </div>
        </DialogHeader>

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error.message}</AlertDescription>
          </Alert>
        )}

        {loading ? (
          <div className="py-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4" />
            <p className="text-muted-foreground">Loading quiz...</p>
          </div>
        ) : currentQuestion ? (
          <div className="space-y-6">
            {/* Progress bar */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">
                  Question {currentQuestionIndex + 1} of {totalQuestions}
                </span>
                <span className="font-medium">{answeredQuestions} answered</span>
              </div>
              <Progress value={progressPercentage} className="h-2" />
            </div>

            {/* Current Question */}
            <QuizQuestion
              question={currentQuestion}
              answer={currentAnswer}
              onChange={handleAnswerChange}
              disabled={submitting}
            />

            {/* Navigation buttons */}
            <div className="flex items-center justify-between pt-4 border-t">
              <Button
                variant="outline"
                onClick={previousQuestion}
                disabled={isFirstQuestion || submitting}
              >
                <ChevronLeft className="h-4 w-4 mr-1" />
                Previous
              </Button>

              <div className="flex gap-2">
                {!isLastQuestion ? (
                  <>
                    <Button
                      variant="outline"
                      onClick={nextQuestion}
                      disabled={submitting}
                    >
                      Skip
                    </Button>
                    <Button
                      onClick={handleSubmitAnswer}
                      disabled={!currentAnswer.trim() || submitting}
                    >
                      {submitting ? 'Submitting...' : 'Submit & Next'}
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      variant="outline"
                      onClick={handleSubmitAnswer}
                      disabled={!currentAnswer.trim() || submitting}
                    >
                      Submit Answer
                    </Button>
                    <Button
                      onClick={handleCompleteQuiz}
                      disabled={!allAnswered || submitting}
                    >
                      Finish Quiz
                    </Button>
                  </>
                )}
              </div>
            </div>

            {/* Helpful hint */}
            {isLastQuestion && !allAnswered && (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  You haven't answered all questions. Go back to complete them or finish now.
                </AlertDescription>
              </Alert>
            )}
          </div>
        ) : (
          <div className="py-12 text-center text-muted-foreground">
            <p>No questions available</p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
