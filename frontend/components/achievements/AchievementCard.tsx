/**
 * AchievementCard Component
 * Displays achievement with locked/unlocked state
 */

'use client';

import React from 'react';
import { Lock, Trophy } from 'lucide-react';
import { cn } from '@/lib/utils';
import { RarityBadge, ProgressBar } from '@/components/shared';
import type { AchievementProgress } from '@/types';

interface AchievementCardProps {
  achievement: AchievementProgress;
  className?: string;
}

const categoryColors = {
  learning: 'from-blue-500/20 to-blue-600/20',
  streak: 'from-orange-500/20 to-orange-600/20',
  mastery: 'from-purple-500/20 to-purple-600/20',
  social: 'from-green-500/20 to-green-600/20',
  milestone: 'from-yellow-500/20 to-yellow-600/20',
  challenge: 'from-red-500/20 to-red-600/20',
};

export function AchievementCard({ achievement, className }: AchievementCardProps) {
  const isUnlocked = !achievement.locked;

  return (
    <div
      className={cn(
        'relative rounded-lg border p-6 transition-all duration-200',
        isUnlocked
          ? 'bg-gradient-to-br shadow-sm hover:shadow-md'
          : 'bg-muted/30 hover:bg-muted/50',
        isUnlocked && categoryColors[achievement.category],
        className
      )}
    >
      {/* Locked Overlay */}
      {!isUnlocked && (
        <div className="absolute inset-0 flex items-center justify-center bg-background/60 backdrop-blur-[2px] rounded-lg">
          <div className="rounded-full bg-muted p-3">
            <Lock className="h-6 w-6 text-muted-foreground" />
          </div>
        </div>
      )}

      {/* Content */}
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start gap-3">
          <div className={cn(
            'text-4xl flex-shrink-0',
            !isUnlocked && 'grayscale opacity-50'
          )}>
            {achievement.icon}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2 mb-2">
              <h3 className={cn(
                'font-semibold text-lg truncate',
                !isUnlocked && 'text-muted-foreground'
              )}>
                {achievement.title}
              </h3>
              <RarityBadge rarity={achievement.rarity} />
            </div>
            <p className={cn(
              'text-sm line-clamp-2',
              isUnlocked ? 'text-muted-foreground' : 'text-muted-foreground/70'
            )}>
              {achievement.description}
            </p>
          </div>
        </div>

        {/* Progress */}
        {!isUnlocked && achievement.progress_percentage > 0 && (
          <div className="space-y-2">
            <ProgressBar
              value={achievement.progress_percentage}
              max={100}
              showLabel={false}
              size="sm"
              color="purple"
            />
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>
                {achievement.current_value} / {achievement.target_value}
              </span>
              <span>{Math.round(achievement.progress_percentage)}% complete</span>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-2 border-t">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Trophy className="h-4 w-4" />
            <span>{achievement.points} XP</span>
          </div>
          <span className="text-xs text-muted-foreground capitalize">
            {achievement.category}
          </span>
        </div>
      </div>
    </div>
  );
}
