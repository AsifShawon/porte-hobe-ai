"""
Dynamic Prompt System for Porte Hobe AI

This module provides intent-aware prompt templates that adapt to user needs.
Instead of static prompts that treat everything as a problem to solve, this
system generates appropriate responses based on detected user intent.

Features:
- Intent-specific prompt templates
- Context injection (user level, history, preferences)
- Personalized, conversational tone
- Structured response formats
- Memori integration for learning history
"""
from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass

from intent_classifier import IntentType, IntentResult, Domain, ThinkingLevel

logger = logging.getLogger(__name__)


# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

class PromptTemplate:
    """Base class for prompt templates"""

    def __init__(self, template_type: str):
        self.template_type = template_type

    def generate(
        self,
        intent_result: IntentResult,
        user_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> tuple[str, str]:
        """
        Generate thinking and answer prompts.

        Returns:
            (thinking_prompt, answer_prompt)
        """
        raise NotImplementedError


# ============================================================================
# LEARNING ROADMAP TEMPLATE
# ============================================================================

class LearningRoadmapTemplate(PromptTemplate):
    """Template for when user wants to learn something new"""

    def __init__(self):
        super().__init__("learning_roadmap")

    def generate(
        self,
        intent_result: IntentResult,
        user_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> tuple[str, str]:

        topic = intent_result.topic or "the subject"
        user_level = intent_result.user_level or "beginner"
        domain = str(intent_result.domain)

        # Context from user history (from Memori)
        learning_history = context.get("learning_history", []) if context else []
        preferences = context.get("preferences", {}) if context else {}

        # Thinking prompt (MINIMAL - just plan the roadmap)
        thinking_prompt = f"""You are an AI tutor helping a student START LEARNING a new topic.

<USER_REQUEST>
The student asked: "{user_query}"
They want to learn: {topic}
Their level: {user_level}
Domain: {domain}
</USER_REQUEST>

Your task in this PLANNING phase:
1. Briefly identify what they want to learn
2. Note their current level (beginner/intermediate/advanced)
3. Plan a learning roadmap structure

Output format:
<THINK>
Topic: [what they want to learn]
Level: [their current level]
Roadmap: [brief outline - prerequisites, main phases, first step]
</THINK>

Be BRIEF - this is just planning, not the full answer.
"""

        # Answer prompt (ROADMAP with clear structure)
        answer_prompt = f"""You are an enthusiastic AI tutor creating a personalized learning roadmap.

<CONTEXT>
Student's request: "{user_query}"
Topic: {topic}
Student level: {user_level}
Domain: {domain}
</CONTEXT>

<YOUR_TASK>
Create a LEARNING ROADMAP that:
1. Welcomes them to the topic warmly
2. Lists prerequisites (if any) - mention if they've already learned them
3. Breaks learning into 3-5 clear phases with:
   - What they'll learn
   - Why it matters
   - Estimated time
4. Suggests a specific FIRST STEP to start right now
5. Asks about their learning preferences (examples vs theory, pace, etc.)
</YOUR_TASK>

<RESPONSE_STRUCTURE>
📚 **Welcome**
[Warm greeting about learning {topic}]

**Prerequisites** (if needed)
[List any foundational topics - keep brief]

**Your Learning Path**

**Phase 1:** [Name]
   - What you'll learn: [concepts]
   - Time: [estimate]
   - Why it matters: [practical relevance]

**Phase 2:** [Name]
   ...

**Let's Start! 🎯**
[Specific first concept/exercise to begin with]
[Ask about their learning style preferences]
</RESPONSE_STRUCTURE>

<TONE>
- Be encouraging and supportive
- Use conversational language, not academic
- Show enthusiasm about learning
- Ask questions to personalize
- Use emojis sparingly for visual breaks
</TONE>

<AVOID>
- DON'T solve problems or show formulas yet
- DON'T use overly technical jargon
- DON'T make it overwhelming with too much detail
- DON'T show code examples in the roadmap (save for actual lessons)
</AVOID>

Generate the roadmap now:
"""

        return (thinking_prompt, answer_prompt)


# ============================================================================
# PROBLEM SOLVING TEMPLATE
# ============================================================================

class ProblemSolvingTemplate(PromptTemplate):
    """Template for solving specific problems"""

    def __init__(self):
        super().__init__("problem_solving")

    def generate(
        self,
        intent_result: IntentResult,
        user_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> tuple[str, str]:

        problem = intent_result.problem_statement or user_query
        domain = str(intent_result.domain)

        # Thinking prompt (FULL - show problem analysis)
        thinking_prompt = f"""You are solving a {domain} problem step by step.

<PROBLEM>
{problem}
</PROBLEM>

Your task in this ANALYSIS phase:
1. Identify the problem type
2. List what's given and what needs to be found
3. Choose the appropriate method/approach
4. Plan the solution steps

Output format:
<THINK>
Problem type: [classification]
Given: [list]
Find: [what to solve for]
Approach: [method to use]
Steps: [brief outline]
</THINK>

Show your complete reasoning.
"""

        # Answer prompt (STEP-BY-STEP solution)
        answer_prompt = f"""You are a tutor solving a problem with the student.

<PROBLEM>
{problem}
</PROBLEM>

<YOUR_TASK>
Provide a clear step-by-step solution that:
1. States what we're solving
2. Shows each step with explanation
3. Verifies the answer
4. Optionally suggests similar practice problems
</YOUR_TASK>

<RESPONSE_STRUCTURE>
**Problem:** [restate clearly]

**Solution:**

**Step 1:** [First step]
[Explain why]

**Step 2:** [Next step]
[Explain reasoning]

...

**Answer:** [final result]

**Verification:** [check if answer makes sense]

**Practice:** [optional - similar problems to try]
</RESPONSE_STRUCTURE>

<TONE>
- Be clear and methodical
- Explain reasoning at each step
- Encourage understanding, not just answers
</TONE>

Solve the problem now:
"""

        return (thinking_prompt, answer_prompt)


# ============================================================================
# QUICK ANSWER TEMPLATE
# ============================================================================

class QuickAnswerTemplate(PromptTemplate):
    """Template for direct questions - NO thinking phase"""

    def __init__(self):
        super().__init__("quick_answer")

    def generate(
        self,
        intent_result: IntentResult,
        user_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> tuple[str, str]:

        question = intent_result.specific_question or user_query

        # NO thinking prompt (we skip the thinking phase)
        thinking_prompt = ""

        # Direct answer prompt
        answer_prompt = f"""You are answering a direct question clearly and concisely.

<QUESTION>
{question}
</QUESTION>

<YOUR_TASK>
Provide:
1. A direct answer (2-3 sentences)
2. One clear example if helpful
3. Optional: related concepts they might want to explore
</YOUR_TASK>

<RESPONSE_STRUCTURE>
**Answer:**
[Clear, direct answer in 2-3 sentences]

**Example:**
[One concrete example to illustrate]

**Related:**
[Optional - 2-3 related topics they might find interesting]
</RESPONSE_STRUCTURE>

<TONE>
- Be direct and clear
- Don't over-explain
- Use simple language
- One good example is better than multiple
</TONE>

<AVOID>
- Don't write essays
- Don't show lengthy derivations
- Don't list everything possible
</AVOID>

Answer the question now:
"""

        return (thinking_prompt, answer_prompt)


# ============================================================================
# EXPLANATION TEMPLATE
# ============================================================================

class ExplanationTemplate(PromptTemplate):
    """Template for detailed concept explanations"""

    def __init__(self):
        super().__init__("explanation")

    def generate(
        self,
        intent_result: IntentResult,
        user_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> tuple[str, str]:

        topic = intent_result.topic or "the concept"
        domain = str(intent_result.domain)
        user_level = intent_result.user_level or "beginner"

        # Thinking prompt (MODERATE)
        thinking_prompt = f"""You are planning an explanation of {topic}.

<REQUEST>
Student asked: "{user_query}"
Topic: {topic}
Level: {user_level}
</REQUEST>

Your task in PLANNING:
1. What's the core concept?
2. What analogies/examples would help?
3. What's the explanation flow?

Output format:
<THINK>
Core concept: [essence]
Key analogy: [simple analogy]
Flow: [intuition → formal → example → application]
</THINK>

Keep it brief.
"""

        # Answer prompt (CLEAR EXPLANATION)
        answer_prompt = f"""You are explaining a concept clearly and engagingly.

<CONTEXT>
Concept to explain: {topic}
Student level: {user_level}
Domain: {domain}
Question: "{user_query}"
</CONTEXT>

<YOUR_TASK>
Explain {topic} by:
1. Starting with intuition/analogy
2. Giving a clear definition
3. Showing 2-3 examples (simple to complex)
4. Explaining practical applications
5. Suggesting next steps for deeper learning
</YOUR_TASK>

<RESPONSE_STRUCTURE>
**Intuition:**
[Start with an analogy or simple explanation]

**Definition:**
[Clear, accessible definition]

**Examples:**

*Example 1 (Simple):*
[Basic example]

*Example 2 (Practical):*
[Real-world application]

**Why It Matters:**
[Practical importance]

**Next Steps:**
[What to learn next to go deeper]
</RESPONSE_STRUCTURE>

<TONE>
- Start simple, build up complexity
- Use everyday analogies
- Make it engaging and relatable
- Encourage curiosity
</TONE>

Explain the concept now:
"""

        return (thinking_prompt, answer_prompt)


# ============================================================================
# PRACTICE EXERCISES TEMPLATE
# ============================================================================

class PracticeTemplate(PromptTemplate):
    """Template for generating practice problems"""

    def __init__(self):
        super().__init__("practice")

    def generate(
        self,
        intent_result: IntentResult,
        user_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> tuple[str, str]:

        topic = intent_result.topic or "the topic"
        user_level = intent_result.user_level or "beginner"

        # Thinking prompt (MINIMAL)
        thinking_prompt = f"""Generate practice problems for {topic}.

<REQUEST>
{user_query}
Topic: {topic}
Level: {user_level}
</REQUEST>

Plan:
<THINK>
Difficulty: {user_level}
Problem types: [variety]
Number: 5 problems
</THINK>
"""

        # Answer prompt (PRACTICE PROBLEMS)
        answer_prompt = f"""You are creating practice problems for a student.

<CONTEXT>
Topic: {topic}
Level: {user_level}
Request: "{user_query}"
</CONTEXT>

<YOUR_TASK>
Generate 5 practice problems that:
1. Start easy, gradually increase difficulty
2. Cover different aspects of {topic}
3. Include varied formats (if applicable)
4. Provide hints (hidden by default)
5. Encourage the student
</YOUR_TASK>

<RESPONSE_STRUCTURE>
**Practice Problems - {topic}**

**Problem 1 (Warm-up):**
[Easy problem]
*Hint:* ||[hidden hint]||

**Problem 2:**
[Medium problem]
*Hint:* ||[hidden hint]||

**Problem 3:**
[Medium problem - different aspect]

**Problem 4:**
[Challenging problem]

**Problem 5 (Challenge):**
[Hard problem]
*Hint:* ||[hidden hint]||

**When you're done:**
Share your answers and I'll check them with you!
</RESPONSE_STRUCTURE>

Generate the practice problems now:
"""

        return (thinking_prompt, answer_prompt)


# ============================================================================
# PROMPT MANAGER
# ============================================================================

class DynamicPromptManager:
    """Manages prompt selection and generation based on intent"""

    def __init__(self):
        """Initialize prompt templates"""
        self.templates: Dict[IntentType, PromptTemplate] = {
            # Learning intents
            IntentType.LEARNING_NEW_TOPIC: LearningRoadmapTemplate(),
            IntentType.ROADMAP_REQUEST: LearningRoadmapTemplate(),
            IntentType.REVIEW_CONCEPT: ExplanationTemplate(),

            # Problem-solving intents
            IntentType.SOLVING_PROBLEM: ProblemSolvingTemplate(),
            IntentType.DEBUGGING_CODE: ProblemSolvingTemplate(),

            # Information intents
            IntentType.ASKING_QUESTION: QuickAnswerTemplate(),
            IntentType.REQUESTING_EXPLANATION: ExplanationTemplate(),

            # Practice intents
            IntentType.PRACTICE_EXERCISES: PracticeTemplate(),
            IntentType.CHALLENGE_REQUEST: PracticeTemplate(),
        }

        # Default template for unclear intent
        self.default_template = ExplanationTemplate()

        logger.info("📝 DynamicPromptManager initialized with templates")

    def get_prompts(
        self,
        intent_result: IntentResult,
        user_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> tuple[str, str]:
        """
        Get thinking and answer prompts for the given intent.

        Args:
            intent_result: Classification result from IntentClassifier
            user_query: Original user query
            context: Additional context (user history, preferences, etc.)

        Returns:
            (thinking_prompt, answer_prompt)
            If thinking_level is NONE, thinking_prompt will be empty string
        """

        # Get appropriate template
        template = self.templates.get(intent_result.intent, self.default_template)

        # Generate prompts
        thinking_prompt, answer_prompt = template.generate(
            intent_result, user_query, context
        )

        # If thinking level is NONE, clear the thinking prompt
        if intent_result.thinking_level == ThinkingLevel.NONE:
            thinking_prompt = ""
            logger.info("🚫 Skipping thinking phase (NONE level)")

        logger.info(f"📋 Generated prompts for intent: {intent_result.intent.name}")
        logger.debug(f"Thinking prompt length: {len(thinking_prompt)} chars")
        logger.debug(f"Answer prompt length: {len(answer_prompt)} chars")

        return (thinking_prompt, answer_prompt)

    def get_template_info(self, intent: IntentType) -> Dict[str, Any]:
        """Get information about a template"""
        template = self.templates.get(intent, self.default_template)
        return {
            "template_type": template.template_type,
            "intent": str(intent),
            "available": intent in self.templates
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_dynamic_prompts(
    intent_result: IntentResult,
    user_query: str,
    user_context: Optional[Dict[str, Any]] = None
) -> tuple[str, str]:
    """
    Convenience function to get dynamic prompts.

    Args:
        intent_result: Result from intent classification
        user_query: User's original query
        user_context: Optional context (learning history, preferences)

    Returns:
        (thinking_prompt, answer_prompt)
    """
    manager = DynamicPromptManager()
    return manager.get_prompts(intent_result, user_query, user_context)
