/**
 * ErrorState Component
 * Display API errors with retry option
 */

import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { ApiError } from '@/types';

interface ErrorStateProps {
  error: ApiError | Error | string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({ error, onRetry, className }: ErrorStateProps) {
  const getErrorMessage = () => {
    if (typeof error === 'string') return error;
    if ('detail' in error && error.detail) return error.detail;
    if ('message' in error) return error.message;
    return 'An unexpected error occurred';
  };

  const getErrorTitle = () => {
    if (typeof error === 'object' && 'status' in error) {
      if (error.status === 401) return 'Authentication Required';
      if (error.status === 403) return 'Access Denied';
      if (error.status === 404) return 'Not Found';
      if (error.status >= 500) return 'Server Error';
    }
    return 'Error';
  };

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center text-center p-12 rounded-lg border border-destructive/50 bg-destructive/5',
        className
      )}
    >
      <div className="rounded-full bg-destructive/10 p-6 mb-4">
        <AlertCircle className="h-12 w-12 text-destructive" />
      </div>

      <h3 className="text-lg font-semibold mb-2">{getErrorTitle()}</h3>

      <p className="text-sm text-muted-foreground max-w-md mb-6">
        {getErrorMessage()}
      </p>

      {onRetry && (
        <Button onClick={onRetry} variant="outline">
          <RefreshCw className="mr-2 h-4 w-4" />
          Try Again
        </Button>
      )}
    </div>
  );
}

/**
 * Inline Error Message
 */

export function InlineError({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-2 text-sm text-destructive p-3 rounded-lg bg-destructive/10">
      <AlertCircle className="h-4 w-4 flex-shrink-0" />
      <span>{message}</span>
    </div>
  );
}
