/**
 * QuizQuestion Component
 * Renders different types of quiz questions (MCQ, code, short answer, true/false)
 */

'use client';

import { QuizQuestion as QuizQuestionType, AnswerResult } from '@/types/quiz';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface QuizQuestionProps {
  question: QuizQuestionType;
  answer?: string;
  onChange: (answer: string) => void;
  disabled?: boolean;
  showFeedback?: boolean;
  feedback?: AnswerResult;
}

export function QuizQuestion({
  question,
  answer = '',
  onChange,
  disabled = false,
  showFeedback = false,
  feedback,
}: QuizQuestionProps) {
  return (
    <div className="space-y-4">
      {/* Question header */}
      <div className="space-y-2">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <h3 className="text-lg font-semibold">{question.question}</h3>
          </div>
          <div className="flex gap-2 flex-shrink-0">
            <Badge variant="secondary">{question.type.replace('_', ' ')}</Badge>
            <Badge variant="outline">{question.points} pts</Badge>
          </div>
        </div>

        {/* Feedback (if shown) */}
        {showFeedback && feedback && (
          <Alert
            variant={feedback.correct ? 'default' : 'destructive'}
            className={cn(
              feedback.correct && 'border-green-500 bg-green-50 dark:bg-green-950/20'
            )}
          >
            <div className="flex items-start gap-2">
              {feedback.correct ? (
                <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
              ) : (
                <XCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
              )}
              <div className="flex-1">
                <div className="font-medium mb-1">
                  {feedback.correct ? 'Correct!' : 'Incorrect'}
                  {feedback.partial_credit && ' (Partial Credit)'}
                  {' '}
                  {feedback.points_earned}/{question.points} points
                </div>
                <AlertDescription>{feedback.feedback}</AlertDescription>
              </div>
            </div>
          </Alert>
        )}
      </div>

      {/* Question content based on type */}
      {question.type === 'multiple_choice' && (
        <MultipleChoiceQuestion
          question={question}
          answer={answer}
          onChange={onChange}
          disabled={disabled}
        />
      )}

      {question.type === 'true_false' && (
        <TrueFalseQuestion
          question={question}
          answer={answer}
          onChange={onChange}
          disabled={disabled}
        />
      )}

      {question.type === 'short_answer' && (
        <ShortAnswerQuestion
          question={question}
          answer={answer}
          onChange={onChange}
          disabled={disabled}
        />
      )}

      {question.type === 'code' && (
        <CodeQuestion
          question={question}
          answer={answer}
          onChange={onChange}
          disabled={disabled}
          testResults={feedback?.test_results}
        />
      )}
    </div>
  );
}

/**
 * Multiple Choice Question
 */
function MultipleChoiceQuestion({
  question,
  answer,
  onChange,
  disabled,
}: {
  question: QuizQuestionType;
  answer: string;
  onChange: (value: string) => void;
  disabled: boolean;
}) {
  return (
    <RadioGroup value={answer} onValueChange={onChange} disabled={disabled}>
      <div className="space-y-3">
        {question.options?.map((option, index) => (
          <div key={index} className="flex items-center space-x-3">
            <RadioGroupItem value={option} id={`option-${index}`} />
            <Label
              htmlFor={`option-${index}`}
              className="flex-1 cursor-pointer font-normal"
            >
              {option}
            </Label>
          </div>
        ))}
      </div>
    </RadioGroup>
  );
}

/**
 * True/False Question
 */
function TrueFalseQuestion({
  question,
  answer,
  onChange,
  disabled,
}: {
  question: QuizQuestionType;
  answer: string;
  onChange: (value: string) => void;
  disabled: boolean;
}) {
  return (
    <RadioGroup value={answer} onValueChange={onChange} disabled={disabled}>
      <div className="space-y-3">
        <div className="flex items-center space-x-3">
          <RadioGroupItem value="True" id="true" />
          <Label htmlFor="true" className="flex-1 cursor-pointer font-normal">
            True
          </Label>
        </div>
        <div className="flex items-center space-x-3">
          <RadioGroupItem value="False" id="false" />
          <Label htmlFor="false" className="flex-1 cursor-pointer font-normal">
            False
          </Label>
        </div>
      </div>
    </RadioGroup>
  );
}

/**
 * Short Answer Question
 */
function ShortAnswerQuestion({
  question,
  answer,
  onChange,
  disabled,
}: {
  question: QuizQuestionType;
  answer: string;
  onChange: (value: string) => void;
  disabled: boolean;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor="answer">Your Answer</Label>
      <Textarea
        id="answer"
        value={answer}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder="Type your answer here..."
        rows={4}
        className="resize-none"
      />
      <p className="text-sm text-muted-foreground">
        Write a clear, concise answer in 1-3 sentences.
      </p>
    </div>
  );
}

/**
 * Code Question
 */
function CodeQuestion({
  question,
  answer,
  onChange,
  disabled,
  testResults,
}: {
  question: QuizQuestionType;
  answer: string;
  onChange: (value: string) => void;
  disabled: boolean;
  testResults?: any[];
}) {
  return (
    <div className="space-y-4">
      {/* Code template hint */}
      {question.template && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <div className="font-medium mb-1">Template:</div>
            <pre className="text-xs bg-muted p-2 rounded overflow-x-auto mt-2">
              <code>{question.template}</code>
            </pre>
          </AlertDescription>
        </Alert>
      )}

      {/* Code editor */}
      <div className="space-y-2">
        <Label htmlFor="code">Your Code</Label>
        <Textarea
          id="code"
          value={answer}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          placeholder="Write your code here..."
          rows={12}
          className="font-mono text-sm resize-none"
        />
      </div>

      {/* Test cases info */}
      {question.test_cases && question.test_cases.length > 0 && (
        <div className="text-sm text-muted-foreground">
          <p className="font-medium mb-1">Test Cases:</p>
          <div className="space-y-1">
            {question.test_cases.map((tc, index) => (
              <div key={index} className="flex items-center gap-2">
                <Badge variant="outline" className="font-mono text-xs">
                  Input: {JSON.stringify(tc.input)}
                </Badge>
                <span>→</span>
                <Badge variant="outline" className="font-mono text-xs">
                  Expected: {JSON.stringify(tc.expected)}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Test results (if shown) */}
      {testResults && testResults.length > 0 && (
        <div className="space-y-2">
          <p className="font-medium text-sm">Test Results:</p>
          <div className="space-y-2">
            {testResults.map((result, index) => (
              <div
                key={index}
                className={cn(
                  'p-3 rounded-lg border text-sm',
                  result.passed
                    ? 'bg-green-50 dark:bg-green-950/20 border-green-200'
                    : 'bg-red-50 dark:bg-red-950/20 border-red-200'
                )}
              >
                <div className="flex items-center gap-2 mb-1">
                  {result.passed ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  ) : (
                    <XCircle className="h-4 w-4 text-red-600" />
                  )}
                  <span className="font-medium">
                    Test Case {index + 1}: {result.passed ? 'Passed' : 'Failed'}
                  </span>
                </div>
                <div className="font-mono text-xs space-y-1 ml-6">
                  <div>Input: {JSON.stringify(result.input)}</div>
                  <div>Expected: {JSON.stringify(result.expected)}</div>
                  {result.output !== undefined && (
                    <div>Your Output: {JSON.stringify(result.output)}</div>
                  )}
                  {result.error && <div className="text-red-600">Error: {result.error}</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
