"""
Progress Inference Engine - AI-driven milestone completion detection
Analyzes conversation to automatically detect learning progress
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class ProgressInferenceEngine:
    """
    Detects milestone completion from conversation analysis using LLM
    Confidence-based auto-completion with evidence extraction
    """
    
    def __init__(self, llm_client, confidence_threshold: float = 0.75):
        """
        Initialize Progress Inference Engine
        
        Args:
            llm_client: Ollama or other LLM client for analysis
            confidence_threshold: Minimum confidence (0-1) for auto-completion
        """
        self.llm = llm_client
        self.confidence_threshold = confidence_threshold
    
    async def analyze_milestone_progress(
        self,
        milestone_info: Dict[str, Any],
        conversation_messages: List[Dict[str, Any]],
        roadmap_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze if milestone learning objectives are met based on conversation
        
        Args:
            milestone_info: Milestone details (title, description, learning_objectives)
            conversation_messages: Recent chat messages
            roadmap_context: Optional roadmap context for better analysis
            
        Returns:
            Analysis result with completion status, confidence, evidence
        """
        try:
            # Extract milestone objectives
            milestone_title = milestone_info.get("title", "")
            milestone_desc = milestone_info.get("description", "")
            learning_objectives = milestone_info.get("learning_objectives", [])
            
            # Build analysis prompt
            analysis_prompt = self._build_analysis_prompt(
                milestone_title,
                milestone_desc,
                learning_objectives,
                conversation_messages,
                roadmap_context
            )
            
            # Get LLM analysis
            llm_response = await self._query_llm(analysis_prompt)
            
            # Parse LLM response
            analysis = self._parse_analysis_response(llm_response)
            
            # Determine completion status
            is_completed = analysis["completion_confidence"] >= self.confidence_threshold
            
            result = {
                "milestone_id": milestone_info.get("milestone_id"),
                "milestone_title": milestone_title,
                "is_completed": is_completed,
                "completion_confidence": analysis["completion_confidence"],
                "objectives_met": analysis["objectives_met"],
                "objectives_partial": analysis["objectives_partial"],
                "objectives_not_met": analysis["objectives_not_met"],
                "evidence_quotes": analysis["evidence_quotes"],
                "learning_gaps": analysis["learning_gaps"],
                "recommendation": analysis["recommendation"],
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Progress analysis for '{milestone_title}': "
                f"Completed={is_completed}, Confidence={analysis['completion_confidence']:.2f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing milestone progress: {e}")
            return {
                "milestone_id": milestone_info.get("milestone_id"),
                "is_completed": False,
                "completion_confidence": 0.0,
                "error": str(e),
                "analyzed_at": datetime.utcnow().isoformat()
            }
    
    def _build_analysis_prompt(
        self,
        milestone_title: str,
        milestone_desc: str,
        learning_objectives: List[str],
        conversation_messages: List[Dict[str, Any]],
        roadmap_context: Optional[Dict[str, Any]]
    ) -> str:
        """Build the analysis prompt for LLM"""
        
        # Format conversation
        conversation_text = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')[:500]}"
            for msg in conversation_messages[-10:]  # Last 10 messages
        ])
        
        # Format objectives
        objectives_text = "\n".join([
            f"- {obj}" for obj in learning_objectives
        ]) if learning_objectives else "No specific objectives listed"
        
        prompt = f"""You are an AI learning progress analyzer. Analyze if the student has completed the learning milestone based on the conversation.

MILESTONE TO ANALYZE:
Title: {milestone_title}
Description: {milestone_desc}

LEARNING OBJECTIVES:
{objectives_text}

RECENT CONVERSATION:
{conversation_text}

ANALYSIS TASK:
1. Determine if the student demonstrates understanding of the milestone concepts
2. Identify which learning objectives are met, partially met, or not met
3. Extract specific conversation quotes as evidence
4. Calculate completion confidence (0.0 to 1.0)
5. Identify any learning gaps
6. Provide recommendation (complete milestone, continue learning, or review)

Respond in JSON format:
{{
  "completion_confidence": 0.85,
  "objectives_met": ["objective 1", "objective 2"],
  "objectives_partial": ["objective 3"],
  "objectives_not_met": ["objective 4"],
  "evidence_quotes": ["quote showing understanding", "another quote"],
  "learning_gaps": ["gap 1", "gap 2"],
  "reasoning": "Brief explanation of the analysis",
  "recommendation": "complete|continue|review"
}}

Provide ONLY the JSON response, no other text."""

        return prompt
    
    async def _query_llm(self, prompt: str) -> str:
        """Query LLM for analysis"""
        try:
            # Use the LLM client (Ollama or other)
            response = await self.llm.ainvoke(prompt)
            
            # Extract text from response
            if hasattr(response, 'content'):
                return response.content
            elif isinstance(response, str):
                return response
            else:
                return str(response)
                
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            raise
    
    def _parse_analysis_response(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM JSON response"""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = llm_response.strip()
            if json_str.startswith("```json"):
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif json_str.startswith("```"):
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            analysis = json.loads(json_str)
            
            # Validate and normalize
            return {
                "completion_confidence": float(analysis.get("completion_confidence", 0.0)),
                "objectives_met": analysis.get("objectives_met", []),
                "objectives_partial": analysis.get("objectives_partial", []),
                "objectives_not_met": analysis.get("objectives_not_met", []),
                "evidence_quotes": analysis.get("evidence_quotes", []),
                "learning_gaps": analysis.get("learning_gaps", []),
                "reasoning": analysis.get("reasoning", ""),
                "recommendation": analysis.get("recommendation", "continue")
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.debug(f"Raw response: {llm_response}")
            
            # Fallback: simple heuristic analysis
            return self._fallback_analysis(llm_response)
    
    def _fallback_analysis(self, llm_response: str) -> Dict[str, Any]:
        """Fallback analysis if JSON parsing fails"""
        
        # Simple keyword-based analysis
        response_lower = llm_response.lower()
        
        positive_keywords = ["understand", "correct", "excellent", "great", "well done", "mastered"]
        negative_keywords = ["confused", "incorrect", "wrong", "misunderstood", "unclear"]
        
        positive_count = sum(1 for kw in positive_keywords if kw in response_lower)
        negative_count = sum(1 for kw in negative_keywords if kw in response_lower)
        
        # Calculate basic confidence
        total = positive_count + negative_count
        confidence = (positive_count / total) if total > 0 else 0.5
        
        return {
            "completion_confidence": confidence,
            "objectives_met": [],
            "objectives_partial": [],
            "objectives_not_met": [],
            "evidence_quotes": [llm_response[:200]],
            "learning_gaps": [],
            "reasoning": "Fallback analysis due to parsing error",
            "recommendation": "continue"
        }
    
    async def check_session_for_completions(
        self,
        session_id: str,
        roadmap_id: str,
        active_milestone_id: str,
        supabase_client
    ) -> Optional[Dict[str, Any]]:
        """
        Check if recent session messages indicate milestone completion
        Called periodically during chat or after significant interactions
        
        Args:
            session_id: Chat session ID
            roadmap_id: Roadmap ID
            active_milestone_id: Current milestone being worked on
            supabase_client: Supabase client for database queries
            
        Returns:
            Completion analysis if milestone completed, None otherwise
        """
        try:
            # Get roadmap and milestone info
            roadmap_result = supabase_client.table("learning_roadmaps")\
                .select("*")\
                .eq("id", roadmap_id)\
                .execute()
            
            if not roadmap_result.data:
                return None
            
            roadmap = roadmap_result.data[0]
            roadmap_data = roadmap["roadmap_data"]
            
            # Find milestone
            milestone_info = None
            for phase in roadmap_data.get("learning_phases", []):
                for milestone in phase.get("milestones", []):
                    if milestone.get("milestone_id") == active_milestone_id:
                        milestone_info = milestone
                        break
                if milestone_info:
                    break
            
            if not milestone_info:
                return None
            
            # Get recent conversation messages
            messages_result = supabase_client.table("chat_messages")\
                .select("role, content, created_at")\
                .eq("session_id", session_id)\
                .order("created_at", desc=False)\
                .limit(20)\
                .execute()
            
            conversation_messages = messages_result.data or []
            
            if len(conversation_messages) < 3:
                # Not enough conversation to analyze
                return None
            
            # Analyze progress
            analysis = await self.analyze_milestone_progress(
                milestone_info=milestone_info,
                conversation_messages=conversation_messages,
                roadmap_context={"roadmap_title": roadmap.get("title")}
            )
            
            # If completed, update milestone_progress
            if analysis["is_completed"]:
                try:
                    # Find phase_id for this milestone
                    phase_id = None
                    for phase in roadmap_data.get("learning_phases", []):
                        for milestone in phase.get("milestones", []):
                            if milestone.get("milestone_id") == active_milestone_id:
                                phase_id = phase.get("phase_id")
                                break
                        if phase_id:
                            break
                    
                    if phase_id:
                        # Update milestone progress with auto-completion
                        supabase_client.table("milestone_progress").upsert({
                            "user_id": roadmap["user_id"],
                            "roadmap_id": roadmap_id,
                            "phase_id": phase_id,
                            "milestone_id": active_milestone_id,
                            "status": "completed",
                            "progress_percentage": 100.0,
                            "completed_at": datetime.utcnow().isoformat(),
                            "auto_completed": True,
                            "completion_confidence": analysis["completion_confidence"],
                            "completion_evidence": analysis["evidence_quotes"],
                            "inference_metadata": json.dumps({
                                "objectives_met": analysis["objectives_met"],
                                "objectives_partial": analysis["objectives_partial"],
                                "learning_gaps": analysis["learning_gaps"],
                                "recommendation": analysis["recommendation"],
                                "analyzed_at": analysis["analyzed_at"]
                            })
                        }, on_conflict="user_id,roadmap_id,phase_id,milestone_id").execute()
                        
                        logger.info(
                            f"✅ Auto-completed milestone {active_milestone_id} "
                            f"with confidence {analysis['completion_confidence']:.2f}"
                        )
                except Exception as e:
                    logger.error(f"Failed to update milestone auto-completion: {e}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error checking session for completions: {e}")
            return None
