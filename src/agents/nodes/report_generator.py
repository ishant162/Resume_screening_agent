from langchain_core.messages import HumanMessage, SystemMessage
from config.settings import settings
from src.models import (
    JobRequirements,
    RankedCandidate,
    CandidateScore
)
from src.llm.groq_llm import GroqLLM
from config.prompts import EXECUTIVE_CANDIDATE_SUMMARY_PROMPT
from typing import List, Dict
from datetime import datetime


class ReportGenerator:
    """Generates comprehensive screening reports"""
    
    def __init__(self):
        self.llm = GroqLLM().get_llm_model()
    
    def generate_report(
        self,
        job_requirements: Dict,
        ranked_candidates: List[Dict]
    ) -> str:
        """
        Generate comprehensive markdown report
        
        Args:
            job_requirements: Job requirements dict
            ranked_candidates: List of ranked candidate dicts
            
        Returns:
            Markdown formatted report
        """
        print("📊 Generating comprehensive report...")
        
        job_req = JobRequirements(**job_requirements)
        ranked = [RankedCandidate(**rc) for rc in ranked_candidates]
        
        # Generate executive summary using LLM
        exec_summary = self._generate_executive_summary(job_req, ranked)
        
        # Build report sections
        report_sections = []
        
        # Header
        report_sections.append(self._generate_header(job_req))
        
        # Executive Summary
        report_sections.append(self._generate_summary_section(exec_summary, ranked))
        
        # Top Candidates Overview
        report_sections.append(self._generate_top_candidates_section(ranked[:3]))
        
        # Detailed Candidate Profiles
        report_sections.append(self._generate_detailed_profiles(ranked))
        
        # Hiring Recommendations
        report_sections.append(self._generate_recommendations(job_req, ranked))
        
        # Footer
        report_sections.append(self._generate_footer())
        
        full_report = "\n\n".join(report_sections)
        
        print("✅ Report generated successfully")
        return full_report
    
    def _generate_executive_summary(
        self,
        job_requirements: JobRequirements,
        ranked_candidates: List[RankedCandidate]
    ) -> str:
        """Use LLM to generate executive summary"""
        
        # Prepare candidate summary
        top_3 = ranked_candidates[:3]
        candidate_summaries = []
        
        for rc in top_3:
            cs = rc.candidate_score
            candidate_summaries.append(
                f"#{rc.rank} {cs.candidate_name} ({cs.total_score:.1f}%) - {cs.recommendation}"
            )
        
        candidates_str = "\n".join(candidate_summaries)

        prompt = EXECUTIVE_CANDIDATE_SUMMARY_PROMPT.format(
            job_title=job_requirements.job_title,
            candidates_screened=len(ranked_candidates),
            top_candidates_summary=candidates_str,
        )

        try:
            messages = [
                SystemMessage(content="You are an expert at writing concise executive summaries for hiring."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            return response.content.strip()
            
        except Exception as e:
            print(f"  ⚠️  Executive summary generation failed: {e}")
            return f"Screened {len(ranked_candidates)} candidates for the {job_requirements.job_title} position. Top candidate scored {ranked_candidates[0].candidate_score.total_score:.1f}%."
    
    def _generate_header(self, job_req: JobRequirements) -> str:
        """Generate report header"""
        
        return f"""# Resume Screening Report
## {job_req.job_title}

**Generated:** {datetime.now().strftime("%B %d, %Y at %I:%M %p")}

---
"""
    
    def _generate_summary_section(
        self,
        exec_summary: str,
        ranked_candidates: List[RankedCandidate]
    ) -> str:
        """Generate summary section"""
        
        # Count recommendations
        strong = sum(1 for rc in ranked_candidates if rc.candidate_score.recommendation == "Strong Match")
        good = sum(1 for rc in ranked_candidates if rc.candidate_score.recommendation == "Good Match")
        potential = sum(1 for rc in ranked_candidates if rc.candidate_score.recommendation == "Potential Match")
        not_rec = sum(1 for rc in ranked_candidates if rc.candidate_score.recommendation == "Not Recommended")
        
        return f"""## Executive Summary

{exec_summary}

### Screening Overview

| Metric | Count |
|--------|-------|
| **Total Candidates Screened** | {len(ranked_candidates)} |
| **Strong Matches** | {strong} |
| **Good Matches** | {good} |
| **Potential Matches** | {potential} |
| **Not Recommended** | {not_rec} |

---
"""
    
    def _generate_top_candidates_section(
        self,
        top_candidates: List[RankedCandidate]
    ) -> str:
        """Generate top candidates comparison"""
        
        section = "## Top Candidates at a Glance\n\n"
        
        # Create comparison table
        section += "| Rank | Name | Overall Score | Skills | Experience | Education | Recommendation |\n"
        section += "|------|------|---------------|--------|------------|-----------|----------------|\n"
        
        for rc in top_candidates:
            cs = rc.candidate_score
            section += f"| #{rc.rank} | **{cs.candidate_name}** | {cs.total_score:.1f}% | "
            section += f"{cs.skill_score.overall_skill_score:.1f}% | "
            section += f"{cs.experience_score.experience_match_score:.1f}% | "
            section += f"{cs.education_score.education_score:.1f}% | "
            section += f"{cs.recommendation} |\n"
        
        section += "\n---\n"
        
        return section
    
    def _generate_detailed_profiles(
        self,
        ranked_candidates: List[RankedCandidate]
    ) -> str:
        """Generate detailed candidate profiles"""
        
        section = "## Detailed Candidate Profiles\n\n"
        
        for rc in ranked_candidates:
            cs = rc.candidate_score
            
            # Candidate header
            section += f"### #{rc.rank} - {cs.candidate_name}\n\n"
            
            # Recommendation badge
            badge_emoji = {
                "Strong Match": "🟢",
                "Good Match": "🟡",
                "Potential Match": "🟠",
                "Not Recommended": "🔴"
            }
            emoji = badge_emoji.get(cs.recommendation, "⚪")
            
            section += f"**{emoji} {cs.recommendation}** (Confidence: {cs.confidence_level})\n\n"
            
            # Contact info
            if cs.candidate_email:
                section += f"📧 {cs.candidate_email}\n\n"
            
            # Score breakdown
            section += f"#### Score Breakdown (Total: {cs.total_score:.1f}%)\n\n"
            section += f"- **Skills:** {cs.skill_score.overall_skill_score:.1f}% "
            section += f"(weighted: {cs.weighted_skill_score:.1f})\n"
            section += f"- **Experience:** {cs.experience_score.experience_match_score:.1f}% "
            section += f"(weighted: {cs.weighted_experience_score:.1f})\n"
            section += f"- **Education:** {cs.education_score.education_score:.1f}% "
            section += f"(weighted: {cs.weighted_education_score:.1f})\n\n"
            
            # Strengths
            section += "#### ✅ Key Strengths\n\n"
            for strength in cs.strengths:
                section += f"- {strength}\n"
            section += "\n"
            
            # Concerns
            if cs.concerns:
                section += "#### ⚠️ Areas of Concern\n\n"
                for concern in cs.concerns:
                    section += f"- {concern}\n"
                section += "\n"
            
            # Red flags
            if cs.red_flags:
                section += "#### 🚩 Red Flags\n\n"
                for flag in cs.red_flags:
                    section += f"- {flag}\n"
                section += "\n"
            
            # Detailed analysis
            section += "#### 📋 Comprehensive Analysis\n\n"
            section += f"{cs.detailed_analysis}\n\n"
            
            # Skill details
            section += "<details>\n"
            section += "<summary><b>Detailed Skill Analysis</b></summary>\n\n"
            section += f"**Matched Must-Have Skills:** {', '.join(cs.skill_score.matched_must_have) if cs.skill_score.matched_must_have else 'None'}\n\n"
            section += f"**Missing Must-Have Skills:** {', '.join(cs.skill_score.missing_must_have) if cs.skill_score.missing_must_have else 'None'}\n\n"
            section += f"**Additional Skills:** {', '.join(cs.skill_score.additional_skills[:10]) if cs.skill_score.additional_skills else 'None'}\n\n"
            section += f"{cs.skill_score.skill_gap_analysis}\n"
            section += "</details>\n\n"
            
            # Experience details
            section += "<details>\n"
            section += "<summary><b>Detailed Experience Analysis</b></summary>\n\n"
            section += f"**Total Experience:** {cs.experience_score.total_years} years\n\n"
            section += f"**Relevant Experience:** {cs.experience_score.relevant_years} years\n\n"
            section += f"**Career Trajectory:** {cs.experience_score.career_trajectory}\n\n"
            section += f"**Domain Match:** {'Yes' if cs.experience_score.domain_match else 'No'}\n\n"
            section += f"{cs.experience_score.experience_analysis}\n"
            section += "</details>\n\n"
            
            # Education details
            section += "<details>\n"
            section += "<summary><b>Detailed Education Analysis</b></summary>\n\n"
            section += f"**Highest Degree:** {cs.education_score.highest_degree or 'Not specified'}\n\n"
            section += f"**Meets Requirement:** {'Yes' if cs.education_score.meets_requirement else 'No'}\n\n"
            section += f"**Field Match:** {'Yes' if cs.education_score.field_match else 'No'}\n\n"
            if cs.education_score.certifications:
                section += f"**Certifications:** {', '.join(cs.education_score.certifications)}\n\n"
            section += f"{cs.education_score.education_analysis}\n"
            section += "</details>\n\n"
            
            # Comparative analysis (if available)
            if rc.comparison_notes:
                section += f"#### 📊 Ranking Context\n\n"
                section += f"{rc.comparison_notes}\n\n"
            
            section += "---\n\n"
        
        return section
    
    def _generate_recommendations(
        self,
        job_req: JobRequirements,
        ranked_candidates: List[RankedCandidate]
    ) -> str:
        """Generate hiring recommendations"""
        
        section = "## Hiring Recommendations\n\n"
        
        # Get top candidates
        strong_matches = [rc for rc in ranked_candidates if rc.candidate_score.recommendation == "Strong Match"]
        good_matches = [rc for rc in ranked_candidates if rc.candidate_score.recommendation == "Good Match"]
        
        if strong_matches:
            section += "### 🎯 Recommended for Immediate Interview\n\n"
            for rc in strong_matches[:3]:
                section += f"- **{rc.candidate_score.candidate_name}** (Score: {rc.candidate_score.total_score:.1f}%)\n"
            section += "\n"
        
        if good_matches:
            section += "### 💼 Recommended for Phone Screen\n\n"
            for rc in good_matches[:3]:
                section += f"- **{rc.candidate_score.candidate_name}** (Score: {rc.candidate_score.total_score:.1f}%)\n"
            section += "\n"
        
        section += "### 📝 Next Steps\n\n"
        section += "1. Review top candidates' detailed profiles above\n"
        section += "2. Review interview questions (see next section)\n"
        section += "3. Schedule interviews with recommended candidates\n"
        section += "4. Consider phone screens for 'Good Match' candidates\n\n"
        
        section += "---\n"
        
        return section
    
    def _generate_footer(self) -> str:
        """Generate report footer"""
        
        return f"""
---

## Report Information

**Generated by:** Resume Screening AI Agent  
**Date:** {datetime.now().strftime("%B %d, %Y")}  
**Scoring Weights:** Skills ({settings.SKILL_WEIGHT*100}%) | Experience ({settings.EXPERIENCE_WEIGHT*100}%) | Education ({settings.EDUCATION_WEIGHT*100}%)

*This report was generated using AI-powered analysis. Final hiring decisions should be made by qualified human recruiters.*
"""


def report_generator_node(state: Dict) -> Dict:
    """
    LangGraph node: Generate comprehensive report
    """
    print("📊 Generating comprehensive screening report...")
    
    generator = ReportGenerator()
    
    report = generator.generate_report(
        state["job_requirements"],
        state["ranked_candidates"]
    )
    
    return {
        "report": report,
        "current_step": "report_generation_complete"
    }


# Test independently
if __name__ == "__main__":
    print("Report generator test - requires full candidate data")
    print("Run full workflow to test report generation")