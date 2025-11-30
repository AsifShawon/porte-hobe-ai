# Quiz & Progress System Implementation Plan

## Overview

Implement an intelligent Quiz and Progress tracking system that:
- 🧠 **Auto-generates learning roadmaps** from user conversations
- 📊 **Tracks progress** through visual timeline/roadmap
- ❓ **Delivers in-conversation quizzes** at strategic learning points
- ✅ **AI-powered grading** with detailed feedback
- 📚 **Quiz library** for practice and review

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Conversation                         │
│  "I want to learn Python programming from scratch"          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              AI Agent (Roadmap Generator)                    │
│  - Analyzes learning goals                                   │
│  - Generates personalized roadmap with milestones            │
│  - Determines quiz insertion points                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    Learning Roadmap                          │
│  Phase 1: Python Basics (3 lessons, 1 quiz)                 │
│  Phase 2: Data Types (4 lessons, 2 quizzes)                 │
│  Phase 3: Control Flow (5 lessons, 2 quizzes)               │
└─────────────────────┬───────────────────────────────────────┘
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│  Progress Track  │    │  Quiz Delivery   │
│  - Visual roadmap│    │  - In-chat pop   │
│  - % complete    │    │  - AI grading    │
│  - Milestones    │    │  - Feedback      │
└──────────────────┘    └──────────────────┘
```

---

## Phase 1: Database Schema Design

### 1.1 Learning Roadmaps Table

```sql
CREATE TABLE learning_roadmaps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    domain VARCHAR(50) NOT NULL, -- 'programming', 'math', 'general'

    -- AI-generated roadmap structure
    roadmap_data JSONB NOT NULL,
    /* Structure:
    {
      "phases": [
        {
          "id": "phase_1",
          "title": "Python Basics",
          "order": 1,
          "milestones": [
            {
              "id": "milestone_1",
              "title": "Variables and Data Types",
              "type": "lesson",
              "estimated_time": 30,
              "status": "not_started"
            },
            {
              "id": "quiz_1",
              "title": "Variables Quiz",
              "type": "quiz",
              "quiz_id": "uuid",
              "status": "locked"
            }
          ]
        }
      ],
      "total_milestones": 15,
      "completed_milestones": 3
    }
    */

    -- Progress tracking
    total_milestones INTEGER NOT NULL DEFAULT 0,
    completed_milestones INTEGER NOT NULL DEFAULT 0,
    progress_percentage FLOAT DEFAULT 0.0,
    current_phase_id VARCHAR(100),
    current_milestone_id VARCHAR(100),

    -- Status
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'completed', 'paused', 'abandoned'

    -- Conversation context
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    chat_session_id UUID REFERENCES chat_sessions(id) ON DELETE SET NULL,

    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    CONSTRAINT valid_progress CHECK (
        completed_milestones >= 0 AND
        completed_milestones <= total_milestones AND
        progress_percentage >= 0 AND
        progress_percentage <= 100
    )
);

CREATE INDEX learning_roadmaps_user_id_idx ON learning_roadmaps(user_id);
CREATE INDEX learning_roadmaps_status_idx ON learning_roadmaps(status);
CREATE INDEX learning_roadmaps_created_at_idx ON learning_roadmaps(created_at DESC);
CREATE INDEX learning_roadmaps_conversation_idx ON learning_roadmaps(conversation_id);
```

### 1.2 In-Conversation Quizzes Table

```sql
CREATE TABLE conversation_quizzes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    roadmap_id UUID REFERENCES learning_roadmaps(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,

    -- Quiz details
    title VARCHAR(200) NOT NULL,
    description TEXT,
    topic VARCHAR(200),
    difficulty VARCHAR(50) NOT NULL, -- 'beginner', 'intermediate', 'advanced'

    -- Questions (AI-generated)
    questions JSONB NOT NULL,
    /* Structure:
    [
      {
        "id": "q1",
        "type": "multiple_choice", // 'multiple_choice', 'true_false', 'short_answer', 'code'
        "question": "What is a variable in Python?",
        "options": ["A storage location", "A function", "A loop", "A class"],
        "correct_answer": "A storage location",
        "explanation": "Variables are containers for storing data values.",
        "points": 10
      },
      {
        "id": "q2",
        "type": "code",
        "question": "Write a Python function that returns the sum of two numbers",
        "template": "def add(a, b):\n    # Your code here\n    pass",
        "test_cases": [
          {"input": [2, 3], "expected": 5},
          {"input": [10, -5], "expected": 5}
        ],
        "points": 20
      }
    ]
    */

    -- Attempt tracking
    total_points INTEGER NOT NULL DEFAULT 0,
    attempts_allowed INTEGER DEFAULT 3,

    -- Timing
    time_limit INTEGER, -- in minutes, null = no limit
    estimated_duration INTEGER DEFAULT 10, -- minutes

    -- Status
    status VARCHAR(50) DEFAULT 'not_started', -- 'not_started', 'in_progress', 'completed', 'skipped'

    -- Triggers
    trigger_condition VARCHAR(100), -- 'after_milestone', 'time_based', 'manual'
    triggered_at TIMESTAMPTZ,
    presented_at TIMESTAMPTZ, -- when shown to user in conversation

    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX conversation_quizzes_user_id_idx ON conversation_quizzes(user_id);
CREATE INDEX conversation_quizzes_roadmap_id_idx ON conversation_quizzes(roadmap_id);
CREATE INDEX conversation_quizzes_conversation_idx ON conversation_quizzes(conversation_id);
CREATE INDEX conversation_quizzes_status_idx ON conversation_quizzes(status);
```

### 1.3 Quiz Attempts Table

```sql
CREATE TABLE quiz_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    quiz_id UUID NOT NULL REFERENCES conversation_quizzes(id) ON DELETE CASCADE,
    roadmap_id UUID REFERENCES learning_roadmaps(id) ON DELETE SET NULL,

    -- Attempt details
    attempt_number INTEGER NOT NULL DEFAULT 1,

    -- User answers
    answers JSONB NOT NULL,
    /* Structure:
    {
      "q1": {
        "answer": "A storage location",
        "correct": true,
        "points_earned": 10,
        "time_spent": 15 // seconds
      },
      "q2": {
        "answer": "def add(a, b):\n    return a + b",
        "correct": true,
        "points_earned": 20,
        "test_results": [
          {"passed": true, "input": [2, 3], "output": 5},
          {"passed": true, "input": [10, -5], "output": 5}
        ]
      }
    }
    */

    -- Grading (AI-powered)
    total_questions INTEGER NOT NULL,
    correct_answers INTEGER DEFAULT 0,
    points_earned FLOAT DEFAULT 0.0,
    total_points FLOAT NOT NULL,
    percentage_score FLOAT DEFAULT 0.0,

    -- AI feedback
    feedback TEXT,
    strengths TEXT[], -- ["Good understanding of variables", "Clean code syntax"]
    weaknesses TEXT[], -- ["Need to review data types"]
    recommendations TEXT[], -- ["Practice more with loops", "Review chapter 3"]

    -- Timing
    time_spent INTEGER, -- total seconds spent
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    -- Status
    status VARCHAR(50) DEFAULT 'in_progress', -- 'in_progress', 'completed', 'abandoned'
    passed BOOLEAN DEFAULT FALSE,

    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX quiz_attempts_user_id_idx ON quiz_attempts(user_id);
CREATE INDEX quiz_attempts_quiz_id_idx ON quiz_attempts(quiz_id);
CREATE INDEX quiz_attempts_roadmap_id_idx ON quiz_attempts(roadmap_id);
CREATE INDEX quiz_attempts_status_idx ON quiz_attempts(status);
CREATE INDEX quiz_attempts_created_at_idx ON quiz_attempts(created_at DESC);
```

### 1.4 Milestone Progress Table

```sql
CREATE TABLE milestone_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    roadmap_id UUID NOT NULL REFERENCES learning_roadmaps(id) ON DELETE CASCADE,

    -- Milestone identification
    phase_id VARCHAR(100) NOT NULL,
    milestone_id VARCHAR(100) NOT NULL,

    -- Progress
    status VARCHAR(50) DEFAULT 'not_started', -- 'not_started', 'in_progress', 'completed', 'skipped'
    progress_percentage FLOAT DEFAULT 0.0,

    -- Associated quiz (if milestone is a quiz)
    quiz_id UUID REFERENCES conversation_quizzes(id) ON DELETE SET NULL,
    quiz_passed BOOLEAN,

    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    time_spent INTEGER DEFAULT 0, -- seconds

    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_milestone UNIQUE(user_id, roadmap_id, phase_id, milestone_id)
);

CREATE INDEX milestone_progress_user_id_idx ON milestone_progress(user_id);
CREATE INDEX milestone_progress_roadmap_id_idx ON milestone_progress(roadmap_id);
CREATE INDEX milestone_progress_status_idx ON milestone_progress(status);
```

---

## Phase 2: Backend Implementation

### 2.1 Roadmap Generator Agent

**File:** `server/roadmap_agent.py`

```python
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import List, Dict, Any
import json

class RoadmapGeneratorAgent:
    """
    AI agent that generates personalized learning roadmaps
    based on user conversation and goals
    """

    ROADMAP_GENERATION_PROMPT = """You are an expert learning path designer.

    Analyze the user's learning goals and conversation history to create a
    personalized learning roadmap.

    The roadmap should:
    1. Break learning into logical phases (3-7 phases)
    2. Each phase has milestones (lessons and quizzes)
    3. Quizzes should be inserted after 2-4 related lessons
    4. Estimate realistic time for each milestone
    5. Order by difficulty (beginner → advanced)

    User Context:
    {user_context}

    Conversation History:
    {conversation_history}

    Generate a JSON roadmap with this structure:
    {{
      "title": "Learning Path Title",
      "domain": "programming|math|general",
      "description": "Brief overview",
      "phases": [
        {{
          "id": "phase_1",
          "title": "Phase Title",
          "order": 1,
          "milestones": [
            {{
              "id": "lesson_1",
              "title": "Milestone Title",
              "type": "lesson",
              "estimated_time": 30,
              "description": "What user will learn",
              "topics": ["topic1", "topic2"],
              "status": "not_started"
            }},
            {{
              "id": "quiz_1",
              "title": "Quiz Title",
              "type": "quiz",
              "estimated_time": 15,
              "topics": ["topic1", "topic2"],
              "difficulty": "beginner",
              "status": "locked"
            }}
          ]
        }}
      ]
    }}
    """

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.7
        )

    async def generate_roadmap(
        self,
        user_goal: str,
        conversation_history: List[Dict],
        user_context: Dict
    ) -> Dict[str, Any]:
        """Generate a personalized learning roadmap"""

        prompt = self.ROADMAP_GENERATION_PROMPT.format(
            user_context=json.dumps(user_context, indent=2),
            conversation_history=self._format_history(conversation_history)
        )

        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=f"User's learning goal: {user_goal}")
        ]

        response = await self.llm.ainvoke(messages)
        roadmap_data = self._parse_roadmap(response.content)

        return roadmap_data

    async def update_roadmap(
        self,
        roadmap_id: str,
        user_progress: Dict,
        new_insights: str
    ) -> Dict[str, Any]:
        """Update existing roadmap based on user progress"""
        # Logic to adapt roadmap based on quiz performance
        pass
```

### 2.2 Quiz Generator Agent

**File:** `server/quiz_generator.py`

```python
class QuizGeneratorAgent:
    """
    AI agent that generates contextual quizzes based on
    what the user has learned in the conversation
    """

    QUIZ_GENERATION_PROMPT = """You are an expert quiz designer.

    Create a quiz to assess the user's understanding of the following topics:
    {topics}

    Recent conversation context:
    {conversation_context}

    Generate {num_questions} questions with these requirements:
    - Mix of question types: multiple choice, true/false, short answer, code
    - Difficulty level: {difficulty}
    - Include explanations for correct answers
    - Provide helpful feedback for wrong answers

    Return JSON array of questions following this structure:
    [
      {{
        "id": "q1",
        "type": "multiple_choice",
        "question": "Question text",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "Option A",
        "explanation": "Why this is correct",
        "points": 10,
        "difficulty": "beginner"
      }}
    ]
    """

    async def generate_quiz(
        self,
        topics: List[str],
        conversation_context: str,
        num_questions: int = 5,
        difficulty: str = "beginner"
    ) -> List[Dict]:
        """Generate quiz questions based on learned topics"""
        pass

    async def should_trigger_quiz(
        self,
        conversation_messages: List[Dict],
        roadmap_data: Dict
    ) -> bool:
        """Determine if it's a good time to present a quiz"""
        # Check if user has covered enough material
        # Check if quiz is due according to roadmap
        # Check conversation flow (don't interrupt active discussion)
        pass
```

### 2.3 Quiz Grading Agent

**File:** `server/quiz_grader.py`

```python
class QuizGraderAgent:
    """
    AI-powered quiz grading with detailed feedback
    """

    GRADING_PROMPT = """You are an expert tutor grading a student's quiz.

    Question: {question}
    Correct Answer: {correct_answer}
    Student Answer: {student_answer}

    Evaluate the student's answer:
    1. Is it correct? (for subjective questions, use judgment)
    2. Provide specific feedback
    3. If wrong, explain the concept
    4. Suggest improvements

    Return JSON:
    {{
      "correct": true/false,
      "points_earned": 8,
      "feedback": "Your answer shows good understanding...",
      "partial_credit": true
    }}
    """

    async def grade_answer(
        self,
        question: Dict,
        student_answer: str
    ) -> Dict:
        """Grade a single answer with AI feedback"""
        pass

    async def grade_code_answer(
        self,
        question: Dict,
        student_code: str
    ) -> Dict:
        """Grade code submission by running test cases"""
        # Execute code safely in sandbox
        # Run test cases
        # Provide feedback on code quality
        pass

    async def generate_overall_feedback(
        self,
        quiz: Dict,
        attempt: Dict
    ) -> Dict:
        """Generate comprehensive feedback for entire quiz"""
        # Identify strengths and weaknesses
        # Provide personalized recommendations
        # Suggest next steps
        pass
```

### 2.4 API Endpoints

**File:** `server/roadmap_router.py`

```python
from fastapi import APIRouter, Depends
from auth import get_current_user
from rate_limit import limit_user

router = APIRouter(prefix="/api/roadmaps", tags=["roadmaps"])

@router.post("/generate")
async def generate_roadmap(
    request: RoadmapRequest,
    user = Depends(get_current_user),
    _limit = Depends(limit_user)
):
    """Generate a new learning roadmap based on user goals"""
    pass

@router.get("/")
async def get_user_roadmaps(
    user = Depends(get_current_user),
    status: Optional[str] = None
):
    """Get all roadmaps for current user"""
    pass

@router.get("/{roadmap_id}")
async def get_roadmap(
    roadmap_id: str,
    user = Depends(get_current_user)
):
    """Get specific roadmap with progress"""
    pass

@router.put("/{roadmap_id}/milestone/{milestone_id}")
async def update_milestone_progress(
    roadmap_id: str,
    milestone_id: str,
    progress: float,
    user = Depends(get_current_user)
):
    """Update progress on a milestone"""
    pass

@router.post("/{roadmap_id}/adapt")
async def adapt_roadmap(
    roadmap_id: str,
    insights: Dict,
    user = Depends(get_current_user)
):
    """AI-powered roadmap adaptation based on performance"""
    pass
```

**File:** `server/quiz_router.py`

```python
router = APIRouter(prefix="/api/quizzes", tags=["quizzes"])

@router.post("/generate")
async def generate_quiz(
    request: QuizGenerationRequest,
    user = Depends(get_current_user)
):
    """Generate quiz based on topics"""
    pass

@router.get("/conversation/{conversation_id}")
async def get_conversation_quizzes(
    conversation_id: str,
    user = Depends(get_current_user)
):
    """Get all quizzes for a conversation"""
    pass

@router.post("/{quiz_id}/attempt")
async def start_quiz_attempt(
    quiz_id: str,
    user = Depends(get_current_user)
):
    """Start a new quiz attempt"""
    pass

@router.post("/attempt/{attempt_id}/submit")
async def submit_quiz_answer(
    attempt_id: str,
    answer: QuizAnswerSubmission,
    user = Depends(get_current_user)
):
    """Submit answer for grading"""
    pass

@router.post("/attempt/{attempt_id}/complete")
async def complete_quiz(
    attempt_id: str,
    user = Depends(get_current_user)
):
    """Complete quiz and get final results"""
    pass

@router.get("/library")
async def get_quiz_library(
    user = Depends(get_current_user),
    difficulty: Optional[str] = None,
    topic: Optional[str] = None
):
    """Get all user's past quizzes for practice"""
    pass
```

---

## Phase 3: Agent Integration

### 3.1 Modify TutorAgent

**File:** `server/agent.py` (modifications)

```python
class TutorAgent:
    def __init__(self):
        # ... existing code ...
        self.roadmap_generator = RoadmapGeneratorAgent()
        self.quiz_generator = QuizGeneratorAgent()
        self.quiz_grader = QuizGraderAgent()

        # Add new nodes to workflow
        self.workflow.add_node("check_roadmap", self._check_roadmap_node)
        self.workflow.add_node("trigger_quiz", self._trigger_quiz_node)

    async def _check_roadmap_node(self, state: TutorState):
        """Check if we should generate or update roadmap"""

        # Extract learning goals from conversation
        if self._detect_new_learning_goal(state["messages"]):
            roadmap = await self.roadmap_generator.generate_roadmap(
                user_goal=state["user_goal"],
                conversation_history=state["messages"],
                user_context=state["user_context"]
            )

            # Store roadmap in database
            await self._save_roadmap(roadmap, state["user_id"])

            # Notify user about roadmap creation
            state["thinking_content"] += "\n✅ Created personalized learning roadmap"

        return state

    async def _trigger_quiz_node(self, state: TutorState):
        """Check if we should present a quiz"""

        # Get active roadmap
        roadmap = await self._get_active_roadmap(state["user_id"])

        if not roadmap:
            return state

        # Check if quiz should be triggered
        should_quiz = await self.quiz_generator.should_trigger_quiz(
            state["messages"],
            roadmap
        )

        if should_quiz:
            # Get topics covered recently
            topics = await self._extract_recent_topics(state["messages"])

            # Generate quiz
            quiz = await self.quiz_generator.generate_quiz(
                topics=topics,
                conversation_context=self._format_recent_context(state["messages"]),
                difficulty=roadmap["current_difficulty"]
            )

            # Save quiz
            quiz_id = await self._save_quiz(quiz, roadmap["id"], state["user_id"])

            # Insert quiz UI into conversation
            state["quiz_to_present"] = {
                "quiz_id": quiz_id,
                "title": quiz["title"],
                "message": "📝 Time for a quick knowledge check! This will help me understand your progress."
            }

        return state
```

### 3.2 Chat Endpoint Modifications

```python
@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    user = Depends(get_current_user)
):
    """Enhanced chat with quiz integration"""

    async def event_generator():
        # ... existing streaming logic ...

        # Check for quiz trigger
        if agent_response.get("quiz_to_present"):
            quiz_data = agent_response["quiz_to_present"]
            yield f"data: {json.dumps({
                'type': 'quiz_trigger',
                'quiz_id': quiz_data['quiz_id'],
                'message': quiz_data['message'],
                'quiz_data': quiz_data
            })}\n\n"

        # ... rest of response ...

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

---

## Phase 4: Frontend Implementation

### 4.1 Types

**File:** `frontend/types/roadmap.ts`

```typescript
export interface LearningRoadmap {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  domain: 'programming' | 'math' | 'general';
  roadmap_data: RoadmapData;
  total_milestones: number;
  completed_milestones: number;
  progress_percentage: number;
  current_phase_id?: string;
  current_milestone_id?: string;
  status: 'active' | 'completed' | 'paused' | 'abandoned';
  conversation_id?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface RoadmapData {
  phases: Phase[];
  total_milestones: number;
  completed_milestones: number;
}

export interface Phase {
  id: string;
  title: string;
  order: number;
  milestones: Milestone[];
}

export interface Milestone {
  id: string;
  title: string;
  type: 'lesson' | 'quiz';
  estimated_time: number;
  description?: string;
  topics?: string[];
  status: 'not_started' | 'in_progress' | 'completed' | 'locked';
  quiz_id?: string;
  progress?: number;
}

export interface ConversationQuiz {
  id: string;
  title: string;
  description?: string;
  topic: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  questions: QuizQuestion[];
  total_points: number;
  attempts_allowed: number;
  time_limit?: number;
  status: 'not_started' | 'in_progress' | 'completed' | 'skipped';
}

export interface QuizQuestion {
  id: string;
  type: 'multiple_choice' | 'true_false' | 'short_answer' | 'code';
  question: string;
  options?: string[];
  correct_answer: string;
  explanation: string;
  points: number;
  template?: string; // for code questions
  test_cases?: TestCase[];
}

export interface QuizAttempt {
  id: string;
  quiz_id: string;
  attempt_number: number;
  answers: Record<string, AnswerResult>;
  total_questions: number;
  correct_answers: number;
  points_earned: number;
  total_points: number;
  percentage_score: number;
  feedback?: string;
  strengths?: string[];
  weaknesses?: string[];
  recommendations?: string[];
  time_spent?: number;
  status: 'in_progress' | 'completed' | 'abandoned';
  passed: boolean;
  started_at: string;
  completed_at?: string;
}
```

### 4.2 Components

**Component 1:** `frontend/components/roadmap/RoadmapTimeline.tsx`

Visual timeline showing phases and milestones

**Component 2:** `frontend/components/roadmap/PhaseCard.tsx`

Individual phase with expandable milestones

**Component 3:** `frontend/components/roadmap/MilestoneItem.tsx`

Single milestone (lesson or quiz) with status

**Component 4:** `frontend/components/quiz/QuizPopup.tsx`

In-conversation quiz modal

**Component 5:** `frontend/components/quiz/QuizQuestion.tsx`

Individual question component (handles all types)

**Component 6:** `frontend/components/quiz/QuizResults.tsx`

Results screen with feedback

**Component 7:** `frontend/components/quiz/QuizLibrary.tsx`

Browse past quizzes for practice

### 4.3 Pages

**Page 1:** `frontend/app/dashboard/progress/page.tsx`

Main progress page with roadmap visualization

**Page 2:** `frontend/app/dashboard/quiz/page.tsx`

Quiz library and practice area

---

## Phase 5: Implementation Steps

### Step 1: Database Setup (Week 1)
- [ ] Create migration SQL for 4 new tables
- [ ] Add RLS policies
- [ ] Create indexes
- [ ] Test migrations in Supabase

### Step 2: Backend Core (Week 1-2)
- [ ] Implement RoadmapGeneratorAgent
- [ ] Implement QuizGeneratorAgent
- [ ] Implement QuizGraderAgent
- [ ] Create roadmap_router.py with endpoints
- [ ] Create quiz_router.py with endpoints

### Step 3: Agent Integration (Week 2)
- [ ] Modify TutorAgent to include roadmap/quiz nodes
- [ ] Add roadmap detection logic
- [ ] Add quiz triggering logic
- [ ] Update chat endpoint for quiz events

### Step 4: Frontend Infrastructure (Week 2-3)
- [ ] Create TypeScript types
- [ ] Build API client functions
- [ ] Create custom hooks (useRoadmap, useQuiz)

### Step 5: UI Components (Week 3)
- [ ] Build RoadmapTimeline component
- [ ] Build QuizPopup component
- [ ] Build QuizQuestion components (all types)
- [ ] Build QuizResults component

### Step 6: Pages (Week 3-4)
- [ ] Implement Progress page
- [ ] Implement Quiz Library page
- [ ] Integrate quiz popup in chat

### Step 7: Testing & Refinement (Week 4)
- [ ] Test roadmap generation accuracy
- [ ] Test quiz triggering logic
- [ ] Test grading accuracy
- [ ] Polish UI/UX
- [ ] Performance optimization

---

## Key Features Breakdown

### 1. Automatic Roadmap Generation
- Triggered when user expresses learning goal
- AI analyzes conversation to extract topics
- Generates structured learning path
- Inserts quiz checkpoints strategically

### 2. In-Conversation Quiz
- Appears as modal/popup during chat
- Smooth UX: "Let's pause for a quick check"
- Questions adapt to what was discussed
- Immediate feedback after submission

### 3. AI Grading
- Objective questions: auto-graded
- Subjective questions: AI evaluates understanding
- Code questions: execute + test + quality review
- Personalized feedback for each answer

### 4. Progress Visualization
- Timeline view of learning phases
- Visual indicators: completed, in-progress, locked
- Progress percentage per phase
- Overall roadmap completion

### 5. Quiz Library
- All past quizzes saved
- Filterable by topic, difficulty, date
- Retry for practice
- Track improvement over time

---

## Technical Considerations

### 1. Quiz Timing
- Don't interrupt active discussion
- Wait for natural pause (user asks "what's next?")
- Or after explaining 2-3 related concepts
- Use conversation sentiment analysis

### 2. Roadmap Adaptation
- Monitor quiz performance
- If user struggles: add remedial milestones
- If user excels: unlock advanced content
- Adjust estimated times based on actual pace

### 3. Grading Fairness
- Multiple correct answers for subjective questions
- Partial credit for close answers
- Detailed rubric for code questions
- Human review option for disputes

### 4. Performance
- Cache roadmap data in frontend
- Lazy load quiz questions
- Background grading for complex submissions
- Optimistic UI updates

### 5. Data Privacy
- All quiz data is user-specific
- RLS policies enforce isolation
- No leaderboards without consent
- Option to delete quiz history

---

## Success Metrics

### User Engagement
- % of users who complete generated roadmaps
- Average quiz completion rate
- Time spent on quizzes vs lessons
- Return rate to quiz library

### Learning Effectiveness
- Average quiz scores over time (should improve)
- Correlation between quiz scores and roadmap completion
- Topics that cause most difficulty
- Effectiveness of AI feedback

### System Performance
- Roadmap generation time
- Quiz generation time
- Grading latency
- UI responsiveness

---

## Future Enhancements

### Phase 6 (Future)
- Collaborative quizzes (compete with peers)
- Voice-based quizzes
- Gamification (badges, streaks)
- Spaced repetition for quiz reviews
- Export quiz results as certificates
- Integration with external learning platforms

---

## Implementation Priority

### Must Have (MVP)
1. ✅ Roadmap generation from conversation
2. ✅ Visual timeline progress tracking
3. ✅ Basic in-conversation quiz (multiple choice)
4. ✅ AI grading with feedback
5. ✅ Quiz library for practice

### Should Have
6. Code-based quiz questions
7. Adaptive roadmap (changes based on performance)
8. Detailed analytics on Progress page
9. Quiz retry with improved questions

### Nice to Have
10. Voice quizzes
11. Collaborative features
12. Advanced visualizations
13. Mobile optimization

---

## Next Steps

1. **Review & Approve** this plan
2. **Database Migration**: Create and run SQL
3. **Backend Development**: Start with agents
4. **Frontend Development**: Build core components
5. **Integration**: Connect everything in chat
6. **Testing**: Validate AI accuracy
7. **Launch**: Deploy to production

**Estimated Timeline:** 3-4 weeks for MVP

**Team Requirements:**
- 1 Backend Developer (Python/FastAPI)
- 1 Frontend Developer (React/TypeScript)
- 1 AI/ML Engineer (LangChain/LLM)
- 1 QA Engineer (Testing)

---

**Generated:** 2025-11-28
**Version:** 1.0
**Status:** Pending Approval
