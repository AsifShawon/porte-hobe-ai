import React from "react";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Construction } from "lucide-react";
import Link from "next/link";
import { SidebarTrigger } from "@/components/ui/sidebar";

interface PlaceholderPageProps {
  title: string;
  description: string;
  icon?: React.ComponentType<{ className?: string }>;
  backLink?: string;
}

export function PlaceholderPage({
  title,
  description,
  icon: Icon = Construction,
  backLink = "/dashboard",
}: PlaceholderPageProps) {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <SidebarTrigger className="-ml-1 lg:hidden" />
        <div className="flex-1">
          <h1 className="text-3xl font-bold">{title}</h1>
          <p className="text-sm text-muted-foreground mt-1">{description}</p>
        </div>
      </div>

      <div className="bg-card text-card-foreground rounded-lg border p-12 shadow-sm">
        <div className="flex flex-col items-center justify-center text-center space-y-6">
          <div className="rounded-full bg-muted p-6">
            <Icon className="h-12 w-12 text-muted-foreground" />
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl font-semibold">Coming Soon!</h2>
            <p className="text-muted-foreground max-w-md">
              This feature is currently under development. Check back soon for updates!
            </p>
          </div>
          <Button asChild variant="outline">
            <Link href={backLink}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Dashboard
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
