import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../redux/store';
import { analysisAPI } from '../services/api';
import { setMatchResult, setGapAnalysis, setOptimizationSuggestions } from '../redux/slices/analysisSlice';
import { ATSScoreCard } from '../components/ATSScoreCard';
import { SkillsList } from '../components/SkillBadge';
import { ErrorBanner } from '../components/ErrorBanner';
import { SkillEvidenceMatrix } from '../components/SkillEvidenceMatrix';

const getScoreStyles = (score: number) => {
  if (score >= 80) return { text: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200' };
  if (score >= 60) return { text: 'text-yellow-600', bg: 'bg-yellow-50', border: 'border-yellow-200' };
  if (score >= 40) return { text: 'text-orange-600', bg: 'bg-orange-50', border: 'border-orange-200' };
  return { text: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200' };
};

const CATEGORY_LABELS: Record<string, string> = {
  required_skills: 'Required Skills',
  preferred_skills: 'Preferred Skills',
  experience: 'Experience',
  projects: 'Projects',
  education: 'Education',
  responsibilities: 'Responsibilities',
  keywords: 'Keywords & ATS',
};

const KEYWORD_STATUS_LABELS: Record<string, { label: string; color: string }> = {
  missing: { label: 'Missing', color: 'bg-red-100 text-red-800' },
  partial: { label: 'Partial Match', color: 'bg-orange-100 text-orange-800' },
  hidden: { label: 'Hidden in Body', color: 'bg-yellow-100 text-yellow-800' },
  underused: { label: 'Underused', color: 'bg-blue-100 text-blue-800' },
};

const KEYWORD_CATEGORY_LABELS: Record<string, string> = {
  required: 'Required',
  technical: 'Technical',
  preferred: 'Preferred',
  soft: 'Soft Skill',
  general: 'General',
  responsibility: 'Responsibility',
};

const formatDetails = (details: string | string[] | undefined) => {
  if (Array.isArray(details)) return details.filter(Boolean);
  return details ? [details] : [];
};

const ImpactBadge: React.FC<{ impact: string }> = ({ impact }) => {
  const colors: Record<string, string> = {
    high: 'bg-red-100 text-red-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-gray-100 text-gray-700',
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${colors[impact] || colors.medium}`}>
      {impact} impact
    </span>
  );
};

const SkillBreakdownSection: React.FC<{ title: string; data: any; color: string }> = ({ title, data, color }) => {
  if (!data || data.total === 0) return null;
  return (
    <div className="mb-6">
      <h4 className={`font-bold mb-3 ${color}`}>{title} ({data.score}% match — {data.matched_exact?.length + data.matched_partial?.length}/{data.total})</h4>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {data.matched_exact?.length > 0 && (
          <div className="bg-green-50 p-4 rounded-lg">
            <p className="font-semibold text-green-800 mb-2">Exact Matches</p>
            <SkillsList skills={data.matched_exact.map((s: string) => ({ skill: s }))} maxDisplay={20} />
          </div>
        )}
        {data.matched_partial?.length > 0 && (
          <div className="bg-yellow-50 p-4 rounded-lg">
            <p className="font-semibold text-yellow-800 mb-2">Partial Matches</p>
            <SkillsList skills={data.matched_partial.map((s: string) => ({ skill: s }))} maxDisplay={20} />
          </div>
        )}
        {data.missing?.length > 0 && (
          <div className="bg-red-50 p-4 rounded-lg">
            <p className="font-semibold text-red-800 mb-2">Missing</p>
            <SkillsList skills={data.missing.map((s: string) => ({ skill: s }))} maxDisplay={20} />
          </div>
        )}
      </div>
    </div>
  );
};

export const MatchResults: React.FC = () => {
  const { resumeId, jdId } = useParams<{ resumeId: string; jdId: string }>();
  const resumeIdNum = Number(resumeId);
  const jdIdNum = Number(jdId);
  const [activeTab, setActiveTab] = useState<'overview' | 'skills' | 'keywords' | 'gaps' | 'optimize'>('overview');
  const [isLoading, setIsLoading] = useState(true);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const dispatch = useDispatch();
  const { matchResult, gapAnalysis, optimizationSuggestions } = useSelector((state: RootState) => state.analysis);

  useEffect(() => {
    if (!resumeIdNum || !jdIdNum) {
      setError('Invalid resume or job description selected.');
      setIsLoading(false);
      return;
    }

    const fetchAnalysis = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [matchRes, gapRes, optRes] = await Promise.all([
          analysisAPI.calculateMatch({ resume_id: resumeIdNum, job_description_id: jdIdNum }),
          analysisAPI.getGapAnalysis({ resume_id: resumeIdNum, job_description_id: jdIdNum }),
          analysisAPI.getOptimizations({ resume_id: resumeIdNum, job_description_id: jdIdNum }),
        ]);
        dispatch(setMatchResult(matchRes.data));
        dispatch(setGapAnalysis(gapRes.data));
        dispatch(setOptimizationSuggestions(optRes.data));
      } catch (err: any) {
        const detail = err.response?.data?.detail;
        setError(typeof detail === 'string' ? detail : 'Failed to load analysis results.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchAnalysis();
  }, [resumeIdNum, jdIdNum, dispatch]);

  const reportMeta = matchResult?.report_meta;
  const overallScore = reportMeta?.overall_resume_score ?? matchResult?.ats_score ?? 0;
  const scoreStyles = getScoreStyles(overallScore);

  const handleDownloadReport = async () => {
    setIsDownloading(true);
    setDownloadError(null);
    try {
      const response = await analysisAPI.downloadReport({
        resume_id: resumeIdNum,
        job_description_id: jdIdNum,
      });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const jobTitle = reportMeta?.job_title || 'Job';
      link.download = `ATS_Report_${jobTitle.replace(/[^\w.-]/g, '_')}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      setDownloadError('Failed to download ATS report. Please try again.');
    } finally {
      setIsDownloading(false);
    }
  };

  if (isLoading) {
    return <div className="p-6 text-center">Running in-depth analysis...</div>;
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <ErrorBanner message={error} />
      </div>
    );
  }

  const keywordEnhancement = matchResult?.keyword_enhancement ?? gapAnalysis?.keyword_enhancement;

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'skills', label: 'Skills Deep Dive' },
    { id: 'keywords', label: 'Keywords & Additions' },
    { id: 'gaps', label: 'Gaps & Priorities' },
    { id: 'optimize', label: 'Optimize Resume' },
  ] as const;

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">Match Analysis Results</h1>
          <p className="text-gray-600">Resume compatibility scored against this specific job description</p>
        </div>
        <button
          onClick={handleDownloadReport}
          disabled={isDownloading}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 font-semibold whitespace-nowrap flex items-center gap-2"
        >
          {isDownloading ? 'Generating PDF...' : 'Download ATS Report (PDF)'}
        </button>
      </div>

      {downloadError && <ErrorBanner message={downloadError} />}

      {matchResult && (
        <div className={`mb-6 rounded-xl border-2 p-8 ${scoreStyles.bg} ${scoreStyles.border}`}>
          <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">
            Overall Resume Score for This Job
          </p>
          {reportMeta && (
            <div className="mb-4">
              <p className="text-lg font-semibold text-gray-800">
                {reportMeta.job_title}
                {reportMeta.company ? ` @ ${reportMeta.company}` : ''}
              </p>
              <p className="text-sm text-gray-600">Resume: {reportMeta.resume_filename}</p>
            </div>
          )}
          <div className="flex flex-wrap items-end gap-4">
            <span className={`text-6xl font-bold ${scoreStyles.text}`}>
              {overallScore.toFixed(1)}
            </span>
            <span className="text-2xl text-gray-500 mb-2">/ 100</span>
            <span className={`text-xl font-semibold mb-2 ${scoreStyles.text}`}>
              {reportMeta?.score_verdict || (overallScore >= 80 ? 'Excellent Match' : overallScore >= 60 ? 'Good Match' : overallScore >= 40 ? 'Moderate Match' : 'Needs Improvement')}
            </span>
          </div>
          <p className="text-gray-600 mt-3 text-sm">
            This score reflects how well your resume matches the requirements, keywords, experience, and responsibilities of this job posting.
          </p>
        </div>
      )}

      {matchResult && (
        <div className="mb-6 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <ATSScoreCard score={overallScore} title="Overall Score" />
          <ATSScoreCard score={matchResult.required_skills_match ?? 0} title="Required Skills" />
          <ATSScoreCard score={matchResult.preferred_skills_match ?? 0} title="Preferred Skills" />
          <ATSScoreCard score={matchResult.experience_match ?? 0} title="Experience" />
          <ATSScoreCard score={matchResult.keyword_coverage ?? 0} title="Keyword Coverage" />
          <ATSScoreCard score={matchResult.responsibility_alignment ?? 0} title="Responsibilities" />
        </div>
      )}

      <div className="bg-white rounded-lg shadow-md">
        <div className="flex border-b overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-3 font-semibold whitespace-nowrap ${
                activeTab === tab.id ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="p-6">
          {activeTab === 'overview' && matchResult && (
            <div className="space-y-8">
              {matchResult.score_breakdown && (
                <section>
                  <h3 className="text-xl font-bold mb-4">Score Breakdown</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b text-left text-gray-600">
                          <th className="py-2 pr-4">Category</th>
                          <th className="py-2 pr-4">Score</th>
                          <th className="py-2 pr-4">Weight</th>
                          <th className="py-2">Contribution</th>
                        </tr>
                      </thead>
                      <tbody>
                        {matchResult.score_breakdown
                          .filter((row: any) => row.category !== 'total')
                          .map((row: any) => (
                            <tr key={row.category} className="border-b">
                              <td className="py-2 pr-4 font-medium">{row.label || row.category}</td>
                              <td className="py-2 pr-4">{row.score}%</td>
                              <td className="py-2 pr-4">{row.weight_percent}%</td>
                              <td className="py-2">{row.weighted_contribution} pts</td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              )}

              {matchResult.experience_analysis && (
                <section>
                  <h3 className="text-xl font-bold mb-3">Experience Analysis</h3>
                  <p className="text-gray-700 mb-2">{matchResult.experience_analysis.gap_summary}</p>
                  {matchResult.experience_analysis.role_details?.length > 0 && (
                    <div className="space-y-2">
                      {matchResult.experience_analysis.role_details.map((role: any, idx: number) => (
                        <div key={idx} className="bg-gray-50 p-3 rounded flex justify-between items-start">
                          <div>
                            <p className="font-semibold">{role.title} @ {role.company}</p>
                            <p className="text-sm text-gray-600">{role.duration}</p>
                          </div>
                          <span className={`text-xs px-2 py-1 rounded ${
                            role.relevance === 'high' ? 'bg-green-100 text-green-800' :
                            role.relevance === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-600'
                          }`}>{role.relevance} relevance</span>
                        </div>
                      ))}
                    </div>
                  )}
                </section>
              )}

              <section>
                <h3 className="text-xl font-bold mb-4">Key Strengths</h3>
                <div className="space-y-3">
                  {matchResult.strengths?.length ? matchResult.strengths.map((strength: any, idx: number) => (
                    <div key={idx} className="bg-green-50 p-4 rounded-lg">
                      <div className="flex justify-between items-center mb-1">
                        <p className="font-semibold text-green-800">
                          {CATEGORY_LABELS[strength.category] || strength.category}
                        </p>
                        <span className="text-green-700 font-bold">{strength.score?.toFixed?.(1) ?? strength.score}%</span>
                      </div>
                      <ul className="list-disc list-inside text-gray-700 text-sm space-y-1">
                        {formatDetails(strength.details).map((d, i) => (
                          <li key={i}>{d}</li>
                        ))}
                      </ul>
                    </div>
                  )) : (
                    <p className="text-gray-600">Upload a more detailed resume to surface strengths.</p>
                  )}
                </div>
              </section>

              {matchResult.recommendations?.length > 0 && (
                <section>
                  <h3 className="text-xl font-bold mb-4">Top Recommendations</h3>
                  <div className="space-y-3">
                    {matchResult.recommendations.slice(0, 5).map((rec: any, idx: number) => (
                      <div key={idx} className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-500">
                        <p className="font-semibold">{rec.suggestion}</p>
                        <p className="text-gray-600 text-sm mt-1">{rec.reason}</p>
                        <span className="text-xs text-blue-600 mt-1 inline-block">Priority {rec.priority}/5</span>
                      </div>
                    ))}
                  </div>
                </section>
              )}
            </div>
          )}

          {activeTab === 'skills' && matchResult?.skill_breakdown && (
            <div>
              <SkillBreakdownSection title="Required & Technical Skills" data={matchResult.skill_breakdown.required} color="text-red-700" />
              <SkillBreakdownSection title="Preferred & Soft Skills" data={matchResult.skill_breakdown.preferred} color="text-blue-700" />

              {matchResult.skill_evidence_matrix && matchResult.skill_evidence_matrix.length > 0 && (
                <section className="mt-8 pt-8 border-t">
                  <SkillEvidenceMatrix data={matchResult.skill_evidence_matrix} />
                </section>
              )}

              {matchResult.keyword_density && Object.keys(matchResult.keyword_density).length > 0 && (
                <section className="mt-6">
                  <h3 className="text-xl font-bold mb-3">Keyword Frequency in Resume</h3>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(matchResult.keyword_density).map(([kw, count]) => (
                      <span key={kw} className="bg-purple-50 text-purple-800 px-3 py-1 rounded-full text-sm">
                        {kw} <strong>({count as number}x)</strong>
                      </span>
                    ))}
                  </div>
                </section>
              )}

              {matchResult.missing_keywords?.length > 0 && (
                <section className="mt-6">
                  <h3 className="text-xl font-bold mb-3 text-orange-700">Missing ATS Keywords</h3>
                  <SkillsList skills={matchResult.missing_keywords.map((s: string) => ({ skill: s }))} maxDisplay={20} />
                </section>
              )}
            </div>
          )}

          {activeTab === 'keywords' && keywordEnhancement && (
            <div className="space-y-8">
              {keywordEnhancement.coverage_summary && (
                <section>
                  <h3 className="text-xl font-bold mb-4">Keyword Coverage Summary</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 mb-4">
                    {[
                      { label: 'JD Keywords', value: keywordEnhancement.coverage_summary.total_jd_keywords, color: 'text-gray-800' },
                      { label: 'Matched', value: keywordEnhancement.coverage_summary.matched, color: 'text-green-700' },
                      { label: 'Partial', value: keywordEnhancement.coverage_summary.partial, color: 'text-orange-700' },
                      { label: 'Hidden', value: keywordEnhancement.coverage_summary.hidden, color: 'text-yellow-700' },
                      { label: 'Underused', value: keywordEnhancement.coverage_summary.underused, color: 'text-blue-700' },
                      { label: 'Missing', value: keywordEnhancement.coverage_summary.missing, color: 'text-red-700' },
                      { label: 'Coverage', value: `${keywordEnhancement.coverage_summary.coverage_percent}%`, color: 'text-purple-700' },
                    ].map(({ label, value, color }) => (
                      <div key={label} className="bg-gray-50 rounded-lg p-3 text-center">
                        <p className="text-xs text-gray-500 font-medium">{label}</p>
                        <p className={`text-xl font-bold ${color}`}>{value}</p>
                      </div>
                    ))}
                  </div>
                  <p className="text-sm text-gray-600">
                    {keywordEnhancement.coverage_summary.actionable_additions} actionable additions identified from your existing resume content.
                  </p>
                </section>
              )}

              {keywordEnhancement.missing_keywords_detailed?.length > 0 && (
                <section>
                  <h3 className="text-xl font-bold mb-2 text-red-700">Keywords You Missed</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    JD keywords not fully present on your resume — sorted by priority and impact on ATS matching.
                  </p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b text-left text-gray-600">
                          <th className="py-2 pr-4">Keyword</th>
                          <th className="py-2 pr-4">Category</th>
                          <th className="py-2 pr-4">Status</th>
                          <th className="py-2 pr-4">In Resume</th>
                          <th className="py-2">Evidence / Gap</th>
                        </tr>
                      </thead>
                      <tbody>
                        {keywordEnhancement.missing_keywords_detailed.map((item: any, idx: number) => {
                          const statusMeta = KEYWORD_STATUS_LABELS[item.status] || { label: item.status, color: 'bg-gray-100 text-gray-700' };
                          return (
                            <tr key={idx} className="border-b align-top">
                              <td className="py-3 pr-4 font-medium capitalize">{item.keyword}</td>
                              <td className="py-3 pr-4">
                                <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">
                                  {KEYWORD_CATEGORY_LABELS[item.category] || item.category}
                                </span>
                              </td>
                              <td className="py-3 pr-4">
                                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusMeta.color}`}>
                                  {statusMeta.label}
                                </span>
                              </td>
                              <td className="py-3 pr-4 text-gray-600">
                                {item.occurrences_in_resume ?? 0}x
                                {item.in_skills_section ? ' · in skills' : ''}
                              </td>
                              <td className="py-3 text-gray-600 text-xs">{item.evidence || '—'}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </section>
              )}

              {keywordEnhancement.add_to_resume?.length > 0 && (
                <section>
                  <h3 className="text-xl font-bold mb-2 text-blue-700">What to Add Based on Your Resume</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Evidence-based suggestions drawn from content already on your resume — not generic advice.
                  </p>
                  <div className="space-y-4">
                    {keywordEnhancement.add_to_resume.map((item: any, idx: number) => (
                      <div key={idx} className="border rounded-lg p-4 bg-blue-50/50">
                        <div className="flex flex-wrap items-center gap-2 mb-2">
                          <span className="font-bold capitalize">{item.keyword}</span>
                          <span className="text-xs bg-white border px-2 py-0.5 rounded">
                            → {item.target_section}
                          </span>
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                            KEYWORD_STATUS_LABELS[item.status]?.color || 'bg-gray-100 text-gray-700'
                          }`}>
                            {KEYWORD_STATUS_LABELS[item.status]?.label || item.status}
                          </span>
                          <span className="text-xs text-blue-600 ml-auto">Priority {item.priority}/5</span>
                        </div>
                        <p className="text-gray-800 font-medium mb-1">{item.suggested_phrase}</p>
                        <p className="text-sm text-gray-600 mb-1">{item.reason}</p>
                        <p className="text-xs text-green-700 bg-green-50 inline-block px-2 py-1 rounded mt-1">
                          From your resume: {item.evidence_from_resume}
                        </p>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {!keywordEnhancement.missing_keywords_detailed?.length &&
                !keywordEnhancement.add_to_resume?.length && (
                <p className="text-gray-600">Your resume covers all JD keywords well. No additions needed.</p>
              )}
            </div>
          )}

          {activeTab === 'gaps' && gapAnalysis && (
            <div className="space-y-8">
              {gapAnalysis.priority_areas?.length > 0 && (
                <section>
                  <h3 className="text-xl font-bold mb-4">Priority Improvement Areas</h3>
                  <div className="space-y-3">
                    {gapAnalysis.priority_areas.map((area: any, idx: number) => (
                      <div key={idx} className="border rounded-lg p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-bold">{area.area}</span>
                          <ImpactBadge impact={area.impact} />
                        </div>
                        <p className="text-gray-700 text-sm mb-1">{area.details}</p>
                        <p className="text-blue-700 text-sm font-medium">→ {area.action}</p>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {gapAnalysis.matched_skills?.length > 0 && (
                <section>
                  <h3 className="text-xl font-bold mb-2 text-green-700">Skills You Have</h3>
                  <SkillsList skills={gapAnalysis.matched_skills.map((s: string) => ({ skill: s }))} maxDisplay={25} />
                </section>
              )}

              {gapAnalysis.critical_missing_skills?.length > 0 && (
                <section>
                  <h3 className="text-xl font-bold mb-2 text-red-700">Critical Missing Skills</h3>
                  <div className="space-y-3">
                    {gapAnalysis.critical_missing_skills.map((s: any, idx: number) => (
                      <div key={idx} className="bg-red-50 p-3 rounded">
                        <p className="font-semibold text-red-800">{s.skill}</p>
                        {s.suggested_resources?.length > 0 && (
                          <p className="text-sm text-gray-600 mt-1">
                            Learn: {s.suggested_resources.join(' · ')}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {gapAnalysis.experience_gap && (
                <section>
                  <h3 className="text-xl font-bold mb-2">Experience Gap</h3>
                  <p className="text-gray-700 bg-yellow-50 p-4 rounded">{gapAnalysis.experience_gap}</p>
                </section>
              )}

              {gapAnalysis.responsibility_gaps?.length > 0 && (
                <section>
                  <h3 className="text-xl font-bold mb-2">Responsibility Gaps</h3>
                  <ul className="list-disc list-inside space-y-1 text-gray-700">
                    {gapAnalysis.responsibility_gaps.map((r: string, idx: number) => (
                      <li key={idx}>{r}</li>
                    ))}
                  </ul>
                </section>
              )}

              {gapAnalysis.keyword_gaps?.length > 0 && (
                <section>
                  <h3 className="text-xl font-bold mb-2">Keyword Gaps</h3>
                  <SkillsList skills={gapAnalysis.keyword_gaps.map((s: string) => ({ skill: s }))} maxDisplay={20} />
                </section>
              )}
            </div>
          )}

          {activeTab === 'optimize' && optimizationSuggestions && (
            <div className="space-y-6">
              {optimizationSuggestions.overall_improvement_potential != null && (
                <div className="bg-purple-50 p-4 rounded-lg text-center">
                  <p className="text-gray-600 text-sm">Improvement Potential</p>
                  <p className="text-3xl font-bold text-purple-700">
                    {optimizationSuggestions.overall_improvement_potential.toFixed(0)}%
                  </p>
                </div>
              )}

              {[
                { key: 'summary_suggestions', title: 'Summary Section' },
                { key: 'experience_suggestions', title: 'Experience Section' },
                { key: 'project_suggestions', title: 'Projects Section' },
              ].map(({ key, title }) => {
                const items = optimizationSuggestions[key];
                if (!items?.length) return null;
                return (
                  <section key={key}>
                    <h3 className="text-lg font-bold mb-3">{title}</h3>
                    <div className="space-y-3">
                      {items.map((s: any, idx: number) => (
                        <div key={idx} className="bg-blue-50 p-4 rounded-lg">
                          <div className="flex items-center gap-2 mb-1">
                            <p className="font-semibold">{s.suggestion}</p>
                            {s.impact && <ImpactBadge impact={s.impact} />}
                          </div>
                          <p className="text-gray-600 text-sm">{s.reason}</p>
                        </div>
                      ))}
                    </div>
                  </section>
                );
              })}

              {optimizationSuggestions.skills_to_add?.length > 0 && (
                <section>
                  <h3 className="text-lg font-bold mb-2">Skills to Add</h3>
                  <SkillsList skills={optimizationSuggestions.skills_to_add.map((s: string) => ({ skill: s }))} maxDisplay={15} />
                </section>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
