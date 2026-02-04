"""
Enhanced Experience Analyzer Node

Uses company verification data from web search to provide richer context.
"""

import json

from langchain_core.messages import HumanMessage, SystemMessage

from config.prompts import COMPANY_CONTEXT_EXPERIENCE_ANALYSIS_PROMPT
from src.llm.groq_llm import GroqLLM
from src.models import Candidate, ExperienceScore, JobRequirements


class EnhancedExperienceAnalyzer:
    """Experience analysis enhanced with company verification data"""

    def __init__(self):
        self.llm = GroqLLM().get_llm_model()

    def analyze_experience(
        self,
        candidate: Candidate,
        job_requirements: JobRequirements,
        company_verifications: dict = None
    ) -> ExperienceScore:
        """
        Analyze experience with company context

        Args:
            candidate: Candidate model
            job_requirements: Job requirements
            company_verifications: Company data from web search

        Returns:
            Enhanced ExperienceScore
        """
        print(f"  💼 Enhanced analysis for {candidate.name}...")

        total_years = candidate.total_experience_years
        required_years = job_requirements.experience.minimum_years or 0

        # Analyze with company context
        analysis = self._analyze_with_company_context(
            candidate,
            job_requirements,
            company_verifications or {}
        )

        # Calculate enhanced score
        experience_match_score = self._calculate_enhanced_score(
            total_years,
            required_years,
            analysis
        )

        return ExperienceScore(
            candidate_name=candidate.name,
            total_years=total_years,
            relevant_years=analysis.get("relevant_years", total_years),
            required_years=required_years,
            domain_match=analysis.get("domain_match", False),
            relevant_domains=analysis.get("relevant_domains", []),
            has_role_progression=analysis.get("has_progression", False),
            career_trajectory=analysis.get("trajectory", "unknown"),
            experience_match_score=round(experience_match_score, 1),
            experience_analysis=analysis.get("comprehensive_analysis", "")
        )

    def _analyze_with_company_context(
        self,
        candidate: Candidate,
        job_requirements: JobRequirements,
        company_verifications: dict
    ) -> dict:
        """Use LLM with company verification context"""

        # Format work history with company data
        work_summary = self._format_work_with_context(
            candidate.work_experience,
            company_verifications
        )

        prompt = COMPANY_CONTEXT_EXPERIENCE_ANALYSIS_PROMPT.format(
            job_title=job_requirements.job_title,
            required_experience_years=job_requirements.experience.minimum_years or 0,
            target_domains=", ".join(job_requirements.experience.specific_domains)
                if job_requirements.experience.specific_domains else "Not specified",
            candidate_name=candidate.name,
            total_experience_years=candidate.total_experience_years,
            work_summary=work_summary,
        )

        try:
            messages = [
                SystemMessage(content="You are an expert at assessing work experience with industry context."),
                HumanMessage(content=prompt)
            ]

            response = self.llm.invoke(messages)
            response_text = response.content.strip()

            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]

            analysis = json.loads(response_text.strip())
            return analysis

        except Exception as e:
            print(f"Enhanced experience analysis failed: {e}")
            return {
                "relevant_years": candidate.total_experience_years,
                "domain_match": False,
                "relevant_domains": [],
                "has_progression": False,
                "trajectory": "unknown",
                "comprehensive_analysis": "Unable to perform enhanced analysis."
            }

    def _format_work_with_context(
        self,
        work_experience: list,
        company_verifications: dict
    ) -> str:
        """Format work history with company verification data"""

        if not work_experience:
            return "No work experience listed"

        summary = []

        for i, exp in enumerate(work_experience[:3], 1):
            company = exp.company
            position = exp.position
            duration = f"{exp.duration_months} months" if exp.duration_months else "Unknown duration"

            summary.append(f"{i}. {position} at {company}")
            summary.append(f"   Duration: {duration}")

            # Add company context if available
            if company in company_verifications:
                company_data = company_verifications[company]

                if company_data.get("exists"):
                    summary.append(f"   Company Info: {company_data.get('description', '')[:150]}")

                    if company_data.get("tech_stack"):
                        tech_stack = company_data["tech_stack"][:5]
                        summary.append(f"   Tech Stack: {', '.join(tech_stack)}")

                    if company_data.get("industry"):
                        summary.append(f"   Industry: {company_data['industry']}")
                else:
                    summary.append("   Company Info: Could not verify")
            else:
                summary.append("   Company Info: Not searched")

            if exp.responsibilities:
                summary.append(f"   Responsibilities: {'; '.join(exp.responsibilities[:2])}")

            summary.append("")

        return "\n".join(summary)

    def _calculate_enhanced_score(
        self,
        total_years: float,
        required_years: int,
        analysis: dict
    ) -> float:
        """Calculate experience score with enhancements"""

        # Years score (40 points)
        if required_years == 0:
            years_score = 40.0
        else:
            years_ratio = total_years / required_years
            years_score = min(40.0, years_ratio * 40.0)

        # Relevance score (35 points)
        relevant_years = analysis.get("relevant_years", total_years)
        if total_years > 0:
            relevance_ratio = relevant_years / total_years
            relevance_score = relevance_ratio * 35.0
        else:
            relevance_score = 0.0

        # Domain match bonus
        if analysis.get("domain_match"):
            relevance_score = min(35.0, relevance_score + 5.0)

        # Progression score (25 points)
        trajectory = analysis.get("trajectory", "unknown")
        progression_map = {
            "upward": 25.0,
            "specialist": 22.0,
            "lateral": 18.0,
            "pivot": 15.0,
            "early-career": 12.0,
            "unknown": 10.0
        }
        progression_score = progression_map.get(trajectory, 10.0)

        # Company quality bonus (up to 5 points)
        company_assessment = analysis.get("company_quality_assessment", "").lower()
        company_bonus = 0.0
        if "strong" in company_assessment or "reputable" in company_assessment:
            company_bonus = 5.0
        elif "solid" in company_assessment or "established" in company_assessment:
            company_bonus = 3.0

        total = years_score + relevance_score + progression_score + company_bonus
        return min(100.0, total)


def experience_analyzer_enhanced_node(state: dict) -> dict:
    """
    LangGraph node: Enhanced experience analysis with company data
    """
    print("💼 Enhanced Experience Analyzer: Using company verification data...\n")

    analyzer = EnhancedExperienceAnalyzer()

    job_req = JobRequirements(**state["job_requirements"])
    company_verifications = state.get("company_verifications", {})

    experience_scores = []

    for candidate_data in state["candidates"]:
        candidate = Candidate(**candidate_data)

        # Get company data for this candidate
        candidate_company_data = company_verifications.get(candidate.name, {})

        experience_score = analyzer.analyze_experience(
            candidate,
            job_req,
            candidate_company_data
        )
        experience_scores.append(experience_score.model_dump())

        print(f" {candidate.name}: {experience_score.experience_match_score:.1f}% "
              f"({experience_score.relevant_years:.1f}/{experience_score.required_years} years)")

    print("Enhanced experience analysis complete\n")

    return {
        "experience_scores": experience_scores,
        "current_step": "experience_analysis_complete"
    }
