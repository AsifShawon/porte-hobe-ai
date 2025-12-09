/**
 * LevelProgress Component
 * Shows user's current level and XP progress
 */

'use client';

import React from 'react';
import { Trophy, Zap } from 'lucide-react';
import { ProgressBar } from '@/components/shared';
import { cn } from '@/lib/utils';
import type { AchievementStats } from '@/types';

interface LevelProgressProps {
  stats: AchievementStats;
  className?: string;
}

export function LevelProgress({ stats, className }: LevelProgressProps) {
  return (
    <div className={cn('bg-gradient-to-br from-primary/10 to-primary/5 rounded-lg border p-6', className)}>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-primary/20 p-3">
              <Trophy className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h3 className="text-sm font-medium text-muted-foreground">Current Level</h3>
              <p className="text-3xl font-bold">Level {stats.level}</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-muted-foreground">Total XP</p>
            <p className="text-2xl font-bold text-primary">{stats.total_points}</p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Progress to Level {stats.level + 1}</span>
            <span className="font-medium">{stats.next_level_points} XP to go</span>
          </div>
          <ProgressBar
            value={stats.level_progress}
            max={100}
            size="lg"
            color="purple"
          />
        </div>

        {/* Achievements Summary */}
        <div className="flex items-center gap-6 pt-4 border-t">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-yellow-500" />
            <span className="text-sm">
              <span className="font-semibold">{stats.unlocked_achievements}</span>
              <span className="text-muted-foreground">/{stats.total_achievements} unlocked</span>
            </span>
          </div>
          <div className="text-sm text-muted-foreground">
            {Math.round((stats.unlocked_achievements / stats.total_achievements) * 100)}% complete
          </div>
        </div>
      </div>
    </div>
  );
}
