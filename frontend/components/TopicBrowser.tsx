"use client";

import React, { useEffect, useState } from 'react';
import { 
  Search, 
  Filter, 
  Lock, 
  Clock, 
  Target, 
  BookOpen,
  Play,
  CheckCircle,
  Circle,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface Topic {
  id: string;
  title: string;
  description: string;
  category: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  prerequisites: string[];
  estimated_hours: number;
  learning_objectives: string[];
  content_structure?: {
    lessons: Array<{
      title: string;
      duration: string;
      topics: string[];
    }>;
  };
  is_active: boolean;
  progress?: number; // 0-100
  is_locked?: boolean;
  is_started?: boolean;
}

interface TopicBrowserProps {
  onTopicSelect?: (topicId: string) => void;
  className?: string;
}

const CATEGORIES = [
  { id: 'all', label: 'All Topics', icon: '📚' },
  { id: 'programming', label: 'Programming', icon: '💻' },
  { id: 'mathematics', label: 'Mathematics', icon: '🔢' },
  { id: 'science', label: 'Science', icon: '🔬' },
  { id: 'language', label: 'Language', icon: '🗣️' },
  { id: 'business', label: 'Business', icon: '💼' },
];

const DIFFICULTY_LEVELS = [
  { id: 'all', label: 'All Levels' },
  { id: 'beginner', label: 'Beginner', color: 'text-green-600 bg-green-50 dark:bg-green-900/20' },
  { id: 'intermediate', label: 'Intermediate', color: 'text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20' },
  { id: 'advanced', label: 'Advanced', color: 'text-red-600 bg-red-50 dark:bg-red-900/20' },
];

export default function TopicBrowser({ onTopicSelect, className }: TopicBrowserProps) {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [filteredTopics, setFilteredTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedDifficulty, setSelectedDifficulty] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [expandedTopics, setExpandedTopics] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchTopics();
  }, []);

  useEffect(() => {
    let filtered = [...topics];

    // Category filter
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(t => t.category === selectedCategory);
    }

    // Difficulty filter
    if (selectedDifficulty !== 'all') {
      filtered = filtered.filter(t => t.difficulty === selectedDifficulty);
    }

    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(t =>
        t.title.toLowerCase().includes(query) ||
        t.description.toLowerCase().includes(query) ||
        t.learning_objectives?.some(obj => obj.toLowerCase().includes(query))
      );
    }

    setFilteredTopics(filtered);
  }, [topics, selectedCategory, selectedDifficulty, searchQuery]);

  const fetchTopics = async () => {
    setLoading(true);
    setError(null);
    try {
      const { createSupabaseBrowserClient } = await import('@/lib/supabaseClient');
      const supabase = createSupabaseBrowserClient();
      const { data: { session } } = await supabase.auth.getSession();

      const headers: Record<string, string> = {};
      if (session?.access_token) {
        headers['Authorization'] = `Bearer ${session.access_token}`;
      }

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/topics`, {
        method: 'GET',
        headers,
      });

      if (!res.ok) {
        throw new Error(`Failed to fetch topics: ${res.status}`);
      }

      const data = await res.json();
      // Assume API returns an array or an object with `topics` key
      setTopics(data?.topics ?? data ?? []);
      setLoading(false);
    } catch (err: unknown) {
      console.error('Error fetching topics:', err);
      setError(err instanceof Error ? err.message : String(err) || 'Failed to load topics');
      setLoading(false);
    }
  };

  const handleStartTopic = async (topicId: string) => {
    try {
      const { createSupabaseBrowserClient } = await import('@/lib/supabaseClient');
      const supabase = createSupabaseBrowserClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session?.access_token) return;

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/topics/${topicId}/start`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        // Refresh topics to update status
        await fetchTopics();
        
        // Notify parent
        if (onTopicSelect) {
          onTopicSelect(topicId);
        }
      } else {
        console.error('Failed to start topic:', await response.text());
      }
    } catch (err) {
      console.error('Error starting topic:', err);
    }
  };

  const toggleExpand = (topicId: string) => {
    setExpandedTopics(prev => {
      const next = new Set(prev);
      if (next.has(topicId)) {
        next.delete(topicId);
      } else {
        next.add(topicId);
      }
      return next;
    });
  };

  const getDifficultyStyle = (difficulty: string) => {
    const level = DIFFICULTY_LEVELS.find(d => d.id === difficulty);
    return level?.color || 'text-gray-600 bg-gray-50 dark:bg-gray-900/20';
  };

  if (loading) {
    return (
      <div className={cn("bg-white dark:bg-gray-900 rounded-lg border p-6", className)}>
        <div className="animate-pulse space-y-4">
          <div className="h-12 bg-gray-200 dark:bg-gray-800 rounded"></div>
          <div className="h-10 bg-gray-200 dark:bg-gray-800 rounded"></div>
          {[1, 2, 3].map(i => (
            <div key={i} className="h-40 bg-gray-200 dark:bg-gray-800 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn("bg-white dark:bg-gray-900 rounded-lg border p-6", className)}>
        <p className="text-red-500">{error}</p>
        <button
          onClick={fetchTopics}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className={cn("bg-white dark:bg-gray-900 rounded-lg border", className)}>
      {/* Header */}
      <div className="p-6 border-b">
        <h2 className="text-2xl font-bold mb-4">Browse Topics</h2>
        
        {/* Search Bar */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search topics, objectives..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-700"
          />
        </div>

        {/* Filter Toggle */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
        >
          <Filter className="w-4 h-4" />
          {showFilters ? 'Hide Filters' : 'Show Filters'}
          {showFilters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {/* Filters */}
        {showFilters && (
          <div className="mt-4 space-y-4">
            {/* Category Filter */}
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                Category
              </label>
              <div className="flex flex-wrap gap-2">
                {CATEGORIES.map(cat => (
                  <button
                    key={cat.id}
                    onClick={() => setSelectedCategory(cat.id)}
                    className={cn(
                      "px-4 py-2 rounded-lg text-sm font-medium transition",
                      selectedCategory === cat.id
                        ? "bg-blue-600 text-white"
                        : "bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700"
                    )}
                  >
                    <span className="mr-1">{cat.icon}</span>
                    {cat.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Difficulty Filter */}
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                Difficulty
              </label>
              <div className="flex flex-wrap gap-2">
                {DIFFICULTY_LEVELS.map(level => (
                  <button
                    key={level.id}
                    onClick={() => setSelectedDifficulty(level.id)}
                    className={cn(
                      "px-4 py-2 rounded-lg text-sm font-medium transition",
                      selectedDifficulty === level.id
                        ? "bg-blue-600 text-white"
                        : "bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700"
                    )}
                  >
                    {level.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Topics List */}
      <div className="p-6 space-y-4">
        {filteredTopics.length === 0 ? (
          <div className="text-center py-12">
            <BookOpen className="w-16 h-16 text-gray-300 dark:text-gray-700 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400">No topics found</p>
          </div>
        ) : (
          filteredTopics.map(topic => (
            <div
              key={topic.id}
              className={cn(
                "border rounded-lg p-5 transition-all hover:shadow-md",
                topic.is_locked ? "opacity-60 bg-gray-50 dark:bg-gray-800/50" : "bg-white dark:bg-gray-800"
              )}
            >
              {/* Topic Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      {topic.title}
                    </h3>
                    <span className={cn("px-2 py-1 rounded text-xs font-medium", getDifficultyStyle(topic.difficulty))}>
                      {topic.difficulty}
                    </span>
                    {topic.is_locked && (
                      <Lock className="w-4 h-4 text-gray-400" />
                    )}
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    {topic.description}
                  </p>
                </div>
              </div>

              {/* Topic Metadata */}
              <div className="flex items-center gap-4 mb-3 text-sm text-gray-500 dark:text-gray-400">
                <div className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  <span>{topic.estimated_hours}h</span>
                </div>
                <div className="flex items-center gap-1">
                  <Target className="w-4 h-4" />
                  <span>{topic.learning_objectives?.length || 0} objectives</span>
                </div>
                {topic.content_structure?.lessons && (
                  <div className="flex items-center gap-1">
                    <BookOpen className="w-4 h-4" />
                    <span>{topic.content_structure.lessons.length} lessons</span>
                  </div>
                )}
              </div>

              {/* Progress Bar (if started) */}
              {topic.is_started && topic.progress !== undefined && (
                <div className="mb-3">
                  <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                    <span>Progress</span>
                    <span>{topic.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all"
                      style={{ width: `${topic.progress}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Expandable Section */}
              {expandedTopics.has(topic.id) && (
                <div className="mt-4 pt-4 border-t space-y-3">
                  {/* Learning Objectives */}
                  {topic.learning_objectives && topic.learning_objectives.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                        Learning Objectives:
                      </h4>
                      <ul className="space-y-1">
                        {topic.learning_objectives.map((obj, idx) => (
                          <li key={idx} className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-2">
                            <Circle className="w-3 h-3 mt-1 flex-shrink-0" />
                            <span>{obj}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Prerequisites */}
                  {topic.prerequisites && topic.prerequisites.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                        Prerequisites:
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {topic.prerequisites.map((prereq, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 text-xs rounded"
                          >
                            {prereq}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Lessons */}
                  {topic.content_structure?.lessons && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                        Course Outline:
                      </h4>
                      <div className="space-y-2">
                        {topic.content_structure.lessons.map((lesson, idx) => (
                          <div key={idx} className="text-sm bg-gray-50 dark:bg-gray-700/50 rounded p-2">
                            <div className="font-medium text-gray-900 dark:text-white">
                              Lesson {idx + 1}: {lesson.title}
                            </div>
                            <div className="text-gray-500 dark:text-gray-400 text-xs">
                              {lesson.duration} • {lesson.topics.join(', ')}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex items-center gap-3 mt-4">
                <button
                  onClick={() => !topic.is_locked && handleStartTopic(topic.id)}
                  disabled={topic.is_locked}
                  className={cn(
                    "px-4 py-2 rounded-lg font-medium transition flex items-center gap-2",
                    topic.is_locked
                      ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                      : topic.is_started
                      ? "bg-blue-600 text-white hover:bg-blue-700"
                      : "bg-green-600 text-white hover:bg-green-700"
                  )}
                >
                  {topic.is_locked ? (
                    <>
                      <Lock className="w-4 h-4" />
                      Locked
                    </>
                  ) : topic.is_started ? (
                    <>
                      <Play className="w-4 h-4" />
                      Resume
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      Start
                    </>
                  )}
                </button>

                <button
                  onClick={() => toggleExpand(topic.id)}
                  className="px-4 py-2 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition text-sm"
                >
                  {expandedTopics.has(topic.id) ? 'Show Less' : 'Show More'}
                </button>

                {topic.progress === 100 && (
                  <div className="ml-auto flex items-center gap-1 text-green-600 dark:text-green-400 text-sm font-medium">
                    <CheckCircle className="w-4 h-4" />
                    Completed
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
