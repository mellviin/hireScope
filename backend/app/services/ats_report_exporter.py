"""
ATS Report Export Engine — generates UI-styled PDF compatibility reports
"""
from io import BytesIO
from datetime import datetime
from html import escape
from typing import Dict, Any, List, Optional
from xhtml2pdf import pisa
from app.utils.logging import setup_logging

logger = setup_logging(__name__)

CATEGORY_LABELS = {
    "required_skills": "Required Skills",
    "preferred_skills": "Preferred Skills",
    "experience": "Experience",
    "projects": "Projects",
    "education": "Education",
    "responsibilities": "Responsibilities",
    "keywords": "Keywords & ATS",
}


def score_verdict(score: float) -> str:
    if score >= 80:
        return "Excellent Match"
    if score >= 60:
        return "Good Match"
    if score >= 40:
        return "Moderate Match"
    return "Needs Improvement"


def _score_theme(score: float) -> Dict[str, str]:
    if score >= 80:
        return {"bg": "#f0fdf4", "border": "#bbf7d0", "text": "#16a34a"}
    if score >= 60:
        return {"bg": "#fefce8", "border": "#fef08a", "text": "#ca8a04"}
    if score >= 40:
        return {"bg": "#fff7ed", "border": "#fed7aa", "text": "#ea580c"}
    return {"bg": "#fef2f2", "border": "#fecaca", "text": "#dc2626"}


def _esc(value: Any) -> str:
    return escape(str(value)) if value is not None else ""


def _skill_pills(skills: List[str], bg: str, color: str) -> str:
    if not skills:
        return "<p class='muted'>None</p>"
    return "".join(
        f"<span class='pill' style='background:{bg};color:{color};'>{_esc(s)}</span>"
        for s in skills[:20]
    )


class ATSReportExporter:
    """Build a downloadable PDF ATS report styled like the Match Analysis UI."""

    def generate_report(
        self,
        match_result: Dict[str, Any],
        gap_analysis: Dict[str, Any],
        optimization: Dict[str, Any],
        resume_filename: str,
        job_title: str,
        company: Optional[str] = None,
    ) -> bytes:
        html = self._build_html(
            match_result, gap_analysis, optimization, resume_filename, job_title, company
        )
        buffer = BytesIO()
        status = pisa.CreatePDF(html, dest=buffer, encoding="utf-8")
        if status.err:
            raise RuntimeError("Failed to generate PDF report")
        logger.info(f"ATS PDF report generated for {resume_filename} vs {job_title}")
        return buffer.getvalue()

    def _build_html(
        self,
        match_result: Dict[str, Any],
        gap_analysis: Dict[str, Any],
        optimization: Dict[str, Any],
        resume_filename: str,
        job_title: str,
        company: Optional[str],
    ) -> str:
        overall = match_result.get("ats_score", 0)
        theme = _score_theme(overall)
        verdict = score_verdict(overall)
        company_line = f" @ {_esc(company)}" if company else ""
        generated = datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")

        score_cards = [
            ("Overall Score", overall),
            ("Required Skills", match_result.get("required_skills_match", 0)),
            ("Preferred Skills", match_result.get("preferred_skills_match", 0)),
            ("Experience", match_result.get("experience_match", 0)),
            ("Keyword Coverage", match_result.get("keyword_coverage", 0)),
            ("Responsibilities", match_result.get("responsibility_alignment", 0)),
        ]
        cards_html = "".join(
            f"""<td class='score-card'>
                <div class='score-card-title'>{_esc(title)}</div>
                <div class='score-card-value'>{val:.1f}</div>
                <div class='score-card-sub'>out of 100</div>
            </td>"""
            for title, val in score_cards
        )

        breakdown_rows = ""
        for row in match_result.get("score_breakdown") or []:
            if row.get("category") == "total":
                continue
            breakdown_rows += f"""<tr>
                <td>{_esc(row.get('label') or row.get('category'))}</td>
                <td>{row.get('score', 0):.1f}%</td>
                <td>{row.get('weight_percent', 0):.1f}%</td>
                <td>{row.get('weighted_contribution', 0):.2f} pts</td>
            </tr>"""

        strengths_html = ""
        for s in match_result.get("strengths") or []:
            cat = CATEGORY_LABELS.get(s.get("category", ""), s.get("category", "General"))
            details = s.get("details") or []
            if isinstance(details, str):
                details = [details]
            items = "".join(f"<li>{_esc(d)}</li>" for d in details if d)
            strengths_html += f"""<div class='box green'>
                <div class='box-head'><strong>{_esc(cat)}</strong><span>{s.get('score', 0):.0f}%</span></div>
                <ul>{items}</ul>
            </div>"""

        recs_html = ""
        for rec in (match_result.get("recommendations") or [])[:8]:
            recs_html += f"""<div class='box blue'>
                <strong>{_esc(rec.get('suggestion', ''))}</strong>
                <p class='muted'>{_esc(rec.get('reason', ''))}</p>
                <span class='badge blue-badge'>Priority {rec.get('priority', 3)}/5</span>
            </div>"""

        skills_html = self._skill_breakdown_html(
            "Required & Technical Skills",
            match_result.get("skill_breakdown", {}).get("required"),
        )
        skills_html += self._skill_breakdown_html(
            "Preferred & Soft Skills",
            match_result.get("skill_breakdown", {}).get("preferred"),
        )

        exp = match_result.get("experience_analysis") or {}
        exp_html = ""
        if exp.get("gap_summary"):
            roles = ""
            for role in exp.get("role_details") or []:
                roles += f"""<div class='role-row'>
                    <div><strong>{_esc(role.get('title'))}</strong> @ {_esc(role.get('company'))}<br/>
                    <span class='muted'>{_esc(role.get('duration'))}</span></div>
                    <span class='badge'>{_esc(role.get('relevance'))} relevance</span>
                </div>"""
            exp_html = f"""<div class='section'>
                <h2>Experience Analysis</h2>
                <p>{_esc(exp.get('gap_summary'))}</p>{roles}
            </div>"""

        gaps_html = ""
        for area in gap_analysis.get("priority_areas") or []:
            gaps_html += f"""<div class='box border'>
                <div class='box-head'><strong>{_esc(area.get('area'))}</strong>
                <span class='badge impact-{_esc(area.get('impact', 'medium'))}'>{_esc(area.get('impact'))} impact</span></div>
                <p>{_esc(area.get('details'))}</p>
                <p class='action'>→ {_esc(area.get('action'))}</p>
            </div>"""

        critical_html = ""
        for s in gap_analysis.get("critical_missing_skills") or []:
            resources = s.get("suggested_resources") or []
            res_line = f"<p class='muted'>Learn: {_esc(' · '.join(resources))}</p>" if resources else ""
            critical_html += f"""<div class='box red'>
                <strong>{_esc(s.get('skill'))}</strong>{res_line}
            </div>"""

        opt_html = ""
        if optimization.get("overall_improvement_potential") is not None:
            opt_html += f"""<div class='improve-box'>
                <p class='muted'>Improvement Potential</p>
                <p class='improve-value'>{optimization['overall_improvement_potential']:.0f}%</p>
            </div>"""
        for key, title in [
            ("summary_suggestions", "Summary Section"),
            ("experience_suggestions", "Experience Section"),
            ("project_suggestions", "Projects Section"),
        ]:
            for item in (optimization.get(key) or [])[:5]:
                opt_html += f"""<div class='box blue'>
                    <strong>{_esc(item.get('suggestion', ''))}</strong>
                    <p class='muted'>{_esc(item.get('reason', ''))}</p>
                </div>"""
        if optimization.get("skills_to_add"):
            opt_html += f"""<div class='section'><h3>Skills to Add</h3>
            {_skill_pills(optimization['skills_to_add'], '#dbeafe', '#1d4ed8')}</div>"""

        kw_density = match_result.get("keyword_density") or {}
        kw_html = ""
        if kw_density:
            kw_html = f"""<div class='section'><h3>Keyword Frequency</h3>
            {_skill_pills(list(kw_density.keys()), '#f3e8ff', '#7e22ce')}</div>"""

        missing_kw = match_result.get("missing_keywords") or gap_analysis.get("keyword_gaps") or []
        missing_kw_html = ""
        if missing_kw:
            missing_kw_html = f"""<div class='section'><h3>Missing ATS Keywords</h3>
            {_skill_pills(missing_kw, '#ffedd5', '#c2410c')}</div>"""

        kw_enhancement = match_result.get("keyword_enhancement") or gap_analysis.get("keyword_enhancement") or {}
        kw_enhancement_html = self._keyword_enhancement_html(kw_enhancement)

        skill_matrix_html = self._skill_evidence_matrix_html(
            match_result.get("skill_evidence_matrix") or []
        )

        return f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'/><style>
@page {{ size: A4; margin: 1.2cm; }}
body {{ font-family: Helvetica, Arial, sans-serif; color: #111827; font-size: 11px; line-height: 1.45; }}
h1 {{ font-size: 22px; color: #2563eb; margin: 0 0 4px 0; }}
h2 {{ font-size: 16px; color: #1f4e79; margin: 18px 0 8px 0; border-bottom: 2px solid #e5e7eb; padding-bottom: 4px; }}
h3 {{ font-size: 13px; color: #374151; margin: 12px 0 6px 0; }}
.muted {{ color: #6b7280; font-size: 10px; }}
.subtitle {{ color: #6b7280; margin-bottom: 14px; }}
.hero {{ background: {theme['bg']}; border: 2px solid {theme['border']}; border-radius: 10px; padding: 18px; margin: 14px 0; }}
.hero-label {{ font-size: 10px; font-weight: bold; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; }}
.hero-score {{ font-size: 42px; font-weight: bold; color: {theme['text']}; }}
.hero-verdict {{ font-size: 16px; font-weight: bold; color: {theme['text']}; }}
.hero-meta {{ font-size: 12px; font-weight: bold; color: #1f2937; }}
.score-cards {{ width: 100%; border-collapse: separate; border-spacing: 6px; margin: 10px 0 16px 0; }}
.score-card {{ background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 10px; text-align: center; width: 16%; }}
.score-card-title {{ font-size: 9px; color: #6b7280; font-weight: bold; }}
.score-card-value {{ font-size: 20px; font-weight: bold; color: #2563eb; }}
.score-card-sub {{ font-size: 8px; color: #9ca3af; }}
table.data {{ width: 100%; border-collapse: collapse; margin-top: 6px; }}
table.data th, table.data td {{ border: 1px solid #e5e7eb; padding: 6px 8px; text-align: left; }}
table.data th {{ background: #f3f4f6; color: #4b5563; font-size: 10px; }}
.section {{ margin-top: 14px; page-break-inside: avoid; }}
.box {{ border-radius: 8px; padding: 10px; margin: 8px 0; page-break-inside: avoid; }}
.box.green {{ background: #f0fdf4; border-left: 4px solid #16a34a; }}
.box.blue {{ background: #eff6ff; border-left: 4px solid #2563eb; }}
.box.red {{ background: #fef2f2; border-left: 4px solid #dc2626; }}
.box.border {{ background: #fff; border: 1px solid #e5e7eb; }}
.box-head {{ display: block; margin-bottom: 4px; }}
.box ul {{ margin: 4px 0 0 16px; padding: 0; }}
.pill {{ display: inline-block; padding: 3px 8px; margin: 2px; border-radius: 999px; font-size: 9px; font-weight: 600; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 9px; background: #f3f4f6; color: #374151; }}
.impact-high {{ background: #fee2e2; color: #991b1b; }}
.impact-medium {{ background: #fef9c3; color: #854d0e; }}
.impact-low {{ background: #f3f4f6; color: #374151; }}
.blue-badge {{ background: #dbeafe; color: #1d4ed8; }}
.action {{ color: #2563eb; font-weight: bold; font-size: 10px; }}
.role-row {{ background: #f9fafb; padding: 8px; border-radius: 6px; margin: 6px 0; }}
.skill-grid td {{ vertical-align: top; width: 33%; padding: 6px; }}
.skill-panel {{ border-radius: 8px; padding: 8px; min-height: 60px; }}
.panel-green {{ background: #f0fdf4; }}
.panel-yellow {{ background: #fefce8; }}
.panel-red {{ background: #fef2f2; }}
.panel-title {{ font-weight: bold; font-size: 10px; margin-bottom: 6px; }}
.improve-box {{ background: #faf5ff; border-radius: 8px; padding: 12px; text-align: center; margin-bottom: 10px; }}
.improve-value {{ font-size: 28px; font-weight: bold; color: #7e22ce; margin: 0; }}
.stat-row {{ border-collapse: separate; border-spacing: 4px; margin: 8px 0; }}
.stat-cell {{ background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 6px; text-align: center; }}
.stat-label {{ font-size: 8px; color: #6b7280; font-weight: bold; }}
.stat-value {{ font-size: 14px; font-weight: bold; color: #1f2937; }}
.footer {{ margin-top: 20px; text-align: center; color: #9ca3af; font-size: 9px; border-top: 1px solid #e5e7eb; padding-top: 8px; }}
</style></head><body>
<h1>Match Analysis Results</h1>
<p class='subtitle'>Resume compatibility scored against this specific job description · Generated {generated}</p>

<div class='hero'>
  <div class='hero-label'>Overall Resume Score for This Job</div>
  <div class='hero-meta'>{_esc(job_title)}{company_line}</div>
  <p class='muted'>Resume: {_esc(resume_filename)}</p>
  <span class='hero-score'>{overall:.1f}</span> <span class='muted'>/ 100</span>
  <span class='hero-verdict'> — {verdict}</span>
  <p class='muted' style='margin-top:8px;'>This score reflects how well your resume matches the requirements, keywords, experience, and responsibilities of this job posting.</p>
</div>

<table class='score-cards'><tr>{cards_html}</tr></table>

<div class='section'>
  <h2>Overview — Score Breakdown</h2>
  <table class='data'>
    <tr><th>Category</th><th>Score</th><th>Weight</th><th>Contribution</th></tr>
    {breakdown_rows}
  </table>
</div>

{exp_html}

<div class='section'>
  <h2>Key Strengths</h2>
  {strengths_html or "<p class='muted'>No strengths identified.</p>"}
</div>

<div class='section'>
  <h2>Top Recommendations</h2>
  {recs_html or "<p class='muted'>No recommendations available.</p>"}
</div>

<div class='section'>
  <h2>Skills Deep Dive</h2>
  {skills_html}
  {skill_matrix_html}
  {kw_html}
  {missing_kw_html}
</div>

<div class='section'>
  <h2>Keywords &amp; Additions</h2>
  {kw_enhancement_html or "<p class='muted'>No keyword enhancement data available.</p>"}
</div>

<div class='section'>
  <h2>Gaps &amp; Priorities</h2>
  {gaps_html}
  {critical_html}
  {f"<p><strong>Experience Gap:</strong> {_esc(gap_analysis.get('experience_gap'))}</p>" if gap_analysis.get('experience_gap') else ""}
</div>

<div class='section'>
  <h2>Optimize Resume</h2>
  {opt_html or "<p class='muted'>No optimization suggestions available.</p>"}
</div>

<div class='footer'>Report generated by HireScope — AI-Powered Resume Intelligence Platform</div>
</body></html>"""

    def _keyword_enhancement_html(self, kw_enhancement: Dict[str, Any]) -> str:
        if not kw_enhancement:
            return ""

        html = ""
        summary = kw_enhancement.get("coverage_summary") or {}
        if summary:
            stats = [
                ("JD Keywords", summary.get("total_jd_keywords", 0)),
                ("Matched", summary.get("matched", 0)),
                ("Partial", summary.get("partial", 0)),
                ("Hidden", summary.get("hidden", 0)),
                ("Underused", summary.get("underused", 0)),
                ("Missing", summary.get("missing", 0)),
                ("Coverage", f"{summary.get('coverage_percent', 0)}%"),
            ]
            cells = "".join(
                f"<td class='stat-cell'><div class='stat-label'>{_esc(l)}</div>"
                f"<div class='stat-value'>{_esc(v)}</div></td>"
                for l, v in stats
            )
            html += f"""<table class='stat-row' width='100%'><tr>{cells}</tr></table>
            <p class='muted'>{summary.get('actionable_additions', 0)} actionable additions from existing resume content.</p>"""

        status_colors = {
            "missing": ("#fee2e2", "#991b1b"),
            "partial": ("#ffedd5", "#c2410c"),
            "hidden": ("#fef9c3", "#854d0e"),
            "underused": ("#dbeafe", "#1d4ed8"),
        }

        missing_detailed = kw_enhancement.get("missing_keywords_detailed") or []
        if missing_detailed:
            rows = ""
            for item in missing_detailed[:15]:
                status = item.get("status", "missing")
                bg, color = status_colors.get(status, ("#f3f4f6", "#374151"))
                rows += f"""<tr>
                    <td><strong>{_esc(item.get('keyword', ''))}</strong></td>
                    <td>{_esc(item.get('category', ''))}</td>
                    <td><span class='pill' style='background:{bg};color:{color};'>{_esc(status)}</span></td>
                    <td>{item.get('occurrences_in_resume', 0)}x</td>
                    <td class='muted'>{_esc(item.get('evidence') or '—')}</td>
                </tr>"""
            html += f"""<h3>Keywords You Missed</h3>
            <table class='data'>
              <tr><th>Keyword</th><th>Category</th><th>Status</th><th>In Resume</th><th>Evidence</th></tr>
              {rows}
            </table>"""

        additions = kw_enhancement.get("add_to_resume") or []
        for item in additions[:12]:
            html += f"""<div class='box blue'>
                <div class='box-head'>
                  <strong>{_esc(item.get('keyword', ''))}</strong>
                  <span class='badge'>→ {_esc(item.get('target_section', ''))}</span>
                  <span class='badge blue-badge'>Priority {item.get('priority', 3)}/5</span>
                </div>
                <p><strong>{_esc(item.get('suggested_phrase', ''))}</strong></p>
                <p class='muted'>{_esc(item.get('reason', ''))}</p>
                <p style='color:#15803d;font-size:9px;'>From your resume: {_esc(item.get('evidence_from_resume', ''))}</p>
            </div>"""

        return html

    def _skill_evidence_matrix_html(self, matrix: List[Dict[str, Any]]) -> str:
        if not matrix:
            return ""
        status_colors = {
            "exact": ("#bbf7d0", "#166534"),
            "partial": ("#fef08a", "#854d0e"),
            "missing": ("#fecaca", "#991b1b"),
        }
        rows = ""
        for item in matrix[:20]:
            mt = item.get("match_type", "missing")
            bg, color = status_colors.get(mt, ("#f3f4f6", "#374151"))
            rows += f"""<tr>
                <td><strong>{_esc(item.get('skill', ''))}</strong></td>
                <td>{_esc(item.get('category', ''))}</td>
                <td>{_esc(item.get('found_in_resume', ''))}</td>
                <td>{item.get('occurrences', 0)}</td>
                <td><span class='pill' style='background:{bg};color:{color};'>{_esc(mt)}</span></td>
                <td class='muted'>{_esc(item.get('evidence_summary', '-'))}</td>
            </tr>"""
        return f"""<h3>Skill Match Evidence Matrix</h3>
        <table class='data'>
          <tr><th>JD Skill</th><th>Category</th><th>Found</th><th>Count</th><th>Match</th><th>Evidence</th></tr>
          {rows}
        </table>"""

    def _skill_breakdown_html(self, title: str, data: Optional[Dict[str, Any]]) -> str:
        if not data or not data.get("total"):
            return ""
        return f"""<h3>{_esc(title)} ({data.get('score', 0)}% match — {len(data.get('matched_exact', [])) + len(data.get('matched_partial', []))}/{data.get('total')})</h3>
        <table class='skill-grid' width='100%'><tr>
          <td><div class='skill-panel panel-green'>
            <div class='panel-title' style='color:#166534;'>Exact Matches</div>
            {_skill_pills(data.get('matched_exact', []), '#bbf7d0', '#166534')}
          </div></td>
          <td><div class='skill-panel panel-yellow'>
            <div class='panel-title' style='color:#854d0e;'>Partial Matches</div>
            {_skill_pills(data.get('matched_partial', []), '#fef08a', '#854d0e')}
          </div></td>
          <td><div class='skill-panel panel-red'>
            <div class='panel-title' style='color:#991b1b;'>Missing</div>
            {_skill_pills(data.get('missing', []), '#fecaca', '#991b1b')}
          </div></td>
        </tr></table>"""
