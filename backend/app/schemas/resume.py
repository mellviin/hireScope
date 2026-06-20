"""
Pydantic schemas for resume and analysis
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class SkillItem(BaseModel):
    """Individual skill item"""
    name: str
    proficiency: Optional[str] = None
    years: Optional[float] = None


class ExperienceItem(BaseModel):
    """Individual experience item"""
    title: str
    company: str
    duration: Optional[str] = None
    description: Optional[str] = None
    skills: Optional[List[str]] = None


class EducationItem(BaseModel):
    """Individual education item"""
    degree: str
    field: str
    institution: str
    graduation_year: Optional[int] = None


class ProjectItem(BaseModel):
    """Individual project item"""
    title: str
    description: str
    technologies: Optional[List[str]] = None
    url: Optional[str] = None


class CertificationItem(BaseModel):
    """Individual certification item"""
    name: str
    issuer: str
    date_obtained: Optional[str] = None
    credential_url: Optional[str] = None


class ParsedResume(BaseModel):
    """Parsed resume data"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    summary: Optional[str] = None
    skills: List[SkillItem] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    certifications: List[CertificationItem] = Field(default_factory=list)


class ResumeUploadResponse(BaseModel):
    """Resume upload response"""
    resume_id: int
    filename: str
    file_type: str
    parsed_resume: ParsedResume
    created_at: datetime
    
    class Config:
        from_attributes = True


class ResumeResponse(BaseModel):
    """Resume response schema"""
    id: int
    filename: str
    file_type: str
    parsed_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ResumeVersionResponse(BaseModel):
    """Resume version response"""
    id: int
    version_number: int
    ats_score: Optional[int] = None
    change_description: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
