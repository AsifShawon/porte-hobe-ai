/**
 * TypeScript types for Quizzes and Quiz Attempts
 */

export interface ConversationQuiz {
  id: string;
  user_id: string;
  roadmap_id?: string;
  conversation_id?: string;
  title: string;
  description?: string;
  topic: string;
  difficulty: QuizDifficulty;
  questions: QuizQuestion[];
  total_points: number;
  passing_score: number; // percentage
  attempts_allowed: number;
  attempts_used: number;
  time_limit?: number; // in minutes
  estimated_duration: number; // in minutes
  status: QuizStatus;
  trigger_condition?: string;
  triggered_at?: string;
  presented_at?: string;
  phase_id?: string;
  milestone_id?: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  // Enriched data (from attempts)
  attempt_count?: number;
  best_score?: number;
  completed_attempts?: number;
}

export type QuizDifficulty = 'beginner' | 'intermediate' | 'advanced' | 'expert';

export type QuizStatus = 'not_started' | 'in_progress' | 'completed' | 'skipped';

export interface QuizQuestion {
  id: string;
  type: QuestionType;
  question: string;
  options?: string[]; // for multiple_choice, true_false
  correct_answer?: string; // hidden until quiz completed or graded
  explanation?: string; // shown after grading
  points: number;
  order: number;
  // For short_answer questions
  keywords?: string[];
  // For code questions
  template?: string;
  test_cases?: TestCase[];
}

export type QuestionType = 'multiple_choice' | 'true_false' | 'short_answer' | 'code';

export interface TestCase {
  input: any | any[];
  expected: any;
}

export interface QuizAttempt {
  id: string;
  user_id: string;
  quiz_id: string;
  roadmap_id?: string;
  attempt_number: number;
  answers: Record<string, AnswerResult>;
  total_questions: number;
  correct_answers: number;
  partial_credit_answers: number;
  points_earned: number;
  total_points: number;
  percentage_score: number;
  overall_feedback?: string;
  strengths?: string[];
  weaknesses?: string[];
  recommendations?: string[];
  time_spent: number; // in seconds
  started_at: string;
  completed_at?: string;
  status: AttemptStatus;
  passed: boolean;
  metadata: Record<string, any>;
  created_at: string;
}

export type AttemptStatus = 'in_progress' | 'completed' | 'abandoned';

export interface AnswerResult {
  answer: string;
  correct: boolean;
  points_earned: number;
  feedback: string;
  time_spent: number; // in seconds
  partial_credit?: boolean;
  test_results?: TestResult[];
  key_concepts_covered?: string[];
}

export interface TestResult {
  passed: boolean;
  input: any | any[];
  expected: any;
  output?: any;
  error?: string;
}

// API Request/Response types

export interface GenerateQuizRequest {
  topics: string[];
  conversation_context?: string;
  num_questions?: number;
  difficulty: QuizDifficulty;
  roadmap_id?: string;
  phase_id?: string;
  milestone_id?: string;
}

export interface GenerateQuizResponse {
  status: string;
  quiz_id: string;
  quiz: ConversationQuiz;
}

export interface StartAttemptRequest {
  quiz_id: string;
}

export interface StartAttemptResponse {
  status: string;
  attempt_id: string;
  attempt: QuizAttempt;
  quiz: ConversationQuiz;
}

export interface SubmitAnswerRequest {
  question_id: string;
  answer: string;
  time_spent?: number;
}

export interface SubmitAnswerResponse {
  status: string;
  question_id: string;
  grading_result: GradingResult;
}

export interface GradingResult {
  correct: boolean;
  points_earned: number;
  feedback: string;
  partial_credit?: boolean;
  test_results?: TestResult[];
  key_concepts_covered?: string[];
}

export interface CompleteQuizResponse {
  status: string;
  results: QuizResults;
  attempt: QuizAttempt;
}

export interface QuizResults {
  attempt_id: string;
  percentage_score: number;
  passed: boolean;
  correct_answers: number;
  total_questions: number;
  time_spent: number;
  overall_feedback: string;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  next_topics: string[];
}

export interface QuizFilters {
  roadmap_id?: string;
  status?: QuizStatus;
  difficulty?: QuizDifficulty;
  limit?: number;
}

export interface QuizStats {
  total_quizzes: number;
  completed_quizzes: number;
  passed_quizzes: number;
  average_score: number;
  total_time_spent: number;
}

// Quiz popup component props
export interface QuizPopupProps {
  quiz: ConversationQuiz;
  onComplete: (results: QuizResults) => void;
  onSkip: () => void;
}

// Question component props
export interface QuizQuestionProps {
  question: QuizQuestion;
  answer?: string;
  onChange: (answer: string) => void;
  disabled?: boolean;
  showFeedback?: boolean;
  feedback?: AnswerResult;
}
