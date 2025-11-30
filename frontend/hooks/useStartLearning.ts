/**
 * useStartLearning Hook
 * Handles starting a learning milestone from a roadmap
 * Calls the backend /start-learning endpoint and navigates to chat
 */

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/auth-provider';

interface StartLearningParams {
  roadmapId: string;
  phaseId: string;
  milestoneId: string;
}

interface StartLearningResponse {
  status: string;
  message: string;
  navigation: {
    session_id: string;
    conversation_id: string;
    contextual_prompt: string;
    chat_url: string;
  };
  milestone: {
    roadmap_id: string;
    phase_id: string;
    milestone_id: string;
    title: string;
    type: string;
    description: string;
  };
}

export function useStartLearning() {
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const { session } = useAuth();

  const startLearning = async ({ roadmapId, phaseId, milestoneId }: StartLearningParams) => {
    if (!session) {
      setError('You must be logged in to start learning');
      return null;
    }

    setIsStarting(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/roadmaps/${roadmapId}/milestone/${phaseId}/${milestoneId}/start-learning`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${session.access_token}`,
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to start learning: ${response.statusText}`);
      }

      const data: StartLearningResponse = await response.json();

      // Navigate to chat with contextual prompt
      const chatUrl = `/dashboard/chat?conversation_id=${data.navigation.conversation_id}&auto_start=true&contextual_prompt=${encodeURIComponent(data.navigation.contextual_prompt)}`;
      
      router.push(chatUrl);

      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      console.error('Start learning error:', err);
      return null;
    } finally {
      setIsStarting(false);
    }
  };

  return {
    startLearning,
    isStarting,
    error,
  };
}
