"""
Roadmap API Router
Endpoints for managing learning roadmaps
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
from roadmap_agent import RoadmapGeneratorAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/roadmaps", tags=["roadmaps"])

# Initialize the roadmap generator
roadmap_generator = RoadmapGeneratorAgent()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class GenerateRoadmapRequest(BaseModel):
    user_goal: str = Field(..., description="User's learning objective")
    domain: str = Field(default="general", description="Learning domain (programming, math, general)")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(default=None, description="Recent conversation")
    user_context: Optional[Dict[str, Any]] = Field(default=None, description="User context (level, preferences)")


class UpdateMilestoneRequest(BaseModel):
    status: str = Field(..., description="Milestone status (not_started, in_progress, completed)")
    progress_percentage: float = Field(default=0.0, description="Progress percentage")
    notes: Optional[str] = Field(None, description="User notes")


class AdaptRoadmapRequest(BaseModel):
    performance_data: Dict[str, Any] = Field(..., description="Quiz scores and completion data")
    user_struggles: List[str] = Field(default=[], description="Topics user is struggling with")
    user_strengths: List[str] = Field(default=[], description="Topics user excels at")


class RoadmapResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    domain: str
    roadmap_data: Dict[str, Any]
    total_milestones: int
    completed_milestones: int
    progress_percentage: float
    current_phase_id: Optional[str]
    current_milestone_id: Optional[str]
    status: str
    conversation_id: Optional[str]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/generate", response_model=Dict[str, Any])
async def generate_roadmap(
    request: GenerateRoadmapRequest,
    user=Depends(get_current_user),
    _limit=Depends(limit_user)
):
    """
    Generate a new personalized learning roadmap based on user goals
    """
    try:
        user_id = user.get("sub")
        logger.info(f"Generating roadmap for user {user_id}")

        # Generate roadmap using AI
        roadmap_data = await roadmap_generator.generate_roadmap(
            user_goal=request.user_goal,
            conversation_history=request.conversation_history or [],
            user_context=request.user_context or {},
            domain=request.domain
        )

        # Store in database
        supabase = get_supabase_client()

        # Get conversation_id if available from context
        conversation_id = request.user_context.get("conversation_id")

        roadmap_record = {
            "user_id": user_id,
            "title": roadmap_data.get("title"),
            "description": roadmap_data.get("description"),
            "domain": request.domain,
            "roadmap_data": roadmap_data,
            "total_milestones": roadmap_data.get("total_milestones", 0),
            "completed_milestones": 0,
            "progress_percentage": 0.0,
            "current_phase_id": roadmap_data["phases"][0]["id"] if roadmap_data.get("phases") else None,
            "current_milestone_id": roadmap_data["phases"][0]["milestones"][0]["id"] if roadmap_data.get("phases") and roadmap_data["phases"][0].get("milestones") else None,
            "status": "active",
            "conversation_id": conversation_id,
            "metadata": {"user_goal": request.user_goal}
        }

        result = supabase.table("learning_roadmaps").insert(roadmap_record).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create roadmap")

        created_roadmap = result.data[0]

        # Create initial milestone progress records
        await _initialize_milestone_progress(user_id, created_roadmap["id"], roadmap_data)

        logger.info(f"Roadmap created successfully: {created_roadmap['id']}")

        return {
            "status": "success",
            "roadmap_id": created_roadmap["id"],
            "roadmap": created_roadmap
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating roadmap: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating roadmap: {str(e)}")


@router.get("/", response_model=Dict[str, Any])
async def get_user_roadmaps(
    status: Optional[str] = None,
    domain: Optional[str] = None,
    limit: int = 10,
    user=Depends(get_current_user)
):
    """
    Get all roadmaps for the current user with optional filters
    """
    try:
        user_id = user.get("sub") if user else None
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        supabase = get_supabase_client()

        # Build query
        query = supabase.table("learning_roadmaps").select("*").eq("user_id", user_id)

        if status:
            query = query.eq("status", status)

        if domain:
            query = query.eq("domain", domain)

        query = query.order("created_at", desc=True).limit(limit)

        result = query.execute()

        return {
            "roadmaps": result.data,
            "count": len(result.data)
        }

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching roadmaps: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching roadmaps: {str(e)}")


@router.get("/{roadmap_id}", response_model=Dict[str, Any])
async def get_roadmap(
    roadmap_id: str,
    user=Depends(get_current_user)
):
    """
    Get a specific roadmap with progress details
    """
    try:
        user_id = user.get("sub") if user else None
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        supabase = get_supabase_client()

        # Get roadmap
        roadmap_result = supabase.table("learning_roadmaps")\
            .select("*")\
            .eq("id", roadmap_id)\
            .eq("user_id", user_id)\
            .execute()

        if not roadmap_result.data:
            raise HTTPException(status_code=404, detail="Roadmap not found")

        roadmap = roadmap_result.data[0]

        # Get milestone progress
        progress_result = supabase.table("milestone_progress")\
            .select("*")\
            .eq("roadmap_id", roadmap_id)\
            .execute()

        milestone_progress = {mp["milestone_id"]: mp for mp in progress_result.data}

        # Enrich roadmap with progress data
        enriched_roadmap = _enrich_roadmap_with_progress(roadmap, milestone_progress)

        return {
            "roadmap": enriched_roadmap,
            "milestone_progress": progress_result.data
        }

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching roadmap: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching roadmap: {str(e)}")


@router.put("/{roadmap_id}/milestone/{phase_id}/{milestone_id}", response_model=Dict[str, Any])
async def update_milestone_progress(
    roadmap_id: str,
    phase_id: str,
    milestone_id: str,
    request: UpdateMilestoneRequest,
    user=Depends(get_current_user)
):
    """
    Update progress on a specific milestone
    """
    try:
        user_id = user.get("sub") if user else None
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        supabase = get_supabase_client()

        # Update or create milestone progress
        update_data = {
            "user_id": user_id,
            "roadmap_id": roadmap_id,
            "phase_id": phase_id,
            "milestone_id": milestone_id,
            "status": request.status,
            "progress_percentage": request.progress_percentage,
            "notes": request.notes
        }

        if request.status == "in_progress" and not update_data.get("started_at"):
            update_data["started_at"] = datetime.now().isoformat()

        if request.status == "completed":
            update_data["completed_at"] = datetime.now().isoformat()
            update_data["progress_percentage"] = 100.0

        # Upsert milestone progress
        result = supabase.table("milestone_progress")\
            .upsert(update_data, on_conflict="user_id,roadmap_id,phase_id,milestone_id")\
            .execute()

        # Recalculate overall roadmap progress
        await _recalculate_roadmap_progress(roadmap_id)

        return {
            "status": "success",
            "milestone_progress": result.data[0] if result.data else update_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating milestone: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating milestone: {str(e)}")


@router.post("/{roadmap_id}/adapt", response_model=Dict[str, Any])
async def adapt_roadmap(
    roadmap_id: str,
    request: AdaptRoadmapRequest,
    user=Depends(get_current_user)
):
    """
    Adapt roadmap based on user performance (AI-powered)
    """
    try:
        user_id = user.get("sub") if user else None
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        supabase = get_supabase_client()

        # Get current roadmap
        roadmap_result = supabase.table("learning_roadmaps")\
            .select("*")\
            .eq("id", roadmap_id)\
            .eq("user_id", user_id)\
            .execute()

        if not roadmap_result.data:
            raise HTTPException(status_code=404, detail="Roadmap not found")

        current_roadmap = roadmap_result.data[0]

        # Use AI to adapt roadmap
        adapted_roadmap_data = await roadmap_generator.adapt_roadmap(
            current_roadmap=current_roadmap["roadmap_data"],
            performance_data=request.performance_data,
            user_struggles=request.user_struggles,
            user_strengths=request.user_strengths
        )

        # Update roadmap in database
        update_data = {
            "roadmap_data": adapted_roadmap_data,
            "total_milestones": adapted_roadmap_data.get("total_milestones", current_roadmap["total_milestones"]),
            "updated_at": datetime.now().isoformat()
        }

        result = supabase.table("learning_roadmaps")\
            .update(update_data)\
            .eq("id", roadmap_id)\
            .execute()

        logger.info(f"Roadmap {roadmap_id} adapted successfully")

        return {
            "status": "success",
            "message": "Roadmap adapted based on performance",
            "roadmap": result.data[0] if result.data else None
        }

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adapting roadmap: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error adapting roadmap: {str(e)}")


@router.delete("/{roadmap_id}", response_model=Dict[str, str])
async def delete_roadmap(
    roadmap_id: str,
    user=Depends(get_current_user)
):
    """
    Delete a roadmap (soft delete by setting status to 'abandoned')
    """
    try:
        user_id = user.get("sub") if user else None
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        supabase = get_supabase_client()

        result = supabase.table("learning_roadmaps")\
            .update({"status": "abandoned"})\
            .eq("id", roadmap_id)\
            .eq("user_id", user_id)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Roadmap not found")

        return {"status": "success", "message": "Roadmap deleted"}

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting roadmap: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting roadmap: {str(e)}")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _initialize_milestone_progress(user_id: str, roadmap_id: str, roadmap_data: Dict):
    """Initialize milestone progress records for all milestones in the roadmap"""
    try:
        supabase = get_supabase_client()
        progress_records = []

        for phase in roadmap_data.get("phases", []):
            for milestone in phase.get("milestones", []):
                progress_records.append({
                    "user_id": user_id,
                    "roadmap_id": roadmap_id,
                    "phase_id": phase["id"],
                    "milestone_id": milestone["id"],
                    "milestone_title": milestone.get("title"),
                    "milestone_type": milestone.get("type"),
                    "status": milestone.get("status", "not_started"),
                    "progress_percentage": 0.0
                })

        if progress_records:
            supabase.table("milestone_progress").insert(progress_records).execute()

        logger.info(f"Initialized {len(progress_records)} milestone progress records")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing milestone progress: {e}")
        # Non-fatal, continue


async def _recalculate_roadmap_progress(roadmap_id: str):
    """Recalculate overall roadmap progress based on completed milestones"""
    try:
        supabase = get_supabase_client()

        # Get all milestone progress
        progress_result = supabase.table("milestone_progress")\
            .select("status")\
            .eq("roadmap_id", roadmap_id)\
            .execute()

        total_milestones = len(progress_result.data)
        completed_milestones = sum(1 for mp in progress_result.data if mp["status"] == "completed")

        progress_percentage = (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0.0

        # Update roadmap
        update_data = {
            "completed_milestones": completed_milestones,
            "progress_percentage": progress_percentage
        }

        # Check if all milestones completed
        if completed_milestones == total_milestones and total_milestones > 0:
            update_data["status"] = "completed"
            update_data["completed_at"] = datetime.now().isoformat()

        supabase.table("learning_roadmaps")\
            .update(update_data)\
            .eq("id", roadmap_id)\
            .execute()

        logger.info(f"Roadmap progress updated: {completed_milestones}/{total_milestones} ({progress_percentage:.1f}%)")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recalculating progress: {e}")


def _enrich_roadmap_with_progress(roadmap: Dict, milestone_progress: Dict) -> Dict:
    """Enrich roadmap data with current progress information"""
    enriched = roadmap.copy()

    # Update milestone statuses from progress records
    for phase in enriched.get("roadmap_data", {}).get("phases", []):
        for milestone in phase.get("milestones", []):
            milestone_id = milestone["id"]
            if milestone_id in milestone_progress:
                progress = milestone_progress[milestone_id]
                milestone["status"] = progress["status"]
                milestone["progress"] = progress.get("progress_percentage", 0.0)
                milestone["started_at"] = progress.get("started_at")
                milestone["completed_at"] = progress.get("completed_at")

    return enriched
