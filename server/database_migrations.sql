-- ============================================================================
-- DATABASE MIGRATIONS FOR STUDENT-FOCUSED FEATURES
-- Porte Hobe AI - Student Dashboard Enhancement
-- ============================================================================
-- Run this in your Supabase SQL Editor to create all necessary tables
-- ============================================================================

-- ============================================================================
-- 1. GOALS TABLE
-- For student study goals and milestones
-- ============================================================================
CREATE TABLE IF NOT EXISTS goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    goal_type VARCHAR(50) NOT NULL, -- daily, weekly, monthly, topic_completion, streak, practice
    target_value FLOAT NOT NULL,
    current_value FLOAT DEFAULT 0.0,
    unit VARCHAR(50) DEFAULT 'items', -- topics, minutes, days, points
    status VARCHAR(50) DEFAULT 'active', -- active, completed, failed, paused
    deadline TIMESTAMPTZ,
    topic_id TEXT REFERENCES topics(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    CONSTRAINT valid_values CHECK (target_value > 0 AND current_value >= 0)
);

-- Indexes for goals
CREATE INDEX IF NOT EXISTS goals_user_id_idx ON goals(user_id);
CREATE INDEX IF NOT EXISTS goals_status_idx ON goals(status);
CREATE INDEX IF NOT EXISTS goals_goal_type_idx ON goals(goal_type);
CREATE INDEX IF NOT EXISTS goals_created_at_idx ON goals(created_at DESC);

-- RLS Policies for goals
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own goals"
    ON goals FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own goals"
    ON goals FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own goals"
    ON goals FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own goals"
    ON goals FOR DELETE
    USING (auth.uid() = user_id);


-- ============================================================================
-- 2. USER ACHIEVEMENTS TABLE
-- For unlocked achievements/badges
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    achievement_id VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL, -- learning, streak, mastery, social, milestone, challenge
    rarity VARCHAR(50) NOT NULL, -- common, uncommon, rare, epic, legendary
    icon VARCHAR(50) NOT NULL,
    points INTEGER DEFAULT 0,
    progress FLOAT DEFAULT 100.0,
    unlocked_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',

    CONSTRAINT unique_user_achievement UNIQUE(user_id, achievement_id)
);

-- Indexes for achievements
CREATE INDEX IF NOT EXISTS user_achievements_user_id_idx ON user_achievements(user_id);
CREATE INDEX IF NOT EXISTS user_achievements_category_idx ON user_achievements(category);
CREATE INDEX IF NOT EXISTS user_achievements_rarity_idx ON user_achievements(rarity);
CREATE INDEX IF NOT EXISTS user_achievements_unlocked_at_idx ON user_achievements(unlocked_at DESC);

-- RLS Policies for achievements
ALTER TABLE user_achievements ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own achievements"
    ON user_achievements FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "System can insert achievements"
    ON user_achievements FOR INSERT
    WITH CHECK (auth.uid() = user_id);


-- ============================================================================
-- 3. PRACTICE EXERCISES TABLE
-- For coding challenges, quizzes, and practice problems
-- ============================================================================
CREATE TABLE IF NOT EXISTS practice_exercises (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    exercise_type VARCHAR(50) NOT NULL, -- coding, quiz, math, concept, debugging
    difficulty VARCHAR(50) NOT NULL, -- beginner, intermediate, advanced, expert
    topic_id TEXT REFERENCES topics(id) ON DELETE SET NULL,
    points INTEGER DEFAULT 10,
    time_limit INTEGER, -- in minutes
    content JSONB NOT NULL, -- exercise-specific content (code template, questions, etc.)
    hints TEXT[] DEFAULT '{}',
    solution TEXT,
    tags TEXT[] DEFAULT '{}',
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for exercises
CREATE INDEX IF NOT EXISTS practice_exercises_type_idx ON practice_exercises(exercise_type);
CREATE INDEX IF NOT EXISTS practice_exercises_difficulty_idx ON practice_exercises(difficulty);
CREATE INDEX IF NOT EXISTS practice_exercises_topic_id_idx ON practice_exercises(topic_id);
CREATE INDEX IF NOT EXISTS practice_exercises_created_at_idx ON practice_exercises(created_at DESC);

-- RLS Policies for exercises
ALTER TABLE practice_exercises ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view exercises"
    ON practice_exercises FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Authenticated users can create exercises"
    ON practice_exercises FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = created_by);


-- ============================================================================
-- 4. PRACTICE SUBMISSIONS TABLE
-- For student exercise submissions
-- ============================================================================
CREATE TABLE IF NOT EXISTS practice_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    exercise_id UUID NOT NULL REFERENCES practice_exercises(id) ON DELETE CASCADE,
    answer TEXT NOT NULL,
    status VARCHAR(50) NOT NULL, -- pending, correct, incorrect, partial
    score FLOAT DEFAULT 0.0,
    feedback TEXT,
    hints_used INTEGER DEFAULT 0,
    time_spent INTEGER, -- in seconds
    test_results JSONB DEFAULT '{}',
    submitted_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for submissions
CREATE INDEX IF NOT EXISTS practice_submissions_user_id_idx ON practice_submissions(user_id);
CREATE INDEX IF NOT EXISTS practice_submissions_exercise_id_idx ON practice_submissions(exercise_id);
CREATE INDEX IF NOT EXISTS practice_submissions_status_idx ON practice_submissions(status);
CREATE INDEX IF NOT EXISTS practice_submissions_submitted_at_idx ON practice_submissions(submitted_at DESC);

-- RLS Policies for submissions
ALTER TABLE practice_submissions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own submissions"
    ON practice_submissions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own submissions"
    ON practice_submissions FOR INSERT
    WITH CHECK (auth.uid() = user_id);


-- ============================================================================
-- 5. RESOURCES TABLE
-- For notes, bookmarks, snippets, and learning materials
-- ============================================================================
CREATE TABLE IF NOT EXISTS resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL, -- note, bookmark, snippet, file, reference
    title VARCHAR(200) NOT NULL,
    content TEXT,
    url TEXT,
    topic_id TEXT REFERENCES topics(id) ON DELETE SET NULL,
    category VARCHAR(50) DEFAULT 'general', -- programming, math, general, tutorial, documentation, example
    tags TEXT[] DEFAULT '{}',
    is_favorite BOOLEAN DEFAULT FALSE,
    folder_id UUID, -- Will reference resource_folders
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for resources
CREATE INDEX IF NOT EXISTS resources_user_id_idx ON resources(user_id);
CREATE INDEX IF NOT EXISTS resources_type_idx ON resources(resource_type);
CREATE INDEX IF NOT EXISTS resources_category_idx ON resources(category);
CREATE INDEX IF NOT EXISTS resources_topic_id_idx ON resources(topic_id);
CREATE INDEX IF NOT EXISTS resources_is_favorite_idx ON resources(is_favorite);
CREATE INDEX IF NOT EXISTS resources_updated_at_idx ON resources(updated_at DESC);
CREATE INDEX IF NOT EXISTS resources_tags_idx ON resources USING GIN(tags);

-- Full-text search index for title and content
CREATE INDEX IF NOT EXISTS resources_search_idx ON resources
    USING GIN(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(content, '')));

-- RLS Policies for resources
ALTER TABLE resources ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own resources"
    ON resources FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own resources"
    ON resources FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own resources"
    ON resources FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own resources"
    ON resources FOR DELETE
    USING (auth.uid() = user_id);


-- ============================================================================
-- 6. RESOURCE FOLDERS TABLE
-- For organizing resources
-- ============================================================================
CREATE TABLE IF NOT EXISTS resource_folders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES resource_folders(id) ON DELETE CASCADE,
    color VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for folders
CREATE INDEX IF NOT EXISTS resource_folders_user_id_idx ON resource_folders(user_id);
CREATE INDEX IF NOT EXISTS resource_folders_parent_id_idx ON resource_folders(parent_id);

-- RLS Policies for folders
ALTER TABLE resource_folders ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own folders"
    ON resource_folders FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own folders"
    ON resource_folders FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own folders"
    ON resource_folders FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own folders"
    ON resource_folders FOR DELETE
    USING (auth.uid() = user_id);

-- Add foreign key to resources table
ALTER TABLE resources
    ADD CONSTRAINT fk_resources_folder
    FOREIGN KEY (folder_id)
    REFERENCES resource_folders(id)
    ON DELETE SET NULL;


-- ============================================================================
-- 7. CHAT SESSIONS TABLE (if not exists)
-- For tracking user activity and streaks
-- ============================================================================
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    topic_id TEXT REFERENCES topics(id) ON DELETE SET NULL,
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ
);

-- Indexes for chat sessions
CREATE INDEX IF NOT EXISTS chat_sessions_user_id_idx ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS chat_sessions_created_at_idx ON chat_sessions(created_at DESC);

-- RLS Policies
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own chat sessions"
    ON chat_sessions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own chat sessions"
    ON chat_sessions FOR INSERT
    WITH CHECK (auth.uid() = user_id);


-- ============================================================================
-- 8. HELPER FUNCTIONS
-- ============================================================================

-- Function to get achievement leaderboard
CREATE OR REPLACE FUNCTION get_achievement_leaderboard(limit_count INTEGER)
RETURNS TABLE (
    user_id UUID,
    total_points INTEGER,
    achievement_count INTEGER,
    rank INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ua.user_id,
        SUM(ua.points)::INTEGER AS total_points,
        COUNT(*)::INTEGER AS achievement_count,
        ROW_NUMBER() OVER (ORDER BY SUM(ua.points) DESC)::INTEGER AS rank
    FROM user_achievements ua
    GROUP BY ua.user_id
    ORDER BY total_points DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for auto-updating updated_at
CREATE TRIGGER update_goals_updated_at BEFORE UPDATE ON goals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_exercises_updated_at BEFORE UPDATE ON practice_exercises
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resources_updated_at BEFORE UPDATE ON resources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_folders_updated_at BEFORE UPDATE ON resource_folders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- 9. SEED DATA - Sample Practice Exercises
-- ============================================================================

-- Sample coding exercise
INSERT INTO practice_exercises (title, description, exercise_type, difficulty, points, content, hints, solution, tags)
VALUES (
    'Hello World in Python',
    'Write a Python program that prints "Hello, World!" to the console.',
    'coding',
    'beginner',
    10,
    '{"language": "python", "template": "# Write your code here\ndef hello_world():\n    pass", "test_cases": [{"input": "", "expected": "Hello, World!"}]}',
    ARRAY['Use the print() function', 'Remember to include the exclamation mark'],
    'def hello_world():\n    print("Hello, World!")',
    ARRAY['python', 'basics', 'syntax']
);

-- Sample quiz exercise
INSERT INTO practice_exercises (title, description, exercise_type, difficulty, points, content, hints, solution, tags)
VALUES (
    'Python Basics Quiz',
    'Test your knowledge of Python fundamentals',
    'quiz',
    'beginner',
    15,
    '{"questions": [{"id": "q1", "text": "What is the correct way to create a variable?", "options": ["var x = 5", "x = 5", "int x = 5", "let x = 5"], "correct": "x = 5"}, {"id": "q2", "text": "Which keyword is used for functions?", "options": ["func", "def", "function", "define"], "correct": "def"}]}',
    ARRAY['Review Python syntax', 'Think about variable declaration'],
    '{"q1": "x = 5", "q2": "def"}',
    ARRAY['python', 'quiz', 'basics']
);

-- Sample math exercise
INSERT INTO practice_exercises (title, description, exercise_type, difficulty, points, content, hints, solution, tags)
VALUES (
    'Solve Linear Equation',
    'Solve for x: 2x + 5 = 15',
    'math',
    'beginner',
    10,
    '{"equation": "2x + 5 = 15", "type": "linear"}',
    ARRAY['Subtract 5 from both sides', 'Divide by 2'],
    '5',
    ARRAY['math', 'algebra', 'linear-equations']
);


-- ============================================================================
-- 10. SAMPLE ACHIEVEMENT DATA
-- Note: Achievements are defined in achievement_router.py and auto-unlocked
-- This table only stores unlocked achievements per user
-- ============================================================================


-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Next steps:
-- 1. Run this SQL in your Supabase SQL Editor
-- 2. Verify all tables are created
-- 3. Test the new API endpoints
-- 4. Create frontend components to use these endpoints
-- ============================================================================
