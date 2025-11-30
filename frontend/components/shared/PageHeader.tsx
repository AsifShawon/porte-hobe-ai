/**
 * PageHeader Component
 * Consistent header for all pages
 */

import React from 'react';
import { LucideIcon } from 'lucide-react';
import { SidebarTrigger } from '@/components/ui/sidebar';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface PageHeaderProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
  action?: {
    label: string;
    onClick: () => void;
    icon?: LucideIcon;
  };
  className?: string;
}

export function PageHeader({
  title,
  description,
  icon: Icon,
  action,
  className,
}: PageHeaderProps) {
  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <SidebarTrigger className="-ml-1 lg:hidden" />
          <div className="flex items-center gap-3">
            {Icon && (
              <div className="rounded-lg bg-primary/10 p-2">
                <Icon className="h-6 w-6 text-primary" />
              </div>
            )}
            <div>
              <h1 className="text-3xl font-bold">{title}</h1>
              {description && (
                <p className="text-sm text-muted-foreground mt-1">{description}</p>
              )}
            </div>
          </div>
        </div>

        {action && (
          <Button onClick={action.onClick}>
            {action.icon && <action.icon className="mr-2 h-4 w-4" />}
            {action.label}
          </Button>
        )}
      </div>
    </div>
  );
}
