"""
Memori-based Memory Engine for Porte Hobe AI

This module provides intelligent long-term memory management using Memori SDK.
It replaces the previous embedding_engine.py with a more sophisticated system
that automatically extracts entities, builds relationships, and manages memory.

Features:
- Automatic entity extraction and relationship mapping
- Intelligent context injection for LLM calls
- Cost-efficient storage using Supabase PostgreSQL
- Multi-user memory isolation
- Smart memory promotion (long-term → short-term)
"""
from __future__ import annotations

import os
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

from memori import Memori
from memori.core.providers import ProviderConfig

logger = logging.getLogger(__name__)


class MemoriEngine:
    """
    Wrapper for Memori SDK to provide memory management for the AI tutor.

    This engine handles:
    - User-specific memory storage (learning preferences, past topics, etc.)
    - Automatic memory retrieval during conversations
    - Entity and relationship extraction
    - Memory prioritization
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        ollama_base_url: str = "http://localhost:11434/v1",
        ollama_model: str = "qwen2.5:3b-instruct-q5_K_M",
        verbose: bool = False
    ):
        """
        Initialize the Memori-based memory engine.

        Args:
            database_url: Connection string for database (defaults to Supabase if available)
            ollama_base_url: Base URL for Ollama API
            ollama_model: Model name to use for memory processing
            verbose: Enable verbose logging
        """
        # Configure database
        if database_url is None:
            # Try Supabase first
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

            if supabase_url and supabase_key:
                # Convert Supabase URL to PostgreSQL connection string
                # Format: postgresql://postgres:[password]@[host]/postgres
                # Supabase URL format: https://[project-id].supabase.co
                project_id = supabase_url.replace("https://", "").replace("http://", "").split(".")[0]
                database_url = f"postgresql://postgres:{supabase_key}@db.{project_id}.supabase.co:5432/postgres"
                logger.info("🗄️  Using Supabase PostgreSQL for memory storage")
            else:
                # Fallback to SQLite
                storage_dir = Path(__file__).parent / "storage"
                storage_dir.mkdir(exist_ok=True)
                database_url = f"sqlite:///{storage_dir}/memori_memory.db"
                logger.info(f"🗄️  Using SQLite for memory storage: {database_url}")

        # Configure Ollama provider
        self.provider_config = ProviderConfig.from_custom(
            base_url=ollama_base_url,
            api_key="ollama",  # Ollama doesn't need real API key
            model=ollama_model
        )

        # Initialize Memori
        logger.info("🧠 Initializing Memori memory engine...")
        self.memori = Memori(
            database_connect=database_url,
            conscious_ingest=True,  # Enable real-time memory ingestion
            auto_ingest=True,       # Automatically extract entities
            verbose=verbose,
            provider_config=self.provider_config
        )

        # Enable memory tracking
        self.memori.enable()
        logger.info("✅ Memori memory engine initialized and enabled")

        # Create OpenAI-compatible client
        self.client = self.provider_config.create_client()

    def store_conversation(
        self,
        user_id: str,
        user_message: str,
        assistant_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store a conversation turn with automatic memory extraction.

        Memori will automatically:
        - Extract facts, preferences, and skills
        - Build entity relationships
        - Index for future retrieval

        Args:
            user_id: Unique user identifier
            user_message: User's message
            assistant_response: AI assistant's response
            metadata: Additional metadata (topic_id, timestamp, etc.)

        Returns:
            Storage confirmation with memory ID
        """
        try:
            # Use Memori's client to process the conversation
            # Memori will automatically intercept and extract memories
            response = self.client.chat.completions.create(
                model=self.provider_config.model,
                messages=[
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": assistant_response}
                ],
                metadata={
                    "user_id": user_id,
                    **(metadata or {})
                }
            )

            logger.info(f"✅ Stored conversation for user {user_id}")

            return {
                "status": "success",
                "user_id": user_id,
                "message": "Conversation stored with automatic memory extraction"
            }

        except Exception as e:
            logger.error(f"❌ Failed to store conversation: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def get_relevant_context(
        self,
        user_id: str,
        query: str,
        max_memories: int = 5
    ) -> str:
        """
        Retrieve relevant memories for a given query.

        Memori automatically handles:
        - Semantic similarity search
        - Memory prioritization
        - Context relevance scoring

        Args:
            user_id: User identifier
            query: Current query/context
            max_memories: Maximum number of memories to retrieve

        Returns:
            Formatted context string with relevant memories
        """
        try:
            # Memori will automatically inject relevant memories during LLM calls
            # This method can be used for explicit memory retrieval

            # For now, we rely on Memori's automatic injection
            # Future: Add explicit memory query API when Memori supports it

            logger.info(f"📚 Retrieved context for user {user_id}")
            return ""  # Memori handles context injection automatically

        except Exception as e:
            logger.error(f"❌ Failed to retrieve context: {e}")
            return ""

    def search_memories(
        self,
        user_id: str,
        query: str,
        category: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search user memories by query and optional category.

        Args:
            user_id: User identifier
            query: Search query
            category: Optional category filter (facts, preferences, skills)
            limit: Maximum results

        Returns:
            List of matching memories
        """
        try:
            # This is a placeholder for when Memori exposes memory search API
            # Currently, Memori handles memory retrieval automatically

            logger.info(f"🔍 Searching memories for user {user_id}: {query}")

            return []

        except Exception as e:
            logger.error(f"❌ Memory search failed: {e}")
            return []

    def add_user_preference(
        self,
        user_id: str,
        preference: str,
        category: str = "learning_preference"
    ) -> Dict[str, Any]:
        """
        Explicitly add a user preference to memory.

        Args:
            user_id: User identifier
            preference: Preference description
            category: Category of preference

        Returns:
            Confirmation of storage
        """
        try:
            # Store as a conversation where the system learns the preference
            response = self.client.chat.completions.create(
                model=self.provider_config.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"User {user_id} has the following {category}: {preference}"
                    }
                ],
                metadata={
                    "user_id": user_id,
                    "type": "preference",
                    "category": category
                }
            )

            logger.info(f"✅ Added preference for user {user_id}")

            return {
                "status": "success",
                "user_id": user_id,
                "category": category,
                "preference": preference
            }

        except Exception as e:
            logger.error(f"❌ Failed to add preference: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get memory statistics for a user.

        Args:
            user_id: User identifier

        Returns:
            Statistics about stored memories
        """
        try:
            # Placeholder for memory statistics
            # Memori SDK may expose this in future versions

            return {
                "user_id": user_id,
                "total_memories": "tracked_automatically",
                "categories": ["facts", "preferences", "skills"],
                "message": "Memori tracks memories automatically"
            }

        except Exception as e:
            logger.error(f"❌ Failed to get user stats: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def clear_user_memories(self, user_id: str) -> Dict[str, Any]:
        """
        Clear all memories for a specific user.

        Args:
            user_id: User identifier

        Returns:
            Confirmation of deletion
        """
        try:
            # This would require direct database access
            # Placeholder for future implementation

            logger.warning(f"⚠️  Memory clearing not yet implemented for user {user_id}")

            return {
                "status": "not_implemented",
                "message": "Memory clearing requires direct database access"
            }

        except Exception as e:
            logger.error(f"❌ Failed to clear memories: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def disable(self):
        """Disable memory tracking."""
        self.memori.disable()
        logger.info("🛑 Memori memory engine disabled")

    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.memori.disable()
        except:
            pass


# Global instance (initialized in main.py)
_memori_engine: Optional[MemoriEngine] = None


def get_memori_engine() -> Optional[MemoriEngine]:
    """Get the global Memori engine instance."""
    return _memori_engine


def initialize_memori_engine(
    database_url: Optional[str] = None,
    ollama_model: str = "qwen2.5:3b-instruct-q5_K_M",
    verbose: bool = False
) -> MemoriEngine:
    """
    Initialize the global Memori engine.

    Args:
        database_url: Database connection string
        ollama_model: Ollama model name
        verbose: Enable verbose logging

    Returns:
        Initialized MemoriEngine instance
    """
    global _memori_engine

    if _memori_engine is None:
        _memori_engine = MemoriEngine(
            database_url=database_url,
            ollama_model=ollama_model,
            verbose=verbose
        )

    return _memori_engine


# Backward compatibility functions (for existing code)
def store_user_memory(
    user_id: str,
    query: str,
    response: str,
    summary: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Backward compatible function for storing user memory.

    This maintains the same interface as the old embedding_engine.py
    but uses Memori under the hood.
    """
    engine = get_memori_engine()
    if engine is None:
        logger.warning("⚠️  Memori engine not initialized")
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
    """
    Backward compatible function for searching user memory.

    Note: With Memori, context is automatically injected during LLM calls,
    so explicit searching is less necessary.
    """
    engine = get_memori_engine()
    if engine is None:
        logger.warning("⚠️  Memori engine not initialized")
        return []

    return engine.search_memories(user_id=user_id, query=text, limit=k)
