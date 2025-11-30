"""
Session Manager for Chat-Roadmap-Quiz Integration
Handles reliable message persistence with transactional saves and retry logic
"""

import uuid
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from supabase import Client

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages chat sessions with reliable message persistence and roadmap linking"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.max_retries = 3
        self.retry_delay = 0.5  # seconds
    
    def get_or_create_session(
        self,
        user_id: str,
        conversation_id: Optional[str] = None,
        roadmap_id: Optional[str] = None,
        topic_id: Optional[str] = None,
        title: str = "New Chat"
    ) -> Dict[str, Any]:
        """
        Get existing session or create new one with roadmap/conversation linking
        
        Args:
            user_id: User UUID
            conversation_id: Optional conversation UUID (for backward compatibility)
            roadmap_id: Optional roadmap UUID (for roadmap-linked chats)
            topic_id: Optional topic UUID
            title: Session title
            
        Returns:
            Session dict with id, user_id, conversation_id, roadmap_id, etc.
        """
        try:
            # Try to find existing session
            if conversation_id:
                result = self.supabase.table("chat_sessions").select("*").eq(
                    "user_id", user_id
                ).eq("conversation_id", conversation_id).order(
                    "created_at", desc=True
                ).limit(1).execute()
                
                if result.data:
                    session = result.data[0]
                    logger.info(f"Found existing session by conversation_id: {session['id']}")
                    
                    # Update roadmap_id if provided and missing
                    if roadmap_id and not session.get('roadmap_id'):
                        self._update_session_roadmap(session['id'], roadmap_id)
                        session['roadmap_id'] = roadmap_id
                    
                    return session
            
            # Try to find by roadmap_id
            if roadmap_id:
                result = self.supabase.table("chat_sessions").select("*").eq(
                    "user_id", user_id
                ).eq("roadmap_id", roadmap_id).is_(
                    "ended_at", "null"
                ).order("created_at", desc=True).limit(1).execute()
                
                if result.data:
                    session = result.data[0]
                    logger.info(f"Found existing session by roadmap_id: {session['id']}")
                    return session
            
            # Create new session
            new_conversation_id = conversation_id or str(uuid.uuid4())
            
            session_data = {
                "user_id": user_id,
                "conversation_id": new_conversation_id,
                "roadmap_id": roadmap_id,
                "topic_id": topic_id,
                "title": title,
                "message_count": 0,
                "metadata": {}
            }
            
            result = self.supabase.table("chat_sessions").insert(session_data).execute()
            
            if result.data:
                session = result.data[0]
                logger.info(f"Created new session: {session['id']}")
                return session
            else:
                raise Exception("Failed to create session: no data returned")
                
        except Exception as e:
            logger.error(f"Error in get_or_create_session: {e}")
            raise
    
    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        message_type: Optional[str] = None,
        thinking_content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        content_html: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Save a message with retry logic and transaction safety
        
        Args:
            session_id: Chat session UUID
            role: 'user', 'assistant', or 'system'
            content: Message content (text)
            message_type: Optional classification (user_message, assistant_message, 
                         roadmap_trigger, quiz_trigger, milestone_update, progress_event)
            thinking_content: AI reasoning/thinking process
            metadata: Additional context (roadmap_id, milestone_id, etc.)
            content_html: HTML-rendered content
            attachments: File attachments
            
        Returns:
            Saved message dict
        """
        # Auto-detect message_type from role if not provided
        if not message_type:
            message_type = {
                'user': 'user_message',
                'assistant': 'assistant_message',
                'system': 'system'
            }.get(role, 'assistant_message')
        
        message_data = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "message_type": message_type,
            "thinking_content": thinking_content,
            "metadata": metadata or {},
            "content_html": content_html,
            "attachments": attachments or []
        }
        
        # Retry logic for message save
        for attempt in range(self.max_retries):
            try:
                result = self.supabase.table("chat_messages").insert(message_data).execute()
                
                if result.data:
                    message = result.data[0]
                    logger.info(
                        f"Saved message {message['id']} (type: {message_type}, "
                        f"attempt: {attempt + 1}/{self.max_retries})"
                    )
                    return message
                else:
                    raise Exception("No data returned from insert")
                    
            except Exception as e:
                logger.warning(
                    f"Message save attempt {attempt + 1}/{self.max_retries} failed: {e}"
                )
                
                if attempt == self.max_retries - 1:
                    # Final attempt failed - log critical error
                    logger.error(
                        f"CRITICAL: Failed to save message after {self.max_retries} attempts. "
                        f"Session: {session_id}, Role: {role}, Type: {message_type}"
                    )
                    raise
                
                # Wait before retry
                import time
                time.sleep(self.retry_delay * (attempt + 1))
    
    def save_message_streaming(
        self,
        session_id: str,
        role: str,
        content: str,
        message_type: Optional[str] = None,
        thinking_content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Save message during streaming (non-blocking, returns message_id or None)
        Used for immediate persistence during SSE streaming
        """
        try:
            message = self.save_message(
                session_id=session_id,
                role=role,
                content=content,
                message_type=message_type,
                thinking_content=thinking_content,
                metadata=metadata
            )
            return message['id']
        except Exception as e:
            logger.error(f"Failed to save streaming message: {e}")
            return None
    
    def update_message(
        self,
        message_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing message (e.g., append to streaming content)
        
        Args:
            message_id: Message UUID
            updates: Fields to update
            
        Returns:
            Updated message dict
        """
        try:
            result = self.supabase.table("chat_messages").update(updates).eq(
                "id", message_id
            ).execute()
            
            if result.data:
                return result.data[0]
            else:
                raise Exception("No data returned from update")
                
        except Exception as e:
            logger.error(f"Failed to update message {message_id}: {e}")
            raise
    
    def get_session_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        include_thinking: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all messages for a session
        
        Args:
            session_id: Chat session UUID
            limit: Optional max number of messages
            include_thinking: Include thinking_content in results
            
        Returns:
            List of message dicts ordered by created_at
        """
        try:
            query = self.supabase.table("chat_messages").select("*").eq(
                "session_id", session_id
            ).order("created_at", desc=False)
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            messages = result.data or []
            
            # Filter out thinking_content if not requested
            if not include_thinking:
                for msg in messages:
                    msg.pop('thinking_content', None)
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get session messages: {e}")
            return []
    
    def get_session_by_conversation_id(
        self,
        user_id: str,
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get session by legacy conversation_id"""
        try:
            result = self.supabase.table("chat_sessions").select("*").eq(
                "user_id", user_id
            ).eq("conversation_id", conversation_id).order(
                "created_at", desc=True
            ).limit(1).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to get session by conversation_id: {e}")
            return None
    
    def end_session(self, session_id: str) -> None:
        """Mark session as ended"""
        try:
            self.supabase.table("chat_sessions").update({
                "ended_at": datetime.utcnow().isoformat()
            }).eq("id", session_id).execute()
            
            logger.info(f"Ended session: {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to end session {session_id}: {e}")
    
    def _update_session_roadmap(self, session_id: str, roadmap_id: str) -> None:
        """Internal: Update session's roadmap_id"""
        try:
            self.supabase.table("chat_sessions").update({
                "roadmap_id": roadmap_id
            }).eq("id", session_id).execute()
            
            logger.info(f"Updated session {session_id} with roadmap {roadmap_id}")
            
        except Exception as e:
            logger.error(f"Failed to update session roadmap: {e}")
    
    def link_roadmap_to_session(
        self,
        session_id: str,
        roadmap_id: str
    ) -> None:
        """
        Link a roadmap to an existing session
        Called when user generates roadmap during chat
        """
        self._update_session_roadmap(session_id, roadmap_id)
    
    def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session statistics"""
        try:
            messages = self.get_session_messages(session_id)
            
            stats = {
                "total_messages": len(messages),
                "user_messages": len([m for m in messages if m['message_type'] in ['user', 'user_message']]),
                "assistant_messages": len([m for m in messages if m['message_type'] in ['assistant', 'assistant_message']]),
                "roadmap_triggers": len([m for m in messages if m['message_type'] == 'roadmap_trigger']),
                "quiz_triggers": len([m for m in messages if m['message_type'] == 'quiz_trigger']),
                "milestone_updates": len([m for m in messages if m['message_type'] == 'milestone_update']),
                "first_message_at": messages[0]['created_at'] if messages else None,
                "last_message_at": messages[-1]['created_at'] if messages else None
            }
            
            # Calculate duration
            if stats['first_message_at'] and stats['last_message_at']:
                from dateutil import parser
                start = parser.parse(stats['first_message_at'])
                end = parser.parse(stats['last_message_at'])
                duration_minutes = (end - start).total_seconds() / 60
                stats['session_duration_minutes'] = round(duration_minutes, 2)
            else:
                stats['session_duration_minutes'] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get session statistics: {e}")
            return {}
