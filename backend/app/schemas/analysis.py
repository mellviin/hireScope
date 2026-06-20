"""
Pydantic schemas for match and analysis results
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class MatchRequest(BaseModel):
    """Match request schema"""
    resume_id: int
    job_description_id: int


class StrengthArea(BaseModel):
    """Strength area in match"""
    category: str
    details: List[str]
    score: float = Field(0, ge=0, le=100)


class MissingSkill(BaseModel):
    """Missing skill item"""
    skill: str
    category: str
    priority: int = Field(1, ge=1, le=5)
    suggested_resources: Optional[List[str]] = None


class Recommendation(BaseModel):
    """Resume improvement recommendation"""
    category: str
    suggestion: str
    priority: int = Field(1, ge=1, le=5)
    reason: Optional[str] = None


class ScoreBreakdownItem(BaseModel):
    """Weighted score contribution"""
    category: str
    label: Optional[str] = None
    score: float = Field(0, ge=0, le=100)
    weight_percent: Optional[float] = None
    weighted_contribution: Optional[float] = None


class ReportMeta(BaseModel):
    """Context for the resume vs JD analysis report"""
    resume_id: int
    resume_filename: str
    job_description_id: int
    job_title: str
    company: Optional[str] = None
    overall_resume_score: float = Field(..., ge=0, le=100)
    score_verdict: str
    generated_at: str


class SkillEvidenceSection(BaseModel):
    """Evidence of a skill in a resume section"""
    section: str
    label: Optional[str] = None
    count: int = 0
    snippet: Optional[str] = None


class SkillEvidenceItem(BaseModel):
    """Single row in the skill evidence matrix"""
    skill: str
    category: str
    found: bool
    found_in_resume: str
    occurrences: int = 0
    match_type: str
    evidence: List[SkillEvidenceSection] = Field(default_factory=list)
    evidence_summary: str = "-"


class matchResult(BaseModel):
    """Match result schema"""
    ats_score: float = Field(..., ge=0, le=100)
    required_skills_match: Optional[float] = None
    preferred_skills_match: Optional[float] = None
    experience_match: Optional[float] = None
    education_match: Optional[float] = None
    projects_match: Optional[float] = None
    keyword_coverage: Optional[float] = None
    responsibility_alignment: Optional[float] = None
    strengths: List[StrengthArea] = Field(default_factory=list)
    missing_skills: List[MissingSkill] = Field(default_factory=list)
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    keyword_density: Dict[str, int] = Field(default_factory=dict)
    recommendations: List[Recommendation] = Field(default_factory=list)
    skill_breakdown: Optional[Dict[str, Any]] = None
    score_breakdown: Optional[List[Dict[str, Any]]] = None
    experience_analysis: Optional[Dict[str, Any]] = None
    projects_analysis: Optional[Dict[str, Any]] = None
    education_analysis: Optional[Dict[str, Any]] = None
    responsibility_analysis: Optional[Dict[str, Any]] = None
    keyword_analysis: Optional[Dict[str, Any]] = None
    keyword_enhancement: Optional[Dict[str, Any]] = None
    skill_evidence_matrix: List[SkillEvidenceItem] = Field(default_factory=list)
    report_meta: Optional[ReportMeta] = None


class matchResultResponse(BaseModel):
    """Match result response"""
    id: int
    resume_id: int
    job_description_id: int
    ats_score: float
    strengths: Optional[List[Dict[str, Any]]] = None
    missing_skills: Optional[List[Dict[str, Any]]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PriorityArea(BaseModel):
    """Priority improvement area"""
    area: str
    impact: str
    details: str
    action: str


class GapAnalysisResponse(BaseModel):
    """Gap analysis response"""
    critical_missing_skills: List[MissingSkill] = Field(default_factory=list)
    recommended_skills: List[str] = Field(default_factory=list)
    matched_skills: List[str] = Field(default_factory=list)
    partial_skills: List[str] = Field(default_factory=list)
    education_gap: List[str] = Field(default_factory=list)
    experience_gap: str = ""
    keyword_gaps: List[str] = Field(default_factory=list)
    responsibility_gaps: List[str] = Field(default_factory=list)
    priority_areas: List[Dict[str, Any]] = Field(default_factory=list)
    keyword_enhancement: Optional[Dict[str, Any]] = None


class OptimizationSuggestion(BaseModel):
    """Optimization suggestion"""
    category: str
    suggestion: str
    reason: str
    impact: str = "medium"


class OptimizationResponse(BaseModel):
    """Resume optimization response"""
    summary_suggestions: List[OptimizationSuggestion] = Field(default_factory=list)
    experience_suggestions: List[OptimizationSuggestion] = Field(default_factory=list)
    project_suggestions: List[OptimizationSuggestion] = Field(default_factory=list)
    skills_to_add: List[str] = Field(default_factory=list)
    overall_improvement_potential: float = Field(0, ge=0, le=100)
