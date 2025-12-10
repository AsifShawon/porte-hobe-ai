"""
Topic Router
Manages learning topics, prerequisites, and topic sessions
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
from config import get_supabase_client

logger = logging.getLogger("topic_router")

router = APIRouter(prefix="/api/topics", tags=["topics"])


class TopicResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    difficulty_level: str
    estimated_hours: int
    prerequisites: List[str]
    learning_objectives: List[str]
    is_locked: bool
    progress_percentage: float
    status: str


class TopicDetail(BaseModel):
    id: str
    title: str
    description: str
    category: str
    difficulty_level: str
    estimated_hours: int
    prerequisites: List[str]
    learning_objectives: List[str]
    content_structure: dict
    resources: List[dict]
    is_locked: bool
    user_progress: Optional[dict]


class StartTopicResponse(BaseModel):
    topic_id: str
    session_id: str
    message: str
    next_lesson: Optional[dict]


@router.get("/", response_model=List[TopicResponse])
async def get_all_topics(
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    search: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """
    Get all available topics with user progress
    
    - **category**: Filter by category (math, science, programming, etc.)
    - **difficulty**: Filter by difficulty (beginner, intermediate, advanced)
    - **search**: Search in title and description
    """
    supabase = get_supabase_client()
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Get topics
        query = supabase.table('topics').select('*').eq('is_active', True)
        
        if category:
            query = query.eq('category', category)
        
        if difficulty:
            query = query.eq('difficulty_level', difficulty)
        
        if search:
            query = query.ilike('title', f'%{search}%')
        
        topics_result = query.execute()
        
        # Get user progress for all topics
        progress_result = supabase.table('progress')\
            .select('topic_id, status, completed_lessons, total_lessons')\
            .eq('user_id', user['user_id'])\
            .execute()
        
        progress_map = {p['topic_id']: p for p in progress_result.data}
        
        # Build response
        topics_list = []
        for topic in topics_result.data:
            topic_id = topic['id']
            progress = progress_map.get(topic_id, {})
            
            # Check if topic is locked (prerequisites not met)
            prerequisites = topic.get('prerequisites', [])
            is_locked = False
            
            if prerequisites:
                for prereq_id in prerequisites:
                    prereq_progress = progress_map.get(prereq_id, {})
                    if prereq_progress.get('status') != 'completed':
                        is_locked = True
                        break
            
            # Calculate progress percentage
            completed = progress.get('completed_lessons', 0)
            total = progress.get('total_lessons', 10)
            progress_percentage = round((completed / total * 100) if total > 0 else 0, 2)
            
            topics_list.append(TopicResponse(
                id=topic_id,
                title=topic['title'],
                description=topic['description'],
                category=topic['category'],
                difficulty_level=topic['difficulty_level'],
                estimated_hours=topic.get('estimated_hours', 5),
                prerequisites=prerequisites,
                learning_objectives=topic.get('learning_objectives', []),
                is_locked=is_locked,
                progress_percentage=progress_percentage,
                status=progress.get('status', 'not_started')
            ))
        
        return topics_list
        
    except Exception as e:
        logger.error(f"❌ Failed to get topics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve topics")


@router.get("/{topic_id}", response_model=TopicDetail)
async def get_topic_detail(
    topic_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get detailed information about a specific topic
    """
    supabase = get_supabase_client()
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Get topic
        topic_result = supabase.table('topics')\
            .select('*')\
            .eq('id', topic_id)\
            .single()\
            .execute()
        
        if not topic_result.data:
            raise HTTPException(status_code=404, detail="Topic not found")
        
        topic = topic_result.data
        
        # Get user progress
        progress_result = supabase.table('progress')\
            .select('*')\
            .eq('user_id', user['user_id'])\
            .eq('topic_id', topic_id)\
            .execute()
        
        user_progress = progress_result.data[0] if progress_result.data else None
        
        # Check prerequisites
        prerequisites = topic.get('prerequisites', [])
        is_locked = False
        
        if prerequisites:
            progress_all = supabase.table('progress')\
                .select('topic_id, status')\
                .eq('user_id', user['user_id'])\
                .in_('topic_id', prerequisites)\
                .execute()
            
            progress_map = {p['topic_id']: p for p in progress_all.data}
            
            for prereq_id in prerequisites:
                if prereq_id not in progress_map or progress_map[prereq_id]['status'] != 'completed':
                    is_locked = True
                    break
        
        return TopicDetail(
            id=topic['id'],
            title=topic['title'],
            description=topic['description'],
            category=topic['category'],
            difficulty_level=topic['difficulty_level'],
            estimated_hours=topic.get('estimated_hours', 5),
            prerequisites=prerequisites,
            learning_objectives=topic.get('learning_objectives', []),
            content_structure=topic.get('content_structure', {}),
            resources=topic.get('resources', []),
            is_locked=is_locked,
            user_progress=user_progress
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get topic detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve topic details")


@router.post("/{topic_id}/start", response_model=StartTopicResponse)
async def start_topic(
    topic_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Initialize a learning session for a topic
    Creates progress record and returns first lesson info
    """
    supabase = get_supabase_client()
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Check if topic exists
        topic = supabase.table('topics')\
            .select('*')\
            .eq('id', topic_id)\
            .single()\
            .execute()
        
        if not topic.data:
            raise HTTPException(status_code=404, detail="Topic not found")
        
        # Check prerequisites
        prerequisites = topic.data.get('prerequisites', [])
        if prerequisites:
            progress_all = supabase.table('progress')\
                .select('topic_id, status')\
                .eq('user_id', user['user_id'])\
                .in_('topic_id', prerequisites)\
                .execute()
            
            completed_prereqs = {p['topic_id'] for p in progress_all.data if p['status'] == 'completed'}
            missing_prereqs = set(prerequisites) - completed_prereqs
            
            if missing_prereqs:
                raise HTTPException(
                    status_code=403,
                    detail=f"Prerequisites not met. Complete these topics first: {list(missing_prereqs)}"
                )
        
        # Check existing progress
        existing_progress = supabase.table('progress')\
            .select('*')\
            .eq('user_id', user['user_id'])\
            .eq('topic_id', topic_id)\
            .execute()
        
        if not existing_progress.data:
            # Create new progress
            new_progress = {
                'user_id': user['user_id'],
                'topic_id': topic_id,
                'score': 0.0,
                'completed_lessons': 0,
                'total_lessons': 10,
                'status': 'in_progress'
            }
            supabase.table('progress').insert(new_progress).execute()
            logger.info(f"✅ Created progress for topic {topic_id}")
        else:
            # Update status to in_progress
            supabase.table('progress')\
                .update({'status': 'in_progress', 'last_activity': datetime.utcnow().isoformat()})\
                .eq('id', existing_progress.data[0]['id'])\
                .execute()
        
        # Create chat session
        session = supabase.table('chat_sessions').insert({
            'user_id': user['user_id'],
            'topic_id': topic_id,
            'title': f"Learning {topic.data['title']}",
            'metadata': {
                'started_at': datetime.utcnow().isoformat(),
                'topic_title': topic.data['title'],
                'difficulty': topic.data['difficulty_level']
            }
        }).execute()
        
        session_id = session.data[0]['id']
        
        # Get first lesson from content structure
        content_structure = topic.data.get('content_structure', {})
        lessons = content_structure.get('lessons', [])
        next_lesson = lessons[0] if lessons else {
            'title': 'Introduction',
            'description': f"Let's start learning {topic.data['title']}!",
            'order': 1
        }
        
        return StartTopicResponse(
            topic_id=topic_id,
            session_id=session_id,
            message=f"Started learning {topic.data['title']}! Let's begin.",
            next_lesson=next_lesson
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to start topic: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start topic: {str(e)}")


@router.post("/{topic_id}/complete")
async def complete_topic(
    topic_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Mark a topic as completed
    """
    supabase = get_supabase_client()
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Get progress
        progress = supabase.table('progress')\
            .select('*')\
            .eq('user_id', user['user_id'])\
            .eq('topic_id', topic_id)\
            .execute()
        
        if not progress.data:
            raise HTTPException(status_code=404, detail="No progress found for this topic")
        
        progress_data = progress.data[0]
        
        # Check if at least 80% lessons completed
        completed = progress_data['completed_lessons']
        total = progress_data.get('total_lessons', 10)
        
        if completed / total < 0.8:
            raise HTTPException(
                status_code=400,
                detail=f"Complete at least 80% of lessons to finish this topic ({completed}/{total} completed)"
            )
        
        # Update to completed
        supabase.table('progress').update({
            'status': 'completed',
            'completed_lessons': total,
            'last_activity': datetime.utcnow().isoformat()
        }).eq('id', progress_data['id']).execute()
        
        logger.info(f"✅ Completed topic {topic_id} for user {user['user_id']}")
        
        return {
            "message": "Congratulations! Topic completed successfully! 🎉",
            "topic_id": topic_id,
            "final_score": progress_data['score'],
            "completed_lessons": total
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to complete topic: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete topic")


@router.get("/categories/list")
async def get_categories(
    user: dict = Depends(get_current_user)
):
    """
    Get all available topic categories with counts
    """
    supabase = get_supabase_client()
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Get all topics
        topics = supabase.table('topics')\
            .select('category')\
            .eq('is_active', True)\
            .execute()
        
        # Count by category
        category_counts = {}
        for topic in topics.data:
            cat = topic['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Format response
        categories = [
            {"name": cat, "count": count}
            for cat, count in sorted(category_counts.items())
        ]
        
        return {"categories": categories}
        
    except Exception as e:
        logger.error(f"❌ Failed to get categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve categories")
