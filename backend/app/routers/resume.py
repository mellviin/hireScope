"""
Resume Router
Handles resume upload, parsing, and version management
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from io import BytesIO
from app.database.session import get_db
from app.models.resume import Resume, ResumeVersion
from app.models.user import User
from app.schemas.resume import ResumeUploadResponse, ResumeResponse, ResumeVersionResponse
from app.services.resume_parser import ResumeParser
from app.services.text_extractor import ResumeTextExtractor
from app.utils.auth import get_current_user_email
from app.utils.logging import setup_logging
from app.utils.exceptions import ProcessingError
import os

logger = setup_logging(__name__)

router = APIRouter(prefix="/api/resume", tags=["Resume"])


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user_email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """
    Upload and parse a resume (PDF or DOCX)
    
    Args:
        file: Resume file (PDF or DOCX)
        current_user_email: Current user email
        db: Database session
        
    Returns:
        Parsed resume data
    """
    # Get current user
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Validate file type
        file_ext = file.filename.split('.')[-1].lower()
        if file_ext not in ['pdf', 'docx', 'doc']:
            raise ProcessingError("File type must be PDF or DOCX")
        
        # Check file size (max 10MB)
        max_size = int(os.getenv("MAX_FILE_SIZE", 10485760))
        file_content = await file.read()
        if len(file_content) > max_size:
            raise ProcessingError(f"File size exceeds {max_size} bytes")
        
        # Extract text from file
        file_obj = BytesIO(file_content)
        text = ResumeTextExtractor.extract_text(file_obj, file_ext)
        
        # Parse resume
        parser = ResumeParser()
        parsed_data = parser.parse_text(text)
        
        # Save resume to database
        resume = Resume(
            user_id=user.id,
            filename=file.filename,
            original_content=text,
            parsed_data=parsed_data,
            file_type=file_ext.lower()
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        
        logger.info(f"Resume uploaded for user {user.email}: {file.filename}")
        
        return ResumeUploadResponse(
            resume_id=resume.id,
            filename=resume.filename,
            file_type=resume.file_type,
            parsed_resume=parsed_data,
            created_at=resume.created_at
        )
    except ProcessingError as e:
        logger.error(f"Error processing resume: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error uploading resume"
        )


@router.get("/list", response_model=list[ResumeResponse])
async def list_resumes(
    current_user_email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """
    List all resumes for current user
    
    Args:
        current_user_email: Current user email
        db: Database session
        
    Returns:
        List of user's resumes
    """
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    resumes = db.query(Resume).filter(Resume.user_id == user.id).all()
    return resumes


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: int,
    current_user_email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """
    Get resume details
    
    Args:
        resume_id: Resume ID
        current_user_email: Current user email
        db: Database session
        
    Returns:
        Resume details
    """
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    resume = db.query(Resume).filter(
        (Resume.id == resume_id) & (Resume.user_id == user.id)
    ).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    return resume


@router.get("/{resume_id}/versions", response_model=list[ResumeVersionResponse])
async def get_resume_versions(
    resume_id: int,
    current_user_email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """
    Get version history for a resume
    
    Args:
        resume_id: Resume ID
        current_user_email: Current user email
        db: Database session
        
    Returns:
        List of resume versions
    """
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    resume = db.query(Resume).filter(
        (Resume.id == resume_id) & (Resume.user_id == user.id)
    ).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    versions = db.query(ResumeVersion).filter(
        ResumeVersion.resume_id == resume_id
    ).order_by(ResumeVersion.version_number.desc()).all()
    
    return versions


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: int,
    current_user_email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """
    Delete a resume
    
    Args:
        resume_id: Resume ID
        current_user_email: Current user email
        db: Database session
        
    Returns:
        Deletion confirmation
    """
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    resume = db.query(Resume).filter(
        (Resume.id == resume_id) & (Resume.user_id == user.id)
    ).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    db.delete(resume)
    db.commit()
    
    logger.info(f"Resume deleted: {resume_id}")
    
    return {"message": "Resume deleted successfully"}
