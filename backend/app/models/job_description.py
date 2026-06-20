"""
Job Description database model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base


class JobDescription(Base):
    """Job Description model for storing and analyzing job postings"""
    
    __tablename__ = "job_descriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    parsed_data = Column(JSON, nullable=True)
    job_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="job_descriptions")
    match_results = relationship("matchResult", back_populates="job_description", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<JobDescription(id={self.id}, job_title={self.job_title}, user_id={self.user_id})>"
