-- ============================================================================
-- QUIZ & PROGRESS SYSTEM MIGRATION
-- Learning Roadmaps + In-Conversation Quizzes
-- ============================================================================

-- ============================================================================
-- 1. LEARNING ROADMAPS TABLE
-- Stores AI-generated personalized learning paths
-- ============================================================================
CREATE TABLE IF NOT EXISTS learning_roadmaps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    domain VARCHAR(50) NOT NULL, -- 'programming', 'math', 'general'

    -- AI-generated roadmap structure (JSONB for flexibility)
    roadmap_data JSONB NOT NULL,
    /*
    Example structure:
    {
      "phases": [
        {
          "id": "phase_1",
          "title": "Python Basics",
          "order": 1,
          "description": "Learn fundamental Python concepts",
          "milestones": [
            {
              "id": "lesson_1",
              "title": "Variables and Data Types",
              "type": "lesson",
              "estimated_time": 30,
              "description": "Understanding variables",
              "topics": ["variables", "data_types"],
              "status": "not_started",
              "order": 1
            },
            {
              "id": "quiz_1",
              "title": "Variables Quiz",
              "type": "quiz",
              "estimated_time": 15,
              "topics": ["variables"],
              "difficulty": "beginner",
              "status": "locked",
              "quiz_id": "uuid-here",
              "order": 2
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

    -- Link to conversation where roadmap was created
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    chat_session_id UUID REFERENCES chat_sessions(id) ON DELETE SET NULL,

    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    CONSTRAINT valid_roadmap_progress CHECK (
        completed_milestones >= 0 AND
        completed_milestones <= total_milestones AND
        progress_percentage >= 0 AND
        progress_percentage <= 100
    )
);

CREATE INDEX IF NOT EXISTS learning_roadmaps_user_id_idx ON learning_roadmaps(user_id);
CREATE INDEX IF NOT EXISTS learning_roadmaps_status_idx ON learning_roadmaps(status);
CREATE INDEX IF NOT EXISTS learning_roadmaps_created_at_idx ON learning_roadmaps(created_at DESC);
CREATE INDEX IF NOT EXISTS learning_roadmaps_conversation_idx ON learning_roadmaps(conversation_id);
CREATE INDEX IF NOT EXISTS learning_roadmaps_domain_idx ON learning_roadmaps(domain);

-- RLS Policies
ALTER TABLE learning_roadmaps ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own roadmaps" ON learning_roadmaps;
CREATE POLICY "Users can view their own roadmaps"
    ON learning_roadmaps FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own roadmaps" ON learning_roadmaps;
CREATE POLICY "Users can insert their own roadmaps"
    ON learning_roadmaps FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own roadmaps" ON learning_roadmaps;
CREATE POLICY "Users can update their own roadmaps"
    ON learning_roadmaps FOR UPDATE
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own roadmaps" ON learning_roadmaps;
CREATE POLICY "Users can delete their own roadmaps"
    ON learning_roadmaps FOR DELETE
    USING (auth.uid() = user_id);


-- ============================================================================
-- 2. CONVERSATION QUIZZES TABLE
-- AI-generated quizzes that appear during conversations
-- ============================================================================
CREATE TABLE IF NOT EXISTS conversation_quizzes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    roadmap_id UUID REFERENCES learning_roadmaps(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,

    -- Quiz details
    title VARCHAR(200) NOT NULL,
    description TEXT,
    topic VARCHAR(200),
    difficulty VARCHAR(50) NOT NULL DEFAULT 'beginner', -- 'beginner', 'intermediate', 'advanced', 'expert'

    -- AI-generated questions (JSONB for flexibility)
    questions JSONB NOT NULL,
    /*
    Example structure:
    [
      {
        "id": "q1",
        "type": "multiple_choice",
        "question": "What is a variable in Python?",
        "options": ["A storage location", "A function", "A loop", "A class"],
        "correct_answer": "A storage location",
        "explanation": "Variables are containers for storing data values.",
        "points": 10,
        "order": 1
      },
      {
        "id": "q2",
        "type": "code",
        "question": "Write a function to add two numbers",
        "template": "def add(a, b):\n    # Your code here\n    pass",
        "test_cases": [
          {"input": [2, 3], "expected": 5},
          {"input": [10, -5], "expected": 5}
        ],
        "correct_answer": "def add(a, b):\n    return a + b",
        "explanation": "Use the return statement to output the sum",
        "points": 20,
        "order": 2
      },
      {
        "id": "q3",
        "type": "short_answer",
        "question": "Explain what a Python list is",
        "correct_answer": "A list is an ordered, mutable collection of items",
        "keywords": ["ordered", "mutable", "collection"],
        "explanation": "Lists can hold multiple items and can be modified",
        "points": 15,
        "order": 3
      }
    ]
    */

    -- Scoring
    total_points INTEGER NOT NULL DEFAULT 0,
    passing_score FLOAT DEFAULT 70.0, -- percentage needed to pass

    -- Attempt tracking
    attempts_allowed INTEGER DEFAULT 3,
    attempts_used INTEGER DEFAULT 0,

    -- Timing
    time_limit INTEGER, -- in minutes, null = no limit
    estimated_duration INTEGER DEFAULT 10, -- minutes

    -- Status
    status VARCHAR(50) DEFAULT 'not_started', -- 'not_started', 'in_progress', 'completed', 'skipped'

    -- Quiz trigger information
    trigger_condition VARCHAR(100), -- 'after_milestone', 'time_based', 'manual', 'ai_suggested'
    triggered_at TIMESTAMPTZ,
    presented_at TIMESTAMPTZ, -- when shown to user in conversation

    -- Phase and milestone link (from roadmap)
    phase_id VARCHAR(100),
    milestone_id VARCHAR(100),

    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS conversation_quizzes_user_id_idx ON conversation_quizzes(user_id);
CREATE INDEX IF NOT EXISTS conversation_quizzes_roadmap_id_idx ON conversation_quizzes(roadmap_id);
CREATE INDEX IF NOT EXISTS conversation_quizzes_conversation_idx ON conversation_quizzes(conversation_id);
CREATE INDEX IF NOT EXISTS conversation_quizzes_status_idx ON conversation_quizzes(status);
CREATE INDEX IF NOT EXISTS conversation_quizzes_difficulty_idx ON conversation_quizzes(difficulty);
CREATE INDEX IF NOT EXISTS conversation_quizzes_created_at_idx ON conversation_quizzes(created_at DESC);

-- RLS Policies
ALTER TABLE conversation_quizzes ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own quizzes" ON conversation_quizzes;
CREATE POLICY "Users can view their own quizzes"
    ON conversation_quizzes FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own quizzes" ON conversation_quizzes;
CREATE POLICY "Users can insert their own quizzes"
    ON conversation_quizzes FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own quizzes" ON conversation_quizzes;
CREATE POLICY "Users can update their own quizzes"
    ON conversation_quizzes FOR UPDATE
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own quizzes" ON conversation_quizzes;
CREATE POLICY "Users can delete their own quizzes"
    ON conversation_quizzes FOR DELETE
    USING (auth.uid() = user_id);


-- ============================================================================
-- 3. QUIZ ATTEMPTS TABLE
-- Tracks each attempt at a quiz with AI grading results
-- ============================================================================
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    quiz_id UUID NOT NULL REFERENCES conversation_quizzes(id) ON DELETE CASCADE,
    roadmap_id UUID REFERENCES learning_roadmaps(id) ON DELETE SET NULL,

    -- Attempt details
    attempt_number INTEGER NOT NULL DEFAULT 1,

    -- User answers (JSONB for flexibility)
    answers JSONB NOT NULL,
    /*
    Example structure:
    {
      "q1": {
        "answer": "A storage location",
        "correct": true,
        "points_earned": 10,
        "time_spent": 15,
        "feedback": "Correct! Well done."
      },
      "q2": {
        "answer": "def add(a, b):\n    return a + b",
        "correct": true,
        "points_earned": 20,
        "time_spent": 120,
        "test_results": [
          {"passed": true, "input": [2, 3], "output": 5, "expected": 5},
          {"passed": true, "input": [10, -5], "output": 5, "expected": 5}
        ],
        "feedback": "Great job! Clean and efficient code."
      },
      "q3": {
        "answer": "A list is a collection of items",
        "correct": true,
        "points_earned": 12,
        "partial_credit": true,
        "time_spent": 45,
        "feedback": "Good answer! You could also mention that lists are ordered and mutable."
      }
    }
    */

    -- Grading results (AI-powered)
    total_questions INTEGER NOT NULL,
    correct_answers INTEGER DEFAULT 0,
    partial_credit_answers INTEGER DEFAULT 0,
    points_earned FLOAT DEFAULT 0.0,
    total_points FLOAT NOT NULL,
    percentage_score FLOAT DEFAULT 0.0,

    -- AI-generated comprehensive feedback
    overall_feedback TEXT,
    strengths TEXT[], -- ["Good understanding of variables", "Clean code syntax"]
    weaknesses TEXT[], -- ["Need to review data types", "Struggled with loops"]
    recommendations TEXT[], -- ["Practice more with conditionals", "Review chapter 3"]
    next_topics TEXT[], -- ["Functions", "Lists and Tuples"]

    -- Timing
    time_spent INTEGER DEFAULT 0, -- total seconds spent
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    -- Status
    status VARCHAR(50) DEFAULT 'in_progress', -- 'in_progress', 'completed', 'abandoned'
    passed BOOLEAN DEFAULT FALSE,

    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS quiz_attempts_user_id_idx ON quiz_attempts(user_id);
CREATE INDEX IF NOT EXISTS quiz_attempts_quiz_id_idx ON quiz_attempts(quiz_id);
CREATE INDEX IF NOT EXISTS quiz_attempts_roadmap_id_idx ON quiz_attempts(roadmap_id);
CREATE INDEX IF NOT EXISTS quiz_attempts_status_idx ON quiz_attempts(status);
CREATE INDEX IF NOT EXISTS quiz_attempts_created_at_idx ON quiz_attempts(created_at DESC);
CREATE INDEX IF NOT EXISTS quiz_attempts_passed_idx ON quiz_attempts(passed);

-- RLS Policies
ALTER TABLE quiz_attempts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own attempts" ON quiz_attempts;
CREATE POLICY "Users can view their own attempts"
    ON quiz_attempts FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own attempts" ON quiz_attempts;
CREATE POLICY "Users can insert their own attempts"
    ON quiz_attempts FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own attempts" ON quiz_attempts;
CREATE POLICY "Users can update their own attempts"
    ON quiz_attempts FOR UPDATE
    USING (auth.uid() = user_id);


-- ============================================================================
-- 4. MILESTONE PROGRESS TABLE
-- Tracks individual milestone completion in roadmaps
-- ============================================================================
CREATE TABLE IF NOT EXISTS milestone_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    roadmap_id UUID NOT NULL REFERENCES learning_roadmaps(id) ON DELETE CASCADE,

    -- Milestone identification (from roadmap_data JSONB)
    phase_id VARCHAR(100) NOT NULL,
    milestone_id VARCHAR(100) NOT NULL,
    milestone_title VARCHAR(200),
    milestone_type VARCHAR(50), -- 'lesson', 'quiz'

    -- Progress tracking
    status VARCHAR(50) DEFAULT 'not_started', -- 'not_started', 'in_progress', 'completed', 'skipped'
    progress_percentage FLOAT DEFAULT 0.0,

    -- Associated quiz (if milestone is a quiz)
    quiz_id UUID REFERENCES conversation_quizzes(id) ON DELETE SET NULL,
    quiz_passed BOOLEAN,
    best_quiz_score FLOAT,

    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    time_spent INTEGER DEFAULT 0, -- seconds

    -- Metadata
    notes TEXT, -- User's notes about this milestone
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_user_milestone UNIQUE(user_id, roadmap_id, phase_id, milestone_id)
);

CREATE INDEX IF NOT EXISTS milestone_progress_user_id_idx ON milestone_progress(user_id);
CREATE INDEX IF NOT EXISTS milestone_progress_roadmap_id_idx ON milestone_progress(roadmap_id);
CREATE INDEX IF NOT EXISTS milestone_progress_status_idx ON milestone_progress(status);
CREATE INDEX IF NOT EXISTS milestone_progress_phase_id_idx ON milestone_progress(phase_id);

-- RLS Policies
ALTER TABLE milestone_progress ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own milestone progress" ON milestone_progress;
CREATE POLICY "Users can view their own milestone progress"
    ON milestone_progress FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own milestone progress" ON milestone_progress;
CREATE POLICY "Users can insert their own milestone progress"
    ON milestone_progress FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own milestone progress" ON milestone_progress;
CREATE POLICY "Users can update their own milestone progress"
    ON milestone_progress FOR UPDATE
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own milestone progress" ON milestone_progress;
CREATE POLICY "Users can delete their own milestone progress"
    ON milestone_progress FOR DELETE
    USING (auth.uid() = user_id);


-- ============================================================================
-- 5. HELPER FUNCTIONS
-- ============================================================================

-- Function to calculate roadmap progress
CREATE OR REPLACE FUNCTION calculate_roadmap_progress(p_roadmap_id UUID)
RETURNS FLOAT AS $$
DECLARE
    total_milestones INTEGER;
    completed_milestones INTEGER;
    progress FLOAT;
BEGIN
    -- Count total and completed milestones
    SELECT COUNT(*), COUNT(*) FILTER (WHERE status = 'completed')
    INTO total_milestones, completed_milestones
    FROM milestone_progress
    WHERE roadmap_id = p_roadmap_id;

    IF total_milestones = 0 THEN
        RETURN 0.0;
    END IF;

    progress := (completed_milestones::FLOAT / total_milestones::FLOAT) * 100.0;

    -- Update roadmap table
    UPDATE learning_roadmaps
    SET
        completed_milestones = completed_milestones,
        progress_percentage = progress,
        updated_at = NOW()
    WHERE id = p_roadmap_id;

    RETURN progress;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


-- Function to get quiz statistics for a user
CREATE OR REPLACE FUNCTION get_quiz_statistics(p_user_id UUID)
RETURNS TABLE (
    total_quizzes INTEGER,
    completed_quizzes INTEGER,
    passed_quizzes INTEGER,
    average_score FLOAT,
    total_time_spent INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(DISTINCT cq.id)::INTEGER AS total_quizzes,
        COUNT(DISTINCT CASE WHEN cq.status = 'completed' THEN cq.id END)::INTEGER AS completed_quizzes,
        COUNT(DISTINCT CASE WHEN qa.passed = true THEN qa.quiz_id END)::INTEGER AS passed_quizzes,
        COALESCE(AVG(qa.percentage_score), 0.0)::FLOAT AS average_score,
        COALESCE(SUM(qa.time_spent), 0)::INTEGER AS total_time_spent
    FROM conversation_quizzes cq
    LEFT JOIN quiz_attempts qa ON cq.id = qa.quiz_id AND qa.status = 'completed'
    WHERE cq.user_id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers
DROP TRIGGER IF EXISTS update_learning_roadmaps_updated_at ON learning_roadmaps;
CREATE TRIGGER update_learning_roadmaps_updated_at
    BEFORE UPDATE ON learning_roadmaps
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_conversation_quizzes_updated_at ON conversation_quizzes;
CREATE TRIGGER update_conversation_quizzes_updated_at
    BEFORE UPDATE ON conversation_quizzes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_milestone_progress_updated_at ON milestone_progress;
CREATE TRIGGER update_milestone_progress_updated_at
    BEFORE UPDATE ON milestone_progress
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Tables created:
-- ✓ learning_roadmaps - AI-generated learning paths
-- ✓ conversation_quizzes - In-conversation quizzes
-- ✓ quiz_attempts - Quiz submissions and grading
-- ✓ milestone_progress - Individual milestone tracking
--
-- Helper functions:
-- ✓ calculate_roadmap_progress() - Auto-calculate progress
-- ✓ get_quiz_statistics() - User quiz stats
--
-- All tables have RLS policies and indexes for performance
-- ============================================================================
