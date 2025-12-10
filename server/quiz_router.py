"""
Quiz API Router
Endpoints for managing quizzes, attempts, and grading
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import uuid

from auth import get_current_user
from rate_limit import limit_user
from config import get_supabase_client
from quiz_generator import QuizGeneratorAgent
from quiz_grader import QuizGraderAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/quizzes", tags=["quizzes"])

# Initialize agents
quiz_generator = QuizGeneratorAgent()
quiz_grader = QuizGraderAgent()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class GenerateQuizRequest(BaseModel):
    topics: List[str] = Field(..., description="Topics to assess")
    conversation_context: str = Field(default="", description="Recent conversation context")
    num_questions: int = Field(default=5, description="Number of questions")
    difficulty: str = Field(default="beginner", description="Difficulty level")
    roadmap_id: Optional[str] = Field(None, description="Associated roadmap ID")
    phase_id: Optional[str] = Field(None, description="Associated phase ID")
    milestone_id: Optional[str] = Field(None, description="Associated milestone ID")


class StartAttemptRequest(BaseModel):
    quiz_id: str = Field(..., description="Quiz ID to attempt")


class SubmitAnswerRequest(BaseModel):
    question_id: str = Field(..., description="Question ID")
    answer: str = Field(..., description="User's answer")
    time_spent: int = Field(default=0, description="Time spent on this question in seconds")


class CompleteQuizRequest(BaseModel):
    attempt_id: str = Field(..., description="Attempt ID to complete")


# ============================================================================
# QUIZ MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/generate", response_model=Dict[str, Any])
async def generate_quiz(
    request: GenerateQuizRequest,
    user=Depends(get_current_user),
    _limit=Depends(limit_user)
):
    """
    Generate a new quiz based on topics and conversation context
    """
    try:
        user_id = user.get("user_id")
        logger.info(f"Generating quiz for user {user_id} on topics: {request.topics}")

        # Generate quiz using AI
        quiz_data = await quiz_generator.generate_quiz(
            topics=request.topics,
            conversation_context=request.conversation_context,
            num_questions=request.num_questions,
            difficulty=request.difficulty
        )

        # Store quiz in database
        supabase = get_supabase_client()

        quiz_record = {
            "user_id": user_id,
            "roadmap_id": request.roadmap_id,
            "title": quiz_data.get("title"),
            "description": quiz_data.get("description"),
            "topic": quiz_data.get("topic"),
            "difficulty": request.difficulty,
            "questions": quiz_data.get("questions"),
            "total_points": quiz_data.get("total_points", 0),
            "passing_score": quiz_data.get("passing_score", 70.0),
            "attempts_allowed": quiz_data.get("attempts_allowed", 3),
            "time_limit": quiz_data.get("time_limit"),
            "estimated_duration": quiz_data.get("estimated_duration", 10),
            "status": "not_started",
            "phase_id": request.phase_id,
            "milestone_id": request.milestone_id,
            "trigger_condition": "manual",
            "metadata": {"topics": request.topics}
        }

        result = supabase.table("conversation_quizzes").insert(quiz_record).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create quiz")

        created_quiz = result.data[0]

        logger.info(f"Quiz created successfully: {created_quiz['id']}")

        return {
            "status": "success",
            "quiz_id": created_quiz["id"],
            "quiz": created_quiz
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating quiz: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating quiz: {str(e)}")


@router.get("/", response_model=Dict[str, Any])
async def get_user_quizzes(
    roadmap_id: Optional[str] = None,
    status: Optional[str] = None,
    difficulty: Optional[str] = None,
    limit: int = 20,
    user=Depends(get_current_user)
):
    """
    Get all quizzes for the current user (quiz library)
    """
    try:
        user_id = user.get("user_id") if user else None
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        supabase = get_supabase_client()

        # Build query
        query = supabase.table("conversation_quizzes").select("*").eq("user_id", user_id)

        if roadmap_id:
            query = query.eq("roadmap_id", roadmap_id)

        if status:
            query = query.eq("status", status)

        if difficulty:
            query = query.eq("difficulty", difficulty)

        query = query.order("created_at", desc=True).limit(limit)

        result = query.execute()

        # Get attempt counts for each quiz
        quiz_ids = [quiz["id"] for quiz in result.data]
        attempts_query = supabase.table("quiz_attempts")\
            .select("quiz_id, id, status, percentage_score")\
            .in_("quiz_id", quiz_ids)\
            .execute()

        # Group attempts by quiz_id
        attempts_by_quiz = {}
        for attempt in attempts_query.data:
            quiz_id = attempt["quiz_id"]
            if quiz_id not in attempts_by_quiz:
                attempts_by_quiz[quiz_id] = []
            attempts_by_quiz[quiz_id].append(attempt)

        # Enrich quizzes with attempt data
        for quiz in result.data:
            quiz_id = quiz["id"]
            quiz_attempts = attempts_by_quiz.get(quiz_id, [])
            quiz["attempt_count"] = len(quiz_attempts)
            quiz["best_score"] = max([a["percentage_score"] for a in quiz_attempts], default=0)
            quiz["completed_attempts"] = len([a for a in quiz_attempts if a["status"] == "completed"])

        return {
            "quizzes": result.data,
            "count": len(result.data)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quizzes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching quizzes: {str(e)}")


@router.get("/{quiz_id}", response_model=Dict[str, Any])
async def get_quiz(
    quiz_id: str,
    user=Depends(get_current_user)
):
    """
    Get a specific quiz (without showing correct answers)
    """
    try:
        user_id = user.get("user_id") if user else None
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        supabase = get_supabase_client()

        # Get quiz
        quiz_result = supabase.table("conversation_quizzes")\
            .select("*")\
            .eq("id", quiz_id)\
            .eq("user_id", user_id)\
            .execute()

        if not quiz_result.data:
            raise HTTPException(status_code=404, detail="Quiz not found")

        quiz = quiz_result.data[0]

        # Remove correct answers from questions (unless quiz is completed)
        if quiz["status"] != "completed":
            for question in quiz["questions"]:
                question.pop("correct_answer", None)
                question.pop("explanation", None)

        # Get attempts
        attempts_result = supabase.table("quiz_attempts")\
            .select("*")\
            .eq("quiz_id", quiz_id)\
            .order("created_at", desc=True)\
            .execute()

        return {
            "quiz": quiz,
            "attempts": attempts_result.data
        }

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quiz: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching quiz: {str(e)}")


# ============================================================================
# QUIZ ATTEMPT ENDPOINTS
# ============================================================================

@router.post("/attempt", response_model=Dict[str, Any])
async def start_quiz_attempt(
    request: StartAttemptRequest,
    user=Depends(get_current_user)
):
    """
    Start a new quiz attempt
    """
    try:
        user_id = user.get("user_id") if user else None
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        supabase = get_supabase_client()

        # Get quiz
        quiz_result = supabase.table("conversation_quizzes")\
            .select("*")\
            .eq("id", request.quiz_id)\
            .eq("user_id", user_id)\
            .execute()

        if not quiz_result.data:
            raise HTTPException(status_code=404, detail="Quiz not found")

        quiz = quiz_result.data[0]

        # Check attempts limit
        existing_attempts = supabase.table("quiz_attempts")\
            .select("id")\
            .eq("quiz_id", request.quiz_id)\
            .execute()

        if len(existing_attempts.data) >= quiz.get("attempts_allowed", 3):
            raise HTTPException(status_code=400, detail="Maximum attempts reached")

        # Create attempt
        attempt_record = {
            "user_id": user_id,
            "quiz_id": request.quiz_id,
            "roadmap_id": quiz.get("roadmap_id"),
            "attempt_number": len(existing_attempts.data) + 1,
            "answers": {},
            "total_questions": len(quiz.get("questions", [])),
            "total_points": quiz.get("total_points", 0),
            "status": "in_progress",
            "started_at": datetime.now().isoformat()
        }

        result = supabase.table("quiz_attempts").insert(attempt_record).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create attempt")

        # Update quiz status
        if quiz["status"] == "not_started":
            supabase.table("conversation_quizzes")\
                .update({"status": "in_progress", "presented_at": datetime.now().isoformat()})\
                .eq("id", request.quiz_id)\
                .execute()

        logger.info(f"Quiz attempt started: {result.data[0]['id']}")

        return {
            "status": "success",
            "attempt_id": result.data[0]["id"],
            "attempt": result.data[0],
            "quiz": quiz
        }

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting quiz attempt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error starting quiz attempt: {str(e)}")


@router.post("/attempt/{attempt_id}/answer", response_model=Dict[str, Any])
async def submit_quiz_answer(
    attempt_id: str,
    request: SubmitAnswerRequest,
    user=Depends(get_current_user)
):
    """
    Submit an answer for grading and update attempt
    """
    try:
        user_id = user.get("user_id") if user else None
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        supabase = get_supabase_client()

        # Get attempt
        attempt_result = supabase.table("quiz_attempts")\
            .select("*")\
            .eq("id", attempt_id)\
            .eq("user_id", user_id)\
            .execute()

        if not attempt_result.data:
            raise HTTPException(status_code=404, detail="Attempt not found")

        attempt = attempt_result.data[0]

        if attempt["status"] != "in_progress":
            raise HTTPException(status_code=400, detail="Attempt is not in progress")

        # Get quiz to access questions
        quiz_result = supabase.table("conversation_quizzes")\
            .select("*")\
            .eq("id", attempt["quiz_id"])\
            .execute()

        if not quiz_result.data:
            raise HTTPException(status_code=404, detail="Quiz not found")

        quiz = quiz_result.data[0]

        # Find the question
        question = None
        for q in quiz["questions"]:
            if q["id"] == request.question_id:
                question = q
                break

        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        # Grade the answer using AI
        grading_result = await quiz_grader.grade_answer(
            question=question,
            student_answer=request.answer,
            question_type=question["type"]
        )

        # Update attempt with graded answer
        answers = attempt.get("answers", {})
        answers[request.question_id] = {
            "answer": request.answer,
            "correct": grading_result["correct"],
            "points_earned": grading_result["points_earned"],
            "feedback": grading_result["feedback"],
            "time_spent": request.time_spent,
            "partial_credit": grading_result.get("partial_credit", False)
        }

        # Add test results for code questions
        if "test_results" in grading_result:
            answers[request.question_id]["test_results"] = grading_result["test_results"]

        # Update attempt
        supabase.table("quiz_attempts")\
            .update({"answers": answers})\
            .eq("id", attempt_id)\
            .execute()

        logger.info(f"Answer graded for question {request.question_id}: {grading_result['correct']}")

        return {
            "status": "success",
            "question_id": request.question_id,
            "grading_result": grading_result
        }

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting answer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error submitting answer: {str(e)}")


@router.post("/attempt/{attempt_id}/complete", response_model=Dict[str, Any])
async def complete_quiz_attempt(
    attempt_id: str,
    user=Depends(get_current_user)
):
    """
    Complete a quiz attempt and generate final results
    """
    try:
        user_id = user.get("user_id") if user else None
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        supabase = get_supabase_client()

        # Get attempt
        attempt_result = supabase.table("quiz_attempts")\
            .select("*")\
            .eq("id", attempt_id)\
            .eq("user_id", user_id)\
            .execute()

        if not attempt_result.data:
            raise HTTPException(status_code=404, detail="Attempt not found")

        attempt = attempt_result.data[0]

        # Get quiz
        quiz_result = supabase.table("conversation_quizzes")\
            .select("*")\
            .eq("id", attempt["quiz_id"])\
            .execute()

        quiz = quiz_result.data[0]

        # Calculate final scores
        answers = attempt.get("answers", {})
        correct_count = sum(1 for ans in answers.values() if ans["correct"])
        partial_count = sum(1 for ans in answers.values() if ans.get("partial_credit", False))
        total_points_earned = sum(ans["points_earned"] for ans in answers.values())
        total_points = attempt["total_points"]
        percentage_score = (total_points_earned / total_points * 100) if total_points > 0 else 0

        # Determine if passed
        passed = percentage_score >= quiz.get("passing_score", 70.0)

        # Generate overall feedback using AI
        overall_feedback = await quiz_grader.generate_overall_feedback(quiz, attempt)

        # Calculate total time spent
        time_spent = sum(ans.get("time_spent", 0) for ans in answers.values())

        # Update attempt with final results
        update_data = {
            "correct_answers": correct_count,
            "partial_credit_answers": partial_count,
            "points_earned": total_points_earned,
            "percentage_score": percentage_score,
            "passed": passed,
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "time_spent": time_spent,
            "overall_feedback": overall_feedback.get("overall_feedback"),
            "strengths": overall_feedback.get("strengths", []),
            "weaknesses": overall_feedback.get("weaknesses", []),
            "recommendations": overall_feedback.get("recommendations", [])
        }

        result = supabase.table("quiz_attempts")\
            .update(update_data)\
            .eq("id", attempt_id)\
            .execute()

        # Update quiz status
        supabase.table("conversation_quizzes")\
            .update({"status": "completed", "attempts_used": len(answers)})\
            .eq("id", attempt["quiz_id"])\
            .execute()

        # Update milestone progress if linked to roadmap
        if attempt.get("roadmap_id") and quiz.get("milestone_id"):
            await _update_milestone_with_quiz_result(
                user_id,
                attempt["roadmap_id"],
                quiz.get("phase_id"),
                quiz.get("milestone_id"),
                quiz["id"],
                passed,
                percentage_score
            )

        logger.info(f"Quiz attempt completed: {attempt_id} - Score: {percentage_score:.1f}% - Passed: {passed}")

        return {
            "status": "success",
            "results": {
                "attempt_id": attempt_id,
                "percentage_score": percentage_score,
                "passed": passed,
                "correct_answers": correct_count,
                "total_questions": attempt["total_questions"],
                "time_spent": time_spent,
                **overall_feedback
            },
            "attempt": result.data[0] if result.data else None
        }

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing quiz: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error completing quiz: {str(e)}")


@router.get("/attempt/{attempt_id}", response_model=Dict[str, Any])
async def get_attempt_details(
    attempt_id: str,
    user=Depends(get_current_user)
):
    """
    Get detailed results of a quiz attempt
    """
    try:
        user_id = user.get("user_id") if user else None
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        supabase = get_supabase_client()

        # Get attempt
        attempt_result = supabase.table("quiz_attempts")\
            .select("*")\
            .eq("id", attempt_id)\
            .eq("user_id", user_id)\
            .execute()

        if not attempt_result.data:
            raise HTTPException(status_code=404, detail="Attempt not found")

        attempt = attempt_result.data[0]

        # Get quiz
        quiz_result = supabase.table("conversation_quizzes")\
            .select("*")\
            .eq("id", attempt["quiz_id"])\
            .execute()

        return {
            "attempt": attempt,
            "quiz": quiz_result.data[0] if quiz_result.data else None
        }

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching attempt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching attempt: {str(e)}")


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@router.get("/stats/summary", response_model=Dict[str, Any])
async def get_quiz_statistics(user=Depends(get_current_user)):
    """
    Get overall quiz statistics for the user
    """
    try:
        user_id = user.get("user_id") if user else None
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        supabase = get_supabase_client()

        # Call the database function
        result = supabase.rpc("get_quiz_statistics", {"p_user_id": user_id}).execute()

        stats = result.data[0] if result.data else {
            "total_quizzes": 0,
            "completed_quizzes": 0,
            "passed_quizzes": 0,
            "average_score": 0.0,
            "total_time_spent": 0
        }

        return {"stats": stats}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quiz stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching quiz stats: {str(e)}")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _update_milestone_with_quiz_result(
    user_id: str,
    roadmap_id: str,
    phase_id: str,
    milestone_id: str,
    quiz_id: str,
    passed: bool,
    score: float
):
    """Update milestone progress when quiz is completed"""
    try:
        supabase = get_supabase_client()

        update_data = {
            "quiz_id": quiz_id,
            "quiz_passed": passed,
            "best_quiz_score": score,
            "status": "completed" if passed else "in_progress",
            "progress_percentage": 100.0 if passed else 50.0
        }

        if passed:
            update_data["completed_at"] = datetime.now().isoformat()

        supabase.table("milestone_progress")\
            .update(update_data)\
            .eq("user_id", user_id)\
            .eq("roadmap_id", roadmap_id)\
            .eq("phase_id", phase_id)\
            .eq("milestone_id", milestone_id)\
            .execute()

        logger.info(f"Milestone {milestone_id} updated with quiz result: passed={passed}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating milestone: {e}")
