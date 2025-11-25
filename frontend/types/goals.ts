/**
 * Goal Type Definitions
 * Matches backend goal_router.py models
 */

export type GoalType = 'daily' | 'weekly' | 'monthly' | 'custom' | 'topic_completion' | 'streak' | 'practice';

export type GoalStatus = 'active' | 'completed' | 'failed' | 'paused';

export interface Goal {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  goal_type: GoalType;
  target_value: number;
  current_value: number;
  unit: string; // topics, minutes, days, points
  progress_percentage: number;
  status: GoalStatus;
  deadline?: string; // ISO datetime
  topic_id?: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface CreateGoalRequest {
  title: string;
  description?: string;
  goal_type: GoalType;
  target_value: number;
  current_value?: number;
  unit?: string;
  deadline?: string;
  topic_id?: string;
  metadata?: Record<string, any>;
}

export interface UpdateGoalRequest {
  title?: string;
  description?: string;
  current_value?: number;
  increment_value?: number;
  status?: GoalStatus;
  deadline?: string;
  metadata?: Record<string, any>;
}

export interface GoalStats {
  total_goals: number;
  active_goals: number;
  completed_goals: number;
  failed_goals: number;
  completion_rate: number;
  current_streak: number;
  longest_streak: number;
}
