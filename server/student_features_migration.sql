-- ============================================================================
-- STUDENT FEATURES MIGRATION (Goals, Achievements, Practice, Resources)
-- Only creates NEW tables - skips existing ones
-- ============================================================================

-- ============================================================================
-- 1. GOALS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    goal_type VARCHAR(50) NOT NULL,
    target_value FLOAT NOT NULL,
    current_value FLOAT DEFAULT 0.0,
    unit VARCHAR(50) DEFAULT 'items',
    status VARCHAR(50) DEFAULT 'active',
    deadline TIMESTAMPTZ,
    topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    CONSTRAINT valid_values CHECK (target_value > 0 AND current_value >= 0)
);

CREATE INDEX IF NOT EXISTS goals_user_id_idx ON goals(user_id);
CREATE INDEX IF NOT EXISTS goals_status_idx ON goals(status);
CREATE INDEX IF NOT EXISTS goals_goal_type_idx ON goals(goal_type);
CREATE INDEX IF NOT EXISTS goals_created_at_idx ON goals(created_at DESC);

ALTER TABLE goals ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own goals" ON goals;
CREATE POLICY "Users can view their own goals"
    ON goals FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own goals" ON goals;
CREATE POLICY "Users can insert their own goals"
    ON goals FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own goals" ON goals;
CREATE POLICY "Users can update their own goals"
    ON goals FOR UPDATE
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own goals" ON goals;
CREATE POLICY "Users can delete their own goals"
    ON goals FOR DELETE
    USING (auth.uid() = user_id);


-- ============================================================================
-- 2. USER ACHIEVEMENTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    achievement_id VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    rarity VARCHAR(50) NOT NULL,
    icon VARCHAR(50) NOT NULL,
    points INTEGER DEFAULT 0,
    progress FLOAT DEFAULT 100.0,
    unlocked_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    CONSTRAINT unique_user_achievement UNIQUE(user_id, achievement_id)
);

CREATE INDEX IF NOT EXISTS user_achievements_user_id_idx ON user_achievements(user_id);
CREATE INDEX IF NOT EXISTS user_achievements_category_idx ON user_achievements(category);
CREATE INDEX IF NOT EXISTS user_achievements_rarity_idx ON user_achievements(rarity);
CREATE INDEX IF NOT EXISTS user_achievements_unlocked_at_idx ON user_achievements(unlocked_at DESC);

ALTER TABLE user_achievements ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own achievements" ON user_achievements;
CREATE POLICY "Users can view their own achievements"
    ON user_achievements FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "System can insert achievements" ON user_achievements;
CREATE POLICY "System can insert achievements"
    ON user_achievements FOR INSERT
    WITH CHECK (auth.uid() = user_id);


-- ============================================================================
-- 3. PRACTICE EXERCISES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS practice_exercises (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    exercise_type VARCHAR(50) NOT NULL,
    difficulty VARCHAR(50) NOT NULL,
    topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
    points INTEGER DEFAULT 10,
    time_limit INTEGER,
    content JSONB NOT NULL,
    hints TEXT[] DEFAULT '{}',
    solution TEXT,
    tags TEXT[] DEFAULT '{}',
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS practice_exercises_type_idx ON practice_exercises(exercise_type);
CREATE INDEX IF NOT EXISTS practice_exercises_difficulty_idx ON practice_exercises(difficulty);
CREATE INDEX IF NOT EXISTS practice_exercises_topic_id_idx ON practice_exercises(topic_id);
CREATE INDEX IF NOT EXISTS practice_exercises_created_at_idx ON practice_exercises(created_at DESC);

ALTER TABLE practice_exercises ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Anyone can view exercises" ON practice_exercises;
CREATE POLICY "Anyone can view exercises"
    ON practice_exercises FOR SELECT
    TO authenticated
    USING (true);

DROP POLICY IF EXISTS "Authenticated users can create exercises" ON practice_exercises;
CREATE POLICY "Authenticated users can create exercises"
    ON practice_exercises FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = created_by);


-- ============================================================================
-- 4. PRACTICE SUBMISSIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS practice_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    exercise_id UUID NOT NULL REFERENCES practice_exercises(id) ON DELETE CASCADE,
    answer TEXT NOT NULL,
    status VARCHAR(50) NOT NULL,
    score FLOAT DEFAULT 0.0,
    feedback TEXT,
    hints_used INTEGER DEFAULT 0,
    time_spent INTEGER,
    test_results JSONB DEFAULT '{}',
    submitted_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS practice_submissions_user_id_idx ON practice_submissions(user_id);
CREATE INDEX IF NOT EXISTS practice_submissions_exercise_id_idx ON practice_submissions(exercise_id);
CREATE INDEX IF NOT EXISTS practice_submissions_status_idx ON practice_submissions(status);
CREATE INDEX IF NOT EXISTS practice_submissions_submitted_at_idx ON practice_submissions(submitted_at DESC);

ALTER TABLE practice_submissions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own submissions" ON practice_submissions;
CREATE POLICY "Users can view their own submissions"
    ON practice_submissions FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own submissions" ON practice_submissions;
CREATE POLICY "Users can insert their own submissions"
    ON practice_submissions FOR INSERT
    WITH CHECK (auth.uid() = user_id);


-- ============================================================================
-- 5. RESOURCES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    url TEXT,
    topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
    category VARCHAR(50) DEFAULT 'general',
    tags TEXT[] DEFAULT '{}',
    is_favorite BOOLEAN DEFAULT FALSE,
    folder_id UUID,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS resources_user_id_idx ON resources(user_id);
CREATE INDEX IF NOT EXISTS resources_type_idx ON resources(resource_type);
CREATE INDEX IF NOT EXISTS resources_category_idx ON resources(category);
CREATE INDEX IF NOT EXISTS resources_topic_id_idx ON resources(topic_id);
CREATE INDEX IF NOT EXISTS resources_is_favorite_idx ON resources(is_favorite);
CREATE INDEX IF NOT EXISTS resources_updated_at_idx ON resources(updated_at DESC);
CREATE INDEX IF NOT EXISTS resources_tags_idx ON resources USING GIN(tags);

CREATE INDEX IF NOT EXISTS resources_search_idx ON resources
    USING GIN(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(content, '')));

ALTER TABLE resources ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own resources" ON resources;
CREATE POLICY "Users can view their own resources"
    ON resources FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own resources" ON resources;
CREATE POLICY "Users can insert their own resources"
    ON resources FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own resources" ON resources;
CREATE POLICY "Users can update their own resources"
    ON resources FOR UPDATE
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own resources" ON resources;
CREATE POLICY "Users can delete their own resources"
    ON resources FOR DELETE
    USING (auth.uid() = user_id);


-- ============================================================================
-- 6. RESOURCE FOLDERS TABLE
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

CREATE INDEX IF NOT EXISTS resource_folders_user_id_idx ON resource_folders(user_id);
CREATE INDEX IF NOT EXISTS resource_folders_parent_id_idx ON resource_folders(parent_id);

ALTER TABLE resource_folders ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own folders" ON resource_folders;
CREATE POLICY "Users can view their own folders"
    ON resource_folders FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own folders" ON resource_folders;
CREATE POLICY "Users can insert their own folders"
    ON resource_folders FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own folders" ON resource_folders;
CREATE POLICY "Users can update their own folders"
    ON resource_folders FOR UPDATE
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own folders" ON resource_folders;
CREATE POLICY "Users can delete their own folders"
    ON resource_folders FOR DELETE
    USING (auth.uid() = user_id);

-- Add foreign key to resources table (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_resources_folder'
    ) THEN
        ALTER TABLE resources
            ADD CONSTRAINT fk_resources_folder
            FOREIGN KEY (folder_id)
            REFERENCES resource_folders(id)
            ON DELETE SET NULL;
    END IF;
END $$;


-- ============================================================================
-- 7. HELPER FUNCTIONS
-- ============================================================================

-- Achievement leaderboard function
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


-- Auto-update updated_at function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Create triggers for auto-updating updated_at
DROP TRIGGER IF EXISTS update_goals_updated_at ON goals;
CREATE TRIGGER update_goals_updated_at BEFORE UPDATE ON goals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_exercises_updated_at ON practice_exercises;
CREATE TRIGGER update_exercises_updated_at BEFORE UPDATE ON practice_exercises
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_resources_updated_at ON resources;
CREATE TRIGGER update_resources_updated_at BEFORE UPDATE ON resources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_folders_updated_at ON resource_folders;
CREATE TRIGGER update_folders_updated_at BEFORE UPDATE ON resource_folders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- 8. SEED DATA - Sample Practice Exercises
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
)
ON CONFLICT DO NOTHING;

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
)
ON CONFLICT DO NOTHING;

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
)
ON CONFLICT DO NOTHING;


-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Tables created:
-- ✓ goals
-- ✓ user_achievements
-- ✓ practice_exercises
-- ✓ practice_submissions
-- ✓ resources
-- ✓ resource_folders
-- ============================================================================
