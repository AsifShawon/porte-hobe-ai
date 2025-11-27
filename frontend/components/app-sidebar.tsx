"use client"

import * as React from "react"
import {
  BookOpen,
  Bot,
  Map,
  Settings2,
  SquareTerminal,
  Target,
  Trophy,
  Flame,
  FileText,
  TrendingUp,
  Sparkles,
} from "lucide-react"

import { NavMain } from "@/components/nav-main"
import { NavProjects } from "@/components/nav-projects"
import { NavUser } from "@/components/nav-user"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Separator } from "@/components/ui/separator"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
  SidebarTrigger,
} from "@/components/ui/sidebar"

// This is sample data for Autonomous Learning Platform.
const data = {
  user: {
    name: "Student Name",
    email: "student@example.com",
    avatar: "/avatars/student.jpg",
  },
  teams: [
    {
      name: "PorteHobeAI",
      logo: Sparkles,
      plan: "Learning",
    },
  ],
  navMain: [
    {
      title: "Dashboard",
      url: "/dashboard",
      icon: SquareTerminal,
      isActive: true,
      items: [
        {
          title: "Overview",
          url: "/dashboard",
        },
        {
          title: "Recent Activity",
          url: "/dashboard/activity",
        },
      ],
    },
    {
      title: "AI Tutor",
      url: "/dashboard/chat",
      icon: Bot,
      items: [
        {
          title: "New Chat",
          url: "/dashboard/chat",
        },
        {
          title: "Chat History",
          url: "/dashboard/chat/history",
        },
        {
          title: "Quick Ask",
          url: "/dashboard/chat/quick",
        },
      ],
    },
    {
      title: "My Learning",
      url: "/dashboard/learning",
      icon: BookOpen,
      items: [
        {
          title: "Learning Path",
          url: "/dashboard/learning/path",
        },
        {
          title: "Current Topics",
          url: "/dashboard/learning/current",
        },
        {
          title: "Browse Topics",
          url: "/dashboard/topics",
        },
        {
          title: "Completed",
          url: "/dashboard/learning/completed",
        },
      ],
    },
    {
      title: "Practice",
      url: "/dashboard/practice",
      icon: Target,
      items: [
        {
          title: "All Exercises",
          url: "/dashboard/practice/exercises",
        },
        {
          title: "Coding Challenges",
          url: "/dashboard/practice/challenges",
        },
        {
          title: "Quizzes",
          url: "/dashboard/practice/quizzes",
        },
        {
          title: "Past Attempts",
          url: "/dashboard/practice/history",
        },
      ],
    },
    {
      title: "Achievements",
      url: "/dashboard/achievements",
      icon: Trophy,
      items: [
        {
          title: "My Badges",
          url: "/dashboard/achievements/",
        },
        {
          title: "Milestones",
          url: "/dashboard/achievements/milestones",
        },
        {
          title: "Certificates",
          url: "/dashboard/achievements/certificates",
        },
      ],
    },
    {
      title: "My Progress",
      url: "/dashboard/progress",
      icon: TrendingUp,
      items: [
        {
          title: "Overall Stats",
          url: "/dashboard/progress",
        },
        {
          title: "Topic Progress",
          url: "/dashboard/progress/topics",
        },
        {
          title: "Performance",
          url: "/dashboard/progress/performance",
        },
        {
          title: "Study Time",
          url: "/dashboard/progress/time",
        },
      ],
    },
    {
      title: "Resources",
      url: "/dashboard/resources",
      icon: FileText,
      items: [
        {
          title: "Saved Materials",
          url: "/dashboard/resources/saved",
        },
        {
          title: "My Notes",
          url: "/dashboard/resources/notes",
        },
        {
          title: "Bookmarks",
          url: "/dashboard/resources/bookmarks",
        },
        {
          title: "Uploaded Files",
          url: "/dashboard/resources/files",
        },
      ],
    },
    {
      title: "Study Goals",
      url: "/dashboard/goals",
      icon: Flame,
      items: [
        {
          title: "Active Goals",
          url: "/dashboard/goals",
        },
        {
          title: "Set New Goal",
          url: "/dashboard/goals/new",
        },
        {
          title: "Goal History",
          url: "/dashboard/goals/history",
        },
      ],
    },
    {
      title: "Settings",
      url: "/dashboard/settings",
      icon: Settings2,
      items: [
        {
          title: "Profile",
          url: "/dashboard/settings/profile",
        },
        {
          title: "Learning Preferences",
          url: "/dashboard/settings/preferences",
        },
        {
          title: "Notifications",
          url: "/dashboard/settings/notifications",
        },
        {
          title: "Privacy",
          url: "/dashboard/settings/privacy",
        },
      ],
    },
  ],
  projects: [
    {
      name: "Current Learning Path",
      url: "/dashboard/learning/path",
      icon: Map,
    },
    {
      name: "Study Streak",
      url: "/dashboard/streak",
      icon: Flame,
    },
    {
      name: "Recent Achievements",
      url: "/dashboard/achievements",
      icon: Trophy,
    },
  ],
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <div className="flex items-center gap-2 px-4 py-2 border-b">
          <SidebarTrigger className="-ml-1" />
          <Separator
            orientation="vertical"
            className="mr-2 data-[orientation=vertical]:h-4"
          />
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem className="hidden md:block">
                <BreadcrumbLink href="/">PorteHobeAi</BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator className="hidden md:block" />
              <BreadcrumbItem>
                <BreadcrumbPage>Dashboard</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        </div>
        {/* <TeamSwitcher teams={data.teams} /> */}
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
        <NavProjects projects={data.projects} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={data.user} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
