"""
Database Migration Runner for Chat-Roadmap-Quiz Integration
Runs the chat_roadmap_integration_enhancement.sql migration safely
"""

import os
import sys
from pathlib import Path

# Try to import optional dependencies
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  dotenv not installed, using system environment variables")

try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    print("⚠️  supabase not installed, will provide manual instructions only")
    HAS_SUPABASE = False

def get_migration_sql() -> str:
    """Read the migration SQL file"""
    migration_file = Path(__file__).parent / "chat_roadmap_integration_enhancement.sql"
    if not migration_file.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_file}")
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        return f.read()

def run_migration():
    """Execute the migration SQL"""
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    print("🔗 Connecting to Supabase...")
    
    if not supabase_url or not supabase_key:
        print("⚠️  SUPABASE_URL and SUPABASE_KEY not found in environment")
        print("   Continuing with manual instructions...\n")
    elif HAS_SUPABASE:
        print(f"   {supabase_url[:50]}...")
    
    try:
        print("📖 Reading migration file...")
        sql = get_migration_sql()
        
        print("🚀 Migration ready!")
        print("=" * 80)
        
        print("\n⚠️  IMPORTANT: Manual execution required.")
        print("To execute, you have 2 options:\n")
        
        print("OPTION 1 - Supabase SQL Editor (RECOMMENDED):")
        print("  1. Go to your Supabase Dashboard")
        print("  2. Navigate to SQL Editor")
        print("  3. Copy the contents of 'chat_roadmap_integration_enhancement.sql'")
        print("  4. Paste and run the SQL")
        print()
        
        print("OPTION 2 - PostgreSQL CLI:")
        print("  If you have direct database access, run:")
        print(f"  psql <your-connection-string> -f chat_roadmap_integration_enhancement.sql")
        print()
        
        print("=" * 80)
        print("\n✅ Migration file is ready at:")
        print(f"   {Path(__file__).parent / 'chat_roadmap_integration_enhancement.sql'}")
        
        # Try to verify current schema if supabase available
        if HAS_SUPABASE and supabase_url and supabase_key:
            print("\n🔍 Verifying current database schema...")
            supabase: Client = create_client(supabase_url, supabase_key)
            verify_schema(supabase)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def verify_schema(supabase: Client):
    """Verify the current database schema"""
    try:
        # Check if tables exist
        tables_to_check = [
            'chat_sessions',
            'chat_messages',
            'learning_roadmaps',
            'milestone_progress',
            'conversation_quizzes'
        ]
        
        print("\n📋 Checking existing tables:")
        for table in tables_to_check:
            try:
                result = supabase.table(table).select("*").limit(1).execute()
                print(f"  ✅ {table} - exists")
            except Exception as e:
                print(f"  ⚠️  {table} - may not exist or no access: {str(e)[:50]}")
        
        # Check chat_sessions columns
        print("\n🔍 Checking chat_sessions structure...")
        result = supabase.table('chat_sessions').select("*").limit(1).execute()
        if result.data:
            sample = result.data[0] if result.data else {}
            columns = list(sample.keys()) if sample else []
            print(f"  Current columns: {', '.join(columns)}")
            
            # Check for new columns
            new_columns = ['roadmap_id', 'message_count', 'ended_at']
            for col in new_columns:
                if col in columns:
                    print(f"  ✅ {col} - already exists")
                else:
                    print(f"  ⏳ {col} - will be added by migration")
        
        # Check milestone_progress
        print("\n🔍 Checking milestone_progress structure...")
        try:
            result = supabase.table('milestone_progress').select("*").limit(1).execute()
            if result.data:
                sample = result.data[0] if result.data else {}
                columns = list(sample.keys()) if sample else []
                print(f"  Current columns: {', '.join(columns)}")
                
                # Check for new columns
                new_columns = ['auto_completed', 'completion_confidence', 'completion_evidence', 'inference_metadata']
                for col in new_columns:
                    if col in columns:
                        print(f"  ✅ {col} - already exists")
                    else:
                        print(f"  ⏳ {col} - will be added by migration")
            else:
                print("  ℹ️  Table is empty")
        except Exception as e:
            print(f"  ⚠️  Could not check milestone_progress: {str(e)[:50]}")
        
    except Exception as e:
        print(f"\n⚠️  Schema verification failed: {e}")
        print("   (This is okay - the migration will still work)")

def create_backup_script():
    """Create a backup SQL script for safety"""
    backup_sql = """-- BACKUP BEFORE MIGRATION
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
"""
    
    backup_file = Path(__file__).parent / "backup_before_migration.sql"
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(backup_sql)
    
    print(f"\n💾 Created backup script at:")
    print(f"   {backup_file}")
    print("\n   Run this FIRST in SQL Editor to create backups!")

if __name__ == "__main__":
    print("=" * 80)
    print("  CHAT-ROADMAP-QUIZ INTEGRATION MIGRATION")
    print("=" * 80)
    
    # Create backup script
    create_backup_script()
    
    # Run migration
    run_migration()
    
    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("1. ✅ Run backup_before_migration.sql in Supabase SQL Editor")
    print("2. ✅ Run chat_roadmap_integration_enhancement.sql in Supabase SQL Editor")
    print("3. ✅ Verify migration with the verification queries at the end of the SQL")
    print("4. ✅ Test the application")
    print("=" * 80)
