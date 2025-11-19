# CLAUDE.md - AI Assistant Guide for Porte Hobe AI

**Last Updated:** 2025-11-19
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

**Porte Hobe AI** is a sophisticated full-stack AI tutoring platform that provides personalized education in programming and mathematics. The system uses a two-phase reasoning approach with LangChain/LangGraph for intelligent tutoring interactions.

### Core Features

- **Autonomous AI Tutor**: Real-time chat with two-phase reasoning (Planning → Teaching)
- **Learning Domains**: Programming Basics and Math Fundamentals
- **Memory System**: User-specific and universal knowledge embeddings with vector search
- **Progress Tracking**: Topic-based progress, achievements, and performance metrics
- **Multi-modal Learning**: Text, PDF, images (OCR), web scraping
- **Streaming Responses**: Server-Sent Events (SSE) for real-time chat
- **Authentication**: Supabase Auth with JWT verification

### Key Statistics

- **Backend**: ~4,554 lines of Python (18 modules)
- **Frontend**: 50+ TypeScript/React components
- **AI Engine**: LangChain + LangGraph + Gemini/Ollama
- **Database**: Supabase (PostgreSQL with pgvector)

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
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 15)                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │   Pages    │  │ Components │  │ API Routes │            │
│  │  (Routes)  │  │    (UI)    │  │  (Proxy)   │            │
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘            │
│         │               │               │                    │
│         └───────────────┴───────────────┘                    │
│                         │                                    │
└─────────────────────────┼────────────────────────────────────┘
                          │ HTTP/SSE
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │    Main    │  │   Agent    │  │    MCP     │            │
│  │ Endpoints  │  │  (Tutor)   │  │   Agents   │            │
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘            │
│         │               │               │                    │
│         └───────────────┴───────────────┘                    │
│                         │                                    │
│         ┌───────────────┼───────────────┐                    │
│         ▼               ▼               ▼                    │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │Embedding │    │  Tools   │    │  HTML    │              │
│  │  Engine  │    │ (Search) │    │  Utils   │              │
│  └──────────┘    └──────────┘    └──────────┘              │
└─────────────────────────┬──────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Supabase (PostgreSQL + Auth)                    │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │   Users    │  │  Memories  │  │  Progress  │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
porte-hobe-ai/
│
├── frontend/                        # Next.js 15 Application
│   ├── app/                         # App Router Pages
│   │   ├── (home)/                  # Public Route Group
│   │   │   ├── page.tsx             # Landing page
│   │   │   ├── login/               # Login page
│   │   │   └── signup/              # Signup page
│   │   ├── dashboard/               # Protected Route Group
│   │   │   ├── page.tsx             # Dashboard home
│   │   │   ├── chat/                # Chat interface
│   │   │   │   ├── page.tsx         # Main chat page
│   │   │   │   └── history/         # Chat history
│   │   │   └── topics/              # Topic browser
│   │   ├── api/                     # API Proxy Routes
│   │   │   ├── chat/                # Chat endpoints
│   │   │   ├── memory/              # Memory endpoints
│   │   │   └── progress/            # Progress endpoints
│   │   ├── layout.tsx               # Root layout
│   │   └── globals.css              # Global styles
│   │
│   ├── components/                  # React Components
│   │   ├── ui/                      # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── avatar.tsx
│   │   │   └── ... (30+ components)
│   │   ├── auth-provider.tsx        # Auth context
│   │   ├── theme-provider.tsx       # Theme context
│   │   ├── app-sidebar.tsx          # Navigation sidebar
│   │   ├── ChatPage.tsx             # Main chat UI
│   │   ├── TopicBrowser.tsx         # Topic selection
│   │   ├── ProgressCard.tsx         # Stats display
│   │   └── FileDrop.tsx             # File upload
│   │
│   ├── lib/                         # Utilities
│   │   ├── supabase/
│   │   │   ├── client.ts            # Browser Supabase client
│   │   │   ├── server.ts            # Server Supabase client
│   │   │   └── middleware.ts        # Auth middleware
│   │   └── utils.ts                 # Helper functions
│   │
│   ├── hooks/                       # Custom Hooks
│   │   └── use-mobile.ts
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
│   ├── main.py                      # FastAPI app + endpoints (25KB)
│   ├── agent.py                     # TutorAgent (LangGraph) (20KB)
│   ├── mcp_agents.py                # MCP agents (scraper, file, math, vector) (12KB)
│   ├── mcp_server.py                # MCP JSON-RPC server (10KB)
│   ├── embedding_engine.py          # Embeddings & vector search (4KB)
│   ├── web_crawler.py               # Advanced web crawling (20KB)
│   ├── html_utils.py                # HTML sanitization/generation (8KB)
│   ├── prompts.py                   # System prompts (7KB)
│   ├── tools.py                     # Tool definitions (3KB)
│   ├── file_router.py               # File upload endpoints (12KB)
│   ├── topic_router.py              # Topic management (13KB)
│   ├── progress_router.py           # Progress tracking (12KB)
│   ├── auth.py                      # JWT authentication (1.5KB)
│   ├── config.py                    # Environment config (3KB)
│   ├── rate_limit.py                # Rate limiting (1.9KB)
│   ├── start_server.py              # Server startup (0.9KB)
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

**Current Branch:** `claude/claude-md-mi6ijisxwcje48ct-01N4dMxMCdpqD74uQMrEczQY`

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
// Files: camelCase with descriptive names
ChatPage.tsx
TopicBrowser.tsx
use-mobile.ts

// Components: PascalCase
export function ChatPage() { }
export const ProgressCard = () => { }

// Hooks: camelCase with 'use' prefix
export function useMobile() { }

// Variables/Functions: camelCase
const handleTopicSelect = () => { }
const [messages, setMessages] = useState([])

// Interfaces/Types: PascalCase
interface Message { }
type ProgressStats = { }

// Constants: UPPER_SNAKE_CASE
const MAX_MESSAGE_LENGTH = 5000
```

#### Backend (Python)

```python
# Files: snake_case
main.py
embedding_engine.py
mcp_agents.py

# Classes: PascalCase
class TutorAgent:
class ScraperAgent:

# Functions/Methods: snake_case
def get_current_user():
def store_user_memory():
async def verify_supabase_jwt():

# Constants: UPPER_SNAKE_CASE
ALLOWED_TAGS = ["p", "strong", "em"]
MAX_FILE_SIZE = 10 * 1024 * 1024
EMBED_DIM = 768

# Variables: snake_case (descriptive)
user_message = "Hello"
conversation_id = uuid.uuid4()
```

#### Database (Supabase)

```sql
-- Tables: snake_case
user_memory
universal_memory
topics
progress

-- Columns: snake_case
created_at
user_id
topic_id

-- Indexes: {table}_{column}_idx
user_memory_user_id_idx
```

### Code Patterns

#### Frontend Patterns

**1. API Route Pattern (Proxy to FastAPI)**

```typescript
// app/api/chat/route.ts
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

  // Proxy to FastAPI with streaming
  const response = await fetch(`${process.env.NEXT_PUBLIC_FASTAPI_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session?.access_token}`
    },
    body: JSON.stringify(await request.json())
  })

  // Return streaming response
  return new Response(response.body, {
    headers: { 'Content-Type': 'text/event-stream' }
  })
}
```

**2. Protected Component Pattern**

```typescript
// components/ProtectedComponent.tsx
'use client'

import { useAuth } from '@/components/auth-provider'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export function ProtectedComponent() {
  const { user, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [user, loading, router])

  if (loading) return <div>Loading...</div>
  if (!user) return null

  return <div>Protected Content</div>
}
```

**3. Supabase Client Pattern**

```typescript
// lib/supabase/server.ts (Server Components)
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export async function createClient() {
  const cookieStore = await cookies()

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return cookieStore.getAll() },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) =>
            cookieStore.set(name, value, options)
          )
        }
      }
    }
  )
}

// lib/supabase/client.ts (Client Components)
import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}
```

#### Backend Patterns

**1. Protected Endpoint Pattern**

```python
# main.py
from auth import get_current_user
from rate_limit import limit_user

@app.post("/api/endpoint")
async def protected_endpoint(
    request: RequestModel,
    user = Depends(get_current_user),  # JWT verification
    _limit = Depends(limit_user)        # Rate limiting
):
    user_id = user.get("sub")

    # Your logic here

    return {"status": "success"}
```

**2. Streaming Response Pattern**

```python
# main.py
from fastapi.responses import StreamingResponse

async def event_generator(request_id: str, user_id: str):
    """Generate SSE events"""

    # Phase 1: Thinking
    yield f"data: {json.dumps({'type': 'thinking', 'content': 'Analyzing...'})}\n\n"

    # Phase 2: Response streaming
    async for chunk in agent.stream_response():
        yield f"data: {json.dumps({'type': 'response', 'content': chunk})}\n\n"

    # Final event
    yield f"data: {json.dumps({'type': 'done'})}\n\n"

@app.post("/api/chat")
async def chat(request: ChatRequest, user = Depends(get_current_user)):
    return StreamingResponse(
        event_generator(request.request_id, user.get("sub")),
        media_type="text/event-stream"
    )
```

**3. LangGraph Agent Pattern**

```python
# agent.py
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage

class TutorState(TypedDict):
    messages: List[BaseMessage]
    thinking_content: str
    user_context: str
    topic_id: Optional[str]

class TutorAgent:
    def __init__(self):
        self.workflow = StateGraph(TutorState)
        self._build_graph()
        self.app = self.workflow.compile()

    def _build_graph(self):
        # Define nodes
        self.workflow.add_node("plan", self._plan_node)
        self.workflow.add_node("respond", self._respond_node)

        # Define edges
        self.workflow.set_entry_point("plan")
        self.workflow.add_edge("plan", "respond")
        self.workflow.add_edge("respond", END)

    async def _plan_node(self, state: TutorState):
        # Phase 1: Planning logic
        return {"thinking_content": "Analysis..."}

    async def _respond_node(self, state: TutorState):
        # Phase 2: Response generation
        return {"messages": [AIMessage(content="Response")]}
```

**4. Database Query Pattern**

```python
# Using Supabase client
from config import get_supabase_client

supabase = get_supabase_client()

# Insert
result = supabase.table("user_memory").insert({
    "user_id": user_id,
    "content": content,
    "embedding": embedding_vector
}).execute()

# Query with filters
result = supabase.table("progress")\
    .select("*")\
    .eq("user_id", user_id)\
    .eq("topic_id", topic_id)\
    .execute()

# Update
result = supabase.table("progress")\
    .update({"score": new_score})\
    .eq("id", progress_id)\
    .execute()
```

### Error Handling Patterns

#### Frontend

```typescript
try {
  const response = await fetch('/api/endpoint', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }

  const result = await response.json()
  // Handle success
} catch (error) {
  console.error('Error:', error)
  // Show user-friendly message
  toast.error('Something went wrong. Please try again.')
}
```

#### Backend

```python
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

@app.post("/api/endpoint")
async def endpoint(request: RequestModel):
    try:
        # Your logic
        result = await process_request(request)
        return {"status": "success", "data": result}

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
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
| `server/main.py` | FastAPI application with all endpoints |
| `server/start_server.py` | Server startup script |

### Core Logic

| File | Lines | Purpose |
|------|-------|---------|
| `server/agent.py` | ~800 | TutorAgent with LangGraph state machine |
| `server/mcp_agents.py` | ~500 | MCP agents (scraper, file, math, vector) |
| `server/embedding_engine.py` | ~150 | Vector search and embeddings |
| `server/html_utils.py` | ~300 | HTML sanitization and generation |
| `server/prompts.py` | ~250 | System prompts for tutor phases |
| `frontend/components/ChatPage.tsx` | ~400 | Main chat interface with streaming |
| `frontend/components/auth-provider.tsx` | ~100 | Auth context and state management |

### Routers

| File | Lines | Purpose |
|------|-------|---------|
| `server/file_router.py` | ~500 | File upload/processing endpoints |
| `server/topic_router.py` | ~550 | Topic management endpoints |
| `server/progress_router.py` | ~500 | Progress tracking endpoints |

---

## Common Tasks Guide

### Task 1: Add a New API Endpoint

**Backend (FastAPI):**

```python
# server/main.py or create new router

from pydantic import BaseModel
from auth import get_current_user
from rate_limit import limit_user

class NewRequest(BaseModel):
    data: str

class NewResponse(BaseModel):
    result: str

@app.post("/api/new-endpoint")
async def new_endpoint(
    request: NewRequest,
    user = Depends(get_current_user),
    _limit = Depends(limit_user)
):
    user_id = user.get("sub")

    # Your logic here
    result = process_data(request.data)

    return NewResponse(result=result)
```

**Frontend (Next.js API Route):**

```typescript
// frontend/app/api/new-endpoint/route.ts

import { createClient } from '@/lib/supabase/server'

export async function POST(request: Request) {
  const supabase = await createClient()

  const { data: { user }, error } = await supabase.auth.getUser()
  if (error || !user) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const { data: { session } } = await supabase.auth.getSession()
  const body = await request.json()

  const response = await fetch(`${process.env.NEXT_PUBLIC_FASTAPI_URL}/api/new-endpoint`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session?.access_token}`
    },
    body: JSON.stringify(body)
  })

  const result = await response.json()
  return Response.json(result)
}
```

### Task 2: Add a New Page/Route

```typescript
// frontend/app/dashboard/new-page/page.tsx

export default function NewPage() {
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-4">New Page</h1>
      {/* Your content */}
    </div>
  )
}
```

Update sidebar navigation:

```typescript
// frontend/components/app-sidebar.tsx

const navItems = [
  // ... existing items
  {
    title: "New Page",
    url: "/dashboard/new-page",
    icon: YourIcon,
  }
]
```

### Task 3: Add a New Database Table

**1. Create migration in Supabase:**

```sql
-- In Supabase SQL Editor

CREATE TABLE new_table (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE new_table ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view their own data"
  ON new_table FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own data"
  ON new_table FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Create index
CREATE INDEX new_table_user_id_idx ON new_table(user_id);
```

**2. Access from backend:**

```python
# server/main.py

@app.post("/api/new-table/create")
async def create_item(
    content: str,
    user = Depends(get_current_user)
):
    user_id = user.get("sub")

    result = supabase.table("new_table").insert({
        "user_id": user_id,
        "content": content
    }).execute()

    return {"id": result.data[0]["id"]}
```

### Task 4: Add Vector Search Capability

```python
# server/embedding_engine.py

async def search_new_collection(query: str, user_id: str, limit: int = 5):
    """Search new collection with embeddings"""

    # Generate query embedding
    query_embedding = await generate_embedding(query)

    # Vector search using pgvector
    result = supabase.rpc(
        'match_new_collection',
        {
            'query_embedding': query_embedding,
            'match_threshold': 0.7,
            'match_count': limit,
            'p_user_id': user_id
        }
    ).execute()

    return result.data
```

**Create matching function in Supabase:**

```sql
CREATE OR REPLACE FUNCTION match_new_collection(
  query_embedding vector(768),
  match_threshold float,
  match_count int,
  p_user_id uuid
)
RETURNS TABLE (
  id uuid,
  content text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    new_table.id,
    new_table.content,
    1 - (new_table.embedding <=> query_embedding) AS similarity
  FROM new_table
  WHERE
    new_table.user_id = p_user_id
    AND 1 - (new_table.embedding <=> query_embedding) > match_threshold
  ORDER BY new_table.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
```

### Task 5: Add New MCP Agent

```python
# server/mcp_agents.py

class NewAgent:
    def __init__(self):
        self.name = "new_agent"

    async def process(self, input_data: str) -> dict:
        """Process input and return result"""

        # Your agent logic
        result = await self._perform_task(input_data)

        return {
            "status": "success",
            "data": result
        }

    async def _perform_task(self, data: str):
        # Implementation
        pass

# Instantiate agent
new_agent = NewAgent()

# Add to main.py
from mcp_agents import new_agent

@app.post("/api/new-agent/process")
async def process_with_agent(
    input_data: str,
    user = Depends(get_current_user)
):
    result = await new_agent.process(input_data)
    return result
```

### Task 6: Modify Tutor Behavior

**Edit system prompts:**

```python
# server/prompts.py

PHASE_1_SYSTEM_PROMPT = """You are an AI tutor in the PLANNING phase.

Your task:
1. Analyze the student's question
2. Plan your teaching approach
3. Determine which tools to use
4. NEW BEHAVIOR: [Add your modification here]

Available tools: {tools}
"""

# Or add domain-specific behavior
PROGRAMMING_DOMAIN_PROMPT = """
Programming Tutor Guidelines:
- Focus on best practices
- Encourage debugging skills
- NEW: Emphasize testing
"""
```

**Modify agent logic:**

```python
# server/agent.py

class TutorAgent:
    async def _plan_node(self, state: TutorState):
        # Add your custom planning logic

        # Example: Add topic-specific context
        if state.get("topic_id"):
            topic_context = await fetch_topic_context(state["topic_id"])
            state["user_context"] += f"\n\nTopic Context:\n{topic_context}"

        # Continue with existing logic
        return state
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
  "topic_id": "programming_basics_001",
  "attachments": ["file_id_123"],
  "enable_web_search": false,
  "enable_math": false,
  "response_format": "text"
}
```

**Response (SSE Stream):**
```
data: {"type": "thinking", "content": "Analyzing question..."}

data: {"type": "response", "content": "Bubble sort is..."}

data: {"type": "done", "request_id": "uuid"}
```

#### POST /api/chat/simple
Non-streaming chat response.

**Response:**
```json
{
  "response": "Full response text",
  "thinking_content": "Planning notes",
  "request_id": "uuid",
  "response_html": "<p>HTML formatted response</p>",
  "attachments_used": ["file_id_123"],
  "web_sources": [{"url": "...", "title": "..."}],
  "math_results": [{"expression": "...", "result": "..."}]
}
```

#### GET /api/chat/history?user_id={user_id}&limit=20
Get conversation history.

**Response:**
```json
{
  "conversations": [
    {
      "id": "uuid",
      "title": "Bubble Sort Discussion",
      "created_at": "2025-11-19T10:30:00Z",
      "updated_at": "2025-11-19T10:45:00Z",
      "messages": [
        {"role": "user", "content": "...", "timestamp": "..."},
        {"role": "assistant", "content": "...", "timestamp": "..."}
      ]
    }
  ]
}
```

#### POST /api/chat/save-message
Save individual message to conversation.

**Request:**
```json
{
  "conversation_id": "uuid",
  "role": "user",
  "content": "Message content",
  "metadata": {}
}
```

#### DELETE /api/chat/history/{conversation_id}
Delete entire conversation.

### Memory Endpoints

#### POST /api/memory/add
Add to user memory with embeddings.

**Request:**
```json
{
  "content": "User prefers visual explanations",
  "category": "learning_preference",
  "metadata": {}
}
```

### File Endpoints

#### POST /api/upload
Upload file (PDF/image, max 10MB).

**Request:** `multipart/form-data`
- `file`: File object
- `description`: Optional description

**Response:**
```json
{
  "file_id": "uuid",
  "filename": "document.pdf",
  "size": 1024000,
  "mime_type": "application/pdf"
}
```

#### GET /api/files?user_id={user_id}
List user's uploaded files.

#### POST /api/files/{file_id}/process
Process uploaded file (extract text, OCR).

**Response:**
```json
{
  "text": "Extracted content",
  "pages": 10,
  "word_count": 5000
}
```

#### DELETE /api/files/{file_id}
Delete uploaded file.

### Topic Endpoints

#### GET /api/topics?domain={domain}&level={level}
Get all topics with optional filters.

**Query Params:**
- `domain`: "programming" | "math"
- `level`: "beginner" | "intermediate" | "advanced"

**Response:**
```json
{
  "topics": [
    {
      "id": "programming_basics_001",
      "title": "Variables and Data Types",
      "domain": "programming",
      "level": "beginner",
      "estimated_time": 30,
      "prerequisites": []
    }
  ]
}
```

#### GET /api/topics/{topic_id}
Get topic details with content.

#### POST /api/topics/{topic_id}/start
Mark topic as started for user.

### Progress Endpoints

#### GET /api/progress?user_id={user_id}
Get user's learning progress.

**Response:**
```json
{
  "overall_progress": 45.5,
  "topics": [
    {
      "topic_id": "programming_basics_001",
      "progress": 80.0,
      "status": "in_progress",
      "time_spent": 1200,
      "last_activity": "2025-11-19T10:30:00Z"
    }
  ]
}
```

#### GET /api/progress/stats
Get overall learning statistics.

**Response:**
```json
{
  "total_topics": 50,
  "completed_topics": 12,
  "in_progress_topics": 3,
  "total_time_minutes": 3600,
  "current_streak": 7,
  "achievements": ["first_topic", "week_streak"]
}
```

#### POST /api/progress/update
Update progress for a topic.

**Request:**
```json
{
  "topic_id": "programming_basics_001",
  "progress": 85.0,
  "time_spent": 1800,
  "score": 92.5
}
```

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
user_memory_embedding_idx ON embedding (IVFFLAT)
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
universal_memory_embedding_idx ON embedding (IVFFLAT)
universal_memory_category_idx ON category
```

#### conversations
```sql
id              UUID PRIMARY KEY DEFAULT uuid_generate_v4()
user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
title           TEXT
created_at      TIMESTAMPTZ DEFAULT NOW()
updated_at      TIMESTAMPTZ DEFAULT NOW()

-- Indexes
conversations_user_id_idx ON user_id
conversations_created_at_idx ON created_at DESC
```

#### messages
```sql
id              UUID PRIMARY KEY DEFAULT uuid_generate_v4()
conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE
role            TEXT NOT NULL  -- 'user' or 'assistant'
content         TEXT NOT NULL
metadata        JSONB
created_at      TIMESTAMPTZ DEFAULT NOW()

-- Indexes
messages_conversation_id_idx ON conversation_id
messages_created_at_idx ON created_at
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

### Row Level Security (RLS)

All tables have RLS enabled. Example policies:

```sql
-- Users can only access their own data
CREATE POLICY "Users can view their own memory"
  ON user_memory FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own memory"
  ON user_memory FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Universal memory is readable by all authenticated users
CREATE POLICY "Authenticated users can view universal memory"
  ON universal_memory FOR SELECT
  TO authenticated
  USING (true);
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
pytest test_agent.py

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

### Supabase Setup

1. Create project at supabase.com
2. Run migrations in SQL Editor (see Database Schema)
3. Enable pgvector extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
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

4. **Vector Search**
   - Embeddings are 768-dimensional (Google GenAI)
   - Must create IVFFLAT index for performance:
     ```sql
     CREATE INDEX ON table USING ivfflat (embedding vector_cosine_ops)
     WITH (lists = 100);
     ```
   - Similarity threshold typically 0.7-0.8

5. **File Uploads**
   - Max size: 10MB (configurable in `file_router.py`)
   - Files stored in `server/storage/uploads/{user_id}/`
   - Always validate MIME types
   - OCR requires Tesseract installation: `apt-get install tesseract-ocr`

6. **LangGraph State**
   - State is immutable between nodes
   - Always return updated state from nodes
   - Don't modify state in-place

7. **Rate Limiting**
   - Currently per-user, in-memory
   - Resets on server restart
   - Consider Redis for production

8. **CORS Issues**
   - Frontend must match allowed origins in `main.py`
   - Update for production domains:
     ```python
     allow_origins=["https://yourdomain.com"]
     ```

9. **Environment Variables**
   - Frontend: Must prefix with `NEXT_PUBLIC_` for client-side access
   - Backend: Never commit `.env` file
   - Always validate env vars exist in `config.py`

10. **Git Branch Naming**
    - ❌ Branches not starting with `claude/` will fail to push (403)
    - ✅ Always use format: `claude/feature-name-sessionid`

### Performance Considerations

1. **Vector Search:** Use appropriate `match_count` (5-10) to avoid slow queries
2. **Embeddings:** Cache frequently used embeddings in memory
3. **Streaming:** Buffer size affects latency vs. memory usage
4. **Database:** Use database indexes for frequently queried columns
5. **LLM Calls:** Use Ollama locally for development, consider rate limits for production

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Unauthorized" | Missing/invalid JWT | Check Supabase session exists |
| "CORS policy error" | Origin not allowed | Add domain to CORS middleware |
| "Vector dimension mismatch" | Wrong embedding model | Ensure all embeddings use same dimension |
| "Too many requests" | Rate limit hit | Implement backoff or increase limit |
| "File too large" | Upload exceeds limit | Check MAX_FILE_SIZE in file_router.py |
| "Ollama not found" | Ollama not running | Start Ollama: `ollama serve` |

### Development Tips

1. **Hot Reload:** Both frontend (`npm run dev`) and backend (`uvicorn --reload`) support hot reload
2. **Debugging:** Use `logger.info()` liberally in backend, `console.log()` in frontend
3. **Database Inspection:** Use Supabase Table Editor for quick data viewing
4. **API Testing:** Use Thunder Client, Postman, or `curl` for testing endpoints
5. **LLM Debugging:** Print prompts and responses to understand agent behavior

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

# Check Next.js build
cd frontend && npm run build

# Check Python dependencies
pip list | grep langchain
```

---

## Quick Reference

### File Locations Cheat Sheet

```
Need to...                          Look at...
────────────────────────────────────────────────────────────────────
Add API endpoint                    server/main.py (or create router)
Modify AI behavior                  server/agent.py, server/prompts.py
Add frontend page                   frontend/app/dashboard/{name}/page.tsx
Add UI component                    frontend/components/{name}.tsx
Configure Supabase                  frontend/lib/supabase/*, server/config.py
Add authentication logic            frontend/middleware.ts, server/auth.py
Modify database schema              Supabase SQL Editor
Add vector search                   server/embedding_engine.py
Process files                       server/file_router.py
Track progress                      server/progress_router.py
Manage topics                       server/topic_router.py
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
# Go to Supabase Dashboard → SQL Editor

# Deployment
cd frontend && vercel --prod
# Backend → Railway/Render dashboard
```

---

## Additional Resources

- **Next.js Docs:** https://nextjs.org/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **LangChain Docs:** https://python.langchain.com
- **LangGraph Docs:** https://langchain-ai.github.io/langgraph/
- **Supabase Docs:** https://supabase.com/docs
- **shadcn/ui Docs:** https://ui.shadcn.com
- **Tailwind CSS:** https://tailwindcss.com/docs

---

**Generated by Claude Code Assistant**
**Version:** 1.0.0
**Date:** 2025-11-19
