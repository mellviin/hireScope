"""
Pydantic schemas for job description and analysis
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class JobRequirement(BaseModel):
    """Individual job requirement"""
    requirement: str
    category: str  # required, preferred, nice_to_have
    priority: int = Field(1, ge=1, le=5)


class ParsedJobDescription(BaseModel):
    """Parsed job description data"""
    job_title: str
    company: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    requirements: List[JobRequirement] = Field(default_factory=list)
    experience_level: Optional[str] = None
    years_of_experience: Optional[int] = None
    education_requirements: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    salary_range: Optional[str] = None
    job_type: Optional[str] = None


class JobDescriptionInput(BaseModel):
    """Job description input"""
    job_title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=10)
    company: Optional[str] = None
    job_url: Optional[str] = None


class JobDescriptionResponse(BaseModel):
    """Job description response"""
    id: int
    job_title: str
    company: Optional[str] = None
    parsed_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
