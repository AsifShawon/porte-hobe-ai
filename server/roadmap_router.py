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
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID to link roadmap to chat")
    chat_session_id: Optional[str] = Field(default=None, description="Chat session ID for navigation")


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
    user=Depends(get_current_user)
):
    """
    Generate a new personalized learning roadmap based on user goals
    """
    try:
        user_id = user.get("user_id")
        logger.info(f"Generating roadmap for user {user_id}")

        # Apply rate limiting using authenticated user's id (avoid query param dependency)
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        limit_user(user_id)

        supabase = get_supabase_client()

        # Get conversation_id from request (directly passed or from user_context)
        conversation_id = request.conversation_id
        if not conversation_id and request.user_context:
            conversation_id = request.user_context.get("conversation_id")

        # If a roadmap already exists for this user + conversation, return it (idempotent)
        if conversation_id:
            try:
                existing_q = supabase.table("learning_roadmaps").select("*") \
                    .eq("user_id", user_id) \
                    .eq("conversation_id", conversation_id) \
                    .not_.eq("status", "abandoned") \
                    .order("created_at", desc=True) \
                    .limit(1) \
                    .execute()
                if existing_q.data:
                    existing = existing_q.data[0]
                    # Load milestone progress to enrich
                    progress_result = supabase.table("milestone_progress") \
                        .select("*") \
                        .eq("roadmap_id", existing["id"]) \
                        .execute()
                    milestone_progress = {mp["milestone_id"]: mp for mp in progress_result.data}
                    enriched = _enrich_roadmap_with_progress(existing, milestone_progress)
                    logger.info(f"Idempotent return of existing roadmap {existing['id']} for conversation {conversation_id}")
                    return {
                        "status": "existing",
                        "roadmap_id": existing["id"],
                        "roadmap": enriched
                    }
            except Exception as e:
                logger.warning(f"Failed idempotent lookup for conversation_id {conversation_id}: {e}")

        # Generate roadmap using AI (no existing one found)
        roadmap_data = await roadmap_generator.generate_roadmap(
            user_goal=request.user_goal,
            conversation_history=request.conversation_history or [],
            user_context=request.user_context or {},
            domain=request.domain
        )

        # Store in database (supabase initialized earlier)

        # Get chat_session_id; validate against chat_sessions to avoid FK errors
        chat_session_id = request.chat_session_id
        if not chat_session_id and request.user_context:
            chat_session_id = request.user_context.get("chat_session_id")

        # Verify chat_session_id exists; if not, try to find/create one via conversation_id
        if chat_session_id:
            try:
                chat_check = supabase.table("chat_sessions").select("id").eq("id", chat_session_id).single().execute()
                if not chat_check.data:
                    logger.warning(f"chat_session_id '{chat_session_id}' not found; attempting lookup by conversation_id")
                    chat_session_id = None
            except Exception:
                # If validation query fails, be safe and try fallback
                logger.debug("chat_session_id validation query failed; attempting fallback")
                chat_session_id = None
        
        # Fallback: Try to find session by conversation_id
        if not chat_session_id and conversation_id:
            try:
                session_lookup = supabase.table("chat_sessions").select("id").eq(
                    "conversation_id", conversation_id
                ).eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
                if session_lookup.data:
                    chat_session_id = session_lookup.data[0]["id"]
                    logger.info(f"Found chat_session_id '{chat_session_id}' via conversation_id lookup")
            except Exception as e:
                logger.debug(f"conversation_id session lookup failed: {e}")

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
            "chat_session_id": chat_session_id,
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
        user_id = user.get("user_id") if user else None
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
        user_id = user.get("user_id") if user else None
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
        user_id = user.get("user_id") if user else None
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

        # Check for quiz triggers if milestone was just completed
        quiz_trigger = None
        if request.status == "completed":
            # Unlock the next milestone
            await _unlock_next_milestone(user_id, roadmap_id, phase_id, milestone_id)
            quiz_trigger = await _check_quiz_triggers(user_id, roadmap_id, phase_id, milestone_id)

        response = {
            "status": "success",
            "milestone_progress": result.data[0] if result.data else update_data
        }

        if quiz_trigger:
            response["quiz_trigger"] = quiz_trigger

        # Emit a chat progress event if this roadmap is linked to a chat session
        try:
            await _emit_progress_chat_event(
                user_id=user_id,
                roadmap_id=roadmap_id,
                phase_id=phase_id,
                milestone_id=milestone_id,
                status=request.status,
                progress_percentage=response["milestone_progress"].get("progress_percentage", request.progress_percentage),
                notes=request.notes,
            )
        except Exception as e:
            logger.warning(f"Failed to emit chat progress event: {e}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating milestone: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating milestone: {str(e)}")


@router.post("/{roadmap_id}/milestone/{phase_id}/{milestone_id}/start-learning", response_model=Dict[str, Any])
async def start_learning_milestone(
    roadmap_id: str,
    phase_id: str,
    milestone_id: str,
    user=Depends(get_current_user)
):
    """
    Start learning a specific milestone - creates contextual chat prompt and links to session
    
    This endpoint:
    1. Gets the roadmap and milestone details
    2. Generates a human-like contextual prompt for the milestone
    3. Creates or retrieves linked chat session
    4. Updates milestone status to 'in_progress'
    5. Returns chat navigation info
    """
    try:
        user_id = user.get("user_id") if user else None
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        supabase = get_supabase_client()

        # Get roadmap details
        roadmap_result = supabase.table("learning_roadmaps")\
            .select("*")\
            .eq("id", roadmap_id)\
            .eq("user_id", user_id)\
            .execute()

        if not roadmap_result.data:
            raise HTTPException(status_code=404, detail="Roadmap not found")

        roadmap = roadmap_result.data[0]
        roadmap_data = roadmap["roadmap_data"]

        # Find the specific milestone (support both legacy and new schema)
        milestone_info = None
        phase_info = None

        phases = roadmap_data.get("phases") or roadmap_data.get("learning_phases") or []

        def _normalize(s: Optional[str]) -> str:
            return (s or "").strip().lower().replace(" ", "_")

        # First try direct id match
        for phase in phases:
            current_phase_id = phase.get("id") or phase.get("phase_id")
            if current_phase_id == phase_id:
                phase_info = phase
                for milestone in phase.get("milestones", []):
                    current_milestone_id = milestone.get("id") or milestone.get("milestone_id")
                    if current_milestone_id == milestone_id:
                        milestone_info = milestone
                        break
                break

        # Fallback: try normalized title matching and index-based matching
        if not phase_info:
            for idx, phase in enumerate(phases, start=1):
                pid_norm = _normalize(phase.get("id") or phase.get("phase_id"))
                ptitle_norm = _normalize(phase.get("title") or phase.get("phase_name"))
                if phase_id == f"phase_{idx}" or _normalize(phase_id) in {pid_norm, ptitle_norm}:
                    phase_info = phase
                    break

        if phase_info and not milestone_info:
            milestones = phase_info.get("milestones", [])
            for midx, ms in enumerate(milestones, start=1):
                ms_id_norm = _normalize(ms.get("id") or ms.get("milestone_id"))
                ms_title_norm = _normalize(ms.get("title"))
                if milestone_id == f"lesson_{midx}" or milestone_id == f"quiz_{midx}" or _normalize(milestone_id) in {ms_id_norm, ms_title_norm}:
                    milestone_info = ms
                    break

        if not milestone_info:
            # Fallback: use roadmap's current milestone if available
            current_phase = roadmap.get("current_phase_id")
            current_milestone = roadmap.get("current_milestone_id")
            if current_phase and current_milestone:
                for phase in phases:
                    pid = phase.get("id") or phase.get("phase_id")
                    if pid == current_phase:
                        phase_info = phase
                        for ms in phase.get("milestones", []):
                            msid = ms.get("id") or ms.get("milestone_id")
                            if msid == current_milestone:
                                milestone_info = ms
                                break
                        break

        if not milestone_info:
            # Last resort: pick the first lesson milestone
            for phase in phases:
                if phase.get("milestones"):
                    phase_info = phase
                    for ms in phase.get("milestones", []):
                        if (ms.get("type") or "lesson") == "lesson":
                            milestone_info = ms
                            break
                    if milestone_info:
                        break

        if not milestone_info:
            # Provide helpful diagnostics in error
            available = []
            for phase in phases:
                pid = phase.get("id") or phase.get("phase_id")
                for ms in phase.get("milestones", []):
                    available.append({
                        "phase_id": pid,
                        "milestone_id": ms.get("id") or ms.get("milestone_id"),
                        "title": ms.get("title")
                    })
            logger.warning(f"Milestone not found. Requested phase_id={phase_id}, milestone_id={milestone_id}. Available: {available}")
            raise HTTPException(status_code=404, detail="Milestone not found in roadmap")

        # Generate contextual chat prompt
        milestone_title = milestone_info.get("title", "")
        milestone_desc = milestone_info.get("description", "")
        # New schema uses 'title' for phase name; legacy may have 'phase_name'
        phase_name = (phase_info.get("title") or phase_info.get("phase_name") or "") if phase_info else ""
        roadmap_title = roadmap.get("title", "")
        
        # Create human-like prompt based on milestone type
        milestone_type = milestone_info.get("type", "lesson")
        
        if milestone_type == "quiz":
            contextual_prompt = (
                f"I'm working on the '{roadmap_title}' learning path. "
                f"I've reached the quiz: '{milestone_title}' in the {phase_name} phase. "
                f"Can you help me prepare for this quiz? {milestone_desc}"
            )
        else:
            contextual_prompt = (
                f"I'm learning '{roadmap_title}' and I want to start the topic: '{milestone_title}' "
                f"from the {phase_name} phase. {milestone_desc} Can you teach me about this?"
            )

        # Get or create chat session linked to this roadmap
        # Priority: Use roadmap's conversation_id if available (roadmap created from chat)
        session_id = None
        conversation_id = roadmap.get("conversation_id")
        
        if conversation_id:
            # Roadmap was created from a chat - find or create session with that conversation_id
            session_result = supabase.table("chat_sessions")\
                .select("*")\
                .eq("conversation_id", conversation_id)\
                .eq("user_id", user_id)\
                .is_("ended_at", "null")\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
            
            if session_result.data:
                session = session_result.data[0]
                session_id = session["id"]
                logger.info(f"Using existing session {session_id} with conversation_id {conversation_id}")
            else:
                # Session doesn't exist for this conversation_id - create it
                new_session = supabase.table("chat_sessions").insert({
                    "user_id": user_id,
                    "roadmap_id": roadmap_id,
                    "conversation_id": conversation_id,
                    "title": f"Learning: {roadmap_title}",
                    "metadata": {
                        "roadmap_title": roadmap_title,
                        "started_from_milestone": milestone_id
                    }
                }).execute()

                if new_session.data:
                    session = new_session.data[0]
                    session_id = session["id"]
                    logger.info(f"Created new session {session_id} for existing conversation {conversation_id}")
        else:
            # No conversation_id - look for existing session by roadmap_id or create new
            session_result = supabase.table("chat_sessions")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("roadmap_id", roadmap_id)\
                .is_("ended_at", "null")\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()

            if session_result.data:
                session = session_result.data[0]
                session_id = session["id"]
                conversation_id = session["conversation_id"]
                logger.info(f"Using existing session {session_id} for roadmap {roadmap_id}")
            else:
                # Create completely new session
                conversation_id = str(uuid.uuid4())
                new_session = supabase.table("chat_sessions").insert({
                    "user_id": user_id,
                    "roadmap_id": roadmap_id,
                    "conversation_id": conversation_id,
                    "title": f"Learning: {roadmap_title}",
                    "metadata": {
                        "roadmap_title": roadmap_title,
                        "started_from_milestone": milestone_id
                    }
                }).execute()

                if new_session.data:
                    session = new_session.data[0]
                    session_id = session["id"]
                    logger.info(f"Created new session {session_id} with new conversation {conversation_id}")
        
        if not session_id or not conversation_id:
            raise HTTPException(status_code=500, detail="Failed to create or find chat session")

        # Update milestone status to in_progress
        try:
            supabase.table("milestone_progress").upsert({
                "user_id": user_id,
                "roadmap_id": roadmap_id,
                "phase_id": phase_id,
                "milestone_id": milestone_id,
                "milestone_title": milestone_title,
                "milestone_type": milestone_type,
                "status": "in_progress",
                "started_at": datetime.now().isoformat(),
                "progress_percentage": 0.0
            }, on_conflict="user_id,roadmap_id,phase_id,milestone_id").execute()
            
            # Update roadmap's current milestone
            supabase.table("learning_roadmaps").update({
                "current_phase_id": phase_id,
                "current_milestone_id": milestone_id
            }).eq("id", roadmap_id).execute()
            
        except Exception as e:
            logger.warning(f"Failed to update milestone status: {e}")

        return {
            "status": "success",
            "message": "Ready to start learning!",
            "navigation": {
                "session_id": session_id,
                "conversation_id": conversation_id,
                "contextual_prompt": contextual_prompt,
                "chat_url": f"/dashboard/chat?conversation_id={conversation_id}&auto_start=true"
            },
            "milestone": {
                "roadmap_id": roadmap_id,
                "phase_id": phase_id,
                "milestone_id": milestone_id,
                "title": milestone_title,
                "type": milestone_type,
                "description": milestone_desc
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting learning milestone: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error starting milestone: {str(e)}")


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
        user_id = user.get("user_id") if user else None
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
        user_id = user.get("user_id") if user else None
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


async def _unlock_next_milestone(user_id: str, roadmap_id: str, completed_phase_id: str, completed_milestone_id: str):
    """
    Unlock the next milestone after one is completed.
    This handles unlocking within the same phase and across phases.
    """
    try:
        supabase = get_supabase_client()

        # Get the roadmap to understand milestone structure
        roadmap_result = supabase.table("learning_roadmaps")\
            .select("*")\
            .eq("id", roadmap_id)\
            .single()\
            .execute()

        if not roadmap_result.data:
            return

        roadmap = roadmap_result.data
        roadmap_data = roadmap.get("roadmap_data", {})
        phases = roadmap_data.get("phases", [])

        # Find the completed milestone and the next one to unlock
        next_milestone_to_unlock = None
        next_phase_id = None
        found_completed = False

        for phase_idx, phase in enumerate(phases):
            phase_id = phase.get("id")
            milestones = phase.get("milestones", [])

            for milestone_idx, milestone in enumerate(milestones):
                milestone_id = milestone.get("id")

                if found_completed:
                    # This is the next milestone after the completed one
                    next_milestone_to_unlock = milestone
                    next_phase_id = phase_id
                    break

                if phase_id == completed_phase_id and milestone_id == completed_milestone_id:
                    found_completed = True
                    # Check if there's a next milestone in the same phase
                    if milestone_idx + 1 < len(milestones):
                        next_milestone_to_unlock = milestones[milestone_idx + 1]
                        next_phase_id = phase_id
                        break

            if next_milestone_to_unlock:
                break

            # If we found the completed milestone but no next in same phase,
            # continue to next phase
            if found_completed and phase_idx + 1 < len(phases):
                next_phase = phases[phase_idx + 1]
                if next_phase.get("milestones"):
                    next_milestone_to_unlock = next_phase["milestones"][0]
                    next_phase_id = next_phase.get("id")
                    break

        if not next_milestone_to_unlock or not next_phase_id:
            logger.info(f"No next milestone to unlock after {completed_milestone_id}")
            return

        next_milestone_id = next_milestone_to_unlock.get("id")

        # Check current status of next milestone
        progress_check = supabase.table("milestone_progress")\
            .select("status")\
            .eq("user_id", user_id)\
            .eq("roadmap_id", roadmap_id)\
            .eq("milestone_id", next_milestone_id)\
            .execute()

        current_status = progress_check.data[0]["status"] if progress_check.data else "locked"

        # Only unlock if currently locked
        if current_status == "locked":
            supabase.table("milestone_progress")\
                .upsert({
                    "user_id": user_id,
                    "roadmap_id": roadmap_id,
                    "phase_id": next_phase_id,
                    "milestone_id": next_milestone_id,
                    "milestone_title": next_milestone_to_unlock.get("title"),
                    "milestone_type": next_milestone_to_unlock.get("type"),
                    "status": "not_started",
                    "progress_percentage": 0.0
                }, on_conflict="user_id,roadmap_id,phase_id,milestone_id")\
                .execute()

            # Also update the current milestone pointer in the roadmap
            supabase.table("learning_roadmaps").update({
                "current_phase_id": next_phase_id,
                "current_milestone_id": next_milestone_id
            }).eq("id", roadmap_id).execute()

            logger.info(f"Unlocked milestone {next_milestone_id} in phase {next_phase_id}")
        else:
            logger.info(f"Milestone {next_milestone_id} already unlocked (status: {current_status})")

    except Exception as e:
        logger.error(f"Error unlocking next milestone: {e}", exc_info=True)


async def _check_quiz_triggers(user_id: str, roadmap_id: str, completed_phase_id: str, completed_milestone_id: str) -> Optional[Dict[str, Any]]:
    """
    Check if completing this milestone should trigger a quiz offer.
    Returns quiz trigger data if a quiz should be offered, None otherwise.
    """
    try:
        supabase = get_supabase_client()

        # Get the roadmap to understand milestone structure
        roadmap_result = supabase.table("learning_roadmaps")\
            .select("*")\
            .eq("id", roadmap_id)\
            .single()\
            .execute()

        if not roadmap_result.data:
            return None

        roadmap = roadmap_result.data
        roadmap_data = roadmap.get("roadmap_data", {})
        phases = roadmap_data.get("phases", [])

        # Find the phase and milestone that was just completed
        completed_phase = None
        completed_milestone = None
        milestone_order = 0

        for phase in phases:
            if phase["id"] == completed_phase_id:
                completed_phase = phase
                for idx, milestone in enumerate(phase.get("milestones", [])):
                    if milestone["id"] == completed_milestone_id:
                        completed_milestone = milestone
                        milestone_order = idx
                        break
                break

        if not completed_phase or not completed_milestone:
            return None

        # Only trigger quiz if the completed milestone was a lesson
        if completed_milestone.get("type") != "lesson":
            return None

        # Look for the next quiz milestone in the same phase
        next_quiz = None
        for idx, milestone in enumerate(completed_phase.get("milestones", [])):
            if idx > milestone_order and milestone.get("type") == "quiz":
                next_quiz = milestone
                break

        if not next_quiz:
            return None

        # Check if quiz milestone is already completed or in progress
        progress_result = supabase.table("milestone_progress")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("roadmap_id", roadmap_id)\
            .eq("milestone_id", next_quiz["id"])\
            .execute()

        if progress_result.data:
            quiz_status = progress_result.data[0].get("status")
            if quiz_status in ["completed", "in_progress"]:
                return None  # Don't trigger if already started or completed

        # Check if this quiz has prerequisites that aren't met
        # For now, assume quiz is unlocked if previous lesson is completed
        # You can add more sophisticated prerequisite checking here

        # Return quiz trigger data
        return {
            "type": "milestone_quiz",
            "phase_id": completed_phase_id,
            "phase_title": completed_phase.get("title"),
            "milestone_id": next_quiz["id"],
            "milestone_title": next_quiz.get("title"),
            "quiz_difficulty": next_quiz.get("difficulty", "beginner"),
            "topics": next_quiz.get("topics", []),
            "trigger_reason": f"Completed {completed_milestone.get('title')}"
        }

    except Exception as e:
        logger.error(f"Error checking quiz triggers: {e}", exc_info=True)
        return None


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


async def _emit_progress_chat_event(
    user_id: str,
    roadmap_id: str,
    phase_id: str,
    milestone_id: str,
    status: str,
    progress_percentage: float,
    notes: Optional[str] = None,
):
    """Append a system-style chat message reflecting milestone progress if roadmap links to a chat session.

    Tries `learning_roadmaps.chat_session_id` first, then falls back to `conversation_id` → session lookup.
    """
    supabase = get_supabase_client()
    if not supabase:
        return

    # Load roadmap linkage metadata
    roadmap_res = supabase.table("learning_roadmaps").select("id, title, conversation_id, chat_session_id").eq("id", roadmap_id).single().execute()
    if not roadmap_res.data:
        return

    roadmap = roadmap_res.data
    session_id = roadmap.get("chat_session_id")

    # If session_id missing, try to find by conversation_id
    if not session_id and roadmap.get("conversation_id"):
        try:
            sess_q = supabase.table("chat_sessions").select("id").eq("conversation_id", roadmap["conversation_id"]).eq("user_id", user_id).limit(1).execute()
            if sess_q.data:
                session_id = sess_q.data[0]["id"]
        except Exception:
            pass

    if not session_id:
        # No chat link available; skip
        return

    # Compose a concise assistant message
    status_text = {
        "not_started": "set to not started",
        "in_progress": "marked in progress",
        "completed": "marked completed",
    }.get(status, f"updated (status: {status})")

    content = (
        f"Progress update: Milestone `{milestone_id}` {status_text}. "
        f"Roadmap `{roadmap['title']}` progress: {round(progress_percentage or 0, 1)}%."
    )

    metadata = {
        "event": "milestone_update",
        "roadmap_id": roadmap_id,
        "phase_id": phase_id,
        "milestone_id": milestone_id,
        "status": status,
        "progress_percentage": progress_percentage,
        "notes": notes,
    }

    # Insert chat message as assistant final answer with metadata
    supabase.table("chat_messages").insert({
        "session_id": session_id,
        "role": "assistant",
        "content": content,
        "message_type": "final_answer",
        "metadata": metadata,
    }).execute()
