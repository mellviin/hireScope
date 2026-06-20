"""
Resume Optimizer Service
Generates ATS-friendly suggestions using rule-based templates and analysis
"""
from typing import Dict, List, Any, Set
from app.utils.logging import setup_logging
from app.utils.exceptions import ProcessingError
import json
import os

logger = setup_logging(__name__)


class ResumeOptimizer:
    """
    Rule-based resume optimizer that generates suggestions without hallucination
    """
    
    def __init__(self):
        """Initialize optimizer with skill templates"""
        self.skill_templates = self._load_skill_templates()
    
    def _load_skill_templates(self) -> Dict[str, List[str]]:
        """Load skill templates from JSON file"""
        try:
            template_path = os.path.join(
                os.path.dirname(__file__),
                '../data/skill_templates.json'
            )
            
            if os.path.exists(template_path):
                with open(template_path, 'r') as f:
                    return json.load(f)
            
            # Return default templates if file doesn't exist
            return self._get_default_templates()
        except Exception as e:
            logger.warning(f"Could not load skill templates: {str(e)}")
            return self._get_default_templates()
    
    def _get_default_templates(self) -> Dict[str, List[str]]:
        """Get default skill templates"""
        return {
            'python': [
                'Developed backend services using Python with clean, maintainable code',
                'Built data processing pipelines in Python using Pandas and NumPy',
                'Created automation scripts to improve team productivity',
                'Implemented RESTful APIs using Python frameworks'
            ],
            'java': [
                'Developed scalable Java applications following object-oriented design principles',
                'Built enterprise applications using Java and Spring Framework',
                'Implemented efficient algorithms and data structures in Java',
                'Designed microservices architecture using Java'
            ],
            'javascript': [
                'Built interactive web applications using JavaScript and modern frameworks',
                'Developed frontend components with responsive design',
                'Implemented complex client-side logic and state management',
                'Created real-time applications using JavaScript'
            ],
            'react': [
                'Built responsive web interfaces using React and component-based architecture',
                'Managed complex application state using Redux or Context API',
                'Optimized React applications for performance and scalability',
                'Implemented modern UI components with React best practices'
            ],
            'sql': [
                'Designed and optimized complex database queries',
                'Created normalized database schemas for efficient data retrieval',
                'Implemented database indexing strategies for performance',
                'Managed relational databases with SQL'
            ],
            'aws': [
                'Deployed applications on AWS cloud infrastructure',
                'Configured AWS services for scalability and reliability',
                'Implemented CI/CD pipelines using AWS services',
                'Managed cloud resources and optimized costs'
            ],
            'docker': [
                'Containerized applications using Docker for consistent deployment',
                'Created Docker images and pushed to registries',
                'Orchestrated containers using Docker Compose',
                'Implemented containerization best practices'
            ],
            'kubernetes': [
                'Deployed and managed applications on Kubernetes clusters',
                'Configured Kubernetes manifests for production environments',
                'Implemented auto-scaling and load balancing strategies',
                'Managed container orchestration at scale'
            ]
        }
    
    def generate_optimization_suggestions(self, parsed_resume: Dict[str, Any], 
                                        parsed_jd: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate optimization suggestions based on resume and JD analysis
        
        Args:
            parsed_resume: Parsed resume data
            parsed_jd: Parsed job description data
            
        Returns:
            Dictionary with optimization suggestions
        """
        try:
            # Extract resume and JD data
            resume_skills = self._get_resume_skills_set(parsed_resume)
            jd_all_skills = self._get_jd_skills_set(parsed_jd)
            missing_skills = jd_all_skills - resume_skills
            
            # Generate suggestions
            summary_suggestions = self._suggest_summary_improvements(parsed_resume, parsed_jd)
            experience_suggestions = self._suggest_experience_improvements(parsed_resume, jd_all_skills)
            project_suggestions = self._suggest_project_improvements(parsed_resume, missing_skills)
            skills_to_add = list(missing_skills)[:10]
            
            # Calculate overall improvement potential
            improvement_potential = self._calculate_improvement_potential(
                parsed_resume, parsed_jd, missing_skills
            )
            
            return {
                'summary_suggestions': summary_suggestions,
                'experience_suggestions': experience_suggestions,
                'project_suggestions': project_suggestions,
                'skills_to_add': skills_to_add,
                'overall_improvement_potential': improvement_potential,
            }
        except Exception as e:
            logger.error(f"Error generating suggestions: {str(e)}")
            raise ProcessingError(f"Failed to generate suggestions: {str(e)}")
    
    def _get_resume_skills_set(self, parsed_resume: Dict[str, Any]) -> Set[str]:
        """Extract all skills from resume as set"""
        skills = set()
        
        if parsed_resume.get('skills'):
            for skill in parsed_resume['skills']:
                if isinstance(skill, dict):
                    skills.add(skill.get('name', '').lower())
                else:
                    skills.add(str(skill).lower())
        
        return {s for s in skills if s}
    
    def _get_jd_skills_set(self, parsed_jd: Dict[str, Any]) -> Set[str]:
        """Extract all skills from JD as set"""
        skills = set()
        
        for key in ['required_skills', 'preferred_skills', 'technical_skills']:
            if parsed_jd.get(key):
                for skill in parsed_jd[key]:
                    skills.add(skill.lower())
        
        return skills
    
    def _suggest_summary_improvements(self, parsed_resume: Dict[str, Any], 
                                     parsed_jd: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate summary section improvement suggestions"""
        suggestions = []
        
        summary = parsed_resume.get('summary', '')
        jd_title = parsed_jd.get('job_title', '')
        
        if not summary or len(summary) < 50:
            suggestions.append({
                'category': 'summary',
                'suggestion': 'Add a professional summary (50-100 words) highlighting relevant skills and experience',
                'reason': 'A strong summary helps ATS and recruiters quickly understand your fit for the role',
                'impact': 'high'
            })
        
        if jd_title and jd_title.lower() not in summary.lower():
            suggestions.append({
                'category': 'summary',
                'suggestion': f'Mention your expertise in {jd_title} role in the summary',
                'reason': 'This shows direct relevance to the job opening',
                'impact': 'high'
            })
        
        if len(summary) > 200:
            suggestions.append({
                'category': 'summary',
                'suggestion': 'Condense summary to 100-150 words for maximum impact',
                'reason': 'Shorter, focused summaries are more likely to be read by ATS and recruiters',
                'impact': 'medium'
            })
        
        return suggestions[:3]
    
    def _suggest_experience_improvements(self, parsed_resume: Dict[str, Any], 
                                        jd_skills: Set[str]) -> List[Dict[str, Any]]:
        """Generate experience section improvement suggestions"""
        suggestions = []
        
        experiences = parsed_resume.get('experience', [])
        
        if not experiences:
            suggestions.append({
                'category': 'experience',
                'suggestion': 'Add your professional work experience with specific achievements and results',
                'reason': 'Experience is critical for ATS matching and recruiter evaluation',
                'impact': 'high'
            })
        
        for exp in experiences:
            description = exp.get('description', '')
            skills = exp.get('skills', [])
            
            if not description or len(description) < 30:
                suggestions.append({
                    'category': 'experience',
                    'suggestion': f'Add more detailed description for {exp.get("title", "position")}',
                    'reason': 'Detailed descriptions help ATS find relevant keywords and achievements',
                    'impact': 'high'
                })
            
            if not skills or len(skills) < 2:
                suggestions.append({
                    'category': 'experience',
                    'suggestion': f'Add specific technologies/skills used in {exp.get("title", "position")}',
                    'reason': 'Technologies mentioned in experience boost keyword matching',
                    'impact': 'medium'
                })
            
            if 'achieved' not in description.lower() and 'improved' not in description.lower():
                suggestions.append({
                    'category': 'experience',
                    'suggestion': 'Include measurable achievements and metrics in experience descriptions',
                    'reason': 'Quantifiable results stand out to both ATS and human recruiters',
                    'impact': 'high'
                })
        
        return suggestions[:5]
    
    def _suggest_project_improvements(self, parsed_resume: Dict[str, Any], 
                                     missing_skills: Set[str]) -> List[Dict[str, Any]]:
        """Generate project section improvement suggestions"""
        suggestions = []
        
        projects = parsed_resume.get('projects', [])
        
        if not projects:
            suggestions.append({
                'category': 'projects',
                'suggestion': 'Add personal or open-source projects that demonstrate key skills',
                'reason': 'Projects provide concrete examples of your technical abilities',
                'impact': 'high'
            })
        
        for project in projects:
            tech = project.get('technologies', [])
            
            if not tech or len(tech) < 2:
                suggestions.append({
                    'category': 'projects',
                    'suggestion': f'List specific technologies used in {project.get("title", "project")}',
                    'reason': 'Technology keywords improve ATS matching',
                    'impact': 'medium'
                })
            
            if not project.get('url'):
                suggestions.append({
                    'category': 'projects',
                    'suggestion': 'Add links to GitHub or portfolio for projects when possible',
                    'reason': 'Links allow recruiters to view your actual work',
                    'impact': 'medium'
                })
        
        return suggestions[:4]
    
    def _calculate_improvement_potential(self, parsed_resume: Dict[str, Any], 
                                        parsed_jd: Dict[str, Any], 
                                        missing_skills: Set[str]) -> float:
        """Calculate overall improvement potential (0-100)"""
        potential = 0
        
        # Missing skills impact (max 40)
        max_missing = 15
        skill_improvement = (min(len(missing_skills), max_missing) / max_missing) * 40
        potential += skill_improvement
        
        # Experience improvements (max 30)
        experiences = parsed_resume.get('experience', [])
        if not experiences:
            potential += 30
        else:
            poor_exp = sum(1 for exp in experiences if not exp.get('description') or len(exp.get('description', '')) < 30)
            potential += (poor_exp / max(len(experiences), 1)) * 30
        
        # Projects improvements (max 20)
        projects = parsed_resume.get('projects', [])
        if not projects:
            potential += 20
        else:
            poor_proj = sum(1 for proj in projects if not proj.get('technologies') or len(proj.get('technologies', [])) < 2)
            potential += (poor_proj / max(len(projects), 1)) * 20
        
        # Summary improvements (max 10)
        summary = parsed_resume.get('summary', '')
        if not summary or len(summary) < 50:
            potential += 10
        
        return min(potential, 100.0)
