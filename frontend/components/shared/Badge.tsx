/**
 * Badge Component
 * Status and achievement badges
 */

import React from 'react';
import { cn } from '@/lib/utils';
import type { AchievementRarity, ExerciseDifficulty, GoalStatus } from '@/types';

interface BadgeProps {
  variant?: 'default' | 'outline' | 'solid';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  children: React.ReactNode;
}

export function Badge({
  variant = 'default',
  size = 'md',
  className,
  children,
}: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full font-medium',
        {
          'px-2 py-0.5 text-xs': size === 'sm',
          'px-2.5 py-0.5 text-sm': size === 'md',
          'px-3 py-1 text-base': size === 'lg',
        },
        {
          'bg-muted text-foreground': variant === 'default',
          'border border-current bg-transparent': variant === 'outline',
          'bg-primary text-primary-foreground': variant === 'solid',
        },
        className
      )}
    >
      {children}
    </span>
  );
}

/**
 * Rarity Badge for Achievements
 */

const rarityColors: Record<AchievementRarity, string> = {
  common: 'bg-gray-500/10 text-gray-700 dark:text-gray-300 border-gray-500/20',
  uncommon: 'bg-green-500/10 text-green-700 dark:text-green-300 border-green-500/20',
  rare: 'bg-blue-500/10 text-blue-700 dark:text-blue-300 border-blue-500/20',
  epic: 'bg-purple-500/10 text-purple-700 dark:text-purple-300 border-purple-500/20',
  legendary: 'bg-yellow-500/10 text-yellow-700 dark:text-yellow-300 border-yellow-500/20',
};

export function RarityBadge({ rarity }: { rarity: AchievementRarity }) {
  return (
    <Badge
      variant="outline"
      size="sm"
      className={cn('border', rarityColors[rarity])}
    >
      {rarity.charAt(0).toUpperCase() + rarity.slice(1)}
    </Badge>
  );
}

/**
 * Difficulty Badge for Exercises
 */

const difficultyColors: Record<ExerciseDifficulty, string> = {
  beginner: 'bg-green-500/10 text-green-700 dark:text-green-300 border-green-500/20',
  intermediate: 'bg-yellow-500/10 text-yellow-700 dark:text-yellow-300 border-yellow-500/20',
  advanced: 'bg-orange-500/10 text-orange-700 dark:text-orange-300 border-orange-500/20',
  expert: 'bg-red-500/10 text-red-700 dark:text-red-300 border-red-500/20',
};

export function DifficultyBadge({ difficulty }: { difficulty: ExerciseDifficulty }) {
  return (
    <Badge
      variant="outline"
      size="sm"
      className={cn('border', difficultyColors[difficulty])}
    >
      {difficulty.charAt(0).toUpperCase() + difficulty.slice(1)}
    </Badge>
  );
}

/**
 * Status Badge for Goals
 */

const statusColors: Record<GoalStatus, string> = {
  active: 'bg-blue-500/10 text-blue-700 dark:text-blue-300 border-blue-500/20',
  completed: 'bg-green-500/10 text-green-700 dark:text-green-300 border-green-500/20',
  failed: 'bg-red-500/10 text-red-700 dark:text-red-300 border-red-500/20',
  paused: 'bg-gray-500/10 text-gray-700 dark:text-gray-300 border-gray-500/20',
};

export function StatusBadge({ status }: { status: GoalStatus }) {
  return (
    <Badge
      variant="outline"
      size="sm"
      className={cn('border', statusColors[status])}
    >
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  );
}
