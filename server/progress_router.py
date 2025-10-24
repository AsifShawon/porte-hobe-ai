"""
Progress Router
Handles user learning progress tracking and statistics
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
from config import get_supabase_client

logger = logging.getLogger("progress_router")

router = APIRouter(prefix="/api/progress", tags=["progress"])


class ProgressUpdate(BaseModel):
    topic_id: str
    score_delta: float = 0.0
    completed_lessons: int = 0
    metadata: Optional[dict] = None


class ProgressResponse(BaseModel):
    id: str
    topic_id: str
    topic_title: str
    score: float
    completed_lessons: int
    total_lessons: int
    status: str
    last_activity: str
    progress_percentage: float


class OverallStats(BaseModel):
    total_topics: int
    completed_topics: int
    in_progress_topics: int
    average_score: float
    total_time_spent: int  # in minutes
    streak_days: int
    achievements: List[dict]


@router.get("/", response_model=List[ProgressResponse])
async def get_all_progress(
    status: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """
    Get all progress records for the current user
    
    - **status**: Optional filter by status (not_started, in_progress, completed)
    """
    supabase = get_supabase_client()
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Query progress with topic details
        query = supabase.table('progress')\
            .select('*, topics(id, title, category, difficulty_level)')\
            .eq('user_id', user['id'])\
            .order('last_activity', desc=True)
        
        if status:
            query = query.eq('status', status)
        
        result = query.execute()
        
        # Format response
        progress_list = []
        for item in result.data:
            topic = item.get('topics', {})
            total_lessons = item.get('total_lessons', 10)  # Default
            completed = item.get('completed_lessons', 0)
            
            progress_list.append(ProgressResponse(
                id=item['id'],
                topic_id=item['topic_id'],
                topic_title=topic.get('title', 'Unknown Topic'),
                score=item.get('score', 0.0),
                completed_lessons=completed,
                total_lessons=total_lessons,
                status=item.get('status', 'not_started'),
                last_activity=item['last_activity'],
                progress_percentage=round((completed / total_lessons * 100) if total_lessons > 0 else 0, 2)
            ))
        
        return progress_list
        
    except Exception as e:
        logger.error(f"❌ Failed to get progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve progress")


@router.get("/topic/{topic_id}", response_model=ProgressResponse)
async def get_topic_progress(
    topic_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get progress for a specific topic
    """
    supabase = get_supabase_client()
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        result = supabase.table('progress')\
            .select('*, topics(id, title, category, difficulty_level)')\
            .eq('user_id', user['id'])\
            .eq('topic_id', topic_id)\
            .single()\
            .execute()
        
        if not result.data:
            # Create initial progress record
            topic = supabase.table('topics').select('*').eq('id', topic_id).single().execute()
            
            if not topic.data:
                raise HTTPException(status_code=404, detail="Topic not found")
            
            new_progress = {
                'user_id': user['id'],
                'topic_id': topic_id,
                'score': 0.0,
                'completed_lessons': 0,
                'total_lessons': 10,  # Default
                'status': 'not_started'
            }
            
            result = supabase.table('progress').insert(new_progress).execute()
            result = supabase.table('progress')\
                .select('*, topics(id, title, category, difficulty_level)')\
                .eq('user_id', user['id'])\
                .eq('topic_id', topic_id)\
                .single()\
                .execute()
        
        item = result.data
        topic = item.get('topics', {})
        total_lessons = item.get('total_lessons', 10)
        completed = item.get('completed_lessons', 0)
        
        return ProgressResponse(
            id=item['id'],
            topic_id=item['topic_id'],
            topic_title=topic.get('title', 'Unknown Topic'),
            score=item.get('score', 0.0),
            completed_lessons=completed,
            total_lessons=total_lessons,
            status=item.get('status', 'not_started'),
            last_activity=item['last_activity'],
            progress_percentage=round((completed / total_lessons * 100) if total_lessons > 0 else 0, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get topic progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve progress")


@router.post("/update", response_model=ProgressResponse)
async def update_progress(
    update: ProgressUpdate,
    user: dict = Depends(get_current_user)
):
    """
    Update progress for a topic
    
    - **topic_id**: Topic ID to update
    - **score_delta**: Amount to add to current score (can be negative)
    - **completed_lessons**: Number of lessons completed in this update
    - **metadata**: Additional metadata to merge
    """
    supabase = get_supabase_client()
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Get current progress
        current = supabase.table('progress')\
            .select('*')\
            .eq('user_id', user['id'])\
            .eq('topic_id', update.topic_id)\
            .execute()
        
        if not current.data:
            # Create new progress
            new_score = max(0.0, min(100.0, update.score_delta))
            status = 'in_progress' if new_score > 0 else 'not_started'
            
            new_progress = {
                'user_id': user['id'],
                'topic_id': update.topic_id,
                'score': new_score,
                'completed_lessons': update.completed_lessons,
                'total_lessons': 10,
                'status': status,
                'metadata': update.metadata or {}
            }
            
            supabase.table('progress').insert(new_progress).execute()
        else:
            # Update existing progress
            current_data = current.data[0]
            new_score = max(0.0, min(100.0, current_data['score'] + update.score_delta))
            new_completed = current_data['completed_lessons'] + update.completed_lessons
            total = current_data.get('total_lessons', 10)
            
            # Determine status
            if new_completed >= total:
                status = 'completed'
            elif new_completed > 0 or new_score > 0:
                status = 'in_progress'
            else:
                status = 'not_started'
            
            # Merge metadata
            current_meta = current_data.get('metadata', {})
            if update.metadata:
                current_meta.update(update.metadata)
            
            supabase.table('progress').update({
                'score': new_score,
                'completed_lessons': new_completed,
                'status': status,
                'last_activity': datetime.utcnow().isoformat(),
                'metadata': current_meta
            }).eq('id', current_data['id']).execute()
        
        # Return updated progress
        return await get_topic_progress(update.topic_id, user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update progress: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update progress: {str(e)}")


@router.get("/stats", response_model=OverallStats)
async def get_overall_stats(
    user: dict = Depends(get_current_user)
):
    """
    Get overall learning statistics for the user
    """
    supabase = get_supabase_client()
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Get all progress
        progress = supabase.table('progress')\
            .select('*')\
            .eq('user_id', user['id'])\
            .execute()
        
        total_topics = len(progress.data)
        completed_topics = sum(1 for p in progress.data if p['status'] == 'completed')
        in_progress_topics = sum(1 for p in progress.data if p['status'] == 'in_progress')
        
        # Calculate average score
        scores = [p['score'] for p in progress.data if p['score'] > 0]
        average_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        
        # Calculate streak (days with activity in last 30 days)
        streak_days = 0
        if progress.data:
            # Get chat sessions for activity tracking
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            sessions = supabase.table('chat_sessions')\
                .select('created_at')\
                .eq('user_id', user['id'])\
                .gte('created_at', thirty_days_ago)\
                .execute()
            
            # Count unique days
            unique_days = set()
            for session in sessions.data:
                day = session['created_at'][:10]  # YYYY-MM-DD
                unique_days.add(day)
            
            streak_days = len(unique_days)
        
        # Calculate total time (estimate: 5 min per chat session)
        total_sessions = supabase.table('chat_sessions')\
            .select('id', count='exact')\
            .eq('user_id', user['id'])\
            .execute()
        
        total_time_spent = (total_sessions.count if hasattr(total_sessions, 'count') else len(total_sessions.data)) * 5
        
        # Generate achievements
        achievements = []
        
        if completed_topics >= 1:
            achievements.append({
                'title': 'First Steps',
                'description': 'Completed your first topic',
                'icon': '🎯'
            })
        
        if completed_topics >= 5:
            achievements.append({
                'title': 'Quick Learner',
                'description': 'Completed 5 topics',
                'icon': '🚀'
            })
        
        if streak_days >= 7:
            achievements.append({
                'title': 'Week Warrior',
                'description': '7-day learning streak',
                'icon': '🔥'
            })
        
        if average_score >= 80:
            achievements.append({
                'title': 'High Achiever',
                'description': 'Maintained 80%+ average score',
                'icon': '⭐'
            })
        
        return OverallStats(
            total_topics=total_topics,
            completed_topics=completed_topics,
            in_progress_topics=in_progress_topics,
            average_score=average_score,
            total_time_spent=total_time_spent,
            streak_days=streak_days,
            achievements=achievements
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@router.delete("/topic/{topic_id}")
async def reset_topic_progress(
    topic_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Reset progress for a specific topic
    """
    supabase = get_supabase_client()
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        supabase.table('progress')\
            .update({
                'score': 0.0,
                'completed_lessons': 0,
                'status': 'not_started',
                'metadata': {}
            })\
            .eq('user_id', user['id'])\
            .eq('topic_id', topic_id)\
            .execute()
        
        logger.info(f"✅ Reset progress for topic {topic_id}")
        
        return {"message": "Progress reset successfully", "topic_id": topic_id}
        
    except Exception as e:
        logger.error(f"❌ Failed to reset progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset progress")
