"use client";

import React, { useState, useCallback, useRef } from 'react';
import { Upload, X, FileText, Image as ImageIcon, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface FileUpload {
  id: string;
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'processing' | 'success' | 'error';
  uploadId?: string;
  error?: string;
  preview?: string;
}

interface FileDropProps {
  onFilesUploaded: (uploadIds: string[]) => void;
  maxFiles?: number;
  maxSizeMB?: number;
  className?: string;
}

const ALLOWED_TYPES = {
  'application/pdf': ['.pdf'],
  'image/png': ['.png'],
  'image/jpeg': ['.jpg', '.jpeg'],
};

export default function FileDrop({
  onFilesUploaded,
  maxFiles = 5,
  maxSizeMB = 10,
  className
}: FileDropProps) {
  const [files, setFiles] = useState<FileUpload[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Validate file
  const validateFile = (file: File): string | null => {
    // Check file type
    if (!Object.keys(ALLOWED_TYPES).includes(file.type)) {
      return `Invalid file type. Only PDF, PNG, and JPG files are allowed.`;
    }

    // Check file size
    if (file.size > maxSizeMB * 1024 * 1024) {
      return `File size exceeds ${maxSizeMB}MB limit.`;
    }

    return null;
  };

  // Generate preview for images
  const generatePreview = (file: File): Promise<string | undefined> => {
    return new Promise((resolve) => {
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result as string);
        reader.onerror = () => resolve(undefined);
        reader.readAsDataURL(file);
      } else {
        resolve(undefined);
      }
    });
  };

  // Upload file to backend
  const uploadFile = async (fileUpload: FileUpload) => {
    const formData = new FormData();
    formData.append('file', fileUpload.file);

    try {
      // Get auth token from Supabase
      const { createSupabaseBrowserClient } = await import('@/lib/supabaseClient');
      const supabase = createSupabaseBrowserClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session?.access_token) {
        throw new Error('Not authenticated');
      }

      // Update status to uploading
      setFiles(prev => prev.map(f =>
        f.id === fileUpload.id ? { ...f, status: 'uploading', progress: 0 } : f
      ));

      // Upload to backend
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }

      const result = await response.json();

      // Update status to processing
      setFiles(prev => prev.map(f =>
        f.id === fileUpload.id ? { ...f, status: 'processing', progress: 75 } : f
      ));

      // Wait a bit for processing
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Update status to success
      setFiles(prev => prev.map(f =>
        f.id === fileUpload.id ? {
          ...f,
          status: 'success',
          progress: 100,
          uploadId: result.id
        } : f
      ));

      return result.id;

    } catch (error) {
      console.error('Upload error:', error);
      setFiles(prev => prev.map(f =>
        f.id === fileUpload.id ? {
          ...f,
          status: 'error',
          error: error instanceof Error ? error.message : 'Upload failed'
        } : f
      ));
      return null;
    }
  };

  // Handle file selection
  const handleFiles = async (selectedFiles: FileList | null) => {
    if (!selectedFiles) return;

    const fileArray = Array.from(selectedFiles);

    // Check max files limit
    if (files.length + fileArray.length > maxFiles) {
      alert(`You can only upload up to ${maxFiles} files at a time.`);
      return;
    }

    // Validate and create file upload objects
    const newFileUploads: FileUpload[] = [];

    for (const file of fileArray) {
      const error = validateFile(file);
      const preview = await generatePreview(file);

      newFileUploads.push({
        id: `${Date.now()}-${Math.random()}`,
        file,
        progress: 0,
        status: error ? 'error' : 'pending',
        error: error || undefined,
        preview,
      });
    }

    setFiles(prev => [...prev, ...newFileUploads]);

    // Upload valid files
    const validFiles = newFileUploads.filter(f => f.status === 'pending');
    const uploadPromises = validFiles.map(uploadFile);
    const uploadIds = (await Promise.all(uploadPromises)).filter(Boolean) as string[];

    // Notify parent of successful uploads
    if (uploadIds.length > 0) {
      onFilesUploaded(uploadIds);
    }
  };

  // Drag and drop handlers
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    const selectedFiles = e.dataTransfer.files;
    if (!selectedFiles) return;

    const fileArray = Array.from(selectedFiles);

    // Check max files limit inline to avoid circular dependency
    if (files.length + fileArray.length > maxFiles) {
      alert(`You can only upload up to ${maxFiles} files at a time.`);
      return;
    }

    // Validate and create file upload objects inline
    (async () => {
      const newFileUploads: FileUpload[] = [];

      for (const file of fileArray) {
        const error = validateFile(file);
        const preview = await generatePreview(file);

        newFileUploads.push({
          id: `${Date.now()}-${Math.random()}`,
          file,
          progress: 0,
          status: error ? 'error' : 'pending',
          error: error || undefined,
          preview,
        });
      }

      setFiles(prev => [...prev, ...newFileUploads]);

      // Upload valid files
      const validFiles = newFileUploads.filter(f => f.status === 'pending');
      const uploadPromises = validFiles.map(uploadFile);
      const uploadIds = (await Promise.all(uploadPromises)).filter(Boolean) as string[];

      // Notify parent of successful uploads
      if (uploadIds.length > 0) {
        onFilesUploaded(uploadIds);
      }
    })();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [files.length, maxFiles]);

  // Remove file
  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  };

  // Get file icon
  const getFileIcon = (file: File) => {
    if (file.type === 'application/pdf') {
      return <FileText className="w-8 h-8 text-red-500" />;
    }
    if (file.type.startsWith('image/')) {
      return <ImageIcon className="w-8 h-8 text-blue-500" />;
    }
    return <FileText className="w-8 h-8 text-gray-500" />;
  };

  // Get status icon
  const getStatusIcon = (status: FileUpload['status']) => {
    switch (status) {
      case 'uploading':
      case 'processing':
        return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />;
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };

  return (
    <div className={cn("space-y-4", className)}>
      {/* Drop Zone */}
      <div
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={cn(
          "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
          isDragging
            ? "border-primary bg-primary/5"
            : "border-gray-300 hover:border-primary/50 hover:bg-gray-50 dark:hover:bg-gray-900"
        )}
      >
        <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        <p className="text-lg font-medium mb-2">
          {isDragging ? "Drop files here" : "Drag & drop files here"}
        </p>
        <p className="text-sm text-gray-500 mb-4">
          or click to browse
        </p>
        <p className="text-xs text-gray-400">
          PDF, PNG, JPG up to {maxSizeMB}MB • Max {maxFiles} files
        </p>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.png,.jpg,.jpeg"
          onChange={(e) => handleFiles(e.target.files)}
          className="hidden"
        />
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((fileUpload) => (
            <div
              key={fileUpload.id}
              className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg border"
            >
              {/* File Icon/Preview */}
              <div className="flex-shrink-0">
                {fileUpload.preview ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={fileUpload.preview}
                    alt={fileUpload.file.name}
                    className="w-12 h-12 object-cover rounded"
                  />
                ) : (
                  getFileIcon(fileUpload.file)
                )}
              </div>

              {/* File Info */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {fileUpload.file.name}
                </p>
                <p className="text-xs text-gray-500">
                  {(fileUpload.file.size / 1024 / 1024).toFixed(2)} MB
                </p>

                {/* Progress Bar */}
                {(fileUpload.status === 'uploading' || fileUpload.status === 'processing') && (
                  <div className="mt-2">
                    <div className="w-full bg-gray-200 rounded-full h-1.5 dark:bg-gray-700">
                      <div
                        className="bg-blue-500 h-1.5 rounded-full transition-all"
                        style={{ width: `${fileUpload.progress}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {fileUpload.status === 'uploading' ? 'Uploading...' : 'Processing...'}
                    </p>
                  </div>
                )}

                {/* Error Message */}
                {fileUpload.status === 'error' && (
                  <p className="text-xs text-red-500 mt-1">
                    {fileUpload.error}
                  </p>
                )}
              </div>

              {/* Status Icon */}
              <div className="flex-shrink-0">
                {getStatusIcon(fileUpload.status)}
              </div>

              {/* Remove Button */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => removeFile(fileUpload.id)}
                className="flex-shrink-0"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
