"""
Quiz Generator Agent
Generates contextual quizzes based on conversation content and learning progress
"""

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class QuizGeneratorAgent:
    """
    AI agent that generates contextual quizzes based on
    what the user has learned in the conversation
    """

    QUIZ_GENERATION_PROMPT = """You are an expert quiz designer and educational assessment specialist.

Your task is to create a quiz that accurately assesses the user's understanding of the topics
they've been learning about in their recent conversation.

Topics to assess: {topics}
Difficulty level: {difficulty}
Number of questions: {num_questions}

Recent conversation context:
{conversation_context}

Learning objectives:
{learning_objectives}

Generate a quiz with the following requirements:
1. Mix question types: multiple_choice, true_false, short_answer, and code (if applicable)
2. Questions should be directly related to what was discussed
3. Include clear, unambiguous questions
4. Provide comprehensive explanations for correct answers
5. For wrong answers, provide helpful feedback that guides learning
6. Assign appropriate points (10-20 per question)
7. Order questions from easier to harder

Return a JSON object with this EXACT structure:
{{
  "title": "Quiz: [Topic Name]",
  "description": "Brief description of what this quiz covers",
  "topic": "main topic name",
  "difficulty": "{difficulty}",
  "questions": [
    {{
      "id": "q1",
      "type": "multiple_choice",
      "question": "Clear, specific question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Option A",
      "explanation": "Detailed explanation of why this is correct",
      "points": 10,
      "order": 1
    }},
    {{
      "id": "q2",
      "type": "true_false",
      "question": "Statement to evaluate as true or false",
      "options": ["True", "False"],
      "correct_answer": "True",
      "explanation": "Why this statement is true/false",
      "points": 10,
      "order": 2
    }},
    {{
      "id": "q3",
      "type": "short_answer",
      "question": "Open-ended question requiring 1-2 sentence answer",
      "correct_answer": "Sample correct answer",
      "keywords": ["keyword1", "keyword2"],
      "explanation": "What we're looking for in the answer",
      "points": 15,
      "order": 3
    }},
    {{
      "id": "q4",
      "type": "code",
      "question": "Programming task description",
      "template": "# Starter code\ndef function_name(param):\n    # Your code here\n    pass",
      "test_cases": [
        {{"input": [2, 3], "expected": 5}},
        {{"input": [10, -5], "expected": 5}}
      ],
      "correct_answer": "def function_name(a, b):\n    return a + b",
      "explanation": "How this code works",
      "points": 20,
      "order": 4
    }}
  ]
}}

Important:
- All questions must be directly answerable based on the conversation
- For code questions, ensure test cases are comprehensive
- Explanations should teach, not just state correctness
- Keywords for short_answer help with partial credit grading
"""

    QUIZ_TRIGGER_ANALYSIS_PROMPT = """You are analyzing whether now is a good time to present a quiz during the conversation.

Recent conversation (last {num_messages} messages):
{conversation_context}

Current roadmap phase: {current_phase}
Topics covered recently: {covered_topics}
Time since last quiz: {time_since_last_quiz}

Determine if a quiz should be triggered now by considering:
1. Has the user learned 2-3 related concepts?
2. Is there a natural pause in the conversation?
3. Has enough time passed since the last quiz?
4. Is the user receptive (not frustrated or confused)?
5. Have they reached a milestone in the roadmap?

Return a JSON object:
{{
  "should_trigger": true/false,
  "confidence": 0.0-1.0,
  "reason": "Explanation of the decision",
  "suggested_topics": ["topic1", "topic2"],
  "recommended_difficulty": "beginner|intermediate|advanced"
}}
"""

    def __init__(self):
        """Initialize the quiz generator with local Ollama model"""
        self.llm = ChatOllama(
            model="gemma3:4b",
            temperature=0.7,
            num_predict=4096,  # Increased for quiz JSON generation
            timeout=120  # 2 minute timeout for quiz generation
        )
        logger.info("QuizGeneratorAgent initialized with gemma3:4b Ollama model")

    async def generate_quiz(
        self,
        topics: List[str],
        conversation_context: str,
        num_questions: int = 5,
        difficulty: str = "beginner",
        learning_objectives: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a quiz based on topics and conversation

        Args:
            topics: List of topics to assess
            conversation_context: Recent conversation text
            num_questions: Number of questions to generate
            difficulty: Difficulty level (beginner, intermediate, advanced)
            learning_objectives: Specific objectives to test

        Returns:
            Dict containing quiz structure with questions
        """
        try:
            logger.info(f"Generating quiz for topics: {topics}")

            # Prepare learning objectives
            objectives_text = "\n".join(learning_objectives) if learning_objectives else "Test understanding of the discussed topics"

            # Create the prompt
            prompt = self.QUIZ_GENERATION_PROMPT.format(
                topics=", ".join(topics),
                difficulty=difficulty,
                num_questions=num_questions,
                conversation_context=conversation_context[:2000] if conversation_context else "General knowledge assessment",
                learning_objectives=objectives_text
            )

            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content=f"Generate a {difficulty} quiz with exactly {num_questions} questions about: {', '.join(topics)}. Return ONLY valid JSON, no other text.")
            ]

            # Generate quiz
            logger.info(f"Invoking LLM for quiz generation...")
            response = await self.llm.ainvoke(messages)
            logger.info(f"LLM response received, parsing...")
            quiz_data = self._parse_quiz_response(response.content)

            # Validate and calculate totals
            quiz_data = self._validate_quiz(quiz_data, topics, difficulty)

            logger.info(f"Generated quiz '{quiz_data.get('title')}' with {len(quiz_data.get('questions', []))} questions")
            return quiz_data

        except Exception as e:
            logger.error(f"Error generating quiz: {e}", exc_info=True)
            # Return a basic fallback quiz
            return self._create_fallback_quiz(topics, difficulty, num_questions)

    async def should_trigger_quiz(
        self,
        conversation_messages: List[Dict],
        roadmap_data: Optional[Dict] = None,
        last_quiz_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Determine if a quiz should be triggered at this point in the conversation

        Args:
            conversation_messages: Recent conversation history
            roadmap_data: Current learning roadmap (if exists)
            last_quiz_time: Timestamp of last quiz (if any)

        Returns:
            Dict with 'should_trigger', 'confidence', 'reason', 'topics'
        """
        try:
            # Get recent messages (last 10)
            recent_messages = conversation_messages[-10:] if len(conversation_messages) > 10 else conversation_messages

            # Format context
            conversation_context = self._format_messages(recent_messages)

            # Extract covered topics
            covered_topics = self._extract_topics_from_conversation(recent_messages)

            # Calculate time since last quiz
            time_since_quiz = "never"
            if last_quiz_time:
                delta = datetime.now() - last_quiz_time
                if delta.total_seconds() < 300:  # Less than 5 minutes
                    time_since_quiz = "very recent"
                elif delta.total_seconds() < 900:  # Less than 15 minutes
                    time_since_quiz = "recent"
                else:
                    time_since_quiz = "long ago"

            # Get current phase from roadmap
            current_phase = "unknown"
            if roadmap_data and "phases" in roadmap_data:
                for phase in roadmap_data["phases"]:
                    if any(m.get("status") == "in_progress" for m in phase.get("milestones", [])):
                        current_phase = phase.get("title", "unknown")
                        break

            # Create analysis prompt
            prompt = self.QUIZ_TRIGGER_ANALYSIS_PROMPT.format(
                num_messages=len(recent_messages),
                conversation_context=conversation_context,
                current_phase=current_phase,
                covered_topics=", ".join(covered_topics),
                time_since_last_quiz=time_since_quiz
            )

            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content="Should we trigger a quiz now?")
            ]

            response = await self.llm.ainvoke(messages)
            decision = self._parse_quiz_trigger_response(response.content)

            logger.info(f"Quiz trigger decision: {decision.get('should_trigger')} (confidence: {decision.get('confidence')})")
            return decision

        except Exception as e:
            logger.error(f"Error in quiz trigger analysis: {e}", exc_info=True)
            # Default to not triggering on error
            return {
                "should_trigger": False,
                "confidence": 0.0,
                "reason": "Error in analysis",
                "suggested_topics": [],
                "recommended_difficulty": "beginner"
            }

    def _extract_topics_from_conversation(self, messages: List[Dict]) -> List[str]:
        """Extract key topics mentioned in conversation"""
        topics = set()

        # Common programming topics
        programming_keywords = {
            "variable", "function", "loop", "array", "list", "dictionary",
            "class", "object", "method", "conditional", "if statement",
            "string", "integer", "float", "boolean", "data type"
        }

        # Common math topics
        math_keywords = {
            "equation", "algebra", "geometry", "calculus", "derivative",
            "integral", "function", "graph", "slope", "probability"
        }

        all_keywords = programming_keywords | math_keywords

        for msg in messages:
            if msg.get("role") == "assistant":
                content = msg.get("content", "").lower()
                for keyword in all_keywords:
                    if keyword in content:
                        topics.add(keyword)

        return list(topics)[:5]  # Return top 5 topics

    def _format_messages(self, messages: List[Dict]) -> str:
        """Format messages for context"""
        formatted = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            formatted.append(f"{role.upper()}: {content[:300]}")
        return "\n".join(formatted)

    def _parse_quiz_response(self, response_content: str) -> Dict[str, Any]:
        """Parse LLM response to extract quiz JSON"""
        try:
            # Try to extract JSON from markdown code blocks
            if "```json" in response_content:
                json_start = response_content.index("```json") + 7
                json_end = response_content.index("```", json_start)
                json_str = response_content[json_start:json_end].strip()
            elif "```" in response_content:
                json_start = response_content.index("```") + 3
                json_end = response_content.index("```", json_start)
                json_str = response_content[json_start:json_end].strip()
            else:
                json_str = response_content.strip()

            quiz = json.loads(json_str)
            return quiz

        except Exception as e:
            logger.error(f"Error parsing quiz response: {e}")
            try:
                start = response_content.index("{")
                end = response_content.rindex("}") + 1
                json_str = response_content[start:end]
                return json.loads(json_str)
            except:
                raise ValueError(f"Could not parse quiz JSON: {e}")

    def _parse_quiz_trigger_response(self, response_content: str) -> Dict[str, Any]:
        """Parse quiz trigger decision response"""
        try:
            if "```json" in response_content:
                json_start = response_content.index("```json") + 7
                json_end = response_content.index("```", json_start)
                json_str = response_content[json_start:json_end].strip()
            else:
                json_str = response_content.strip()

            decision = json.loads(json_str)
            return decision

        except Exception as e:
            logger.error(f"Error parsing trigger response: {e}")
            return {
                "should_trigger": False,
                "confidence": 0.0,
                "reason": "Parse error",
                "suggested_topics": [],
                "recommended_difficulty": "beginner"
            }

    def _validate_quiz(self, quiz: Dict[str, Any], topics: List[str], difficulty: str) -> Dict[str, Any]:
        """Validate and enrich quiz data"""
        # Ensure required fields
        if "questions" not in quiz:
            quiz["questions"] = []

        if "title" not in quiz:
            quiz["title"] = f"Quiz: {topics[0] if topics else 'Knowledge Check'}"

        if "topic" not in quiz:
            quiz["topic"] = topics[0] if topics else "general"

        if "difficulty" not in quiz:
            quiz["difficulty"] = difficulty

        # Calculate total points
        total_points = sum(q.get("points", 10) for q in quiz["questions"])
        quiz["total_points"] = total_points

        # Ensure each question has required fields
        for idx, question in enumerate(quiz["questions"], 1):
            if "id" not in question:
                question["id"] = f"q{idx}"
            if "order" not in question:
                question["order"] = idx
            if "points" not in question:
                question["points"] = 10

        # Set metadata
        quiz["estimated_duration"] = len(quiz["questions"]) * 2  # 2 minutes per question
        quiz["attempts_allowed"] = 3
        quiz["passing_score"] = 70.0

        return quiz

    def _create_fallback_quiz(self, topics: List[str], difficulty: str, num_questions: int) -> Dict[str, Any]:
        """Create a basic fallback quiz if generation fails"""
        topic = topics[0] if topics else "General Knowledge"

        questions = []
        for i in range(min(num_questions, 3)):
            questions.append({
                "id": f"q{i+1}",
                "type": "multiple_choice",
                "question": f"Question {i+1} about {topic}",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": "Option A",
                "explanation": "This is the correct answer.",
                "points": 10,
                "order": i+1
            })

        return {
            "title": f"Quiz: {topic}",
            "description": f"Test your knowledge of {topic}",
            "topic": topic,
            "difficulty": difficulty,
            "questions": questions,
            "total_points": len(questions) * 10,
            "estimated_duration": len(questions) * 2,
            "attempts_allowed": 3,
            "passing_score": 70.0
        }


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test():
        agent = QuizGeneratorAgent()

        quiz = await agent.generate_quiz(
            topics=["variables", "data types"],
            conversation_context="We discussed Python variables and how to use different data types like integers, strings, and floats.",
            num_questions=4,
            difficulty="beginner"
        )

        print(json.dumps(quiz, indent=2))

    asyncio.run(test())
