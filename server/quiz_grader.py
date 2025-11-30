"""
Quiz Grader Agent
AI-powered grading system for quiz answers including subjective and code questions
"""

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama
from typing import List, Dict, Any, Optional
import json
import logging
import sys
from io import StringIO
import traceback

logger = logging.getLogger(__name__)


class QuizGraderAgent:
    """
    AI-powered quiz grading with detailed feedback
    Handles multiple question types including code execution
    """

    GRADING_PROMPT = """You are an expert tutor grading a student's quiz answer.

Question Type: {question_type}
Question: {question}
Correct Answer: {correct_answer}
Student Answer: {student_answer}

{additional_context}

Evaluate the student's answer carefully:
1. Is it correct? (Consider partial credit for close answers)
2. Provide specific, constructive feedback
3. If wrong, explain the concept clearly
4. Suggest improvements if needed

For short_answer questions:
- Check if key concepts are present (keywords: {keywords})
- Award partial credit if answer shows understanding but misses details
- Full credit if all main points are covered

For multiple_choice/true_false:
- Either correct or incorrect (no partial credit)
- Explain why the answer is right/wrong

Return JSON:
{{
  "correct": true/false,
  "points_earned": number (0 to {max_points}),
  "feedback": "Detailed feedback for the student",
  "partial_credit": true/false,
  "key_concepts_covered": ["concept1", "concept2"]
}}
"""

    OVERALL_FEEDBACK_PROMPT = """You are an expert tutor providing comprehensive feedback on a completed quiz.

Quiz Title: {quiz_title}
Topic: {topic}
Difficulty: {difficulty}

Student Performance:
- Total Questions: {total_questions}
- Correct Answers: {correct_answers}
- Score: {percentage_score}%
- Time Spent: {time_spent} seconds

Detailed Answers:
{answer_details}

Provide comprehensive feedback:
1. Identify 2-3 strengths (what they did well)
2. Identify 1-2 weaknesses (areas needing improvement)
3. Give 2-3 specific recommendations for next steps
4. Suggest 2-3 related topics to study next

Return JSON:
{{
  "overall_feedback": "2-3 sentence summary of performance",
  "strengths": ["strength1", "strength2"],
  "weaknesses": ["weakness1", "weakness2"],
  "recommendations": ["recommendation1", "recommendation2", "recommendation3"],
  "next_topics": ["topic1", "topic2"]
}}
"""

    def __init__(self):
        """Initialize the quiz grader with local Ollama verification model"""
        self.llm = ChatOllama(
            model="gemma3:4b",  # Using verification model for consistent, accurate grading
            temperature=0.1,  # Lower temperature for more consistent grading
            num_predict=2048
        )
        logger.info("QuizGraderAgent initialized with local Ollama verification model (gemma3:4b)")

    async def grade_answer(
        self,
        question: Dict[str, Any],
        student_answer: str,
        question_type: str
    ) -> Dict[str, Any]:
        """
        Grade a single quiz answer with AI feedback

        Args:
            question: The question data (including correct answer)
            student_answer: Student's submitted answer
            question_type: Type of question (multiple_choice, short_answer, etc.)

        Returns:
            Dict with grading results and feedback
        """
        try:
            logger.info(f"Grading {question_type} question: {question.get('id')}")

            # Handle different question types
            if question_type == "multiple_choice" or question_type == "true_false":
                return self._grade_objective_answer(question, student_answer)

            elif question_type == "short_answer":
                return await self._grade_subjective_answer(question, student_answer)

            elif question_type == "code":
                return await self._grade_code_answer(question, student_answer)

            else:
                logger.warning(f"Unknown question type: {question_type}")
                return {
                    "correct": False,
                    "points_earned": 0,
                    "feedback": "Unknown question type",
                    "partial_credit": False
                }

        except Exception as e:
            logger.error(f"Error grading answer: {e}", exc_info=True)
            return {
                "correct": False,
                "points_earned": 0,
                "feedback": f"Error grading answer: {str(e)}",
                "partial_credit": False
            }

    def _grade_objective_answer(
        self,
        question: Dict[str, Any],
        student_answer: str
    ) -> Dict[str, Any]:
        """Grade multiple choice or true/false questions"""
        correct_answer = question.get("correct_answer", "")
        points = question.get("points", 10)

        # Normalize answers for comparison
        student_normalized = student_answer.strip().lower()
        correct_normalized = correct_answer.strip().lower()

        is_correct = student_normalized == correct_normalized

        feedback = question.get("explanation", "")
        if not is_correct:
            feedback = f"Incorrect. The correct answer is: {correct_answer}. {feedback}"
        else:
            feedback = f"Correct! {feedback}"

        return {
            "correct": is_correct,
            "points_earned": points if is_correct else 0,
            "feedback": feedback,
            "partial_credit": False
        }

    async def _grade_subjective_answer(
        self,
        question: Dict[str, Any],
        student_answer: str
    ) -> Dict[str, Any]:
        """Grade short answer questions with AI"""
        try:
            keywords = question.get("keywords", [])
            correct_answer = question.get("correct_answer", "")
            max_points = question.get("points", 10)

            # Prepare additional context
            additional_context = ""
            if keywords:
                additional_context = f"Key concepts to look for: {', '.join(keywords)}"

            # Create grading prompt
            prompt = self.GRADING_PROMPT.format(
                question_type="short_answer",
                question=question.get("question", ""),
                correct_answer=correct_answer,
                student_answer=student_answer,
                additional_context=additional_context,
                keywords=keywords,
                max_points=max_points
            )

            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content="Grade this answer")
            ]

            response = await self.llm.ainvoke(messages)
            result = self._parse_grading_response(response.content)

            # Ensure points don't exceed max
            result["points_earned"] = min(result.get("points_earned", 0), max_points)

            # Determine correctness (>70% of points = correct)
            result["correct"] = result["points_earned"] >= (max_points * 0.7)

            return result

        except Exception as e:
            logger.error(f"Error in AI grading: {e}", exc_info=True)
            # Fallback: simple keyword matching
            return self._fallback_keyword_grading(question, student_answer)

    async def _grade_code_answer(
        self,
        question: Dict[str, Any],
        student_code: str
    ) -> Dict[str, Any]:
        """Grade code submissions by running test cases"""
        try:
            test_cases = question.get("test_cases", [])
            max_points = question.get("points", 20)

            if not test_cases:
                # No test cases, use AI to evaluate
                return await self._ai_grade_code(question, student_code, max_points)

            # Execute code with test cases
            execution_results = self._execute_code_safely(student_code, test_cases)

            # Calculate score based on passed tests
            total_tests = len(test_cases)
            passed_tests = sum(1 for result in execution_results if result.get("passed", False))

            points_earned = (passed_tests / total_tests) * max_points if total_tests > 0 else 0
            is_correct = passed_tests == total_tests

            # Generate feedback
            if is_correct:
                feedback = f"Excellent! All {total_tests} test cases passed. Your code works correctly."
            elif passed_tests > 0:
                feedback = f"Partial credit: {passed_tests}/{total_tests} test cases passed. Review the failing tests."
            else:
                feedback = f"No test cases passed. Review your logic and try again."

            return {
                "correct": is_correct,
                "points_earned": round(points_earned, 1),
                "feedback": feedback,
                "partial_credit": passed_tests > 0 and not is_correct,
                "test_results": execution_results
            }

        except Exception as e:
            logger.error(f"Error grading code: {e}", exc_info=True)
            return {
                "correct": False,
                "points_earned": 0,
                "feedback": f"Error executing code: {str(e)}",
                "partial_credit": False
            }

    def _execute_code_safely(
        self,
        code: str,
        test_cases: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Safely execute Python code with test cases
        WARNING: This is a simplified version. In production, use a proper sandbox!
        """
        results = []

        # Create a safe execution environment
        safe_globals = {
            "__builtins__": {
                "print": print,
                "len": len,
                "range": range,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "abs": abs,
                "min": min,
                "max": max,
                "sum": sum,
                "sorted": sorted,
                "enumerate": enumerate,
                "zip": zip,
            }
        }

        try:
            # Execute the student's code to define functions
            exec(code, safe_globals)

            # Extract the function name (assume first defined function)
            function_names = [name for name in safe_globals.keys() if callable(safe_globals[name]) and not name.startswith("_")]

            if not function_names:
                return [{"passed": False, "error": "No function defined in code"}]

            function_name = function_names[0]
            student_function = safe_globals[function_name]

            # Run each test case
            for test_case in test_cases:
                try:
                    input_data = test_case.get("input", [])
                    expected = test_case.get("expected")

                    # Call the function
                    if isinstance(input_data, list):
                        output = student_function(*input_data)
                    else:
                        output = student_function(input_data)

                    # Check result
                    passed = output == expected

                    results.append({
                        "passed": passed,
                        "input": input_data,
                        "expected": expected,
                        "output": output
                    })

                except Exception as e:
                    results.append({
                        "passed": False,
                        "input": test_case.get("input"),
                        "expected": test_case.get("expected"),
                        "error": str(e)
                    })

        except Exception as e:
            results.append({
                "passed": False,
                "error": f"Code execution error: {str(e)}"
            })

        return results

    async def _ai_grade_code(
        self,
        question: Dict[str, Any],
        student_code: str,
        max_points: int
    ) -> Dict[str, Any]:
        """Use AI to grade code when no test cases are available"""
        try:
            prompt = self.GRADING_PROMPT.format(
                question_type="code",
                question=question.get("question", ""),
                correct_answer=question.get("correct_answer", "Sample solution"),
                student_answer=student_code,
                additional_context="Evaluate code quality, correctness, and efficiency",
                keywords=[],
                max_points=max_points
            )

            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content="Grade this code")
            ]

            response = await self.llm.ainvoke(messages)
            result = self._parse_grading_response(response.content)
            result["points_earned"] = min(result.get("points_earned", 0), max_points)

            return result

        except Exception as e:
            logger.error(f"Error in AI code grading: {e}")
            return {
                "correct": False,
                "points_earned": 0,
                "feedback": "Could not grade code",
                "partial_credit": False
            }

    async def generate_overall_feedback(
        self,
        quiz: Dict[str, Any],
        attempt: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive feedback for entire quiz

        Args:
            quiz: The quiz data
            attempt: The attempt data with answers

        Returns:
            Dict with overall feedback, strengths, weaknesses, recommendations
        """
        try:
            logger.info("Generating overall quiz feedback...")

            # Format answer details
            answer_details = []
            for question in quiz.get("questions", []):
                q_id = question.get("id")
                answer_data = attempt.get("answers", {}).get(q_id, {})

                answer_details.append(
                    f"Q: {question.get('question')}\n"
                    f"Answer: {answer_data.get('answer', 'No answer')}\n"
                    f"Correct: {answer_data.get('correct', False)}\n"
                    f"Points: {answer_data.get('points_earned', 0)}/{question.get('points', 10)}"
                )

            # Create feedback prompt
            prompt = self.OVERALL_FEEDBACK_PROMPT.format(
                quiz_title=quiz.get("title", "Quiz"),
                topic=quiz.get("topic", "General"),
                difficulty=quiz.get("difficulty", "beginner"),
                total_questions=attempt.get("total_questions", 0),
                correct_answers=attempt.get("correct_answers", 0),
                percentage_score=attempt.get("percentage_score", 0),
                time_spent=attempt.get("time_spent", 0),
                answer_details="\n\n".join(answer_details)
            )

            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content="Provide comprehensive feedback")
            ]

            response = await self.llm.ainvoke(messages)
            feedback = self._parse_feedback_response(response.content)

            return feedback

        except Exception as e:
            logger.error(f"Error generating overall feedback: {e}", exc_info=True)
            return self._create_fallback_feedback(attempt)

    def _fallback_keyword_grading(
        self,
        question: Dict[str, Any],
        student_answer: str
    ) -> Dict[str, Any]:
        """Fallback grading using simple keyword matching"""
        keywords = question.get("keywords", [])
        max_points = question.get("points", 10)

        if not keywords:
            return {
                "correct": False,
                "points_earned": 0,
                "feedback": "Unable to grade this answer",
                "partial_credit": False
            }

        # Count keywords present
        student_lower = student_answer.lower()
        matched_keywords = [kw for kw in keywords if kw.lower() in student_lower]

        # Calculate points based on keyword coverage
        keyword_coverage = len(matched_keywords) / len(keywords) if keywords else 0
        points = max_points * keyword_coverage

        return {
            "correct": keyword_coverage >= 0.7,
            "points_earned": round(points, 1),
            "feedback": f"Your answer covered {len(matched_keywords)}/{len(keywords)} key concepts. {question.get('explanation', '')}",
            "partial_credit": 0 < keyword_coverage < 0.7,
            "key_concepts_covered": matched_keywords
        }

    def _parse_grading_response(self, response_content: str) -> Dict[str, Any]:
        """Parse AI grading response"""
        try:
            if "```json" in response_content:
                json_start = response_content.index("```json") + 7
                json_end = response_content.index("```", json_start)
                json_str = response_content[json_start:json_end].strip()
            else:
                json_str = response_content.strip()

            return json.loads(json_str)

        except Exception as e:
            logger.error(f"Error parsing grading response: {e}")
            return {
                "correct": False,
                "points_earned": 0,
                "feedback": "Error in grading",
                "partial_credit": False
            }

    def _parse_feedback_response(self, response_content: str) -> Dict[str, Any]:
        """Parse overall feedback response"""
        try:
            if "```json" in response_content:
                json_start = response_content.index("```json") + 7
                json_end = response_content.index("```", json_start)
                json_str = response_content[json_start:json_end].strip()
            else:
                json_str = response_content.strip()

            return json.loads(json_str)

        except Exception as e:
            logger.error(f"Error parsing feedback response: {e}")
            return self._create_fallback_feedback({})

    def _create_fallback_feedback(self, attempt: Dict[str, Any]) -> Dict[str, Any]:
        """Create basic feedback when AI generation fails"""
        percentage = attempt.get("percentage_score", 0)

        if percentage >= 80:
            overall = "Great job! You demonstrated strong understanding of the material."
            strengths = ["Good performance overall"]
        elif percentage >= 60:
            overall = "Good effort! You've grasped the main concepts but there's room for improvement."
            strengths = ["Understanding of basic concepts"]
        else:
            overall = "Keep practicing! Review the material and try again."
            strengths = ["Attempted all questions"]

        return {
            "overall_feedback": overall,
            "strengths": strengths,
            "weaknesses": ["Review incorrect answers"],
            "recommendations": ["Practice more problems", "Review the explanations"],
            "next_topics": ["Continue with next lesson"]
        }


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test():
        grader = QuizGraderAgent()

        # Test objective question
        question = {
            "id": "q1",
            "type": "multiple_choice",
            "question": "What is 2 + 2?",
            "correct_answer": "4",
            "points": 10
        }

        result = await grader.grade_answer(question, "4", "multiple_choice")
        print(json.dumps(result, indent=2))

    asyncio.run(test())
