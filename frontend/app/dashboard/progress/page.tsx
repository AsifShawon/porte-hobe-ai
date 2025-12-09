/**
 * Progress Page
 * Displays learning roadmaps with visual timeline and progress tracking
 */

'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useActiveRoadmap, useRoadmaps, useRoadmapStats } from '@/hooks/useRoadmap';
import { RoadmapTimeline } from '@/components/roadmap/RoadmapTimeline';
import { QuizTriggerDialog } from '@/components/roadmap/QuizTriggerDialog';
import { PageHeader } from '@/components/shared/PageHeader';
import { StatsCard } from '@/components/shared/StatsCard';
import { LoadingState } from '@/components/shared/LoadingState';
import { ErrorState } from '@/components/shared/ErrorState';
import { EmptyState } from '@/components/shared/EmptyState';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  TrendingUp,
  Target,
  CheckCircle2,
  Clock,
  Plus,
  Map,
} from 'lucide-react';
import type { RoadmapStatus } from '@/types/roadmap';

export default function ProgressPage() {
  const [selectedStatus, setSelectedStatus] = useState<RoadmapStatus | 'all'>('active');
  const [quizTrigger, setQuizTrigger] = useState<any>(null);
  const [quizDialogOpen, setQuizDialogOpen] = useState(false);

  const { roadmap: activeRoadmap, loading: activeLoading, error: activeError, completeMilestone } = useActiveRoadmap();
  const { stats, loading: statsLoading } = useRoadmapStats();
  const {
    roadmaps,
    loading: roadmapsLoading,
    error: roadmapsError,
    refetch,
  } = useRoadmaps(selectedStatus !== 'all' ? { status: selectedStatus } : undefined);

  const router = useRouter();

  // Milestone click: redirect to chat with auto_query prompt
  const handleMilestoneClick = useCallback((phaseId: string, milestoneId: string) => {
    if (!activeRoadmap) return;
    const phase = activeRoadmap.roadmap_data.phases.find(p => p.id === phaseId);
    const milestone = phase?.milestones.find(m => m.id === milestoneId);
    if (!phase || !milestone) return;

    const topicsStr = milestone.topics && milestone.topics.length ? milestone.topics.join(', ') : 'general fundamentals';
    const lessonPrompt = `You are my autonomous tutor. Teach milestone "${milestone.title}" from roadmap "${activeRoadmap.title}" (Phase: ${phase.title}).\nLearning objectives: ${milestone.description || 'Provide clear, structured guidance.'}\nTopics: ${topicsStr}.\nProvide:\n1. Concise overview\n2. Key concepts with examples\n3. Step-by-step explanation\n4. One interactive question (wait for my answer)\n5. Quick recap.\nAdapt depth to a beginner unless content implies otherwise.`;
    const quizPrompt = `Prepare me for quiz milestone "${milestone.title}" in roadmap "${activeRoadmap.title}" (Phase: ${phase.title}). Topics: ${topicsStr}. Provide:\n1. Key concept summary\n2. Common pitfalls\n3. 3 practice questions (wait for answers one by one)\n4. Final readiness check.`;
    const prompt = milestone.type === 'quiz' ? quizPrompt : lessonPrompt;
    const url = `/dashboard/chat?auto_query=${encodeURIComponent(prompt)}&roadmap_id=${activeRoadmap.id}&phase_id=${phaseId}&milestone_id=${milestoneId}` + (activeRoadmap.conversation_id ? `&conversation_id=${activeRoadmap.conversation_id}` : '');
    router.push(url);
  }, [activeRoadmap, router]);

  // Handle milestone completion
  const handleMilestoneComplete = async (phaseId: string, milestoneId: string) => {
    if (!completeMilestone) return;

    const result = await completeMilestone(phaseId, milestoneId);

    if (result.success && result.quiz_trigger) {
      // Show quiz trigger dialog
      setQuizTrigger(result.quiz_trigger);
      setQuizDialogOpen(true);
    }
  };

  if (activeLoading || statsLoading) {
    return (
      <div className="container mx-auto p-6">
        <PageHeader title="Learning Progress" icon={TrendingUp} />
        <LoadingState layout="grid" />
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Page Header */}
      <PageHeader
        title="Learning Progress"
        description="Track your learning journey and roadmap milestones"
        icon={TrendingUp}
      />

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Active Roadmaps"
          value={stats.active_roadmaps}
          subtitle={`${stats.total_roadmaps} total`}
          icon={Map}
          trend={{
            value: stats.active_roadmaps,
            isPositive: stats.active_roadmaps > 0,
          }}
        />

        <StatsCard
          title="Completed Roadmaps"
          value={stats.completed_roadmaps}
          subtitle={`${Math.round(stats.average_progress)}% avg progress`}
          icon={CheckCircle2}
          trend={{
            value: stats.completed_roadmaps,
            isPositive: true,
          }}
        />

        <StatsCard
          title="Total Milestones"
          value={stats.total_milestones}
          subtitle={`${stats.completed_milestones} completed`}
          icon={Target}
        />

        <StatsCard
          title="Progress"
          value={`${Math.round(stats.average_progress)}%`}
          subtitle="Average across all"
          icon={TrendingUp}
          trend={{
            value: stats.average_progress,
            isPositive: stats.average_progress > 0,
          }}
        />
      </div>

      {/* Active Roadmap Section */}
      {activeRoadmap ? (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold">Current Roadmap</h2>
            <Button variant="outline" size="sm" onClick={refetch}>
              Refresh
            </Button>
          </div>

          <RoadmapTimeline
            roadmap={activeRoadmap}
            onMilestoneClick={handleMilestoneClick}
            onMilestoneComplete={handleMilestoneComplete}
          />
        </div>
      ) : (
        !activeLoading && (
          <EmptyState
            icon={Map}
            title="No Active Roadmap"
            description="Create a learning roadmap to track your progress"
            action={{
              label: 'Create Roadmap',
              onClick: () => console.log('Create roadmap'),
            }}
          />
        )
      )}

      {/* All Roadmaps Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">All Roadmaps</h2>
          <div className="flex gap-2">
            <Select value={selectedStatus} onValueChange={(v) => setSelectedStatus(v as any)}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Roadmaps</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="paused">Paused</SelectItem>
              </SelectContent>
            </Select>

            <Button onClick={refetch} variant="outline" size="sm">
              Refresh
            </Button>
          </div>
        </div>

        {roadmapsLoading ? (
          <LoadingState layout="list" />
        ) : roadmapsError ? (
          <ErrorState
            title="Failed to load roadmaps"
            message={roadmapsError.message}
            onRetry={refetch}
          />
        ) : roadmaps.length === 0 ? (
          <EmptyState
            icon={Map}
            title="No Roadmaps Found"
            description={
              selectedStatus === 'all'
                ? 'Start your learning journey by creating a roadmap'
                : `No ${selectedStatus} roadmaps found`
            }
            action={
              selectedStatus === 'all'
                ? {
                    label: 'Create First Roadmap',
                    onClick: () => console.log('Create roadmap'),
                  }
                : undefined
            }
          />
        ) : (
          <div className="space-y-4">
            {roadmaps.map((roadmap) => (
              <Card key={roadmap.id} className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-semibold">{roadmap.title}</h3>
                    {roadmap.description && (
                      <p className="text-muted-foreground mt-1">{roadmap.description}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="text-right">
                      <div className="text-2xl font-bold text-primary">
                        {Math.round(roadmap.progress_percentage)}%
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {roadmap.completed_milestones}/{roadmap.total_milestones}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={() => {
                      // TODO: View full roadmap
                      console.log('View roadmap:', roadmap.id);
                    }}
                  >
                    View Roadmap
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Quiz Trigger Dialog */}
      <QuizTriggerDialog
        open={quizDialogOpen}
        onOpenChange={setQuizDialogOpen}
        quizData={quizTrigger}
        roadmapId={activeRoadmap?.id}
      />
    </div>
  );
}
