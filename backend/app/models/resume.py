"""
Resume database models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base


class Resume(Base):
    """Resume model for storing uploaded resumes"""
    
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    original_content = Column(Text, nullable=False)
    parsed_data = Column(JSON, nullable=True)
    file_type = Column(String(10), nullable=False)  # pdf, docx
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="resumes")
    versions = relationship("ResumeVersion", back_populates="resume", cascade="all, delete-orphan")
    match_results = relationship("matchResult", back_populates="resume", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Resume(id={self.id}, filename={self.filename}, user_id={self.user_id})>"


class ResumeVersion(Base):
    """Resume version model for tracking resume improvements"""
    
    __tablename__ = "resume_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    parsed_data = Column(JSON, nullable=True)
    ats_score = Column(Integer, nullable=True)
    change_description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    resume = relationship("Resume", back_populates="versions")
    
    def __repr__(self):
        return f"<ResumeVersion(id={self.id}, resume_id={self.resume_id}, version={self.version_number})>"
