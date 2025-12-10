"""
File Upload Router
Handles file uploads, processing, and management
"""

import os
import logging
import uuid
import aiofiles
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from auth import get_current_user
from config import get_supabase_client
from mcp_agents import file_agent, vector_agent

logger = logging.getLogger("file_router")

router = APIRouter(prefix="/api", tags=["files"])

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_TYPES = {
    'application/pdf': 'pdf',
    'image/png': 'image',
    'image/jpeg': 'image',
    'image/jpg': 'image'
}
UPLOAD_DIR = Path("./storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class UploadResponse(BaseModel):
    id: str
    file_name: str
    file_type: str
    file_size: int
    status: str
    message: str


class FileProcessResponse(BaseModel):
    id: str
    processed: bool
    summary: str
    extracted_text: str
    metadata: dict


class FileListResponse(BaseModel):
    uploads: List[dict]
    total: int


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    topic_id: Optional[str] = Form(None),
    user: dict = Depends(get_current_user)
):
    """
    Upload a file (PDF or image) for processing
    
    - **file**: The file to upload
    - **topic_id**: Optional topic ID to associate with
    """
    supabase = get_supabase_client()
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Supported: PDF, PNG, JPG"
        )
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_type = ALLOWED_TYPES[file.content_type]
    file_ext = Path(file.filename).suffix
    safe_filename = f"{file_id}{file_ext}"
    
    # Save file locally first
    local_path = UPLOAD_DIR / safe_filename
    
    try:
        async with aiofiles.open(local_path, 'wb') as f:
            await f.write(file_content)
        
        logger.info(f"✅ File saved locally: {safe_filename}")
        
        # Upload to Supabase Storage
        storage_path = f"{user['user_id']}/{safe_filename}"
        
        try:
            # Upload to Supabase Storage bucket 'uploads'
            supabase.storage.from_('uploads').upload(
                storage_path,
                file_content,
                {
                    'content-type': file.content_type,
                    'x-upsert': 'true'
                }
            )
            
            # Get public URL
            file_url = supabase.storage.from_('uploads').get_public_url(storage_path)
            
            logger.info(f"✅ File uploaded to Supabase Storage: {storage_path}")
            
        except Exception as e:
            logger.warning(f"⚠️ Supabase Storage upload failed: {e}. Using local storage.")
            file_url = f"/storage/uploads/{safe_filename}"
        
        # Create database record
        upload_data = {
            'id': file_id,
                'user_id': user['user_id'],
            'file_url': file_url,
            'file_name': file.filename,
            'file_type': file_type,
            'file_size': file_size,
            'processed': False,
            'metadata': {
                'original_name': file.filename,
                'content_type': file.content_type,
                'topic_id': topic_id
            }
        }
        
        result = supabase.table('uploads').insert(upload_data).execute()
        
        logger.info(f"✅ Upload record created: {file_id}")
        
        # Process file asynchronously (in background)
        # For now, we'll do it synchronously
        if file_type == 'pdf':
            process_result = await file_agent.process_pdf(str(local_path))
        else:
            process_result = await file_agent.process_image(str(local_path))
        
        # Update with processed content
        if 'error' not in process_result:
            extracted_text = process_result.get('text', '')
            summary = extracted_text[:500] + ('...' if len(extracted_text) > 500 else '')
            
            supabase.table('uploads').update({
                'processed': True,
                'extracted_text': extracted_text,
                'summary': summary,
                'metadata': {
                    **upload_data['metadata'],
                    'processing_result': process_result
                }
            }).eq('id', file_id).execute()
            
            # Create embedding for search
            if extracted_text:
                await vector_agent.store_embedding(
                    user_id=user['user_id'],
                    content=extracted_text[:1000],
                    source_type='upload',
                    source_id=file_id,
                    metadata={'file_name': file.filename, 'file_type': file_type}
                )
            
            logger.info(f"✅ File processed and indexed: {file_id}")
        
        return UploadResponse(
            id=file_id,
            file_name=file.filename,
            file_type=file_type,
            file_size=file_size,
            status="processed" if 'error' not in process_result else "uploaded",
            message="File uploaded and processed successfully"
        )
        
    except Exception as e:
        logger.error(f"❌ Upload failed: {e}")
        
        # Cleanup local file
        if local_path.exists():
            local_path.unlink()
        
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/uploads", response_model=FileListResponse)
async def list_uploads(
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(get_current_user)
):
    """
    List all uploads for the current user
    """
    supabase = get_supabase_client()
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Query uploads
        result = supabase.table('uploads')\
            .select('*')\
            .eq('user_id', user['user_id'])\
            .order('created_at', desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        # Count total
        count_result = supabase.table('uploads')\
            .select('id', count='exact')\
            .eq('user_id', user['user_id'])\
            .execute()
        
        total = count_result.count if hasattr(count_result, 'count') else len(result.data)
        
        return FileListResponse(
            uploads=result.data,
            total=total
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to list uploads: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve uploads")


@router.get("/uploads/{upload_id}", response_model=dict)
async def get_upload(
    upload_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get details of a specific upload
    """
    supabase = get_supabase_client()
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        result = supabase.table('uploads')\
            .select('*')\
            .eq('id', upload_id)\
            .eq('user_id', user['user_id'])\
            .single()\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        return result.data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve upload")


@router.post("/uploads/{upload_id}/process", response_model=FileProcessResponse)
async def process_upload(
    upload_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Reprocess an uploaded file
    """
    supabase = get_supabase_client()
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Get upload record
        upload = supabase.table('uploads')\
            .select('*')\
            .eq('id', upload_id)\
            .eq('user_id', user['user_id'])\
            .single()\
            .execute()
        
        if not upload.data:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        # Find local file
        file_name = Path(upload.data['file_url']).name
        local_path = UPLOAD_DIR / file_name
        
        if not local_path.exists():
            raise HTTPException(status_code=404, detail="File not found locally")
        
        # Process based on type
        if upload.data['file_type'] == 'pdf':
            result = await file_agent.process_pdf(str(local_path))
        else:
            result = await file_agent.process_image(str(local_path))
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        # Update database
        extracted_text = result.get('text', '')
        summary = extracted_text[:500] + ('...' if len(extracted_text) > 500 else '')
        
        supabase.table('uploads').update({
            'processed': True,
            'extracted_text': extracted_text,
            'summary': summary,
            'metadata': {
                **upload.data.get('metadata', {}),
                'processing_result': result,
                'reprocessed_at': datetime.utcnow().isoformat()
            }
        }).eq('id', upload_id).execute()
        
        return FileProcessResponse(
            id=upload_id,
            processed=True,
            summary=summary,
            extracted_text=extracted_text,
            metadata=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to process upload: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.delete("/uploads/{upload_id}")
async def delete_upload(
    upload_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Delete an upload
    """
    supabase = get_supabase_client()
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Get upload record
        upload = supabase.table('uploads')\
            .select('*')\
            .eq('id', upload_id)\
            .eq('user_id', user['user_id'])\
            .single()\
            .execute()
        
        if not upload.data:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        # Delete from Supabase Storage
        try:
            storage_path = Path(upload.data['file_url']).name
            supabase.storage.from_('uploads').remove([f"{user['user_id']}/{storage_path}"])
        except Exception as e:
            logger.warning(f"⚠️ Failed to delete from storage: {e}")
        
        # Delete local file
        file_name = Path(upload.data['file_url']).name
        local_path = UPLOAD_DIR / file_name
        if local_path.exists():
            local_path.unlink()
        
        # Delete database record (cascade will handle embeddings)
        supabase.table('uploads').delete().eq('id', upload_id).execute()
        
        logger.info(f"✅ Deleted upload: {upload_id}")
        
        return {"message": "Upload deleted successfully", "id": upload_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete upload")
