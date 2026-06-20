"""
Resume Parser Service
Extracts structured information from PDF and DOCX resumes
"""
import re
from typing import Dict, List, Optional, Any, Tuple
import spacy
from app.utils.logging import setup_logging
from app.utils.exceptions import ProcessingError

logger = setup_logging(__name__)


class ResumeParser:
    """
    Comprehensive resume parser using spaCy NER, regex patterns, and keyword matching
    """
    
    # Contact information patterns
    EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    PHONE_PATTERN = r'(?:\+1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
    LINKEDIN_PATTERN = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+'
    GITHUB_PATTERN = r'(?:https?://)?(?:www\.)?github\.com/[\w-]+'
    
    # Section headers
    SECTION_HEADERS = {
        'summary': r'(?:professional\s+)?summary|objective|profile|about',
        'experience': r'(?:professional\s+)?experience|work\s+(?:history|experience)|employment',
        'education': r'education|academic',
        'skills': r'skills|technical\s+skills|core\s+competencies',
        'projects': r'projects|portfolio|personal\s+projects',
        'certifications': r'certifications?|licenses?|credentials?',
    }
    
    # Technical skills database
    TECHNICAL_SKILLS = {
        'languages': [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby',
            'php', 'swift', 'kotlin', 'go', 'rust', 'scala', 'r', 'matlab',
            'sql', 'html', 'css', 'bash', 'shell', 'groovy', 'perl'
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
        ],
        'soft_skills': [
            'communication', 'teamwork', 'leadership', 'project management',
            'problem solving', 'analytical', 'agile', 'scrum'
        ]
    }
    
    def __init__(self):
        """Initialize parser with spaCy model"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded successfully")
        except OSError:
            logger.error("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            raise ProcessingError("NLP model not available")
    
    def parse_text(self, text: str) -> Dict[str, Any]:
        """
        Parse resume text and extract structured information
        
        Args:
            text: Resume content as string
            
        Returns:
            Dictionary with extracted resume information
        """
        try:
            # Clean text
            text = self._clean_text(text)
            
            # Extract contact information
            contact_info = self._extract_contact_info(text)
            
            # Extract sections
            sections = self._extract_sections(text)
            
            # Extract entities using spaCy
            doc = self.nlp(text)
            
            # Parse specific sections
            skills = self._extract_skills(text)
            experience = self._extract_experience(sections.get('experience', ''), doc)
            education = self._extract_education(sections.get('education', ''), doc)
            projects = self._extract_projects(sections.get('projects', ''))
            certifications = self._extract_certifications(sections.get('certifications', ''))
            
            return {
                'name': contact_info.get('name'),
                'email': contact_info.get('email'),
                'phone': contact_info.get('phone'),
                'linkedin': contact_info.get('linkedin'),
                'github': contact_info.get('github'),
                'portfolio': contact_info.get('portfolio'),
                'summary': self._clean_text(sections.get('summary', ''))[:500],
                'skills': skills,
                'experience': experience,
                'education': education,
                'projects': projects,
                'certifications': certifications,
            }
        except Exception as e:
            logger.error(f"Error parsing resume: {str(e)}")
            raise ProcessingError(f"Failed to parse resume: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep necessary ones
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        return text.strip()
    
    def _extract_contact_info(self, text: str) -> Dict[str, Optional[str]]:
        """Extract contact information"""
        contact_info = {
            'name': None,
            'email': None,
            'phone': None,
            'linkedin': None,
            'github': None,
            'portfolio': None,
        }
        
        # Extract email
        email_match = re.search(self.EMAIL_PATTERN, text)
        if email_match:
            contact_info['email'] = email_match.group(0)
        
        # Extract phone
        phone_match = re.search(self.PHONE_PATTERN, text)
        if phone_match:
            contact_info['phone'] = f"+1-{phone_match.group(1)}-{phone_match.group(2)}-{phone_match.group(3)}"
        
        # Extract LinkedIn
        linkedin_match = re.search(self.LINKEDIN_PATTERN, text, re.IGNORECASE)
        if linkedin_match:
            contact_info['linkedin'] = linkedin_match.group(0)
        
        # Extract GitHub
        github_match = re.search(self.GITHUB_PATTERN, text, re.IGNORECASE)
        if github_match:
            contact_info['github'] = github_match.group(0)
        
        # Extract name (usually first line or using spaCy NER)
        lines = text.split('\n')
        if lines:
            first_line = lines[0].strip()
            if len(first_line) < 100 and not email_match:
                contact_info['name'] = first_line
        
        return contact_info
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extract resume sections"""
        sections = {}
        text_lower = text.lower()
        
        for section_name, pattern in self.SECTION_HEADERS.items():
            # Find section header
            match = re.search(pattern, text_lower)
            if match:
                start_pos = match.start()
                
                # Find next section
                next_section_matches = [
                    re.search(p, text_lower[start_pos+1:])
                    for p in self.SECTION_HEADERS.values()
                    if p != pattern
                ]
                
                # Get end position
                end_pos = len(text)
                for next_match in next_section_matches:
                    if next_match:
                        end_pos = min(end_pos, start_pos + 1 + next_match.start())
                
                # Extract section content
                section_content = text[start_pos:end_pos]
                # Remove section header
                section_content = re.sub(pattern, '', section_content, flags=re.IGNORECASE)
                sections[section_name] = section_content.strip()
        
        return sections
    
    def _extract_skills(self, text: str) -> List[Dict[str, Any]]:
        """Extract technical and soft skills"""
        skills = []
        text_lower = text.lower()
        
        for category, skill_list in self.TECHNICAL_SKILLS.items():
            for skill in skill_list:
                if skill in text_lower:
                    # Check if skill appears in text
                    count = len(re.findall(r'\b' + re.escape(skill) + r'\b', text_lower))
                    skills.append({
                        'name': skill.title(),
                        'category': category,
                        'frequency': count
                    })
        
        # Remove duplicates and sort by frequency
        unique_skills = {}
        for skill in skills:
            if skill['name'] not in unique_skills:
                unique_skills[skill['name']] = skill
        
        skills = sorted(unique_skills.values(), key=lambda x: x['frequency'], reverse=True)
        return skills[:50]  # Limit to 50 skills
    
    def _extract_experience(self, experience_section: str, doc) -> List[Dict[str, Any]]:
        """Extract work experience"""
        experiences = []
        
        # Split by common separators
        entries = re.split(r'\n(?=\d{4}|\w+\s+\d{4}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', experience_section)
        
        for entry in entries:
            if len(entry.strip()) < 20:
                continue
            
            lines = entry.strip().split('\n')
            if lines:
                # First line usually contains title and company
                first_line = lines[0].strip()
                
                # Try to extract dates
                date_pattern = r'(\w+\s+\d{4})\s*-\s*(\w+\s+\d{4}|Present|Current)'
                date_match = re.search(date_pattern, entry)
                duration = date_match.group(0) if date_match else None
                
                # Description is usually the rest
                description = ' '.join(lines[1:]).strip()[:200]
                
                # Extract skills from description
                skills = self._extract_skills(entry)
                
                experiences.append({
                    'title': first_line,
                    'company': '',  # Try to extract from context
                    'duration': duration,
                    'description': description,
                    'skills': [s['name'] for s in skills[:5]]
                })
        
        return experiences[:10]  # Limit to 10 experiences
    
    def _extract_education(self, education_section: str, doc) -> List[Dict[str, Any]]:
        """Extract education information"""
        educations = []
        
        # Split by common separators
        entries = re.split(r'\n(?=[A-Z])', education_section)
        
        for entry in entries:
            if len(entry.strip()) < 15:
                continue
            
            # Extract degree and field
            degree_pattern = r'(Bachelor|Master|PhD|Associate|Diploma|BS|MS|BA|MA)'
            degree_match = re.search(degree_pattern, entry, re.IGNORECASE)
            
            # Extract year
            year_pattern = r'(\d{4})'
            year_match = re.search(year_pattern, entry)
            
            lines = entry.strip().split('\n')
            
            educations.append({
                'degree': degree_match.group(0) if degree_match else '',
                'field': '',  # Would need more complex parsing
                'institution': lines[0].strip() if lines else '',
                'graduation_year': int(year_match.group(0)) if year_match else None
            })
        
        return educations[:5]  # Limit to 5 educations
    
    def _extract_projects(self, projects_section: str) -> List[Dict[str, Any]]:
        """Extract projects"""
        projects = []
        
        # Split by common separators
        entries = re.split(r'\n(?=[A-Z][a-z])', projects_section)
        
        for entry in entries:
            if len(entry.strip()) < 20:
                continue
            
            lines = entry.strip().split('\n')
            if lines:
                project_name = lines[0].strip()
                description = ' '.join(lines[1:]).strip()[:150]
                
                # Extract technologies
                tech_pattern = r'(\w+)(?:\s+|,|;)'
                tech_matches = re.findall(tech_pattern, description)
                technologies = list(set(tech_matches))[:10]
                
                projects.append({
                    'title': project_name,
                    'description': description,
                    'technologies': technologies,
                    'url': None
                })
        
        return projects[:5]  # Limit to 5 projects
    
    def _extract_certifications(self, certifications_section: str) -> List[Dict[str, Any]]:
        """Extract certifications"""
        certifications = []
        
        # Split by lines
        entries = [line.strip() for line in certifications_section.split('\n') if line.strip()]
        
        for entry in entries:
            # Extract year
            year_pattern = r'(\d{4})'
            year_match = re.search(year_pattern, entry)
            
            certifications.append({
                'name': entry,
                'issuer': '',
                'date_obtained': year_match.group(0) if year_match else None,
                'credential_url': None
            })
        
        return certifications[:10]  # Limit to 10 certifications
