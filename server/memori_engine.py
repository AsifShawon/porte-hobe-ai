"""
Memori-based Memory Engine for Porte Hobe AI

This module provides intelligent long-term memory management using Memori SDK v3.
Memori automatically extracts entities, builds relationships, and manages memory
by intercepting LLM calls.

Features:
- Automatic entity extraction and relationship mapping
- Intelligent context injection for LLM calls
- Multi-user memory isolation via attribution
- Smart memory augmentation (facts, preferences, skills, rules, events)

Memori v3 Key Concepts:
- Entity: Person, place, or thing (like a user) - entity_id
- Process: Your agent, LLM interaction, or program - process_id  
- Session: Groups LLM interactions together - auto-managed
- Augmentation: Background AI enhancement of memories
"""
from __future__ import annotations

import os
import logging
import sqlite3
from typing import Optional, Dict, Any, List, Callable
from pathlib import Path

from memori import Memori

logger = logging.getLogger(__name__)

# Process ID for this application
PROCESS_ID = "porte-hobe-ai-tutor"


def _get_sqlite_connection() -> sqlite3.Connection:
    """Get SQLite connection for Memori storage."""
    storage_dir = Path(__file__).parent / "storage"
    storage_dir.mkdir(exist_ok=True)
    db_path = storage_dir / "memori_memory.db"
    return sqlite3.connect(str(db_path))


def _get_postgres_connection_factory() -> Optional[Callable]:
    """Get PostgreSQL connection factory for Supabase if available."""
    try:
        import psycopg2
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if supabase_url and supabase_key:
            project_id = supabase_url.replace("https://", "").replace("http://", "").split(".")[0]
            connection_string = f"postgresql://postgres:{supabase_key}@db.{project_id}.supabase.co:5432/postgres"
            
            def get_connection():
                return psycopg2.connect(connection_string)
            
            return get_connection
    except ImportError:
        logger.debug("psycopg2 not available, will use SQLite")
    except Exception as e:
        logger.warning(f"Failed to setup PostgreSQL connection: {e}")
    
    return None


class MemoriEngine:
    """
    Wrapper for Memori SDK v3 to provide memory management for the AI tutor.

    Memori v3 works by:
    1. Registering your LLM client (OpenAI, Anthropic, etc.)
    2. Setting attribution (entity_id for user, process_id for app)
    3. Automatically intercepting LLM calls to extract and inject memories
    """

    def __init__(
        self,
        use_postgres: bool = True,
        verbose: bool = False
    ):
        self._initialized = False
        self._memori: Optional[Memori] = None
        self._registered_client = None
        
        conn_factory = None
        
        if use_postgres:
            conn_factory = _get_postgres_connection_factory()
            if conn_factory:
                logger.info("Using PostgreSQL/Supabase for memory storage")
        
        if conn_factory is None:
            storage_dir = Path(__file__).parent / "storage"
            storage_dir.mkdir(exist_ok=True)
            db_path = storage_dir / "memori_memory.db"
            logger.info(f"Using SQLite for memory storage: sqlite:///{db_path}")
            conn_factory = _get_sqlite_connection

        logger.info("Initializing Memori memory engine...")
        
        try:
            self._memori = Memori(conn=conn_factory)
            self._memori.config.storage.build()
            self._initialized = True
            logger.info("Memori memory engine initialized and enabled")
            
        except Exception as e:
            logger.error(f"Failed to initialize Memori: {e}")
            self._initialized = False

    @property
    def is_initialized(self) -> bool:
        return self._initialized and self._memori is not None

    def register_client(self, client: Any) -> Any:
        if not self.is_initialized:
            logger.warning("Memori not initialized, returning unwrapped client")
            return client
            
        try:
            self._memori.llm.register(client)
            self._registered_client = client
            logger.info("LLM client registered with Memori")
            return client
        except Exception as e:
            logger.error(f"Failed to register client: {e}")
            return client

    def set_attribution(self, user_id: str, process_id: str = PROCESS_ID) -> None:
        if not self.is_initialized:
            logger.warning("Memori not initialized, skipping attribution")
            return
            
        try:
            self._memori.attribution(entity_id=user_id, process_id=process_id)
            logger.debug(f"Attribution set: entity={user_id}, process={process_id}")
        except Exception as e:
            logger.error(f"Failed to set attribution: {e}")

    def new_session(self) -> None:
        if not self.is_initialized:
            return
        try:
            self._memori.new_session()
            logger.debug("New Memori session started")
        except Exception as e:
            logger.error(f"Failed to start new session: {e}")

    def set_session(self, session_id: str) -> None:
        if not self.is_initialized:
            return
        try:
            self._memori.set_session(session_id)
            logger.debug(f"Session set to: {session_id}")
        except Exception as e:
            logger.error(f"Failed to set session: {e}")

    def get_session_id(self) -> Optional[str]:
        if not self.is_initialized:
            return None
        try:
            return str(self._memori.config.session_id)
        except Exception:
            return None

    def recall(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not self.is_initialized:
            return []
        try:
            results = self._memori.recall(query, limit=limit)
            logger.debug(f"Recalled {len(results) if results else 0} memories")
            return results if results else []
        except Exception as e:
            logger.error(f"Memory recall failed: {e}")
            return []

    def wait_for_augmentation(self) -> None:
        if not self.is_initialized:
            return
        try:
            self._memori.augmentation.wait()
            logger.debug("Augmentation complete")
        except Exception as e:
            logger.error(f"Failed to wait for augmentation: {e}")

    def store_conversation(
        self,
        user_id: str,
        user_message: str,
        assistant_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if not self.is_initialized:
            return {"status": "error", "error": "Memori not initialized"}
        try:
            self.set_attribution(user_id)
            logger.info(f"Conversation context set for user {user_id}")
            return {
                "status": "success",
                "user_id": user_id,
                "message": "Attribution set. Use registered LLM client for automatic memory extraction."
            }
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
            return {"status": "error", "error": str(e)}

    def get_user_context(self, user_id: str, query: str = "") -> Dict[str, Any]:
        if not self.is_initialized:
            return {"memories": [], "error": "Memori not initialized"}
        try:
            self.set_attribution(user_id)
            memories = []
            if query:
                memories = self.recall(query, limit=5)
            return {
                "user_id": user_id,
                "memories": memories,
                "session_id": self.get_session_id()
            }
        except Exception as e:
            logger.error(f"Failed to get user context: {e}")
            return {"memories": [], "error": str(e)}

    def add_user_preference(
        self,
        user_id: str,
        preference: str,
        category: str = "learning_preference"
    ) -> Dict[str, Any]:
        if not self.is_initialized:
            return {"status": "error", "error": "Memori not initialized"}
        try:
            self.set_attribution(user_id)
            logger.info(f"Attribution set for preference tracking: {user_id}")
            return {
                "status": "success",
                "user_id": user_id,
                "message": "Attribution set. Preferences will be auto-extracted from conversations."
            }
        except Exception as e:
            logger.error(f"Failed to set preference attribution: {e}")
            return {"status": "error", "error": str(e)}

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        try:
            self.set_attribution(user_id)
            sample_memories = self.recall("learning preferences skills", limit=10)
            return {
                "user_id": user_id,
                "sample_memories": len(sample_memories) if sample_memories else 0,
                "session_id": self.get_session_id(),
                "augmentation_types": ["facts", "preferences", "skills", "rules", "events"],
                "message": "Memori automatically tracks and organizes memories"
            }
        except Exception as e:
            logger.error(f"Failed to get user stats: {e}")
            return {"status": "error", "error": str(e)}


# Global instance
_memori_engine: Optional[MemoriEngine] = None


def get_memori_engine() -> Optional[MemoriEngine]:
    return _memori_engine


def initialize_memori_engine(
    use_postgres: bool = True,
    verbose: bool = False
) -> Optional[MemoriEngine]:
    global _memori_engine
    
    if _memori_engine is None:
        try:
            _memori_engine = MemoriEngine(
                use_postgres=use_postgres,
                verbose=verbose
            )
            if not _memori_engine.is_initialized:
                logger.warning("Memori engine created but not fully initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Memori engine: {e}")
            _memori_engine = None
    
    return _memori_engine


# Backward compatibility functions
def store_user_memory(
    user_id: str,
    query: str,
    response: str,
    summary: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    engine = get_memori_engine()
    if engine is None or not engine.is_initialized:
        logger.warning("Memori engine not initialized")
        return {"status": "error", "error": "Memory engine not initialized"}
    
    return engine.store_conversation(
        user_id=user_id,
        user_message=query,
        assistant_response=response,
        metadata=metadata
    )


def search_user_memory(
    user_id: str,
    text: str,
    k: int = 5
) -> List[Dict[str, Any]]:
    engine = get_memori_engine()
    if engine is None or not engine.is_initialized:
        logger.warning("Memori engine not initialized")
        return []
    
    engine.set_attribution(user_id)
    return engine.recall(text, limit=k)


def search_universal_memory(text: str, k: int = 5) -> List[Dict[str, Any]]:
    engine = get_memori_engine()
    if engine is None or not engine.is_initialized:
        return []
    
    engine.set_attribution("universal_knowledge")
    return engine.recall(text, limit=k)
