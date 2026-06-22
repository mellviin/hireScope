"""
Job Description Analyzer Service
Converts raw job descriptions into structured schemas using NLP and rule-based extraction.

Extraction pipeline (4 strategies, merged by trust level):
  1. FlashText whitelist scan        — O(n) Aho-Corasick, highest precision
  2. Section-based keyword parsing   — catches explicit skill lists in JD
  3. spaCy NER + noun chunks         — catches proper nouns / tech names
  4. KeyBERT semantic extraction     — catches domain terms not in whitelist
     (lazy-loaded on first use; gracefully skipped if unavailable)

Performance design:
  - spaCy runs ONCE per analyze_jd() call; doc object shared across all strategies
  - KeyBERT runs ONCE per analyze_jd() call; results shared between skill + keyword extraction
  - FlashText replaces O(N*M) regex loop with O(text_length) Aho-Corasick scan
  - KeyBERT is lazy-loaded on first actual use, not at __init__, to save Render cold-start RAM
"""
import re
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import Counter

import spacy
from flashtext import KeywordProcessor

from app.utils.logging import setup_logging
from app.utils.exceptions import ProcessingError

logger = setup_logging(__name__)


# ---------------------------------------------------------------------------
# Skill taxonomy — extend these lists to improve coverage for new domains
# ---------------------------------------------------------------------------

TECHNICAL_SKILLS: Dict[str, List[str]] = {
    'languages': [
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby',
        'php', 'swift', 'kotlin', 'go', 'rust', 'scala', 'r', 'matlab',
        'sql', 'html', 'css', 'bash', 'shell', 'groovy', 'perl', 'dart',
    ],
    'frameworks': [
        'spring', 'spring boot', 'django', 'flask', 'fastapi', 'nodejs',
        'express', 'react', 'angular', 'vue', 'next.js', 'nuxt', 'svelte',
        'asp.net', 'rails', 'laravel', 'kubernetes', 'docker', 'kafka',
        'spark', 'hadoop', 'pytorch', 'tensorflow', 'scikit-learn', 'pandas',
        'numpy', 'celery', 'graphql', 'rest api', 'grpc',
    ],
    'databases': [
        'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
        'cassandra', 'dynamodb', 'oracle', 'sql server', 'sqlite',
        'firebase', 'supabase', 'neo4j', 'influxdb',
    ],
    'cloud': [
        'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'digital ocean',
        'cloudflare', 'vercel', 'netlify', 'render',
    ],
    'devops': [
        'docker', 'kubernetes', 'jenkins', 'gitlab', 'github', 'circleci',
        'terraform', 'ansible', 'cloudformation', 'prometheus', 'grafana',
        'datadog', 'splunk', 'nginx', 'linux', 'git',
    ],
    'testing': [
        'junit', 'mockito', 'pytest', 'jest', 'selenium', 'cypress',
        'postman', 'jmeter', 'unit testing', 'integration testing',
        'test driven development', 'tdd', 'bdd',
    ],
}

SOFT_SKILLS: List[str] = [
    'communication', 'teamwork', 'leadership', 'project management',
    'problem solving', 'analytical', 'agile', 'scrum', 'initiative',
    'organization', 'attention to detail', 'time management', 'collaboration',
    'critical thinking', 'adaptability', 'creativity', 'multitasking',
    'customer service', 'negotiation', 'presentation', 'mentoring',
    'conflict resolution', 'decision making', 'emotional intelligence',
    'active listening', 'interpersonal skills', 'written communication',
    'verbal communication', 'cross-functional', 'stakeholder management',
    'fast learner', 'self-motivated', 'detail-oriented', 'proactive',
]

DOMAIN_SKILLS_WHITELIST: Set[str] = {
    # Customer service / support
    'chat', 'live chat', 'ticketing', 'zendesk', 'freshdesk', 'intercom',
    'crm', 'salesforce', 'customer support', 'customer service', 'help desk',
    'technical support', 'call center', 'contact center', 'escalation',
    'sla management', 'service desk', 'client relations', 'account management',
    'voice support', 'email support', 'chat support', 'troubleshooting',
    # General business / productivity
    'microsoft office', 'excel', 'word', 'powerpoint', 'outlook',
    'google workspace', 'google sheets', 'google docs', 'slack', 'jira',
    'confluence', 'trello', 'asana', 'notion', 'data entry', 'reporting',
    'documentation', 'research', 'analysis', 'budgeting', 'forecasting',
    'invoicing', 'billing', 'scheduling', 'coordination',
    # Marketing / content / design
    'seo', 'sem', 'google analytics', 'social media', 'content marketing',
    'email marketing', 'copywriting', 'adobe creative suite', 'figma',
    'canva', 'photoshop', 'illustrator', 'indesign', 'ux design', 'ui design',
    'wireframing', 'prototyping', 'user research', 'a/b testing',
    # Finance / accounting
    'accounting', 'bookkeeping', 'financial reporting', 'auditing', 'taxation',
    'accounts payable', 'accounts receivable', 'tally', 'quickbooks', 'sap',
    'financial analysis', 'cost accounting', 'reconciliation', 'payroll',
    # HR / operations
    'recruitment', 'onboarding', 'performance management', 'training',
    'compliance', 'operations management', 'vendor management', 'procurement',
    'supply chain', 'inventory management', 'quality assurance', 'qa',
    # Data / analytics
    'data analysis', 'data visualization', 'tableau', 'power bi', 'looker',
    'excel advanced', 'pivot tables', 'sql queries', 'etl', 'data pipelines',
    'machine learning', 'deep learning', 'nlp', 'computer vision',
    'statistics', 'data science', 'jupyter', 'r studio',
    # Healthcare
    'hipaa', 'ehr', 'emr', 'medical coding', 'clinical documentation',
}

ACRONYMS: Set[str] = {
    'sql', 'html', 'css', 'api', 'crm', 'erp', 'aws', 'gcp', 'seo',
    'sem', 'sla', 'qa', 'etl', 'nlp', 'ai', 'ml', 'ui', 'ux',
    'tdd', 'bdd', 'ci', 'cd', 'sdk', 'ide', 'ehr', 'emr',
}

# Signals that a text fragment is a sentence, not a skill name
FRAGMENT_SIGNALS = re.compile(
    r'\b('
    r'our|their|your|we|they|this|that|these|those|which|where|when|who|whom|'
    r'required to|ability to|responsible for|experience in|knowledge of|'
    r'proficiency in|familiarity with|understanding of|exposure to|'
    r'good at|skilled in|worked with|working with|background in|'
    r'must be|should be|will be|you will|you must|you should|'
    r'including but|as well as|such as|e\.g\.|i\.e\.'
    r')\b',
    re.IGNORECASE,
)

STOPWORDS: Set[str] = {
    'the', 'a', 'an', 'is', 'are', 'was', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'shall', 'can', 'need',
    'not', 'no', 'nor', 'so', 'yet', 'both', 'either', 'neither',
    'and', 'or', 'but', 'if', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through',
}

REQUIRED_SECTION_KEYWORDS = [
    'required', 'must have', 'essential', 'mandatory', 'required skills',
    'you need', 'we need', 'need to have',
]

PREFERRED_SECTION_KEYWORDS = [
    'preferred', 'nice to have', 'bonus', 'desirable', 'preferred skills',
    'good to have', 'plus', 'advantage',
]

EXPERIENCE_LEVELS: Dict[str, str] = {
    'entry':     r'entry\s*(?:level|position)|junior|fresh\s*(?:graduate|pass)',
    'mid':       r'mid\s*(?:level|career)|intermediate|3\s*-\s*5\s+years?',
    'senior':    r'senior|lead|principal|5\s*-\s*10\s+years?|10\+\s+years?',
    'executive': r'executive|director|c-suite|vp|vice\s+president',
}


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------

class JDAnalyzer:
    """
    Job Description Analyzer — spaCy + FlashText + KeyBERT (lazy).

    Performance characteristics:
      - spaCy  : 1 pass per request, doc shared across all strategies
      - KeyBERT: lazy-loaded on first use (not at startup), 1 call per request,
                 results cached in _keybert_cache for skill + keyword extraction
      - FlashText: O(text_length) whitelist scan via Aho-Corasick (replaces O(N*M) regex)
    """

    def __init__(self):
        # spaCy — required, loaded at startup
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy loaded")
        except OSError:
            logger.error("spaCy model missing. Run: python -m spacy download en_core_web_sm")
            raise ProcessingError("NLP model not available")

        # KeyBERT — NOT loaded here; lazy-loaded on first analyze_jd() call
        # This keeps Render cold-start memory low (~200MB instead of ~400MB)
        self._keybert = None
        self._keybert_attempted = False   # only try loading once

        # Build unified skill set for validation
        self._all_technical: Set[str] = {
            s.lower() for skills in TECHNICAL_SKILLS.values() for s in skills
        }
        self._all_soft: Set[str] = {s.lower() for s in SOFT_SKILLS}
        self._all_known: Set[str] = self._all_technical | self._all_soft | DOMAIN_SKILLS_WHITELIST

        # FlashText processor — O(text_length) Aho-Corasick scan
        # Replaces the O(N_skills * text_length) regex loop
        self._skill_processor = KeywordProcessor(case_sensitive=False)
        for skill in self._all_known:
            # Map each skill to its display form (title-cased)
            self._skill_processor.add_keyword(skill, self._title_skill(skill))

        logger.info(f"FlashText loaded with {len(self._all_known)} skills")

    # ------------------------------------------------------------------
    # Lazy KeyBERT loader
    # ------------------------------------------------------------------

    def _load_keybert(self) -> None:
        """
        Load KeyBERT on first use, not at startup.
        Sets self._keybert = None permanently if unavailable, so we never retry.
        """
        if self._keybert_attempted:
            return
        self._keybert_attempted = True
        try:
            from keybert import KeyBERT
            self._keybert = KeyBERT()
            logger.info("KeyBERT loaded (lazy)")
        except Exception as e:
            logger.warning(f"KeyBERT unavailable — semantic extraction disabled: {e}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_jd(
        self,
        job_title: str,
        content: str,
        company: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            content = self._clean_text(content)

            # --- ONE spaCy pass, shared everywhere ---
            doc = self.nlp(content[:5000])

            # --- ONE KeyBERT pass, results reused for both skill + keyword extraction ---
            keybert_results = self._run_keybert_once(content)

            required_skills, preferred_skills = self._extract_skills(content, doc, keybert_results)
            tech_skills      = self._extract_technical_skills(content)
            soft_skills      = self._extract_soft_skills(content)
            responsibilities = self._extract_responsibilities(content)
            requirements     = self._extract_requirements(content)
            experience_level = self._detect_experience_level(content)
            years_exp        = self._extract_years_of_experience(content)
            education        = self._extract_education_requirements(content)
            keywords         = self._build_keywords(doc, keybert_results)

            return {
                'job_title':              job_title,
                'company':                company,
                'required_skills':        required_skills,
                'preferred_skills':       preferred_skills,
                'technical_skills':       tech_skills,
                'soft_skills':            soft_skills,
                'responsibilities':       responsibilities,
                'requirements':           requirements,
                'experience_level':       experience_level,
                'years_of_experience':    years_exp,
                'education_requirements': education,
                'keywords':               keywords,
            }

        except Exception as e:
            logger.error(f"JD analysis failed: {e}")
            raise ProcessingError(f"Failed to analyze job description: {e}")

    # ------------------------------------------------------------------
    # Single KeyBERT call — results reused by skills + keywords
    # ------------------------------------------------------------------

    def _run_keybert_once(self, content: str) -> List[Tuple[str, float]]:
        """
        Run KeyBERT once and return raw (phrase, score) pairs.
        Returns [] if KeyBERT is unavailable.
        Uses ngram range (1,3) to serve both skill extraction (1-2) and
        keyword extraction (1-3) — filtered downstream.
        """
        self._load_keybert()
        if self._keybert is None:
            return []
        try:
            return self._keybert.extract_keywords(
                content[:5000],
                keyphrase_ngram_range=(1, 3),
                stop_words='english',
                top_n=30,
                use_mmr=True,
                diversity=0.5,
            )
        except Exception as e:
            logger.warning(f"KeyBERT call failed: {e}")
            return []

    # ------------------------------------------------------------------
    # Master skill extractor — merges 4 strategies
    # ------------------------------------------------------------------

    def _extract_skills(
        self,
        content: str,
        doc,                              # pre-computed spaCy doc
        keybert_results: List[Tuple[str, float]],
    ) -> Tuple[List[str], List[str]]:

        content_lower = content.lower()

        # Strategy 1: FlashText whitelist scan — O(text_length), highest precision
        whitelist_hits = self._scan_whitelist(content_lower)

        # Strategy 2: section-based parsing — explicit skill lists
        section_required, section_preferred = self._parse_skill_sections(content_lower)

        # Strategy 3: spaCy NER + noun chunks — uses shared doc, zero extra cost
        nlp_skills = self._extract_via_spacy(doc)

        # Strategy 4: KeyBERT — filter shared results to 1-2 word valid skills
        keybert_skills = [
            self._title_skill(phrase)
            for phrase, score in keybert_results
            if score >= 0.25
            and len(phrase.split()) <= 2
            and self._is_valid_skill(phrase)
        ]
        keybert_skills = list(dict.fromkeys(keybert_skills))

        # Merge by trust level
        required = list(dict.fromkeys(
            whitelist_hits + section_required + nlp_skills + keybert_skills
        ))
        preferred = list(dict.fromkeys(
            s for s in section_preferred if s not in required
        ))

        return required[:20], preferred[:20]

    # ------------------------------------------------------------------
    # Strategy 1 — FlashText whitelist scan
    # ------------------------------------------------------------------

    def _scan_whitelist(self, content_lower: str) -> List[str]:
        """O(text_length) Aho-Corasick scan via FlashText."""
        found = self._skill_processor.extract_keywords(content_lower)
        return list(dict.fromkeys(found))  # preserve order, deduplicate

    # ------------------------------------------------------------------
    # Strategy 2 — section-based parsing
    # ------------------------------------------------------------------

    def _parse_skill_sections(self, content_lower: str) -> Tuple[List[str], List[str]]:
        required, preferred = [], []

        for kw in REQUIRED_SECTION_KEYWORDS:
            for m in re.finditer(
                rf'{re.escape(kw)}[:\s].*?(?=\n|$)',
                content_lower, re.IGNORECASE | re.MULTILINE
            ):
                required.extend(self._tokenize_skill_line(m.group(0)))

        for kw in PREFERRED_SECTION_KEYWORDS:
            for m in re.finditer(
                rf'{re.escape(kw)}[:\s].*?(?=\n|$)',
                content_lower, re.IGNORECASE | re.MULTILINE
            ):
                preferred.extend(self._tokenize_skill_line(m.group(0)))

        required  = list(dict.fromkeys(required))
        preferred = list(dict.fromkeys(s for s in preferred if s not in required))
        return required, preferred

    def _tokenize_skill_line(self, text: str) -> List[str]:
        skills = []
        for raw in re.split(r'[,;•|\-–/]', text):
            token = raw.strip()
            token = re.sub(r'^(and|or|the|a|an|to|with|for|in|of)\s+', '', token, flags=re.IGNORECASE)
            token = re.sub(r'\s+(and|or)$', '', token, flags=re.IGNORECASE).strip()
            if token and self._is_valid_skill(token):
                skills.append(self._title_skill(token))
        return skills

    # ------------------------------------------------------------------
    # Strategy 3 — spaCy (uses shared doc)
    # ------------------------------------------------------------------

    def _extract_via_spacy(self, doc) -> List[str]:
        """Uses the pre-computed doc — zero extra NLP cost."""
        skills = []
        for ent in doc.ents:
            if ent.label_ in ('ORG', 'PRODUCT'):
                candidate = ent.text.strip()
                if self._is_valid_skill(candidate):
                    skills.append(self._title_skill(candidate))
        for chunk in doc.noun_chunks:
            words = chunk.text.split()
            if 1 <= len(words) <= 2 and chunk.text.strip().lower() in self._all_known:
                skills.append(self._title_skill(chunk.text.strip()))
        return list(dict.fromkeys(skills))

    # ------------------------------------------------------------------
    # Keyword extraction — reuses shared spaCy doc + KeyBERT results
    # ------------------------------------------------------------------

    def _build_keywords(self, doc, keybert_results: List[Tuple[str, float]]) -> List[str]:
        """
        Build keyword list from pre-computed KeyBERT results (1-3 grams).
        Falls back to spaCy noun chunks if KeyBERT unavailable.
        No extra NLP calls made here.
        """
        if keybert_results:
            return [phrase for phrase, _ in keybert_results[:15]]

        # spaCy fallback — still uses shared doc
        keywords = []
        for chunk in doc.noun_chunks:
            if 2 <= len(chunk.text.split()) <= 3 and len(chunk.text) > 3:
                keywords.append(chunk.text.lower())
        for ent in doc.ents:
            if ent.label_ in ('ORG', 'PRODUCT', 'GPE'):
                keywords.append(ent.text.lower())
        return [kw for kw, _ in Counter(keywords).most_common(15)]

    # ------------------------------------------------------------------
    # Skill validator
    # ------------------------------------------------------------------

    def _is_valid_skill(self, text: str) -> bool:
        text = text.strip()
        if not text or len(text) < 2 or len(text) > 35:
            return False
        if text[0].isdigit():
            return False
        words = text.split()
        if len(words) > 4:
            return False
        if FRAGMENT_SIGNALS.search(text):
            return False
        word_set = set(w.lower() for w in words)
        if word_set.issubset(STOPWORDS):
            return False
        if text.lower() in self._all_known:
            return True
        if len(words) <= 2 and not word_set.issubset(STOPWORDS):
            return True
        return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _title_skill(self, skill: str) -> str:
        parts = skill.strip().split()
        return ' '.join(p.upper() if p.lower() in ACRONYMS else p.capitalize() for p in parts)

    # ------------------------------------------------------------------
    # Remaining extractors
    # ------------------------------------------------------------------

    def _extract_technical_skills(self, content: str) -> List[str]:
        content_lower = content.lower()
        skills = []
        for skill_list in TECHNICAL_SKILLS.values():
            for skill in skill_list:
                if re.search(r'\b' + re.escape(skill) + r'\b', content_lower):
                    skills.append(self._title_skill(skill))
        return list(dict.fromkeys(skills))

    def _extract_soft_skills(self, content: str) -> List[str]:
        content_lower = content.lower()
        skills = []
        for skill in SOFT_SKILLS:
            if re.search(r'\b' + re.escape(skill) + r'\b', content_lower):
                skills.append(skill.title())
        return list(dict.fromkeys(skills))

    def _extract_responsibilities(self, content: str) -> List[str]:
        responsibilities = []
        for pattern in [r'[•*-]\s*([^•*\n-][^\n]+)', r'^\d+\.\s+([^\n]+)']:
            for match in re.finditer(pattern, content, re.MULTILINE):
                resp = match.group(1).strip()
                if 10 < len(resp) < 300:
                    responsibilities.append(resp)
        return list(dict.fromkeys(responsibilities))[:10]

    def _extract_requirements(self, content: str) -> List[Dict[str, Any]]:
        requirements = []
        req_match = re.search(r'requirements?.*?(?=\n\n|\nwhat|$)', content, re.IGNORECASE | re.DOTALL)
        if req_match:
            for item in re.findall(r'[•*-]\s*([^\n•*-]+)', req_match.group(0)):
                item = item.strip()
                if 5 < len(item) < 200:
                    requirements.append({'requirement': item, 'category': 'general', 'priority': 2})
        return requirements[:15]

    def _clean_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        return text.strip()

    def _detect_experience_level(self, content: str) -> str:
        content_lower = content.lower()
        for level, pattern in EXPERIENCE_LEVELS.items():
            if re.search(pattern, content_lower):
                return level
        return 'mid'

    def _extract_years_of_experience(self, content: str) -> Optional[int]:
        matches = []
        for pattern in [r'(\d+)\+?\s*(?:years?|yrs?)', r'(\d+)\s*-\s*(\d+)\s*(?:years?|yrs?)']:
            found = re.search(pattern, content, re.IGNORECASE)
            if found:
                matches.append(int(found.group(1)))
        return min(matches) if matches else None

    def _extract_education_requirements(self, content: str) -> List[str]:
        edu_patterns = {
            'Bachelor':    r"Bachelor('s)?|B\.?S\.?|B\.?A\.?",
            'Master':      r"Master('s)?|M\.?S\.?|M\.?B\.?A\.?",
            'PhD':         r'PhD|Ph\.D\.|Doctorate',
            'Associates':  r"Associate('s)?|A\.?S\.?",
            'High School': r'High School|GED|Secondary',
        }
        return [deg for deg, pat in edu_patterns.items() if re.search(pat, content, re.IGNORECASE)]