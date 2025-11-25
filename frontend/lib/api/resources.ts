/**
 * Resources API Client
 * Functions for interacting with resources endpoints
 */

import { apiClient } from './client';
import type {
  Resource,
  CreateNoteRequest,
  CreateBookmarkRequest,
  UpdateResourceRequest,
  ResourceFolder,
  CreateFolderRequest,
  ResourceStats,
  ResourceFilters,
} from '@/types';

export const resourcesApi = {
  /**
   * Get all resources with optional filters
   */
  async getAll(filters?: ResourceFilters, limit: number = 50): Promise<Resource[]> {
    const params: Record<string, string> = { limit: String(limit) };
    if (filters?.resource_type) params.resource_type = filters.resource_type;
    if (filters?.category) params.category = filters.category;
    if (filters?.topic_id) params.topic_id = filters.topic_id;
    if (filters?.is_favorite !== undefined) params.is_favorite = String(filters.is_favorite);
    if (filters?.tag) params.tag = filters.tag;
    if (filters?.search) params.search = filters.search;

    return apiClient.get<Resource[]>('/api/resources', params);
  },

  /**
   * Get a specific resource by ID
   */
  async getById(id: string): Promise<Resource> {
    return apiClient.get<Resource>(`/api/resources/${id}`);
  },

  /**
   * Create a new note
   */
  async createNote(data: CreateNoteRequest): Promise<Resource> {
    return apiClient.post<Resource>('/api/resources/notes', data);
  },

  /**
   * Create a new bookmark
   */
  async createBookmark(data: CreateBookmarkRequest): Promise<Resource> {
    return apiClient.post<Resource>('/api/resources/bookmarks', data);
  },

  /**
   * Update a resource
   */
  async update(id: string, data: UpdateResourceRequest): Promise<Resource> {
    return apiClient.patch<Resource>(`/api/resources/${id}`, data);
  },

  /**
   * Delete a resource
   */
  async delete(id: string): Promise<{ message: string; resource_id: string }> {
    return apiClient.delete(`/api/resources/${id}`);
  },

  /**
   * Get all folders
   */
  async getFolders(): Promise<ResourceFolder[]> {
    return apiClient.get<ResourceFolder[]>('/api/resources/folders/all');
  },

  /**
   * Create a new folder
   */
  async createFolder(data: CreateFolderRequest): Promise<ResourceFolder> {
    return apiClient.post<ResourceFolder>('/api/resources/folders', data);
  },

  /**
   * Get resource statistics
   */
  async getStats(): Promise<ResourceStats> {
    return apiClient.get<ResourceStats>('/api/resources/stats/summary');
  },
};
