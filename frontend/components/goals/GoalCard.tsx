/**
 * GoalCard Component
 * Displays individual goal with progress and actions
 */

'use client';

import React from 'react';
import { Target, Calendar, Trash2, Edit, CheckCircle, Play } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ProgressBar, StatusBadge } from '@/components/shared';
import { cn } from '@/lib/utils';
import type { Goal } from '@/types';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface GoalCardProps {
  goal: Goal;
  onUpdate?: (id: string, data: { current_value?: number; status?: string }) => void;
  onDelete?: (id: string) => void;
  className?: string;
}

export function GoalCard({ goal, onUpdate, onDelete, className }: GoalCardProps) {
  const isExpired =
    goal.deadline &&
    new Date(goal.deadline) < new Date() &&
    goal.status === 'active';

  const daysLeft = goal.deadline
    ? Math.ceil(
        (new Date(goal.deadline).getTime() - new Date().getTime()) /
          (1000 * 60 * 60 * 24)
      )
    : null;

  const handleMarkComplete = () => {
    if (onUpdate) {
      onUpdate(goal.id, { status: 'completed' });
    }
  };

  const handleIncrement = () => {
    if (onUpdate && goal.current_value < goal.target_value) {
      onUpdate(goal.id, { current_value: goal.current_value + 1 });
    }
  };

  return (
    <div
      className={cn(
        'bg-card rounded-lg border p-6 shadow-sm hover:shadow-md transition-shadow',
        isExpired && 'border-destructive/50',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start gap-3 flex-1">
          <div className="rounded-lg bg-primary/10 p-2 mt-1">
            <Target className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-lg mb-1">{goal.title}</h3>
            {goal.description && (
              <p className="text-sm text-muted-foreground">{goal.description}</p>
            )}
            <div className="flex items-center gap-2 mt-2">
              <StatusBadge status={goal.status} />
              <span className="text-xs text-muted-foreground">
                {goal.goal_type.replace('_', ' ')}
              </span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm">
              •••
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {goal.status === 'active' && (
              <>
                <DropdownMenuItem onClick={handleIncrement}>
                  <Play className="mr-2 h-4 w-4" />
                  Increment Progress
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleMarkComplete}>
                  <CheckCircle className="mr-2 h-4 w-4" />
                  Mark Complete
                </DropdownMenuItem>
              </>
            )}
            <DropdownMenuItem onClick={() => onDelete?.(goal.id)} className="text-destructive">
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Progress */}
      <div className="mb-4">
        <ProgressBar
          value={goal.current_value}
          max={goal.target_value}
          showLabel
          color={goal.status === 'completed' ? 'green' : 'blue'}
          size="lg"
        />
        <div className="flex items-center justify-between text-xs text-muted-foreground mt-1">
          <span>
            {goal.current_value} / {goal.target_value} {goal.unit}
          </span>
          <span>{goal.progress_percentage}%</span>
        </div>
      </div>

      {/* Deadline */}
      {goal.deadline && (
        <div
          className={cn(
            'flex items-center gap-2 text-sm',
            isExpired ? 'text-destructive' : 'text-muted-foreground'
          )}
        >
          <Calendar className="h-4 w-4" />
          <span>
            {isExpired
              ? 'Expired'
              : daysLeft !== null
              ? `${daysLeft} day${daysLeft !== 1 ? 's' : ''} left`
              : 'No deadline'}
          </span>
        </div>
      )}
    </div>
  );
}
