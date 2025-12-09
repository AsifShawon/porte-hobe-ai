"""
Practice Router
Handles practice exercises, coding challenges, quizzes, and submissions
"""

import logging
from typing import List, Optional
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import get_current_user
from config import get_supabase_client

logger = logging.getLogger("practice_router")

router = APIRouter(prefix="/api/practice", tags=["practice"])


class ExerciseType(str, Enum):
    """Types of practice exercises"""
    CODING = "coding"
    QUIZ = "quiz"
    MATH = "math"
    CONCEPT = "concept"
    DEBUGGING = "debugging"


class ExerciseDifficulty(str, Enum):
    """Difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class SubmissionStatus(str, Enum):
    """Submission status"""
    PENDING = "pending"
    CORRECT = "correct"
    INCORRECT = "incorrect"
    PARTIAL = "partial"


class ExerciseResponse(BaseModel):
    """Practice exercise response"""
    id: str
    title: str
    description: str
    exercise_type: str
    difficulty: str
    topic_id: Optional[str]
    topic_title: Optional[str]
    points: int
    time_limit: Optional[int]  # minutes
    content: dict  # Exercise-specific content (code template, questions, etc.)
    hints: List[str]
    solution: Optional[str] = None  # Only shown after completion
    tags: List[str]
    created_at: str
    attempts: int = 0  # User's attempts
    completed: bool = False
    best_score: Optional[float] = None


class ExerciseSubmission(BaseModel):
    """Submit exercise solution"""
    exercise_id: str
    answer: str  # Code, answer text, or JSON for quiz
    time_spent: Optional[int] = None  # seconds
    metadata: Optional[dict] = {}


class SubmissionResponse(BaseModel):
    """Submission result"""
    id: str
    exercise_id: str
    user_id: str
    answer: str
    status: str
    score: float  # 0-100
    feedback: str
    hints_used: int
    time_spent: Optional[int]
    submitted_at: str
    test_results: Optional[dict] = {}  # For coding exercises


class ExerciseStats(BaseModel):
    """User's practice statistics"""
    total_exercises: int
    completed_exercises: int
    in_progress_exercises: int
    total_attempts: int
    success_rate: float
    average_score: float
    total_points_earned: int
    exercises_by_type: dict
    exercises_by_difficulty: dict
    recent_submissions: List[SubmissionResponse]


class CreateExercise(BaseModel):
    """Create a new exercise (admin/teacher only in future)"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str
    exercise_type: ExerciseType
    difficulty: ExerciseDifficulty
    topic_id: Optional[str] = None
    points: int = Field(default=10, ge=0)
    time_limit: Optional[int] = None
    content: dict  # Exercise content (varies by type)
    hints: List[str] = []
    solution: Optional[str] = None
    tags: List[str] = []


@router.get("/exercises", response_model=List[ExerciseResponse])
async def get_exercises(
    exercise_type: Optional[ExerciseType] = None,
    difficulty: Optional[ExerciseDifficulty] = None,
    topic_id: Optional[str] = None,
    completed: Optional[bool] = None,
    user: dict = Depends(get_current_user)
):
    """
    Get all available practice exercises with user progress

    - **exercise_type**: Filter by type (coding, quiz, math, etc.)
    - **difficulty**: Filter by difficulty
    - **topic_id**: Filter by topic
    - **completed**: Filter by completion status
    """
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        # Get exercises
        query = supabase.table('practice_exercises')\
            .select('*, topics(title)')\
            .order('difficulty', desc=False)\
            .order('created_at', desc=True)

        if exercise_type:
            query = query.eq('exercise_type', exercise_type.value)

        if difficulty:
            query = query.eq('difficulty', difficulty.value)

        if topic_id:
            query = query.eq('topic_id', topic_id)

        exercises_result = query.execute()

        # Get user's submissions
        submissions = supabase.table('practice_submissions')\
            .select('exercise_id, status, score, submitted_at')\
            .eq('user_id', user['user_id'])\
            .execute()

        # Create lookup for user progress
        user_progress = {}
        for sub in submissions.data:
            ex_id = sub['exercise_id']
            if ex_id not in user_progress:
                user_progress[ex_id] = {
                    'attempts': 0,
                    'completed': False,
                    'best_score': 0.0
                }

            user_progress[ex_id]['attempts'] += 1

            if sub['status'] == SubmissionStatus.CORRECT.value:
                user_progress[ex_id]['completed'] = True

            if sub['score'] > user_progress[ex_id]['best_score']:
                user_progress[ex_id]['best_score'] = sub['score']

        # Format response
        exercises = []
        for ex in exercises_result.data:
            progress = user_progress.get(ex['id'], {
                'attempts': 0,
                'completed': False,
                'best_score': None
            })

            # Apply completed filter
            if completed is not None and progress['completed'] != completed:
                continue

            topic_title = None
            if ex.get('topics'):
                topic_title = ex['topics'].get('title')

            exercises.append(ExerciseResponse(
                id=ex['id'],
                title=ex['title'],
                description=ex['description'],
                exercise_type=ex['exercise_type'],
                difficulty=ex['difficulty'],
                topic_id=ex.get('topic_id'),
                topic_title=topic_title,
                points=ex['points'],
                time_limit=ex.get('time_limit'),
                content=ex['content'],
                hints=ex.get('hints', []),
                solution=ex.get('solution') if progress['completed'] else None,
                tags=ex.get('tags', []),
                created_at=ex['created_at'],
                attempts=progress['attempts'],
                completed=progress['completed'],
                best_score=progress['best_score']
            ))

        return exercises

    except Exception as e:
        logger.error(f"❌ Failed to get exercises: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve exercises")


@router.get("/exercises/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(
    exercise_id: str,
    user: dict = Depends(get_current_user)
):
    """Get a specific exercise with user progress"""
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        # Get exercise
        exercise = supabase.table('practice_exercises')\
            .select('*, topics(title)')\
            .eq('id', exercise_id)\
            .single()\
            .execute()

        if not exercise.data:
            raise HTTPException(status_code=404, detail="Exercise not found")

        ex = exercise.data

        # Get user's submissions for this exercise
        submissions = supabase.table('practice_submissions')\
            .select('status, score')\
            .eq('user_id', user['user_id'])\
            .eq('exercise_id', exercise_id)\
            .execute()

        attempts = len(submissions.data)
        completed = any(s['status'] == SubmissionStatus.CORRECT.value for s in submissions.data)
        best_score = max([s['score'] for s in submissions.data], default=None)

        topic_title = None
        if ex.get('topics'):
            topic_title = ex['topics'].get('title')

        return ExerciseResponse(
            id=ex['id'],
            title=ex['title'],
            description=ex['description'],
            exercise_type=ex['exercise_type'],
            difficulty=ex['difficulty'],
            topic_id=ex.get('topic_id'),
            topic_title=topic_title,
            points=ex['points'],
            time_limit=ex.get('time_limit'),
            content=ex['content'],
            hints=ex.get('hints', []),
            solution=ex.get('solution') if completed else None,
            tags=ex.get('tags', []),
            created_at=ex['created_at'],
            attempts=attempts,
            completed=completed,
            best_score=best_score
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get exercise: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve exercise")


@router.post("/submit", response_model=SubmissionResponse)
async def submit_exercise(
    submission: ExerciseSubmission,
    user: dict = Depends(get_current_user)
):
    """
    Submit exercise solution for evaluation

    - **exercise_id**: Exercise ID
    - **answer**: Solution (code, text, or JSON)
    - **time_spent**: Time spent in seconds
    """
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        # Get exercise
        exercise = supabase.table('practice_exercises')\
            .select('*')\
            .eq('id', submission.exercise_id)\
            .single()\
            .execute()

        if not exercise.data:
            raise HTTPException(status_code=404, detail="Exercise not found")

        ex = exercise.data

        # Evaluate submission based on type
        evaluation = await _evaluate_submission(
            ex['exercise_type'],
            submission.answer,
            ex.get('solution'),
            ex['content']
        )

        # Create submission record
        submission_data = {
            'user_id': user['user_id'],
            'exercise_id': submission.exercise_id,
            'answer': submission.answer,
            'status': evaluation['status'],
            'score': evaluation['score'],
            'feedback': evaluation['feedback'],
            'hints_used': submission.metadata.get('hints_used', 0),
            'time_spent': submission.time_spent,
            'test_results': evaluation.get('test_results', {}),
            'submitted_at': datetime.utcnow().isoformat()
        }

        result = supabase.table('practice_submissions').insert(submission_data).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to save submission")

        # Award points if correct
        if evaluation['status'] == SubmissionStatus.CORRECT.value:
            await _award_practice_points(supabase, user['user_id'], ex['points'])

        logger.info(f"✅ Submission for exercise {submission.exercise_id} by user {user['user_id']}: {evaluation['status']}")

        return SubmissionResponse(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to submit exercise: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit exercise: {str(e)}")


@router.get("/submissions", response_model=List[SubmissionResponse])
async def get_submissions(
    exercise_id: Optional[str] = None,
    status: Optional[SubmissionStatus] = None,
    limit: int = 20,
    user: dict = Depends(get_current_user)
):
    """
    Get user's exercise submissions

    - **exercise_id**: Filter by exercise
    - **status**: Filter by status
    - **limit**: Max results (default 20)
    """
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        query = supabase.table('practice_submissions')\
            .select('*')\
            .eq('user_id', user['user_id'])\
            .order('submitted_at', desc=True)\
            .limit(limit)

        if exercise_id:
            query = query.eq('exercise_id', exercise_id)

        if status:
            query = query.eq('status', status.value)

        result = query.execute()

        return [SubmissionResponse(**s) for s in result.data]

    except Exception as e:
        logger.error(f"❌ Failed to get submissions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve submissions")


@router.get("/stats", response_model=ExerciseStats)
async def get_practice_stats(
    user: dict = Depends(get_current_user)
):
    """Get user's practice statistics"""
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        # Get all exercises
        all_exercises = supabase.table('practice_exercises').select('id, exercise_type, difficulty, points').execute()

        # Get user's submissions
        submissions = supabase.table('practice_submissions')\
            .select('*')\
            .eq('user_id', user['user_id'])\
            .execute()

        # Calculate stats
        total_exercises = len(all_exercises.data)
        completed_exercise_ids = set()
        in_progress_ids = set()

        for sub in submissions.data:
            if sub['status'] == SubmissionStatus.CORRECT.value:
                completed_exercise_ids.add(sub['exercise_id'])
            else:
                in_progress_ids.add(sub['exercise_id'])

        # Remove completed from in_progress
        in_progress_ids = in_progress_ids - completed_exercise_ids

        total_attempts = len(submissions.data)
        correct_submissions = sum(1 for s in submissions.data if s['status'] == SubmissionStatus.CORRECT.value)
        success_rate = round((correct_submissions / total_attempts * 100) if total_attempts > 0 else 0.0, 2)

        scores = [s['score'] for s in submissions.data]
        average_score = round(sum(scores) / len(scores), 2) if scores else 0.0

        # Calculate total points earned (from completed exercises only)
        completed_exercises = [e for e in all_exercises.data if e['id'] in completed_exercise_ids]
        total_points_earned = sum(e['points'] for e in completed_exercises)

        # Breakdown by type
        exercises_by_type = {}
        for ex in all_exercises.data:
            ex_type = ex['exercise_type']
            if ex_type not in exercises_by_type:
                exercises_by_type[ex_type] = {'total': 0, 'completed': 0}
            exercises_by_type[ex_type]['total'] += 1
            if ex['id'] in completed_exercise_ids:
                exercises_by_type[ex_type]['completed'] += 1

        # Breakdown by difficulty
        exercises_by_difficulty = {}
        for ex in all_exercises.data:
            difficulty = ex['difficulty']
            if difficulty not in exercises_by_difficulty:
                exercises_by_difficulty[difficulty] = {'total': 0, 'completed': 0}
            exercises_by_difficulty[difficulty]['total'] += 1
            if ex['id'] in completed_exercise_ids:
                exercises_by_difficulty[difficulty]['completed'] += 1

        # Recent submissions
        recent = sorted(submissions.data, key=lambda x: x['submitted_at'], reverse=True)[:10]
        recent_submissions = [SubmissionResponse(**s) for s in recent]

        return ExerciseStats(
            total_exercises=total_exercises,
            completed_exercises=len(completed_exercise_ids),
            in_progress_exercises=len(in_progress_ids),
            total_attempts=total_attempts,
            success_rate=success_rate,
            average_score=average_score,
            total_points_earned=total_points_earned,
            exercises_by_type=exercises_by_type,
            exercises_by_difficulty=exercises_by_difficulty,
            recent_submissions=recent_submissions
        )

    except Exception as e:
        logger.error(f"❌ Failed to get practice stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@router.post("/exercises", response_model=ExerciseResponse)
async def create_exercise(
    exercise: CreateExercise,
    user: dict = Depends(get_current_user)
):
    """
    Create a new practice exercise

    Note: In production, this should be admin/teacher only
    """
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        exercise_data = {
            'title': exercise.title,
            'description': exercise.description,
            'exercise_type': exercise.exercise_type.value,
            'difficulty': exercise.difficulty.value,
            'topic_id': exercise.topic_id,
            'points': exercise.points,
            'time_limit': exercise.time_limit,
            'content': exercise.content,
            'hints': exercise.hints,
            'solution': exercise.solution,
            'tags': exercise.tags,
            'created_by': user['user_id']
        }

        result = supabase.table('practice_exercises').insert(exercise_data).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create exercise")

        logger.info(f"✅ Created exercise '{exercise.title}'")

        ex = result.data[0]
        return ExerciseResponse(
            id=ex['id'],
            title=ex['title'],
            description=ex['description'],
            exercise_type=ex['exercise_type'],
            difficulty=ex['difficulty'],
            topic_id=ex.get('topic_id'),
            topic_title=None,
            points=ex['points'],
            time_limit=ex.get('time_limit'),
            content=ex['content'],
            hints=ex.get('hints', []),
            solution=None,  # Don't expose to creator
            tags=ex.get('tags', []),
            created_at=ex['created_at'],
            attempts=0,
            completed=False,
            best_score=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create exercise: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create exercise: {str(e)}")


# --- Helper Functions ---
async def _evaluate_submission(
    exercise_type: str,
    answer: str,
    solution: Optional[str],
    content: dict
) -> dict:
    """
    Evaluate submission based on exercise type

    Returns: {status, score, feedback, test_results}
    """
    if exercise_type == ExerciseType.QUIZ.value:
        # Quiz evaluation
        return _evaluate_quiz(answer, solution, content)

    elif exercise_type == ExerciseType.CODING.value:
        # Coding evaluation (simplified - would use code execution sandbox in production)
        return _evaluate_code(answer, solution, content)

    elif exercise_type == ExerciseType.MATH.value:
        # Math evaluation
        return _evaluate_math(answer, solution)

    else:
        # Generic text comparison
        return _evaluate_text(answer, solution)


def _evaluate_quiz(answer: str, solution: str, content: dict) -> dict:
    """Evaluate quiz answer"""
    import json

    try:
        user_answers = json.loads(answer)
        correct_answers = json.loads(solution) if solution else {}

        total_questions = len(correct_answers)
        correct_count = 0

        for q_id, correct_ans in correct_answers.items():
            if user_answers.get(q_id) == correct_ans:
                correct_count += 1

        score = round((correct_count / total_questions * 100) if total_questions > 0 else 0.0, 2)

        if score >= 100:
            status = SubmissionStatus.CORRECT.value
            feedback = "Perfect! All answers correct."
        elif score >= 70:
            status = SubmissionStatus.PARTIAL.value
            feedback = f"Good job! {correct_count}/{total_questions} correct."
        else:
            status = SubmissionStatus.INCORRECT.value
            feedback = f"Keep trying! {correct_count}/{total_questions} correct."

        return {
            'status': status,
            'score': score,
            'feedback': feedback,
            'test_results': {
                'correct': correct_count,
                'total': total_questions
            }
        }
    except:
        return {
            'status': SubmissionStatus.INCORRECT.value,
            'score': 0.0,
            'feedback': 'Invalid answer format',
            'test_results': {}
        }


def _evaluate_code(answer: str, solution: str, content: dict) -> dict:
    """
    Evaluate code submission (simplified)

    In production, this would:
    1. Run code in a secure sandbox
    2. Execute test cases
    3. Check for syntax errors, performance, etc.
    """
    # Simplified: just check if answer is not empty and has basic structure
    if not answer or len(answer.strip()) < 10:
        return {
            'status': SubmissionStatus.INCORRECT.value,
            'score': 0.0,
            'feedback': 'Solution is too short or empty',
            'test_results': {}
        }

    # In a real system, run test cases from content['test_cases']
    # For now, give partial credit
    return {
        'status': SubmissionStatus.PARTIAL.value,
        'score': 75.0,
        'feedback': 'Code submitted successfully. Manual review required.',
        'test_results': {
            'message': 'Code execution sandbox not implemented yet'
        }
    }


def _evaluate_math(answer: str, solution: str) -> dict:
    """Evaluate math answer"""
    # Normalize and compare
    answer_clean = answer.strip().lower().replace(' ', '')
    solution_clean = solution.strip().lower().replace(' ', '') if solution else ''

    if answer_clean == solution_clean:
        return {
            'status': SubmissionStatus.CORRECT.value,
            'score': 100.0,
            'feedback': 'Correct!',
            'test_results': {}
        }
    else:
        return {
            'status': SubmissionStatus.INCORRECT.value,
            'score': 0.0,
            'feedback': 'Incorrect answer. Try again!',
            'test_results': {}
        }


def _evaluate_text(answer: str, solution: str) -> dict:
    """Evaluate text answer"""
    # Simple text comparison (case-insensitive)
    answer_clean = answer.strip().lower()
    solution_clean = solution.strip().lower() if solution else ''

    if answer_clean == solution_clean:
        return {
            'status': SubmissionStatus.CORRECT.value,
            'score': 100.0,
            'feedback': 'Correct!',
            'test_results': {}
        }
    else:
        # Check for partial match
        similarity = len(set(answer_clean.split()) & set(solution_clean.split())) / len(set(solution_clean.split())) if solution_clean else 0

        if similarity > 0.7:
            return {
                'status': SubmissionStatus.PARTIAL.value,
                'score': round(similarity * 100, 2),
                'feedback': 'Partially correct. Review your answer.',
                'test_results': {}
            }
        else:
            return {
                'status': SubmissionStatus.INCORRECT.value,
                'score': 0.0,
                'feedback': 'Incorrect. Try again!',
                'test_results': {}
            }


async def _award_practice_points(supabase, user_id: str, points: int):
    """Award points to user for completing practice"""
    try:
        # This could update a user_stats table or trigger achievement checks
        logger.info(f"🎯 Awarded {points} points to user {user_id}")

        # In a full implementation, you'd:
        # 1. Update user's total points
        # 2. Check for level-up
        # 3. Trigger achievement checks

    except Exception as e:
        logger.warning(f"⚠️ Failed to award points: {e}")
