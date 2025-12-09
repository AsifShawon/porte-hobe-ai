-- BACKUP BEFORE MIGRATION
-- Run this BEFORE applying chat_roadmap_integration_enhancement.sql

-- Backup chat_sessions
CREATE TABLE IF NOT EXISTS chat_sessions_backup_20251130 AS 
SELECT * FROM chat_sessions;

-- Backup chat_messages
CREATE TABLE IF NOT EXISTS chat_messages_backup_20251130 AS 
SELECT * FROM chat_messages;

-- Backup learning_roadmaps
CREATE TABLE IF NOT EXISTS learning_roadmaps_backup_20251130 AS 
SELECT * FROM learning_roadmaps;

-- Backup milestone_progress (if exists)
DO $$ 
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'milestone_progress') THEN
    EXECUTE 'CREATE TABLE IF NOT EXISTS milestone_progress_backup_20251130 AS SELECT * FROM milestone_progress';
  END IF;
END $$;

-- Backup conversation_quizzes (if exists)
DO $$ 
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'conversation_quizzes') THEN
    EXECUTE 'CREATE TABLE IF NOT EXISTS conversation_quizzes_backup_20251130 AS SELECT * FROM conversation_quizzes';
  END IF;
END $$;

-- Verify backups
SELECT 
  'chat_sessions_backup_20251130' as backup_table,
  COUNT(*) as row_count 
FROM chat_sessions_backup_20251130
UNION ALL
SELECT 
  'chat_messages_backup_20251130',
  COUNT(*) 
FROM chat_messages_backup_20251130;
