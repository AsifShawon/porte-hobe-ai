# CLAUDE.md - AI Assistant Guide for Porte Hobe AI

**Last Updated:** 2025-11-30
**Repository:** Porte Hobe AI - AI-Powered Tutoring Platform
**Architecture:** Monorepo (Next.js Frontend + FastAPI Backend)

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture & Tech Stack](#architecture--tech-stack)
3. [Directory Structure](#directory-structure)
4. [Development Workflows](#development-workflows)
5. [Key Conventions & Patterns](#key-conventions--patterns)
6. [Critical Files Reference](#critical-files-reference)
7. [Common Tasks Guide](#common-tasks-guide)
8. [API Endpoints](#api-endpoints)
9. [Database Schema](#database-schema)
10. [Testing & Quality](#testing--quality)
11. [Deployment](#deployment)
12. [Gotchas & Important Notes](#gotchas--important-notes)

---

## Project Overview

**Porte Hobe AI** is a comprehensive full-stack AI-powered student learning platform that provides personalized education in programming and mathematics. The system uses advanced AI agents with LangChain/LangGraph for intelligent tutoring, automated assessment, and adaptive learning paths.

### Core Features

#### Learning & Teaching
- **Autonomous AI Tutor**: Real-time chat with two-phase reasoning (Planning → Teaching)
- **Learning Domains**: Programming Basics and Math Fundamentals
- **Personalized Roadmaps**: AI-generated learning paths with phases and milestones
- **Progress Inference Engine**: AI automatically detects milestone completion from conversations
- **Session Management**: Reliable message persistence with chat-roadmap-quiz integration

#### Assessment & Practice
- **AI-Generated Quizzes**: Context-aware quizzes from conversation topics
- **Intelligent Grading**: AI-powered grading with detailed feedback and partial credit
- **Multiple Question Types**: Multiple choice, true/false, short answer, code challenges
- **Quiz Triggers**: Milestone-based quiz unlocking system
- **Practice Exercises**: Coding challenges, math problems, topic-based exercises

#### Gamification & Motivation
- **Achievement System**: 17+ badges with rarity levels and XP rewards
- **Study Goals**: Daily, weekly, monthly goals with progress tracking
- **Streak Calendar**: Learning streak visualization and management
- **Level System**: XP-based progression with unlockable features

#### Resources & Tools
- **Resource Library**: Save materials, notes, bookmarks, file uploads
- **Multi-modal Learning**: Text, PDF, images (OCR), web scraping
- **Memory System**: User-specific and universal knowledge embeddings with vector search
- **Progress Analytics**: Detailed performance metrics and time tracking

#### Technical Features
- **Streaming Responses**: Server-Sent Events (SSE) for real-time chat
- **Authentication**: Supabase Auth with JWT verification
- **Rate Limiting**: Per-user API rate limiting
- **Dynamic Prompts**: Context-aware prompt generation
- **Intent Classification**: LLM-based user intent detection
- **Specialist Models**: Task-specific LLM routing

### Key Statistics

- **Backend**: ~13,785 lines of Python (48 modules)
- **Frontend**: 50+ pages, 30+ component groups
- **API Endpoints**: 60+ protected endpoints across 9 routers
- **AI Agents**: 7+ specialized agents (Tutor, Quiz Generator, Quiz Grader, Roadmap Generator, Progress Inference, MCP agents)
- **Database**: Supabase (PostgreSQL with pgvector) - 15+ tables
- **AI Engine**: LangChain + LangGraph + Gemini/Ollama

---

## Architecture & Tech Stack

### Frontend Stack

```
Technology          Version     Purpose
────────────────────────────────────────────────────────────
Next.js             15.5.2      App Router, SSR/SSG
React               19.1.0      UI Framework
TypeScript          ^5          Type Safety
Tailwind CSS        ^4          Styling
Radix UI            Various     Accessible UI Primitives
shadcn/ui           Latest      Component Library
Zustand             5.0.8       State Management
Supabase SSR        0.5.2       Authentication
React Markdown      10.1.0      Content Rendering
KaTeX               0.16.25     Math Rendering
Recharts            3.3.0       Data Visualization
DOMPurify           3.3.0       HTML Sanitization
```

### Backend Stack

```
Technology          Version     Purpose
────────────────────────────────────────────────────────────
FastAPI             ≥0.115.0    REST API Framework
Uvicorn             ≥0.30.0     ASGI Server
LangChain           ≥0.3.0      LLM Orchestration
LangGraph           ≥0.6.0      Agent State Machine
Ollama              Latest      Local LLM (qwen2.5:3b)
Google GenAI        ≥0.8.0      Gemini Integration
Tavily              ≥0.5.0      Web Search
Supabase            ≥2.0.0      Database & Auth
PyMuPDF             ≥1.23.0     PDF Processing
Pytesseract         ≥0.3.10     OCR
BeautifulSoup4      ≥4.12.0     HTML Parsing
SymPy               ≥1.12       Symbolic Math
PyJWT               2.8.0       JWT Verification
```

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                       Frontend (Next.js 15)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │   Pages     │  │ Components  │  │ API Routes  │                 │
│  │  (50+)      │  │    (30+)    │  │   (Proxy)   │                 │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                 │
│         │                │                │                          │
│         └────────────────┴────────────────┘                          │
│                          │                                           │
└──────────────────────────┼───────────────────────────────────────────┘
                           │ HTTP/SSE
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │     Main     │  │   Routers    │  │   AI Agents  │              │
│  │  Endpoints   │  │     (9)      │  │     (7+)     │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                        │
│         └─────────────────┴─────────────────┘                        │
│                           │                                          │
│         ┌─────────────────┼─────────────────┐                        │
│         ▼                 ▼                 ▼                        │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐                  │
│  │ Tutor    │      │  Quiz    │      │ Roadmap  │                  │
│  │ Agent    │      │Generator │      │Generator │                  │
│  └──────────┘      └──────────┘      └──────────┘                  │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐                  │
│  │  Quiz    │      │Progress  │      │ Session  │                  │
│  │ Grader   │      │Inference │      │ Manager  │                  │
│  └──────────┘      └──────────┘      └──────────┘                  │
│         │                 │                 │                        │
│         └─────────────────┴─────────────────┘                        │
│                           │                                          │
│         ┌─────────────────┼─────────────────┐                        │
│         ▼                 ▼                 ▼                        │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐                  │
│  │  Memori  │      │  Tools   │      │  HTML    │                  │
│  │  Engine  │      │ (Search) │      │  Utils   │                  │
│  └──────────┘      └──────────┘      └──────────┘                  │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                Supabase (PostgreSQL + Auth + pgvector)               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │   Users     │  │  Roadmaps   │  │   Quizzes   │                 │
│  │  Memories   │  │ Milestones  │  │  Attempts   │                 │
│  │  Sessions   │  │  Progress   │  │Achievements │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
porte-hobe-ai/
│
├── frontend/                        # Next.js 15 Application
│   ├── app/                         # App Router Pages (50+)
│   │   ├── (home)/                  # Public Route Group
│   │   │   ├── page.tsx             # Landing page
│   │   │   ├── login/               # Login page
│   │   │   └── signup/              # Signup page
│   │   │
│   │   ├── dashboard/               # Protected Route Group
│   │   │   ├── page.tsx             # Dashboard home
│   │   │   │
│   │   │   ├── chat/                # AI Tutor Chat
│   │   │   │   ├── page.tsx         # Main chat interface
│   │   │   │   ├── history/         # Chat history
│   │   │   │   └── quick/           # Quick ask
│   │   │   │
│   │   │   ├── quiz/                # Quiz System
│   │   │   │   ├── page.tsx         # Quiz library
│   │   │   │   ├── [quizId]/        # Take quiz
│   │   │   │   └── [quizId]/results/# Quiz results
│   │   │   │
│   │   │   ├── learning/            # Learning Paths
│   │   │   │   ├── path/            # Visual roadmap
│   │   │   │   ├── current/         # Current topics
│   │   │   │   └── completed/       # Completed topics
│   │   │   │
│   │   │   ├── my-progress/         # Progress Tracking
│   │   │   │   ├── roadmaps/        # User roadmaps
│   │   │   │   └── topics/          # Topic progress
│   │   │   │
│   │   │   ├── practice/            # Practice Hub
│   │   │   │   ├── page.tsx         # Practice home
│   │   │   │   ├── exercises/       # All exercises
│   │   │   │   ├── challenges/      # Coding challenges
│   │   │   │   ├── quizzes/         # Quiz practice
│   │   │   │   └── history/         # Past attempts
│   │   │   │
│   │   │   ├── achievements/        # Gamification
│   │   │   │   ├── page.tsx         # Achievements home
│   │   │   │   ├── badges/          # Badge collection
│   │   │   │   ├── milestones/      # Milestone view
│   │   │   │   └── certificates/    # Certificates
│   │   │   │
│   │   │   ├── goals/               # Study Goals
│   │   │   │   ├── page.tsx         # Active goals
│   │   │   │   ├── new/             # Create goal
│   │   │   │   └── history/         # Goal history
│   │   │   │
│   │   │   ├── progress/            # Analytics
│   │   │   │   ├── page.tsx         # Overall stats
│   │   │   │   ├── topics/          # Topic analytics
│   │   │   │   ├── performance/     # Performance metrics
│   │   │   │   └── time/            # Time tracking
│   │   │   │
│   │   │   ├── resources/           # Resource Library
│   │   │   │   ├── page.tsx         # Library home
│   │   │   │   ├── saved/           # Saved materials
│   │   │   │   ├── notes/           # Notes
│   │   │   │   ├── bookmarks/       # Bookmarks
│   │   │   │   └── files/           # Uploaded files
│   │   │   │
│   │   │   ├── settings/            # User Settings
│   │   │   │   ├── profile/         # Profile settings
│   │   │   │   ├── preferences/     # Preferences
│   │   │   │   └── privacy/         # Privacy settings
│   │   │   │
│   │   │   ├── topics/              # Topic Browser
│   │   │   └── streak/              # Streak Calendar
│   │   │
│   │   ├── api/                     # API Proxy Routes
│   │   │   ├── chat/                # Chat endpoints
│   │   │   ├── quizzes/             # Quiz endpoints
│   │   │   ├── roadmaps/            # Roadmap endpoints
│   │   │   ├── goals/               # Goals endpoints
│   │   │   ├── achievements/        # Achievement endpoints
│   │   │   ├── practice/            # Practice endpoints
│   │   │   ├── resources/           # Resource endpoints
│   │   │   ├── memory/              # Memory endpoints
│   │   │   └── progress/            # Progress endpoints
│   │   │
│   │   ├── layout.tsx               # Root layout
│   │   └── globals.css              # Global styles
│   │
│   ├── components/                  # React Components
│   │   ├── ui/                      # shadcn/ui components (30+)
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── progress.tsx
│   │   │   └── ... (25+ more)
│   │   │
│   │   ├── quiz/                    # Quiz Components
│   │   │   ├── QuestionForm.tsx     # Question-by-question UI
│   │   │   ├── QuizPopup.tsx        # In-chat quiz modal
│   │   │   ├── QuizQuestion.tsx     # Question renderer
│   │   │   └── QuizResults.tsx      # Results display
│   │   │
│   │   ├── roadmap/                 # Roadmap Components
│   │   │   ├── QuizTriggerDialog.tsx # Quiz unlock notification
│   │   │   ├── MilestoneItem.tsx    # Milestone display
│   │   │   ├── PhaseCard.tsx        # Phase visualization
│   │   │   └── RoadmapTimeline.tsx  # Timeline view
│   │   │
│   │   ├── achievements/            # Achievement Components
│   │   │   ├── AchievementCard.tsx
│   │   │   └── LevelProgress.tsx
│   │   │
│   │   ├── goals/                   # Goal Components
│   │   │   ├── CreateGoalDialog.tsx
│   │   │   └── GoalCard.tsx
│   │   │
│   │   ├── shared/                  # Shared Components
│   │   │   ├── Badge.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   ├── ErrorState.tsx
│   │   │   ├── LoadingState.tsx
│   │   │   ├── PageHeader.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   └── StatsCard.tsx
│   │   │
│   │   ├── auth-provider.tsx        # Auth context
│   │   ├── theme-provider.tsx       # Theme context
│   │   ├── app-sidebar.tsx          # Navigation sidebar
│   │   ├── ChatPage.tsx             # Main chat UI
│   │   ├── TopicBrowser.tsx         # Topic selection
│   │   ├── ProgressCard.tsx         # Stats display
│   │   └── FileDrop.tsx             # File upload
│   │
│   ├── lib/                         # Utilities
│   │   ├── api/                     # API Client Functions
│   │   │   ├── quizzes.ts
│   │   │   ├── roadmaps.ts
│   │   │   ├── goals.ts
│   │   │   ├── achievements.ts
│   │   │   ├── practice.ts
│   │   │   ├── resources.ts
│   │   │   └── progress.ts
│   │   │
│   │   ├── supabase/
│   │   │   ├── client.ts            # Browser Supabase client
│   │   │   ├── server.ts            # Server Supabase client
│   │   │   └── middleware.ts        # Auth middleware
│   │   │
│   │   └── utils.ts                 # Helper functions
│   │
│   ├── hooks/                       # Custom Hooks
│   │   ├── use-mobile.ts
│   │   ├── useQuiz.ts               # Quiz management
│   │   ├── useRoadmap.ts            # Roadmap management
│   │   ├── useGoals.ts              # Goals management
│   │   ├── useAchievements.ts       # Achievements tracking
│   │   ├── usePractice.ts           # Practice exercises
│   │   ├── useResources.ts          # Resource management
│   │   ├── useProgress.ts           # Progress tracking
│   │   └── useStartLearning.ts      # Learning initiation
│   │
│   ├── types/                       # TypeScript Types
│   │   ├── quiz.ts                  # Quiz types (211 lines)
│   │   ├── roadmap.ts               # Roadmap types (132 lines)
│   │   ├── achievements.ts          # Achievement types
│   │   ├── goals.ts                 # Goal types
│   │   ├── practice.ts              # Practice types
│   │   ├── resources.ts             # Resource types
│   │   └── progress.ts              # Progress types
│   │
│   ├── public/                      # Static Assets
│   │
│   ├── package.json                 # Dependencies
│   ├── tsconfig.json                # TypeScript config
│   ├── next.config.ts               # Next.js config
│   ├── tailwind.config.ts           # Tailwind config
│   ├── components.json              # shadcn config
│   └── README.md                    # Frontend docs
│
├── server/                          # FastAPI Backend
│   ├── main.py                      # FastAPI app + endpoints (857 lines)
│   │
│   ├── Core AI Agents/
│   ├── agent.py                     # TutorAgent (LangGraph) (652 lines)
│   ├── quiz_generator.py            # AI quiz generation (444 lines)
│   ├── quiz_grader.py               # AI grading (563 lines)
│   ├── roadmap_agent.py             # Roadmap generation (404 lines)
│   ├── progress_inference.py        # Milestone detection (350 lines)
│   ├── mcp_agents.py                # MCP agents (scraper, file, math, vector)
│   │
│   ├── API Routers/
│   ├── quiz_router.py               # Quiz CRUD & generation (668 lines)
│   ├── roadmap_router.py            # Roadmap management (846 lines)
│   ├── achievement_router.py        # Achievement system (673 lines)
│   ├── goal_router.py               # Study goals (451 lines)
│   ├── practice_router.py           # Practice exercises (731 lines)
│   ├── resource_router.py           # Resource library (612 lines)
│   ├── file_router.py               # File upload/processing (12KB)
│   ├── topic_router.py              # Topic management (13KB)
│   ├── progress_router.py           # Progress tracking (12KB)
│   │
│   ├── Core Systems/
│   ├── session_manager.py           # Chat session management (400 lines)
│   ├── memori_engine.py             # Advanced memory (419 lines)
│   ├── embedding_engine.py          # Vector search (legacy support)
│   ├── dynamic_prompts.py           # Dynamic prompt generation (612 lines)
│   ├── intent_classifier.py         # Intent detection (493 lines)
│   ├── specialist_models.py         # Task-specific LLMs (498 lines)
│   │
│   ├── Utilities/
│   ├── web_crawler.py               # Advanced web crawling (20KB)
│   ├── html_utils.py                # HTML sanitization (8KB)
│   ├── prompts.py                   # System prompts (7KB)
│   ├── tools.py                     # Tool definitions (3KB)
│   ├── auth.py                      # JWT authentication (1.5KB)
│   ├── config.py                    # Environment config (3KB)
│   ├── rate_limit.py                # Rate limiting (1.9KB)
│   ├── start_server.py              # Server startup (0.9KB)
│   │
│   ├── Database Migrations/
│   ├── quiz_progress_migration.sql  # Quiz & roadmap tables (22KB)
│   ├── chat_roadmap_integration_enhancement.sql # Session linking (16KB)
│   ├── chat_history_migration.sql   # Message persistence (6.3KB)
│   ├── student_features_migration.sql # Goals, achievements, etc (16KB)
│   ├── database_migrations.sql      # Original schema (17KB)
│   │
│   ├── Documentation/
│   ├── QUIZ_PROGRESS_IMPLEMENTATION_PLAN.md # Quiz/roadmap spec (1,095 lines)
│   ├── BACKEND_IMPLEMENTATION_SUMMARY.md # Backend features (20KB)
│   ├── FRONTEND_IMPLEMENTATION_PLAN.md # Frontend guide (25KB)
│   ├── DYNAMIC_PROMPTS_EXAMPLES.md
│   ├── INTENT_CLASSIFICATION.md
│   ├── MCP_MULTI_MODEL_ARCHITECTURE.md
│   ├── MEMORI_INTEGRATION.md
│   ├── NEXT_STEPS.md
│   │
│   ├── storage/                     # Persistent Data
│   │   ├── uploads/                 # User uploads (PDFs, images)
│   │   └── cache/                   # Cached data
│   │
│   ├── requirements.txt             # Python dependencies (49 packages)
│   └── .env.example                 # Environment template
│
├── .git/                            # Git repository
├── .gitignore                       # Git ignore rules
└── CLAUDE.md                        # This file
```

---

## Development Workflows

### Setting Up Development Environment

#### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local

# Edit .env.local with:
# NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
# NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
# NEXT_PUBLIC_FASTAPI_URL=http://localhost:8000

# Start development server
npm run dev  # Runs on http://localhost:3000
```

#### Backend Setup

```bash
# Navigate to server
cd server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Ollama and pull model
ollama pull qwen2.5:3b-instruct-q5_K_M

# Create environment file
cp .env.example .env

# Edit .env with:
# SUPABASE_URL=your_supabase_url
# SUPABASE_SERVICE_KEY=your_service_key
# TAVILY_API_KEY=your_tavily_key

# Start server
python start_server.py  # Runs on http://localhost:8000
```

#### Database Setup

```bash
# 1. Create Supabase project at supabase.com
# 2. Enable pgvector extension in SQL Editor:
CREATE EXTENSION IF NOT EXISTS vector;

# 3. Run migrations in order:
# - database_migrations.sql
# - quiz_progress_migration.sql
# - chat_history_migration.sql
# - chat_roadmap_integration_enhancement.sql
# - student_features_migration.sql
```

### Development Commands

#### Frontend

```bash
npm run dev        # Start dev server (port 3000)
npm run build      # Production build
npm run start      # Run production build
npm run lint       # Run ESLint
```

#### Backend

```bash
python start_server.py              # Start with auto-reload
python main.py                      # Direct FastAPI start
uvicorn main:app --reload           # Alternative start
pytest                              # Run tests
```

### Git Workflow

**Current Branch:** `claude/claude-md-mim9s33bi6i1zriz-01HRRJcXSEeVHweMtBx7pbz8`

```bash
# Check status
git status

# Create feature branch (must start with 'claude/')
git checkout -b claude/feature-name-sessionid

# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add new feature"

# Push to remote (MUST use -u flag)
git push -u origin claude/feature-name-sessionid

# If push fails due to network, retry with exponential backoff
# (2s, 4s, 8s, 16s intervals)
```

**Important:** Branch names MUST start with `claude/` and end with matching session ID, otherwise push will fail with 403.

---

## Key Conventions & Patterns

### Naming Conventions

#### Frontend (TypeScript/React)

```typescript
// Files: PascalCase for components, camelCase for utilities
ChatPage.tsx
QuizQuestion.tsx
use-mobile.ts
useQuiz.ts

// Components: PascalCase
export function ChatPage() { }
export const QuizResults = () => { }

// Hooks: camelCase with 'use' prefix
export function useMobile() { }
export function useQuiz() { }

// Variables/Functions: camelCase
const handleQuizSubmit = () => { }
const [quizAttempt, setQuizAttempt] = useState(null)

// Interfaces/Types: PascalCase
interface ConversationQuiz { }
type QuizDifficulty = 'beginner' | 'intermediate' | 'advanced'

// Constants: UPPER_SNAKE_CASE
const MAX_QUIZ_ATTEMPTS = 3
const PASSING_SCORE = 70
```

#### Backend (Python)

```python
# Files: snake_case
quiz_generator.py
progress_inference.py
roadmap_router.py

# Classes: PascalCase
class QuizGenerator:
class ProgressInferenceEngine:
class SessionManager:

# Functions/Methods: snake_case
def generate_quiz():
def detect_milestone_completion():
async def create_roadmap():

# Constants: UPPER_SNAKE_CASE
CONFIDENCE_THRESHOLD = 0.75
MAX_RETRIES = 3
DEFAULT_QUIZ_QUESTIONS = 5

# Variables: snake_case (descriptive)
quiz_attempt = None
milestone_progress = {}
session_id = uuid.uuid4()
```

#### Database (Supabase)

```sql
-- Tables: snake_case
learning_roadmaps
conversation_quizzes
milestone_progress
chat_sessions

-- Columns: snake_case
created_at
user_id
roadmap_id
completion_confidence

-- Indexes: {table}_{column}_idx
learning_roadmaps_user_id_idx
quiz_attempts_quiz_id_idx
```

### Code Patterns

#### Frontend Patterns

**1. API Route Pattern (Proxy to FastAPI)**

```typescript
// app/api/quizzes/route.ts
import { createClient } from '@/lib/supabase/server'

export async function POST(request: Request) {
  const supabase = await createClient()

  // Verify authentication
  const { data: { user }, error } = await supabase.auth.getUser()
  if (error || !user) {
    return new Response('Unauthorized', { status: 401 })
  }

  // Get session token
  const { data: { session } } = await supabase.auth.getSession()

  // Proxy to FastAPI
  const response = await fetch(`${process.env.NEXT_PUBLIC_FASTAPI_URL}/api/quizzes`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session?.access_token}`
    },
    body: JSON.stringify(await request.json())
  })

  const result = await response.json()
  return Response.json(result)
}
```

**2. Quiz Hook Pattern**

```typescript
// hooks/useQuiz.ts
import { useState, useEffect } from 'react'
import { ConversationQuiz, QuizAttempt } from '@/types/quiz'

export function useQuiz(quizId: string) {
  const [quiz, setQuiz] = useState<ConversationQuiz | null>(null)
  const [attempt, setAttempt] = useState<QuizAttempt | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadQuiz() {
      const response = await fetch(`/api/quizzes/${quizId}`)
      const data = await response.json()
      setQuiz(data)
      setLoading(false)
    }
    loadQuiz()
  }, [quizId])

  const startAttempt = async () => {
    const response = await fetch(`/api/quizzes/${quizId}/attempt`, {
      method: 'POST'
    })
    const data = await response.json()
    setAttempt(data)
  }

  return { quiz, attempt, loading, startAttempt }
}
```

**3. Streaming Chat with Quiz Triggers**

```typescript
// Enhanced SSE handling
const eventSource = new EventSource('/api/chat')

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data)

  switch (data.type) {
    case 'thinking':
      setThinkingContent(data.content)
      break
    case 'response':
      setResponse(prev => prev + data.content)
      break
    case 'quiz_trigger':
      // Show quiz notification
      setShowQuizDialog(true)
      setTriggeredQuiz(data.quiz)
      break
    case 'milestone_update':
      // Update milestone progress
      updateMilestoneProgress(data.milestone)
      break
    case 'done':
      eventSource.close()
      break
  }
}
```

#### Backend Patterns

**1. Quiz Generation Pattern**

```python
# quiz_generator.py
from langchain_core.messages import SystemMessage, HumanMessage

class QuizGenerator:
    def __init__(self):
        self.llm = ChatOllama(model="qwen2.5:3b-instruct-q5_K_M")

    async def generate_from_conversation(
        self,
        conversation_messages: List[dict],
        topic: str,
        difficulty: str = "intermediate",
        num_questions: int = 5
    ) -> dict:
        """Generate quiz from conversation context"""

        # Build context
        context = self._build_context(conversation_messages)

        # Generate questions
        prompt = f"""Generate {num_questions} {difficulty} questions about {topic}.

Context from conversation:
{context}

Return JSON with questions array."""

        response = await self.llm.ainvoke([
            SystemMessage(content=QUIZ_GENERATION_PROMPT),
            HumanMessage(content=prompt)
        ])

        # Parse and validate
        quiz_data = json.loads(response.content)
        return self._validate_quiz(quiz_data)
```

**2. Progress Inference Pattern**

```python
# progress_inference.py
class ProgressInferenceEngine:
    def __init__(self):
        self.llm = ChatOllama(model="qwen2.5:3b-instruct-q5_K_M")
        self.confidence_threshold = 0.75

    async def analyze_milestone_progress(
        self,
        milestone_info: dict,
        conversation_messages: List[dict]
    ) -> dict:
        """Detect milestone completion from conversation"""

        # Analyze conversation
        prompt = f"""Analyze if the student has completed this milestone:

Milestone: {milestone_info['title']}
Description: {milestone_info['description']}

Recent conversation:
{self._format_messages(conversation_messages[-10:])}

Determine:
1. Is the milestone completed? (yes/no)
2. Confidence level (0.0-1.0)
3. Evidence from conversation
4. Learning gaps (if any)

Return JSON."""

        response = await self.llm.ainvoke([
            SystemMessage(content=PROGRESS_INFERENCE_PROMPT),
            HumanMessage(content=prompt)
        ])

        analysis = json.loads(response.content)

        # Auto-complete if confidence is high
        if analysis['confidence'] >= self.confidence_threshold:
            await self._auto_complete_milestone(milestone_info['id'], analysis)

        return analysis
```

**3. Session Management Pattern**

```python
# session_manager.py
class SessionManager:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.max_retries = 3

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict = None
    ):
        """Save message with retry logic"""

        for attempt in range(self.max_retries):
            try:
                result = self.supabase.table("chat_messages").insert({
                    "session_id": session_id,
                    "role": role,
                    "content": content,
                    "metadata": metadata or {}
                }).execute()

                # Update session message count
                await self._increment_message_count(session_id)
                return result.data[0]

            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
```

**4. Protected Endpoint with Rate Limiting**

```python
# quiz_router.py
from auth import get_current_user
from rate_limit import limit_user

@router.post("/api/quizzes/generate")
async def generate_quiz(
    request: QuizGenerationRequest,
    user = Depends(get_current_user),
    _limit = Depends(limit_user)
):
    user_id = user.get("sub")

    # Generate quiz using AI agent
    quiz = await quiz_generator.generate_from_conversation(
        conversation_messages=request.conversation_messages,
        topic=request.topic,
        difficulty=request.difficulty,
        num_questions=request.num_questions
    )

    # Store in database
    result = supabase.table("conversation_quizzes").insert({
        "user_id": user_id,
        "conversation_id": request.conversation_id,
        "roadmap_id": request.roadmap_id,
        **quiz
    }).execute()

    return result.data[0]
```

**5. Streaming Response with Events**

```python
# main.py
async def chat_event_generator(
    request_id: str,
    user_id: str,
    message: str,
    session_id: str
):
    """Generate SSE events for chat"""

    # Phase 1: Thinking
    yield f"data: {json.dumps({'type': 'thinking', 'content': 'Analyzing...'})}\n\n"

    # Phase 2: Response
    async for chunk in tutor_agent.stream_response(message, user_id):
        yield f"data: {json.dumps({'type': 'response', 'content': chunk})}\n\n"

    # Check for milestone completion
    milestone_update = await progress_inference.check_milestones(session_id)
    if milestone_update:
        yield f"data: {json.dumps({'type': 'milestone_update', 'milestone': milestone_update})}\n\n"

    # Check for quiz trigger
    quiz = await check_quiz_trigger(session_id)
    if quiz:
        yield f"data: {json.dumps({'type': 'quiz_trigger', 'quiz': quiz})}\n\n"

    # Done
    yield f"data: {json.dumps({'type': 'done', 'request_id': request_id})}\n\n"
```

### Error Handling Patterns

#### Frontend

```typescript
// Error handling with toast notifications
import { toast } from 'sonner'

async function submitQuizAnswer(answerId: string, answer: any) {
  try {
    const response = await fetch(`/api/quizzes/attempt/${attemptId}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answer_id: answerId, answer })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Submission failed')
    }

    const result = await response.json()
    toast.success('Answer submitted!')
    return result

  } catch (error) {
    console.error('Quiz submission error:', error)
    toast.error(error instanceof Error ? error.message : 'Something went wrong')
    throw error
  }
}
```

#### Backend

```python
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

@router.post("/api/quizzes/{quiz_id}/attempt")
async def start_quiz_attempt(
    quiz_id: str,
    user = Depends(get_current_user)
):
    user_id = user.get("sub")

    try:
        # Check if quiz exists
        quiz = supabase.table("conversation_quizzes")\
            .select("*")\
            .eq("id", quiz_id)\
            .execute()

        if not quiz.data:
            raise HTTPException(status_code=404, detail="Quiz not found")

        # Check attempts limit
        attempts = supabase.table("quiz_attempts")\
            .select("*")\
            .eq("quiz_id", quiz_id)\
            .eq("user_id", user_id)\
            .execute()

        if len(attempts.data) >= quiz.data[0]["attempts_allowed"]:
            raise HTTPException(
                status_code=403,
                detail="Maximum attempts reached"
            )

        # Create attempt
        attempt = supabase.table("quiz_attempts").insert({
            "user_id": user_id,
            "quiz_id": quiz_id,
            "attempt_number": len(attempts.data) + 1,
            "status": "in_progress"
        }).execute()

        return attempt.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating quiz attempt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## Critical Files Reference

### Configuration Files

| File | Purpose | Key Contents |
|------|---------|--------------|
| `frontend/package.json` | Frontend dependencies | Next.js 15.5.2, React 19, Zustand, Supabase |
| `frontend/tsconfig.json` | TypeScript config | Strict mode, path aliases (@/*) |
| `frontend/next.config.ts` | Next.js config | Image domains, redirects |
| `frontend/components.json` | shadcn/ui config | Component aliases, styling |
| `server/requirements.txt` | Backend dependencies | FastAPI, LangChain, Supabase, PyMuPDF |
| `server/config.py` | Environment setup | Supabase client, env vars |

### Entry Points

| File | Purpose |
|------|---------|
| `frontend/app/layout.tsx` | Root layout with providers |
| `frontend/middleware.ts` | Auth middleware for route protection |
| `server/main.py` | FastAPI application with 9 routers |
| `server/start_server.py` | Server startup script |

### Core AI Agents

| File | Lines | Purpose |
|------|-------|---------|
| `server/agent.py` | 652 | TutorAgent with LangGraph state machine |
| `server/quiz_generator.py` | 444 | AI-powered quiz generation from context |
| `server/quiz_grader.py` | 563 | Intelligent grading with feedback |
| `server/roadmap_agent.py` | 404 | Personalized learning roadmap creation |
| `server/progress_inference.py` | 350 | Auto milestone completion detection |
| `server/session_manager.py` | 400 | Chat-roadmap-quiz integration |
| `server/mcp_agents.py` | ~500 | MCP agents (scraper, file, math, vector) |

### API Routers

| File | Lines | Purpose |
|------|-------|---------|
| `server/quiz_router.py` | 668 | Quiz CRUD, generation, attempts, grading |
| `server/roadmap_router.py` | 846 | Roadmap generation, milestone tracking |
| `server/achievement_router.py` | 673 | Achievement system with 17+ badges |
| `server/goal_router.py` | 451 | Study goals CRUD and tracking |
| `server/practice_router.py` | 731 | Practice exercises and challenges |
| `server/resource_router.py` | 612 | Resource library management |
| `server/file_router.py` | ~500 | File upload/processing endpoints |
| `server/topic_router.py` | ~550 | Topic management endpoints |
| `server/progress_router.py` | ~500 | Progress tracking endpoints |

### Core Systems

| File | Lines | Purpose |
|------|-------|---------|
| `server/memori_engine.py` | 419 | Advanced memory management with vector search |
| `server/dynamic_prompts.py` | 612 | Context-aware prompt generation |
| `server/intent_classifier.py` | 493 | LLM-based user intent detection |
| `server/specialist_models.py` | 498 | Task-specific LLM routing |
| `server/html_utils.py` | ~300 | HTML sanitization and generation |
| `server/prompts.py` | ~250 | System prompts for all agents |
| `server/auth.py` | ~150 | JWT authentication |
| `server/rate_limit.py` | ~190 | Per-user rate limiting |

### Frontend Components

| Component Group | Key Files | Purpose |
|----------------|-----------|---------|
| Quiz Components | QuestionForm, QuizPopup, QuizQuestion, QuizResults | Quiz taking and results |
| Roadmap Components | QuizTriggerDialog, MilestoneItem, PhaseCard, RoadmapTimeline | Learning path visualization |
| Achievement Components | AchievementCard, LevelProgress | Gamification display |
| Goal Components | CreateGoalDialog, GoalCard | Study goals management |
| Shared Components | EmptyState, ErrorState, LoadingState, PageHeader, ProgressBar, StatsCard | Reusable UI patterns |

---

## Common Tasks Guide

### Task 1: Add a New Quiz Question Type

**Backend:**

```python
# quiz_generator.py - Add new question type

QUESTION_TYPES = [
    "multiple_choice",
    "true_false",
    "short_answer",
    "code",
    "fill_blank"  # NEW TYPE
]

def _generate_fill_blank_question(self, topic: str) -> dict:
    """Generate fill-in-the-blank question"""

    prompt = f"""Generate a fill-in-the-blank question about {topic}.

Return JSON:
{{
    "question": "The _____ keyword is used to...",
    "blanks": ["correct", "answer"],
    "hints": "Optional hint",
    "explanation": "Why this is correct"
}}"""

    # Generate and validate
    return self._validate_question(response)
```

**Frontend:**

```typescript
// components/quiz/QuizQuestion.tsx - Add renderer

function renderFillBlankQuestion(question: QuizQuestion) {
  const [answers, setAnswers] = useState<string[]>(
    Array(question.blanks.length).fill('')
  )

  return (
    <div className="space-y-4">
      <p className="text-lg">{question.question}</p>
      {question.blanks.map((_, index) => (
        <Input
          key={index}
          placeholder={`Blank ${index + 1}`}
          value={answers[index]}
          onChange={(e) => {
            const newAnswers = [...answers]
            newAnswers[index] = e.target.value
            setAnswers(newAnswers)
          }}
        />
      ))}
    </div>
  )
}
```

### Task 2: Add a New Achievement

**Backend:**

```python
# achievement_router.py - Define achievement

ACHIEVEMENTS = {
    # ... existing achievements

    "quiz_master": {
        "id": "quiz_master",
        "title": "Quiz Master",
        "description": "Score 100% on 5 different quizzes",
        "category": "quiz",
        "rarity": "legendary",
        "xp_reward": 500,
        "icon": "trophy",
        "requirement": {
            "type": "quiz_perfect_scores",
            "count": 5
        }
    }
}

async def check_quiz_achievements(user_id: str, quiz_attempt: dict):
    """Check if quiz unlocks achievements"""

    # Check for perfect score
    if quiz_attempt["percentage_score"] == 100:
        # Count perfect scores
        perfect_scores = supabase.table("quiz_attempts")\
            .select("id")\
            .eq("user_id", user_id)\
            .eq("percentage_score", 100)\
            .execute()

        if len(perfect_scores.data) >= 5:
            await unlock_achievement(user_id, "quiz_master")
```

**Database:**

```sql
-- Add to student_features_migration.sql or create new migration

INSERT INTO achievements (id, title, description, category, rarity, xp_reward, icon, requirement)
VALUES (
    'quiz_master',
    'Quiz Master',
    'Score 100% on 5 different quizzes',
    'quiz',
    'legendary',
    500,
    'trophy',
    '{"type": "quiz_perfect_scores", "count": 5}'::jsonb
);
```

### Task 3: Implement Custom Progress Inference Rule

```python
# progress_inference.py - Add custom rule

class ProgressInferenceEngine:

    async def analyze_milestone_progress(
        self,
        milestone_info: dict,
        conversation_messages: List[dict]
    ) -> dict:
        """Detect milestone completion with custom rules"""

        # Standard AI analysis
        ai_analysis = await self._ai_analyze(milestone_info, conversation_messages)

        # Apply custom rules
        custom_analysis = await self._apply_custom_rules(
            milestone_info,
            conversation_messages,
            ai_analysis
        )

        # Combine results
        final_confidence = max(ai_analysis['confidence'], custom_analysis['confidence'])

        return {
            "is_completed": final_confidence >= self.confidence_threshold,
            "confidence": final_confidence,
            "evidence": ai_analysis['evidence'] + custom_analysis['evidence'],
            "method": "hybrid"
        }

    async def _apply_custom_rules(
        self,
        milestone_info: dict,
        messages: List[dict],
        ai_analysis: dict
    ) -> dict:
        """Apply domain-specific completion rules"""

        # Example: Code milestone requires code in conversation
        if milestone_info.get('type') == 'coding':
            has_code = any('```' in msg['content'] for msg in messages)
            if has_code:
                return {
                    "confidence": 0.9,
                    "evidence": ["Student wrote code in conversation"]
                }

        # Example: Math milestone requires calculation
        if milestone_info.get('type') == 'math':
            has_calculation = any(
                any(char in msg['content'] for char in '+=/*^')
                for msg in messages
            )
            if has_calculation:
                return {
                    "confidence": 0.85,
                    "evidence": ["Student performed calculations"]
                }

        return {"confidence": 0.0, "evidence": []}
```

### Task 4: Create a Custom Roadmap Template

```python
# roadmap_agent.py - Add template

ROADMAP_TEMPLATES = {
    "web_development_bootcamp": {
        "title": "Web Development Bootcamp",
        "domain": "programming",
        "phases": [
            {
                "id": "phase_1",
                "title": "HTML & CSS Fundamentals",
                "order": 1,
                "milestones": [
                    {
                        "id": "html_basics",
                        "title": "HTML Structure",
                        "type": "lesson",
                        "estimated_duration": 120,
                        "content": "Learn HTML tags, attributes, semantic HTML"
                    },
                    {
                        "id": "html_quiz",
                        "title": "HTML Knowledge Check",
                        "type": "quiz",
                        "trigger_condition": "html_basics_completed"
                    },
                    # ... more milestones
                ]
            },
            # ... more phases
        ]
    }
}

async def generate_from_template(
    template_id: str,
    user_id: str,
    customization: dict = None
) -> dict:
    """Generate roadmap from template with customization"""

    template = ROADMAP_TEMPLATES[template_id]

    # Customize based on user level
    if customization and customization.get('skip_basics'):
        template['phases'] = [
            p for p in template['phases']
            if p.get('level') != 'beginner'
        ]

    # Store roadmap
    roadmap = supabase.table("learning_roadmaps").insert({
        "user_id": user_id,
        "title": template['title'],
        "domain": template['domain'],
        "roadmap_data": {"phases": template['phases']},
        "total_milestones": self._count_milestones(template['phases'])
    }).execute()

    return roadmap.data[0]
```

### Task 5: Add New Practice Exercise Type

```python
# practice_router.py

@router.post("/api/practice/exercises/create")
async def create_exercise(
    exercise: ExerciseCreate,
    user = Depends(get_current_user),
    _limit = Depends(limit_user)
):
    """Create new practice exercise"""

    # Validate exercise type
    ALLOWED_TYPES = [
        "coding_challenge",
        "debugging",
        "code_review",
        "algorithm_design",
        "system_design"  # NEW TYPE
    ]

    if exercise.type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Invalid exercise type")

    # Generate exercise content using AI
    if exercise.type == "system_design":
        content = await generate_system_design_exercise(
            topic=exercise.topic,
            difficulty=exercise.difficulty
        )

    # Store exercise
    result = supabase.table("practice_exercises").insert({
        "user_id": user.get("sub"),
        "type": exercise.type,
        "topic": exercise.topic,
        "difficulty": exercise.difficulty,
        "content": content,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    return result.data[0]

async def generate_system_design_exercise(topic: str, difficulty: str) -> dict:
    """Generate system design exercise"""

    llm = ChatOllama(model="qwen2.5:3b-instruct-q5_K_M")

    prompt = f"""Create a system design exercise for {topic} at {difficulty} level.

Include:
1. Problem statement
2. Requirements (functional and non-functional)
3. Constraints
4. Evaluation criteria
5. Hints

Return JSON."""

    response = await llm.ainvoke([
        SystemMessage(content=SYSTEM_DESIGN_PROMPT),
        HumanMessage(content=prompt)
    ])

    return json.loads(response.content)
```

---

## API Endpoints

### Authentication

All protected endpoints require JWT token in `Authorization: Bearer <token>` header.

### Chat Endpoints

#### POST /api/chat
Streaming chat with AI tutor (SSE).

**Request:**
```json
{
  "message": "Explain bubble sort",
  "history": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! How can I help?"}
  ],
  "session_id": "uuid",
  "roadmap_id": "uuid (optional)",
  "topic_id": "programming_basics_001",
  "attachments": ["file_id_123"],
  "enable_web_search": false,
  "enable_math": false
}
```

**Response (SSE Stream):**
```
data: {"type": "thinking", "content": "Analyzing question..."}

data: {"type": "response", "content": "Bubble sort is..."}

data: {"type": "milestone_update", "milestone": {...}}

data: {"type": "quiz_trigger", "quiz": {...}}

data: {"type": "done", "request_id": "uuid", "session_id": "uuid"}
```

#### POST /api/chat/simple
Non-streaming chat response.

#### GET /api/chat/history?user_id={user_id}&limit=20
Get conversation history.

#### POST /api/chat/save-message
Save individual message to conversation.

#### DELETE /api/chat/history/{conversation_id}
Delete entire conversation.

### Quiz Endpoints

#### POST /api/quizzes/generate
Generate AI quiz from conversation.

**Request:**
```json
{
  "conversation_id": "uuid",
  "roadmap_id": "uuid",
  "conversation_messages": [...],
  "topic": "Sorting Algorithms",
  "difficulty": "intermediate",
  "num_questions": 5,
  "question_types": ["multiple_choice", "code"]
}
```

**Response:**
```json
{
  "id": "uuid",
  "title": "Sorting Algorithms Quiz",
  "questions": [
    {
      "id": "q1",
      "type": "multiple_choice",
      "question": "What is the time complexity...",
      "options": ["O(n)", "O(n²)", "O(log n)", "O(n log n)"],
      "correct_answer": "O(n²)",
      "explanation": "..."
    }
  ],
  "total_points": 100,
  "passing_score": 70,
  "estimated_duration": 300
}
```

#### POST /api/quizzes/{quiz_id}/attempt
Start a quiz attempt.

**Response:**
```json
{
  "id": "attempt_uuid",
  "quiz_id": "uuid",
  "attempt_number": 1,
  "started_at": "2025-11-30T10:00:00Z",
  "status": "in_progress"
}
```

#### POST /api/quizzes/attempt/{attempt_id}/submit
Submit answer for AI grading.

**Request:**
```json
{
  "question_id": "q1",
  "answer": "O(n²)"
}
```

**Response:**
```json
{
  "question_id": "q1",
  "is_correct": true,
  "points_earned": 20,
  "feedback": "Correct! Bubble sort has...",
  "partial_credit": 0.0
}
```

#### POST /api/quizzes/attempt/{attempt_id}/complete
Complete quiz and get final results.

**Response:**
```json
{
  "attempt_id": "uuid",
  "total_questions": 5,
  "correct_answers": 4,
  "points_earned": 85,
  "percentage_score": 85.0,
  "passed": true,
  "overall_feedback": "Great job! You showed...",
  "strengths": ["Time complexity analysis", "Code reading"],
  "weaknesses": ["Edge cases"],
  "recommendations": ["Review edge case handling"]
}
```

#### GET /api/quizzes/library?user_id={user_id}
Browse all user quizzes.

#### GET /api/quizzes/conversation/{conversation_id}
Get quizzes for specific conversation.

### Roadmap Endpoints

#### POST /api/roadmaps/generate
Generate personalized learning roadmap.

**Request:**
```json
{
  "title": "Python Mastery",
  "domain": "programming",
  "conversation_id": "uuid",
  "user_level": "beginner",
  "goals": ["Learn web development", "Build projects"],
  "time_commitment": "10 hours/week"
}
```

**Response:**
```json
{
  "id": "uuid",
  "title": "Python Mastery",
  "phases": [
    {
      "id": "phase_1",
      "title": "Python Fundamentals",
      "order": 1,
      "milestones": [
        {
          "id": "m1",
          "title": "Variables and Data Types",
          "type": "lesson",
          "estimated_duration": 120,
          "content": "...",
          "status": "not_started"
        },
        {
          "id": "m2",
          "title": "Variables Quiz",
          "type": "quiz",
          "trigger_condition": "m1_completed",
          "status": "locked"
        }
      ]
    }
  ],
  "total_milestones": 20,
  "estimated_total_time": 2400
}
```

#### GET /api/roadmaps?user_id={user_id}
List user's roadmaps.

#### GET /api/roadmaps/{roadmap_id}
Get roadmap with current progress.

**Response:**
```json
{
  "id": "uuid",
  "title": "Python Mastery",
  "progress_percentage": 45.5,
  "completed_milestones": 9,
  "total_milestones": 20,
  "current_phase_id": "phase_2",
  "current_milestone_id": "m10",
  "phases": [...]
}
```

#### PUT /api/roadmaps/{roadmap_id}/milestone/{milestone_id}
Update milestone progress.

**Request:**
```json
{
  "status": "completed",
  "time_spent": 1800,
  "quiz_passed": true,
  "quiz_score": 92.5
}
```

#### POST /api/roadmaps/{roadmap_id}/adapt
AI-powered roadmap adaptation based on performance.

**Request:**
```json
{
  "reason": "struggling_with_topic",
  "feedback": "Need more practice with loops"
}
```

### Goal Endpoints

#### POST /api/goals
Create study goal.

**Request:**
```json
{
  "title": "Complete 5 quizzes this week",
  "type": "weekly",
  "target": 5,
  "metric": "quizzes_completed",
  "deadline": "2025-12-07T23:59:59Z"
}
```

#### GET /api/goals?user_id={user_id}&type={type}&status={status}
List goals with filters.

#### PATCH /api/goals/{goal_id}
Update goal progress.

#### DELETE /api/goals/{goal_id}
Delete goal.

#### GET /api/goals/stats/summary
Goal statistics and completion rates.

### Achievement Endpoints

#### GET /api/achievements/available?user_id={user_id}
All achievements with user progress.

**Response:**
```json
{
  "achievements": [
    {
      "id": "first_quiz",
      "title": "First Steps",
      "description": "Complete your first quiz",
      "category": "quiz",
      "rarity": "common",
      "xp_reward": 50,
      "unlocked": true,
      "unlocked_at": "2025-11-20T10:00:00Z",
      "progress": 1,
      "required": 1
    },
    {
      "id": "quiz_master",
      "title": "Quiz Master",
      "description": "Score 100% on 5 quizzes",
      "category": "quiz",
      "rarity": "legendary",
      "xp_reward": 500,
      "unlocked": false,
      "progress": 3,
      "required": 5
    }
  ]
}
```

#### GET /api/achievements/unlocked?user_id={user_id}
User's unlocked achievements.

#### POST /api/achievements/check
Check and unlock achievements.

**Request:**
```json
{
  "user_id": "uuid",
  "event_type": "quiz_completed",
  "event_data": {
    "quiz_id": "uuid",
    "score": 100
  }
}
```

#### GET /api/achievements/stats?user_id={user_id}
Achievement stats and level.

**Response:**
```json
{
  "total_achievements": 24,
  "unlocked_achievements": 12,
  "total_xp": 2450,
  "current_level": 5,
  "xp_to_next_level": 550,
  "completion_percentage": 50.0,
  "rarity_breakdown": {
    "common": 8,
    "rare": 3,
    "epic": 1,
    "legendary": 0
  }
}
```

### Practice Endpoints

#### GET /api/practice/exercises?topic={topic}&difficulty={difficulty}
List practice exercises.

#### POST /api/practice/exercises/{id}/submit
Submit solution.

**Request:**
```json
{
  "solution": "def bubble_sort(arr):\n    ...",
  "language": "python"
}
```

**Response:**
```json
{
  "correct": true,
  "test_results": [
    {"test": "Basic sorting", "passed": true},
    {"test": "Edge cases", "passed": true}
  ],
  "feedback": "Excellent solution!",
  "time_complexity": "O(n²)",
  "space_complexity": "O(1)"
}
```

#### GET /api/practice/challenges
Coding challenges.

#### GET /api/practice/history?user_id={user_id}
Past practice attempts.

### Resource Endpoints

#### POST /api/resources
Save resource.

**Request:**
```json
{
  "title": "Python Documentation",
  "type": "link",
  "url": "https://docs.python.org",
  "tags": ["python", "reference"],
  "notes": "Official Python docs"
}
```

#### GET /api/resources?user_id={user_id}&type={type}&tags={tags}
List resources.

#### POST /api/resources/{id}/bookmark
Bookmark resource.

#### POST /api/resources/notes
Create note.

#### GET /api/resources/files
List uploaded files.

### Progress Endpoints

#### GET /api/progress?user_id={user_id}
Get comprehensive learning progress.

**Response:**
```json
{
  "overall_progress": 45.5,
  "roadmaps": [
    {
      "roadmap_id": "uuid",
      "title": "Python Mastery",
      "progress": 60.0,
      "completed_milestones": 12,
      "total_milestones": 20
    }
  ],
  "topics": [
    {
      "topic_id": "programming_basics_001",
      "progress": 80.0,
      "status": "in_progress",
      "time_spent": 1200
    }
  ],
  "quizzes": {
    "total_attempts": 15,
    "passed": 12,
    "average_score": 87.5
  }
}
```

#### GET /api/progress/stats
Overall learning statistics.

**Response:**
```json
{
  "total_roadmaps": 3,
  "completed_roadmaps": 1,
  "total_topics": 50,
  "completed_topics": 22,
  "total_time_minutes": 4800,
  "current_streak": 14,
  "longest_streak": 21,
  "total_achievements": 12,
  "total_xp": 2450,
  "current_level": 5
}
```

#### POST /api/progress/update
Update topic progress.

### Health Endpoints

#### GET /
API root with version info.

#### GET /health
Health check endpoint.

---

## Database Schema

### Supabase Tables

#### auth.users (Built-in)
```sql
id              UUID PRIMARY KEY
email           TEXT UNIQUE
created_at      TIMESTAMPTZ
```

#### learning_roadmaps
```sql
id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4()
user_id                 UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
title                   TEXT NOT NULL
description             TEXT
domain                  TEXT NOT NULL  -- 'programming' or 'math'
roadmap_data            JSONB NOT NULL  -- phases and milestones structure
total_milestones        INTEGER NOT NULL
completed_milestones    INTEGER DEFAULT 0
progress_percentage     FLOAT DEFAULT 0.0
current_phase_id        TEXT
current_milestone_id    TEXT
status                  TEXT DEFAULT 'active'  -- 'active', 'completed', 'paused'
conversation_id         UUID REFERENCES conversations(id)
chat_session_id         UUID REFERENCES chat_sessions(id)
created_at              TIMESTAMPTZ DEFAULT NOW()
updated_at              TIMESTAMPTZ DEFAULT NOW()
completed_at            TIMESTAMPTZ

-- Indexes
learning_roadmaps_user_id_idx ON user_id
learning_roadmaps_status_idx ON status
learning_roadmaps_conversation_id_idx ON conversation_id
```

#### conversation_quizzes
```sql
id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4()
user_id             UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
roadmap_id          UUID REFERENCES learning_roadmaps(id) ON DELETE CASCADE
conversation_id     UUID REFERENCES conversations(id)
title               TEXT NOT NULL
description         TEXT
topic               TEXT NOT NULL
difficulty          TEXT NOT NULL  -- 'beginner', 'intermediate', 'advanced', 'expert'
questions           JSONB NOT NULL  -- array of question objects
total_points        INTEGER NOT NULL
passing_score       INTEGER NOT NULL
attempts_allowed    INTEGER DEFAULT 3
time_limit          INTEGER  -- seconds (optional)
estimated_duration  INTEGER  -- seconds
status              TEXT DEFAULT 'available'  -- 'available', 'locked', 'completed'
phase_id            TEXT
milestone_id        TEXT
trigger_condition   TEXT  -- when quiz should be presented
triggered_at        TIMESTAMPTZ
presented_at        TIMESTAMPTZ
created_at          TIMESTAMPTZ DEFAULT NOW()

-- Indexes
conversation_quizzes_user_id_idx ON user_id
conversation_quizzes_roadmap_id_idx ON roadmap_id
conversation_quizzes_conversation_id_idx ON conversation_id
```

#### quiz_attempts
```sql
id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4()
user_id                     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
quiz_id                     UUID NOT NULL REFERENCES conversation_quizzes(id) ON DELETE CASCADE
roadmap_id                  UUID REFERENCES learning_roadmaps(id)
attempt_number              INTEGER NOT NULL
answers                     JSONB NOT NULL  -- question_id -> answer mapping
total_questions             INTEGER NOT NULL
correct_answers             INTEGER DEFAULT 0
partial_credit_answers      INTEGER DEFAULT 0
points_earned               INTEGER DEFAULT 0
total_points                INTEGER NOT NULL
percentage_score            FLOAT DEFAULT 0.0
overall_feedback            TEXT
strengths                   TEXT[]
weaknesses                  TEXT[]
recommendations             TEXT[]
time_spent                  INTEGER  -- seconds
started_at                  TIMESTAMPTZ DEFAULT NOW()
completed_at                TIMESTAMPTZ
status                      TEXT DEFAULT 'in_progress'  -- 'in_progress', 'completed', 'abandoned'
passed                      BOOLEAN DEFAULT FALSE

-- Indexes
quiz_attempts_user_id_idx ON user_id
quiz_attempts_quiz_id_idx ON quiz_id
quiz_attempts_roadmap_id_idx ON roadmap_id
quiz_attempts_status_idx ON status
```

#### milestone_progress
```sql
id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4()
user_id                 UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
roadmap_id              UUID NOT NULL REFERENCES learning_roadmaps(id) ON DELETE CASCADE
phase_id                TEXT NOT NULL
milestone_id            TEXT NOT NULL
status                  TEXT DEFAULT 'not_started'  -- 'not_started', 'in_progress', 'completed', 'locked', 'skipped'
progress_percentage     FLOAT DEFAULT 0.0
quiz_id                 UUID REFERENCES conversation_quizzes(id)
quiz_passed             BOOLEAN
best_quiz_score         FLOAT
started_at              TIMESTAMPTZ
completed_at            TIMESTAMPTZ
time_spent              INTEGER DEFAULT 0  -- seconds
auto_completed          BOOLEAN DEFAULT FALSE
completion_confidence   FLOAT  -- AI confidence (0.0-1.0)
completion_evidence     TEXT[]  -- evidence from conversation
inference_metadata      JSONB  -- AI analysis data

-- Indexes
milestone_progress_user_id_idx ON user_id
milestone_progress_roadmap_id_idx ON roadmap_id
milestone_progress_status_idx ON status
milestone_progress_unique ON (user_id, roadmap_id, milestone_id) UNIQUE
```

#### chat_sessions
```sql
id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4()
user_id             UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
conversation_id     UUID REFERENCES conversations(id)
roadmap_id          UUID REFERENCES learning_roadmaps(id)  -- NEW: links chat to roadmap
topic_id            TEXT
title               TEXT
message_count       INTEGER DEFAULT 0
started_at          TIMESTAMPTZ DEFAULT NOW()
ended_at            TIMESTAMPTZ
metadata            JSONB

-- Indexes
chat_sessions_user_id_idx ON user_id
chat_sessions_conversation_id_idx ON conversation_id
chat_sessions_roadmap_id_idx ON roadmap_id
```

#### chat_messages
```sql
id              UUID PRIMARY KEY DEFAULT uuid_generate_v4()
session_id      UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE
role            TEXT NOT NULL  -- 'user' or 'assistant'
content         TEXT NOT NULL
message_type    TEXT  -- 'text', 'thinking', 'code', etc.
metadata        JSONB
created_at      TIMESTAMPTZ DEFAULT NOW()

-- Indexes
chat_messages_session_id_idx ON session_id
chat_messages_created_at_idx ON created_at
```

#### conversations (Enhanced)
```sql
id              UUID PRIMARY KEY DEFAULT uuid_generate_v4()
user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
title           TEXT
roadmap_id      UUID REFERENCES learning_roadmaps(id)  -- Optional roadmap link
created_at      TIMESTAMPTZ DEFAULT NOW()
updated_at      TIMESTAMPTZ DEFAULT NOW()

-- Indexes
conversations_user_id_idx ON user_id
conversations_roadmap_id_idx ON roadmap_id
```

#### user_memory
```sql
id              UUID PRIMARY KEY DEFAULT uuid_generate_v4()
user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
content         TEXT NOT NULL
category        TEXT
embedding       VECTOR(768)  -- pgvector
metadata        JSONB
created_at      TIMESTAMPTZ DEFAULT NOW()

-- Indexes
user_memory_user_id_idx ON user_id
user_memory_embedding_idx ON embedding USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
```

#### universal_memory
```sql
id              UUID PRIMARY KEY DEFAULT uuid_generate_v4()
content         TEXT NOT NULL
category        TEXT
embedding       VECTOR(768)
source          TEXT
metadata        JSONB
created_at      TIMESTAMPTZ DEFAULT NOW()

-- Indexes
universal_memory_embedding_idx ON embedding USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
universal_memory_category_idx ON category
```

#### topics
```sql
id              TEXT PRIMARY KEY
title           TEXT NOT NULL
domain          TEXT NOT NULL  -- 'programming' or 'math'
level           TEXT NOT NULL  -- 'beginner', 'intermediate', 'advanced'
description     TEXT
content         TEXT
prerequisites   TEXT[]
estimated_time  INTEGER  -- minutes
metadata        JSONB
created_at      TIMESTAMPTZ DEFAULT NOW()

-- Indexes
topics_domain_idx ON domain
topics_level_idx ON level
```

#### progress
```sql
id              UUID PRIMARY KEY DEFAULT uuid_generate_v4()
user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
topic_id        TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE
progress        FLOAT DEFAULT 0.0  -- 0-100
status          TEXT DEFAULT 'not_started'  -- 'not_started', 'in_progress', 'completed'
time_spent      INTEGER DEFAULT 0  -- seconds
score           FLOAT
last_activity   TIMESTAMPTZ DEFAULT NOW()
created_at      TIMESTAMPTZ DEFAULT NOW()

-- Indexes
progress_user_id_idx ON user_id
progress_topic_id_idx ON topic_id
progress_user_topic_idx ON (user_id, topic_id) UNIQUE
```

#### uploads
```sql
id              UUID PRIMARY KEY DEFAULT uuid_generate_v4()
user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
filename        TEXT NOT NULL
filepath        TEXT NOT NULL
mime_type       TEXT NOT NULL
size            INTEGER NOT NULL
description     TEXT
processed       BOOLEAN DEFAULT FALSE
extracted_text  TEXT
metadata        JSONB
created_at      TIMESTAMPTZ DEFAULT NOW()

-- Indexes
uploads_user_id_idx ON user_id
uploads_created_at_idx ON created_at DESC
```

#### achievements (from student_features_migration.sql)
```sql
id              TEXT PRIMARY KEY
title           TEXT NOT NULL
description     TEXT NOT NULL
category        TEXT NOT NULL  -- 'quiz', 'roadmap', 'streak', 'practice', etc.
rarity          TEXT NOT NULL  -- 'common', 'rare', 'epic', 'legendary'
xp_reward       INTEGER NOT NULL
icon            TEXT
requirement     JSONB  -- conditions to unlock
created_at      TIMESTAMPTZ DEFAULT NOW()
```

#### user_achievements
```sql
id              UUID PRIMARY KEY DEFAULT uuid_generate_v4()
user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
achievement_id  TEXT NOT NULL REFERENCES achievements(id)
unlocked_at     TIMESTAMPTZ DEFAULT NOW()
progress        INTEGER DEFAULT 0
metadata        JSONB

-- Indexes
user_achievements_user_id_idx ON user_id
user_achievements_unique ON (user_id, achievement_id) UNIQUE
```

#### goals
```sql
id              UUID PRIMARY KEY DEFAULT uuid_generate_v4()
user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
title           TEXT NOT NULL
type            TEXT NOT NULL  -- 'daily', 'weekly', 'monthly', 'custom'
target          INTEGER NOT NULL
current         INTEGER DEFAULT 0
metric          TEXT NOT NULL  -- 'quizzes_completed', 'time_spent', 'topics_finished'
status          TEXT DEFAULT 'active'  -- 'active', 'completed', 'failed', 'abandoned'
deadline        TIMESTAMPTZ
created_at      TIMESTAMPTZ DEFAULT NOW()
completed_at    TIMESTAMPTZ

-- Indexes
goals_user_id_idx ON user_id
goals_status_idx ON status
goals_deadline_idx ON deadline
```

#### practice_exercises
```sql
id              UUID PRIMARY KEY DEFAULT uuid_generate_v4()
user_id         UUID REFERENCES auth.users(id) ON DELETE CASCADE
type            TEXT NOT NULL  -- 'coding_challenge', 'debugging', 'code_review', etc.
topic           TEXT NOT NULL
difficulty      TEXT NOT NULL
title           TEXT NOT NULL
description     TEXT
content         JSONB  -- exercise data (problem, tests, hints, etc.)
created_at      TIMESTAMPTZ DEFAULT NOW()

-- Indexes
practice_exercises_type_idx ON type
practice_exercises_topic_idx ON topic
practice_exercises_difficulty_idx ON difficulty
```

#### practice_submissions
```sql
id              UUID PRIMARY KEY DEFAULT uuid_generate_v4()
user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
exercise_id     UUID NOT NULL REFERENCES practice_exercises(id) ON DELETE CASCADE
solution        TEXT NOT NULL
language        TEXT
correct         BOOLEAN
test_results    JSONB
feedback        TEXT
time_spent      INTEGER  -- seconds
submitted_at    TIMESTAMPTZ DEFAULT NOW()

-- Indexes
practice_submissions_user_id_idx ON user_id
practice_submissions_exercise_id_idx ON exercise_id
```

#### resources
```sql
id              UUID PRIMARY KEY DEFAULT uuid_generate_v4()
user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
title           TEXT NOT NULL
type            TEXT NOT NULL  -- 'link', 'note', 'file', 'bookmark'
url             TEXT
content         TEXT
tags            TEXT[]
bookmarked      BOOLEAN DEFAULT FALSE
metadata        JSONB
created_at      TIMESTAMPTZ DEFAULT NOW()

-- Indexes
resources_user_id_idx ON user_id
resources_type_idx ON type
resources_bookmarked_idx ON bookmarked
```

### Row Level Security (RLS)

All tables have RLS enabled. Example policies:

```sql
-- Users can only access their own data
CREATE POLICY "Users can view their own roadmaps"
  ON learning_roadmaps FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own roadmaps"
  ON learning_roadmaps FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own roadmaps"
  ON learning_roadmaps FOR UPDATE
  USING (auth.uid() = user_id);

-- Quiz attempts
CREATE POLICY "Users can view their own quiz attempts"
  ON quiz_attempts FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create quiz attempts"
  ON quiz_attempts FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Achievements (read-only for users)
CREATE POLICY "Authenticated users can view achievements"
  ON achievements FOR SELECT
  TO authenticated
  USING (true);

-- User achievements
CREATE POLICY "Users can view their own achievements"
  ON user_achievements FOR SELECT
  USING (auth.uid() = user_id);
```

---

## Testing & Quality

### Frontend Testing

**Not currently configured.** To add:

```bash
npm install --save-dev @testing-library/react @testing-library/jest-dom jest jest-environment-jsdom
```

### Backend Testing

**Location:** `server/` (pytest configured)

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest test_quiz_generator.py

# Run with verbose output
pytest -v
```

### Code Quality

**Frontend:**
```bash
npm run lint          # ESLint
npm run type-check    # TypeScript checking (if configured)
```

**Backend:**
```bash
# Install formatters/linters
pip install black isort flake8 mypy

# Format code
black .
isort .

# Lint
flake8 .

# Type checking
mypy main.py
```

### Security Checks

1. **HTML Sanitization:** Always use `sanitize_html()` for user-generated HTML
2. **Input Validation:** Use Pydantic models for all API inputs
3. **SQL Injection:** Use Supabase ORM, never raw SQL with user input
4. **XSS Prevention:** Use DOMPurify on frontend
5. **CSRF Protection:** Handled by Supabase JWT
6. **Rate Limiting:** Implemented per-user in `rate_limit.py`
7. **Quiz Answer Security:** Answers stored server-side, not exposed to client
8. **Progress Verification:** AI inference validated before auto-completion

---

## Deployment

### Frontend Deployment (Vercel)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel

# Production deployment
vercel --prod
```

**Environment Variables (Vercel):**
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_FASTAPI_URL`

### Backend Deployment (Railway/Render)

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Railway:**
1. Connect GitHub repo
2. Select `server/` as root directory
3. Add environment variables
4. Deploy

**Environment Variables (Backend):**
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `TAVILY_API_KEY`
- `OLLAMA_HOST` (if using remote Ollama)
- `GEMINI_API_KEY` (optional)

### Supabase Setup

1. Create project at supabase.com
2. Enable pgvector extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. Run migrations in order:
   - `database_migrations.sql`
   - `quiz_progress_migration.sql`
   - `chat_history_migration.sql`
   - `chat_roadmap_integration_enhancement.sql`
   - `student_features_migration.sql`
4. Configure RLS policies
5. Get API keys from Settings → API

---

## Gotchas & Important Notes

### Critical Issues to Avoid

1. **Supabase Client Confusion**
   - ❌ Don't use browser client in Server Components
   - ✅ Use `createClient()` from `@/lib/supabase/server` in Server Components
   - ✅ Use `createClient()` from `@/lib/supabase/client` in Client Components

2. **Authentication Flow**
   - JWT tokens are passed from Next.js API routes to FastAPI
   - Always verify auth in BOTH frontend middleware AND backend dependencies
   - Session cookies are HTTP-only and managed by Supabase SSR

3. **Streaming Responses**
   - Must use `StreamingResponse` with `media_type="text/event-stream"`
   - Frontend must handle SSE events properly
   - Don't forget `\n\n` after each SSE message
   - Include all event types: thinking, response, milestone_update, quiz_trigger, done

4. **Vector Search**
   - Embeddings are 768-dimensional (Google GenAI)
   - Must create IVFFLAT index for performance:
     ```sql
     CREATE INDEX ON table USING ivfflat (embedding vector_cosine_ops)
     WITH (lists = 100);
     ```
   - Similarity threshold typically 0.7-0.8

5. **Quiz Security**
   - ❌ Never expose correct answers to client before submission
   - ✅ Store quiz data with answers on server
   - ✅ Validate all submissions server-side
   - ✅ Use AI grading for subjective questions

6. **Progress Inference**
   - Confidence threshold is 0.75 by default (configurable)
   - Only auto-complete milestones with high confidence
   - Store evidence for manual review
   - Allow manual override of AI decisions

7. **Session Management**
   - Always use `SessionManager` for message persistence
   - Link sessions to roadmaps and conversations
   - Implement retry logic for database operations
   - Handle session cleanup on completion

8. **Roadmap State**
   - Milestone status: not_started, in_progress, completed, locked, skipped
   - Quiz milestones lock until previous lesson completed
   - Update roadmap progress after milestone completion
   - Trigger next milestone unlock automatically

9. **LangGraph State**
   - State is immutable between nodes
   - Always return updated state from nodes
   - Don't modify state in-place

10. **Rate Limiting**
    - Currently per-user, in-memory
    - Resets on server restart
    - Consider Redis for production
    - Quiz generation has higher limits than regular chat

11. **File Uploads**
    - Max size: 10MB (configurable in `file_router.py`)
    - Files stored in `server/storage/uploads/{user_id}/`
    - Always validate MIME types
    - OCR requires Tesseract installation: `apt-get install tesseract-ocr`

12. **CORS Issues**
    - Frontend must match allowed origins in `main.py`
    - Update for production domains:
      ```python
      allow_origins=["https://yourdomain.com"]
      ```

13. **Environment Variables**
    - Frontend: Must prefix with `NEXT_PUBLIC_` for client-side access
    - Backend: Never commit `.env` file
    - Always validate env vars exist in `config.py`

14. **Git Branch Naming**
    - ❌ Branches not starting with `claude/` will fail to push (403)
    - ✅ Always use format: `claude/feature-name-sessionid`

### Performance Considerations

1. **Vector Search:** Use appropriate `match_count` (5-10) to avoid slow queries
2. **Embeddings:** Cache frequently used embeddings in memory
3. **Streaming:** Buffer size affects latency vs. memory usage
4. **Database:** Use database indexes for frequently queried columns
5. **LLM Calls:** Use Ollama locally for development, consider rate limits for production
6. **Quiz Generation:** Can be slow (10-30s), show loading indicators
7. **Progress Inference:** Run asynchronously, don't block chat responses
8. **Roadmap Rendering:** Use pagination for large roadmaps (20+ milestones)

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Unauthorized" | Missing/invalid JWT | Check Supabase session exists |
| "CORS policy error" | Origin not allowed | Add domain to CORS middleware |
| "Vector dimension mismatch" | Wrong embedding model | Ensure all embeddings use same dimension |
| "Too many requests" | Rate limit hit | Implement backoff or increase limit |
| "File too large" | Upload exceeds limit | Check MAX_FILE_SIZE in file_router.py |
| "Ollama not found" | Ollama not running | Start Ollama: `ollama serve` |
| "Maximum attempts reached" | Quiz attempt limit | Check attempts_allowed in quiz |
| "Milestone locked" | Prerequisites not met | Complete previous milestones first |
| "Quiz not found" | Invalid quiz ID | Verify quiz exists and user has access |
| "Insufficient confidence" | AI unsure about completion | Requires manual milestone completion |

### Development Tips

1. **Hot Reload:** Both frontend (`npm run dev`) and backend (`uvicorn --reload`) support hot reload
2. **Debugging:** Use `logger.info()` liberally in backend, `console.log()` in frontend
3. **Database Inspection:** Use Supabase Table Editor for quick data viewing
4. **API Testing:** Use Thunder Client, Postman, or `curl` for testing endpoints
5. **LLM Debugging:** Print prompts and responses to understand agent behavior
6. **Quiz Testing:** Use simple topics first, then complex ones
7. **Roadmap Testing:** Start with 2-3 milestone roadmaps, then scale up
8. **Progress Inference Testing:** Test with varied conversation styles
9. **Session Testing:** Verify message persistence and linking

### Useful Commands

```bash
# Check Ollama is running
ollama list

# Pull new model
ollama pull qwen2.5:3b-instruct-q5_K_M

# Test Ollama
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:3b-instruct-q5_K_M",
  "prompt": "Hello"
}'

# Check Supabase connection
curl -H "apikey: YOUR_ANON_KEY" "https://YOUR_PROJECT.supabase.co/rest/v1/"

# Test FastAPI endpoint
curl -X POST http://localhost:8000/api/health

# Test quiz generation
curl -X POST http://localhost:8000/api/quizzes/generate \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{"topic": "Python Basics", "difficulty": "beginner", "num_questions": 3}'

# Check Next.js build
cd frontend && npm run build

# Check Python dependencies
pip list | grep langchain

# Monitor backend logs
tail -f server/logs/app.log
```

---

## Quick Reference

### File Locations Cheat Sheet

```
Need to...                          Look at...
────────────────────────────────────────────────────────────────────
Add API endpoint                    server/main.py (or create router)
Generate quizzes                    server/quiz_generator.py
Grade quiz answers                  server/quiz_grader.py
Create roadmaps                     server/roadmap_agent.py
Detect milestone completion         server/progress_inference.py
Manage chat sessions                server/session_manager.py
Modify AI behavior                  server/agent.py, server/prompts.py
Add frontend page                   frontend/app/dashboard/{name}/page.tsx
Add UI component                    frontend/components/{name}.tsx
Add quiz UI                         frontend/components/quiz/
Add roadmap UI                      frontend/components/roadmap/
Configure Supabase                  frontend/lib/supabase/*, server/config.py
Add authentication logic            frontend/middleware.ts, server/auth.py
Modify database schema              Supabase SQL Editor (run migrations)
Add vector search                   server/memori_engine.py
Process files                       server/file_router.py
Track progress                      server/progress_router.py
Manage topics                       server/topic_router.py
Create achievements                 server/achievement_router.py
Add practice exercises              server/practice_router.py
Manage resources                    server/resource_router.py
Customize styling                   frontend/app/globals.css, tailwind.config.ts
Add environment variable            frontend/.env.local, server/.env
```

### Command Cheat Sheet

```bash
# Start development
cd frontend && npm run dev          # Frontend on :3000
cd server && python start_server.py # Backend on :8000

# Install dependencies
cd frontend && npm install
cd server && pip install -r requirements.txt

# Build for production
cd frontend && npm run build
cd server && docker build -t api .

# Testing
cd frontend && npm run lint
cd server && pytest

# Database
# Go to Supabase Dashboard → SQL Editor → Run migrations

# Deployment
cd frontend && vercel --prod
# Backend → Railway/Render dashboard
```

### Key Metrics & Limits

```
Quiz Generation:          10-30 seconds
Quiz Grading (per Q):     2-5 seconds
Roadmap Generation:       15-45 seconds
Progress Inference:       5-10 seconds
Max Quiz Questions:       20 questions
Quiz Attempt Limit:       3 attempts (default)
Passing Score:            70% (default)
Confidence Threshold:     0.75 (progress inference)
Session Timeout:          30 minutes inactive
File Upload Limit:        10 MB
Rate Limit (chat):        20 requests/minute
Rate Limit (quiz gen):    5 requests/minute
Vector Search Results:    5-10 matches
Embedding Dimension:      768 (Google GenAI)
```

---

## Additional Resources

### Documentation
- **Next.js Docs:** https://nextjs.org/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **LangChain Docs:** https://python.langchain.com
- **LangGraph Docs:** https://langchain-ai.github.io/langgraph/
- **Supabase Docs:** https://supabase.com/docs
- **shadcn/ui Docs:** https://ui.shadcn.com
- **Tailwind CSS:** https://tailwindcss.com/docs

### Project Documentation
- `QUIZ_PROGRESS_IMPLEMENTATION_PLAN.md` - Comprehensive quiz/roadmap spec
- `BACKEND_IMPLEMENTATION_SUMMARY.md` - Backend features overview
- `FRONTEND_IMPLEMENTATION_PLAN.md` - Frontend implementation guide
- `DYNAMIC_PROMPTS_EXAMPLES.md` - Prompt engineering examples
- `INTENT_CLASSIFICATION.md` - Intent detection guide
- `MCP_MULTI_MODEL_ARCHITECTURE.md` - Multi-model architecture
- `MEMORI_INTEGRATION.md` - Memory system integration
- `NEXT_STEPS.md` - Development roadmap

---

**Generated by Claude Code Assistant**
**Version:** 2.0.0
**Date:** 2025-11-30
**Major Changes:**
- Added complete quiz and assessment system
- Added learning roadmap system with AI-generated paths
- Added progress inference engine for auto-completion
- Added session management for reliable persistence
- Added gamification (achievements, goals, streaks)
- Added practice exercises and coding challenges
- Added resource library and note-taking
- Updated all API endpoints (60+ total)
- Updated database schema (15+ tables)
- Updated architecture diagrams
- Added comprehensive task guides
- Updated statistics and metrics
