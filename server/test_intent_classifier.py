"""
Test script for Intent Classifier

Tests various query types to ensure proper intent detection.
Run with: python test_intent_classifier.py
"""
import asyncio
import logging
from intent_classifier import IntentClassifier, IntentType, ThinkingLevel

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


# Test queries for each intent type
TEST_QUERIES = {
    "LEARNING_NEW_TOPIC": [
        "I want to learn Calculus",
        "Teach me about Python programming",
        "I'm new to recursion",
        "Can you help me start learning data structures?",
        "Getting started with algebra"
    ],
    "ROADMAP_REQUEST": [
        "How do I master Python?",
        "What's the roadmap for learning web development?",
        "Create a study plan for calculus",
        "What should I learn to become a data scientist?"
    ],
    "SOLVING_PROBLEM": [
        "Solve 2x + 3 = 7",
        "Calculate the derivative of x^2 + 3x",
        "Find the area of a circle with radius 5",
        "What is 15% of 200?",
        "Evaluate the integral of sin(x)"
    ],
    "DEBUGGING_CODE": [
        "Why doesn't my code work?",
        "This loop isn't iterating properly",
        "I'm getting an IndexError, can you help?",
        "My function returns None instead of a value"
    ],
    "ASKING_QUESTION": [
        "What is a derivative?",
        "What are loops in programming?",
        "Define recursion",
        "What's the difference between a list and a tuple?"
    ],
    "REQUESTING_EXPLANATION": [
        "Explain how recursion works",
        "How does bubble sort algorithm work?",
        "Can you explain the concept of limits?",
        "Tell me about object-oriented programming"
    ],
    "PRACTICE_EXERCISES": [
        "Give me practice problems for algebra",
        "Can I have some Python coding exercises?",
        "Show me more calculus problems",
        "I need additional practice with loops"
    ],
    "GREETING": [
        "Hello",
        "Hi there!",
        "Good morning",
        "Hey, how are you?"
    ]
}


async def test_intent_classifier():
    """Test the intent classifier with various queries"""

    print("=" * 80)
    print("INTENT CLASSIFIER TEST SUITE")
    print("=" * 80)

    classifier = IntentClassifier()

    total_tests = 0
    correct_predictions = 0
    results_summary = []

    for expected_intent_name, queries in TEST_QUERIES.items():
        print(f"\n{'='*80}")
        print(f"Testing: {expected_intent_name}")
        print(f"{'='*80}\n")

        for query in queries:
            total_tests += 1
            print(f"Query: \"{query}\"")

            # Classify
            result = await classifier.classify(query)

            # Check if prediction matches expected
            predicted_intent = result.intent.name
            is_correct = (predicted_intent == expected_intent_name)

            if is_correct:
                correct_predictions += 1
                status = "✅ CORRECT"
            else:
                status = "❌ WRONG"

            print(f"  {status}")
            print(f"  Expected: {expected_intent_name}")
            print(f"  Predicted: {predicted_intent}")
            print(f"  Confidence: {result.confidence:.2f}")
            print(f"  Domain: {result.domain}")
            print(f"  Thinking Level: {result.thinking_level}")
            if result.topic:
                print(f"  Topic Extracted: {result.topic}")
            if result.reasoning:
                print(f"  Reasoning: {result.reasoning}")
            print()

            # Store result
            results_summary.append({
                "query": query,
                "expected": expected_intent_name,
                "predicted": predicted_intent,
                "correct": is_correct,
                "confidence": result.confidence,
                "thinking": str(result.thinking_level)
            })

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Correct Predictions: {correct_predictions}")
    print(f"Accuracy: {(correct_predictions/total_tests)*100:.1f}%")
    print()

    # Show thinking level distribution
    print("Thinking Level Distribution:")
    thinking_levels = {}
    for result in results_summary:
        thinking = result["thinking"]
        thinking_levels[thinking] = thinking_levels.get(thinking, 0) + 1

    for level, count in sorted(thinking_levels.items()):
        print(f"  {level}: {count} queries")

    print("\n" + "=" * 80)


async def test_single_query():
    """Test a single query interactively"""

    print("\n" + "=" * 80)
    print("SINGLE QUERY TEST")
    print("=" * 80)

    classifier = IntentClassifier()

    # Test the exact query from the screenshot
    test_query = "I want to learn Calculus"

    print(f"\nQuery: \"{test_query}\"")
    print("-" * 80)

    result = await classifier.classify(test_query)

    print(f"\n📊 Classification Results:")
    print(f"  Intent: {result.intent.name} ({result.intent.value})")
    print(f"  Confidence: {result.confidence:.2%}")
    print(f"  Domain: {result.domain.name}")
    print(f"  Thinking Level: {result.thinking_level.name}")
    print(f"  Topic: {result.topic or 'Not extracted'}")
    print(f"  User Level: {result.user_level or 'Unknown'}")
    print(f"  Reasoning: {result.reasoning}")

    print(f"\n💡 Recommended Response Type:")
    if result.intent == IntentType.LEARNING_NEW_TOPIC:
        print("  ✅ Should provide: LEARNING ROADMAP")
        print("  ✅ Should include:")
        print("     - Prerequisites")
        print("     - Learning path phases")
        print("     - First step to start")
        print("     - Estimated timeline")
    elif result.intent == IntentType.SOLVING_PROBLEM:
        print("  ⚠️  Should provide: STEP-BY-STEP SOLUTION")
        print("  (This is NOT what we want for learning queries!)")

    print(f"\n⚙️  Thinking Display:")
    if result.thinking_level == ThinkingLevel.NONE:
        print("  Skip thinking phase entirely")
    elif result.thinking_level == ThinkingLevel.MINIMAL:
        print("  Show brief planning (1-2 lines)")
    elif result.thinking_level == ThinkingLevel.MODERATE:
        print("  Show moderate thinking (roadmap planning)")
    elif result.thinking_level == ThinkingLevel.FULL:
        print("  Show complete reasoning process")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("\n🚀 Starting Intent Classifier Tests...\n")

    # Run single query test first
    asyncio.run(test_single_query())

    # Ask user if they want full test suite
    print("\n" + "=" * 80)
    response = input("\nRun full test suite? (y/n): ").strip().lower()

    if response == 'y':
        asyncio.run(test_intent_classifier())
    else:
        print("\n✅ Single query test completed!")
