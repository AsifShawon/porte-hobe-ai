# Frontend Implementation Plan
## Student-Focused Dashboard - From Placeholders to Production

**Date:** 2025-11-25
**Project:** Porte Hobe AI - Student Learning Platform
**Branch:** `claude/backend-frontend-sync-01HWKMtHWSdW8QRKv5dCNoJk`

---

## 📊 Current State

### ✅ Already Completed
- **30 page routes created** with placeholder content
- **Sidebar navigation** fully updated for student experience
- **Main dashboard** enhanced with student-focused widgets
- **PlaceholderPage component** for "Coming Soon" states
- **Backend APIs** ready with 29 endpoints across 4 routers

### 🎯 Implementation Goal
Transform **30 placeholder pages** into **fully functional, production-ready pages** with real data from backend APIs.

---

## 📁 Page Inventory

### Pages to Implement (30 Total)

#### 🏆 **Achievements** (4 pages)
1. `/dashboard/achievements` - Main achievements showcase
2. `/dashboard/achievements/badges` - Badge collection
3. `/dashboard/achievements/milestones` - Milestone tracker
4. `/dashboard/achievements/certificates` - Certificates earned

#### 🎯 **Study Goals** (3 pages)
5. `/dashboard/goals` - Active goals list
6. `/dashboard/goals/new` - Create new goal
7. `/dashboard/goals/history` - Past goals

#### 📚 **My Learning** (3 pages)
8. `/dashboard/learning/path` - Learning path/roadmap
9. `/dashboard/learning/current` - Current topics
10. `/dashboard/learning/completed` - Completed topics

#### 💪 **Practice** (5 pages)
11. `/dashboard/practice` - Practice hub
12. `/dashboard/practice/exercises` - All exercises
13. `/dashboard/practice/challenges` - Coding challenges
14. `/dashboard/practice/quizzes` - Quizzes
15. `/dashboard/practice/history` - Past attempts

#### 📈 **Progress** (4 pages)
16. `/dashboard/progress` - Overall stats
17. `/dashboard/progress/topics` - Topic progress
18. `/dashboard/progress/performance` - Performance analytics
19. `/dashboard/progress/time` - Study time tracking

#### 📝 **Resources** (5 pages)
20. `/dashboard/resources` - Resource library
21. `/dashboard/resources/saved` - Saved materials
22. `/dashboard/resources/notes` - My notes
23. `/dashboard/resources/bookmarks` - Bookmarks
24. `/dashboard/resources/files` - Uploaded files

#### ⚙️ **Settings** (4 pages)
25. `/dashboard/settings/profile` - User profile
26. `/dashboard/settings/preferences` - Learning preferences
27. `/dashboard/settings/notifications` - Notification settings
28. `/dashboard/settings/privacy` - Privacy settings

#### 🔥 **Other** (2 pages)
29. `/dashboard/streak` - Streak calendar
30. `/dashboard/chat/quick` - Quick AI ask

---

## 🏗️ Implementation Strategy

### Phase 1: Core Infrastructure (Priority 1)
**Goal:** Set up data fetching and shared components
**Estimated Time:** 4-6 hours

#### Tasks:
1. **Create API client utilities** (`lib/api/`)
   - `goals.ts` - Goals API functions
   - `achievements.ts` - Achievements API functions
   - `practice.ts` - Practice API functions
   - `resources.ts` - Resources API functions
   - `progress.ts` - Progress API functions (extend existing)

2. **Create shared UI components** (`components/`)
   - `StatsCard.tsx` - Reusable stat display card
   - `ProgressBar.tsx` - Progress visualization
   - `Badge.tsx` - Achievement badge display
   - `GoalCard.tsx` - Goal display card
   - `ExerciseCard.tsx` - Practice exercise card
   - `ResourceCard.tsx` - Resource item card
   - `EmptyState.tsx` - "No data yet" states
   - `LoadingState.tsx` - Loading skeletons
   - `ErrorState.tsx` - Error handling display

3. **Create custom hooks** (`hooks/`)
   - `useGoals.ts` - Fetch and manage goals
   - `useAchievements.ts` - Fetch achievements
   - `usePractice.ts` - Fetch exercises
   - `useResources.ts` - Fetch resources
   - `useProgress.ts` - Fetch progress stats

4. **Set up TypeScript types** (`types/`)
   - `goals.ts` - Goal interfaces
   - `achievements.ts` - Achievement interfaces
   - `practice.ts` - Practice/exercise interfaces
   - `resources.ts` - Resource interfaces
   - `progress.ts` - Progress interfaces

---

### Phase 2: High-Priority Pages (Priority 1)
**Goal:** Implement most-used student features
**Estimated Time:** 8-10 hours

#### 2.1 Study Goals (3 pages)

**`/dashboard/goals` - Active Goals List**
- **Components:**
  - Goals filter (active/completed/failed)
  - Goal cards with progress bars
  - Quick stats (completion rate, active count)
  - Empty state with "Create Goal" CTA
- **Data:** `GET /api/goals` + `GET /api/goals/stats/summary`
- **Actions:** Mark complete, edit, delete
- **UI Elements:**
  - Grid of goal cards
  - Progress percentage visualization
  - Deadline countdown
  - Quick actions dropdown

**`/dashboard/goals/new` - Create Goal**
- **Components:**
  - Goal type selector (daily, weekly, monthly, topic, streak)
  - Target value input
  - Unit selector (topics, minutes, days, points)
  - Optional deadline picker
  - Topic association dropdown
  - Preview card
- **Data:** `POST /api/goals`
- **Validation:**
  - Target value > 0
  - Valid deadline (future date)
  - Title required (1-200 chars)

**`/dashboard/goals/history` - Past Goals**
- **Components:**
  - Completed/Failed tabs
  - Timeline view
  - Success/failure statistics
  - Insights (common patterns, best streaks)
- **Data:** `GET /api/goals?status=completed` + `GET /api/goals?status=failed`

---

#### 2.2 Achievements & Badges (4 pages)

**`/dashboard/achievements` - Main Achievements**
- **Components:**
  - XP bar and current level
  - Achievement grid (locked/unlocked states)
  - Progress bars for locked achievements
  - Rarity filter (common → legendary)
  - Category tabs (learning, streak, mastery, etc.)
  - Recent unlocks timeline
- **Data:**
  - `GET /api/achievements/available`
  - `GET /api/achievements/unlocked`
  - `GET /api/achievements/stats`
  - `POST /api/achievements/check` (on page load)
- **UI Features:**
  - Animated unlock effects
  - Tooltip with requirements
  - Share achievement (future)
  - Confetti on new unlock

**`/dashboard/achievements/badges` - Badge Collection**
- **Components:**
  - Badge showcase grid
  - Filter by category/rarity
  - Badge details modal
  - Earn date and description
- **Data:** `GET /api/achievements/unlocked?category=...`

**`/dashboard/achievements/milestones` - Milestones**
- **Components:**
  - Major milestone timeline
  - Upcoming milestones tracker
  - Milestone progress indicators
- **Data:** `GET /api/achievements/available` (filtered)

**`/dashboard/achievements/certificates` - Certificates**
- **Components:**
  - Certificate gallery
  - Downloadable certificates (PDF)
  - Share options
- **Data:** Achievement data + certificate generation

---

#### 2.3 Practice Hub (5 pages)

**`/dashboard/practice` - Practice Hub**
- **Components:**
  - Practice stats cards
  - Recommended exercises
  - Continue last exercise CTA
  - Quick filters (type, difficulty)
  - Recent submissions
- **Data:**
  - `GET /api/practice/stats`
  - `GET /api/practice/exercises?limit=5`
  - `GET /api/practice/submissions?limit=5`

**`/dashboard/practice/exercises` - All Exercises**
- **Components:**
  - Exercise list with filters
  - Difficulty badges
  - Points display
  - Completion status
  - Topic tags
  - Search functionality
- **Data:** `GET /api/practice/exercises`
- **Filters:**
  - Type (coding, quiz, math, concept, debugging)
  - Difficulty (beginner → expert)
  - Topic
  - Completion status

**`/dashboard/practice/challenges` - Coding Challenges**
- **Components:**
  - Code editor interface
  - Test case runner
  - Hints system
  - Timer (if time limit)
  - Submit button
  - Results display
- **Data:**
  - `GET /api/practice/exercises?exercise_type=coding`
  - `POST /api/practice/submit`
- **Libraries:**
  - `@monaco-editor/react` for code editing
  - Or `react-simple-code-editor` for lighter option

**`/dashboard/practice/quizzes` - Quizzes**
- **Components:**
  - Quiz question display
  - Multiple choice UI
  - Question navigator
  - Timer
  - Score display
- **Data:**
  - `GET /api/practice/exercises?exercise_type=quiz`
  - `POST /api/practice/submit`

**`/dashboard/practice/history` - Past Attempts**
- **Components:**
  - Submission history table
  - Score/status badges
  - Filter by exercise/date
  - View submission details
  - Retry button
- **Data:** `GET /api/practice/submissions`

---

#### 2.4 My Learning (3 pages)

**`/dashboard/learning/path` - Learning Path**
- **Components:**
  - Visual roadmap/flowchart
  - Current position indicator
  - Next recommended topic
  - Prerequisites visualization
  - Progress percentage
  - Topic cards (clickable)
- **Data:**
  - `GET /api/topics`
  - `GET /api/progress`
- **UI Pattern:**
  - Vertical timeline with branches
  - Or interactive graph with connections

**`/dashboard/learning/current` - Current Topics**
- **Components:**
  - In-progress topics list
  - Continue learning CTAs
  - Progress bars
  - Last activity timestamp
  - Quick stats per topic
- **Data:** `GET /api/progress?status=in_progress`

**`/dashboard/learning/completed` - Completed Topics**
- **Components:**
  - Completed topics grid
  - Completion date
  - Final score
  - Review/revisit button
  - Certificate download (if applicable)
- **Data:** `GET /api/progress?status=completed`

---

### Phase 3: Mid-Priority Pages (Priority 2)
**Goal:** Analytics and resource management
**Estimated Time:** 6-8 hours

#### 3.1 Progress & Analytics (4 pages)

**`/dashboard/progress` - Overall Stats**
- **Components:**
  - Key metrics cards
  - Progress charts (line/bar)
  - Topic completion pie chart
  - Study time visualization
  - Streak calendar
  - Achievements summary
- **Data:** `GET /api/progress/stats`
- **Charts:** Use `recharts` library

**`/dashboard/progress/topics` - Topic Progress**
- **Components:**
  - Topic list with progress
  - Sorting (by progress, score, time)
  - Filter by status
  - Detailed progress modal
- **Data:** `GET /api/progress`

**`/dashboard/progress/performance` - Performance**
- **Components:**
  - Score trends chart
  - Best/worst topics
  - Improvement suggestions
  - Comparison to goals
- **Data:** `GET /api/progress` + calculations

**`/dashboard/progress/time` - Study Time**
- **Components:**
  - Daily/weekly/monthly time charts
  - Time by topic breakdown
  - Productivity heatmap
  - Longest streak
- **Data:** `GET /api/progress/stats` + session data

---

#### 3.2 Resources Library (5 pages)

**`/dashboard/resources` - Resource Library**
- **Components:**
  - Resource type tabs
  - Search bar
  - Tag filter
  - Recent resources
  - Favorites section
  - Folder navigation
- **Data:** `GET /api/resources`

**`/dashboard/resources/saved` - Saved Materials**
- **Components:**
  - All saved resources
  - Grid/list view toggle
  - Sort options
  - Bulk actions
- **Data:** `GET /api/resources`

**`/dashboard/resources/notes` - My Notes**
- **Components:**
  - Notes list
  - Markdown editor
  - Create new note
  - Edit/delete actions
  - Topic tagging
- **Data:**
  - `GET /api/resources?resource_type=note`
  - `POST /api/resources/notes`
  - `PATCH /api/resources/{id}`
- **Editor:** `react-markdown` + `react-mde` or similar

**`/dashboard/resources/bookmarks` - Bookmarks**
- **Components:**
  - Bookmark cards with preview
  - Add bookmark form
  - URL validation
  - Edit/delete actions
- **Data:**
  - `GET /api/resources?resource_type=bookmark`
  - `POST /api/resources/bookmarks`

**`/dashboard/resources/files` - Uploaded Files**
- **Components:**
  - File list with icons
  - Upload dropzone
  - File preview
  - Download/delete actions
- **Data:** Existing `/api/files` endpoints

---

### Phase 4: Low-Priority Pages (Priority 3)
**Goal:** Settings and misc features
**Estimated Time:** 4-6 hours

#### 4.1 Settings (4 pages)

**`/dashboard/settings/profile` - User Profile**
- **Components:**
  - Avatar upload
  - Name/email display
  - Bio/description
  - Learning goals
  - Account info
- **Data:** Supabase user data + update functions

**`/dashboard/settings/preferences` - Learning Preferences**
- **Components:**
  - Difficulty preference
  - Learning pace
  - Notification preferences
  - AI tutor settings
  - Theme toggle
- **Data:** User metadata (JSONB in database)

**`/dashboard/settings/notifications` - Notifications**
- **Components:**
  - Email notifications toggle
  - Achievement notifications
  - Goal reminders
  - Weekly summary
- **Data:** Notification preferences

**`/dashboard/settings/privacy` - Privacy**
- **Components:**
  - Data sharing settings
  - Leaderboard visibility
  - Profile visibility
  - Delete account option
- **Data:** Privacy settings

---

#### 4.2 Other Pages (2 pages)

**`/dashboard/streak` - Streak Calendar**
- **Components:**
  - Large calendar heatmap
  - Current streak display
  - Longest streak record
  - Streak milestones
  - Motivational messages
- **Data:** `GET /api/progress/stats` (streak data)
- **UI:** GitHub-style contribution calendar

**`/dashboard/chat/quick` - Quick AI Ask**
- **Components:**
  - Simplified chat interface
  - Single question input
  - Quick response
  - No history
  - Topic context selector
- **Data:** Existing chat API
- **Use Case:** Quick questions without full conversation

---

## 🧩 Reusable Components Library

### UI Components to Build

```
components/
├── shared/
│   ├── StatsCard.tsx              # Metric display card
│   ├── ProgressBar.tsx            # Progress visualization
│   ├── ProgressRing.tsx           # Circular progress
│   ├── Badge.tsx                  # Achievement/status badge
│   ├── EmptyState.tsx             # No data placeholder
│   ├── LoadingState.tsx           # Loading skeleton
│   ├── ErrorState.tsx             # Error display
│   ├── PageHeader.tsx             # Consistent page headers
│   └── FilterBar.tsx              # Reusable filters
│
├── goals/
│   ├── GoalCard.tsx               # Individual goal card
│   ├── GoalForm.tsx               # Create/edit goal form
│   ├── GoalProgress.tsx           # Goal progress display
│   └── GoalFilters.tsx            # Goal filter controls
│
├── achievements/
│   ├── AchievementCard.tsx        # Achievement display
│   ├── AchievementGrid.tsx        # Achievement grid layout
│   ├── LevelProgress.tsx          # XP/Level bar
│   ├── BadgeIcon.tsx              # Badge with rarity styling
│   └── UnlockAnimation.tsx        # Animated unlock effect
│
├── practice/
│   ├── ExerciseCard.tsx           # Exercise list item
│   ├── CodeEditor.tsx             # Code editor wrapper
│   ├── QuizQuestion.tsx           # Quiz UI
│   ├── HintButton.tsx             # Hint reveal button
│   ├── SubmissionFeedback.tsx     # Result display
│   └── DifficultyBadge.tsx        # Difficulty indicator
│
├── resources/
│   ├── ResourceCard.tsx           # Resource item card
│   ├── NoteEditor.tsx             # Markdown note editor
│   ├── BookmarkCard.tsx           # Bookmark display
│   ├── FileUploader.tsx           # File upload UI
│   └── FolderNav.tsx              # Folder navigation
│
├── progress/
│   ├── StatChart.tsx              # Chart wrapper
│   ├── TopicProgressCard.tsx     # Topic progress item
│   ├── StreakCalendar.tsx         # Heatmap calendar
│   └── TimeChart.tsx              # Study time visualization
│
└── learning/
    ├── LearningPathGraph.tsx      # Visual roadmap
    ├── TopicCard.tsx              # Topic display card
    ├── PrerequisiteTree.tsx       # Prerequisite visualization
    └── NextTopicCard.tsx          # Recommended next topic
```

---

## 🔌 API Integration Pattern

### Standard Data Fetching Pattern

```typescript
// hooks/useGoals.ts
'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'

export function useGoals(filters?: { status?: string }) {
  const [goals, setGoals] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function fetchGoals() {
      try {
        const supabase = createClient()
        const { data: { session } } = await supabase.auth.getSession()

        if (!session) throw new Error('Not authenticated')

        const url = new URL('/api/goals', process.env.NEXT_PUBLIC_FASTAPI_URL)
        if (filters?.status) url.searchParams.set('status', filters.status)

        const response = await fetch(url, {
          headers: {
            'Authorization': `Bearer ${session.access_token}`
          }
        })

        if (!response.ok) throw new Error('Failed to fetch goals')

        const data = await response.json()
        setGoals(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchGoals()
  }, [filters])

  return { goals, loading, error, refetch: fetchGoals }
}
```

### Next.js API Route Pattern (Proxy)

```typescript
// app/api/goals/route.ts
import { createClient } from '@/lib/supabase/server'

export async function GET(request: Request) {
  const supabase = await createClient()

  const { data: { user }, error } = await supabase.auth.getUser()
  if (error || !user) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const { data: { session } } = await supabase.auth.getSession()
  const { searchParams } = new URL(request.url)

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_FASTAPI_URL}/api/goals?${searchParams}`,
    {
      headers: {
        'Authorization': `Bearer ${session?.access_token}`
      }
    }
  )

  const data = await response.json()
  return Response.json(data)
}
```

---

## 📊 Implementation Priority Matrix

| Priority | Pages | Estimated Hours | Dependencies |
|----------|-------|----------------|--------------|
| **P1 - Core** | Infrastructure (9 items) | 4-6h | None |
| **P1 - High** | Goals (3), Achievements (4), Practice (5) | 8-10h | P1 Core |
| **P2 - Mid** | Progress (4), Resources (5) | 6-8h | P1 High |
| **P3 - Low** | Settings (4), Other (2) | 4-6h | P1 Core |
| **TOTAL** | **30 pages + infrastructure** | **22-30 hours** | Sequential |

---

## 🎨 Design System & Styling

### Color Coding

```typescript
// Consistent color scheme
const achievementRarity = {
  common: 'bg-gray-500',
  uncommon: 'bg-green-500',
  rare: 'bg-blue-500',
  epic: 'bg-purple-500',
  legendary: 'bg-yellow-500'
}

const goalStatus = {
  active: 'bg-blue-500',
  completed: 'bg-green-500',
  failed: 'bg-red-500',
  paused: 'bg-gray-500'
}

const difficulty = {
  beginner: 'bg-green-500',
  intermediate: 'bg-yellow-500',
  advanced: 'bg-orange-500',
  expert: 'bg-red-500'
}
```

### Icon System

```typescript
import {
  Target,        // Goals
  Trophy,        // Achievements
  BookOpen,      // Learning
  Code,          // Practice
  TrendingUp,    // Progress
  FileText,      // Resources
  Flame,         // Streak
  CheckCircle,   // Completed
  Clock,         // Time
  Zap            // Quick actions
} from 'lucide-react'
```

---

## 🧪 Testing Strategy

### Component Testing

```bash
# For each component
- Unit tests with Jest
- Accessibility tests
- Snapshot tests
```

### Integration Testing

```bash
# For each page
- API integration tests
- Data flow tests
- Error state handling
```

### E2E Testing (Optional)

```bash
# Critical flows
- Goal creation → completion
- Exercise submission
- Achievement unlock
- Resource creation
```

---

## 📦 Required Dependencies

### Already Installed
- `react`, `next` - Core framework
- `@supabase/ssr` - Authentication
- `lucide-react` - Icons
- `tailwindcss` - Styling
- `recharts` - Charts (check if installed)

### To Install

```bash
cd frontend

# Code editor for practice pages
npm install @monaco-editor/react

# Markdown editor for notes
npm install react-markdown react-mde remark-gfm

# Date utilities
npm install date-fns

# Form handling
npm install react-hook-form @hookform/resolvers zod

# Charts (if not installed)
npm install recharts

# Calendar heatmap for streak
npm install react-calendar-heatmap

# Confetti for achievements
npm install canvas-confetti
```

---

## 🚀 Implementation Workflow

### For Each Page:

1. **Create TypeScript types**
   ```typescript
   // types/goals.ts
   export interface Goal { ... }
   ```

2. **Create API hook**
   ```typescript
   // hooks/useGoals.ts
   export function useGoals() { ... }
   ```

3. **Create components**
   ```typescript
   // components/goals/GoalCard.tsx
   export function GoalCard({ goal }: { goal: Goal }) { ... }
   ```

4. **Implement page**
   ```typescript
   // app/dashboard/goals/page.tsx
   'use client'
   export default function GoalsPage() { ... }
   ```

5. **Add loading/error states**
   ```typescript
   if (loading) return <LoadingState />
   if (error) return <ErrorState error={error} />
   ```

6. **Test with real data**
   - Create test data in database
   - Verify API responses
   - Test all interactions

---

## 📝 Implementation Checklist

### Phase 1: Infrastructure ✅
- [ ] Create API client utilities (5 files)
- [ ] Create shared UI components (9 components)
- [ ] Create custom hooks (5 hooks)
- [ ] Define TypeScript types (5 type files)
- [ ] Set up error boundaries
- [ ] Configure loading states

### Phase 2: High Priority Pages
- [ ] **Goals** (3 pages)
  - [ ] `/dashboard/goals`
  - [ ] `/dashboard/goals/new`
  - [ ] `/dashboard/goals/history`
- [ ] **Achievements** (4 pages)
  - [ ] `/dashboard/achievements`
  - [ ] `/dashboard/achievements/badges`
  - [ ] `/dashboard/achievements/milestones`
  - [ ] `/dashboard/achievements/certificates`
- [ ] **Practice** (5 pages)
  - [ ] `/dashboard/practice`
  - [ ] `/dashboard/practice/exercises`
  - [ ] `/dashboard/practice/challenges`
  - [ ] `/dashboard/practice/quizzes`
  - [ ] `/dashboard/practice/history`
- [ ] **Learning** (3 pages)
  - [ ] `/dashboard/learning/path`
  - [ ] `/dashboard/learning/current`
  - [ ] `/dashboard/learning/completed`

### Phase 3: Mid Priority Pages
- [ ] **Progress** (4 pages)
  - [ ] `/dashboard/progress`
  - [ ] `/dashboard/progress/topics`
  - [ ] `/dashboard/progress/performance`
  - [ ] `/dashboard/progress/time`
- [ ] **Resources** (5 pages)
  - [ ] `/dashboard/resources`
  - [ ] `/dashboard/resources/saved`
  - [ ] `/dashboard/resources/notes`
  - [ ] `/dashboard/resources/bookmarks`
  - [ ] `/dashboard/resources/files`

### Phase 4: Low Priority Pages
- [ ] **Settings** (4 pages)
  - [ ] `/dashboard/settings/profile`
  - [ ] `/dashboard/settings/preferences`
  - [ ] `/dashboard/settings/notifications`
  - [ ] `/dashboard/settings/privacy`
- [ ] **Other** (2 pages)
  - [ ] `/dashboard/streak`
  - [ ] `/dashboard/chat/quick`

---

## 🎯 Success Metrics

### Functionality
- [ ] All pages load without errors
- [ ] All API calls work correctly
- [ ] Data displays accurately
- [ ] Forms validate properly
- [ ] Mutations update state correctly

### Performance
- [ ] Page load < 2 seconds
- [ ] API responses < 500ms
- [ ] No hydration errors
- [ ] Smooth animations (60fps)

### UX
- [ ] Clear loading states
- [ ] Helpful error messages
- [ ] Responsive on mobile
- [ ] Accessible (WCAG AA)
- [ ] Intuitive navigation

---

## 📖 Next Steps

1. **Review this plan** with the team
2. **Set up Phase 1 infrastructure** (critical foundation)
3. **Implement one page end-to-end** as a template
4. **Iterate and refine** the pattern
5. **Scale to remaining pages** following the pattern

---

## 🆘 Support & Resources

- **Backend API Docs:** `BACKEND_IMPLEMENTATION_SUMMARY.md`
- **Database Schema:** `server/database_migrations.sql`
- **Component Library:** shadcn/ui documentation
- **Icons:** Lucide React documentation
- **Charts:** Recharts documentation

---

**End of Implementation Plan**

*This plan provides a structured roadmap to transform 30 placeholder pages into a fully functional student learning platform. Follow the phases sequentially for best results.*
