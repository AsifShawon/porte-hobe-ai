/**
 * Resource Type Definitions
 * Matches backend resource_router.py models
 */

export type ResourceType = 'note' | 'bookmark' | 'snippet' | 'file' | 'reference';

export type ResourceCategory =
  | 'programming'
  | 'math'
  | 'general'
  | 'tutorial'
  | 'documentation'
  | 'example';

export interface Resource {
  id: string;
  user_id: string;
  resource_type: ResourceType;
  title: string;
  content?: string;
  url?: string;
  topic_id?: string;
  topic_title?: string;
  category: ResourceCategory;
  tags: string[];
  is_favorite: boolean;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface CreateNoteRequest {
  title: string;
  content: string;
  topic_id?: string;
  category?: ResourceCategory;
  tags?: string[];
  is_favorite?: boolean;
  metadata?: Record<string, any>;
}

export interface CreateBookmarkRequest {
  title: string;
  url: string;
  description?: string;
  topic_id?: string;
  category?: ResourceCategory;
  tags?: string[];
  is_favorite?: boolean;
  metadata?: Record<string, any>;
}

export interface UpdateResourceRequest {
  title?: string;
  content?: string;
  topic_id?: string;
  category?: ResourceCategory;
  tags?: string[];
  is_favorite?: boolean;
  metadata?: Record<string, any>;
}

export interface ResourceFolder {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  parent_id?: string;
  color?: string;
  resource_count: number;
  created_at: string;
  updated_at: string;
}

export interface CreateFolderRequest {
  name: string;
  description?: string;
  parent_id?: string;
  color?: string;
}

export interface ResourceStats {
  total_resources: number;
  notes_count: number;
  bookmarks_count: number;
  snippets_count: number;
  files_count: number;
  favorites_count: number;
  total_folders: number;
  resources_by_category: Record<ResourceCategory, number>;
  recent_resources: Resource[];
}
