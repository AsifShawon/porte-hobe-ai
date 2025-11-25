"""
Achievement Router
Handles student achievements, badges, milestones, and gamification
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import get_current_user
from config import get_supabase_client

logger = logging.getLogger("achievement_router")

router = APIRouter(prefix="/api/achievements", tags=["achievements"])


class AchievementCategory(str, Enum):
    """Achievement categories"""
    LEARNING = "learning"
    STREAK = "streak"
    MASTERY = "mastery"
    SOCIAL = "social"
    MILESTONE = "milestone"
    CHALLENGE = "challenge"


class AchievementRarity(str, Enum):
    """Achievement rarity levels"""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class AchievementDefinition(BaseModel):
    """Predefined achievement template"""
    id: str
    title: str
    description: str
    category: AchievementCategory
    rarity: AchievementRarity
    icon: str  # Emoji or icon identifier
    points: int  # XP points awarded
    requirement: dict  # Requirements to unlock (e.g., {"topics_completed": 5})
    secret: bool = False  # Hidden until unlocked


class UserAchievement(BaseModel):
    """User's earned achievement"""
    id: str
    user_id: str
    achievement_id: str
    title: str
    description: str
    category: str
    rarity: str
    icon: str
    points: int
    unlocked_at: str
    progress: Optional[float] = 100.0  # Percentage progress towards achievement
    metadata: Optional[dict] = {}


class AchievementProgress(BaseModel):
    """Progress towards an achievement"""
    achievement_id: str
    title: str
    description: str
    category: str
    rarity: str
    icon: str
    points: int
    current_value: float
    target_value: float
    progress_percentage: float
    locked: bool


class AchievementStats(BaseModel):
    """Overall achievement statistics"""
    total_achievements: int
    unlocked_achievements: int
    total_points: int
    level: int
    level_progress: float  # Progress to next level (0-100%)
    next_level_points: int
    rarity_breakdown: Dict[str, int]
    category_breakdown: Dict[str, int]
    recent_achievements: List[UserAchievement]


# Predefined achievement templates
ACHIEVEMENT_TEMPLATES = [
    # Learning Achievements
    {
        "id": "first_steps",
        "title": "First Steps",
        "description": "Complete your first topic",
        "category": "learning",
        "rarity": "common",
        "icon": "🎯",
        "points": 10,
        "requirement": {"topics_completed": 1}
    },
    {
        "id": "quick_learner",
        "title": "Quick Learner",
        "description": "Complete 5 topics",
        "category": "learning",
        "rarity": "uncommon",
        "icon": "🚀",
        "points": 50,
        "requirement": {"topics_completed": 5}
    },
    {
        "id": "knowledge_seeker",
        "title": "Knowledge Seeker",
        "description": "Complete 10 topics",
        "category": "learning",
        "rarity": "rare",
        "icon": "📚",
        "points": 100,
        "requirement": {"topics_completed": 10}
    },
    {
        "id": "master_scholar",
        "title": "Master Scholar",
        "description": "Complete 25 topics",
        "category": "learning",
        "rarity": "epic",
        "icon": "🎓",
        "points": 250,
        "requirement": {"topics_completed": 25}
    },
    {
        "id": "grand_master",
        "title": "Grand Master",
        "description": "Complete 50 topics",
        "category": "learning",
        "rarity": "legendary",
        "icon": "👑",
        "points": 500,
        "requirement": {"topics_completed": 50}
    },

    # Streak Achievements
    {
        "id": "consistency_beginner",
        "title": "Getting Started",
        "description": "Maintain a 3-day learning streak",
        "category": "streak",
        "rarity": "common",
        "icon": "🔥",
        "points": 15,
        "requirement": {"streak_days": 3}
    },
    {
        "id": "week_warrior",
        "title": "Week Warrior",
        "description": "Maintain a 7-day learning streak",
        "category": "streak",
        "rarity": "uncommon",
        "icon": "💪",
        "points": 30,
        "requirement": {"streak_days": 7}
    },
    {
        "id": "month_master",
        "title": "Month Master",
        "description": "Maintain a 30-day learning streak",
        "category": "streak",
        "rarity": "rare",
        "icon": "⚡",
        "points": 150,
        "requirement": {"streak_days": 30}
    },
    {
        "id": "unstoppable",
        "title": "Unstoppable",
        "description": "Maintain a 100-day learning streak",
        "category": "streak",
        "rarity": "legendary",
        "icon": "🌟",
        "points": 1000,
        "requirement": {"streak_days": 100}
    },

    # Mastery Achievements
    {
        "id": "high_achiever",
        "title": "High Achiever",
        "description": "Maintain 80%+ average score",
        "category": "mastery",
        "rarity": "rare",
        "icon": "⭐",
        "points": 100,
        "requirement": {"average_score": 80}
    },
    {
        "id": "perfectionist",
        "title": "Perfectionist",
        "description": "Achieve 100% on 5 topics",
        "category": "mastery",
        "rarity": "epic",
        "icon": "💯",
        "points": 200,
        "requirement": {"perfect_scores": 5}
    },
    {
        "id": "speed_demon",
        "title": "Speed Demon",
        "description": "Complete a topic in under 30 minutes",
        "category": "mastery",
        "rarity": "uncommon",
        "icon": "⚡",
        "points": 50,
        "requirement": {"fast_completion": 30}
    },

    # Challenge Achievements
    {
        "id": "problem_solver",
        "title": "Problem Solver",
        "description": "Complete 10 practice exercises",
        "category": "challenge",
        "rarity": "uncommon",
        "icon": "🧩",
        "points": 40,
        "requirement": {"exercises_completed": 10}
    },
    {
        "id": "challenge_champion",
        "title": "Challenge Champion",
        "description": "Complete 50 practice exercises",
        "category": "challenge",
        "rarity": "rare",
        "icon": "🏆",
        "points": 150,
        "requirement": {"exercises_completed": 50}
    },
    {
        "id": "code_master",
        "title": "Code Master",
        "description": "Complete all programming challenges",
        "category": "challenge",
        "rarity": "legendary",
        "icon": "💻",
        "points": 500,
        "requirement": {"programming_challenges_complete": True}
    },

    # Milestone Achievements
    {
        "id": "early_bird",
        "title": "Early Bird",
        "description": "Complete a session before 8 AM",
        "category": "milestone",
        "rarity": "uncommon",
        "icon": "🌅",
        "points": 25,
        "requirement": {"early_session": True}
    },
    {
        "id": "night_owl",
        "title": "Night Owl",
        "description": "Complete a session after 10 PM",
        "category": "milestone",
        "rarity": "uncommon",
        "icon": "🦉",
        "points": 25,
        "requirement": {"late_session": True}
    },
    {
        "id": "time_traveler",
        "title": "Time Traveler",
        "description": "Study for 100+ hours total",
        "category": "milestone",
        "rarity": "epic",
        "icon": "⏰",
        "points": 300,
        "requirement": {"total_hours": 100}
    },
]


@router.get("/available", response_model=List[AchievementProgress])
async def get_available_achievements(
    user: dict = Depends(get_current_user)
):
    """
    Get all available achievements and user's progress towards them
    """
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        # Get user's unlocked achievements
        unlocked = supabase.table('user_achievements')\
            .select('achievement_id')\
            .eq('user_id', user['user_id'])\
            .execute()

        unlocked_ids = set(a['achievement_id'] for a in unlocked.data)

        # Get user's progress data
        progress_data = await _get_user_progress_data(supabase, user['user_id'])

        # Calculate progress for each achievement
        achievement_progress = []
        for template in ACHIEVEMENT_TEMPLATES:
            is_unlocked = template['id'] in unlocked_ids

            # Calculate progress
            current, target, progress_pct = _calculate_achievement_progress(
                template['requirement'],
                progress_data
            )

            achievement_progress.append(AchievementProgress(
                achievement_id=template['id'],
                title=template['title'],
                description=template['description'],
                category=template['category'],
                rarity=template['rarity'],
                icon=template['icon'],
                points=template['points'],
                current_value=current,
                target_value=target,
                progress_percentage=progress_pct,
                locked=not is_unlocked
            ))

        # Sort: unlocked first, then by progress
        achievement_progress.sort(key=lambda x: (x.locked, -x.progress_percentage))

        return achievement_progress

    except Exception as e:
        logger.error(f"❌ Failed to get available achievements: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve achievements")


@router.get("/unlocked", response_model=List[UserAchievement])
async def get_unlocked_achievements(
    category: Optional[AchievementCategory] = None,
    user: dict = Depends(get_current_user)
):
    """
    Get all unlocked achievements for the user

    - **category**: Optional filter by category
    """
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        query = supabase.table('user_achievements')\
            .select('*')\
            .eq('user_id', user['user_id'])\
            .order('unlocked_at', desc=True)

        if category:
            query = query.eq('category', category.value)

        result = query.execute()

        return [UserAchievement(**a) for a in result.data]

    except Exception as e:
        logger.error(f"❌ Failed to get unlocked achievements: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve unlocked achievements")


@router.post("/check")
async def check_and_unlock_achievements(
    user: dict = Depends(get_current_user)
):
    """
    Check user progress and auto-unlock any earned achievements
    Returns newly unlocked achievements
    """
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        # Get already unlocked achievements
        unlocked = supabase.table('user_achievements')\
            .select('achievement_id')\
            .eq('user_id', user['user_id'])\
            .execute()

        unlocked_ids = set(a['achievement_id'] for a in unlocked.data)

        # Get user's current progress
        progress_data = await _get_user_progress_data(supabase, user['user_id'])

        # Check each achievement
        newly_unlocked = []
        for template in ACHIEVEMENT_TEMPLATES:
            if template['id'] in unlocked_ids:
                continue  # Already unlocked

            # Check if requirements are met
            if _check_achievement_requirements(template['requirement'], progress_data):
                # Unlock achievement
                achievement_data = {
                    'user_id': user['user_id'],
                    'achievement_id': template['id'],
                    'title': template['title'],
                    'description': template['description'],
                    'category': template['category'],
                    'rarity': template['rarity'],
                    'icon': template['icon'],
                    'points': template['points'],
                    'unlocked_at': datetime.utcnow().isoformat(),
                    'metadata': {}
                }

                result = supabase.table('user_achievements').insert(achievement_data).execute()

                if result.data:
                    newly_unlocked.append(UserAchievement(**result.data[0]))
                    logger.info(f"🏆 Unlocked achievement '{template['title']}' for user {user['user_id']}")

        return {
            "newly_unlocked": newly_unlocked,
            "count": len(newly_unlocked)
        }

    except Exception as e:
        logger.error(f"❌ Failed to check achievements: {e}")
        raise HTTPException(status_code=500, detail="Failed to check achievements")


@router.get("/stats", response_model=AchievementStats)
async def get_achievement_stats(
    user: dict = Depends(get_current_user)
):
    """Get overall achievement statistics and gamification data"""
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        # Get all unlocked achievements
        unlocked = supabase.table('user_achievements')\
            .select('*')\
            .eq('user_id', user['user_id'])\
            .execute()

        total_achievements = len(ACHIEVEMENT_TEMPLATES)
        unlocked_count = len(unlocked.data)
        total_points = sum(a['points'] for a in unlocked.data)

        # Calculate level (100 points per level)
        POINTS_PER_LEVEL = 100
        level = total_points // POINTS_PER_LEVEL
        points_in_level = total_points % POINTS_PER_LEVEL
        level_progress = round((points_in_level / POINTS_PER_LEVEL) * 100, 2)
        next_level_points = POINTS_PER_LEVEL - points_in_level

        # Rarity breakdown
        rarity_breakdown = {}
        for rarity in AchievementRarity:
            rarity_breakdown[rarity.value] = sum(
                1 for a in unlocked.data if a['rarity'] == rarity.value
            )

        # Category breakdown
        category_breakdown = {}
        for category in AchievementCategory:
            category_breakdown[category.value] = sum(
                1 for a in unlocked.data if a['category'] == category.value
            )

        # Recent achievements (last 5)
        recent = sorted(
            unlocked.data,
            key=lambda x: x['unlocked_at'],
            reverse=True
        )[:5]

        recent_achievements = [UserAchievement(**a) for a in recent]

        return AchievementStats(
            total_achievements=total_achievements,
            unlocked_achievements=unlocked_count,
            total_points=total_points,
            level=level,
            level_progress=level_progress,
            next_level_points=next_level_points,
            rarity_breakdown=rarity_breakdown,
            category_breakdown=category_breakdown,
            recent_achievements=recent_achievements
        )

    except Exception as e:
        logger.error(f"❌ Failed to get achievement stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve achievement statistics")


@router.get("/leaderboard")
async def get_leaderboard(
    limit: int = 10,
    user: dict = Depends(get_current_user)
):
    """
    Get achievement leaderboard (top users by points)

    Note: This requires a user_stats or leaderboard table
    """
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        # Aggregate points per user
        # Note: This is a simplified version. In production, you'd want a materialized view
        result = supabase.rpc('get_achievement_leaderboard', {
            'limit_count': limit
        }).execute()

        # If RPC doesn't exist, return placeholder
        if not result.data:
            return {
                "leaderboard": [],
                "user_rank": None,
                "message": "Leaderboard feature requires database function setup"
            }

        return {
            "leaderboard": result.data,
            "user_rank": _find_user_rank(result.data, user['user_id'])
        }

    except Exception as e:
        logger.warning(f"⚠️ Leaderboard not available: {e}")
        return {
            "leaderboard": [],
            "user_rank": None,
            "message": "Leaderboard feature not yet implemented"
        }


# --- Helper Functions ---
async def _get_user_progress_data(supabase, user_id: str) -> Dict[str, Any]:
    """Get all relevant user progress data for achievement checking"""
    try:
        # Get progress records
        progress = supabase.table('progress')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()

        # Get chat sessions for streak calculation
        sessions = supabase.table('chat_sessions')\
            .select('created_at')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .execute()

        # Get practice exercises (if table exists)
        try:
            exercises = supabase.table('practice_submissions')\
                .select('*')\
                .eq('user_id', user_id)\
                .execute()
            exercises_data = exercises.data
        except:
            exercises_data = []

        # Calculate metrics
        completed_topics = sum(1 for p in progress.data if p['status'] == 'completed')
        scores = [p['score'] for p in progress.data if p['score'] > 0]
        average_score = sum(scores) / len(scores) if scores else 0.0
        perfect_scores = sum(1 for s in scores if s >= 100)

        # Calculate streak
        unique_days = set()
        for session in sessions.data:
            day = session['created_at'][:10]
            unique_days.add(day)

        # Current streak (consecutive days from today)
        from datetime import datetime, timedelta
        current_streak = 0
        today = datetime.utcnow().date()
        check_date = today
        sorted_days = sorted([datetime.fromisoformat(d).date() for d in unique_days], reverse=True)

        for day in sorted_days:
            if day == check_date:
                current_streak += 1
                check_date -= timedelta(days=1)
            else:
                break

        # Total study time (estimate: 5 min per session)
        total_minutes = len(sessions.data) * 5
        total_hours = total_minutes / 60

        return {
            'topics_completed': completed_topics,
            'average_score': average_score,
            'perfect_scores': perfect_scores,
            'streak_days': current_streak,
            'exercises_completed': len(exercises_data),
            'total_hours': total_hours,
            'total_sessions': len(sessions.data)
        }

    except Exception as e:
        logger.error(f"❌ Error getting progress data: {e}")
        return {}


def _calculate_achievement_progress(requirement: dict, progress_data: dict) -> tuple:
    """
    Calculate current progress towards an achievement
    Returns (current_value, target_value, progress_percentage)
    """
    # Get the first requirement key (achievements have single requirements)
    req_key = list(requirement.keys())[0]
    target_value = requirement[req_key]

    if isinstance(target_value, bool):
        # Boolean requirements
        current_value = 1.0 if progress_data.get(req_key, False) else 0.0
        target = 1.0
    else:
        # Numeric requirements
        current_value = float(progress_data.get(req_key, 0))
        target = float(target_value)

    progress_pct = round((current_value / target * 100) if target > 0 else 0.0, 2)
    return current_value, target, min(progress_pct, 100.0)


def _check_achievement_requirements(requirement: dict, progress_data: dict) -> bool:
    """Check if achievement requirements are met"""
    for key, target in requirement.items():
        current = progress_data.get(key, 0)

        if isinstance(target, bool):
            if not current:
                return False
        else:
            if current < target:
                return False

    return True


def _find_user_rank(leaderboard: List[dict], user_id: str) -> Optional[int]:
    """Find user's rank in leaderboard"""
    for i, entry in enumerate(leaderboard, start=1):
        if entry.get('user_id') == user_id:
            return i
    return None
