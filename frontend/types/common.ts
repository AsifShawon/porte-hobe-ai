/**
 * Common Type Definitions
 * Shared types across the application
 */

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface ApiError {
  status: number;
  message: string;
  detail?: string;
}

export interface LoadingState {
  isLoading: boolean;
  error: ApiError | null;
}

// Filters
export interface GoalFilters {
  status?: string;
  goal_type?: string;
}

export interface ExerciseFilters {
  exercise_type?: string;
  difficulty?: string;
  topic_id?: string;
  completed?: boolean;
}

export interface ResourceFilters {
  resource_type?: string;
  category?: string;
  topic_id?: string;
  is_favorite?: boolean;
  tag?: string;
  search?: string;
}

export interface ProgressFilters {
  status?: string;
}

// Topic (from existing system)
export interface Topic {
  id: string;
  title: string;
  description: string;
  category: string;
  difficulty_level: string;
  estimated_hours: number;
  prerequisites: string[];
  learning_objectives: string[];
  is_locked: boolean;
  progress_percentage: number;
  status: ProgressStatus;
}
