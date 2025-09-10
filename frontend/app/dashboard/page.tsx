import React from "react";
import { Button } from "@/components/ui/button";
import { BookOpen, TrendingUp, Calendar, CheckCircle } from "lucide-react";
import { SidebarTrigger } from "@/components/ui/sidebar";

export default function DashboardPage() {
  // Placeholder data for the logged-in user - will be replaced with Supabase data later
  const userStats = {
    myLessons: 12,
    myProgress: 75, // percentage
    completedTasks: 89,
    upcomingSessions: 5,
  };

  const recentActivities = [
    { id: 1, action: "Completed lesson: Algebra Basics", time: "2 hours ago" },
    { id: 2, action: "Submitted assignment", time: "4 hours ago" },
    { id: 3, action: "Achieved milestone: 80% progress", time: "1 day ago" },
  ];

  return (
    <div className="space-y-8">
      <div>
        <div className="mb-2 flex items-center space-x-4">
          <SidebarTrigger className="-ml-1 lg:hidden" />
          <h1 className="text-3xl font-bold">My Learning Dashboard</h1>
        </div>
        <p className="text-muted-foreground">
          Track your progress in one-to-one tutoring
        </p>
      </div>

      {/* Personal Stats Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <div className="bg-card text-card-foreground rounded-lg border p-8 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                My Lessons
              </p>
              <p className="text-3xl font-bold">{userStats.myLessons}</p>
              <p className="text-xs text-muted-foreground">Enrolled courses</p>
            </div>
            <BookOpen className="h-10 w-10 text-muted-foreground" />
          </div>
        </div>

        <div className="bg-card text-card-foreground rounded-lg border p-8 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                My Progress
              </p>
              <p className="text-3xl font-bold">{userStats.myProgress}%</p>
              <p className="text-xs text-muted-foreground">
                Overall completion
              </p>
            </div>
            <TrendingUp className="h-10 w-10 text-muted-foreground" />
          </div>
        </div>

        <div className="bg-card text-card-foreground rounded-lg border p-8 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                Completed Tasks
              </p>
              <p className="text-3xl font-bold">{userStats.completedTasks}</p>
              <p className="text-xs text-muted-foreground">Assignments done</p>
            </div>
            <CheckCircle className="h-10 w-10 text-muted-foreground" />
          </div>
        </div>

        <div className="bg-card text-card-foreground rounded-lg border p-8 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                Upcoming Sessions
              </p>
              <p className="text-3xl font-bold">{userStats.upcomingSessions}</p>
              <p className="text-xs text-muted-foreground">Next in 2 hours</p>
            </div>
            <Calendar className="h-10 w-10 text-muted-foreground" />
          </div>
        </div>
      </div>

      {/* Recent Activities */}
      <div className="bg-card text-card-foreground rounded-lg border p-8 shadow-sm">
        <div className="mb-6">
          <h3 className="text-xl font-semibold">Recent Activities</h3>
          <p className="text-sm text-muted-foreground">
            Your latest learning milestones
          </p>
        </div>
        <div className="space-y-6">
          {recentActivities.map((activity) => (
            <div
              key={activity.id}
              className="flex items-center justify-between py-2"
            >
              <div>
                <p className="text-sm font-medium">{activity.action}</p>
                <p className="text-xs text-muted-foreground">{activity.time}</p>
              </div>
              <Button variant="ghost" size="sm">
                View
              </Button>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-card text-card-foreground rounded-lg border p-8 shadow-sm">
        <div className="mb-6">
          <h3 className="text-xl font-semibold">Quick Actions</h3>
          <p className="text-sm text-muted-foreground">
            Continue your learning journey
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Button className="justify-start">
            <BookOpen className="mr-2 h-4 w-4" />
            Start Next Lesson
          </Button>
          <Button variant="outline" className="justify-start">
            <CheckCircle className="mr-2 h-4 w-4" />
            View Assignments
          </Button>
          <Button variant="outline" className="justify-start">
            <TrendingUp className="mr-2 h-4 w-4" />
            Check Progress
          </Button>
          <Button variant="outline" className="justify-start">
            <Calendar className="mr-2 h-4 w-4" />
            Schedule Session
          </Button>
        </div>
      </div>
    </div>
  );
}
