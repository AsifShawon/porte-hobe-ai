"use client"

import * as React from "react"
import {
  BookOpen,
  Bot,
  Frame,
  Map,
  PieChart,
  Settings2,
  SquareTerminal,
} from "lucide-react"

import { NavMain } from "@/components/nav-main"
import { NavProjects } from "@/components/nav-projects"
import { NavUser } from "@/components/nav-user"
import { TeamSwitcher } from "@/components/team-switcher"
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

// This is sample data for Autonomous Teaching Assistant.
const data = {
  user: {
    name: "Teacher Name",
    email: "teacher@example.com",
    avatar: "/avatars/teacher.jpg",
  },
  teams: [
    {
      name: "Teaching Assistant",
      logo: BookOpen,
      plan: "Pro",
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
      title: "AI Tutor Chat",
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
      ],
    },
    {
      title: "Lessons",
      url: "/dashboard/lessons",
      icon: BookOpen,
      items: [
        {
          title: "All Lessons",
          url: "/dashboard/lessons",
        },
        {
          title: "Create Lesson",
          url: "/dashboard/lessons/create",
        },
        {
          title: "Lesson Plans",
          url: "/dashboard/lessons/plans",
        },
      ],
    },
    {
      title: "Students",
      url: "/dashboard/students",
      icon: Bot,
      items: [
        {
          title: "Student List",
          url: "/dashboard/students",
        },
        {
          title: "Progress Reports",
          url: "/dashboard/students/progress",
        },
        {
          title: "Assignments",
          url: "/dashboard/students/assignments",
        },
      ],
    },
    {
      title: "Analytics",
      url: "/dashboard/analytics",
      icon: PieChart,
      items: [
        {
          title: "Performance",
          url: "/dashboard/analytics/performance",
        },
        {
          title: "Engagement",
          url: "/dashboard/analytics/engagement",
        },
        {
          title: "Reports",
          url: "/dashboard/analytics/reports",
        },
      ],
    },
    {
      title: "Settings",
      url: "/dashboard/settings",
      icon: Settings2,
      items: [
        {
          title: "General",
          url: "/dashboard/settings/general",
        },
        {
          title: "Notifications",
          url: "/dashboard/settings/notifications",
        },
        {
          title: "Account",
          url: "/dashboard/settings/account",
        },
      ],
    },
  ],
  projects: [
    {
      name: "Current Course",
      url: "/dashboard/courses/current",
      icon: Frame,
    },
    {
      name: "Upcoming Lessons",
      url: "/dashboard/lessons/upcoming",
      icon: PieChart,
    },
    {
      name: "Student Feedback",
      url: "/dashboard/feedback",
      icon: Map,
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
