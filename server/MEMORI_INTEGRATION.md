# Memori Integration Guide

## Overview

This project now uses **[Memori](https://github.com/GibsonAI/Memori)** for intelligent long-term memory management. Memori provides automatic entity extraction, relationship mapping, and smart memory retrieval for the AI tutoring system.

## What is Memori?

Memori is an open-source memory engine that gives LLMs persistent, queryable memory using standard SQL databases. It offers:

- **Automatic Entity Extraction**: Extracts facts, preferences, and skills from conversations
- **Relationship Mapping**: Builds connections between entities
- **Cost Savings**: 80-90% reduction vs. vector databases
- **Smart Retrieval**: Automatically injects relevant context during LLM calls
- **Multi-user Support**: Isolated memory spaces per user

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Backend                        │
│                                                           │
│  ┌────────────┐         ┌────────────┐                  │
│  │   Agent    │◄────────┤   Memori   │                  │
│  │  (Tutor)   │         │   Engine   │                  │
│  └─────┬──────┘         └──────┬─────┘                  │
│        │                       │                         │
│        │                       │                         │
│        ▼                       ▼                         │
│  ┌────────────┐         ┌────────────┐                  │
│  │  Ollama    │         │  Supabase  │                  │
│  │   LLM      │         │   (PG DB)  │                  │
│  └────────────┘         └────────────┘                  │
└─────────────────────────────────────────────────────────┘
```

## Key Files

### 1. `memori_engine.py`
Main Memori wrapper that provides:
- `MemoriEngine`: Core class for memory management
- `store_conversation()`: Store user-assistant conversations
- `add_user_preference()`: Explicitly add learning preferences
- `get_user_stats()`: Get memory statistics
- Backward compatibility functions

### 2. `agent.py` (Updated)
TutorAgent now includes:
- `memori_engine`: Instance of MemoriEngine
- `store_conversation_memory()`: Store chat in Memori
- `add_user_learning_preference()`: Add explicit preferences

### 3. `main.py` (Updated)
FastAPI endpoints updated:
- `/api/memory/add`: Now uses Memori for storage
- Automatic memory initialization on startup
- Fallback handling if Memori unavailable

## Usage

### Initialization

Memori is automatically initialized when the server starts:

```python
# In main.py lifespan
initialize_memori_engine(verbose=False)
tutor_agent = TutorAgent(enable_memori=True)
```

### Storing Conversations

After each chat interaction, store it in Memori:

```python
# Automatically happens in /api/memory/add endpoint
result = tutor_agent.store_conversation_memory(
    user_id="user_123",
    user_message="Explain recursion",
    assistant_response="Recursion is when a function calls itself...",
    metadata={"topic_id": "programming_basics"}
)
```

### Adding Explicit Preferences

```python
result = tutor_agent.add_user_learning_preference(
    user_id="user_123",
    preference="Prefers code examples over theory",
    category="learning_style"
)
```

### How Memory is Retrieved

Memori automatically injects relevant memories during LLM calls. No explicit retrieval needed!

```
User Query → Memori retrieves relevant context → LLM receives enriched prompt
```

## Database Configuration

Memori supports multiple databases:

### Option 1: Supabase PostgreSQL (Recommended)

If `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are set, Memori uses Supabase:

```bash
# .env file
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_key
```

Memori automatically constructs the PostgreSQL connection string.

### Option 2: SQLite (Fallback)

If Supabase env vars are not set, uses local SQLite:

```
server/storage/memori_memory.db
```

### Option 3: Custom Database

Pass a custom connection string:

```python
engine = MemoriEngine(
    database_url="postgresql://user:pass@host:5432/db"
)
```

## API Changes

### `/api/memory/add` (Updated)

**Before:**
```json
{
  "query": "User message",
  "response": "AI response",
  "summary": "Optional summary"
}
```

**After:**
Same interface, but now uses Memori internally for intelligent memory extraction.

**Response:**
```json
{
  "ok": true,
  "item": {
    "status": "success",
    "user_id": "user_123",
    "message": "Conversation stored with automatic memory extraction"
  },
  "engine": "memori"
}
```

## Testing

Run the test script to verify integration:

```bash
cd server
python test_memori.py
```

Expected output:
```
============================================================
MEMORI ENGINE TEST
============================================================

1. Initializing Memori Engine...
✅ Memori engine initialized successfully

2. Testing conversation storage...
✅ Conversation stored: {...}

3. Testing preference storage...
✅ Preference stored: {...}

4. Testing user statistics...
✅ User stats: {...}
```

## Benefits Over Previous System

| Feature | Old (embedding_engine.py) | New (Memori) |
|---------|---------------------------|--------------|
| Entity Extraction | Manual | Automatic |
| Relationship Mapping | None | Built-in |
| Context Injection | Manual search | Automatic |
| Cost | High (vector ops) | 80-90% lower |
| Memory Types | Generic | Facts, Preferences, Skills |
| Setup Complexity | High | One-line |

## Migration Notes

### No Data Migration Needed

The new Memori system is independent. Old memories in Supabase's `user_memory` table remain untouched. New memories go to Memori's database.

### Backward Compatibility

If Memori fails to initialize, the system gracefully falls back:

```python
if not tutor_agent.memori_engine:
    # Fallback: basic storage without Memori
    logger.warning("Memori not available")
```

## Troubleshooting

### Memori not initializing

**Check Ollama is running:**
```bash
ollama list
ollama serve  # If not running
```

**Check database connection:**
```bash
# For Supabase
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_KEY

# For SQLite
ls -la server/storage/memori_memory.db
```

### Import errors

**Ensure Memori is installed:**
```bash
pip install memorisdk>=2.3.0
```

### Memory not being stored

**Enable verbose logging:**
```python
engine = MemoriEngine(verbose=True)
```

Check logs for detailed information.

## Advanced Configuration

### Custom Memory Categories

```python
engine.add_user_preference(
    user_id="user_123",
    preference="Struggles with loops",
    category="pain_points"
)
```

### Multi-tenancy

Memori automatically isolates memories by user_id. Each user has their own memory space.

### Performance Tuning

For production, consider:
- Using PostgreSQL (Supabase) instead of SQLite
- Adjusting Memori's internal parameters
- Implementing memory cleanup policies

## Environment Variables

```bash
# Required for Ollama
OLLAMA_HOST=http://localhost:11434  # Optional, defaults to localhost

# Required for Supabase PostgreSQL
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_key

# Optional: Override model
MEMORI_MODEL=qwen2.5:3b-instruct-q5_K_M
```

## Resources

- **Memori GitHub**: https://github.com/GibsonAI/Memori
- **Memori Docs**: https://memori.dev
- **Ollama**: https://ollama.ai
- **Supabase**: https://supabase.com

## Support

For issues related to:
- **Memori SDK**: Open issue on [Memori GitHub](https://github.com/GibsonAI/Memori/issues)
- **Integration**: Check server logs and MEMORI_INTEGRATION.md
- **Database**: Verify Supabase connection or SQLite file permissions

---

**Last Updated**: 2025-11-19
**Version**: 1.0.0
**Status**: Production Ready ✅
