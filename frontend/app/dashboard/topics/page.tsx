"use client";

import TopicBrowser from '@/components/TopicBrowser';
import { useRouter } from 'next/navigation';

export default function TopicsPage() {
  const router = useRouter();

  const handleTopicSelect = (topicId: string) => {
    // Navigate to chat page with topic context
    router.push(`/dashboard/chat?topic=${topicId}`);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Learning Topics
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Explore and start learning from our curated topics
        </p>
      </div>

      <TopicBrowser onTopicSelect={handleTopicSelect} />
    </div>
  );
}
