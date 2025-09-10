import asyncio
import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import uuid

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from agent import TutorAgent

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
    
    # Initialize the TutorAgent
    try:
        tutor_agent = TutorAgent()
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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request/Response Models ---
class MessageItem(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[MessageItem]] = []
    request_id: Optional[str] = None  # Optional: frontend can provide its own ID

class ChatResponse(BaseModel):
    response: str
    thinking_content: Optional[str] = None
    type: str = "response"
    request_id: str  # Unique identifier for this request
    timestamp: Optional[str] = None

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
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint streaming thinking tokens first then answer tokens."""
    if tutor_agent is None:
        logger.error("❌ TutorAgent not initialized")
        raise HTTPException(status_code=503, detail="AI service is not available. Please try again later.")

    async def event_stream():
        request_id = request.request_id or str(uuid.uuid4())
        start_ts = asyncio.get_event_loop().time()
        try:
            langchain_history = convert_history_to_langchain(request.history)
            # Stream phases
            async for evt in tutor_agent.stream_phases(request.message, langchain_history):
                base = {
                    "request_id": request_id,
                    "timestamp": str(asyncio.get_event_loop().time())
                }
                payload = {**base, **evt}
                yield f"data: {json.dumps(payload)}\n\n"
        except Exception as e:
            logger.exception("Streaming error")
            err_payload = {
                "type": "error",
                "response": "Streaming failed due to an internal error.",
                "thinking_content": "An exception occurred; please retry.",
                "request_id": request_id,
                "timestamp": str(asyncio.get_event_loop().time())
            }
            yield f"data: {json.dumps(err_payload)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "text/event-stream"
    })

@app.post("/api/chat/simple", response_model=ChatResponse)
async def chat_simple_endpoint(request: ChatRequest) -> ChatResponse:
    """Simple non-streaming chat endpoint for fallback"""
    
    if tutor_agent is None:
        logger.error("❌ TutorAgent not initialized")
        raise HTTPException(
            status_code=503, 
            detail="AI service is not available. Please try again later."
        )
    
    try:
        # Generate unique request ID
        request_id = request.request_id or str(uuid.uuid4())
        timestamp = str(asyncio.get_event_loop().time())
        
        logger.info(f"📝 Received message [ID: {request_id[:8]}...]: {request.message[:50]}...")
        
        # Convert frontend history to LangChain format
        langchain_history = convert_history_to_langchain(request.history)
        
        # Process the query through the agent
        messages = langchain_history + [HumanMessage(content=request.message)]
        
        # Run the agent and collect the final state
        final_state = await tutor_agent.graph.ainvoke({"messages": messages})
        
        # Extract the final answer
        final_answer = final_state.get("final_answer", "I apologize, but I couldn't process your request right now.")
        
        # Extract thinking content from the messages
        thinking_content = extract_thinking_content(final_state.get("messages", []))
        
        logger.info(f"✅ Successfully processed request [ID: {request_id[:8]}...]")
        
        return ChatResponse(
            response=final_answer,
            thinking_content=thinking_content,
            type="complete",
            request_id=request_id,
            timestamp=timestamp
        )
        
    except Exception as e:
        logger.exception(f"❌ Error processing chat request: {e}")
        
        # Return a fallback response
        return ChatResponse(
            response="I'm experiencing some technical difficulties right now. Please try asking your question again, or rephrase it in a different way.",
            thinking_content="The system encountered an error while processing the request. This could be due to model availability or network issues.",
            type="error",
            request_id=request.request_id or str(uuid.uuid4()),
            timestamp=str(asyncio.get_event_loop().time())
        )

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
