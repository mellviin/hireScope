"""
Job Description Analyzer Service
Converts raw job descriptions into structured schemas using NLP and rule-based extraction
"""
import re
from typing import Dict, List, Optional, Any
from collections import Counter
import spacy
from app.utils.logging import setup_logging
from app.utils.exceptions import ProcessingError

logger = setup_logging(__name__)


class JDAnalyzer:
    """
    Job Description Analyzer using spaCy, regex patterns, and keyword extraction
    """
    
    # Keywords indicating required skills
    REQUIRED_KEYWORDS = ['required', 'must have', 'essential', 'mandatory', 'required skills', 'need']
    
    # Keywords indicating preferred skills
    PREFERRED_KEYWORDS = ['preferred', 'nice to have', 'bonus', 'desirable', 'preferred skills']
    
    # Experience level indicators
    EXPERIENCE_LEVELS = {
        'entry': r'entry\s*(?:level|position)|junior|fresh\s*(?:graduate|pass)',
        'mid': r'mid\s*(?:level|career)|intermediate|3\s*-\s*5\s+years?',
        'senior': r'senior|lead|principal|5\s*-\s*10\s+years?|10\+\s+years?',
        'executive': r'executive|director|c-suite|vp|vice\s+president'
    }
    
    # Technical skills
    TECHNICAL_SKILLS = {
        'languages': [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby',
            'php', 'swift', 'kotlin', 'go', 'rust', 'scala', 'r', 'matlab',
            'sql', 'html', 'css', 'bash', 'shell', 'groovy'
        ],
        'frameworks': [
            'spring', 'spring boot', 'django', 'flask', 'fastapi', 'nodejs',
            'express', 'react', 'angular', 'vue', 'asp.net', 'rails', 'laravel',
            'kubernetes', 'docker', 'kafka', 'spark', 'hadoop'
        ],
        'databases': [
            'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
            'cassandra', 'dynamodb', 'oracle', 'sql server', 'sqlite'
        ],
        'cloud': [
            'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'digital ocean'
        ],
        'devops': [
            'docker', 'kubernetes', 'jenkins', 'gitlab', 'github', 'circleci',
            'terraform', 'ansible', 'cloudformation'
        ]
    }
    
    # Soft skills
    SOFT_SKILLS = [
        'communication', 'teamwork', 'leadership', 'project management',
        'problem solving', 'analytical', 'agile', 'scrum', 'initiative',
        'organization', 'attention to detail'
    ]
    
    def __init__(self):
        """Initialize analyzer with spaCy model"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded successfully")
        except OSError:
            logger.error("spaCy model not found")
            raise ProcessingError("NLP model not available")
    
    def analyze_jd(self, job_title: str, content: str, company: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze job description and extract structured information
        
        Args:
            job_title: Job title
            content: Job description content
            company: Company name (optional)
            
        Returns:
            Dictionary with extracted job description information
        """
        try:
            # Clean text
            content = self._clean_text(content)
            
            # Extract required and preferred skills
            required_skills, preferred_skills = self._extract_skills(content)
            
            # Extract all technical skills mentioned
            tech_skills = self._extract_technical_skills(content)
            
            # Extract soft skills
            soft_skills = self._extract_soft_skills(content)
            
            # Extract responsibilities
            responsibilities = self._extract_responsibilities(content)
            
            # Extract requirements
            requirements = self._extract_requirements(content)
            
            # Detect experience level
            experience_level = self._detect_experience_level(content)
            
            # Extract years of experience
            years_of_experience = self._extract_years_of_experience(content)
            
            # Extract education requirements
            education_requirements = self._extract_education_requirements(content)
            
            # Extract keywords using TF-IDF like approach
            keywords = self._extract_keywords(content)
            
            return {
                'job_title': job_title,
                'company': company,
                'required_skills': required_skills,
                'preferred_skills': preferred_skills,
                'technical_skills': tech_skills,
                'soft_skills': soft_skills,
                'responsibilities': responsibilities,
                'requirements': requirements,
                'experience_level': experience_level,
                'years_of_experience': years_of_experience,
                'education_requirements': education_requirements,
                'keywords': keywords,
            }
        except Exception as e:
            logger.error(f"Error analyzing job description: {str(e)}")
            raise ProcessingError(f"Failed to analyze job description: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep necessary ones
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        return text.strip()
    
    def _extract_skills(self, content: str) -> tuple:
        """Extract required and preferred skills"""
        required_skills = []
        preferred_skills = []
        content_lower = content.lower()
        
        # Find required skills section
        for keyword in self.REQUIRED_KEYWORDS:
            pattern = rf'{keyword}.*?(?=\n|$)'
            matches = re.finditer(pattern, content_lower, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                section = match.group(0)
                # Extract skill-like phrases
                skills = self._extract_skill_phrases(section)
                required_skills.extend(skills)
        
        # Find preferred skills section
        for keyword in self.PREFERRED_KEYWORDS:
            pattern = rf'{keyword}.*?(?=\n|$)'
            matches = re.finditer(pattern, content_lower, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                section = match.group(0)
                skills = self._extract_skill_phrases(section)
                preferred_skills.extend(skills)
        
        # Remove duplicates while preserving order
        required_skills = list(dict.fromkeys(required_skills))
        preferred_skills = list(dict.fromkeys([s for s in preferred_skills if s not in required_skills]))
        
        return required_skills[:20], preferred_skills[:20]
    
    def _extract_skill_phrases(self, text: str) -> List[str]:
        """Extract skill phrases from text"""
        skills = []
        
        # Split by common delimiters
        items = re.split(r'[,;•-]', text)
        
        for item in items:
            item = item.strip()
            # Keep items that are 2-50 characters and look like skills
            if 2 <= len(item) <= 50 and not item[0].isdigit():
                # Clean up the item
                item = re.sub(r'^(and|or|the|a|an)\s+', '', item, flags=re.IGNORECASE)
                item = re.sub(r'\s+(and|or|the|a|an)$', '', item, flags=re.IGNORECASE)
                if item and len(item) > 2:
                    skills.append(item.capitalize())
        
        return skills
    
    def _extract_technical_skills(self, content: str) -> List[str]:
        """Extract technical skills from content"""
        skills = []
        content_lower = content.lower()
        
        for category, skill_list in self.TECHNICAL_SKILLS.items():
            for skill in skill_list:
                if re.search(r'\b' + re.escape(skill) + r'\b', content_lower):
                    skills.append(skill.title())
        
        return list(dict.fromkeys(skills))  # Remove duplicates
    
    def _extract_soft_skills(self, content: str) -> List[str]:
        """Extract soft skills from content"""
        skills = []
        content_lower = content.lower()
        
        for skill in self.SOFT_SKILLS:
            if re.search(r'\b' + re.escape(skill) + r'\b', content_lower):
                skills.append(skill.title())
        
        return list(dict.fromkeys(skills))
    
    def _extract_responsibilities(self, content: str) -> List[str]:
        """Extract job responsibilities"""
        responsibilities = []
        
        # Look for bullet points or numbered lists
        patterns = [
            r'[•*-]\s*([^•*\n-][^\n]+)',
            r'^\d+\.\s+([^\n]+)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                resp = match.group(1).strip()
                if 10 < len(resp) < 300:
                    responsibilities.append(resp)
        
        # Remove duplicates
        responsibilities = list(dict.fromkeys(responsibilities))
        return responsibilities[:10]  # Return top 10
    
    def _extract_requirements(self, content: str) -> List[Dict[str, Any]]:
        """Extract job requirements"""
        requirements = []
        
        # Look for requirements section
        req_match = re.search(r'requirements?.*?(?=\n\n|\nwhat|$)', content, re.IGNORECASE | re.DOTALL)
        
        if req_match:
            req_section = req_match.group(0)
            
            # Extract bullet points
            items = re.findall(r'[•*-]\s*([^\n•*-]+)', req_section)
            
            for item in items:
                item = item.strip()
                if 5 < len(item) < 200:
                    requirements.append({
                        'requirement': item,
                        'category': 'general',
                        'priority': 2
                    })
        
        return requirements[:15]
    
    def _detect_experience_level(self, content: str) -> str:
        """Detect job experience level"""
        content_lower = content.lower()
        
        for level, pattern in self.EXPERIENCE_LEVELS.items():
            if re.search(pattern, content_lower):
                return level
        
        return 'mid'  # Default to mid-level
    
    def _extract_years_of_experience(self, content: str) -> Optional[int]:
        """Extract required years of experience"""
        # Look for patterns like "5 years", "5+ years", "3-5 years"
        patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)',
            r'(\d+)\s*-\s*(\d+)\s*(?:years?|yrs?)',
        ]
        
        matches = []
        for pattern in patterns:
            found = re.search(pattern, content, re.IGNORECASE)
            if found:
                if len(found.groups()) == 2 and found.group(2):
                    # Range: take the lower value
                    matches.append(int(found.group(1)))
                else:
                    matches.append(int(found.group(1)))
        
        return min(matches) if matches else None
    
    def _extract_education_requirements(self, content: str) -> List[str]:
        """Extract education requirements"""
        education = []
        
        # Look for education-related keywords
        edu_keywords = {
            'Bachelor': r"Bachelor('s)?|B\.?S\.?|B\.?A\.?",
            'Master': r"Master('s)?|M\.?S\.?|M\.?B\.?A\.?",
            'PhD': r'PhD|Ph\.D\.|Doctorate',
            'Associates': r"Associate('s)?|A\.?S\.?",
            'High School': r'High School|GED|Secondary',
        }
        
        content_lower = content.lower()
        
        for degree, pattern in edu_keywords.items():
            if re.search(pattern, content, re.IGNORECASE):
                education.append(degree)
        
        return education
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract important keywords from JD"""
        # Process with spaCy
        doc = self.nlp(content[:5000])  # Limit to first 5000 chars for performance
        
        # Extract noun chunks and named entities
        keywords = []
        
        # Noun chunks
        for chunk in doc.noun_chunks:
            if 2 <= len(chunk.text.split()) <= 3 and len(chunk.text) > 3:
                keywords.append(chunk.text.lower())
        
        # Named entities
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PRODUCT', 'GPE']:
                keywords.append(ent.text.lower())
        
        # Count and get top keywords
        keyword_counts = Counter(keywords)
        top_keywords = [kw for kw, count in keyword_counts.most_common(15)]
        
        return top_keywords
