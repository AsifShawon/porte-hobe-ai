-- ============================================================================
-- CHAT DATA UNIFICATION MIGRATION
-- Purpose:
--   * Introduce conversation_id to chat_sessions (for legacy continuity)
--   * Introduce message_type to chat_messages for richer classification
--   * Backfill legacy rows from old chat_history (simple log) into chat_sessions + chat_messages
--   * (Optional) Link conversation_quizzes to chat_sessions via session_id
--   * Provide compatibility view for legacy consumers expecting chat_history structure
-- Safe to re-run sections guarded by IF NOT EXISTS / ON CONFLICT DO NOTHING.
-- ============================================================================

BEGIN;

-- 1. Extensions (uuid generation)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- gen_random_uuid() is provided by pgcrypto
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 2. Schema adjustments ------------------------------------------------------
-- 2.1 Add conversation_id to chat_sessions (legacy mapping)
ALTER TABLE public.chat_sessions ADD COLUMN IF NOT EXISTS conversation_id uuid NULL;
CREATE INDEX IF NOT EXISTS idx_chat_sessions_conversation_id ON public.chat_sessions(conversation_id);

-- 2.2 Add message_type to chat_messages for richer classification
ALTER TABLE public.chat_messages ADD COLUMN IF NOT EXISTS message_type text NULL;
-- ADD CONSTRAINT doesn't support IF NOT EXISTS; emulate with catalog check
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chat_messages_message_type_check'
    ) THEN
        ALTER TABLE public.chat_messages
            ADD CONSTRAINT chat_messages_message_type_check
            CHECK (message_type = ANY (ARRAY['user','assistant','system','roadmap_trigger','quiz_trigger']));
    END IF;
END $$;
CREATE INDEX IF NOT EXISTS idx_chat_messages_message_type ON public.chat_messages(message_type);

-- 3. Legacy chat_history presence check --------------------------------------
-- If a legacy chat_history table exists (old simple schema), migrate its data.
DO $$
DECLARE
    legacy_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'chat_history'
    ) INTO legacy_exists;

    IF legacy_exists THEN
        -- 3.1 Create sessions for distinct (user_id, conversation_id) pairs
        --     Filter out orphan user_ids that do not exist in auth.users to satisfy FK constraint.
        --     Capture orphan user_ids for audit (optional) in a staging table.
        CREATE TABLE IF NOT EXISTS public.legacy_orphan_chat_users (
            user_id uuid PRIMARY KEY,
            first_seen timestamptz NOT NULL DEFAULT now()
        );

        -- Record orphan user_ids (those present in legacy chat_history but missing in auth.users)
        INSERT INTO public.legacy_orphan_chat_users (user_id)
        SELECT DISTINCT h.user_id
        FROM public.chat_history h
        LEFT JOIN auth.users u ON u.id = h.user_id
        WHERE u.id IS NULL
        ON CONFLICT DO NOTHING;

        WITH distinct_pairs AS (
            SELECT h.user_id, h.conversation_id
            FROM public.chat_history h
            JOIN auth.users u ON u.id = h.user_id  -- ensures only valid users
            GROUP BY h.user_id, h.conversation_id
        )
        INSERT INTO public.chat_sessions (id, user_id, conversation_id, title, metadata)
        SELECT gen_random_uuid(), user_id, conversation_id,
               CASE WHEN conversation_id IS NULL THEN 'Imported Chat (No Conversation ID)'
                    ELSE 'Imported Conversation' END,
               '{}'::jsonb
        FROM distinct_pairs
        ON CONFLICT DO NOTHING;

        -- 3.2 Backfill messages
        WITH session_map AS (
            SELECT cs.id AS session_id, cs.user_id, cs.conversation_id
            FROM public.chat_sessions cs
        ), legacy_rows AS (
            SELECT h.*, sm.session_id
            FROM public.chat_history h
            JOIN session_map sm
              ON sm.user_id = h.user_id
             AND ((sm.conversation_id IS NULL AND h.conversation_id IS NULL) OR sm.conversation_id = h.conversation_id)
            JOIN auth.users u ON u.id = h.user_id  -- ensure valid users only
        )
        INSERT INTO public.chat_messages (id, session_id, role, content, content_html, attachments,
                                          thinking_content, metadata, created_at, message_type)
        SELECT gen_random_uuid(), session_id, role, message, NULL, '[]'::jsonb,
               NULL, '{}'::jsonb, created_at, role
        FROM legacy_rows
        ON CONFLICT DO NOTHING;
    END IF;
END $$;

-- 4. conversation_quizzes session linkage -----------------------------------
ALTER TABLE public.conversation_quizzes ADD COLUMN IF NOT EXISTS session_id uuid NULL;
CREATE INDEX IF NOT EXISTS conversation_quizzes_session_id_idx ON public.conversation_quizzes(session_id);
UPDATE public.conversation_quizzes cq
SET session_id = cs.id
FROM public.chat_sessions cs
WHERE cq.conversation_id IS NOT NULL
  AND cq.session_id IS NULL
  AND cq.conversation_id = cs.conversation_id;

COMMIT;

-- 5. Compatibility view (replicates legacy chat_history shape) ---------------
CREATE OR REPLACE VIEW public.chat_history_view AS
SELECT m.id AS id,
       s.user_id AS user_id,
       s.conversation_id AS conversation_id,
       m.role AS role,
       m.content AS message,
       m.created_at AS created_at
FROM public.chat_messages m
JOIN public.chat_sessions s ON m.session_id = s.id;

-- 6. Summary notes -----------------------------------------------------------
-- * Future inserts should use chat_messages with message_type classification.
-- * Roadmap triggers: insert rows with role='system', message_type='roadmap_trigger' + metadata.
-- * Quiz triggers: message_type='quiz_trigger'.
-- * Legacy chat_history table can be dropped after validation (manual step).

-- 7. Validation queries (manual, not executed automatically):
--   SELECT COUNT(*) FROM public.chat_history; -- legacy
--   SELECT COUNT(*) FROM public.chat_messages WHERE message_type IN ('user','assistant','system');
--   SELECT * FROM public.chat_history_view LIMIT 20;

-- ============================================================================
-- END UNIFICATION MIGRATION
-- ============================================================================
