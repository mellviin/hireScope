"""
ATS Match Engine
Compares resume and job description data to calculate compatibility scores
"""
from typing import Dict, List, Any, Set, Tuple, Optional
from collections import Counter
from datetime import datetime
import re
from app.utils.logging import setup_logging
from app.utils.exceptions import ProcessingError

logger = setup_logging(__name__)

LEARNING_RESOURCES = {
    'python': ['Python official docs', 'Real Python tutorials', 'LeetCode Python track'],
    'javascript': ['MDN Web Docs', 'JavaScript.info', 'freeCodeCamp'],
    'react': ['React official docs', 'React Beta docs', 'Frontend Masters'],
    'java': ['Oracle Java Tutorials', 'Baeldung', 'Spring Guides'],
    'sql': ['SQLBolt', 'Mode SQL Tutorial', 'PostgreSQL docs'],
    'aws': ['AWS Skill Builder', 'AWS Certified Cloud Practitioner path'],
    'docker': ['Docker Getting Started guide', 'Play with Docker labs'],
    'kubernetes': ['Kubernetes.io tutorials', 'KodeKloud free courses'],
    'typescript': ['TypeScript Handbook', 'Total TypeScript'],
    'node': ['Node.js docs', 'Express.js guide'],
    'agile': ['Scrum Guide', 'Atlassian Agile tutorials'],
}

SKILL_RELATED_TERMS = {
    'python': ['django', 'flask', 'fastapi', 'pandas', 'numpy', 'scripting', 'backend'],
    'javascript': ['js', 'node', 'nodejs', 'react', 'frontend', 'web'],
    'typescript': ['javascript', 'js', 'react', 'node', 'frontend'],
    'react': ['javascript', 'frontend', 'ui', 'web', 'redux'],
    'node': ['javascript', 'nodejs', 'express', 'backend', 'api'],
    'nodejs': ['node', 'javascript', 'express', 'backend'],
    'java': ['spring', 'backend', 'enterprise', 'jvm'],
    'spring': ['java', 'backend', 'microservices'],
    'aws': ['cloud', 'ec2', 's3', 'lambda', 'devops', 'azure', 'gcp'],
    'docker': ['container', 'kubernetes', 'devops', 'ci/cd', 'deployment'],
    'kubernetes': ['docker', 'k8s', 'container', 'devops', 'orchestration'],
    'sql': ['database', 'mysql', 'postgresql', 'postgres', 'query'],
    'postgresql': ['sql', 'database', 'postgres'],
    'mongodb': ['database', 'nosql', 'document'],
    'rest': ['api', 'backend', 'microservices', 'http'],
    'api': ['rest', 'backend', 'microservices', 'services'],
    'fastapi': ['python', 'api', 'rest', 'backend'],
    'git': ['github', 'gitlab', 'version control', 'ci/cd'],
    'agile': ['scrum', 'sprint', 'kanban'],
    'scrum': ['agile', 'sprint'],
    'machine learning': ['ml', 'data', 'model', 'python', 'ai'],
    'ci/cd': ['jenkins', 'github actions', 'devops', 'deployment', 'pipeline'],
}


class ATSMatchEngine:
    """
    ATS Match Engine using weighted scoring system with detailed breakdowns.
    """

    WEIGHTS = {
        'required_skills': 0.40,
        'preferred_skills': 0.20,
        'experience': 0.20,
        'projects': 0.10,
        'education': 0.10,
    }

    CATEGORY_LABELS = {
        'required_skills': 'Required Skills',
        'preferred_skills': 'Preferred Skills',
        'experience': 'Experience',
        'projects': 'Projects & Portfolio',
        'education': 'Education',
    }

    def __init__(self):
        logger.info("ATS Match Engine initialized")

    def calculate_match(self, parsed_resume: Dict[str, Any], parsed_jd: Dict[str, Any]) -> Dict[str, Any]:
        try:
            resume_skills = self._get_resume_skills_set(parsed_resume)
            resume_text = self._get_full_resume_text(parsed_resume)

            jd_required = self._normalize_skill_set(parsed_jd.get('required_skills', []))
            jd_preferred = self._normalize_skill_set(parsed_jd.get('preferred_skills', []))
            jd_technical = self._normalize_skill_set(parsed_jd.get('technical_skills', []))
            jd_soft = self._normalize_skill_set(parsed_jd.get('soft_skills', []))

            all_required = jd_required | jd_technical
            all_preferred = jd_preferred | jd_soft

            req_detail = self._analyze_skill_category(resume_skills, resume_text, all_required, 'required')
            pref_detail = self._analyze_skill_category(resume_skills, resume_text, all_preferred, 'preferred')

            required_skills_score = req_detail['score']
            preferred_skills_score = pref_detail['score']

            experience_analysis = self._analyze_experience_detailed(parsed_resume, parsed_jd)
            experience_score = experience_analysis['score']

            projects_analysis = self._analyze_projects_detailed(parsed_resume, all_required | all_preferred)
            projects_score = projects_analysis['score']

            education_analysis = self._analyze_education_detailed(parsed_resume, parsed_jd)
            education_score = education_analysis['score']

            responsibility_analysis = self._analyze_responsibility_alignment(resume_text, parsed_jd)
            keyword_analysis = self._analyze_keyword_coverage(resume_text, parsed_jd)

            required_skills_score = required_skills_score or 0.0
            preferred_skills_score = preferred_skills_score or 0.0
            experience_score = experience_score or 0.0
            projects_score = projects_score or 0.0
            education_score = education_score or 0.0

            ats_score = (
                required_skills_score * self.WEIGHTS['required_skills'] +
                preferred_skills_score * self.WEIGHTS['preferred_skills'] +
                experience_score * self.WEIGHTS['experience'] +
                projects_score * self.WEIGHTS['projects'] +
                education_score * self.WEIGHTS['education']
            )

            score_breakdown = self._build_score_breakdown(
                required_skills_score, preferred_skills_score,
                experience_score, projects_score, education_score, ats_score
            )

            missing_skills = self._build_missing_skills_list(req_detail, pref_detail)
            matched_keywords = keyword_analysis['matched']
            keyword_density = self._calculate_keyword_density(resume_text, matched_keywords)

            strengths = self._extract_detailed_strengths(
                req_detail, pref_detail, experience_analysis,
                projects_analysis, education_analysis, responsibility_analysis, keyword_analysis
            )

            recommendations = self._generate_detailed_recommendations(
                req_detail, pref_detail, experience_analysis,
                projects_analysis, education_analysis, responsibility_analysis, keyword_analysis, parsed_jd
            )

            keyword_enhancement = self._build_keyword_enhancement_plan(
                parsed_resume, parsed_jd, resume_text, resume_skills,
                req_detail, pref_detail, keyword_analysis,
                responsibility_analysis, keyword_density,
            )

            skill_evidence_matrix = self._build_skill_evidence_matrix(
                parsed_resume, parsed_jd, resume_skills,
            )

            return {
                'ats_score': round(ats_score, 2),
                'required_skills_match': round(required_skills_score, 2),
                'preferred_skills_match': round(preferred_skills_score, 2),
                'experience_match': round(experience_score, 2),
                'projects_match': round(projects_score, 2),
                'education_match': round(education_score, 2),
                'keyword_coverage': round(keyword_analysis['coverage_percent'], 2),
                'responsibility_alignment': round(responsibility_analysis['alignment_percent'], 2),
                'strengths': strengths,
                'missing_skills': missing_skills,
                'matched_keywords': matched_keywords[:30],
                'missing_keywords': keyword_analysis['missing'][:20],
                'keyword_density': keyword_density,
                'recommendations': recommendations,
                'skill_breakdown': {
                    'required': req_detail,
                    'preferred': pref_detail,
                },
                'score_breakdown': score_breakdown,
                'experience_analysis': experience_analysis,
                'projects_analysis': projects_analysis,
                'education_analysis': education_analysis,
                'responsibility_analysis': responsibility_analysis,
                'keyword_analysis': keyword_analysis,
                'keyword_enhancement': keyword_enhancement,
                'skill_evidence_matrix': skill_evidence_matrix,
            }
        except Exception as e:
            logger.error(f"Error calculating match: {str(e)}")
            raise ProcessingError(f"Failed to calculate match: {str(e)}")

    def build_gap_analysis(
        self,
        match_result: Dict[str, Any],
        parsed_resume: Dict[str, Any],
        parsed_jd: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build comprehensive gap analysis from match result."""
        req = match_result.get('skill_breakdown', {}).get('required', {})
        pref = match_result.get('skill_breakdown', {}).get('preferred', {})
        exp = match_result.get('experience_analysis', {})
        edu = match_result.get('education_analysis', {})
        kw = match_result.get('keyword_analysis', {})

        critical_missing = [
            {
                'skill': s,
                'category': 'required',
                'priority': 5,
                'suggested_resources': self._get_learning_resources(s),
            }
            for s in req.get('missing', [])[:10]
        ]

        priority_areas = []
        if req.get('missing'):
            priority_areas.append({
                'area': 'Critical Skills',
                'impact': 'high',
                'details': f"Missing {len(req['missing'])} required skills: {', '.join(req['missing'][:5])}",
                'action': 'Add these skills to your resume or pursue targeted learning',
            })
        if exp.get('gap_summary'):
            priority_areas.append({
                'area': 'Experience',
                'impact': 'high' if exp.get('score', 100) < 60 else 'medium',
                'details': exp['gap_summary'],
                'action': exp.get('recommendation', 'Highlight relevant roles and quantify impact'),
            })
        if kw.get('missing'):
            priority_areas.append({
                'area': 'Keywords & ATS',
                'impact': 'medium',
                'details': f"Resume missing {len(kw['missing'])} JD keywords: {', '.join(kw['missing'][:5])}",
                'action': 'Naturally incorporate these terms in summary and experience bullets',
            })
        if edu.get('gap'):
            priority_areas.append({
                'area': 'Education',
                'impact': 'medium',
                'details': edu['gap'],
                'action': 'Add degrees, certifications, or relevant coursework',
            })

        return {
            'critical_missing_skills': critical_missing,
            'recommended_skills': pref.get('missing', [])[:10],
            'matched_skills': req.get('matched_exact', []) + pref.get('matched_exact', []),
            'partial_skills': req.get('matched_partial', []) + pref.get('matched_partial', []),
            'education_gap': edu.get('missing_requirements', parsed_jd.get('education_requirements', [])),
            'experience_gap': exp.get('gap_summary', ''),
            'keyword_gaps': kw.get('missing', [])[:15],
            'priority_areas': priority_areas,
            'responsibility_gaps': match_result.get('responsibility_analysis', {}).get('missing_responsibilities', [])[:8],
            'keyword_enhancement': match_result.get('keyword_enhancement', {}),
        }

    def _normalize_skill_set(self, skills: List[Any]) -> Set[str]:
        return {str(s).lower().strip() for s in skills if s}

    def _get_resume_skills_set(self, parsed_resume: Dict[str, Any]) -> Set[str]:
        skills = set()
        for skill in parsed_resume.get('skills') or []:
            if isinstance(skill, dict):
                skills.add(skill.get('name', '').lower())
            else:
                skills.add(str(skill).lower())
        for exp in parsed_resume.get('experience') or []:
            for skill in exp.get('skills') or []:
                skills.add(str(skill).lower())
        for project in parsed_resume.get('projects') or []:
            for tech in project.get('technologies') or []:
                skills.add(str(tech).lower())
        return {s for s in skills if s}

    def _get_full_resume_text(self, parsed_resume: Dict[str, Any]) -> str:
        parts = []
        if parsed_resume.get('summary'):
            parts.append(parsed_resume['summary'])
        for exp in parsed_resume.get('experience') or []:
            parts.append(exp.get('title', ''))
            parts.append(exp.get('company', ''))
            parts.append(exp.get('description', ''))
            parts.extend(exp.get('skills') or [])
        for edu in parsed_resume.get('education') or []:
            parts.append(edu.get('degree', ''))
            parts.append(edu.get('field', ''))
            parts.append(edu.get('institution', ''))
        for project in parsed_resume.get('projects') or []:
            parts.append(project.get('title', ''))
            parts.append(project.get('description', ''))
            parts.extend(project.get('technologies') or [])
        for skill in parsed_resume.get('skills') or []:
            parts.append(skill.get('name', '') if isinstance(skill, dict) else str(skill))
        return ' '.join(str(p) for p in parts if p).lower()

    def _analyze_skill_category(
        self, resume_skills: Set[str], resume_text: str, jd_skills: Set[str], category: str
    ) -> Dict[str, Any]:
        if not jd_skills:
            return {
                'category': category,
                'score': 100.0,
                'total': 0,
                'matched_exact': [],
                'matched_partial': [],
                'missing': [],
                'match_details': [],
            }

        matched_exact = []
        matched_partial = []
        missing = []
        match_details = []

        for skill in sorted(jd_skills):
            if skill in resume_skills:
                matched_exact.append(skill)
                match_details.append({'skill': skill, 'match_type': 'exact', 'evidence': 'Listed in resume skills'})
            else:
                partial_evidence = self._find_partial_evidence(skill, resume_skills, resume_text)
                if partial_evidence:
                    matched_partial.append(skill)
                    match_details.append({'skill': skill, 'match_type': 'partial', 'evidence': partial_evidence})
                else:
                    missing.append(skill)
                    match_details.append({'skill': skill, 'match_type': 'missing', 'evidence': None})

        matched_weight = len(matched_exact) + (len(matched_partial) * 0.6)
        score = min((matched_weight / len(jd_skills)) * 100, 100.0)

        return {
            'category': category,
            'score': round(score, 2),
            'total': len(jd_skills),
            'matched_exact': matched_exact,
            'matched_partial': matched_partial,
            'missing': missing,
            'match_details': match_details,
        }

    def _find_partial_evidence(self, skill: str, resume_skills: Set[str], resume_text: str) -> Optional[str]:
        for res_skill in resume_skills:
            if len(skill) > 3 and (skill in res_skill or res_skill in skill):
                return f'Related skill on resume: {res_skill}'
        if len(skill) > 2 and re.search(r'\b' + re.escape(skill) + r'\b', resume_text):
            return 'Mentioned in resume text but not in skills section'
        aliases = {
            'javascript': ['js', 'node', 'nodejs'],
            'typescript': ['ts'],
            'kubernetes': ['k8s'],
            'amazon web services': ['aws'],
            'machine learning': ['ml', 'deep learning'],
        }
        for alias in aliases.get(skill, []):
            if alias in resume_text or alias in resume_skills:
                return f'Related term found: {alias}'
        return None

    def _parse_duration_years(self, duration: str) -> float:
        if not duration:
            return 0.0
        duration = duration.lower()
        year_match = re.search(r'(\d+)\s*(?:\+?\s*)?(?:years?|yrs?)', duration)
        if year_match:
            return float(year_match.group(1))
        years = re.findall(r'(19|20)\d{2}', duration)
        if len(years) >= 2:
            return max(float(int(years[-1]) - int(years[0])), 1.0)
        if len(years) == 1:
            if 'present' in duration or 'current' in duration:
                return max(datetime.now().year - int(years[0]), 1.0)
        return 1.0

    def _estimate_resume_years(self, parsed_resume: Dict[str, Any]) -> float:
        experiences = parsed_resume.get('experience') or []
        if not experiences:
            return 0.0
        total = sum(self._parse_duration_years(exp.get('duration', '')) for exp in experiences)
        return total if total > 0 else float(len(experiences))

    def _analyze_experience_detailed(self, parsed_resume: Dict[str, Any], parsed_jd: Dict[str, Any]) -> Dict[str, Any]:
        experiences = parsed_resume.get('experience') or []
        resume_years = self._estimate_resume_years(parsed_resume)
        required_years = parsed_jd.get('years_of_experience')
        if required_years is None:
            required_years = 0
        else:
            try:
                required_years = int(required_years)
            except (TypeError, ValueError):
                required_years = 0

        jd_title = (parsed_jd.get('job_title') or '').lower()
        jd_title_tokens = set(re.findall(r'[a-z]{3,}', jd_title))
        matching_roles = []
        role_details = []

        for exp in experiences:
            title = (exp.get('title') or '').lower()
            company = exp.get('company') or 'Unknown company'
            duration = exp.get('duration') or 'Unknown duration'
            title_tokens = set(re.findall(r'[a-z]{3,}', title))
            overlap = jd_title_tokens & title_tokens
            relevance = 'high' if len(overlap) >= 2 else ('medium' if overlap else 'low')
            if overlap or any(t in title for t in ['engineer', 'developer', 'analyst', 'manager', 'lead']):
                matching_roles.append(exp.get('title', 'Role'))
            role_details.append({
                'title': exp.get('title', ''),
                'company': company,
                'duration': duration,
                'years_estimate': self._parse_duration_years(duration),
                'relevance': relevance,
                'matching_terms': list(overlap),
            })

        if required_years == 0:
            score = 100.0 if experiences else 50.0
            gap_summary = 'No specific years requirement in job description'
        elif resume_years >= required_years + 1:
            score = 100.0
            gap_summary = f'Strong experience fit: ~{resume_years:.0f} years vs {required_years} required'
        elif resume_years >= required_years:
            score = 90.0
            gap_summary = f'Meets experience requirement: ~{resume_years:.0f} years vs {required_years} required'
        elif resume_years >= required_years * 0.7:
            score = 70.0
            gap_summary = f'Slightly below requirement: ~{resume_years:.0f} years vs {required_years} required'
        elif resume_years > 0:
            score = 45.0
            gap_summary = f'Experience gap: ~{resume_years:.0f} years vs {required_years} required'
        else:
            score = 0.0
            gap_summary = 'No work experience found on resume'

        recommendation = 'Quantify achievements with metrics in each role'
        if score < 70:
            recommendation = 'Emphasize relevant projects, internships, or transferable experience to close the gap'

        return {
            'score': round(score, 2),
            'resume_years_estimate': round(resume_years, 1),
            'required_years': required_years,
            'experience_level_jd': parsed_jd.get('experience_level'),
            'matching_roles': matching_roles[:5],
            'role_details': role_details,
            'gap_summary': gap_summary,
            'recommendation': recommendation,
        }

    def _analyze_projects_detailed(self, parsed_resume: Dict[str, Any], jd_skills: Set[str]) -> Dict[str, Any]:
        projects = parsed_resume.get('projects') or []
        if not projects:
            return {
                'score': 20.0,
                'project_count': 0,
                'relevant_projects': [],
                'gap': 'No projects listed — add 1-2 projects demonstrating JD skills',
            }

        relevant = []
        for project in projects:
            title = project.get('title', 'Untitled')
            tech = {str(t).lower() for t in (project.get('technologies') or [])}
            overlap = tech & jd_skills
            desc = (project.get('description') or '').lower()
            desc_hits = [s for s in jd_skills if s in desc]
            relevance_score = len(overlap) + len(desc_hits) * 0.5
            if relevance_score > 0:
                relevant.append({
                    'title': title,
                    'matching_technologies': list(overlap),
                    'keyword_hits': desc_hits[:5],
                    'relevance_score': round(relevance_score, 1),
                })

        base_score = min(len(projects) * 25, 70.0)
        relevance_bonus = min(len(relevant) * 15, 30.0)
        score = min(base_score + relevance_bonus, 100.0)

        return {
            'score': round(score, 2),
            'project_count': len(projects),
            'relevant_projects': sorted(relevant, key=lambda x: x['relevance_score'], reverse=True)[:5],
            'gap': None if relevant else 'Projects exist but none clearly align with job requirements',
        }

    def _analyze_education_detailed(self, parsed_resume: Dict[str, Any], parsed_jd: Dict[str, Any]) -> Dict[str, Any]:
        education_items = parsed_resume.get('education') or []
        required_education = parsed_jd.get('education_requirements') or []
        resume_degrees = []
        for edu in education_items:
            resume_degrees.append({
                'degree': edu.get('degree', ''),
                'field': edu.get('field', ''),
                'institution': edu.get('institution', ''),
            })

        if not required_education:
            score = 100.0 if education_items else 50.0
            return {
                'score': round(score, 2),
                'resume_education': resume_degrees,
                'required': [],
                'missing_requirements': [],
                'gap': None if education_items else 'No education section on resume',
            }

        if not education_items:
            return {
                'score': 0.0,
                'resume_education': [],
                'required': required_education,
                'missing_requirements': required_education,
                'gap': f'Job requires: {", ".join(required_education[:3])}',
            }

        resume_text = ' '.join(
            f"{e.get('degree', '')} {e.get('field', '')}".lower() for e in education_items
        )
        matched_reqs = []
        missing_reqs = []
        for req in required_education:
            if req.lower() in resume_text or any(req.lower() in d.lower() for d in resume_text.split()):
                matched_reqs.append(req)
            else:
                missing_reqs.append(req)

        if not missing_reqs:
            score = 100.0
        elif matched_reqs:
            score = 60.0
        else:
            score = 30.0

        return {
            'score': round(score, 2),
            'resume_education': resume_degrees,
            'required': required_education,
            'matched_requirements': matched_reqs,
            'missing_requirements': missing_reqs,
            'gap': f'Missing education: {", ".join(missing_reqs)}' if missing_reqs else None,
        }

    def _analyze_responsibility_alignment(self, resume_text: str, parsed_jd: Dict[str, Any]) -> Dict[str, Any]:
        responsibilities = parsed_jd.get('responsibilities') or []
        if not responsibilities:
            return {
                'alignment_percent': 100.0,
                'matched_responsibilities': [],
                'missing_responsibilities': [],
                'total': 0,
            }

        matched = []
        missing = []
        for resp in responsibilities:
            tokens = [t for t in re.findall(r'[a-z]{4,}', resp.lower()) if t not in {'will', 'with', 'that', 'this', 'your', 'have', 'work'}]
            if not tokens:
                continue
            hits = sum(1 for t in tokens if t in resume_text)
            ratio = hits / len(tokens)
            if ratio >= 0.35:
                matched.append({'responsibility': resp, 'token_match_percent': round(ratio * 100, 1)})
            else:
                missing.append(resp)

        alignment = (len(matched) / len(responsibilities)) * 100 if responsibilities else 100.0
        return {
            'alignment_percent': round(alignment, 2),
            'matched_responsibilities': matched[:8],
            'missing_responsibilities': missing[:8],
            'total': len(responsibilities),
        }

    def _analyze_keyword_coverage(self, resume_text: str, parsed_jd: Dict[str, Any]) -> Dict[str, Any]:
        keywords = []
        for key in ['required_skills', 'preferred_skills', 'technical_skills', 'soft_skills', 'keywords']:
            keywords.extend(parsed_jd.get(key) or [])
        keywords = list(dict.fromkeys(k.lower() for k in keywords if k))

        if not keywords:
            return {'coverage_percent': 100.0, 'matched': [], 'missing': [], 'total': 0}

        matched = [kw for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', resume_text)]
        missing = [kw for kw in keywords if kw not in matched]
        coverage = (len(matched) / len(keywords)) * 100

        return {
            'coverage_percent': round(coverage, 2),
            'matched': matched,
            'missing': missing,
            'total': len(keywords),
        }

    def _build_score_breakdown(
        self, req: float, pref: float, exp: float, proj: float, edu: float, total: float
    ) -> List[Dict[str, Any]]:
        scores = {
            'required_skills': req,
            'preferred_skills': pref,
            'experience': exp,
            'projects': proj,
            'education': edu,
        }
        breakdown = []
        for key, score in scores.items():
            weight = self.WEIGHTS[key]
            contribution = score * weight
            breakdown.append({
                'category': key,
                'label': self.CATEGORY_LABELS[key],
                'score': round(score, 2),
                'weight_percent': round(weight * 100, 1),
                'weighted_contribution': round(contribution, 2),
            })
        breakdown.append({
            'category': 'total',
            'label': 'Overall ATS Score',
            'score': round(total, 2),
            'weight_percent': 100.0,
            'weighted_contribution': round(total, 2),
        })
        return breakdown

    def _build_missing_skills_list(self, req_detail: Dict, pref_detail: Dict) -> List[Dict[str, Any]]:
        items = []
        for skill in req_detail.get('missing', [])[:10]:
            items.append({
                'skill': skill,
                'category': 'required',
                'priority': 5,
                'suggested_resources': self._get_learning_resources(skill),
            })
        for skill in pref_detail.get('missing', [])[:10]:
            items.append({
                'skill': skill,
                'category': 'preferred',
                'priority': 3,
                'suggested_resources': self._get_learning_resources(skill),
            })
        return items

    def _get_learning_resources(self, skill: str) -> List[str]:
        skill_lower = skill.lower()
        for key, resources in LEARNING_RESOURCES.items():
            if key in skill_lower or skill_lower in key:
                return resources
        return [f'Search "{skill} tutorial" on official docs or Coursera', 'Build a small project using this skill']

    def _calculate_keyword_density(self, resume_text: str, matched_keywords: List[str]) -> Dict[str, int]:
        density = {}
        for keyword in matched_keywords:
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            count = len(re.findall(pattern, resume_text))
            if count > 0:
                density[keyword] = count
        return dict(sorted(density.items(), key=lambda x: x[1], reverse=True))

    def _extract_detailed_strengths(
        self, req_detail, pref_detail, exp_analysis, proj_analysis,
        edu_analysis, resp_analysis, kw_analysis
    ) -> List[Dict[str, Any]]:
        strengths = []

        if req_detail.get('matched_exact'):
            strengths.append({
                'category': 'required_skills',
                'details': [
                    f"Matched {len(req_detail['matched_exact'])}/{req_detail['total']} required skills",
                    f"Skills: {', '.join(req_detail['matched_exact'][:8])}",
                ],
                'score': req_detail['score'],
            })
        if pref_detail.get('matched_exact'):
            strengths.append({
                'category': 'preferred_skills',
                'details': [
                    f"Matched {len(pref_detail['matched_exact'])}/{pref_detail['total']} preferred skills",
                    f"Skills: {', '.join(pref_detail['matched_exact'][:8])}",
                ],
                'score': pref_detail['score'],
            })
        if exp_analysis.get('matching_roles'):
            strengths.append({
                'category': 'experience',
                'details': [
                    exp_analysis['gap_summary'],
                    f"Relevant roles: {', '.join(exp_analysis['matching_roles'][:3])}",
                ],
                'score': exp_analysis['score'],
            })
        if proj_analysis.get('relevant_projects'):
            titles = [p['title'] for p in proj_analysis['relevant_projects'][:3]]
            strengths.append({
                'category': 'projects',
                'details': [
                    f"{proj_analysis['project_count']} project(s) on resume, {len(proj_analysis['relevant_projects'])} align with JD",
                    f"Top projects: {', '.join(titles)}",
                ],
                'score': proj_analysis['score'],
            })
        if edu_analysis.get('matched_requirements'):
            strengths.append({
                'category': 'education',
                'details': [
                    f"Meets education requirements: {', '.join(edu_analysis['matched_requirements'])}",
                ],
                'score': edu_analysis['score'],
            })
        if resp_analysis.get('matched_responsibilities'):
            strengths.append({
                'category': 'responsibilities',
                'details': [
                    f"{resp_analysis['alignment_percent']}% responsibility alignment with job description",
                    f"Covers: {resp_analysis['matched_responsibilities'][0]['responsibility'][:80]}..." if resp_analysis['matched_responsibilities'] else '',
                ],
                'score': resp_analysis['alignment_percent'],
            })
        if kw_analysis.get('coverage_percent', 0) >= 60:
            strengths.append({
                'category': 'keywords',
                'details': [
                    f"{kw_analysis['coverage_percent']}% keyword coverage ({len(kw_analysis['matched'])}/{kw_analysis['total']} JD keywords found)",
                ],
                'score': kw_analysis['coverage_percent'],
            })

        return strengths

    def _generate_detailed_recommendations(
        self, req_detail, pref_detail, exp_analysis, proj_analysis,
        edu_analysis, resp_analysis, kw_analysis, parsed_jd
    ) -> List[Dict[str, Any]]:
        recommendations = []

        if req_detail.get('missing'):
            top = req_detail['missing'][:3]
            recommendations.append({
                'category': 'skills',
                'suggestion': f"Priority: acquire or demonstrate {', '.join(top)}",
                'priority': 5,
                'reason': f"Missing {len(req_detail['missing'])} of {req_detail['total']} required skills for this role",
            })
        if pref_detail.get('missing')[:3]:
            recommendations.append({
                'category': 'skills',
                'suggestion': f"Strengthen profile with: {', '.join(pref_detail['missing'][:3])}",
                'priority': 3,
                'reason': 'Preferred skills differentiate candidates with similar required skill sets',
            })
        if exp_analysis.get('score', 100) < 75:
            recommendations.append({
                'category': 'experience',
                'suggestion': exp_analysis.get('recommendation', 'Expand experience descriptions'),
                'priority': 4,
                'reason': exp_analysis.get('gap_summary', 'Experience section needs improvement'),
            })
        if proj_analysis.get('gap'):
            recommendations.append({
                'category': 'projects',
                'suggestion': proj_analysis['gap'],
                'priority': 3,
                'reason': 'Projects provide proof of skills when experience is limited',
            })
        if edu_analysis.get('gap'):
            recommendations.append({
                'category': 'education',
                'suggestion': edu_analysis['gap'],
                'priority': 2,
                'reason': 'Education requirements are explicitly stated in the job description',
            })
        if resp_analysis.get('missing_responsibilities'):
            recommendations.append({
                'category': 'experience',
                'suggestion': f"Add bullet points covering: {resp_analysis['missing_responsibilities'][0][:60]}...",
                'priority': 4,
                'reason': f"Only {resp_analysis['alignment_percent']}% of job responsibilities reflected in resume",
            })
        if kw_analysis.get('missing')[:5]:
            recommendations.append({
                'category': 'keywords',
                'suggestion': f"Incorporate ATS keywords: {', '.join(kw_analysis['missing'][:5])}",
                'priority': 3,
                'reason': f"Keyword coverage is {kw_analysis['coverage_percent']}% — aim for 70%+ for better ATS ranking",
            })

        job_title = parsed_jd.get('job_title', '')
        if job_title:
            recommendations.append({
                'category': 'summary',
                'suggestion': f"Tailor summary to target the {job_title} role with top matched skills upfront",
                'priority': 3,
                'reason': 'Recruiters and ATS scan the summary first for role fit',
            })

        return recommendations[:8]

    def _get_dedicated_skills_text(self, parsed_resume: Dict[str, Any]) -> str:
        parts = []
        for skill in parsed_resume.get('skills') or []:
            parts.append(skill.get('name', '') if isinstance(skill, dict) else str(skill))
        return ' '.join(str(p) for p in parts if p).lower()

    def _collect_jd_keywords_categorized(self, parsed_jd: Dict[str, Any]) -> List[Dict[str, Any]]:
        category_map = [
            ('required_skills', 'required', 5),
            ('technical_skills', 'technical', 5),
            ('preferred_skills', 'preferred', 3),
            ('soft_skills', 'soft', 3),
            ('keywords', 'general', 4),
        ]
        seen: Set[str] = set()
        items: List[Dict[str, Any]] = []
        for key, category, priority in category_map:
            for kw in parsed_jd.get(key) or []:
                kw_lower = str(kw).lower().strip()
                if kw_lower and kw_lower not in seen:
                    seen.add(kw_lower)
                    items.append({'keyword': kw_lower, 'category': category, 'priority': priority})
        return items

    def _find_experience_containing_keyword(
        self, keyword: str, parsed_resume: Dict[str, Any]
    ) -> Optional[Dict[str, str]]:
        pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
        for exp in parsed_resume.get('experience') or []:
            blob = ' '.join([
                exp.get('title', ''), exp.get('description', ''),
                ' '.join(exp.get('skills') or []),
            ])
            if pattern.search(blob):
                return {
                    'title': exp.get('title', 'Role'),
                    'company': exp.get('company', 'Company'),
                }
        return None

    def _find_related_resume_evidence(
        self, keyword: str, resume_text: str, resume_skills: Set[str], parsed_resume: Dict[str, Any]
    ) -> Optional[str]:
        related_terms = SKILL_RELATED_TERMS.get(keyword, [])
        for term in related_terms:
            if term in resume_skills:
                return f'Related skill on resume: {term}'
            if re.search(r'\b' + re.escape(term) + r'\b', resume_text):
                return f'Related term in resume: {term}'

        for exp in parsed_resume.get('experience') or []:
            exp_text = ' '.join([
                exp.get('title', ''), exp.get('description', ''),
                ' '.join(exp.get('skills') or []),
            ]).lower()
            for term in related_terms:
                if re.search(r'\b' + re.escape(term) + r'\b', exp_text):
                    return f'Related experience at {exp.get("company", "previous role")}: {term}'

        for project in parsed_resume.get('projects') or []:
            proj_text = ' '.join([
                project.get('title', ''), project.get('description', ''),
                ' '.join(project.get('technologies') or []),
            ]).lower()
            for term in related_terms:
                if re.search(r'\b' + re.escape(term) + r'\b', proj_text):
                    return f'Related project "{project.get("title", "Project")}": {term}'
        return None

    def _find_experience_with_related(
        self, keyword: str, parsed_resume: Dict[str, Any]
    ) -> Optional[Dict[str, str]]:
        related_terms = SKILL_RELATED_TERMS.get(keyword, [])
        for exp in parsed_resume.get('experience') or []:
            exp_text = ' '.join([
                exp.get('title', ''), exp.get('description', ''),
                ' '.join(exp.get('skills') or []),
            ]).lower()
            for term in related_terms:
                if re.search(r'\b' + re.escape(term) + r'\b', exp_text):
                    return {
                        'title': exp.get('title', 'Role'),
                        'company': exp.get('company', 'Company'),
                        'related_term': term,
                    }
        return None

    def _find_project_with_related(
        self, keyword: str, parsed_resume: Dict[str, Any]
    ) -> Optional[Dict[str, str]]:
        related_terms = SKILL_RELATED_TERMS.get(keyword, [])
        for project in parsed_resume.get('projects') or []:
            proj_text = ' '.join([
                project.get('title', ''), project.get('description', ''),
                ' '.join(project.get('technologies') or []),
            ]).lower()
            for term in related_terms:
                if re.search(r'\b' + re.escape(term) + r'\b', proj_text):
                    return {
                        'title': project.get('title', 'Project'),
                        'related_term': term,
                    }
        return None

    def _build_addition_suggestion(
        self,
        keyword: str,
        status: str,
        category: str,
        priority: int,
        count: int,
        parsed_resume: Dict[str, Any],
        partial_evidence: Optional[str],
        related_evidence: Optional[str],
    ) -> Dict[str, Any]:
        exp_ctx = self._find_experience_containing_keyword(keyword, parsed_resume)
        exp_related = self._find_experience_with_related(keyword, parsed_resume)
        proj_related = self._find_project_with_related(keyword, parsed_resume)

        if status == 'hidden':
            target = 'Skills'
            reason = 'Keyword appears in resume body but not in your Skills section — ATS may under-weight it'
            evidence = (
                f"Mentioned in {exp_ctx['title']} @ {exp_ctx['company']}"
                if exp_ctx else 'Found in experience or project descriptions'
            )
            phrase = f'Add "{keyword.title()}" to your Skills section'
            if exp_ctx:
                phrase += f' — you already reference it in your {exp_ctx["title"]} role at {exp_ctx["company"]}'
            action_type = 'add_to_skills'
        elif status == 'partial':
            target = 'Experience'
            reason = 'Related experience exists but JD uses different exact terminology'
            evidence = partial_evidence or 'Partial match detected in resume'
            related = (partial_evidence or '').replace('Related skill on resume: ', '').replace(
                'Related term found: ', ''
            ).replace('Mentioned in resume text but not in skills section', keyword)
            phrase = (
                f'Use the exact term "{keyword.title()}" in an experience bullet '
                f'(you currently mention "{related}")'
            )
            action_type = 'add_to_experience_bullet'
        elif status == 'underused':
            target = 'Summary'
            reason = 'Keyword appears only once — reinforcing it improves ATS keyword density'
            evidence = f'Currently appears {count}x in resume'
            phrase = (
                f'Reinforce "{keyword.title()}" in your professional summary '
                f'to strengthen keyword density (currently {count}x)'
            )
            action_type = 'add_to_summary'
        else:
            if exp_related:
                target = 'Experience'
                reason = 'JD requires this keyword — your resume has related experience that can be reframed'
                evidence = related_evidence or (
                    f'Related work at {exp_related["company"]} using {exp_related["related_term"]}'
                )
                phrase = (
                    f'Add "{keyword.title()}" to your {exp_related["title"]} bullet at {exp_related["company"]} '
                    f'— you already demonstrate {exp_related["related_term"]}'
                )
                action_type = 'add_to_experience_bullet'
            elif proj_related:
                target = 'Projects'
                reason = 'JD keyword can be surfaced from an existing project on your resume'
                evidence = related_evidence or (
                    f'Project "{proj_related["title"]}" uses {proj_related["related_term"]}'
                )
                phrase = (
                    f'Highlight "{keyword.title()}" in your {proj_related["title"]} project description '
                    f'(related tech: {proj_related["related_term"]})'
                )
                action_type = 'add_to_projects'
            else:
                target = 'Skills'
                reason = 'Required by JD but not found anywhere on your resume'
                evidence = related_evidence or 'No direct or related evidence found in resume'
                phrase = (
                    f'Add "{keyword.title()}" to Skills if you have experience, '
                    f'or pursue learning — it is a {category} requirement for this role'
                )
                action_type = 'learn_new' if category in ('required', 'technical') else 'add_to_skills'

        return {
            'keyword': keyword,
            'target_section': target,
            'priority': priority,
            'status': status,
            'category': category,
            'reason': reason,
            'evidence_from_resume': evidence,
            'suggested_phrase': phrase,
            'action_type': action_type,
        }

    def _build_keyword_enhancement_plan(
        self,
        parsed_resume: Dict[str, Any],
        parsed_jd: Dict[str, Any],
        resume_text: str,
        resume_skills: Set[str],
        req_detail: Dict[str, Any],
        pref_detail: Dict[str, Any],
        keyword_analysis: Dict[str, Any],
        responsibility_analysis: Dict[str, Any],
        keyword_density: Dict[str, int],
    ) -> Dict[str, Any]:
        skills_text = self._get_dedicated_skills_text(parsed_resume)
        categorized = self._collect_jd_keywords_categorized(parsed_jd)

        partial_map: Dict[str, str] = {}
        for detail in req_detail.get('match_details', []) + pref_detail.get('match_details', []):
            if detail.get('match_type') == 'partial':
                partial_map[detail['skill']] = detail.get('evidence') or ''

        missing_keywords_detailed: List[Dict[str, Any]] = []
        add_to_resume: List[Dict[str, Any]] = []
        matched_count = hidden_count = underused_count = partial_count = missing_count = 0

        for item in categorized:
            kw = item['keyword']
            category = item['category']
            priority = item['priority']
            pattern = re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
            in_text = bool(pattern.search(resume_text))
            in_skills = bool(pattern.search(skills_text)) or kw in resume_skills
            count = keyword_density.get(kw, 0) or len(pattern.findall(resume_text))

            if in_text and in_skills and count >= 2:
                matched_count += 1
                continue

            partial_evidence = partial_map.get(kw)
            related_evidence = None

            if partial_evidence:
                status = 'partial'
                partial_count += 1
            elif in_text and not in_skills:
                status = 'hidden'
                hidden_count += 1
            elif in_text and count <= 1:
                status = 'underused'
                underused_count += 1
            elif not in_text:
                status = 'missing'
                missing_count += 1
                related_evidence = self._find_related_resume_evidence(
                    kw, resume_text, resume_skills, parsed_resume
                )
            else:
                matched_count += 1
                continue

            missing_keywords_detailed.append({
                'keyword': kw,
                'category': category,
                'priority': priority,
                'status': status,
                'occurrences_in_resume': count,
                'in_skills_section': in_skills,
                'evidence': partial_evidence or related_evidence,
            })

            add_to_resume.append(self._build_addition_suggestion(
                kw, status, category, priority, count, parsed_resume,
                partial_evidence, related_evidence,
            ))

        for resp in responsibility_analysis.get('missing_responsibilities') or []:
            resp_lower = resp.lower()
            key_terms = [t for t in re.findall(r'[a-z]{4,}', resp_lower) if t not in {
                'with', 'that', 'this', 'will', 'have', 'work', 'team', 'using', 'ability',
            }][:3]
            if not key_terms:
                continue
            resp_pattern = '|'.join(re.escape(t) for t in key_terms[:2])
            if not re.search(resp_pattern, resume_text):
                phrase_terms = ', '.join(t.title() for t in key_terms[:2])
                add_to_resume.append({
                    'keyword': phrase_terms,
                    'target_section': 'Experience',
                    'priority': 4,
                    'status': 'missing',
                    'category': 'responsibility',
                    'reason': 'Job responsibility not reflected in any experience bullet',
                    'evidence_from_resume': 'No matching responsibility language found',
                    'suggested_phrase': (
                        f'Add an experience bullet addressing: "{resp[:100]}{"..." if len(resp) > 100 else ""}"'
                    ),
                    'action_type': 'add_to_experience_bullet',
                })
                missing_keywords_detailed.append({
                    'keyword': phrase_terms,
                    'category': 'responsibility',
                    'priority': 4,
                    'status': 'missing',
                    'occurrences_in_resume': 0,
                    'in_skills_section': False,
                    'evidence': resp[:120],
                })
                missing_count += 1

        status_order = {'missing': 0, 'partial': 1, 'hidden': 2, 'underused': 3}
        missing_keywords_detailed.sort(
            key=lambda x: (-x['priority'], status_order.get(x['status'], 9), x['keyword'])
        )
        add_to_resume.sort(key=lambda x: (-x['priority'], status_order.get(x['status'], 9)))

        total = len(categorized) or 1
        return {
            'coverage_summary': {
                'total_jd_keywords': len(categorized),
                'matched': matched_count,
                'partial': partial_count,
                'hidden': hidden_count,
                'underused': underused_count,
                'missing': missing_count,
                'coverage_percent': keyword_analysis.get('coverage_percent', 0),
                'actionable_additions': len(add_to_resume),
                'fully_optimized': matched_count,
            },
            'missing_keywords_detailed': missing_keywords_detailed[:30],
            'add_to_resume': add_to_resume[:20],
        }

    def _collect_jd_skills_for_matrix(self, parsed_jd: Dict[str, Any]) -> List[Dict[str, str]]:
        """Collect JD skills preserving individual categories for evidence matrix."""
        category_map = [
            ('required_skills', 'required'),
            ('technical_skills', 'technical'),
            ('preferred_skills', 'preferred'),
            ('soft_skills', 'soft'),
        ]
        seen: Set[str] = set()
        items: List[Dict[str, str]] = []
        for key, category in category_map:
            for skill in parsed_jd.get(key) or []:
                skill_lower = str(skill).lower().strip()
                if skill_lower and skill_lower not in seen:
                    seen.add(skill_lower)
                    items.append({'skill': skill_lower, 'category': category})
        return items

    def _get_partial_match_terms(self, skill: str) -> List[str]:
        """Terms used to detect partial matches for a JD skill."""
        terms = []
        aliases = {
            'javascript': ['js', 'node', 'nodejs'],
            'typescript': ['ts'],
            'kubernetes': ['k8s'],
            'amazon web services': ['aws'],
            'machine learning': ['ml', 'deep learning'],
        }
        terms.extend(SKILL_RELATED_TERMS.get(skill, []))
        terms.extend(aliases.get(skill, []))
        return list(dict.fromkeys(t for t in terms if t and t != skill))

    def _extract_snippet(self, text: str, match_start: int, match_end: int, max_len: int = 80) -> str:
        if not text:
            return ''
        start = max(0, match_start - 35)
        end = min(len(text), match_end + 35)
        snippet = text[start:end].strip()
        if start > 0:
            snippet = '...' + snippet
        if end < len(text):
            snippet = snippet + '...'
        return snippet[:max_len]

    def _count_term_occurrences(
        self, text: str, terms: List[str]
    ) -> Tuple[int, Optional[str]]:
        if not text or not terms:
            return 0, None
        total = 0
        snippet = None
        text_lower = text.lower()
        for term in terms:
            pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
            for match in pattern.finditer(text_lower):
                total += 1
                if not snippet:
                    snippet = self._extract_snippet(text, match.start(), match.end())
        return total, snippet

    def _build_skill_evidence_matrix(
        self,
        parsed_resume: Dict[str, Any],
        parsed_jd: Dict[str, Any],
        resume_skills: Set[str],
    ) -> List[Dict[str, Any]]:
        """Build per-JD-skill evidence matrix with section-level occurrence counts."""
        matrix: List[Dict[str, Any]] = []
        jd_skills = self._collect_jd_skills_for_matrix(parsed_jd)

        summary_text = parsed_resume.get('summary') or ''
        skills_parts = []
        for skill in parsed_resume.get('skills') or []:
            skills_parts.append(skill.get('name', '') if isinstance(skill, dict) else str(skill))
        skills_text = ' '.join(skills_parts)

        for item in jd_skills:
            skill = item['skill']
            category = item['category']
            exact_terms = [skill]
            partial_terms = self._get_partial_match_terms(skill)

            evidence: List[Dict[str, Any]] = []
            exact_total = 0
            partial_total = 0

            # Skills section
            skills_count, skills_snippet = self._count_term_occurrences(skills_text, exact_terms)
            if skill in resume_skills:
                skills_count = max(skills_count, 1)
            if skills_count > 0:
                evidence.append({
                    'section': 'skills',
                    'label': 'Skills section',
                    'count': skills_count,
                    'snippet': skills_snippet,
                })
                exact_total += skills_count

            # Summary
            summary_count, summary_snippet = self._count_term_occurrences(summary_text, exact_terms)
            if summary_count > 0:
                evidence.append({
                    'section': 'summary',
                    'label': 'Summary',
                    'count': summary_count,
                    'snippet': summary_snippet,
                })
                exact_total += summary_count

            # Experience entries
            for idx, exp in enumerate(parsed_resume.get('experience') or [], start=1):
                exp_text = ' '.join([
                    exp.get('title', ''),
                    exp.get('company', ''),
                    exp.get('description', ''),
                    ' '.join(exp.get('skills') or []),
                ])
                exp_count, exp_snippet = self._count_term_occurrences(exp_text, exact_terms)
                if exp_count > 0:
                    title = exp.get('title', 'Role')
                    company = exp.get('company', '')
                    label = f'Experience {idx}: {title}'
                    if company:
                        label += f' @ {company}'
                    evidence.append({
                        'section': 'experience',
                        'label': label,
                        'count': exp_count,
                        'snippet': exp_snippet,
                    })
                    exact_total += exp_count

            # Projects
            for idx, project in enumerate(parsed_resume.get('projects') or [], start=1):
                proj_text = ' '.join([
                    project.get('title', ''),
                    project.get('description', ''),
                    ' '.join(project.get('technologies') or []),
                ])
                proj_count, proj_snippet = self._count_term_occurrences(proj_text, exact_terms)
                if proj_count > 0:
                    title = project.get('title', f'Project {idx}')
                    evidence.append({
                        'section': 'projects',
                        'label': f'Project {idx}: {title}',
                        'count': proj_count,
                        'snippet': proj_snippet,
                    })
                    exact_total += proj_count

            # Partial matching if no exact occurrences
            partial_evidence_text = None
            if exact_total == 0 and partial_terms:
                for idx, exp in enumerate(parsed_resume.get('experience') or [], start=1):
                    exp_text = ' '.join([
                        exp.get('title', ''), exp.get('description', ''),
                        ' '.join(exp.get('skills') or []),
                    ])
                    p_count, p_snippet = self._count_term_occurrences(exp_text, partial_terms)
                    if p_count > 0:
                        related = partial_terms[0] if partial_terms else ''
                        evidence.append({
                            'section': 'experience',
                            'label': f'Experience {idx} (as {related})',
                            'count': p_count,
                            'snippet': p_snippet,
                        })
                        partial_total += p_count
                        partial_evidence_text = f'Mentioned as {related} in Experience {idx}'

                for idx, project in enumerate(parsed_resume.get('projects') or [], start=1):
                    proj_text = ' '.join([
                        project.get('title', ''), project.get('description', ''),
                        ' '.join(project.get('technologies') or []),
                    ])
                    p_count, p_snippet = self._count_term_occurrences(proj_text, partial_terms)
                    if p_count > 0:
                        related = partial_terms[0] if partial_terms else ''
                        evidence.append({
                            'section': 'projects',
                            'label': f'Project {idx} (as {related})',
                            'count': p_count,
                            'snippet': p_snippet,
                        })
                        partial_total += p_count
                        if not partial_evidence_text:
                            partial_evidence_text = f'Mentioned as {related} in Project {idx}'

                if partial_total == 0:
                    for res_skill in resume_skills:
                        if len(skill) > 3 and (skill in res_skill or res_skill in skill):
                            partial_total = 1
                            partial_evidence_text = f'Related skill on resume: {res_skill}'
                            evidence.append({
                                'section': 'skills',
                                'label': f'Related skill: {res_skill}',
                                'count': 1,
                                'snippet': res_skill,
                            })
                            break

            total_occurrences = exact_total + partial_total

            if exact_total > 0 or skill in resume_skills:
                match_type = 'exact'
            elif partial_total > 0:
                match_type = 'partial'
            else:
                match_type = 'missing'

            found = match_type != 'missing'

            # Human-readable evidence summary for table display
            if match_type == 'missing':
                evidence_summary = '-'
            else:
                parts = []
                for ev in evidence:
                    if ev.get('label'):
                        parts.append(ev['label'])
                    else:
                        parts.append(ev['section'].title())
                evidence_summary = ', '.join(parts[:4])
                if partial_evidence_text and match_type == 'partial':
                    evidence_summary = partial_evidence_text

            matrix.append({
                'skill': skill,
                'category': category,
                'found': found,
                'found_in_resume': 'Yes' if found else 'No',
                'occurrences': total_occurrences,
                'match_type': match_type,
                'evidence': evidence,
                'evidence_summary': evidence_summary,
            })

        category_order = {'required': 0, 'technical': 1, 'preferred': 2, 'soft': 3}
        matrix.sort(key=lambda x: (category_order.get(x['category'], 9), x['skill']))
        return matrix
