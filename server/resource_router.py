"""
Resource Router
Handles saved learning materials, notes, bookmarks, and resource organization
"""

import logging
from typing import List, Optional
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import get_current_user
from config import get_supabase_client

logger = logging.getLogger("resource_router")

router = APIRouter(prefix="/api/resources", tags=["resources"])


class ResourceType(str, Enum):
    """Types of resources"""
    NOTE = "note"
    BOOKMARK = "bookmark"
    SNIPPET = "snippet"
    FILE = "file"
    REFERENCE = "reference"


class ResourceCategory(str, Enum):
    """Resource categories"""
    PROGRAMMING = "programming"
    MATH = "math"
    GENERAL = "general"
    TUTORIAL = "tutorial"
    DOCUMENTATION = "documentation"
    EXAMPLE = "example"


class NoteCreate(BaseModel):
    """Create a new note"""
    title: str = Field(..., min_length=1, max_length=200)
    content: str
    topic_id: Optional[str] = None
    category: ResourceCategory = ResourceCategory.GENERAL
    tags: List[str] = []
    is_favorite: bool = False
    metadata: Optional[dict] = {}


class NoteUpdate(BaseModel):
    """Update note"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None
    topic_id: Optional[str] = None
    category: Optional[ResourceCategory] = None
    tags: Optional[List[str]] = None
    is_favorite: Optional[bool] = None
    metadata: Optional[dict] = None


class BookmarkCreate(BaseModel):
    """Create a bookmark"""
    title: str = Field(..., min_length=1, max_length=200)
    url: str
    description: Optional[str] = None
    topic_id: Optional[str] = None
    category: ResourceCategory = ResourceCategory.GENERAL
    tags: List[str] = []
    is_favorite: bool = False
    metadata: Optional[dict] = {}


class ResourceResponse(BaseModel):
    """Resource response model"""
    id: str
    user_id: str
    resource_type: str
    title: str
    content: Optional[str] = None
    url: Optional[str] = None
    topic_id: Optional[str] = None
    topic_title: Optional[str] = None
    category: str
    tags: List[str]
    is_favorite: bool
    metadata: dict
    created_at: str
    updated_at: str


class FolderCreate(BaseModel):
    """Create a resource folder/collection"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[str] = None
    color: Optional[str] = None  # Hex color code


class FolderResponse(BaseModel):
    """Folder response"""
    id: str
    user_id: str
    name: str
    description: Optional[str]
    parent_id: Optional[str]
    color: Optional[str]
    resource_count: int
    created_at: str
    updated_at: str


class ResourceStats(BaseModel):
    """Resource statistics"""
    total_resources: int
    notes_count: int
    bookmarks_count: int
    snippets_count: int
    files_count: int
    favorites_count: int
    total_folders: int
    resources_by_category: dict
    recent_resources: List[ResourceResponse]


@router.post("/notes", response_model=ResourceResponse)
async def create_note(
    note: NoteCreate,
    user: dict = Depends(get_current_user)
):
    """
    Create a new note

    - **title**: Note title
    - **content**: Note content (supports Markdown)
    - **topic_id**: Optional topic association
    - **category**: Resource category
    - **tags**: List of tags for organization
    """
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        resource_data = {
            'user_id': user['user_id'],
            'resource_type': ResourceType.NOTE.value,
            'title': note.title,
            'content': note.content,
            'topic_id': note.topic_id,
            'category': note.category.value,
            'tags': note.tags,
            'is_favorite': note.is_favorite,
            'metadata': note.metadata or {}
        }

        result = supabase.table('resources').insert(resource_data).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create note")

        logger.info(f"✅ Created note '{note.title}' for user {user['user_id']}")

        return await _format_resource_response(supabase, result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create note: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create note: {str(e)}")


@router.post("/bookmarks", response_model=ResourceResponse)
async def create_bookmark(
    bookmark: BookmarkCreate,
    user: dict = Depends(get_current_user)
):
    """
    Create a new bookmark

    - **title**: Bookmark title
    - **url**: URL to bookmark
    - **description**: Optional description
    - **topic_id**: Optional topic association
    - **category**: Resource category
    """
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        resource_data = {
            'user_id': user['user_id'],
            'resource_type': ResourceType.BOOKMARK.value,
            'title': bookmark.title,
            'url': bookmark.url,
            'content': bookmark.description,
            'topic_id': bookmark.topic_id,
            'category': bookmark.category.value,
            'tags': bookmark.tags,
            'is_favorite': bookmark.is_favorite,
            'metadata': bookmark.metadata or {}
        }

        result = supabase.table('resources').insert(resource_data).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create bookmark")

        logger.info(f"✅ Created bookmark '{bookmark.title}' for user {user['user_id']}")

        return await _format_resource_response(supabase, result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create bookmark: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create bookmark: {str(e)}")


@router.get("/", response_model=List[ResourceResponse])
async def get_all_resources(
    resource_type: Optional[ResourceType] = None,
    category: Optional[ResourceCategory] = None,
    topic_id: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """
    Get all resources with filters

    - **resource_type**: Filter by type (note, bookmark, snippet, etc.)
    - **category**: Filter by category
    - **topic_id**: Filter by topic
    - **is_favorite**: Filter favorites
    - **tag**: Filter by tag
    - **search**: Search in title and content
    - **limit**: Max results (default 50)
    """
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        query = supabase.table('resources')\
            .select('*')\
            .eq('user_id', user['user_id'])\
            .order('updated_at', desc=True)\
            .limit(limit)

        if resource_type:
            query = query.eq('resource_type', resource_type.value)

        if category:
            query = query.eq('category', category.value)

        if topic_id:
            query = query.eq('topic_id', topic_id)

        if is_favorite is not None:
            query = query.eq('is_favorite', is_favorite)

        if tag:
            query = query.contains('tags', [tag])

        if search:
            query = query.or_(f'title.ilike.%{search}%,content.ilike.%{search}%')

        result = query.execute()

        resources = []
        for r in result.data:
            resources.append(await _format_resource_response(supabase, r))

        return resources

    except Exception as e:
        logger.error(f"❌ Failed to get resources: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve resources")


@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: str,
    user: dict = Depends(get_current_user)
):
    """Get a specific resource by ID"""
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        result = supabase.table('resources')\
            .select('*')\
            .eq('id', resource_id)\
            .eq('user_id', user['user_id'])\
            .single()\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Resource not found")

        return await _format_resource_response(supabase, result.data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get resource: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve resource")


@router.patch("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: str,
    update: NoteUpdate,
    user: dict = Depends(get_current_user)
):
    """
    Update a resource

    - **title**: New title
    - **content**: New content
    - **category**: New category
    - **tags**: New tags
    - **is_favorite**: Toggle favorite
    """
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        # Check resource exists and belongs to user
        existing = supabase.table('resources')\
            .select('*')\
            .eq('id', resource_id)\
            .eq('user_id', user['user_id'])\
            .single()\
            .execute()

        if not existing.data:
            raise HTTPException(status_code=404, detail="Resource not found")

        # Build update data
        update_data = {'updated_at': datetime.utcnow().isoformat()}

        if update.title is not None:
            update_data['title'] = update.title

        if update.content is not None:
            update_data['content'] = update.content

        if update.topic_id is not None:
            update_data['topic_id'] = update.topic_id

        if update.category is not None:
            update_data['category'] = update.category.value

        if update.tags is not None:
            update_data['tags'] = update.tags

        if update.is_favorite is not None:
            update_data['is_favorite'] = update.is_favorite

        if update.metadata is not None:
            current_meta = existing.data.get('metadata', {})
            current_meta.update(update.metadata)
            update_data['metadata'] = current_meta

        # Update in database
        result = supabase.table('resources')\
            .update(update_data)\
            .eq('id', resource_id)\
            .execute()

        logger.info(f"✅ Updated resource {resource_id}")

        return await get_resource(resource_id, user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update resource: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update resource: {str(e)}")


@router.delete("/{resource_id}")
async def delete_resource(
    resource_id: str,
    user: dict = Depends(get_current_user)
):
    """Delete a resource"""
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        result = supabase.table('resources')\
            .delete()\
            .eq('id', resource_id)\
            .eq('user_id', user['user_id'])\
            .execute()

        logger.info(f"✅ Deleted resource {resource_id}")

        return {"message": "Resource deleted successfully", "resource_id": resource_id}

    except Exception as e:
        logger.error(f"❌ Failed to delete resource: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete resource")


@router.post("/folders", response_model=FolderResponse)
async def create_folder(
    folder: FolderCreate,
    user: dict = Depends(get_current_user)
):
    """
    Create a resource folder for organization

    - **name**: Folder name
    - **description**: Optional description
    - **parent_id**: Optional parent folder (for nested folders)
    - **color**: Optional color code
    """
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        folder_data = {
            'user_id': user['user_id'],
            'name': folder.name,
            'description': folder.description,
            'parent_id': folder.parent_id,
            'color': folder.color
        }

        result = supabase.table('resource_folders').insert(folder_data).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create folder")

        logger.info(f"✅ Created folder '{folder.name}' for user {user['user_id']}")

        folder_record = result.data[0]

        return FolderResponse(
            id=folder_record['id'],
            user_id=folder_record['user_id'],
            name=folder_record['name'],
            description=folder_record.get('description'),
            parent_id=folder_record.get('parent_id'),
            color=folder_record.get('color'),
            resource_count=0,  # No resources yet
            created_at=folder_record['created_at'],
            updated_at=folder_record.get('updated_at', folder_record['created_at'])
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create folder: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create folder: {str(e)}")


@router.get("/folders/all", response_model=List[FolderResponse])
async def get_folders(
    user: dict = Depends(get_current_user)
):
    """Get all resource folders"""
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        folders = supabase.table('resource_folders')\
            .select('*')\
            .eq('user_id', user['user_id'])\
            .order('created_at', desc=False)\
            .execute()

        # Count resources in each folder
        folder_responses = []
        for folder in folders.data:
            # Count resources (would need folder_id field in resources table)
            resource_count = 0  # Placeholder

            folder_responses.append(FolderResponse(
                id=folder['id'],
                user_id=folder['user_id'],
                name=folder['name'],
                description=folder.get('description'),
                parent_id=folder.get('parent_id'),
                color=folder.get('color'),
                resource_count=resource_count,
                created_at=folder['created_at'],
                updated_at=folder.get('updated_at', folder['created_at'])
            ))

        return folder_responses

    except Exception as e:
        logger.error(f"❌ Failed to get folders: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve folders")


@router.get("/stats/summary", response_model=ResourceStats)
async def get_resource_stats(
    user: dict = Depends(get_current_user)
):
    """Get resource statistics"""
    supabase = get_supabase_client()

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        # Get all resources
        resources = supabase.table('resources')\
            .select('*')\
            .eq('user_id', user['user_id'])\
            .execute()

        # Get folders
        folders = supabase.table('resource_folders')\
            .select('id')\
            .eq('user_id', user['user_id'])\
            .execute()

        total_resources = len(resources.data)
        notes_count = sum(1 for r in resources.data if r['resource_type'] == ResourceType.NOTE.value)
        bookmarks_count = sum(1 for r in resources.data if r['resource_type'] == ResourceType.BOOKMARK.value)
        snippets_count = sum(1 for r in resources.data if r['resource_type'] == ResourceType.SNIPPET.value)
        files_count = sum(1 for r in resources.data if r['resource_type'] == ResourceType.FILE.value)
        favorites_count = sum(1 for r in resources.data if r.get('is_favorite', False))

        # Breakdown by category
        resources_by_category = {}
        for category in ResourceCategory:
            resources_by_category[category.value] = sum(
                1 for r in resources.data if r['category'] == category.value
            )

        # Recent resources
        recent = sorted(resources.data, key=lambda x: x['updated_at'], reverse=True)[:10]
        recent_resources = []
        for r in recent:
            recent_resources.append(await _format_resource_response(supabase, r))

        return ResourceStats(
            total_resources=total_resources,
            notes_count=notes_count,
            bookmarks_count=bookmarks_count,
            snippets_count=snippets_count,
            files_count=files_count,
            favorites_count=favorites_count,
            total_folders=len(folders.data),
            resources_by_category=resources_by_category,
            recent_resources=recent_resources
        )

    except Exception as e:
        logger.error(f"❌ Failed to get resource stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


# --- Helper Functions ---
async def _format_resource_response(supabase, resource_data: dict) -> ResourceResponse:
    """Format resource data for response with topic details"""
    topic_title = None

    if resource_data.get('topic_id'):
        try:
            topic = supabase.table('topics')\
                .select('title')\
                .eq('id', resource_data['topic_id'])\
                .single()\
                .execute()

            if topic.data:
                topic_title = topic.data['title']
        except:
            pass

    return ResourceResponse(
        id=resource_data['id'],
        user_id=resource_data['user_id'],
        resource_type=resource_data['resource_type'],
        title=resource_data['title'],
        content=resource_data.get('content'),
        url=resource_data.get('url'),
        topic_id=resource_data.get('topic_id'),
        topic_title=topic_title,
        category=resource_data['category'],
        tags=resource_data.get('tags', []),
        is_favorite=resource_data.get('is_favorite', False),
        metadata=resource_data.get('metadata', {}),
        created_at=resource_data['created_at'],
        updated_at=resource_data.get('updated_at', resource_data['created_at'])
    )
