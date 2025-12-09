"""
Roadmap Generator Agent
Analyzes user conversations and goals to generate personalized learning roadmaps
"""

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class RoadmapGeneratorAgent:
    """
    AI agent that generates personalized learning roadmaps
    based on user conversation and learning goals
    """

    ROADMAP_GENERATION_PROMPT = """You are an expert learning path designer and educational consultant.

Your task is to analyze the user's learning goals and conversation history to create a
personalized, actionable learning roadmap.

Guidelines:
1. Break learning into 3-7 logical phases (based on complexity)
2. Each phase should have 3-8 milestones (lessons and quizzes)
3. Insert quizzes strategically after 2-4 related lessons
4. Estimate realistic time for each milestone (in minutes)
5. Order by difficulty: beginner → intermediate → advanced
6. Make the roadmap specific to what the user wants to learn
7. Include clear, actionable milestone titles

User Context:
{user_context}

Recent Conversation:
{conversation_history}

User's Stated Goal:
{user_goal}

Current Domain: {domain}

Generate a detailed JSON roadmap following this EXACT structure:
{{
  "title": "Clear, motivating title (e.g., 'Python Programming Mastery Path')",
  "domain": "{domain}",
  "description": "2-3 sentence overview of what user will achieve",
  "phases": [
    {{
      "id": "phase_1",
      "title": "Phase Title (e.g., 'Python Fundamentals')",
      "order": 1,
      "description": "What user will learn in this phase",
      "milestones": [
        {{
          "id": "lesson_1",
          "title": "Specific milestone title",
          "type": "lesson",
          "estimated_time": 30,
          "description": "What user will learn and why it matters",
          "topics": ["topic1", "topic2"],
          "status": "not_started",
          "order": 1
        }},
        {{
          "id": "quiz_1",
          "title": "Quiz: [Topic Name]",
          "type": "quiz",
          "estimated_time": 15,
          "topics": ["topic1", "topic2"],
          "difficulty": "beginner",
          "status": "locked",
          "order": 2
        }}
      ]
    }}
  ]
}}

Important:
- First milestone in first phase should be "not_started", all others "locked"
- Quizzes should be "locked" until prerequisites are completed
- Be specific with milestone titles (not "Learn basics" but "Variables and Data Types")
- Estimate time realistically (30-60 min for lessons, 10-20 min for quizzes)
"""

    ROADMAP_ADAPTATION_PROMPT = """You are adapting an existing learning roadmap based on user performance.

Current Roadmap:
{current_roadmap}

User Performance Data:
{performance_data}

User Struggles: {struggles}
User Strengths: {strengths}

Adapt the roadmap by:
1. Adding remedial milestones if user is struggling with topics
2. Removing unnecessary milestones if user is excelling
3. Adjusting difficulty of upcoming quizzes
4. Reordering topics if needed for better learning flow
5. Adding practice milestones for weak areas

Return the UPDATED roadmap in the same JSON format as before.
"""

    def __init__(self):
        """Initialize the roadmap generator with local Ollama model"""
        self.llm = ChatOllama(
            model="qwen2.5:3b-instruct-q5_K_M",
            temperature=0.7,
            num_predict=4096
        )
        logger.info("RoadmapGeneratorAgent initialized with local Ollama model")

    async def generate_roadmap(
        self,
        user_goal: str,
        conversation_history: List[Dict],
        user_context: Dict,
        domain: str = "general"
    ) -> Dict[str, Any]:
        """
        Generate a personalized learning roadmap

        Args:
            user_goal: User's stated learning objective
            conversation_history: Recent conversation messages
            user_context: Additional context about user (level, preferences, etc.)
            domain: Learning domain ('programming', 'math', 'general')

        Returns:
            Dict containing the roadmap structure
        """
        try:
            logger.info(f"Generating roadmap for goal: {user_goal[:50]}...")

            # Format conversation history
            formatted_history = self._format_conversation_history(conversation_history)

            # Create the prompt
            prompt = self.ROADMAP_GENERATION_PROMPT.format(
                user_context=json.dumps(user_context, indent=2),
                conversation_history=formatted_history,
                user_goal=user_goal,
                domain=domain
            )

            # Generate roadmap
            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content=f"Generate the roadmap for: {user_goal}")
            ]

            response = await self.llm.ainvoke(messages)
            roadmap_data = self._parse_roadmap_response(response.content)

            # Validate and enrich roadmap
            roadmap_data = self._validate_and_enrich_roadmap(roadmap_data)

            logger.info(f"Generated roadmap with {len(roadmap_data.get('phases', []))} phases")
            return roadmap_data

        except Exception as e:
            logger.error(f"Error generating roadmap: {e}", exc_info=True)
            # Return a basic fallback roadmap
            return self._create_fallback_roadmap(user_goal, domain)

    async def adapt_roadmap(
        self,
        current_roadmap: Dict[str, Any],
        performance_data: Dict[str, Any],
        user_struggles: List[str],
        user_strengths: List[str]
    ) -> Dict[str, Any]:
        """
        Adapt existing roadmap based on user performance

        Args:
            current_roadmap: The existing roadmap data
            performance_data: Quiz scores, completion rates, etc.
            user_struggles: Topics user is struggling with
            user_strengths: Topics user excels at

        Returns:
            Updated roadmap structure
        """
        try:
            logger.info("Adapting roadmap based on performance...")

            prompt = self.ROADMAP_ADAPTATION_PROMPT.format(
                current_roadmap=json.dumps(current_roadmap, indent=2),
                performance_data=json.dumps(performance_data, indent=2),
                struggles=", ".join(user_struggles),
                strengths=", ".join(user_strengths)
            )

            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content="Adapt the roadmap based on this performance data")
            ]

            response = await self.llm.ainvoke(messages)
            adapted_roadmap = self._parse_roadmap_response(response.content)

            logger.info("Roadmap adapted successfully")
            return adapted_roadmap

        except Exception as e:
            logger.error(f"Error adapting roadmap: {e}", exc_info=True)
            # Return original roadmap if adaptation fails
            return current_roadmap

    def detect_learning_goal(self, conversation_messages: List[Dict]) -> Optional[Dict[str, str]]:
        """
        Detect if user has expressed a learning goal in conversation

        Args:
            conversation_messages: Recent conversation history

        Returns:
            Dict with 'goal' and 'domain' if detected, None otherwise
        """
        # Check last few messages for learning intent
        recent_messages = conversation_messages[-3:] if len(conversation_messages) > 3 else conversation_messages

        learning_keywords = [
            "learn", "want to learn", "teach me", "i want to understand",
            "help me learn", "study", "master", "get better at",
            "i need to learn", "can you teach", "how do i learn"
        ]

        for msg in recent_messages:
            if msg.get("role") == "user":
                content = msg.get("content", "").lower()

                # Check for learning intent
                if any(keyword in content for keyword in learning_keywords):
                    # Detect domain
                    domain = "general"
                    if any(word in content for word in ["python", "javascript", "code", "programming", "function", "variable"]):
                        domain = "programming"
                    elif any(word in content for word in ["math", "algebra", "calculus", "equation", "geometry"]):
                        domain = "math"

                    return {
                        "goal": content,
                        "domain": domain,
                        "detected": True
                    }

        return None

    def _format_conversation_history(self, messages: List[Dict], limit: int = 10) -> str:
        """Format conversation history for the prompt"""
        recent_messages = messages[-limit:] if len(messages) > limit else messages

        formatted = []
        for msg in recent_messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            formatted.append(f"{role.upper()}: {content[:200]}")

        return "\n".join(formatted)

    def _parse_roadmap_response(self, response_content: str) -> Dict[str, Any]:
        """Parse the LLM response to extract roadmap JSON"""
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
                # Assume entire response is JSON
                json_str = response_content.strip()

            roadmap = json.loads(json_str)
            return roadmap

        except Exception as e:
            logger.error(f"Error parsing roadmap response: {e}")
            # Try to find JSON object in the response
            try:
                start = response_content.index("{")
                end = response_content.rindex("}") + 1
                json_str = response_content[start:end]
                return json.loads(json_str)
            except:
                raise ValueError(f"Could not parse roadmap JSON: {e}")

    def _validate_and_enrich_roadmap(self, roadmap: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enrich the roadmap data"""
        # Ensure required fields
        if "phases" not in roadmap:
            roadmap["phases"] = []

        # Calculate total milestones
        total_milestones = 0
        for phase in roadmap["phases"]:
            total_milestones += len(phase.get("milestones", []))

        roadmap["total_milestones"] = total_milestones
        roadmap["completed_milestones"] = 0

        # Ensure milestone IDs are unique
        milestone_counter = 1
        quiz_counter = 1

        for phase_idx, phase in enumerate(roadmap["phases"], 1):
            # Ensure phase has ID
            if "id" not in phase:
                phase["id"] = f"phase_{phase_idx}"

            for milestone in phase.get("milestones", []):
                # Ensure milestone has ID
                if "id" not in milestone:
                    if milestone.get("type") == "quiz":
                        milestone["id"] = f"quiz_{quiz_counter}"
                        quiz_counter += 1
                    else:
                        milestone["id"] = f"lesson_{milestone_counter}"
                        milestone_counter += 1

                # Ensure status
                if "status" not in milestone:
                    milestone["status"] = "locked"

        # Set first milestone to not_started
        if roadmap["phases"] and roadmap["phases"][0].get("milestones"):
            roadmap["phases"][0]["milestones"][0]["status"] = "not_started"

        return roadmap

    def _create_fallback_roadmap(self, user_goal: str, domain: str) -> Dict[str, Any]:
        """Create a basic fallback roadmap if generation fails"""
        return {
            "title": f"Learning Path: {user_goal[:50]}",
            "domain": domain,
            "description": f"A structured path to help you {user_goal}",
            "phases": [
                {
                    "id": "phase_1",
                    "title": "Getting Started",
                    "order": 1,
                    "description": "Foundation concepts and basics",
                    "milestones": [
                        {
                            "id": "lesson_1",
                            "title": "Introduction",
                            "type": "lesson",
                            "estimated_time": 30,
                            "description": "Introduction to the topic",
                            "topics": ["basics"],
                            "status": "not_started",
                            "order": 1
                        },
                        {
                            "id": "quiz_1",
                            "title": "Quiz: Basics",
                            "type": "quiz",
                            "estimated_time": 15,
                            "topics": ["basics"],
                            "difficulty": "beginner",
                            "status": "locked",
                            "order": 2
                        }
                    ]
                }
            ],
            "total_milestones": 2,
            "completed_milestones": 0
        }


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test():
        agent = RoadmapGeneratorAgent()

        roadmap = await agent.generate_roadmap(
            user_goal="I want to learn Python programming from scratch",
            conversation_history=[
                {"role": "user", "content": "I want to learn Python programming"},
                {"role": "assistant", "content": "Great! I can help you with that."}
            ],
            user_context={"level": "beginner", "background": "no programming experience"},
            domain="programming"
        )

        print(json.dumps(roadmap, indent=2))

    asyncio.run(test())
