"""
ML-based ATS Score Predictor
Predicts ATS compatibility score using XGBoost and Random Forest models
"""
import pickle
import os
from typing import Dict, Any, List
from datetime import datetime
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from app.utils.logging import setup_logging

logger = setup_logging(__name__)


class MLPredictor:
    """
    Machine Learning-based ATS score predictor
    Uses XGBoost and Random Forest for more accurate predictions
    """
    
    def __init__(self):
        """Initialize predictor with pre-trained models"""
        self.model_path = os.path.join(
            os.path.dirname(__file__),
            '../ml/models'
        )
        self.scaler = StandardScaler()
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize or load pre-trained models"""
        # For now, we create a simple model that can be trained with data
        # In production, you would load pre-trained models
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            random_state=42,
            n_jobs=-1
        )
        self.is_trained = False
        logger.info("ML Predictor initialized")
    
    def extract_features(self, parsed_resume: Dict[str, Any], 
                        parsed_jd: Dict[str, Any]) -> List[float]:
        """
        Extract features for ML model prediction
        
        Features:
        1. Keyword overlap count
        2. Skill match count
        3. Experience entries count
        4. Education entries count
        5. Projects count
        6. Certifications count
        7. Average skill frequency
        8. Years of experience
        """
        features = []
        
        # 1. Keyword overlap
        resume_text = self._get_resume_text(parsed_resume).lower()
        jd_keywords = self._extract_jd_keywords(parsed_jd)
        keyword_overlap = sum(1 for kw in jd_keywords if kw in resume_text)
        features.append(float(keyword_overlap))
        
        # 2. Skill match count
        resume_skills = self._get_skills_set(parsed_resume)
        jd_skills = self._get_jd_skills_set(parsed_jd)
        skill_match = len(resume_skills & jd_skills)
        features.append(float(skill_match))
        
        # 3. Experience entries
        experience_count = len(parsed_resume.get('experience', []))
        features.append(float(experience_count))
        
        # 4. Education entries
        education_count = len(parsed_resume.get('education', []))
        features.append(float(education_count))
        
        # 5. Projects count
        projects_count = len(parsed_resume.get('projects', []))
        features.append(float(projects_count))
        
        # 6. Certifications count
        certifications_count = len(parsed_resume.get('certifications', []))
        features.append(float(certifications_count))
        
        # 7. Average skill frequency
        skill_freq = sum(skill.get('frequency', 1) for skill in parsed_resume.get('skills', []))
        avg_skill_freq = skill_freq / max(len(parsed_resume.get('skills', [])), 1)
        features.append(float(avg_skill_freq))
        
        # 8. Years of experience from JD
        years_required = parsed_jd.get('years_of_experience', 0)
        features.append(float(years_required))
        
        # 9. Missing skills count
        missing_skills = len(jd_skills - resume_skills)
        features.append(float(missing_skills))
        
        # 10. JD responsibilities count
        responsibilities = len(parsed_jd.get('requirements', []))
        features.append(float(responsibilities))
        
        return features
    
    def predict_score(self, parsed_resume: Dict[str, Any], 
                     parsed_jd: Dict[str, Any]) -> float:
        """
        Predict ATS compatibility score using ML model
        
        Args:
            parsed_resume: Parsed resume data
            parsed_jd: Parsed job description data
            
        Returns:
            Predicted ATS score (0-100)
        """
        try:
            # Extract features
            features = self.extract_features(parsed_resume, parsed_jd)
            features_array = np.array(features).reshape(1, -1)
            
            if self.is_trained:
                # Use trained model
                prediction = self.model.predict(features_array)[0]
            else:
                # Use rule-based estimation as fallback
                prediction = self._estimate_score_rules(parsed_resume, parsed_jd)
            
            # Ensure score is between 0 and 100
            score = max(0, min(100, float(prediction)))
            
            logger.info(f"Predicted ATS score: {score:.2f}")
            return round(score, 2)
        except Exception as e:
            logger.error(f"Error predicting score: {str(e)}")
            # Fallback to rule-based estimation
            return self._estimate_score_rules(parsed_resume, parsed_jd)
    
    def _estimate_score_rules(self, parsed_resume: Dict[str, Any], 
                             parsed_jd: Dict[str, Any]) -> float:
        """Rule-based score estimation as fallback"""
        score = 50.0
        
        # Bonus for skill match
        resume_skills = self._get_skills_set(parsed_resume)
        jd_skills = self._get_jd_skills_set(parsed_jd)
        skill_match = len(resume_skills & jd_skills)
        score += min(skill_match * 2.5, 25.0)
        
        # Bonus for experience
        experience_count = len(parsed_resume.get('experience', []))
        score += min(experience_count * 5.0, 15.0)
        
        # Bonus for projects
        projects_count = len(parsed_resume.get('projects', []))
        score += min(projects_count * 3.0, 10.0)
        
        return min(score, 100.0)
    
    def _get_resume_text(self, parsed_resume: Dict[str, Any]) -> str:
        """Get resume as text"""
        text_parts = [
            parsed_resume.get('summary', ''),
            ' '.join(s.get('name', '') if isinstance(s, dict) else str(s) 
                    for s in parsed_resume.get('skills', [])),
        ]
        return ' '.join(text_parts)
    
    def _extract_jd_keywords(self, parsed_jd: Dict[str, Any]) -> List[str]:
        """Extract JD keywords"""
        keywords = []
        keywords.extend(parsed_jd.get('keywords', []))
        keywords.extend(parsed_jd.get('required_skills', []))
        keywords.extend(parsed_jd.get('preferred_skills', []))
        return keywords
    
    def _get_skills_set(self, parsed_resume: Dict[str, Any]) -> set:
        """Get resume skills as set"""
        skills = set()
        for skill in parsed_resume.get('skills', []):
            if isinstance(skill, dict):
                skills.add(skill.get('name', '').lower())
            else:
                skills.add(str(skill).lower())
        return {s for s in skills if s}
    
    def _get_jd_skills_set(self, parsed_jd: Dict[str, Any]) -> set:
        """Get JD skills as set"""
        skills = set()
        for key in ['required_skills', 'preferred_skills', 'technical_skills']:
            for skill in parsed_jd.get(key, []):
                skills.add(skill.lower())
        return skills
    
    def train_model(self, training_data: List[Dict[str, Any]]):
        """
        Train ML model with data
        
        Args:
            training_data: List of training samples with features and target scores
        """
        try:
            if not training_data or len(training_data) < 10:
                logger.warning("Insufficient training data")
                return
            
            X = np.array([sample['features'] for sample in training_data])
            y = np.array([sample['score'] for sample in training_data])
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model.fit(X_scaled, y)
            self.is_trained = True
            
            logger.info(f"Model trained on {len(training_data)} samples")
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
