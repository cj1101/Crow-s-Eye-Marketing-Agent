from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from crow_eye_api.crud import crud_context_files
from crow_eye_api import schemas, models
from crow_eye_api.database import get_db
from crow_eye_api.api.api_v1.dependencies import get_current_active_user

router = APIRouter()

@router.post("/", response_model=schemas.ContextFileResponse)
async def upload_context_file(
    file: UploadFile = File(...),
    description: Optional[str] = None,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a context file (documents, notes, etc.) for use in AI content generation.
    """
    try:
        # Validate file type (only allow text-based files and PDFs)
        allowed_types = {
            'text/plain': '.txt',
            'text/markdown': '.md',
            'application/pdf': '.pdf',
            'text/csv': '.csv',
            'application/json': '.json',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx'
        }
        
        content_type = file.content_type
        if content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not supported. Allowed types: {list(allowed_types.values())}"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Check file size (max 10MB for context files)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File too large. Maximum size is 10MB for context files."
            )
        
        # Extract text content based on file type
        if content_type == 'text/plain':
            text_content = file_content.decode('utf-8')
        elif content_type == 'text/markdown':
            text_content = file_content.decode('utf-8')
        elif content_type == 'application/json':
            text_content = file_content.decode('utf-8')
        elif content_type == 'text/csv':
            text_content = file_content.decode('utf-8')
        elif content_type == 'application/pdf':
            # For PDF files, we'd need a PDF parser
            try:
                import PyPDF2
                import io
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                text_content = ""
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"
            except ImportError:
                # If PyPDF2 is not available, store as binary and handle later
                text_content = "[PDF content - requires processing]"
        else:
            text_content = "[Binary content - requires processing]"
        
        # Create context file record
        context_file_create = schemas.ContextFileCreate(
            filename=file.filename or "unnamed_file",
            original_filename=file.filename or "unnamed_file",
            content_type=content_type,
            file_size=len(file_content),
            text_content=text_content,
            description=description
        )
        
        context_file = await crud_context_files.create_context_file(
            db=db, 
            context_file=context_file_create, 
            user_id=current_user.id,
            file_content=file_content
        )
        
        return schemas.ContextFileResponse.from_orm(context_file)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading context file: {str(e)}"
        )

@router.get("/", response_model=List[schemas.ContextFileResponse])
async def list_context_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all context files for the current user.
    """
    context_files = await crud_context_files.get_context_files(
        db=db, 
        user_id=current_user.id, 
        skip=skip, 
        limit=limit
    )
    return [schemas.ContextFileResponse.from_orm(cf) for cf in context_files]

@router.get("/{file_id}", response_model=schemas.ContextFileResponse)
async def get_context_file(
    file_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific context file by ID.
    """
    context_file = await crud_context_files.get_context_file(
        db, file_id=file_id, user_id=current_user.id
    )
    if not context_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Context file not found"
        )
    return schemas.ContextFileResponse.from_orm(context_file)

@router.delete("/{file_id}")
async def delete_context_file(
    file_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a context file.
    """
    context_file = await crud_context_files.get_context_file(
        db, file_id=file_id, user_id=current_user.id
    )
    if not context_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Context file not found"
        )
    
    await crud_context_files.delete_context_file(db=db, file_id=file_id)
    return {"message": "Context file deleted successfully"}

@router.get("/{file_id}/content")
async def get_context_file_content(
    file_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the text content of a context file for AI processing.
    """
    context_file = await crud_context_files.get_context_file(
        db, file_id=file_id, user_id=current_user.id
    )
    if not context_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Context file not found"
        )
    
    return {
        "file_id": file_id,
        "filename": context_file.filename,
        "content_type": context_file.content_type,
        "text_content": context_file.text_content,
        "description": context_file.description
    } 