import asyncio
import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import json
import uuid

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from agent import TutorAgent
from auth import get_current_user
from rate_limit import limit_user
from config import supabase, get_supabase_client, CORS_ALLOW_ORIGINS
from session_manager import SessionManager
# Updated to use Memori engine instead of embedding_engine
from memori_engine import initialize_memori_engine, get_memori_engine, store_user_memory
from mcp_agents import scraper_agent, file_agent, math_agent, vector_agent
from html_utils import sanitize_html, generate_teaching_html

# Import routers
from file_router import router as file_router
from progress_router import router as progress_router
from topic_router import router as topic_router
from note_router import router as note_router
from goal_router import router as goal_router
from achievement_router import router as achievement_router
from practice_router import router as practice_router
from resource_router import router as resource_router
from quiz_router import router as quiz_router
from roadmap_router import router as roadmap_router

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("FastAPI")

# --- Global Agent Instance ---
tutor_agent: Optional[TutorAgent] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - initialize agent on startup"""
    global tutor_agent
    logger.info("🚀 Starting FastAPI server...")

    # Initialize Memori memory engine first
    try:
        initialize_memori_engine(verbose=False)
        logger.info("✅ Memori engine initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️  Failed to initialize Memori: {e}")
        logger.info("Continuing without Memori (will use fallback)")

    # Initialize the TutorAgent
    try:
        tutor_agent = TutorAgent(enable_memori=True)
        logger.info("✅ TutorAgent initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize TutorAgent: {e}")
        tutor_agent = None

    yield

    logger.info("🛑 Shutting down FastAPI server...")

# --- FastAPI App ---
app = FastAPI(
    title="Porte Hobe AI Tutor API",
    description="AI Tutor API for Math and Programming",
    version="1.0.0",
    lifespan=lifespan
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"❌ Validation Error: {exc.errors()}")
    try:
        body = await request.json()
        logger.error(f"Request Body: {json.dumps(body, indent=2)}")
    except Exception:
        logger.error("Could not read request body")
    
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)},
    )

# --- Include Routers ---
app.include_router(file_router)
app.include_router(progress_router)
app.include_router(topic_router)
app.include_router(note_router)
app.include_router(goal_router)
app.include_router(achievement_router)
app.include_router(practice_router)
app.include_router(resource_router)
app.include_router(quiz_router)
app.include_router(roadmap_router)

# --- Request/Response Models ---
class MessageItem(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[MessageItem]] = []
    request_id: Optional[str] = None  # Optional: frontend can provide its own ID
    conversation_id: Optional[str] = None  # Conversation ID for tracking and linking to roadmaps
    session_id: Optional[str] = None  # Session ID for continuing existing sessions
    topic_id: Optional[str] = None  # Topic context for progress tracking
    attachments: Optional[List[str]] = []  # Upload IDs to include as context
    enable_web_search: bool = False  # Enable web scraping
    enable_math: bool = False  # Enable symbolic math computation
    response_format: str = "text"  # "text" or "html"
    # Optional metadata bag to pass roadmap/topic linkage & other context from frontend
    metadata: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    thinking_content: Optional[str] = None
    type: str = "response"
    request_id: str  # Unique identifier for this request
    timestamp: Optional[str] = None
    response_html: Optional[str] = None  # Sanitized HTML response
    attachments_used: Optional[List[str]] = []  # Which uploads were used
    web_sources: Optional[List[dict]] = []  # URLs scraped
    math_results: Optional[List[dict]] = []  # Math computations

# --- Helper Functions ---
def convert_history_to_langchain(history: List[MessageItem]) -> List[BaseMessage]:
    """Convert frontend message format to LangChain format"""
    langchain_messages = []
    for msg in history:
        if msg.role == "user":
            langchain_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            langchain_messages.append(AIMessage(content=msg.content))
    return langchain_messages

def extract_thinking_content(messages: List[BaseMessage]) -> Optional[str]:
    """Extract thinking content from the agent's reasoning"""
    for msg in reversed(messages):
        if isinstance(msg, (AIMessage,)) and msg.content:
            # Check for <THINK> tags first
            if "<THINK>" in msg.content:
                import re
                match = re.search(r'<THINK>(.*?)</THINK>', msg.content, re.DOTALL)
                if match:
                    return match.group(1).strip()
            
            # If no <THINK> tags, look for thinking patterns in the content
            # This is for the planning phase output that doesn't use <THINK> tags
            content = msg.content.strip()
            if ("NEED_SEARCH:" in content or 
                "SEARCH_QUERY:" in content or 
                "Phase 1:" in content or
                any(keyword in content.lower() for keyword in ["plan:", "thinking", "reasoning", "approach"])):
                return content
    return None

# --- API Endpoints ---
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Porte Hobe AI Tutor API is running!"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "agent_initialized": tutor_agent is not None,
        "version": "1.0.0"
    }

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest, user=Depends(get_current_user)):
    """Main chat endpoint with reliable message persistence via Session Manager."""
    if tutor_agent is None:
        logger.error("❌ TutorAgent not initialized")
        raise HTTPException(status_code=503, detail="AI service is not available. Please try again later.")

    if supabase is None:
        raise HTTPException(status_code=503, detail="Database service is not available.")

    # Rate limit by user
    try:
        limit_user(user["user_id"])  # 20 req/min default
    except HTTPException as e:
        raise e

    async def event_stream():
        request_id = request.request_id or str(uuid.uuid4())
        conversation_id = request.conversation_id or str(uuid.uuid4())
        thinking_buffer = ""
        answer_buffer = ""
        final_metadata: Dict[str, Any] = {}
        session_id = None
        user_message_id = None
        
        # Initialize Session Manager
        session_mgr = SessionManager(supabase)
        
        try:
            # Priority 1: Use session_id if provided (for continuing existing sessions)
            if request.session_id:
                try:
                    # Verify session belongs to user
                    result = supabase.table("chat_sessions").select("*").eq(
                        "id", request.session_id
                    ).eq("user_id", user["user_id"]).single().execute()
                    
                    if result.data and not result.data.get('ended_at'):
                        session = result.data
                        session_id = session["id"]
                        conversation_id = session.get("conversation_id") or conversation_id
                        logger.info(f"♻️ Continuing session: {session_id}")
                    else:
                        # Invalid or ended session, create new
                        logger.warning(f"Session {request.session_id} invalid or ended, creating new")
                        request.session_id = None
                except Exception as e:
                    logger.warning(f"Failed to load session {request.session_id}: {e}")
                    request.session_id = None
            
            # Priority 2: Get or create session by conversation_id/roadmap_id
            if not request.session_id:
                roadmap_id = request.metadata.get("roadmap_id") if hasattr(request, "metadata") and request.metadata else None
                topic_id = request.metadata.get("topic_id") if hasattr(request, "metadata") and request.metadata else None
                
                session = session_mgr.get_or_create_session(
                    user_id=user["user_id"],
                    conversation_id=conversation_id,
                    roadmap_id=roadmap_id,
                    topic_id=topic_id,
                    title=request.message[:50] + "..." if len(request.message) > 50 else request.message
                )
                session_id = session["id"]
                conversation_id = session.get("conversation_id") or conversation_id
            
            # Convert history
            langchain_history = convert_history_to_langchain(request.history)
            
            # Save user message immediately with retry logic
            try:
                user_msg = session_mgr.save_message(
                    session_id=session_id,
                    role="user",
                    content=request.message,
                    message_type="user_message",
                    metadata={
                        "roadmap_id": roadmap_id,
                        "topic_id": topic_id
                    } if roadmap_id or topic_id else None
                )
                user_message_id = user_msg["id"]
                logger.info(f"✅ User message saved: {user_message_id}")
            except Exception as e:
                logger.error(f"❌ CRITICAL: Failed to save user message: {e}")
                # Still continue with streaming, but log the failure

            # Extract roadmap and topic context from session
            roadmap_id = None
            topic_id = request.topic_id if hasattr(request, 'topic_id') and request.topic_id else None

            # Try to get roadmap_id from session metadata
            if session.get("roadmap_id"):
                roadmap_id = session["roadmap_id"]

            # Stream AI response with session context
            async for evt in tutor_agent.stream_phases(
                request.message,
                langchain_history,
                user_id=user.get("user_id"),
                conversation_id=conversation_id,
                roadmap_id=roadmap_id,
                topic_id=topic_id
            ):
                evt_type = evt.get("type")
                
                if evt_type == "thinking_delta":
                    thinking_buffer += evt.get("delta", "")
                    
                elif evt_type == "thinking_complete":
                    thinking_buffer = evt.get("thinking_content", thinking_buffer)
                    
                elif evt_type == "answer_delta":
                    answer_buffer += evt.get("delta", "")
                    
                elif evt_type == "roadmap_trigger":
                    trigger_meta = {k: v for k, v in evt.items() if k not in {"delta"}}
                    final_metadata.setdefault("roadmap_triggers", []).append(trigger_meta)
                    
                    # Save roadmap trigger as separate message
                    try:
                        session_mgr.save_message(
                            session_id=session_id,
                            role="system",
                            content=f"Roadmap generated: {trigger_meta.get('topic', 'Learning Path')}",
                            message_type="roadmap_trigger",
                            metadata=trigger_meta
                        )
                        logger.info(f"✅ Roadmap trigger saved for session {session_id}")
                        
                        # Link roadmap to session if roadmap_id provided
                        if trigger_meta.get("roadmap_id"):
                            session_mgr.link_roadmap_to_session(session_id, trigger_meta["roadmap_id"])
                    except Exception as e:
                        logger.error(f"❌ Failed to save roadmap trigger: {e}")
                        
                elif evt_type == "quiz_trigger":
                    quiz_meta = {k: v for k, v in evt.items() if k not in {"delta"}}
                    final_metadata.setdefault("quiz_triggers", []).append(quiz_meta)
                    
                    # Save quiz trigger
                    try:
                        session_mgr.save_message(
                            session_id=session_id,
                            role="system",
                            content=f"Quiz generated: {quiz_meta.get('title', 'Practice Quiz')}",
                            message_type="quiz_trigger",
                            metadata=quiz_meta
                        )
                        logger.info(f"✅ Quiz trigger saved for session {session_id}")
                    except Exception as e:
                        logger.error(f"❌ Failed to save quiz trigger: {e}")
                        
                elif evt_type == "answer_complete":
                    answer_buffer = evt.get("response", answer_buffer)
                    
                    # Save complete assistant message with thinking
                    try:
                        assistant_msg = session_mgr.save_message(
                            session_id=session_id,
                            role="assistant",
                            content=answer_buffer,
                            message_type="assistant_message",
                            thinking_content=thinking_buffer or None,
                            metadata=final_metadata if final_metadata else None
                        )
                        logger.info(f"✅ Assistant message saved: {assistant_msg['id']}")
                    except Exception as e:
                        logger.error(f"❌ CRITICAL: Failed to save assistant message: {e}")

                # Stream event to client
                base = {
                    "request_id": request_id,
                    "conversation_id": conversation_id,
                    "session_id": session_id,
                    "timestamp": str(asyncio.get_event_loop().time())
                }
                payload = {**base, **evt}
                yield f"data: {json.dumps(payload)}\n\n"
                
        except Exception as e:
            logger.exception("❌ Streaming error")
            err_payload = {
                "type": "error",
                "response": "Streaming failed due to an internal error.",
                "thinking_content": "An exception occurred; please retry.",
                "request_id": request_id,
                "conversation_id": conversation_id,
                "session_id": session_id,
                "timestamp": str(asyncio.get_event_loop().time())
            }
            yield f"data: {json.dumps(err_payload)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "text/event-stream"
    })


class MemoryAddRequest(BaseModel):
    query: str
    response: str
    summary: str | None = None
    request_id: str | None = None

class MemoryAddResponse(BaseModel):
    ok: bool
    item: Dict[str, Any] | None = None
    engine: str | None = None


@app.post("/api/memory/add", response_model=MemoryAddResponse)
async def memory_add(req: MemoryAddRequest, user=Depends(get_current_user)):
    """Store a memory record for the authenticated user using Memori.

    Intended to be called by the frontend after a streaming chat completes.
    Memori will automatically extract entities, facts, and relationships.
    """
    try:
        limit_user(user["user_id"])  # apply rate limit as well

        # Use TutorAgent's Memori integration if available
        if tutor_agent and tutor_agent.memori_engine:
            result = tutor_agent.store_conversation_memory(
                user_id=user["user_id"],
                user_message=req.query,
                assistant_response=req.response,
                metadata={"request_id": req.request_id} if req.request_id else None
            )
            return {"ok": True, "item": result, "engine": "memori"}
        else:
            # Fallback: basic storage without Memori
            logger.warning("Memori not available, storing basic memory")
            return {
                "ok": True,
                "item": {
                    "user_id": user["user_id"],
                    "query": req.query,
                    "response": req.response[:400]
                },
                "engine": "fallback"
            }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("/api/memory/add failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/simple", response_model=ChatResponse)
async def chat_simple_endpoint(request: ChatRequest, user=Depends(get_current_user)) -> ChatResponse:
    """Enhanced chat endpoint with MCP agent integration"""
    
    if tutor_agent is None:
        logger.error("❌ TutorAgent not initialized")
        raise HTTPException(
            status_code=503, 
            detail="AI service is not available. Please try again later."
        )
    
    try:
        # Rate limit
        limit_user(user["user_id"])  
        # Generate unique request ID
        request_id = request.request_id or str(uuid.uuid4())
        timestamp = str(asyncio.get_event_loop().time())
        
        logger.info(f"📝 Received message [ID: {request_id[:8]}...]: {request.message[:50]}...")
        
        # --- Phase 1: Gather context from attachments ---
        attachments_context = []
        attachments_used = []
        
        if request.attachments:
            logger.info(f"📎 Processing {len(request.attachments)} attachments...")
            supabase_client = get_supabase_client()
            
            for upload_id in request.attachments:
                try:
                    # Get upload from database
                    result = supabase_client.table('uploads')\
                        .select('*')\
                        .eq('id', upload_id)\
                        .eq('user_id', user['user_id'])\
                        .single()\
                        .execute()
                    
                    if result.data:
                        upload = result.data
                        # Add extracted text to context
                        attachments_context.append({
                            'filename': upload['filename'],
                            'text': upload['extracted_text'][:2000],  # Limit length
                            'summary': upload.get('summary', '')
                        })
                        attachments_used.append(upload_id)
                        logger.info(f"✅ Loaded attachment: {upload['filename']}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to load attachment {upload_id}: {e}")
        
        # --- Phase 2: Web search if enabled ---
        web_sources = []
        web_context = ""
        
        if request.enable_web_search:
            logger.info("🌐 Web search enabled, looking for URLs...")
            # Extract URLs from message
            import re
            urls = re.findall(r'https?://[^\s]+', request.message)
            
            if urls:
                for url in urls[:3]:  # Limit to 3 URLs
                    try:
                        content = await scraper_agent.scrape_url(url)
                        web_sources.append({
                            'url': url,
                            'title': content.get('title', 'Unknown'),
                            'text_length': len(content.get('text', ''))
                        })
                        web_context += f"\n\n--- Content from {url} ---\n{content.get('text', '')[:1500]}"
                        logger.info(f"✅ Scraped: {url}")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to scrape {url}: {e}")
        
        # --- Phase 3: Math computation if enabled ---
        math_results = []
        
        if request.enable_math:
            logger.info("🔢 Math computation enabled...")
            # Look for equations or expressions
            import re
            
            # Check for "solve" or "simplify" commands
            if "solve" in request.message.lower():
                # Extract equation pattern: "solve x^2 + 2x + 1 = 0"
                match = re.search(r'solve\s+(.+?)(?:\s|$)', request.message, re.IGNORECASE)
                if match:
                    equation = match.group(1).strip()
                    try:
                        result = math_agent.solve_equation(equation)
                        math_results.append({
                            'operation': 'solve',
                            'input': equation,
                            'result': result
                        })
                        logger.info(f"✅ Solved equation: {equation}")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to solve {equation}: {e}")
            
            if "simplify" in request.message.lower():
                match = re.search(r'simplify\s+(.+?)(?:\s|$)', request.message, re.IGNORECASE)
                if match:
                    expression = match.group(1).strip()
                    try:
                        result = math_agent.simplify_expression(expression)
                        math_results.append({
                            'operation': 'simplify',
                            'input': expression,
                            'result': result
                        })
                        logger.info(f"✅ Simplified expression: {expression}")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to simplify {expression}: {e}")
        
        # --- Phase 4: Build enhanced prompt ---
        enhanced_message = request.message
        
        if attachments_context:
            attachment_text = "\n\n--- Attached Files Context ---\n"
            for att in attachments_context:
                attachment_text += f"\n**{att['filename']}**:\n{att['text']}\n"
            enhanced_message = attachment_text + "\n\n" + enhanced_message
        
        if web_context:
            enhanced_message = enhanced_message + web_context
        
        if math_results:
            math_text = "\n\n--- Math Results ---\n"
            for result in math_results:
                math_text += f"{result['operation'].capitalize()} '{result['input']}': {result['result']}\n"
            enhanced_message = enhanced_message + math_text
        
        # Convert frontend history to LangChain format
        langchain_history = convert_history_to_langchain(request.history)
        
        # Persist user message in chat_history (best-effort)
        try:
            if supabase is not None:
                supabase.table("chat_history").insert({
                    "user_id": user["user_id"],
                    "conversation_id": None,
                    "role": "user",
                    "message": request.message,
                }).execute()
        except Exception:
            logger.debug("chat_history insert (user) failed", exc_info=True)
        
        # --- Phase 5: Process through LLM agent ---
        messages = langchain_history + [HumanMessage(content=enhanced_message)]
        
        # Run the agent and collect the final state
        final_state = await tutor_agent.graph.ainvoke({"messages": messages})
        
        # Extract the final answer
        final_answer = final_state.get("final_answer", "I apologize, but I couldn't process your request right now.")
        
        # Extract thinking content from the messages
        thinking_content = extract_thinking_content(final_state.get("messages", []))
        
        # --- Phase 6: Generate HTML response if requested ---
        response_html = None
        if request.response_format == "html":
            # Determine content type based on message
            content_type = "explanation"
            if "example" in request.message.lower():
                content_type = "example"
            elif "exercise" in request.message.lower() or "practice" in request.message.lower():
                content_type = "exercise"
            
            response_html = generate_teaching_html(
                content=final_answer,
                content_type=content_type,
                title=request.topic_id or "Lesson"
            )
            response_html = sanitize_html(response_html)

        # --- Phase 7: Update progress if topic is specified ---
        if request.topic_id:
            try:
                supabase_client = get_supabase_client()
                # Update progress
                supabase_client.table('progress').update({
                    'last_activity': timestamp
                }).eq('user_id', user['user_id']).eq('topic_id', request.topic_id).execute()
                logger.info(f"✅ Updated progress for topic {request.topic_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to update progress: {e}")

        # Persist assistant reply to chat_history (best-effort)
        try:
            if supabase is not None:
                supabase.table("chat_history").insert({
                    "user_id": user["user_id"],
                    "conversation_id": None,
                    "role": "assistant",
                    "message": final_answer,
                }).execute()
        except Exception:
            logger.debug("chat_history insert (assistant) failed", exc_info=True)

        # Create a small summary and store in user_memory (backend-only embeddings)
        try:
            summary = (thinking_content or "")[:400]  # simple placeholder summary
            store_user_memory(
                user_id=user["user_id"],
                query=request.message,
                response=final_answer,
                summary=summary or final_answer[:400],
                metadata={"request_id": request_id},
            )
        except Exception:
            logger.debug("user_memory store failed", exc_info=True)
        
        logger.info(f"✅ Successfully processed request [ID: {request_id[:8]}...]")
        
        return ChatResponse(
            response=final_answer,
            thinking_content=thinking_content,
            type="complete",
            request_id=request_id,
            timestamp=timestamp,
            response_html=response_html,
            attachments_used=attachments_used,
            web_sources=web_sources,
            math_results=math_results
        )
        
    except Exception as e:
        logger.exception(f"❌ Error processing chat request: {e}")
        
        # Return a fallback response
        return ChatResponse(
            response="I'm experiencing some technical difficulties right now. Please try asking your question again, or rephrase it in a different way.",
            thinking_content="The system encountered an error while processing the request. This could be due to model availability or network issues.",
            type="error",
            request_id=request.request_id or str(uuid.uuid4()),
            timestamp=str(asyncio.get_event_loop().time()),
            response_html=None,
            attachments_used=[],
            web_sources=[],
            math_results=[]
        )

@app.get("/api/chat/history")
async def get_chat_history(
    user=Depends(get_current_user),
    limit: int = 50,
    conversation_id: Optional[str] = None
):
    """Get chat history from unified chat_sessions/chat_messages tables"""
    try:
        if not supabase:
            return {"messages": []}
        
        session_mgr = SessionManager(supabase)
        
        # Get all sessions for user (most recent first)
        sessions_query = supabase.table("chat_sessions")\
            .select("id, conversation_id, title, created_at, ended_at, roadmap_id")\
            .eq("user_id", user["user_id"])\
            .order("created_at", desc=True)
        
        if conversation_id:
            sessions_query = sessions_query.eq("conversation_id", conversation_id)
        
        sessions = sessions_query.limit(limit).execute().data or []
        
        # For each session, get messages and format for frontend
        result = []
        for session in sessions:
            messages = session_mgr.get_session_messages(
                session_id=session["id"],
                include_thinking=False
            )
            
            # Format for frontend (legacy compatible format)
            for msg in messages:
                # Skip system messages (roadmap/quiz triggers) unless they have useful content
                if msg.get("role") == "system" and msg.get("message_type") in ["roadmap_trigger", "quiz_trigger"]:
                    continue
                    
                result.append({
                    "id": msg["id"],
                    "user_id": user["user_id"],
                    "conversation_id": session["conversation_id"],
                    "session_id": session["id"],
                    "roadmap_id": session.get("roadmap_id"),  # Include roadmap_id for history restoration
                    "role": msg["role"],
                    "message": msg["content"],
                    "created_at": msg["created_at"],
                    "message_type": msg.get("message_type"),
                    "thinking_content": msg.get("thinking_content")
                })
        
        # Reverse to get chronological order (oldest first)
        result.reverse()
        
        return {"messages": result}
        
    except Exception as e:
        logger.exception("Failed to fetch chat history")
        raise HTTPException(status_code=500, detail=str(e))

class SaveMessageRequest(BaseModel):
    role: str
    message: str
    conversation_id: Optional[str] = None
    thinking_content: Optional[str] = None
    message_type: Optional[str] = None  # user_message / assistant_message / system / roadmap_trigger
    metadata: Optional[Dict[str, Any]] = None

@app.post("/api/chat/save-message")
async def save_message(
    request: SaveMessageRequest,
    user=Depends(get_current_user)
):
    """Save a chat message to history"""
    try:
        if not supabase:
            raise HTTPException(status_code=500, detail="Database not configured")
        
        # Insert message into chat_history
        # Only use columns that exist in the legacy chat_history table
        # (id, user_id, conversation_id, role, message, created_at)
        result = supabase.table("chat_history").insert({
            "user_id": user["user_id"],
            "conversation_id": request.conversation_id,
            "role": request.role,
            "message": request.message,
        }).execute()
        
        logger.info(f"✅ Saved {request.role} message to chat history")
        
        return {"message": "Message saved successfully"}
        
    except Exception as e:
        logger.exception("Failed to save message")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/chat/history/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user=Depends(get_current_user)
):
    """Delete all messages in a conversation"""
    try:
        if not supabase:
            raise HTTPException(status_code=500, detail="Database not configured")
        
        # Delete all messages with this conversation_id for this user
        result = supabase.table("chat_history")\
            .delete()\
            .eq("user_id", user["user_id"])\
            .eq("conversation_id", conversation_id)\
            .execute()
        
        logger.info(f"✅ Deleted conversation {conversation_id}")
        
        return {"message": "Conversation deleted successfully", "conversation_id": conversation_id}
        
    except Exception as e:
        logger.exception("Failed to delete conversation")
        raise HTTPException(status_code=500, detail=str(e))

class DeleteMessagesRequest(BaseModel):
    messageIds: List[Any]  # Accept any type of ID (string, int, UUID)

@app.post("/api/chat/history/delete-messages")
async def delete_messages(
    request: DeleteMessagesRequest,
    user=Depends(get_current_user)
):
    """Delete specific messages by their IDs"""
    try:
        if not supabase:
            raise HTTPException(status_code=500, detail="Database not configured")
        
        if not request.messageIds:
            return {"message": "No messages to delete", "deleted_count": 0}
        
        logger.info(f"🗑️ Attempting to delete {len(request.messageIds)} messages")
        
        # Delete messages by IDs for this user only
        # Messages come from chat_messages table (UUID ids), so we need to:
        # 1. Find sessions that belong to this user
        # 2. Delete messages from those sessions
        deleted_count = 0
        for message_id in request.messageIds:
            try:
                # Get the message's session to verify ownership
                msg_query = supabase.table("chat_messages")\
                    .select("id, session_id")\
                    .eq("id", str(message_id))\
                    .execute()
                
                if not msg_query.data:
                    logger.debug(f"Message {message_id} not found in chat_messages")
                    continue
                
                session_id = msg_query.data[0]["session_id"]
                
                # Verify the session belongs to this user
                session_query = supabase.table("chat_sessions")\
                    .select("id")\
                    .eq("id", session_id)\
                    .eq("user_id", user["user_id"])\
                    .execute()
                
                if not session_query.data:
                    logger.warning(f"Session {session_id} not owned by user, skipping message {message_id}")
                    continue
                
                # Delete the message
                result = supabase.table("chat_messages")\
                    .delete()\
                    .eq("id", str(message_id))\
                    .execute()
                deleted_count += 1
                logger.debug(f"Deleted message {message_id}")
            except Exception as e:
                logger.warning(f"Failed to delete message {message_id}: {e}")
        
        logger.info(f"✅ Deleted {deleted_count} messages")
        
        return {"message": f"Successfully deleted {deleted_count} messages", "deleted_count": deleted_count}
        
    except Exception as e:
        logger.exception("Failed to delete messages")
        raise HTTPException(status_code=500, detail=str(e))

# --- Lightweight SSE for chat events (progress updates, new messages) ---
@app.get("/api/chat/events")
async def chat_events(
    request: Request,
    session_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    since: Optional[str] = None,
    user=Depends(get_current_user)
):
    """Server-Sent Events stream for a user's chat session.

    Connect with either `session_id` or `conversation_id` (legacy linkage).
    Emits newly inserted `chat_messages` rows as events.
    """
    supabase_client = get_supabase_client()
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not configured")

    # Resolve session_id from conversation_id if needed
    resolved_session_id = session_id
    if not resolved_session_id and conversation_id:
        try:
            sess = supabase_client.table("chat_sessions").select("id").eq("conversation_id", conversation_id).eq("user_id", user["user_id"]).limit(1).execute()
            if sess.data:
                resolved_session_id = sess.data[0]["id"]
        except Exception:
            logger.debug("Failed to resolve session by conversation_id", exc_info=True)

    if not resolved_session_id:
        raise HTTPException(status_code=400, detail="Missing session linkage (session_id or conversation_id)")

    # Track last seen time
    import time
    last_seen = since or datetime.utcnow().isoformat()

    async def sse_loop():
        try:
            while True:
                # Client disconnect check
                if await request.is_disconnected():
                    break

                # Fetch new messages for this session after last_seen
                try:
                    res = supabase_client.table("chat_messages")\
                        .select("id, role, content, thinking_content, message_type, metadata, created_at")\
                        .eq("session_id", resolved_session_id)\
                        .gt("created_at", last_seen)\
                        .order("created_at", desc=False)\
                        .limit(50)\
                        .execute()

                    for row in res.data or []:
                        last_seen = row["created_at"]
                        payload = {
                            "type": "chat_message",
                            "session_id": resolved_session_id,
                            "data": row,
                        }
                        yield f"data: {json.dumps(payload)}\n\n"
                except Exception:
                    logger.debug("Polling chat_messages failed", exc_info=True)

                # Sleep briefly to avoid hammering DB
                await asyncio.sleep(1.0)
        except Exception:
            logger.debug("SSE loop error", exc_info=True)

    return StreamingResponse(sse_loop(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "text/event-stream"
    })

# --- Run Server ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

