"""
Job Description Router
Handles job description submission and analysis
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.job_description import JobDescription
from app.models.user import User
from app.schemas.job_description import JobDescriptionInput, JobDescriptionResponse, ParsedJobDescription
from app.services.jd_analyzer import JDAnalyzer
from app.utils.auth import get_current_user_email
from app.utils.logging import setup_logging
from app.utils.exceptions import ProcessingError

logger = setup_logging(__name__)

router = APIRouter(prefix="/api/jd", tags=["Job Description"])


@router.post("/analyze", response_model=JobDescriptionResponse)
async def analyze_job_description(
    jd_input: JobDescriptionInput,
    current_user_email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """
    Submit and analyze a job description
    
    Args:
        jd_input: Job description input
        current_user_email: Current user email
        db: Database session
        
    Returns:
        Analyzed job description
    """
    # Get current user
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Analyze job description
        analyzer = JDAnalyzer()
        parsed_data = analyzer.analyze_jd(
            job_title=jd_input.job_title,
            content=jd_input.content,
            company=jd_input.company
        )
        
        # Save to database
        jd = JobDescription(
            user_id=user.id,
            job_title=jd_input.job_title,
            company=jd_input.company,
            content=jd_input.content,
            job_url=jd_input.job_url,
            parsed_data=parsed_data
        )
        db.add(jd)
        db.commit()
        db.refresh(jd)
        
        logger.info(f"Job description analyzed for user {user.email}: {jd_input.job_title}")
        
        return jd
    except ProcessingError as e:
        logger.error(f"Error analyzing JD: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing JD: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error analyzing job description"
        )


@router.get("/list", response_model=list[JobDescriptionResponse])
async def list_job_descriptions(
    current_user_email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """
    List all job descriptions for current user
    
    Args:
        current_user_email: Current user email
        db: Database session
        
    Returns:
        List of user's job descriptions
    """
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    jds = db.query(JobDescription).filter(JobDescription.user_id == user.id).all()
    return jds


@router.get("/{jd_id}", response_model=JobDescriptionResponse)
async def get_job_description(
    jd_id: int,
    current_user_email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """
    Get job description details
    
    Args:
        jd_id: Job description ID
        current_user_email: Current user email
        db: Database session
        
    Returns:
        Job description details
    """
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    jd = db.query(JobDescription).filter(
        (JobDescription.id == jd_id) & (JobDescription.user_id == user.id)
    ).first()
    
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found"
        )
    
    return jd


@router.delete("/{jd_id}")
async def delete_job_description(
    jd_id: int,
    current_user_email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """
    Delete a job description
    
    Args:
        jd_id: Job description ID
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
    
    jd = db.query(JobDescription).filter(
        (JobDescription.id == jd_id) & (JobDescription.user_id == user.id)
    ).first()
    
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found"
        )
    
    db.delete(jd)
    db.commit()
    
    logger.info(f"Job description deleted: {jd_id}")
    
    return {"message": "Job description deleted successfully"}
