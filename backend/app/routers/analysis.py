"""
Analysis Router
Handles ATS matching, gap analysis, and optimization
"""
import re
from io import BytesIO
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User
from app.models.resume import Resume
from app.models.job_description import JobDescription
from app.models.match_result import matchResult
from app.schemas.analysis import (
    MatchRequest, matchResult as matchResultSchema,
    GapAnalysisResponse, OptimizationResponse
)
from app.services.match_engine import ATSMatchEngine
from app.services.resume_optimizer import ResumeOptimizer
from app.services.ats_report_exporter import ATSReportExporter, score_verdict
from app.ml.predictor import MLPredictor
from app.utils.auth import get_current_user_email
from app.utils.logging import setup_logging

logger = setup_logging(__name__)

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


def _get_match_context(
    match_request: MatchRequest,
    current_user_email: str,
    db: Session,
) -> tuple[User, Resume, JobDescription]:
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    resume = db.query(Resume).filter(
        (Resume.id == match_request.resume_id) & (Resume.user_id == user.id)
    ).first()
    jd = db.query(JobDescription).filter(
        (JobDescription.id == match_request.job_description_id) &
        (JobDescription.user_id == user.id)
    ).first()

    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    if not jd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found")

    return user, resume, jd


def _run_match_analysis(resume: Resume, jd: JobDescription) -> dict:
    match_engine = ATSMatchEngine()
    match_result = match_engine.calculate_match(
        resume.parsed_data or {},
        jd.parsed_data or {},
    )

    ml_predictor = MLPredictor()
    ml_score = ml_predictor.predict_score(
        resume.parsed_data or {},
        jd.parsed_data or {},
    )
    final_score = (match_result['ats_score'] * 0.7) + (ml_score * 0.3)
    match_result['ats_score'] = round(final_score, 2)

    match_result['report_meta'] = {
        'resume_id': resume.id,
        'resume_filename': resume.filename,
        'job_description_id': jd.id,
        'job_title': jd.job_title,
        'company': jd.company,
        'overall_resume_score': match_result['ats_score'],
        'score_verdict': score_verdict(match_result['ats_score']),
        'generated_at': datetime.utcnow().isoformat() + 'Z',
    }
    return match_result


@router.post("/match", response_model=matchResultSchema)
async def calculate_match(
    match_request: MatchRequest,
    current_user_email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """
    Calculate ATS compatibility between resume and job description
    
    Args:
        match_request: Match request with resume and JD IDs
        current_user_email: Current user email
        db: Database session
        
    Returns:
        Detailed match analysis
    """
    try:
        user, resume, jd = _get_match_context(match_request, current_user_email, db)
        match_result = _run_match_analysis(resume, jd)

        db_match_result = matchResult(
            user_id=user.id,
            resume_id=resume.id,
            job_description_id=jd.id,
            ats_score=match_result['ats_score'],
            required_skills_match=match_result.get('required_skills_match'),
            preferred_skills_match=match_result.get('preferred_skills_match'),
            experience_match=match_result.get('experience_match'),
            education_match=match_result.get('education_match'),
            strengths=match_result.get('strengths'),
            missing_skills=match_result.get('missing_skills'),
            matched_keywords=match_result.get('matched_keywords'),
            keyword_density=match_result.get('keyword_density'),
            recommendations=match_result.get('recommendations'),
        )
        db.add(db_match_result)
        db.commit()
        
        logger.info(f"Match calculated for user {user.email}: {match_result['ats_score']}")
        
        return match_result
    except Exception as e:
        logger.error(f"Error calculating match: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating match: {str(e)}"
        )


@router.post("/gap-analysis")
async def analyze_gaps(
    match_request: MatchRequest,
    current_user_email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """
    Analyze skill gaps between resume and job description
    
    Args:
        match_request: Match request with resume and JD IDs
        current_user_email: Current user email
        db: Database session
        
    Returns:
        Gap analysis results
    """
    # Get current user
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get resume and job description
    resume = db.query(Resume).filter(
        (Resume.id == match_request.resume_id) & (Resume.user_id == user.id)
    ).first()
    
    jd = db.query(JobDescription).filter(
        (JobDescription.id == match_request.job_description_id) & 
        (JobDescription.user_id == user.id)
    ).first()
    
    if not resume or not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume or Job description not found"
        )
    
    try:
        match_engine = ATSMatchEngine()
        match_result = match_engine.calculate_match(
            resume.parsed_data or {},
            jd.parsed_data or {}
        )

        gap_data = match_engine.build_gap_analysis(
            match_result,
            resume.parsed_data or {},
            jd.parsed_data or {},
        )

        gap_analysis = GapAnalysisResponse(**gap_data)
        
        logger.info(f"Gap analysis completed for user {user.email}")
        
        return gap_analysis
    except Exception as e:
        logger.error(f"Error analyzing gaps: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error analyzing gaps"
        )


@router.post("/optimize")
async def get_optimization_suggestions(
    match_request: MatchRequest,
    current_user_email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """
    Get resume optimization suggestions
    
    Args:
        match_request: Match request with resume and JD IDs
        current_user_email: Current user email
        db: Database session
        
    Returns:
        Optimization suggestions
    """
    # Get current user
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get resume and job description
    resume = db.query(Resume).filter(
        (Resume.id == match_request.resume_id) & (Resume.user_id == user.id)
    ).first()
    
    jd = db.query(JobDescription).filter(
        (JobDescription.id == match_request.job_description_id) & 
        (JobDescription.user_id == user.id)
    ).first()
    
    if not resume or not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume or Job description not found"
        )
    
    try:
        # Get optimization suggestions
        optimizer = ResumeOptimizer()
        suggestions = optimizer.generate_optimization_suggestions(
            resume.parsed_data or {},
            jd.parsed_data or {}
        )
        
        logger.info(f"Optimization suggestions generated for user {user.email}")
        
        return OptimizationResponse(**suggestions)
    except Exception as e:
        logger.error(f"Error generating suggestions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating suggestions"
        )


@router.get("/history")
async def get_match_history(
    current_user_email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db),
    limit: int = 20
):
    """
    Get match analysis history for current user
    
    Args:
        current_user_email: Current user email
        db: Database session
        limit: Number of results to return
        
    Returns:
        Match history
    """
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    results = db.query(matchResult).filter(
        matchResult.user_id == user.id
    ).order_by(matchResult.created_at.desc()).limit(limit).all()
    
    return results


@router.post("/report/download")
async def download_ats_report(
    match_request: MatchRequest,
    current_user_email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db),
):
    """Generate and download a PDF ATS compatibility report for resume vs JD."""
    try:
        _, resume, jd = _get_match_context(match_request, current_user_email, db)
        match_result = _run_match_analysis(resume, jd)

        match_engine = ATSMatchEngine()
        gap_data = match_engine.build_gap_analysis(
            match_result,
            resume.parsed_data or {},
            jd.parsed_data or {},
        )

        optimizer = ResumeOptimizer()
        optimization = optimizer.generate_optimization_suggestions(
            resume.parsed_data or {},
            jd.parsed_data or {},
        )

        exporter = ATSReportExporter()
        report_bytes = exporter.generate_report(
            match_result=match_result,
            gap_analysis=gap_data,
            optimization=optimization,
            resume_filename=resume.filename,
            job_title=jd.job_title,
            company=jd.company,
        )

        safe_name = re.sub(r'[^\w\-]', '_', f"{resume.filename}_{jd.job_title}")[:80]
        filename = f"ATS_Report_{safe_name}.pdf"

        logger.info(f"ATS report downloaded for {current_user_email}: {filename}")

        return StreamingResponse(
            BytesIO(report_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating ATS report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating ATS report",
        )
