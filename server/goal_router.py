"""
Goal Router
Handles student study goals, milestones, and goal tracking
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import get_current_user
from config import get_supabase_client

logger = logging.getLogger("goal_router")

router = APIRouter(prefix="/api/goals", tags=["goals"])


class GoalType(str, Enum):
    """Types of goals students can set"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"
    TOPIC_COMPLETION = "topic_completion"
    STREAK = "streak"
    PRACTICE = "practice"


class GoalStatus(str, Enum):
    """Goal status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class GoalCreate(BaseModel):
    """Create a new goal"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    goal_type: GoalType
    target_value: float = Field(..., gt=0)  # e.g., 5 topics, 30 minutes, 7 days
    current_value: float = Field(default=0.0, ge=0)
    unit: str = Field(default="items")  # topics, minutes, days, points
    deadline: Optional[str] = None  # ISO datetime string
    topic_id: Optional[str] = None  # If goal is related to specific topic
    metadata: Optional[dict] = {}


class GoalUpdate(BaseModel):
    """Update goal progress"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    current_value: Optional[float] = Field(None, ge=0)
    increment_value: Optional[float] = None  # Add to current value
    status: Optional[GoalStatus] = None
    deadline: Optional[str] = None
    metadata: Optional[dict] = None


class GoalResponse(BaseModel):
    """Goal response model"""
    id: str
    user_id: str
    title: str
    description: Optional[str]
    goal_type: str
    target_value: float
    current_value: float
    unit: str
    progress_percentage: float
    status: str
    deadline: Optional[str]
    topic_id: Optional[str]
    metadata: dict
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None


class GoalStats(BaseModel):
    """Overall goal statistics"""
    total_goals: int
    active_goals: int
    completed_goals: int
    failed_goals: int
    completion_rate: float
    current_streak: int  # Consecutive days with active goals
    longest_streak: int


@router.post("/", response_model=GoalResponse)
async def create_goal(
    goal: GoalCreate,
    user: dict = Depends(get_current_user)
):
    """
    Create a new study goal

    - **title**: Goal title (e.g., "Complete 5 topics this week")
    - **goal_type**: Type of goal (daily, weekly, monthly, topic_completion, etc.)
    - **target_value**: Target to achieve (e.g., 5 topics, 30 minutes)
    - **unit**: Unit of measurement (topics, minutes, days, points)
    - **deadline**: Optional deadline (ISO datetime)
    - **topic_id**: Optional topic ID if goal is topic-specific
    """
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        # Create goal data
        goal_data = {
            'user_id': user['user_id'],
            'title': goal.title,
            'description': goal.description,
            'goal_type': goal.goal_type.value,
            'target_value': goal.target_value,
            'current_value': goal.current_value,
            'unit': goal.unit,
            'status': GoalStatus.ACTIVE.value,
            'deadline': goal.deadline,
            'topic_id': goal.topic_id,
            'metadata': goal.metadata or {}
        }

        # Insert into database
        result = supabase.table('goals').insert(goal_data).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create goal")

        goal_record = result.data[0]

        logger.info(f"✅ Created goal '{goal.title}' for user {user['user_id']}")

        return _format_goal_response(goal_record)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create goal: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create goal: {str(e)}")


@router.get("/", response_model=List[GoalResponse])
async def get_all_goals(
    status: Optional[GoalStatus] = None,
    goal_type: Optional[GoalType] = None,
    user: dict = Depends(get_current_user)
):
    """
    Get all goals for the current user

    - **status**: Optional filter by status (active, completed, failed, paused)
    - **goal_type**: Optional filter by goal type
    """
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        query = supabase.table('goals')\
            .select('*')\
            .eq('user_id', user['user_id'])\
            .order('created_at', desc=True)

        if status:
            query = query.eq('status', status.value)

        if goal_type:
            query = query.eq('goal_type', goal_type.value)

        result = query.execute()

        goals = [_format_goal_response(g) for g in result.data]

        # Auto-update expired goals
        now = datetime.utcnow()
        for goal in goals:
            if goal.status == GoalStatus.ACTIVE.value and goal.deadline:
                deadline = datetime.fromisoformat(goal.deadline.replace('Z', '+00:00'))
                if deadline < now and goal.progress_percentage < 100:
                    # Mark as failed
                    await _update_goal_status(supabase, goal.id, GoalStatus.FAILED.value)
                    goal.status = GoalStatus.FAILED.value

        return goals

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get goals: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve goals")


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: str,
    user: dict = Depends(get_current_user)
):
    """Get a specific goal by ID"""
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        result = supabase.table('goals')\
            .select('*')\
            .eq('id', goal_id)\
            .eq('user_id', user['user_id'])\
            .single()\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Goal not found")

        return _format_goal_response(result.data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get goal: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve goal")


@router.patch("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: str,
    update: GoalUpdate,
    user: dict = Depends(get_current_user)
):
    """
    Update goal progress or details

    - **current_value**: Set new current value
    - **increment_value**: Add to current value (e.g., +1 topic completed)
    - **status**: Change goal status
    """
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        # Get current goal
        current = supabase.table('goals')\
            .select('*')\
            .eq('id', goal_id)\
            .eq('user_id', user['user_id'])\
            .single()\
            .execute()

        if not current.data:
            raise HTTPException(status_code=404, detail="Goal not found")

        goal_data = current.data
        update_data = {'updated_at': datetime.utcnow().isoformat()}

        # Update fields
        if update.title is not None:
            update_data['title'] = update.title

        if update.description is not None:
            update_data['description'] = update.description

        if update.deadline is not None:
            update_data['deadline'] = update.deadline

        # Update current value
        if update.current_value is not None:
            update_data['current_value'] = update.current_value
        elif update.increment_value is not None:
            update_data['current_value'] = goal_data['current_value'] + update.increment_value

        # Check if goal is completed
        if 'current_value' in update_data:
            new_current = update_data['current_value']
            target = goal_data['target_value']

            if new_current >= target and goal_data['status'] == GoalStatus.ACTIVE.value:
                update_data['status'] = GoalStatus.COMPLETED.value
                update_data['completed_at'] = datetime.utcnow().isoformat()
                logger.info(f"🎯 Goal '{goal_data['title']}' completed!")

        # Manual status update
        if update.status is not None:
            update_data['status'] = update.status.value
            if update.status == GoalStatus.COMPLETED and not goal_data.get('completed_at'):
                update_data['completed_at'] = datetime.utcnow().isoformat()

        # Merge metadata
        if update.metadata is not None:
            current_meta = goal_data.get('metadata', {})
            current_meta.update(update.metadata)
            update_data['metadata'] = current_meta

        # Update in database
        result = supabase.table('goals')\
            .update(update_data)\
            .eq('id', goal_id)\
            .execute()

        # Return updated goal
        return await get_goal(goal_id, user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update goal: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update goal: {str(e)}")


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: str,
    user: dict = Depends(get_current_user)
):
    """Delete a goal"""
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        result = supabase.table('goals')\
            .delete()\
            .eq('id', goal_id)\
            .eq('user_id', user['user_id'])\
            .execute()

        logger.info(f"✅ Deleted goal {goal_id}")

        return {"message": "Goal deleted successfully", "goal_id": goal_id}

    except Exception as e:
        logger.error(f"❌ Failed to delete goal: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete goal")


@router.get("/stats/summary", response_model=GoalStats)
async def get_goal_stats(
    user: dict = Depends(get_current_user)
):
    """Get overall goal statistics for the user"""
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        # Get all goals
        result = supabase.table('goals')\
            .select('*')\
            .eq('user_id', user['user_id'])\
            .execute()

        goals = result.data
        total_goals = len(goals)
        active_goals = sum(1 for g in goals if g['status'] == GoalStatus.ACTIVE.value)
        completed_goals = sum(1 for g in goals if g['status'] == GoalStatus.COMPLETED.value)
        failed_goals = sum(1 for g in goals if g['status'] == GoalStatus.FAILED.value)

        # Calculate completion rate
        completion_rate = round(
            (completed_goals / total_goals * 100) if total_goals > 0 else 0.0,
            2
        )

        # Calculate streak (consecutive days with at least one active goal)
        current_streak = 0
        longest_streak = 0

        if goals:
            # Get goals sorted by date
            sorted_goals = sorted(goals, key=lambda x: x['created_at'])

            # Simple streak calculation based on consecutive days with goals
            streak_dates = set()
            for goal in sorted_goals:
                created = datetime.fromisoformat(goal['created_at'].replace('Z', '+00:00'))
                streak_dates.add(created.date())

            # Calculate current streak (from today backwards)
            today = datetime.utcnow().date()
            current_date = today
            while current_date in streak_dates:
                current_streak += 1
                current_date -= timedelta(days=1)

            # Longest streak is just the count of unique dates (simplified)
            longest_streak = len(streak_dates)

        return GoalStats(
            total_goals=total_goals,
            active_goals=active_goals,
            completed_goals=completed_goals,
            failed_goals=failed_goals,
            completion_rate=completion_rate,
            current_streak=current_streak,
            longest_streak=longest_streak
        )

    except Exception as e:
        logger.error(f"❌ Failed to get goal stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve goal statistics")


# --- Helper Functions ---
def _format_goal_response(goal_data: dict) -> GoalResponse:
    """Format goal data for response"""
    current = goal_data.get('current_value', 0.0)
    target = goal_data.get('target_value', 1.0)
    progress = round((current / target * 100) if target > 0 else 0.0, 2)

    return GoalResponse(
        id=goal_data['id'],
        user_id=goal_data['user_id'],
        title=goal_data['title'],
        description=goal_data.get('description'),
        goal_type=goal_data['goal_type'],
        target_value=goal_data['target_value'],
        current_value=current,
        unit=goal_data.get('unit', 'items'),
        progress_percentage=min(progress, 100.0),
        status=goal_data['status'],
        deadline=goal_data.get('deadline'),
        topic_id=goal_data.get('topic_id'),
        metadata=goal_data.get('metadata', {}),
        created_at=goal_data['created_at'],
        updated_at=goal_data.get('updated_at', goal_data['created_at']),
        completed_at=goal_data.get('completed_at')
    )


async def _update_goal_status(supabase, goal_id: str, status: str):
    """Helper to update goal status"""
    try:
        supabase.table('goals').update({
            'status': status,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', goal_id).execute()
    except Exception as e:
        logger.warning(f"⚠️ Failed to auto-update goal status: {e}")
