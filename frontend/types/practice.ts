/**
 * Practice & Exercise Type Definitions
 * Matches backend practice_router.py models
 */

export type ExerciseType = 'coding' | 'quiz' | 'math' | 'concept' | 'debugging';

export type ExerciseDifficulty = 'beginner' | 'intermediate' | 'advanced' | 'expert';

export type SubmissionStatus = 'pending' | 'correct' | 'incorrect' | 'partial';

export interface Exercise {
  id: string;
  title: string;
  description: string;
  exercise_type: ExerciseType;
  difficulty: ExerciseDifficulty;
  topic_id?: string;
  topic_title?: string;
  points: number;
  time_limit?: number; // minutes
  content: Record<string, any>; // Exercise-specific content
  hints: string[];
  solution?: string; // Only shown after completion
  tags: string[];
  created_at: string;
  attempts: number;
  completed: boolean;
  best_score?: number;
}

export interface ExerciseSubmission {
  exercise_id: string;
  answer: string; // Code, answer text, or JSON
  time_spent?: number; // seconds
  metadata?: Record<string, any>;
}

export interface Submission {
  id: string;
  exercise_id: string;
  user_id: string;
  answer: string;
  status: SubmissionStatus;
  score: number; // 0-100
  feedback: string;
  hints_used: number;
  time_spent?: number;
  submitted_at: string;
  test_results?: Record<string, any>;
}

export interface PracticeStats {
  total_exercises: number;
  completed_exercises: number;
  in_progress_exercises: number;
  total_attempts: number;
  success_rate: number;
  average_score: number;
  total_points_earned: number;
  exercises_by_type: Record<ExerciseType, { total: number; completed: number }>;
  exercises_by_difficulty: Record<ExerciseDifficulty, { total: number; completed: number }>;
  recent_submissions: Submission[];
}

export interface CreateExerciseRequest {
  title: string;
  description: string;
  exercise_type: ExerciseType;
  difficulty: ExerciseDifficulty;
  topic_id?: string;
  points?: number;
  time_limit?: number;
  content: Record<string, any>;
  hints?: string[];
  solution?: string;
  tags?: string[];
}
