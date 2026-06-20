import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface MatchResult {
  ats_score: number;
  required_skills_match?: number;
  preferred_skills_match?: number;
  experience_match?: number;
  education_match?: number;
  projects_match?: number;
  keyword_coverage?: number;
  responsibility_alignment?: number;
  strengths: any[];
  missing_skills: any[];
  matched_keywords: string[];
  missing_keywords?: string[];
  recommendations: any[];
  keyword_density?: Record<string, number>;
  skill_breakdown?: any;
  score_breakdown?: any[];
  experience_analysis?: any;
  projects_analysis?: any;
  education_analysis?: any;
  responsibility_analysis?: any;
  keyword_analysis?: any;
  keyword_enhancement?: {
    coverage_summary?: {
      total_jd_keywords: number;
      matched: number;
      partial: number;
      hidden: number;
      underused: number;
      missing: number;
      coverage_percent: number;
      actionable_additions: number;
      fully_optimized?: number;
    };
    missing_keywords_detailed?: Array<{
      keyword: string;
      category: string;
      priority: number;
      status: string;
      occurrences_in_resume?: number;
      in_skills_section?: boolean;
      evidence?: string;
    }>;
    add_to_resume?: Array<{
      keyword: string;
      target_section: string;
      priority: number;
      status: string;
      category: string;
      reason: string;
      evidence_from_resume: string;
      suggested_phrase: string;
      action_type: string;
    }>;
  };
  skill_evidence_matrix?: Array<{
    skill: string;
    category: string;
    found: boolean;
    found_in_resume: string;
    occurrences: number;
    match_type: string;
    evidence: Array<{
      section: string;
      label?: string;
      count: number;
      snippet?: string;
    }>;
    evidence_summary: string;
  }>;
  report_meta?: {
    resume_id: number;
    resume_filename: string;
    job_description_id: number;
    job_title: string;
    company?: string;
    overall_resume_score: number;
    score_verdict: string;
    generated_at: string;
  };
}

interface AnalysisState {
  matchResult: MatchResult | null;
  gapAnalysis: any | null;
  optimizationSuggestions: any | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: AnalysisState = {
  matchResult: null,
  gapAnalysis: null,
  optimizationSuggestions: null,
  isLoading: false,
  error: null,
};

const analysisSlice = createSlice({
  name: 'analysis',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setMatchResult: (state, action: PayloadAction<MatchResult>) => {
      state.matchResult = action.payload;
    },
    setGapAnalysis: (state, action: PayloadAction<any>) => {
      state.gapAnalysis = action.payload;
    },
    setOptimizationSuggestions: (state, action: PayloadAction<any>) => {
      state.optimizationSuggestions = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    resetAnalysis: (state) => {
      state.matchResult = null;
      state.gapAnalysis = null;
      state.optimizationSuggestions = null;
      state.error = null;
    },
  },
});

export const { setLoading, setMatchResult, setGapAnalysis, setOptimizationSuggestions, setError, resetAnalysis } = analysisSlice.actions;
export default analysisSlice.reducer;
