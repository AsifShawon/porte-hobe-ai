import React from "react";
import { Button } from "@/components/ui/button";
import { BookOpen, TrendingUp, CheckCircle, Target, Flame, Trophy, Sparkles, Clock, BarChart3 } from "lucide-react";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { getUser } from "@/lib/supabase/server";
import { redirect } from "next/navigation";
import ProgressCard from "@/components/ProgressCard";
import Link from "next/link";

export default async function DashboardPage() {
  // Fetch the authenticated user
  const user = await getUser()
  
  if (!user) {
    redirect('/login')
  }

  // Placeholder data for the logged-in user - will be replaced with real data from backend
  const userStats = {
    streak: 7,
    overallProgress: 65,
    timeToday: 45, // minutes
    topicsCompleted: 12,
    topicsTotal: 18,
    avgScore: 85.5,
    timeThisMonth: 1470, // minutes (24h 30m)
    currentPath: "Python Fundamentals",
    pathProgress: 60,
    nextTopic: "Data Structures",
  };

  const recentActivities = [
    { id: 1, action: 'Completed "Variables in Python"', time: "2h ago", icon: CheckCircle },
    { id: 2, action: 'Earned badge: "Code Warrior"', time: "5h ago", icon: Trophy },
    { id: 3, action: "Practiced: Loops", time: "1 day ago", icon: Target },
    { id: 4, action: 'Started "Functions & Scope"', time: "2 days ago", icon: BookOpen },
  ];

  const recentBadges = [
    { id: 1, name: "Week Streak", icon: "🔥" },
    { id: 2, name: "Fast Learner", icon: "⚡" },
    { id: 3, name: "Bug Hunter", icon: "🐛" },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Header with Key Metrics */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/20 dark:to-purple-950/20 rounded-lg border p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold">Welcome back!</h1>
            <p className="text-sm text-muted-foreground mt-1">
              {user.email?.split('@')[0] || 'Student'}
            </p>
          </div>
          <SidebarTrigger className="-ml-1 lg:hidden" />
        </div>

        <div className="flex flex-wrap gap-6 text-sm">
          <div className="flex items-center gap-2">
            <Flame className="h-5 w-5 text-orange-500" />
            <span className="font-semibold">{userStats.streak}-day streak</span>
          </div>
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-blue-500" />
            <span className="font-semibold">{userStats.overallProgress}% progress</span>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-green-500" />
            <span className="font-semibold">{userStats.timeToday}m today</span>
          </div>
        </div>
      </div>

      {/* Stats Cards Row */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="bg-card text-card-foreground rounded-lg border p-6 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-muted-foreground">Topics</p>
            <BookOpen className="h-5 w-5 text-muted-foreground" />
          </div>
          <p className="text-2xl font-bold">{userStats.topicsCompleted}/{userStats.topicsTotal} completed</p>
          <div className="mt-2 w-full bg-muted rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all"
              style={{ width: `${(userStats.topicsCompleted / userStats.topicsTotal) * 100}%` }}
            />
          </div>
        </div>

        <div className="bg-card text-card-foreground rounded-lg border p-6 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-muted-foreground">Avg Score</p>
            <TrendingUp className="h-5 w-5 text-muted-foreground" />
          </div>
          <p className="text-2xl font-bold">{userStats.avgScore}%</p>
          <p className="text-xs text-muted-foreground mt-2">👍 Keep going!</p>
        </div>

        <div className="bg-card text-card-foreground rounded-lg border p-6 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-muted-foreground">Time</p>
            <Clock className="h-5 w-5 text-muted-foreground" />
          </div>
          <p className="text-2xl font-bold">{Math.floor(userStats.timeThisMonth / 60)}h {userStats.timeThisMonth % 60}m</p>
          <p className="text-xs text-muted-foreground mt-2">This month</p>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Streak Calendar */}
        <div className="bg-card text-card-foreground rounded-lg border p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Flame className="h-5 w-5 text-orange-500" />
            <h3 className="text-lg font-semibold">Streak</h3>
          </div>
          <p className="text-3xl font-bold mb-2">{userStats.streak} days active</p>
          <p className="text-sm text-muted-foreground mb-4">Keep learning every day to maintain your streak!</p>
          <div className="grid grid-cols-7 gap-1">
            {Array.from({ length: 28 }).map((_, i) => (
              <div
                key={i}
                className={`aspect-square rounded-sm ${
                  i < 21 ? 'bg-green-500' : i < 24 ? 'bg-muted' : 'bg-green-500'
                }`}
                title={`Day ${i + 1}`}
              />
            ))}
          </div>
        </div>

        {/* Current Learning Path */}
        <div className="bg-card text-card-foreground rounded-lg border p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <BookOpen className="h-5 w-5 text-blue-500" />
            <h3 className="text-lg font-semibold">Current Learning Path</h3>
          </div>
          <div className="space-y-3">
            <div>
              <div className="flex items-center justify-between mb-1">
                <p className="font-medium">▶ {userStats.currentPath}</p>
                <span className="text-sm text-muted-foreground">{userStats.pathProgress}%</span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all"
                  style={{ width: `${userStats.pathProgress}%` }}
                />
              </div>
            </div>
            <div className="pt-2 border-t">
              <p className="text-sm text-muted-foreground">Next up:</p>
              <p className="font-medium">▶ {userStats.nextTopic}</p>
            </div>
          </div>
        </div>
      </div>

      {/* AI Learning Progress */}
      <ProgressCard className="w-full" />

      {/* Quick Actions */}
      <div className="bg-card text-card-foreground rounded-lg border p-6 shadow-sm">
        <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Button asChild className="justify-start">
            <Link href="/dashboard/learning/path">
              <BookOpen className="mr-2 h-4 w-4" />
              Continue Learning
            </Link>
          </Button>
          <Button asChild variant="outline" className="justify-start">
            <Link href="/dashboard/practice">
              <Target className="mr-2 h-4 w-4" />
              Practice
            </Link>
          </Button>
          <Button asChild variant="outline" className="justify-start">
            <Link href="/dashboard/chat/quick">
              <Sparkles className="mr-2 h-4 w-4" />
              Ask AI
            </Link>
          </Button>
          <Button asChild variant="outline" className="justify-start">
            <Link href="/dashboard/goals/new">
              <Target className="mr-2 h-4 w-4" />
              Set Goal
            </Link>
          </Button>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-card text-card-foreground rounded-lg border p-6 shadow-sm">
        <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
        <div className="space-y-3">
          {recentActivities.map((activity) => {
            const IconComponent = activity.icon;
            return (
              <div
                key={activity.id}
                className="flex items-center gap-3 py-2 border-b last:border-0"
              >
                <IconComponent className="h-4 w-4 text-muted-foreground" />
                <div className="flex-1">
                  <p className="text-sm font-medium">{activity.action}</p>
                  <p className="text-xs text-muted-foreground">{activity.time}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Achievements */}
      <div className="bg-card text-card-foreground rounded-lg border p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Recent Achievements</h3>
          <Button asChild variant="ghost" size="sm">
            <Link href="/dashboard/achievements">View All</Link>
          </Button>
        </div>
        <div className="flex gap-4">
          {recentBadges.map((badge) => (
            <div
              key={badge.id}
              className="flex flex-col items-center gap-2 p-4 rounded-lg border bg-muted/50 hover:bg-muted transition-colors"
            >
              <span className="text-4xl">{badge.icon}</span>
              <span className="text-xs font-medium text-center">{badge.name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
