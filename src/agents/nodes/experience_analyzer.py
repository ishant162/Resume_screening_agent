from datetime import date

from langchain_core.messages import HumanMessage, SystemMessage

from config.prompts import (
    CAREER_PROGRESSION_ANALYSIS_PROMPT,
    EXPERIENCE_ASSESSMENT_PROMPT,
    WORK_EXPERIENCE_RELEVANCE_PROMPT,
)
from src.data_models import Candidate, ExperienceScore, JobRequirements, WorkExperience
from src.llm.groq_llm import GroqLLM
from src.utils.utils import extract_response_text


class ExperienceAnalyzer:
    """Analyzes candidate work experience using LLM for intelligent assessment"""

    def __init__(self):
        self.llm = GroqLLM().get_llm_model()

    def analyze_experience(
        self, candidate: Candidate, job_requirements: JobRequirements
    ) -> ExperienceScore:
        """
        Analyze candidate's work experience comprehensively

        Uses LLM to assess:
        - Experience relevance and depth
        - Career trajectory and progression
        - Domain/industry alignment
        - Role complexity and responsibilities
        - Leadership and impact

        Args:
            candidate: Candidate object
            job_requirements: JobRequirements object

        Returns:
            ExperienceScore with detailed analysis
        """
        print(f" Analyzing experience for {candidate.name}...")

        # Basic metrics
        total_years = candidate.total_experience_years
        required_years = job_requirements.experience.minimum_years or 0

        # Determine relevant experience using LLM
        relevant_analysis = self._analyze_relevant_experience(
            candidate, job_requirements
        )

        # Analyze career progression using LLM
        progression_analysis = self._analyze_career_progression(
            candidate.work_experience, job_requirements
        )

        # Calculate score based on analysis
        experience_match_score = self._calculate_experience_score(
            total_years, required_years, relevant_analysis, progression_analysis
        )

        # Generate comprehensive analysis
        final_analysis = self._generate_comprehensive_analysis(
            candidate,
            job_requirements,
            relevant_analysis,
            progression_analysis,
            total_years,
            required_years,
        )

        return ExperienceScore(
            candidate_name=candidate.name,
            total_years=total_years,
            relevant_years=relevant_analysis.get("relevant_years", total_years),
            required_years=required_years,
            domain_match=relevant_analysis.get("domain_match", False),
            relevant_domains=relevant_analysis.get("relevant_domains", []),
            has_role_progression=progression_analysis.get("has_progression", False),
            career_trajectory=progression_analysis.get("trajectory", "lateral"),
            experience_match_score=round(experience_match_score, 1),
            experience_analysis=final_analysis,
        )

    def _analyze_relevant_experience(
        self, candidate: Candidate, job_requirements: JobRequirements
    ) -> dict:
        """
        Use LLM to determine which experience is relevant to the role

        This is more nuanced than simple keyword matching - the LLM can understand:
        - Transferable skills across domains
        - Similar role responsibilities
        - Industry adjacency
        """

        # Prepare work history summary
        work_summary = self._format_work_history(candidate.work_experience)

        prompt = WORK_EXPERIENCE_RELEVANCE_PROMPT.format(
            job_title=job_requirements.job_title,
            required_domains=", ".join(job_requirements.experience.specific_domains)
            if job_requirements.experience.specific_domains
            else "Not specified",
            role_types=", ".join(job_requirements.experience.role_types)
            if job_requirements.experience.role_types
            else "Not specified",
            key_responsibilities=", ".join(job_requirements.responsibilities[:5])
            if job_requirements.responsibilities
            else "Not specified",
            work_summary=work_summary,
            total_experience_years=candidate.total_experience_years,
        )

        try:
            messages = [
                SystemMessage(
                    content="You are an expert at assessing work experience relevance with nuance and fairness."
                ),
                HumanMessage(content=prompt),
            ]

            response = self.llm.invoke(messages)
            response_text = extract_response_text(response)
            # Parse JSON response
            import json

            analysis = json.loads(response_text)
            return analysis

        except Exception as e:
            print(f" LLM relevance analysis failed: {e}")
            # Fallback: assume all experience is relevant
            return {
                "relevant_years": candidate.total_experience_years,
                "domain_match": False,
                "relevant_domains": [],
                "relevance_reasoning": "Unable to assess relevance automatically.",
            }

    def _analyze_career_progression(
        self, work_history: list[WorkExperience], job_requirements: JobRequirements
    ) -> dict:
        """
        Use LLM to analyze career trajectory and progression

        Assesses:
        - Role level progression (junior → senior → lead)
        - Increasing responsibility
        - Skill development trajectory
        - Career direction alignment with target role
        """

        if not work_history:
            return {
                "has_progression": False,
                "trajectory": "unknown",
                "progression_reasoning": "No work history available.",
            }

        # Format work history chronologically
        work_summary = self._format_work_history_chronological(work_history)

        prompt = CAREER_PROGRESSION_ANALYSIS_PROMPT.format(
            job_title=job_requirements.job_title,
            work_summary=work_summary,
        )

        try:
            messages = [
                SystemMessage(
                    content="You are an expert career analyst who understands professional growth patterns."
                ),
                HumanMessage(content=prompt),
            ]

            response = self.llm.invoke(messages)
            response_text = extract_response_text(response)
            # Parse JSON
            import json

            analysis = json.loads(response_text)
            return analysis

        except Exception as e:
            print(f" LLM progression analysis failed: {e}")
            return {
                "has_progression": False,
                "trajectory": "unknown",
                "progression_reasoning": "Unable to assess progression automatically.",
            }

    def _calculate_experience_score(
        self,
        total_years: float,
        required_years: int,
        relevance_analysis: dict,
        progression_analysis: dict,
    ) -> float:
        """
        Calculate numerical experience match score (0-100)

        Scoring factors:
        - Years match (40%): Does experience meet minimum?
        - Relevance (35%): How relevant is the experience?
        - Progression (25%): Career trajectory quality
        """

        # Years score (40 points)
        if required_years == 0:
            years_score = 40.0
        else:
            years_ratio = total_years / required_years
            years_score = min(40.0, years_ratio * 40.0)

        # Relevance score (35 points)
        relevant_years = relevance_analysis.get("relevant_years", total_years)
        if total_years > 0:
            relevance_ratio = relevant_years / total_years
            relevance_score = relevance_ratio * 35.0
        else:
            relevance_score = 0.0

        # Domain match bonus
        if relevance_analysis.get("domain_match", False):
            relevance_score = min(35.0, relevance_score + 5.0)

        # Progression score (25 points)
        trajectory = progression_analysis.get("trajectory", "unknown")
        progression_map = {
            "upward": 25.0,
            "specialist": 22.0,
            "lateral": 18.0,
            "pivot": 15.0,
            "early-career": 12.0,
            "stagnant": 8.0,
            "unknown": 10.0,
        }
        progression_score = progression_map.get(trajectory, 10.0)

        total_score = years_score + relevance_score + progression_score
        return min(100.0, total_score)

    def _generate_comprehensive_analysis(
        self,
        candidate: Candidate,
        job_requirements: JobRequirements,
        relevance_analysis: dict,
        progression_analysis: dict,
        total_years: float,
        required_years: int,
    ) -> str:
        """
        Generate final comprehensive experience analysis using LLM

        This creates a holistic narrative that synthesizes all insights
        """
        prompt = EXPERIENCE_ASSESSMENT_PROMPT.format(
            candidate_name=candidate.name,
            job_title=job_requirements.job_title,
            required_years=required_years,
            total_years=total_years,
            relevance_reasoning=relevance_analysis.get(
                "relevance_reasoning", "Not available"
            ),
            relevant_years=relevance_analysis.get("relevant_years", total_years),
            domain_match="Yes" if relevance_analysis.get("domain_match") else "No",
            progression_reasoning=progression_analysis.get(
                "progression_reasoning", "Not available"
            ),
            trajectory=progression_analysis.get("trajectory", "unknown"),
            readiness_for_role=progression_analysis.get(
                "readiness_for_role", "Not assessed"
            ),
        )

        try:
            messages = [
                SystemMessage(
                    content="You are an expert recruiter writing clear, actionable candidate assessments."
                ),
                HumanMessage(content=prompt),
            ]

            response = self.llm.invoke(messages)
            return response.content.strip()

        except Exception as e:
            print(f" LLM comprehensive analysis failed: {e}")
            # Fallback to basic analysis
            return self._generate_basic_analysis(
                candidate.name,
                total_years,
                required_years,
                relevance_analysis,
                progression_analysis,
            )

    def _format_work_history(self, work_experience: list[WorkExperience]) -> str:
        """Format work history for LLM prompt"""
        if not work_experience:
            return "No work experience listed."

        summary = []
        for i, exp in enumerate(work_experience, 1):
            duration = (
                f"{exp.duration_months} months"
                if exp.duration_months
                else "Unknown duration"
            )
            current = " (Current)" if exp.is_current else ""

            summary.append(f"{i}. {exp.position} at {exp.company}{current}")
            summary.append(f"   Duration: {duration}")
            if exp.technologies:
                summary.append(f"   Technologies: {', '.join(exp.technologies[:5])}")
            if exp.responsibilities:
                summary.append(
                    f"   Key responsibilities: {'; '.join(exp.responsibilities[:3])}"
                )
            summary.append("")

        return "\n".join(summary)

    def _format_work_history_chronological(
        self, work_experience: list[WorkExperience]
    ) -> str:
        """Format work history in chronological order (oldest to newest)"""
        if not work_experience:
            return "No work experience listed."

        # Sort by start date (oldest first)
        sorted_exp = sorted(
            work_experience,
            key=lambda x: x.start_date if x.start_date else date(1900, 1, 1),
        )

        summary = []
        for i, exp in enumerate(sorted_exp, 1):
            start = exp.start_date.strftime("%Y-%m") if exp.start_date else "Unknown"
            end = exp.end_date.strftime("%Y-%m") if exp.end_date else "Present"

            summary.append(f"{i}. {exp.position} at {exp.company} ({start} to {end})")
            if exp.responsibilities:
                summary.append(
                    f"   Responsibilities: {'; '.join(exp.responsibilities[:2])}"
                )
            summary.append("")

        return "\n".join(summary)

    def _generate_basic_analysis(
        self,
        name: str,
        total_years: float,
        required_years: int,
        relevance_analysis: dict,
        progression_analysis: dict,
    ) -> str:
        """Fallback basic analysis"""

        analysis = f"Experience Assessment for {name}:\n\n"

        if total_years >= required_years:
            analysis += f"Meets experience requirement with {total_years} years (required: {required_years}+).\n"
        else:
            analysis += f"Below experience requirement: {total_years} years (required: {required_years}+).\n"

        relevant_years = relevance_analysis.get("relevant_years", total_years)
        analysis += f"Relevant experience: ~{relevant_years} years.\n"

        trajectory = progression_analysis.get("trajectory", "unknown")
        analysis += f"Career trajectory: {trajectory}.\n"

        return analysis


def experience_analyzer_node(state: dict) -> dict:
    """
    LangGraph node: Analyze experience for all candidates
    """
    print("Analyzing work experience...")

    analyzer = ExperienceAnalyzer()

    # Convert job_requirements dict back to model
    job_req = JobRequirements(**state["job_requirements"])

    experience_scores = []

    for candidate_data in state["candidates"]:
        candidate = Candidate(**candidate_data)

        experience_score = analyzer.analyze_experience(candidate, job_req)
        experience_scores.append(experience_score.model_dump())

        print(
            f" {candidate.name}: {experience_score.experience_match_score:.1f}% "
            f"({experience_score.relevant_years}/{experience_score.required_years} years, "
            f"{experience_score.career_trajectory} trajectory)"
        )

    print(f"Experience analysis complete for {len(experience_scores)} candidates\n")

    return {
        "experience_scores": experience_scores,
        "current_step": "experience_analysis_complete",
    }


# Test independently
if __name__ == "__main__":
    from datetime import date

    from src.data_models import (
        EducationRequirement,
        ExperienceRequirement,
        WorkExperience,
    )

    # Mock job requirements
    job = JobRequirements(
        job_title="Senior AI Engineer",
        job_description="Build AI systems",
        responsibilities=[
            "Design and implement ML models",
            "Lead technical projects",
            "Mentor junior engineers",
        ],
        technical_skills=[],
        experience=ExperienceRequirement(
            minimum_years=5,
            specific_domains=["Machine Learning", "AI"],
            role_types=["AI Engineer", "ML Engineer", "Data Scientist"],
        ),
        education=EducationRequirement(minimum_degree="Bachelor"),
    )

    # Mock candidate
    candidate = Candidate(
        name="Jane Smith",
        technical_skills=["Python", "TensorFlow"],
        total_experience_months=72,  # 6 years
        work_experience=[
            WorkExperience(
                company="Tech Corp",
                position="Junior ML Engineer",
                start_date=date(2018, 1, 1),
                end_date=date(2020, 6, 1),
                duration_months=30,
                responsibilities=[
                    "Built recommendation systems",
                    "Trained deep learning models",
                ],
                technologies=["Python", "TensorFlow", "AWS"],
            ),
            WorkExperience(
                company="AI Startup",
                position="Senior ML Engineer",
                start_date=date(2020, 7, 1),
                end_date=date(2023, 12, 1),
                duration_months=42,
                responsibilities=[
                    "Led ML team of 3 engineers",
                    "Designed NLP pipelines",
                    "Deployed models to production",
                ],
                technologies=["Python", "PyTorch", "Docker", "Kubernetes"],
            ),
        ],
        education=[],
    )

    analyzer = ExperienceAnalyzer()
    score = analyzer.analyze_experience(candidate, job)

    print("\n" + "=" * 80)
    print("EXPERIENCE ANALYSIS RESULT")
    print("=" * 80)
    print(f"\nCandidate: {candidate.name}")
    print(f"Experience Score: {score.experience_match_score}%")
    print(f"Total Years: {score.total_years}")
    print(f"Relevant Years: {score.relevant_years}")
    print(f"Required Years: {score.required_years}")
    print(f"Domain Match: {score.domain_match}")
    print(f"Career Trajectory: {score.career_trajectory}")
    print(f"\n{'=' * 80}")
    print("COMPREHENSIVE ANALYSIS:")
    print("=" * 80)
    print(f"\n{score.experience_analysis}")
    print("\n" + "=" * 80)
