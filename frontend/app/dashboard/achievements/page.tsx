/**
 * Achievements Page
 * View all achievements, track progress, and see XP/level
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Trophy, Award, Star, Filter } from 'lucide-react';
import { PageHeader, LoadingState, ErrorState, EmptyState } from '@/components/shared';
import { AchievementCard, LevelProgress } from '@/components/achievements';
import { useAchievementProgress, useAchievementStats } from '@/hooks';
import type { AchievementCategory, AchievementRarity } from '@/types';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';

type FilterType = 'all' | 'locked' | 'unlocked';

export default function AchievementsPage() {
  const [categoryFilter, setCategoryFilter] = useState<AchievementCategory | 'all'>('all');
  const [rarityFilter, setRarityFilter] = useState<AchievementRarity | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<FilterType>('all');

  // Fetch all achievements with progress
  const {
    progress: allAchievements,
    loading: achievementsLoading,
    error: achievementsError,
    refetch,
  } = useAchievementProgress();

  // Fetch stats
  const {
    stats,
    loading: statsLoading,
    checkForNew,
  } = useAchievementStats();

  // Check for new achievements on mount
  useEffect(() => {
    checkForNew().then((result) => {
      if (result.count > 0) {
        // Could show a toast notification here
        console.log(`🎉 Unlocked ${result.count} new achievement(s)!`);
      }
    });
  }, []);

  // Filter achievements
  const filteredAchievements = allAchievements.filter((achievement) => {
    if (categoryFilter !== 'all' && achievement.category !== categoryFilter) {
      return false;
    }
    if (rarityFilter !== 'all' && achievement.rarity !== rarityFilter) {
      return false;
    }
    if (statusFilter === 'locked' && !achievement.locked) {
      return false;
    }
    if (statusFilter === 'unlocked' && achievement.locked) {
      return false;
    }
    return true;
  });

  // Loading state
  if (achievementsLoading || statsLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Achievements"
          description="Your badges, milestones, and XP progress"
          icon={Trophy}
        />
        <LoadingState type="grid" count={6} />
      </div>
    );
  }

  // Error state
  if (achievementsError) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Achievements"
          description="Your badges, milestones, and XP progress"
          icon={Trophy}
        />
        <ErrorState error={achievementsError} onRetry={refetch} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        title="Achievements"
        description="Your badges, milestones, and XP progress"
        icon={Trophy}
      />

      {/* Level Progress Card */}
      {stats && <LevelProgress stats={stats} />}

      {/* Quick Stats */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-3">
          {/* Rarity Breakdown */}
          <div className="bg-card rounded-lg border p-4">
            <h4 className="text-sm font-medium mb-3">By Rarity</h4>
            <div className="space-y-2">
              {Object.entries(stats.rarity_breakdown).map(([rarity, count]) => (
                <div key={rarity} className="flex items-center justify-between text-sm">
                  <span className="capitalize text-muted-foreground">{rarity}</span>
                  <span className="font-medium">{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Category Breakdown */}
          <div className="bg-card rounded-lg border p-4">
            <h4 className="text-sm font-medium mb-3">By Category</h4>
            <div className="space-y-2">
              {Object.entries(stats.category_breakdown).slice(0, 5).map(([category, count]) => (
                <div key={category} className="flex items-center justify-between text-sm">
                  <span className="capitalize text-muted-foreground">{category}</span>
                  <span className="font-medium">{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Unlocks */}
          <div className="bg-card rounded-lg border p-4">
            <h4 className="text-sm font-medium mb-3">Recent Unlocks</h4>
            {stats.recent_achievements.length === 0 ? (
              <p className="text-sm text-muted-foreground">No achievements yet</p>
            ) : (
              <div className="space-y-2">
                {stats.recent_achievements.slice(0, 3).map((achievement) => (
                  <div key={achievement.id} className="flex items-center gap-2">
                    <span className="text-lg">{achievement.icon}</span>
                    <span className="text-sm truncate">{achievement.title}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Filters:</span>
        </div>

        <Select
          value={statusFilter}
          onValueChange={(value) => setStatusFilter(value as FilterType)}
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="unlocked">Unlocked</SelectItem>
            <SelectItem value="locked">Locked</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={categoryFilter}
          onValueChange={(value) => setCategoryFilter(value as AchievementCategory | 'all')}
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            <SelectItem value="learning">Learning</SelectItem>
            <SelectItem value="streak">Streak</SelectItem>
            <SelectItem value="mastery">Mastery</SelectItem>
            <SelectItem value="challenge">Challenge</SelectItem>
            <SelectItem value="milestone">Milestone</SelectItem>
            <SelectItem value="social">Social</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={rarityFilter}
          onValueChange={(value) => setRarityFilter(value as AchievementRarity | 'all')}
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Rarity" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Rarities</SelectItem>
            <SelectItem value="common">Common</SelectItem>
            <SelectItem value="uncommon">Uncommon</SelectItem>
            <SelectItem value="rare">Rare</SelectItem>
            <SelectItem value="epic">Epic</SelectItem>
            <SelectItem value="legendary">Legendary</SelectItem>
          </SelectContent>
        </Select>

        <div className="ml-auto text-sm text-muted-foreground">
          {filteredAchievements.length} achievement{filteredAchievements.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Achievements Grid */}
      {filteredAchievements.length === 0 ? (
        <EmptyState
          icon={Award}
          title="No achievements match your filters"
          description="Try adjusting your filters to see more achievements"
        />
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredAchievements.map((achievement) => (
            <AchievementCard
              key={achievement.achievement_id}
              achievement={achievement}
            />
          ))}
        </div>
      )}
    </div>
  );
}
