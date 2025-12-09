"""Notes management router for Notion-like editor."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
from config import get_supabase_client
from rate_limit import limit_user

logger = logging.getLogger("note_router")

router = APIRouter(prefix="/api/notes", tags=["notes"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class FolderUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    position: Optional[int] = None


class NoteCreate(BaseModel):
    title: str = "Untitled Note"
    folder_id: Optional[str] = None
    content_json: Dict[str, Any] = {"type": "doc", "content": []}


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content_json: Optional[Dict[str, Any]] = None
    folder_id: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None
    tags: Optional[List[str]] = None


class ChatToNoteRequest(BaseModel):
    chat_message_id: Optional[str] = None
    content: str
    note_id: Optional[str] = None
    folder_id: Optional[str] = None
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Folder endpoints
# ---------------------------------------------------------------------------
@router.get("/folders")
async def list_folders(user: Dict[str, str] = Depends(get_current_user)) -> Dict[str, Any]:
    """Return all folders for the authenticated user."""
    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        result = (
            supabase.table("note_folders")
            .select("*")
            .eq("user_id", user["user_id"])
            .order("position")
            .execute()
        )
        return {"folders": result.data or []}
    except Exception as exc:  # pragma: no cover - supabase error surface
        logger.exception("Failed to fetch folders")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/folders")
async def create_folder(
    folder: FolderCreate, user: Dict[str, str] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new folder for the current user."""
    limit_user(user["user_id"])

    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    payload = {
        "user_id": user["user_id"],
        "name": folder.name,
        "parent_id": folder.parent_id,
        "color": folder.color,
        "icon": folder.icon,
    }

    try:
        result = supabase.table("note_folders").insert(payload).execute()
        folder_row = result.data[0] if result.data else None
        return {"folder": folder_row}
    except Exception as exc:  # pragma: no cover
        logger.exception("Failed to create folder")
        raise HTTPException(status_code=500, detail=str(exc))


@router.patch("/folders/{folder_id}")
async def update_folder(
    folder_id: str, folder: FolderUpdate, user: Dict[str, str] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update folder metadata for the current user."""
    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    update_data = {k: v for k, v in folder.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow().isoformat()

    try:
        result = (
            supabase.table("note_folders")
            .update(update_data)
            .eq("id", folder_id)
            .eq("user_id", user["user_id"])
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Folder not found")
        return {"folder": result.data[0]}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        logger.exception("Failed to update folder")
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/folders/{folder_id}")
async def delete_folder(
    folder_id: str, user: Dict[str, str] = Depends(get_current_user)
) -> Dict[str, str]:
    """Delete a folder owned by the current user."""
    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        (
            supabase.table("note_folders")
            .delete()
            .eq("id", folder_id)
            .eq("user_id", user["user_id"])
            .execute()
        )
        return {"message": "Folder deleted"}
    except Exception as exc:  # pragma: no cover
        logger.exception("Failed to delete folder")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Note endpoints
# ---------------------------------------------------------------------------
@router.get("/")
async def list_notes(
    folder_id: Optional[str] = None,
    is_archived: bool = False,
    search: Optional[str] = None,
    user: Dict[str, str] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return notes for the authenticated user with optional filters."""
    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        query = (
            supabase.table("learning_notes")
            .select("*")
            .eq("user_id", user["user_id"])
            .eq("is_archived", is_archived)
        )

        if folder_id:
            if folder_id == "root":
                query = query.is_("folder_id", "null")
            else:
                query = query.eq("folder_id", folder_id)

        if search:
            search_term = search.replace(",", " ")
            query = query.or_(
                f"title.ilike.%{search_term}%,content_text.ilike.%{search_term}%"
            )

        result = query.order("position").execute()
        return {"notes": result.data or []}
    except Exception as exc:  # pragma: no cover
        logger.exception("Failed to fetch notes")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{note_id}")
async def get_note(note_id: str, user: Dict[str, str] = Depends(get_current_user)) -> Dict[str, Any]:
    """Return a single note for the current user."""
    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        result = (
            supabase.table("learning_notes")
            .select("*")
            .eq("id", note_id)
            .eq("user_id", user["user_id"])
            .single()
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Note not found")
        return {"note": result.data}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        logger.exception("Failed to fetch note")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/")
async def create_note(
    note: NoteCreate, user: Dict[str, str] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new note."""
    limit_user(user["user_id"])

    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    content_text = extract_text_from_tiptap(note.content_json)
    payload = {
        "user_id": user["user_id"],
        "title": note.title or "Untitled Note",
        "folder_id": note.folder_id,
        "content_json": note.content_json,
        "content_text": content_text,
    }

    try:
        result = supabase.table("learning_notes").insert(payload).execute()
        created_note = result.data[0] if result.data else None
        return {"note": created_note}
    except Exception as exc:  # pragma: no cover
        logger.exception("Failed to create note")
        raise HTTPException(status_code=500, detail=str(exc))


@router.patch("/{note_id}")
async def update_note(
    note_id: str,
    note: NoteUpdate,
    user: Dict[str, str] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Update an existing note."""
    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    update_data = {k: v for k, v in note.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow().isoformat()

    if "content_json" in update_data:
        update_data["content_text"] = extract_text_from_tiptap(update_data["content_json"])

    try:
        result = (
            supabase.table("learning_notes")
            .update(update_data)
            .eq("id", note_id)
            .eq("user_id", user["user_id"])
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Note not found")
        return {"note": result.data[0]}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        logger.exception("Failed to update note")
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/{note_id}")
async def delete_note(note_id: str, user: Dict[str, str] = Depends(get_current_user)) -> Dict[str, str]:
    """Delete a note."""
    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        (
            supabase.table("learning_notes")
            .delete()
            .eq("id", note_id)
            .eq("user_id", user["user_id"])
            .execute()
        )
        return {"message": "Note deleted"}
    except Exception as exc:  # pragma: no cover
        logger.exception("Failed to delete note")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Chat → note integration
# ---------------------------------------------------------------------------
@router.post("/inject-from-chat")
async def inject_chat_to_note(
    request: ChatToNoteRequest,
    user: Dict[str, str] = Depends(get_current_user),
) -> Dict[str, str]:
    """Append chat content to an existing note or create a new one."""
    limit_user(user["user_id"])

    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    note_id = request.note_id

    try:
        # Auto-create or find "Chat Notes" folder if no folder_id is provided
        folder_id = request.folder_id
        if not folder_id and not note_id:
            # Check if "Chat Notes" folder exists
            folder_result = (
                supabase.table("note_folders")
                .select("id")
                .eq("user_id", user["user_id"])
                .eq("name", "Chat Notes")
                .limit(1)
                .execute()
            )
            
            if folder_result.data and len(folder_result.data) > 0:
                folder_id = folder_result.data[0]["id"]
            else:
                # Create "Chat Notes" folder
                new_folder = supabase.table("note_folders").insert(
                    {
                        "user_id": user["user_id"],
                        "name": "Chat Notes",
                        "icon": "💬",
                        "color": "#3b82f6",
                    }
                ).execute()
                if new_folder.data:
                    folder_id = new_folder.data[0]["id"]

        if not note_id:
            title = request.title or f"Chat Note - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
            content_json = {
                "type": "doc",
                "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": request.content}]}
                ],
            }
            payload = {
                "user_id": user["user_id"],
                "title": title,
                "folder_id": folder_id,
                "content_json": content_json,
                "content_text": extract_text_from_tiptap(content_json),
            }
            result = supabase.table("learning_notes").insert(payload).execute()
            if not result.data:
                raise HTTPException(status_code=500, detail="Failed to create note")
            note_id = result.data[0]["id"]
        else:
            existing = (
                supabase.table("learning_notes")
                .select("content_json")
                .eq("id", note_id)
                .eq("user_id", user["user_id"])
                .single()
                .execute()
            )
            if not existing.data:
                raise HTTPException(status_code=404, detail="Note not found")

            content_json = existing.data.get("content_json") or {"type": "doc", "content": []}
            if not isinstance(content_json, dict):
                raise HTTPException(status_code=500, detail="Stored note content is invalid")

            content_json.setdefault("content", []).append(
                {"type": "paragraph", "content": [{"type": "text", "text": request.content}]}
            )

            supabase.table("learning_notes").update(
                {
                    "content_json": content_json,
                    "content_text": extract_text_from_tiptap(content_json),
                    "updated_at": datetime.utcnow().isoformat(),
                }
            ).eq("id", note_id).execute()

        supabase.table("note_chat_links").insert(
            {
                "note_id": note_id,
                "user_id": user["user_id"],
                "chat_message_id": request.chat_message_id,
                "content": request.content,
                "metadata": request.metadata or {},
            }
        ).execute()

        if request.chat_message_id:
            supabase.table("chat_history").update(
                {"saved_to_note": True, "note_id": note_id}
            ).eq("id", request.chat_message_id).execute()

        return {"message": "Content added to note", "note_id": note_id}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        logger.exception("Failed to inject chat content into note")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def extract_text_from_tiptap(tiptap_json: Dict[str, Any]) -> str:
    """Flatten Tiptap JSON to a searchable text string."""

    def recurse(node: Any) -> List[str]:
        parts: List[str] = []
        if isinstance(node, dict):
            node_type = node.get("type")
            if node_type == "text":
                parts.append(node.get("text", ""))
            for child in node.get("content", []) or []:
                parts.extend(recurse(child))
        elif isinstance(node, list):
            for item in node:
                parts.extend(recurse(item))
        return parts

    text = " ".join(recurse(tiptap_json)).strip()
    return " ".join(text.split())  # collapse excessive whitespace
