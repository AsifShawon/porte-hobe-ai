/**
 * QuestionForm Component
 * Renders different question types with appropriate input controls
 */

'use client';

import { useState } from 'react';
import type { QuizQuestion, AnswerResult } from '@/types/quiz';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Checkbox } from '@/components/ui/checkbox';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

interface QuestionFormProps {
  question: QuizQuestion;
  answer?: string;
  onChange: (answer: string) => void;
  disabled?: boolean;
  showFeedback?: boolean;
  feedback?: AnswerResult;
}

export function QuestionForm({
  question,
  answer,
  onChange,
  disabled = false,
  showFeedback = false,
  feedback,
}: QuestionFormProps) {
  // Render different question types
  switch (question.type) {
    case 'multiple_choice':
      return (
        <MultipleChoiceQuestion
          question={question}
          answer={answer}
          onChange={onChange}
          disabled={disabled}
          showFeedback={showFeedback}
          feedback={feedback}
        />
      );

    case 'true_false':
      return (
        <TrueFalseQuestion
          question={question}
          answer={answer}
          onChange={onChange}
          disabled={disabled}
          showFeedback={showFeedback}
          feedback={feedback}
        />
      );

    case 'short_answer':
      return (
        <ShortAnswerQuestion
          question={question}
          answer={answer}
          onChange={onChange}
          disabled={disabled}
          showFeedback={showFeedback}
          feedback={feedback}
        />
      );

    case 'code':
      return (
        <CodeQuestion
          question={question}
          answer={answer}
          onChange={onChange}
          disabled={disabled}
          showFeedback={showFeedback}
          feedback={feedback}
        />
      );

    default:
      return (
        <div className="text-muted-foreground">
          Unsupported question type: {question.type}
        </div>
      );
  }
}

// Multiple Choice Question
function MultipleChoiceQuestion({
  question,
  answer,
  onChange,
  disabled,
  showFeedback,
  feedback,
}: QuestionFormProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium">{question.question}</h3>

      <RadioGroup
        value={answer || ''}
        onValueChange={onChange}
        disabled={disabled}
        className="space-y-3"
      >
        {question.options?.map((option, index) => {
          const isSelected = answer === option;
          const isCorrect = showFeedback && feedback?.correct && isSelected;
          const isWrong = showFeedback && !feedback?.correct && isSelected;

          return (
            <div
              key={index}
              className={cn(
                'flex items-center space-x-3 p-4 rounded-lg border transition-all',
                isSelected && !showFeedback && 'border-primary bg-primary/5',
                isCorrect && 'border-green-500 bg-green-50 dark:bg-green-950/20',
                isWrong && 'border-red-500 bg-red-50 dark:bg-red-950/20',
                !isSelected && !showFeedback && 'hover:border-primary/50'
              )}
            >
              <RadioGroupItem value={option} id={`option-${index}`} />
              <Label
                htmlFor={`option-${index}`}
                className={cn(
                  'flex-1 cursor-pointer',
                  disabled && 'cursor-not-allowed opacity-60'
                )}
              >
                {option}
              </Label>
            </div>
          );
        })}
      </RadioGroup>
    </div>
  );
}

// True/False Question
function TrueFalseQuestion({
  question,
  answer,
  onChange,
  disabled,
  showFeedback,
  feedback,
}: QuestionFormProps) {
  const options = ['True', 'False'];

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium">{question.question}</h3>

      <RadioGroup
        value={answer || ''}
        onValueChange={onChange}
        disabled={disabled}
        className="space-y-3"
      >
        {options.map((option) => {
          const isSelected = answer === option;
          const isCorrect = showFeedback && feedback?.correct && isSelected;
          const isWrong = showFeedback && !feedback?.correct && isSelected;

          return (
            <div
              key={option}
              className={cn(
                'flex items-center space-x-3 p-4 rounded-lg border transition-all',
                isSelected && !showFeedback && 'border-primary bg-primary/5',
                isCorrect && 'border-green-500 bg-green-50 dark:bg-green-950/20',
                isWrong && 'border-red-500 bg-red-50 dark:bg-red-950/20',
                !isSelected && !showFeedback && 'hover:border-primary/50'
              )}
            >
              <RadioGroupItem value={option} id={option.toLowerCase()} />
              <Label
                htmlFor={option.toLowerCase()}
                className={cn(
                  'flex-1 cursor-pointer text-lg font-medium',
                  disabled && 'cursor-not-allowed opacity-60'
                )}
              >
                {option}
              </Label>
            </div>
          );
        })}
      </RadioGroup>
    </div>
  );
}

// Short Answer Question
function ShortAnswerQuestion({
  question,
  answer,
  onChange,
  disabled,
  showFeedback,
  feedback,
}: QuestionFormProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium">{question.question}</h3>

      {question.keywords && question.keywords.length > 0 && !showFeedback && (
        <div className="bg-muted/50 p-3 rounded-lg">
          <p className="text-sm text-muted-foreground mb-1">
            💡 Hint: Your answer should cover these concepts:
          </p>
          <div className="flex flex-wrap gap-2">
            {question.keywords.map((keyword, index) => (
              <span
                key={index}
                className="text-xs bg-background px-2 py-1 rounded border"
              >
                {keyword}
              </span>
            ))}
          </div>
        </div>
      )}

      <Textarea
        value={answer || ''}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder="Type your answer here..."
        rows={6}
        className={cn(
          'resize-none',
          showFeedback && feedback?.correct && 'border-green-500',
          showFeedback && !feedback?.correct && 'border-red-500'
        )}
      />

      <p className="text-xs text-muted-foreground">
        Be clear and concise. Include key concepts and explanations.
      </p>
    </div>
  );
}

// Code Question
function CodeQuestion({
  question,
  answer,
  onChange,
  disabled,
  showFeedback,
  feedback,
}: QuestionFormProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium">{question.question}</h3>

      {question.template && !showFeedback && (
        <div className="bg-muted/50 p-3 rounded-lg">
          <p className="text-sm text-muted-foreground mb-2">Template:</p>
          <pre className="text-xs bg-background p-2 rounded border overflow-x-auto">
            <code>{question.template}</code>
          </pre>
        </div>
      )}

      <div className="relative">
        <Textarea
          value={answer || question.template || ''}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          placeholder="Write your code here..."
          rows={12}
          className={cn(
            'font-mono text-sm resize-none',
            showFeedback && feedback?.correct && 'border-green-500',
            showFeedback && !feedback?.correct && 'border-red-500'
          )}
        />
      </div>

      {question.test_cases && question.test_cases.length > 0 && !showFeedback && (
        <div className="bg-muted/50 p-3 rounded-lg">
          <p className="text-sm font-medium mb-2">Test Cases:</p>
          <div className="space-y-2">
            {question.test_cases.map((testCase, index) => (
              <div key={index} className="text-xs bg-background p-2 rounded">
                <span className="text-muted-foreground">Input:</span>{' '}
                <code className="text-primary">
                  {Array.isArray(testCase.input)
                    ? JSON.stringify(testCase.input)
                    : testCase.input}
                </code>
                <br />
                <span className="text-muted-foreground">Expected:</span>{' '}
                <code className="text-green-600">{JSON.stringify(testCase.expected)}</code>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Show test results if available */}
      {showFeedback && feedback?.test_results && (
        <div className="space-y-2">
          <p className="text-sm font-medium">Test Results:</p>
          {feedback.test_results.map((result, index) => (
            <div
              key={index}
              className={cn(
                'p-3 rounded-lg border text-xs',
                result.passed
                  ? 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-900'
                  : 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900'
              )}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className={result.passed ? 'text-green-600' : 'text-red-600'}>
                  {result.passed ? '✓' : '✗'}
                </span>
                <span className="font-medium">Test Case {index + 1}</span>
              </div>
              <div className="text-muted-foreground space-y-1">
                <div>
                  Input: <code>{JSON.stringify(result.input)}</code>
                </div>
                <div>
                  Expected: <code className="text-green-600">{JSON.stringify(result.expected)}</code>
                </div>
                {result.output && (
                  <div>
                    Output: <code className={result.passed ? 'text-green-600' : 'text-red-600'}>
                      {JSON.stringify(result.output)}
                    </code>
                  </div>
                )}
                {result.error && (
                  <div className="text-red-600">
                    Error: <code>{result.error}</code>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <p className="text-xs text-muted-foreground">
        Write clean, working code. Your solution will be tested automatically.
      </p>
    </div>
  );
}
