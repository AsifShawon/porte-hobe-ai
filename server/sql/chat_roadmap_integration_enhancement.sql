-- ============================================================================
-- CHAT-ROADMAP-QUIZ INTEGRATION ENHANCEMENT
-- Date: November 30, 2025
-- Purpose: Add missing columns and constraints to support:
--   1. Roadmap linking from chat_sessions
--   2. Enhanced message type classification
--   3. Milestone auto-completion tracking
--   4. Progress inference metadata
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. ENHANCE chat_sessions TABLE
-- ============================================================================

-- Add roadmap_id to link sessions to learning paths
ALTER TABLE public.chat_sessions 
  ADD COLUMN IF NOT EXISTS roadmap_id UUID REFERENCES learning_roadmaps(id) ON DELETE SET NULL;

-- Add index for roadmap lookups
CREATE INDEX IF NOT EXISTS idx_chat_sessions_roadmap_id 
  ON public.chat_sessions USING btree (roadmap_id);

-- Add message_count for tracking
ALTER TABLE public.chat_sessions 
  ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0;

-- Add ended_at for session tracking
ALTER TABLE public.chat_sessions 
  ADD COLUMN IF NOT EXISTS ended_at TIMESTAMPTZ;

COMMENT ON COLUMN public.chat_sessions.roadmap_id IS 'Links chat session to a learning roadmap for context';
COMMENT ON COLUMN public.chat_sessions.conversation_id IS 'Legacy conversation ID for backward compatibility';

-- ============================================================================
-- 2. ENHANCE chat_messages TABLE
-- ============================================================================

-- Update message_type constraint to include new types
ALTER TABLE public.chat_messages 
  DROP CONSTRAINT IF EXISTS chat_messages_message_type_check;

ALTER TABLE public.chat_messages 
  ADD CONSTRAINT chat_messages_message_type_check 
  CHECK (
    message_type = ANY (ARRAY[
      'user'::text,
      'assistant'::text,
      'system'::text,
      'roadmap_trigger'::text,
      'quiz_trigger'::text,
      'milestone_update'::text,
      'progress_event'::text,
      'user_message'::text,        -- Added for consistency
      'assistant_message'::text     -- Added for consistency
    ])
  );

-- Add GIN index on metadata for faster JSON queries
CREATE INDEX IF NOT EXISTS idx_chat_messages_metadata_gin 
  ON public.chat_messages USING GIN (metadata);

COMMENT ON COLUMN public.chat_messages.message_type IS 'Classification: user_message, assistant_message, system, roadmap_trigger, quiz_trigger, milestone_update, progress_event';
COMMENT ON COLUMN public.chat_messages.thinking_content IS 'AI reasoning/thinking process (Phase 1 output)';
COMMENT ON COLUMN public.chat_messages.metadata IS 'Additional context: roadmap_id, milestone_id, quiz_id, completion_inference';

-- ============================================================================
-- 3. ENHANCE milestone_progress TABLE
-- ============================================================================

-- Check if milestone_progress table exists
DO $$ 
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'milestone_progress'
  ) THEN
    
    -- Add auto-completion tracking columns
    ALTER TABLE public.milestone_progress
      ADD COLUMN IF NOT EXISTS auto_completed BOOLEAN DEFAULT FALSE;
    
    ALTER TABLE public.milestone_progress
      ADD COLUMN IF NOT EXISTS completion_confidence FLOAT;
    
    ALTER TABLE public.milestone_progress
      ADD COLUMN IF NOT EXISTS completion_evidence TEXT[];
    
    ALTER TABLE public.milestone_progress
      ADD COLUMN IF NOT EXISTS inference_metadata JSONB DEFAULT '{}'::jsonb;
    
    -- Add index for auto-completed milestones
    CREATE INDEX IF NOT EXISTS idx_milestone_progress_auto_completed 
      ON public.milestone_progress USING btree (auto_completed) 
      WHERE auto_completed = TRUE;
    
    COMMENT ON COLUMN public.milestone_progress.auto_completed IS 'TRUE if milestone was completed by AI inference, FALSE if manually completed';
    COMMENT ON COLUMN public.milestone_progress.completion_confidence IS 'AI confidence score (0.0-1.0) for auto-completion';
    COMMENT ON COLUMN public.milestone_progress.completion_evidence IS 'Quotes from conversation showing learning evidence';
    COMMENT ON COLUMN public.milestone_progress.inference_metadata IS 'Full AI analysis result (scores, gaps, recommendations)';
    
  END IF;
END $$;

-- ============================================================================
-- 4. ENHANCE conversation_quizzes TABLE
-- ============================================================================

-- Check if conversation_quizzes table exists
DO $$ 
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'conversation_quizzes'
  ) THEN
    
    -- Add session_id to link quizzes to chat sessions
    ALTER TABLE public.conversation_quizzes
      ADD COLUMN IF NOT EXISTS session_id UUID REFERENCES chat_sessions(id) ON DELETE SET NULL;
    
    -- Add index for session lookups
    CREATE INDEX IF NOT EXISTS idx_conversation_quizzes_session_id 
      ON public.conversation_quizzes USING btree (session_id);
    
    COMMENT ON COLUMN public.conversation_quizzes.session_id IS 'Links quiz to the chat session where it was offered/taken';
    
  END IF;
END $$;

-- ============================================================================
-- 5. CREATE HELPER FUNCTIONS
-- ============================================================================

-- Function to get or create chat session
CREATE OR REPLACE FUNCTION public.get_or_create_chat_session(
  p_user_id UUID,
  p_conversation_id UUID DEFAULT NULL,
  p_roadmap_id UUID DEFAULT NULL,
  p_title TEXT DEFAULT 'New Chat'
) RETURNS UUID AS $$
DECLARE
  v_session_id UUID;
BEGIN
  -- Try to find existing session by conversation_id or roadmap_id
  SELECT id INTO v_session_id
  FROM public.chat_sessions
  WHERE user_id = p_user_id
    AND (
      (p_conversation_id IS NOT NULL AND conversation_id = p_conversation_id)
      OR (p_roadmap_id IS NOT NULL AND roadmap_id = p_roadmap_id)
    )
  ORDER BY created_at DESC
  LIMIT 1;

  -- Create new session if not found
  IF v_session_id IS NULL THEN
    INSERT INTO public.chat_sessions (
      user_id, 
      conversation_id, 
      roadmap_id,
      title,
      metadata
    )
    VALUES (
      p_user_id, 
      COALESCE(p_conversation_id, gen_random_uuid()), 
      p_roadmap_id,
      p_title,
      '{}'::jsonb
    )
    RETURNING id INTO v_session_id;
  END IF;

  RETURN v_session_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION public.get_or_create_chat_session IS 'Get existing or create new chat session with roadmap/conversation linking';

-- Function to update session message count
CREATE OR REPLACE FUNCTION public.update_session_message_count()
RETURNS TRIGGER AS $$
BEGIN
  -- Increment message count on insert
  IF TG_OP = 'INSERT' THEN
    UPDATE public.chat_sessions
    SET message_count = message_count + 1,
        updated_at = NOW()
    WHERE id = NEW.session_id;
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for message count (drop if exists first)
DROP TRIGGER IF EXISTS update_session_message_count_trigger ON public.chat_messages;

CREATE TRIGGER update_session_message_count_trigger
  AFTER INSERT ON public.chat_messages
  FOR EACH ROW
  EXECUTE FUNCTION public.update_session_message_count();

COMMENT ON FUNCTION public.update_session_message_count IS 'Automatically updates chat_sessions.message_count when messages are added';

-- Function to get session statistics
CREATE OR REPLACE FUNCTION public.get_session_statistics(p_session_id UUID)
RETURNS TABLE (
  total_messages BIGINT,
  user_messages BIGINT,
  assistant_messages BIGINT,
  roadmap_triggers BIGINT,
  quiz_triggers BIGINT,
  milestone_updates BIGINT,
  first_message_at TIMESTAMPTZ,
  last_message_at TIMESTAMPTZ,
  session_duration_minutes INTEGER
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    COUNT(*)::BIGINT as total_messages,
    COUNT(*) FILTER (WHERE message_type IN ('user', 'user_message'))::BIGINT as user_messages,
    COUNT(*) FILTER (WHERE message_type IN ('assistant', 'assistant_message'))::BIGINT as assistant_messages,
    COUNT(*) FILTER (WHERE message_type = 'roadmap_trigger')::BIGINT as roadmap_triggers,
    COUNT(*) FILTER (WHERE message_type = 'quiz_trigger')::BIGINT as quiz_triggers,
    COUNT(*) FILTER (WHERE message_type = 'milestone_update')::BIGINT as milestone_updates,
    MIN(created_at) as first_message_at,
    MAX(created_at) as last_message_at,
    EXTRACT(EPOCH FROM (MAX(created_at) - MIN(created_at)))/60 as session_duration_minutes
  FROM public.chat_messages
  WHERE session_id = p_session_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION public.get_session_statistics IS 'Returns comprehensive statistics for a chat session';

-- ============================================================================
-- 6. CREATE VIEWS FOR CONVENIENCE
-- ============================================================================

-- View: Active learning sessions (sessions linked to roadmaps)
CREATE OR REPLACE VIEW public.active_learning_sessions AS
SELECT 
  s.id as session_id,
  s.user_id,
  s.conversation_id,
  s.title as session_title,
  s.message_count,
  s.created_at as session_started_at,
  s.updated_at as last_activity_at,
  r.id as roadmap_id,
  r.title as roadmap_title,
  r.domain,
  r.progress_percentage,
  r.current_milestone_id,
  r.status as roadmap_status
FROM public.chat_sessions s
INNER JOIN public.learning_roadmaps r ON s.roadmap_id = r.id
WHERE s.ended_at IS NULL
  AND r.status = 'active';

COMMENT ON VIEW public.active_learning_sessions IS 'Active chat sessions linked to learning roadmaps';

-- View: Message type distribution by session
CREATE OR REPLACE VIEW public.session_message_types AS
SELECT 
  session_id,
  message_type,
  COUNT(*) as message_count,
  MIN(created_at) as first_occurrence,
  MAX(created_at) as last_occurrence
FROM public.chat_messages
WHERE message_type IS NOT NULL
GROUP BY session_id, message_type;

COMMENT ON VIEW public.session_message_types IS 'Distribution of message types per session for analytics';

-- ============================================================================
-- 7. UPDATE EXISTING DATA (BACKFILL)
-- ============================================================================

-- Set default message_type for existing messages where NULL
UPDATE public.chat_messages
SET message_type = CASE 
  WHEN role = 'user' THEN 'user_message'
  WHEN role = 'assistant' THEN 'assistant_message'
  WHEN role = 'system' THEN 'system'
  ELSE 'assistant_message'
END
WHERE message_type IS NULL;

-- Update message_count for existing sessions
UPDATE public.chat_sessions s
SET message_count = (
  SELECT COUNT(*)
  FROM public.chat_messages m
  WHERE m.session_id = s.id
)
WHERE message_count = 0;

-- ============================================================================
-- 8. ADD ROW LEVEL SECURITY POLICIES (if needed)
-- ============================================================================

-- Enable RLS on enhanced tables if not already enabled
DO $$ 
BEGIN
  -- chat_sessions RLS
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'chat_sessions'
    AND policyname = 'Users can view their own chat sessions'
  ) THEN
    ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;
    
    CREATE POLICY "Users can view their own chat sessions"
      ON public.chat_sessions FOR SELECT
      USING (auth.uid() = user_id);
    
    CREATE POLICY "Users can insert their own chat sessions"
      ON public.chat_sessions FOR INSERT
      WITH CHECK (auth.uid() = user_id);
    
    CREATE POLICY "Users can update their own chat sessions"
      ON public.chat_sessions FOR UPDATE
      USING (auth.uid() = user_id);
  END IF;

  -- chat_messages RLS
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'chat_messages'
    AND policyname = 'Users can view messages in their sessions'
  ) THEN
    ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;
    
    CREATE POLICY "Users can view messages in their sessions"
      ON public.chat_messages FOR SELECT
      USING (
        session_id IN (
          SELECT id FROM public.chat_sessions WHERE user_id = auth.uid()
        )
      );
    
    CREATE POLICY "Users can insert messages in their sessions"
      ON public.chat_messages FOR INSERT
      WITH CHECK (
        session_id IN (
          SELECT id FROM public.chat_sessions WHERE user_id = auth.uid()
        )
      );
  END IF;
END $$;

COMMIT;

-- ============================================================================
-- VERIFICATION QUERIES (run after migration)
-- ============================================================================

-- Verify chat_sessions structure
SELECT 
  column_name, 
  data_type,
  is_nullable,
  column_default
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = 'chat_sessions' 
ORDER BY ordinal_position;

-- Verify chat_messages structure
SELECT 
  column_name, 
  data_type,
  is_nullable
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = 'chat_messages' 
ORDER BY ordinal_position;

-- Check message type distribution
SELECT 
  message_type, 
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM public.chat_messages 
WHERE message_type IS NOT NULL
GROUP BY message_type
ORDER BY count DESC;

-- Verify indexes created
SELECT 
  schemaname,
  tablename,
  indexname,
  indexdef
FROM pg_indexes
WHERE schemaname = 'public' 
  AND tablename IN ('chat_sessions', 'chat_messages', 'milestone_progress', 'conversation_quizzes')
ORDER BY tablename, indexname;

-- Check active learning sessions
SELECT 
  session_title,
  roadmap_title,
  message_count,
  progress_percentage,
  last_activity_at
FROM public.active_learning_sessions
LIMIT 10;

-- ============================================================================
-- ROLLBACK SCRIPT (if needed)
-- ============================================================================

/*
BEGIN;

-- Remove new columns
ALTER TABLE public.chat_sessions DROP COLUMN IF EXISTS roadmap_id CASCADE;
ALTER TABLE public.chat_sessions DROP COLUMN IF EXISTS message_count CASCADE;
ALTER TABLE public.chat_sessions DROP COLUMN IF EXISTS ended_at CASCADE;

ALTER TABLE public.milestone_progress DROP COLUMN IF EXISTS auto_completed CASCADE;
ALTER TABLE public.milestone_progress DROP COLUMN IF EXISTS completion_confidence CASCADE;
ALTER TABLE public.milestone_progress DROP COLUMN IF EXISTS completion_evidence CASCADE;
ALTER TABLE public.milestone_progress DROP COLUMN IF EXISTS inference_metadata CASCADE;

ALTER TABLE public.conversation_quizzes DROP COLUMN IF EXISTS session_id CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS public.get_or_create_chat_session(UUID, UUID, UUID, TEXT) CASCADE;
DROP FUNCTION IF EXISTS public.update_session_message_count() CASCADE;
DROP FUNCTION IF EXISTS public.get_session_statistics(UUID) CASCADE;

-- Drop views
DROP VIEW IF EXISTS public.active_learning_sessions CASCADE;
DROP VIEW IF EXISTS public.session_message_types CASCADE;

-- Drop trigger
DROP TRIGGER IF EXISTS update_session_message_count_trigger ON public.chat_messages;

COMMIT;
*/

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
