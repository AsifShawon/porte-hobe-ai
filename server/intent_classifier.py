"""
Intent Classification System for Porte Hobe AI

This module detects user intent from queries to enable dynamic, context-aware
responses. It classifies queries into categories like learning new topics,
solving problems, asking questions, etc.

Features:
- Fast intent detection using LLM
- Entity extraction (topics, problem statements)
- Confidence scoring
- Context-aware classification (uses conversation history)
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

logger = logging.getLogger(__name__)


# ============================================================================
# INTENT TYPES
# ============================================================================

class IntentType(Enum):
    """User intent categories for dynamic prompting"""

    # Learning intents
    LEARNING_NEW_TOPIC = "learning_new_topic"      # "I want to learn calculus"
    ROADMAP_REQUEST = "roadmap_request"            # "How do I master Python?"
    REVIEW_CONCEPT = "review_concept"              # "Review recursion with me"

    # Problem-solving intents
    SOLVING_PROBLEM = "solving_problem"            # "Solve 2x + 3 = 7"
    DEBUGGING_CODE = "debugging_code"              # "Why doesn't this work?"

    # Information intents
    ASKING_QUESTION = "asking_question"            # "What is a derivative?"
    REQUESTING_EXPLANATION = "requesting_explanation"  # "Explain how loops work"

    # Practice intents
    PRACTICE_EXERCISES = "practice_exercises"      # "Give me practice problems"
    CHALLENGE_REQUEST = "challenge_request"        # "Give me a hard problem"

    # Conversational intents
    GREETING = "greeting"                          # "Hello", "Hi"
    FEEDBACK = "feedback"                          # "That was helpful"
    UNCLEAR = "unclear"                            # Intent cannot be determined

    def __str__(self):
        return self.value


class ThinkingLevel(Enum):
    """How much thinking/planning the agent should show"""
    NONE = "none"           # Skip thinking entirely, direct answer
    MINIMAL = "minimal"     # Brief planning only (1-2 lines)
    MODERATE = "moderate"   # Some thinking (roadmap planning)
    FULL = "full"          # Complete reasoning process

    def __str__(self):
        return self.value


class Domain(Enum):
    """Subject domain for the query"""
    PROGRAMMING = "programming"
    MATHEMATICS = "mathematics"
    GENERAL = "general"
    MIXED = "mixed"

    def __str__(self):
        return self.value


# ============================================================================
# INTENT DATA STRUCTURE
# ============================================================================

@dataclass
class IntentResult:
    """Result of intent classification"""

    # Core classification
    intent: IntentType
    confidence: float  # 0.0 to 1.0
    domain: Domain

    # Extracted entities
    topic: Optional[str] = None              # "calculus", "Python", "recursion"
    problem_statement: Optional[str] = None  # For SOLVING_PROBLEM intent
    specific_question: Optional[str] = None  # For ASKING_QUESTION intent

    # Context
    user_level: Optional[str] = None         # "beginner", "intermediate", "advanced"
    thinking_level: ThinkingLevel = ThinkingLevel.MODERATE

    # Metadata
    keywords: List[str] = None
    reasoning: str = ""  # Why this classification was made

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/debugging"""
        return {
            "intent": str(self.intent),
            "confidence": self.confidence,
            "domain": str(self.domain),
            "topic": self.topic,
            "problem_statement": self.problem_statement,
            "specific_question": self.specific_question,
            "user_level": self.user_level,
            "thinking_level": str(self.thinking_level),
            "keywords": self.keywords,
            "reasoning": self.reasoning
        }


# ============================================================================
# INTENT CLASSIFIER
# ============================================================================

class IntentClassifier:
    """
    Classifies user intent using LLM-based analysis.

    Uses a lightweight classification prompt to quickly determine
    what the user wants to accomplish.
    """

    # Intent keywords for pattern matching (fallback)
    INTENT_PATTERNS = {
        IntentType.LEARNING_NEW_TOPIC: [
            r"(want to|how to|teach me|learn|start learning)\s+(?:about\s+)?(\w+)",
            r"(new to|beginner in|starting)\s+(\w+)",
            r"(introduce me to|getting started with)\s+(\w+)"
        ],
        IntentType.ROADMAP_REQUEST: [
            r"(roadmap|learning path|study plan|curriculum) (for|to)",
            r"(how (?:do I|can I|should I)) (master|learn|become|get good at)",
            r"(what should I learn|where (?:do I|should I) start)"
        ],
        IntentType.SOLVING_PROBLEM: [
            r"(solve|calculate|find|compute|evaluate)",
            r"(what is|what's) .+[\d\+\-\*\/\=\(\)]",  # Math expressions
            r"(x|y|z)\s*[\+\-\*\/\=]",  # Variables with operators
        ],
        IntentType.DEBUGGING_CODE: [
            r"(why (?:doesn't|does not|isn't|is not)|what's wrong)",
            r"(debug|fix|error|bug|issue|problem) (?:in|with)",
            r"(not working|doesn't work|failing)"
        ],
        IntentType.ASKING_QUESTION: [
            r"^(what is|what's|what are|define|definition of)",
            r"^(who|when|where|which|whose)",
            r"^(can you explain|could you tell me)"
        ],
        IntentType.REQUESTING_EXPLANATION: [
            r"(explain|how does|how do|describe)",
            r"(tell me (?:about|how|why))",
            r"(understand|concept of|idea of)"
        ],
        IntentType.PRACTICE_EXERCISES: [
            r"(give me|show me|can I (?:have|get)) .+ (practice|exercises|problems)",
            r"(practice|exercise|quiz|test) (?:on|for|about)",
            r"(more problems|additional exercises)"
        ],
        IntentType.GREETING: [
            r"^(hi|hello|hey|greetings|good morning|good afternoon|good evening)",
            r"^(what's up|how are you|how's it going)"
        ]
    }

    # Domain keywords
    DOMAIN_KEYWORDS = {
        Domain.PROGRAMMING: [
            'python', 'javascript', 'java', 'code', 'function', 'loop', 'array',
            'variable', 'class', 'object', 'algorithm', 'recursion', 'api',
            'database', 'framework', 'library', 'syntax', 'debug', 'compile'
        ],
        Domain.MATHEMATICS: [
            'algebra', 'calculus', 'geometry', 'trigonometry', 'derivative',
            'integral', 'equation', 'formula', 'theorem', 'proof', 'matrix',
            'vector', 'limit', 'function', 'graph', 'solve', 'calculate'
        ]
    }

    def __init__(self, model_name: str = "qwen2.5:3b-instruct-q5_K_M"):
        """
        Initialize the intent classifier.

        Args:
            model_name: Ollama model to use for classification
        """
        self.llm = ChatOllama(
            model=model_name,
            temperature=0.0,  # Deterministic classification
            num_predict=100   # Short response for classification
        )
        logger.info(f"🎯 IntentClassifier initialized with model: {model_name}")

    async def classify(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> IntentResult:
        """
        Classify user intent from query.

        Args:
            query: User's input query
            conversation_history: Previous messages for context

        Returns:
            IntentResult with classification and extracted entities
        """
        logger.info(f"🔍 Classifying intent for query: {query[:100]}...")

        # Quick pattern matching first (faster)
        pattern_result = self._pattern_based_classification(query)

        # Use LLM for confident classification
        llm_result = await self._llm_based_classification(query, conversation_history)

        # Combine results (LLM takes precedence if confident)
        final_result = self._merge_classifications(pattern_result, llm_result)

        # Determine thinking level based on intent
        final_result.thinking_level = self._determine_thinking_level(final_result.intent)

        logger.info(f"✅ Intent: {final_result.intent} (confidence: {final_result.confidence:.2f})")
        logger.debug(f"Intent details: {final_result.to_dict()}")

        return final_result

    def _pattern_based_classification(self, query: str) -> IntentResult:
        """Fast pattern-based classification using regex"""
        query_lower = query.lower().strip()

        # Check patterns for each intent
        best_match = None
        best_score = 0.0

        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, query_lower)
                if match:
                    # Score based on match length vs query length
                    match_score = len(match.group(0)) / len(query_lower)
                    if match_score > best_score:
                        best_score = match_score
                        best_match = intent

                        # Extract topic if captured
                        if match.groups():
                            topic = match.group(len(match.groups()))

        # Determine domain
        domain = self._detect_domain(query_lower)

        if best_match:
            return IntentResult(
                intent=best_match,
                confidence=min(best_score * 1.5, 0.8),  # Cap at 0.8 for pattern-based
                domain=domain,
                reasoning="Pattern-based classification"
            )

        # Default to UNCLEAR if no pattern matches
        return IntentResult(
            intent=IntentType.UNCLEAR,
            confidence=0.3,
            domain=domain,
            reasoning="No clear pattern match"
        )

    async def _llm_based_classification(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> IntentResult:
        """LLM-based classification for nuanced understanding"""

        # Build context from history
        history_context = ""
        if conversation_history and len(conversation_history) > 0:
            recent = conversation_history[-3:]  # Last 3 messages
            history_context = "\nRecent conversation:\n" + "\n".join(
                f"{msg['role']}: {msg['content'][:100]}" for msg in recent
            )

        # Classification prompt
        classification_prompt = f"""You are an intent classifier for an AI tutor. Analyze the user's query and classify it into ONE category.

Categories:
- learning_new_topic: User wants to start learning a new topic/concept
- roadmap_request: User wants a learning plan/curriculum/roadmap
- solving_problem: User has a specific problem to solve (math, coding)
- debugging_code: User's code isn't working, needs debugging help
- asking_question: User wants a direct answer to a question (what/who/when)
- requesting_explanation: User wants detailed explanation of a concept
- practice_exercises: User wants practice problems or exercises
- review_concept: User wants to review/revisit a concept
- greeting: Simple greeting or chitchat
- unclear: Cannot determine intent clearly

Also extract:
- Topic: Main subject mentioned (if any)
- Domain: programming or mathematics or general
- User level: beginner, intermediate, or advanced (infer from query tone)

Query: "{query}"{history_context}

Respond in this EXACT format:
INTENT: [category]
TOPIC: [topic or none]
DOMAIN: [domain]
LEVEL: [level or unknown]
CONFIDENCE: [0.0-1.0]
REASON: [brief explanation]"""

        try:
            # Get LLM classification
            response = await self.llm.ainvoke([
                SystemMessage(content=classification_prompt)
            ])

            # Parse response
            return self._parse_llm_response(response.content, query)

        except Exception as e:
            logger.error(f"❌ LLM classification failed: {e}")
            # Fallback to pattern-based
            return IntentResult(
                intent=IntentType.UNCLEAR,
                confidence=0.2,
                domain=Domain.GENERAL,
                reasoning=f"LLM classification failed: {str(e)}"
            )

    def _parse_llm_response(self, response: str, original_query: str) -> IntentResult:
        """Parse LLM classification response"""

        # Extract fields using regex
        intent_match = re.search(r'INTENT:\s*(\w+)', response, re.IGNORECASE)
        topic_match = re.search(r'TOPIC:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
        domain_match = re.search(r'DOMAIN:\s*(\w+)', response, re.IGNORECASE)
        level_match = re.search(r'LEVEL:\s*(\w+)', response, re.IGNORECASE)
        confidence_match = re.search(r'CONFIDENCE:\s*([\d\.]+)', response, re.IGNORECASE)
        reason_match = re.search(r'REASON:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)

        # Parse intent
        intent_str = intent_match.group(1).lower() if intent_match else "unclear"
        try:
            intent = IntentType(intent_str)
        except ValueError:
            intent = IntentType.UNCLEAR

        # Parse domain
        domain_str = domain_match.group(1).lower() if domain_match else "general"
        try:
            domain = Domain(domain_str)
        except ValueError:
            domain = Domain.GENERAL

        # Extract other fields
        topic = topic_match.group(1).strip() if topic_match else None
        if topic and topic.lower() in ['none', 'n/a', 'unknown']:
            topic = None

        user_level = level_match.group(1).strip() if level_match else "unknown"

        confidence = float(confidence_match.group(1)) if confidence_match else 0.7
        confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]

        reasoning = reason_match.group(1).strip() if reason_match else "LLM classification"

        # Extract problem statement or question for specific intents
        problem_statement = None
        specific_question = None

        if intent == IntentType.SOLVING_PROBLEM:
            problem_statement = original_query
        elif intent == IntentType.ASKING_QUESTION:
            specific_question = original_query

        return IntentResult(
            intent=intent,
            confidence=confidence,
            domain=domain,
            topic=topic,
            problem_statement=problem_statement,
            specific_question=specific_question,
            user_level=user_level if user_level != "unknown" else None,
            reasoning=reasoning
        )

    def _merge_classifications(
        self,
        pattern_result: IntentResult,
        llm_result: IntentResult
    ) -> IntentResult:
        """Merge pattern and LLM classifications intelligently"""

        # If LLM is confident (>0.7), use it
        if llm_result.confidence > 0.7:
            return llm_result

        # If pattern is confident (>0.6), use it
        if pattern_result.confidence > 0.6:
            return pattern_result

        # Use LLM result but lower confidence
        llm_result.confidence = max(pattern_result.confidence, llm_result.confidence * 0.8)
        return llm_result

    def _detect_domain(self, query: str) -> Domain:
        """Detect subject domain from keywords"""
        prog_score = sum(1 for kw in self.DOMAIN_KEYWORDS[Domain.PROGRAMMING] if kw in query)
        math_score = sum(1 for kw in self.DOMAIN_KEYWORDS[Domain.MATHEMATICS] if kw in query)

        if prog_score > 0 and math_score > 0:
            return Domain.MIXED
        elif prog_score > 0:
            return Domain.PROGRAMMING
        elif math_score > 0:
            return Domain.MATHEMATICS
        else:
            return Domain.GENERAL

    def _determine_thinking_level(self, intent: IntentType) -> ThinkingLevel:
        """Determine how much thinking to show based on intent"""

        THINKING_MAP = {
            # Skip thinking for these
            IntentType.GREETING: ThinkingLevel.NONE,
            IntentType.ASKING_QUESTION: ThinkingLevel.NONE,
            IntentType.FEEDBACK: ThinkingLevel.NONE,

            # Minimal thinking
            IntentType.LEARNING_NEW_TOPIC: ThinkingLevel.MINIMAL,
            IntentType.ROADMAP_REQUEST: ThinkingLevel.MINIMAL,
            IntentType.PRACTICE_EXERCISES: ThinkingLevel.MINIMAL,

            # Moderate thinking
            IntentType.REQUESTING_EXPLANATION: ThinkingLevel.MODERATE,
            IntentType.REVIEW_CONCEPT: ThinkingLevel.MODERATE,

            # Full thinking
            IntentType.SOLVING_PROBLEM: ThinkingLevel.FULL,
            IntentType.DEBUGGING_CODE: ThinkingLevel.FULL,

            # Default
            IntentType.UNCLEAR: ThinkingLevel.MODERATE,
            IntentType.CHALLENGE_REQUEST: ThinkingLevel.FULL
        }

        return THINKING_MAP.get(intent, ThinkingLevel.MODERATE)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def classify_user_intent(
    query: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    model_name: str = "qwen2.5:3b-instruct-q5_K_M"
) -> IntentResult:
    """
    Convenience function to classify user intent.

    Args:
        query: User's input query
        conversation_history: Previous conversation for context
        model_name: Ollama model to use

    Returns:
        IntentResult with classification
    """
    classifier = IntentClassifier(model_name=model_name)
    return await classifier.classify(query, conversation_history)
