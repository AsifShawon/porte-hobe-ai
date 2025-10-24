"use client";

import React, { useEffect, useRef, useState } from 'react';
import DOMPurify from 'dompurify';
import { AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface VisualizerProps {
  html: string;
  className?: string;
  onError?: (error: Error) => void;
}

export default function Visualizer({ html, className, onError }: VisualizerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [sanitizedHTML, setSanitizedHTML] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      if (!html) {
        setSanitizedHTML('');
        return;
      }

      // Configure DOMPurify
      const config = {
        ALLOWED_TAGS: [
          'div', 'span', 'p', 'br', 'strong', 'em', 'u', 's',
          'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
          'ul', 'ol', 'li',
          'a', 'img',
          'table', 'thead', 'tbody', 'tr', 'th', 'td',
          'code', 'pre',
          'blockquote',
          'hr',
          'sub', 'sup',
          'mark',
          'details', 'summary',
        ],
        ALLOWED_ATTR: [
          'class', 'id', 'style',
          'href', 'target', 'rel',
          'src', 'alt', 'width', 'height',
          'title',
          'data-*',
        ],
        ALLOWED_URI_REGEXP: /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|cid|xmpp|data):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i,
        ALLOW_DATA_ATTR: true,
        ADD_TAGS: ['iframe'], // For embedded content (carefully controlled)
        ADD_ATTR: ['allow', 'allowfullscreen', 'frameborder', 'scrolling'],
      };

      // Sanitize the HTML
      const clean = DOMPurify.sanitize(html, config);
      setSanitizedHTML(clean);
      setError(null);

    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to sanitize HTML');
      setError(error.message);
      onError?.(error);
      console.error('Visualization error:', error);
    }
  }, [html, onError]);

  // Apply syntax highlighting after render
  useEffect(() => {
    if (!containerRef.current || !sanitizedHTML) return;

    // Find all code blocks
    const codeBlocks = containerRef.current.querySelectorAll('pre code');
    
    // Simple syntax highlighting (you can enhance this with highlight.js or prism.js)
    codeBlocks.forEach((block) => {
      const code = block.textContent || '';
      
      // Basic keyword highlighting
      const keywords = /\b(function|const|let|var|if|else|for|while|return|class|import|export|async|await|try|catch)\b/g;
      const strings = /(["'`])(?:(?=(\\?))\2.)*?\1/g;
      const comments = /\/\/.*$/gm;
      
      let highlighted = code
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
      
      highlighted = highlighted
        .replace(keywords, '<span class="text-purple-600 dark:text-purple-400">$&</span>')
        .replace(strings, '<span class="text-green-600 dark:text-green-400">$&</span>')
        .replace(comments, '<span class="text-gray-500 dark:text-gray-400">$&</span>');
      
      block.innerHTML = highlighted;
    });

    // Find all math expressions (if any)
    const mathElements = containerRef.current.querySelectorAll('[data-math]');
    mathElements.forEach((element) => {
      // You can integrate KaTeX or MathJax here
      element.classList.add('math-expression');
    });

  }, [sanitizedHTML]);

  if (error) {
    return (
      <div className={cn("border border-red-300 bg-red-50 dark:bg-red-900/20 rounded-lg p-4", className)}>
        <div className="flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-medium text-red-900 dark:text-red-100">
              Failed to render content
            </h4>
            <p className="text-sm text-red-700 dark:text-red-300 mt-1">
              {error}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!sanitizedHTML) {
    return null;
  }

  return (
    <div
      ref={containerRef}
      className={cn(
        "prose prose-slate dark:prose-invert max-w-none",
        "prose-headings:scroll-mt-20",
        "prose-a:text-blue-600 dark:prose-a:text-blue-400",
        "prose-code:text-sm prose-code:bg-gray-100 dark:prose-code:bg-gray-800",
        "prose-code:px-1 prose-code:py-0.5 prose-code:rounded",
        "prose-pre:bg-gray-900 dark:prose-pre:bg-gray-950",
        "prose-pre:border prose-pre:border-gray-700",
        "prose-img:rounded-lg prose-img:shadow-md",
        "prose-table:border prose-table:border-gray-300 dark:prose-table:border-gray-700",
        className
      )}
      dangerouslySetInnerHTML={{ __html: sanitizedHTML }}
    />
  );
}

// Optional: Export a hook for using the visualizer programmatically
export function useSanitizedHTML(html: string) {
  const [sanitized, setSanitized] = useState<string>('');

  useEffect(() => {
    if (!html) {
      setSanitized('');
      return;
    }

    const config = {
      ALLOWED_TAGS: [
        'div', 'span', 'p', 'br', 'strong', 'em', 'u',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li',
        'a', 'img',
        'code', 'pre',
      ],
      ALLOWED_ATTR: ['class', 'href', 'src', 'alt', 'title'],
    };

    const clean = DOMPurify.sanitize(html, config);
    setSanitized(clean);
  }, [html]);

  return sanitized;
}
