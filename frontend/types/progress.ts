/**
 * Progress & Analytics Type Definitions
 * Matches backend progress_router.py models
 */

export type ProgressStatus = 'not_started' | 'in_progress' | 'completed';

export interface TopicProgress {
  id: string;
  topic_id: string;
  topic_title: string;
  score: number;
  completed_lessons: number;
  total_lessons: number;
  status: ProgressStatus;
  last_activity: string;
  progress_percentage: number;
}

export interface UpdateProgressRequest {
  topic_id: string;
  score_delta?: number;
  completed_lessons?: number;
  metadata?: Record<string, any>;
}

export interface OverallStats {
  total_topics: number;
  completed_topics: number;
  in_progress_topics: number;
  average_score: number;
  total_time_spent: number; // minutes
  streak_days: number;
  achievements: Array<{
    title: string;
    description: string;
    icon: string;
  }>;
}

export interface LearningStats extends OverallStats {
  topics_by_category?: Record<string, number>;
  weekly_activity?: Array<{
    date: string;
    minutes: number;
    topics_completed: number;
  }>;
  score_trend?: Array<{
    date: string;
    average_score: number;
  }>;
}
