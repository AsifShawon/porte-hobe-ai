# Intent Classification System

## Overview

The Intent Classification System is the foundation of dynamic prompting in Porte Hobe AI. It analyzes user queries to determine **what the user wants** and guides the AI tutor to respond appropriately.

## Problem Solved

**Before:** The tutor treated all queries as "problems to solve", showing step-by-step solutions even when users wanted to learn a new topic.

**After:** The tutor detects user intent and adapts:
- Learning request → Roadmap + guidance
- Problem to solve → Step-by-step solution
- Quick question → Direct answer
- And more...

## Architecture

```
User Query
    ↓
┌─────────────────────────────────┐
│  Pattern-based Classification   │ ← Fast regex matching
│  (Fallback, low confidence)     │
└────────────┬────────────────────┘
             │
             ↓
┌─────────────────────────────────┐
│  LLM-based Classification       │ ← Nuanced understanding
│  (Primary, high confidence)     │
└────────────┬────────────────────┘
             │
             ↓
┌─────────────────────────────────┐
│  Merge & Finalize               │ ← Best of both
└────────────┬────────────────────┘
             │
             ↓
        IntentResult
             │
    ┌────────┴────────┐
    ↓                 ↓
Intent Type      Thinking Level
    ↓                 ↓
Dynamic Prompt   Conditional Display
```

## Intent Types

### 1. **Learning Intents**

#### `LEARNING_NEW_TOPIC`
User wants to start learning something new.

**Examples:**
- "I want to learn Calculus"
- "Teach me about Python"
- "I'm new to recursion"

**Response:** Learning roadmap with prerequisites, phases, and first step

**Thinking Level:** MINIMAL (just show roadmap planning)

---

#### `ROADMAP_REQUEST`
User wants a complete learning path or curriculum.

**Examples:**
- "How do I master Python?"
- "What's the roadmap for web development?"
- "Create a study plan for calculus"

**Response:** Comprehensive curriculum with timeline

**Thinking Level:** MINIMAL

---

#### `REVIEW_CONCEPT`
User wants to revisit/review a concept they've learned.

**Examples:**
- "Review recursion with me"
- "Let's go over loops again"
- "Can we revisit derivatives?"

**Response:** Concise review with key points and practice

**Thinking Level:** MODERATE

---

### 2. **Problem-Solving Intents**

#### `SOLVING_PROBLEM`
User has a specific problem to solve.

**Examples:**
- "Solve 2x + 3 = 7"
- "Calculate the derivative of x^2"
- "Find the area of a circle with radius 5"

**Response:** Step-by-step solution with reasoning

**Thinking Level:** FULL (show complete thought process)

---

#### `DEBUGGING_CODE`
User's code isn't working, needs help fixing it.

**Examples:**
- "Why doesn't my code work?"
- "I'm getting an IndexError"
- "This function returns None"

**Response:** Debug analysis with fix and explanation

**Thinking Level:** FULL (show debugging reasoning)

---

### 3. **Information Intents**

#### `ASKING_QUESTION`
User wants a direct answer to a factual question.

**Examples:**
- "What is a derivative?"
- "What are loops in programming?"
- "Define recursion"

**Response:** Direct answer with brief example

**Thinking Level:** NONE (skip thinking, answer directly)

---

#### `REQUESTING_EXPLANATION`
User wants detailed explanation of a concept.

**Examples:**
- "Explain how recursion works"
- "How does bubble sort work?"
- "Tell me about OOP"

**Response:** Detailed explanation with examples

**Thinking Level:** MODERATE

---

### 4. **Practice Intents**

#### `PRACTICE_EXERCISES`
User wants practice problems or exercises.

**Examples:**
- "Give me practice problems for algebra"
- "Can I have Python exercises?"
- "Show me more calculus problems"

**Response:** Set of practice problems with difficulty levels

**Thinking Level:** MINIMAL

---

#### `CHALLENGE_REQUEST`
User wants a challenging problem to test themselves.

**Examples:**
- "Give me a hard problem"
- "Challenge me with advanced calculus"
- "Test my Python skills"

**Response:** Difficult problem with hints available

**Thinking Level:** FULL

---

### 5. **Conversational Intents**

#### `GREETING`
Simple greetings or chitchat.

**Examples:**
- "Hello"
- "Hi there"
- "Good morning"

**Response:** Friendly greeting + ask what they want to learn

**Thinking Level:** NONE

---

#### `FEEDBACK`
User providing feedback on previous response.

**Examples:**
- "That was helpful"
- "I understand now"
- "Can you explain more?"

**Response:** Acknowledge and offer follow-up

**Thinking Level:** NONE

---

#### `UNCLEAR`
Intent cannot be determined clearly.

**Examples:**
- Ambiguous queries
- Multiple possible intents
- Very short queries

**Response:** Ask for clarification

**Thinking Level:** MODERATE

---

## Thinking Levels

The thinking level determines how much planning/reasoning to show:

| Level | When Used | Display |
|-------|-----------|---------|
| **NONE** | Direct questions, greetings | Skip thinking phase entirely |
| **MINIMAL** | Learning roadmaps, practice requests | 1-2 lines of planning |
| **MODERATE** | Explanations, reviews | Brief roadmap (3-5 lines) |
| **FULL** | Problem solving, debugging | Complete reasoning process |

## Domain Detection

The classifier also detects the subject domain:

- **PROGRAMMING**: Code, algorithms, languages
- **MATHEMATICS**: Calculus, algebra, geometry
- **GENERAL**: Generic or mixed topics
- **MIXED**: Both programming and math

This enables domain-specific prompts and model routing (future).

## Classification Process

### 1. Pattern-based (Fast)
```python
# Regex patterns for quick matching
"I want to learn (\w+)" → LEARNING_NEW_TOPIC
"Solve (.+)" → SOLVING_PROBLEM
"What is (.+)?" → ASKING_QUESTION
```

**Pros:** Instant, no LLM call
**Cons:** Limited to predefined patterns

### 2. LLM-based (Accurate)
```python
# Uses Ollama with classification prompt
LLM analyzes query context and nuance
Returns: intent, topic, confidence, reasoning
```

**Pros:** Understands nuance, context-aware
**Cons:** Slower, requires LLM call

### 3. Merge Strategy
- If LLM confidence > 0.7 → Use LLM result
- Else if Pattern confidence > 0.6 → Use Pattern result
- Otherwise → Use LLM but reduce confidence

## IntentResult Structure

```python
@dataclass
class IntentResult:
    # Classification
    intent: IntentType           # Detected intent
    confidence: float            # 0.0 to 1.0
    domain: Domain               # Subject area

    # Extracted entities
    topic: Optional[str]         # "calculus", "Python"
    problem_statement: str       # For SOLVING_PROBLEM
    specific_question: str       # For ASKING_QUESTION

    # Context
    user_level: str              # beginner/intermediate/advanced
    thinking_level: ThinkingLevel

    # Metadata
    keywords: List[str]
    reasoning: str               # Why this classification
```

## Usage

### Basic Usage

```python
from intent_classifier import classify_user_intent

# Classify a query
result = await classify_user_intent("I want to learn Calculus")

print(result.intent)           # LEARNING_NEW_TOPIC
print(result.thinking_level)   # MINIMAL
print(result.topic)            # "calculus"
print(result.confidence)       # 0.85
```

### With Context

```python
# Provide conversation history for better classification
history = [
    {"role": "user", "content": "I'm a beginner"},
    {"role": "assistant", "content": "Great! What would you like to learn?"}
]

result = await classify_user_intent(
    "Teach me calculus",
    conversation_history=history
)

print(result.user_level)  # "beginner" (inferred from history)
```

### Advanced Usage

```python
from intent_classifier import IntentClassifier

# Create classifier instance (reuse for multiple queries)
classifier = IntentClassifier(model_name="qwen2.5:3b-instruct-q5_K_M")

# Classify multiple queries
queries = [
    "I want to learn Python",
    "Solve 2x + 3 = 7",
    "What is a derivative?"
]

for query in queries:
    result = await classifier.classify(query)
    print(f"{query} → {result.intent.name} ({result.thinking_level.name})")
```

## Testing

### Run Test Suite

```bash
cd server
python test_intent_classifier.py
```

### Test Output

```
Query: "I want to learn Calculus"
  ✅ CORRECT
  Expected: LEARNING_NEW_TOPIC
  Predicted: LEARNING_NEW_TOPIC
  Confidence: 0.85
  Domain: MATHEMATICS
  Thinking Level: MINIMAL
  Topic Extracted: calculus
  Reasoning: User explicitly wants to start learning new topic

TEST SUMMARY
Total Tests: 35
Correct Predictions: 32
Accuracy: 91.4%
```

## Integration with TutorAgent

The intent classifier will be integrated into the agent workflow:

```python
# In agent.py (future)
class TutorAgent:
    async def process_query(self, query: str, history: List):
        # 1. Classify intent
        intent = await self.intent_classifier.classify(query, history)

        # 2. Select appropriate prompt based on intent
        prompt = self.prompt_manager.get_prompt(intent.intent)

        # 3. Conditionally show thinking
        if intent.thinking_level == ThinkingLevel.NONE:
            # Skip thinking, answer directly
            return await self._direct_answer(query, prompt)
        else:
            # Show thinking as needed
            return await self._answer_with_thinking(query, prompt, intent.thinking_level)
```

## Performance

- **Pattern matching:** ~1-2ms
- **LLM classification:** ~200-500ms (depends on Ollama)
- **Total classification time:** ~300-600ms
- **Accuracy:** ~85-95% (based on test suite)

## Future Enhancements

1. **Fine-tuned Classification Model**: Train a small classifier for faster detection
2. **Multi-language Support**: Detect intent in multiple languages
3. **Confidence Thresholds**: Ask for clarification when confidence < 0.6
4. **Learning from Feedback**: Improve classification based on user corrections
5. **Intent Chaining**: Detect multiple intents in complex queries

## Troubleshooting

### Low Confidence Classifications

If confidence is consistently low:
- Add more patterns to `INTENT_PATTERNS`
- Improve LLM classification prompt
- Provide conversation history for context

### Wrong Classifications

Check the reasoning in `IntentResult`:
```python
result = await classify_user_intent(query)
print(result.reasoning)  # See why this classification was made
```

### Performance Issues

- Use pattern-based only (skip LLM) for simple queries
- Cache recent classifications
- Use faster Ollama model for classification

---

**Version:** 1.0.0
**Status:** Production Ready ✅
**Last Updated:** 2025-11-19
