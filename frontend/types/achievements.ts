/**
 * Achievement Type Definitions
 * Matches backend achievement_router.py models
 */

export type AchievementCategory =
  | 'learning'
  | 'streak'
  | 'mastery'
  | 'social'
  | 'milestone'
  | 'challenge';

export type AchievementRarity =
  | 'common'
  | 'uncommon'
  | 'rare'
  | 'epic'
  | 'legendary';

export interface Achievement {
  id: string;
  user_id: string;
  achievement_id: string;
  title: string;
  description: string;
  category: AchievementCategory;
  rarity: AchievementRarity;
  icon: string;
  points: number;
  progress?: number;
  unlocked_at: string;
  metadata: Record<string, any>;
}

export interface AchievementProgress {
  achievement_id: string;
  title: string;
  description: string;
  category: AchievementCategory;
  rarity: AchievementRarity;
  icon: string;
  points: number;
  current_value: number;
  target_value: number;
  progress_percentage: number;
  locked: boolean;
}

export interface AchievementStats {
  total_achievements: number;
  unlocked_achievements: number;
  total_points: number;
  level: number;
  level_progress: number;
  next_level_points: number;
  rarity_breakdown: Record<AchievementRarity, number>;
  category_breakdown: Record<AchievementCategory, number>;
  recent_achievements: Achievement[];
}

export interface CheckAchievementsResponse {
  newly_unlocked: Achievement[];
  count: number;
}
