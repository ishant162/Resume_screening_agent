import json

from langchain_core.messages import HumanMessage, SystemMessage

from config.prompts import EDUCATION_VERIFICATION_PROMPT
from src.data_models import Candidate, Education, EducationScore, JobRequirements
from src.llm.groq_llm import GroqLLM
from src.utils.utils import extract_response_text


class EducationVerifier:
    """Verifies education requirements using LLM for intelligent assessment"""

    def __init__(self):
        self.llm = GroqLLM().get_llm_model()

    def verify_education(
        self, candidate: Candidate, job_requirements: JobRequirements
    ) -> EducationScore:
        """
        Verify candidate's education against requirements

        Uses LLM to assess:
        - Degree level equivalency (global degrees, bootcamps, etc.)
        - Field of study relevance
        - Alternative qualifications (certifications, self-taught)
        - Educational trajectory and continuous learning

        Args:
            candidate: Candidate object
            job_requirements: JobRequirements object

        Returns:
            EducationScore with verification results
        """
        print(f"  🎓 Verifying education for {candidate.name}...")

        # Get highest degree
        highest_degree = candidate.highest_education

        # Perform LLM-based verification
        verification_result = self._llm_verify_education(candidate, job_requirements)

        # Calculate education score
        education_score = self._calculate_education_score(
            verification_result, job_requirements.education.required
        )

        return EducationScore(
            candidate_name=candidate.name,
            highest_degree=highest_degree.degree if highest_degree else None,
            required_degree=job_requirements.education.minimum_degree,
            meets_requirement=verification_result.get("meets_requirement", False),
            field_match=verification_result.get("field_match", False),
            relevant_coursework=verification_result.get("relevant_coursework", []),
            certifications=[cert.name for cert in candidate.certifications],
            education_score=round(education_score, 1),
            education_analysis=verification_result.get(
                "analysis", "No analysis available"
            ),
        )

    def _llm_verify_education(
        self, candidate: Candidate, job_requirements: JobRequirements
    ) -> dict:
        """
        Use LLM to intelligently verify education requirements

        The LLM can handle:
        - International degree equivalents (e.g., BTech = BS)
        - Non-traditional education (bootcamps, MOOCs, self-taught)
        - Field adjacency (e.g., Physics degree for ML role)
        - Experience as substitute for formal education
        """

        # Format candidate education
        education_summary = self._format_education(candidate.education)

        # Format certifications
        cert_summary = (
            ", ".join([cert.name for cert in candidate.certifications])
            if candidate.certifications
            else "None"
        )

        prompt = EDUCATION_VERIFICATION_PROMPT.format(
            minimum_degree=job_requirements.education.minimum_degree,
            preferred_degree=job_requirements.education.preferred_degree
            or "Not specified",
            fields_of_study=", ".join(job_requirements.education.fields_of_study)
            if job_requirements.education.fields_of_study
            else "Not specified",
            degree_required="Yes"
            if job_requirements.education.required
            else "No (preferred but not required)",
            candidate_name=candidate.name,
            total_experience_years=candidate.total_experience_years,
            education_summary=education_summary,
            cert_summary=cert_summary,
        )

        try:
            messages = [
                SystemMessage(
                    content="You are an expert at fairly assessing educational qualifications with global and non-traditional education awareness."
                ),
                HumanMessage(content=prompt),
            ]

            response = self.llm.invoke(messages)
            response_text = extract_response_text(response)

            result = json.loads(response_text)
            return result

        except Exception as e:
            print(f"LLM education verification failed: {e}")
            # Fallback: simple verification
            return self._simple_verification(candidate, job_requirements)

    def _simple_verification(
        self, candidate: Candidate, job_requirements: JobRequirements
    ) -> dict:
        """Fallback simple verification"""

        highest = candidate.highest_education
        required = job_requirements.education.minimum_degree.lower()

        meets_requirement = False
        if highest:
            degree_lower = highest.degree.lower()
            # Simple matching
            if "master" in required or "mtech" in required or "msc" in required:
                meets_requirement = any(
                    x in degree_lower
                    for x in ["master", "mtech", "msc", "phd", "doctorate"]
                )
            elif "bachelor" in required or "btech" in required or "bsc" in required:
                meets_requirement = any(
                    x in degree_lower
                    for x in ["bachelor", "btech", "bsc", "master", "phd"]
                )

        return {
            "meets_requirement": meets_requirement,
            "field_match": False,
            "degree_level_match": "unknown",
            "relevant_coursework": [],
            "compensating_factors": [],
            "analysis": f"Basic verification: {'Meets' if meets_requirement else 'Does not meet'} minimum degree requirement.",
        }

    def _calculate_education_score(
        self, verification_result: dict, education_required: bool
    ) -> float:
        """
        Calculate education score (0-100)

        Scoring:
        - Meets requirement: 60 points
        - Field match: 20 points
        - Additional factors: 20 points
        """

        score = 0.0

        # Base requirement (60 points)
        if verification_result.get("meets_requirement", False):
            score += 60.0
        elif not education_required:
            # If education not required, give partial credit
            score += 30.0

        # Field match (20 points)
        if verification_result.get("field_match", False):
            score += 20.0

        # Compensating factors (20 points)
        compensating = verification_result.get("compensating_factors", [])
        if compensating:
            score += min(20.0, len(compensating) * 7.0)

        # Degree level bonus
        degree_match = verification_result.get("degree_level_match", "")
        if degree_match == "above":
            score = min(100.0, score + 10.0)  # Bonus for exceeding requirement

        return min(100.0, score)

    def _format_education(self, education: list[Education]) -> str:
        """Format education for LLM prompt"""
        if not education:
            return "No formal education listed."

        summary = []
        for i, edu in enumerate(education, 1):
            end_year = edu.end_year if edu.end_year else "In Progress"
            summary.append(f"{i}. {edu.degree} in {edu.field_of_study}")
            summary.append(f"   Institution: {edu.institution}")
            summary.append(f"   Year: {end_year}")
            if edu.grade:
                summary.append(f"   Grade: {edu.grade}")
            if edu.relevant_coursework:
                summary.append(
                    f"   Relevant Coursework: {', '.join(edu.relevant_coursework[:5])}"
                )
            summary.append("")

        return "\n".join(summary)


def education_verifier_node(state: dict) -> dict:
    """
    LangGraph node: Verify education for all candidates
    """
    print("🎓 Verifying education requirements...")

    verifier = EducationVerifier()

    # Convert job_requirements dict back to model
    job_req = JobRequirements(**state["job_requirements"])

    education_scores = []

    for candidate_data in state["candidates"]:
        candidate = Candidate(**candidate_data)

        education_score = verifier.verify_education(candidate, job_req)
        education_scores.append(education_score.model_dump())

        meets = "✅" if education_score.meets_requirement else "⚠️"
        print(
            f"  {meets} {candidate.name}: {education_score.education_score:.1f}% "
            f"({education_score.highest_degree or 'No degree'}, "
            f"field match: {education_score.field_match})"
        )

    print(f"Education verification complete for {len(education_scores)} candidates\n")

    return {
        "education_scores": education_scores,
        "current_step": "education_verification_complete",
    }


# Test independently
if __name__ == "__main__":
    from src.data_models import (
        Certification,
        Education,
        EducationRequirement,
        ExperienceRequirement,
    )

    # Mock job requirements
    job = JobRequirements(
        job_title="Senior AI Engineer",
        job_description="Build AI systems",
        technical_skills=[],
        experience=ExperienceRequirement(minimum_years=5),
        education=EducationRequirement(
            minimum_degree="Bachelor",
            preferred_degree="Master",
            fields_of_study=[
                "Computer Science",
                "AI",
                "Machine Learning",
                "Related Field",
            ],
            required=True,
        ),
    )

    # Mock candidate with BTech (Indian degree)
    candidate = Candidate(
        name="Raj Kumar",
        technical_skills=["Python", "TensorFlow"],
        total_experience_months=60,  # 5 years
        work_experience=[],
        education=[
            Education(
                institution="IIT Bombay",
                degree="Bachelor of Technology",
                field_of_study="Computer Science and Engineering",
                start_year=2014,
                end_year=2018,
                grade="8.5 CGPA",
                relevant_coursework=[
                    "Machine Learning",
                    "Deep Learning",
                    "Data Structures",
                    "Algorithms",
                ],
            )
        ],
        certifications=[
            Certification(
                name="TensorFlow Developer Certificate", issuing_organization="Google"
            ),
            Certification(
                name="Deep Learning Specialization",
                issuing_organization="Coursera/DeepLearning.AI",
            ),
        ],
    )

    verifier = EducationVerifier()
    score = verifier.verify_education(candidate, job)

    print("\n" + "=" * 80)
    print("EDUCATION VERIFICATION RESULT")
    print("=" * 80)
    print(f"\nCandidate: {candidate.name}")
    print(f"Education Score: {score.education_score}%")
    print(f"Highest Degree: {score.highest_degree}")
    print(f"Required Degree: {score.required_degree}")
    print(f"Meets Requirement: {score.meets_requirement}")
    print(f"Field Match: {score.field_match}")
    print(f"Certifications: {score.certifications}")
    print(f"\n{'=' * 80}")
    print("ANALYSIS:")
    print("=" * 80)
    print(f"\n{score.education_analysis}")
    print("\n" + "=" * 80)
