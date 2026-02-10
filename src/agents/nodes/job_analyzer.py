import json

from langchain_core.messages import HumanMessage, SystemMessage

from config.prompts import JOB_ANALYSIS_PROMPT
from src.data_models import (
    EducationRequirement,
    ExperienceRequirement,
    JobRequirements,
    Skill,
    SkillPriority,
)
from src.llm.groq_llm import GroqLLM


class JobAnalyzer:
    """Analyzes job descriptions and extracts structured requirements"""

    def __init__(self):
        self.llm = GroqLLM().get_llm_model()

    def analyze(self, job_description: str) -> JobRequirements:
        """
        Extract structured job requirements from text

        Args:
            job_description: Raw job description text

        Returns:
            JobRequirements object with parsed data
        """
        prompt = JOB_ANALYSIS_PROMPT.format(job_description=job_description)
        messages = [
            SystemMessage(
                content="You are an expert recruiter. Extract job requirements accurately."
            ),
            HumanMessage(content=prompt),
        ]
        response = self.llm.invoke(messages)

        try:
            # Extract JSON from response (handle markdown code blocks)
            response_text = response.content
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            job_data = json.loads(response_text.strip())

            # Convert to JobRequirements model
            job_requirements = self._convert_to_model(job_data, job_description)
            return job_requirements

        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Response was: {response.content}")
            # Return a minimal JobRequirements object
            return JobRequirements(
                job_title="Unknown",
                job_description=job_description,
                technical_skills=[],
                experience=ExperienceRequirement(),
                education=EducationRequirement(
                    minimum_degree="Bachelor", required=False
                ),
            )

    def _convert_to_model(self, job_data: dict, original_jd: str) -> JobRequirements:
        """Convert raw JSON to JobRequirements Pydantic model"""

        # Parse technical skills
        technical_skills = []
        for skill_data in job_data.get("technical_skills", []):
            if isinstance(skill_data, str):
                # Simple string format
                technical_skills.append(
                    Skill(name=skill_data, priority=SkillPriority.MUST_HAVE)
                )
            else:
                # Detailed format
                priority = skill_data.get("priority", "must_have")
                technical_skills.append(
                    Skill(
                        name=skill_data["name"],
                        priority=SkillPriority(priority)
                        if priority in ["must_have", "nice_to_have", "preferred"]
                        else SkillPriority.MUST_HAVE,
                        years_required=skill_data.get("years_required"),
                    )
                )

        # Parse experience requirements
        exp_data = job_data.get("experience", {})
        experience = ExperienceRequirement(
            minimum_years=exp_data.get("minimum_years"),
            preferred_years=exp_data.get("preferred_years"),
            specific_domains=exp_data.get("specific_domains", []),
            role_types=exp_data.get("role_types", []),
        )

        # Parse education requirements
        edu_data = job_data.get("education", {})
        education = EducationRequirement(
            minimum_degree=edu_data.get("minimum_degree", "Bachelor"),
            preferred_degree=edu_data.get("preferred_degree"),
            fields_of_study=edu_data.get("fields_of_study", []),
            required=edu_data.get("required", True),
        )

        # Create JobRequirements object
        return JobRequirements(
            job_title=job_data.get("job_title", "Unknown Position"),
            job_description=original_jd,
            responsibilities=job_data.get("responsibilities", []),
            technical_skills=technical_skills,
            soft_skills=job_data.get("soft_skills", []),
            tools_and_technologies=job_data.get("tools_and_technologies", []),
            experience=experience,
            education=education,
            certifications=job_data.get("certifications", []),
            preferred_qualifications=job_data.get("preferred_qualifications", []),
        )


def job_analyzer_node(state: dict) -> dict:
    """
    LangGraph node: Analyze job description

    This is the actual node function that LangGraph will call.
    It takes the state, runs the analyzer, and returns updated state.
    """
    print("Analyzing job description...")

    analyzer = JobAnalyzer()
    job_requirements = analyzer.analyze(state["job_description"])

    # Convert to dict for state (LangGraph works with dicts)
    return {
        "job_requirements": job_requirements.model_dump(),
        "current_step": "job_analysis_complete",
    }


# Test the node independently
if __name__ == "__main__":
    sample_jd = """
    Senior Applied AI Engineer

    We are looking for an experienced AI Engineer to join our team.

    Requirements:
    - 3+ years of experience in Machine Learning
    - Strong Python programming skills
    - Experience with TensorFlow or PyTorch
    - Knowledge of NLP and Computer Vision
    - Bachelor's degree in Computer Science or related field

    Nice to have:
    - Experience with LangChain/LangGraph
    - Cloud deployment (AWS/GCP)
    - PhD in AI/ML

    Responsibilities:
    - Build and deploy ML models
    - Collaborate with cross-functional teams
    - Research new AI techniques
    """

    analyzer = JobAnalyzer()
    result = analyzer.analyze(sample_jd)

    print("\nJob Analysis Result:")
    print(f"Title: {result.job_title}")
    print(f"Must-have skills: {[s.name for s in result.must_have_skills]}")
    print(f"Experience required: {result.experience.minimum_years} years")
    print(f"Education: {result.education.minimum_degree}")
