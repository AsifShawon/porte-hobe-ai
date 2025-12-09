/**
 * CreateGoalDialog Component
 * Dialog for creating new goals
 */

'use client';

import React, { useState } from 'react';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { CreateGoalRequest, GoalType } from '@/types';

interface CreateGoalDialogProps {
  onCreateGoal: (data: CreateGoalRequest) => Promise<void>;
}

const goalTypes: { value: GoalType; label: string }[] = [
  { value: 'daily', label: 'Daily Goal' },
  { value: 'weekly', label: 'Weekly Goal' },
  { value: 'monthly', label: 'Monthly Goal' },
  { value: 'topic_completion', label: 'Topic Completion' },
  { value: 'streak', label: 'Streak Goal' },
  { value: 'practice', label: 'Practice Goal' },
  { value: 'custom', label: 'Custom Goal' },
];

const units = ['topics', 'minutes', 'days', 'points', 'exercises', 'hours'];

export function CreateGoalDialog({ onCreateGoal }: CreateGoalDialogProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState<CreateGoalRequest>({
    title: '',
    description: '',
    goal_type: 'daily',
    target_value: 1,
    unit: 'topics',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await onCreateGoal(formData);
      setOpen(false);
      // Reset form
      setFormData({
        title: '',
        description: '',
        goal_type: 'daily',
        target_value: 1,
        unit: 'topics',
      });
    } catch (error) {
      console.error('Failed to create goal:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Create Goal
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Create New Goal</DialogTitle>
          <DialogDescription>
            Set a new learning goal to track your progress
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title">Goal Title *</Label>
            <Input
              id="title"
              placeholder="e.g., Complete 5 programming topics"
              value={formData.title}
              onChange={(e) =>
                setFormData({ ...formData, title: e.target.value })
              }
              required
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description (Optional)</Label>
            <Input
              id="description"
              placeholder="Add more details about this goal"
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
            />
          </div>

          {/* Goal Type */}
          <div className="space-y-2">
            <Label htmlFor="goal_type">Goal Type *</Label>
            <Select
              value={formData.goal_type}
              onValueChange={(value) =>
                setFormData({ ...formData, goal_type: value as GoalType })
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {goalTypes.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Target & Unit */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="target">Target Value *</Label>
              <Input
                id="target"
                type="number"
                min="1"
                value={formData.target_value}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    target_value: parseInt(e.target.value) || 1,
                  })
                }
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="unit">Unit *</Label>
              <Select
                value={formData.unit}
                onValueChange={(value) =>
                  setFormData({ ...formData, unit: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {units.map((unit) => (
                    <SelectItem key={unit} value={unit}>
                      {unit}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Deadline */}
          <div className="space-y-2">
            <Label htmlFor="deadline">Deadline (Optional)</Label>
            <Input
              id="deadline"
              type="datetime-local"
              value={formData.deadline || ''}
              onChange={(e) =>
                setFormData({ ...formData, deadline: e.target.value })
              }
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Creating...' : 'Create Goal'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
