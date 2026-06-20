"""
Match Result database model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.database.session import Base


class matchResult(Base):
    """Match Result model for storing ATS compatibility analysis results"""
    
    __tablename__ = "match_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Scoring
    ats_score = Column(Float, nullable=False)
    required_skills_match = Column(Float, nullable=True)
    preferred_skills_match = Column(Float, nullable=True)
    experience_match = Column(Float, nullable=True)
    education_match = Column(Float, nullable=True)
    
    # Analysis Data
    strengths = Column(JSON, nullable=True)  # List of strength areas
    missing_skills = Column(JSON, nullable=True)  # List of missing skills
    matched_keywords = Column(JSON, nullable=True)  # Matched keywords
    keyword_density = Column(JSON, nullable=True)  # Keyword frequency
    recommendations = Column(JSON, nullable=True)  # Improvement suggestions
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="match_results")
    resume = relationship("Resume", back_populates="match_results")
    job_description = relationship("JobDescription", back_populates="match_results")
    
    def __repr__(self):
        return f"<matchResult(id={self.id}, resume_id={self.resume_id}, jd_id={self.job_description_id}, score={self.ats_score})>"
