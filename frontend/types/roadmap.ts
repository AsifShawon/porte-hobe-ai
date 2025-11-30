/**
 * TypeScript types for Learning Roadmaps
 */

export interface LearningRoadmap {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  domain: RoadmapDomain;
  roadmap_data: RoadmapData;
  total_milestones: number;
  completed_milestones: number;
  progress_percentage: number;
  current_phase_id?: string;
  current_milestone_id?: string;
  status: RoadmapStatus;
  conversation_id?: string;
  chat_session_id?: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export type RoadmapDomain = 'programming' | 'math' | 'general';

export type RoadmapStatus = 'active' | 'completed' | 'paused' | 'abandoned';

export interface RoadmapData {
  phases: Phase[];
  total_milestones: number;
  completed_milestones: number;
}

export interface Phase {
  id: string;
  title: string;
  order: number;
  description?: string;
  milestones: Milestone[];
}

export interface Milestone {
  id: string;
  title: string;
  type: MilestoneType;
  estimated_time: number; // in minutes
  description?: string;
  topics?: string[];
  status: MilestoneStatus;
  quiz_id?: string;
  difficulty?: QuizDifficulty;
  order: number;
  // Progress data (enriched from milestone_progress table)
  progress?: number;
  started_at?: string;
  completed_at?: string;
}

export type MilestoneType = 'lesson' | 'quiz';

export type MilestoneStatus = 'not_started' | 'in_progress' | 'completed' | 'locked' | 'skipped';

export type QuizDifficulty = 'beginner' | 'intermediate' | 'advanced' | 'expert';

// API Request/Response types

export interface CreateRoadmapRequest {
  user_goal: string;
  domain: RoadmapDomain;
  conversation_history?: Array<{role: string; content: string}>;
  user_context?: Record<string, any>;
  conversation_id?: string;  // Link roadmap to chat conversation
  chat_session_id?: string;  // Chat session for navigation
}

export interface CreateRoadmapResponse {
  status: string;
  roadmap_id: string;
  roadmap: LearningRoadmap;
}

export interface UpdateMilestoneRequest {
  status: MilestoneStatus;
  progress_percentage?: number;
  notes?: string;
}

export interface AdaptRoadmapRequest {
  performance_data: Record<string, any>;
  user_struggles?: string[];
  user_strengths?: string[];
}

export interface MilestoneProgress {
  id: string;
  user_id: string;
  roadmap_id: string;
  phase_id: string;
  milestone_id: string;
  milestone_title?: string;
  milestone_type?: MilestoneType;
  status: MilestoneStatus;
  progress_percentage: number;
  quiz_id?: string;
  quiz_passed?: boolean;
  best_quiz_score?: number;
  started_at?: string;
  completed_at?: string;
  time_spent: number; // in seconds
  notes?: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface RoadmapFilters {
  status?: RoadmapStatus;
  domain?: RoadmapDomain;
  limit?: number;
}

export interface RoadmapStats {
  total_roadmaps: number;
  active_roadmaps: number;
  completed_roadmaps: number;
  total_milestones: number;
  completed_milestones: number;
  average_progress: number;
}
