/**
 * Resources Data Fetching Hook
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { resourcesApi } from '@/lib/api';
import type {
  Resource,
  ResourceFilters,
  ResourceStats,
  CreateNoteRequest,
  CreateBookmarkRequest,
  UpdateResourceRequest,
  ResourceFolder,
  CreateFolderRequest,
  ApiError,
} from '@/types';

export function useResources(filters?: ResourceFilters, limit: number = 50) {
  const [resources, setResources] = useState<Resource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchResources = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await resourcesApi.getAll(filters, limit);
      setResources(data);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setLoading(false);
    }
  }, [filters, limit]);

  useEffect(() => {
    fetchResources();
  }, [fetchResources]);

  const createNote = async (data: CreateNoteRequest) => {
    const newResource = await resourcesApi.createNote(data);
    setResources((prev) => [newResource, ...prev]);
    return newResource;
  };

  const createBookmark = async (data: CreateBookmarkRequest) => {
    const newResource = await resourcesApi.createBookmark(data);
    setResources((prev) => [newResource, ...prev]);
    return newResource;
  };

  const updateResource = async (id: string, data: UpdateResourceRequest) => {
    const updated = await resourcesApi.update(id, data);
    setResources((prev) => prev.map((r) => (r.id === id ? updated : r)));
    return updated;
  };

  const deleteResource = async (id: string) => {
    await resourcesApi.delete(id);
    setResources((prev) => prev.filter((r) => r.id !== id));
  };

  return {
    resources,
    loading,
    error,
    refetch: fetchResources,
    createNote,
    createBookmark,
    updateResource,
    deleteResource,
  };
}

export function useResourceFolders() {
  const [folders, setFolders] = useState<ResourceFolder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchFolders = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await resourcesApi.getFolders();
      setFolders(data);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFolders();
  }, [fetchFolders]);

  const createFolder = async (data: CreateFolderRequest) => {
    const newFolder = await resourcesApi.createFolder(data);
    setFolders((prev) => [...prev, newFolder]);
    return newFolder;
  };

  return {
    folders,
    loading,
    error,
    refetch: fetchFolders,
    createFolder,
  };
}

export function useResourceStats() {
  const [stats, setStats] = useState<ResourceStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await resourcesApi.getStats();
      setStats(data);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return { stats, loading, error, refetch: fetchStats };
}
