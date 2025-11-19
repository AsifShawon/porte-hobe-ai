"""
Test script for Memori integration

This script tests the basic functionality of the Memori memory engine.
Run with: python test_memori.py
"""
import asyncio
import logging
from memori_engine import MemoriEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_memori_engine():
    """Test basic Memori engine functionality"""

    print("=" * 60)
    print("MEMORI ENGINE TEST")
    print("=" * 60)

    # Initialize engine
    print("\n1. Initializing Memori Engine...")
    try:
        engine = MemoriEngine(
            ollama_model="qwen2.5:3b-instruct-q5_K_M",
            verbose=True
        )
        print("✅ Memori engine initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return

    # Test storing a conversation
    print("\n2. Testing conversation storage...")
    try:
        result = engine.store_conversation(
            user_id="test_user_123",
            user_message="I'm learning Python and I love using lists",
            assistant_response="Great! Lists are fundamental data structures in Python. They're mutable, ordered collections.",
            metadata={"topic": "python_basics", "test": True}
        )
        print(f"✅ Conversation stored: {result}")
    except Exception as e:
        print(f"❌ Failed to store conversation: {e}")

    # Test adding a preference
    print("\n3. Testing preference storage...")
    try:
        result = engine.add_user_preference(
            user_id="test_user_123",
            preference="Prefers visual explanations with diagrams",
            category="learning_style"
        )
        print(f"✅ Preference stored: {result}")
    except Exception as e:
        print(f"❌ Failed to store preference: {e}")

    # Test getting user stats
    print("\n4. Testing user statistics...")
    try:
        stats = engine.get_user_stats("test_user_123")
        print(f"✅ User stats: {stats}")
    except Exception as e:
        print(f"❌ Failed to get stats: {e}")

    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)
    print("\n📝 Notes:")
    print("- Memori automatically extracts entities and relationships")
    print("- Memories are stored in the configured database")
    print("- Context is automatically injected during LLM calls")
    print("- Check the database for stored memories")


if __name__ == "__main__":
    asyncio.run(test_memori_engine())
