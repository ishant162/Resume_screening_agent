import json

from langchain_core.messages import HumanMessage, SystemMessage

from config.prompts import SKILL_MATCHING_PROMPT
from src.llm.groq_llm import GroqLLM
from src.models import Candidate, JobRequirements, Skill, SkillPriority, SkillScore


class SkillMatcher:
    """AI-powered skill matcher using LLM for intelligent analysis"""

    def __init__(self):
        self.llm = GroqLLM().get_llm_model()

    def match_skills(
        self,
        candidate: Candidate,
        job_requirements: JobRequirements
    ) -> SkillScore:
        """
        Use LLM to intelligently match and analyze candidate skills

        This uses AI to:
        - Recognize similar/related skills (e.g., PyTorch ≈ TensorFlow)
        - Understand skill transferability
        - Provide contextual gap analysis
        - Consider experience levels and depth

        Args:
            candidate: Candidate object
            job_requirements: JobRequirements object

        Returns:
            SkillScore with AI-powered analysis
        """
        print(f" AI analyzing skills for {candidate.name}...")

        # Prepare data for the prompt template
        must_have_skills_list = [
            f"{s.name} ({s.years_required}+ years)" if s.years_required
            else s.name
            for s in job_requirements.must_have_skills
        ]

        nice_to_have_skills_list = [
            s.name for s in job_requirements.nice_to_have_skills
        ]

        recent_projects_str = ', '.join([
            p.name for p in candidate.projects[:3]
        ]) if candidate.projects else 'None listed'

        # Format the prompt using SKILL_MATCHING_PROMPT template
        prompt = SKILL_MATCHING_PROMPT.format(
            must_have_skills=', '.join(must_have_skills_list) if must_have_skills_list else 'None',
            nice_to_have_skills=', '.join(nice_to_have_skills_list) if nice_to_have_skills_list else 'None',
            candidate_name=candidate.name,
            candidate_skills=', '.join(candidate.all_skills),
            total_experience=candidate.total_experience_years,
            recent_projects=recent_projects_str
        )

        # Call LLM with system message for context
        messages = [
            SystemMessage(
                content="""
                You are an expert technical recruiter with deep knowledge of:
                - Software engineering skills and their equivalents
                - Skill transferability and learning curves
                - Industry standards and best practices
                - How different technologies relate to each other

                Be thorough but fair in your assessment. Recognize when skills are transferable or closely related.
                """
            ),
            HumanMessage(content=prompt)
        ]

        response = self.llm.invoke(messages)

        # Parse LLM response
        try:
            skill_analysis = self._parse_llm_response(response.content)

            # Create SkillScore object
            return SkillScore(
                candidate_name=candidate.name,
                matched_must_have=skill_analysis["matched_must_have"],
                matched_nice_to_have=skill_analysis["matched_nice_to_have"],
                missing_must_have=skill_analysis["missing_must_have"],
                missing_nice_to_have=skill_analysis["missing_nice_to_have"],
                additional_skills=skill_analysis["additional_skills"][:10],
                must_have_match_percentage=round(skill_analysis["must_have_match_percentage"], 1),
                nice_to_have_match_percentage=round(skill_analysis["nice_to_have_match_percentage"], 1),
                overall_skill_score=round(skill_analysis["overall_skill_score"], 1),
                skill_gap_analysis=skill_analysis["skill_gap_analysis"]
            )

        except Exception as e:
            print(f"  Error parsing LLM response: {e}")
            print(f"  Response was: {response.content[:200]}...")
            # Fallback to basic matching
            return self._fallback_matching(candidate, job_requirements)

    def _parse_llm_response(self, response_text: str) -> dict:
        """Extract JSON from LLM response"""
        # Handle markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        # Parse JSON
        return json.loads(response_text.strip())

    def _fallback_matching(
        self,
        candidate: Candidate,
        job_requirements: JobRequirements
    ) -> SkillScore:
        """Fallback to basic rule-based matching if LLM fails"""
        print(f"  Using fallback matching for {candidate.name}")

        candidate_skills_set = set(skill.lower() for skill in candidate.all_skills)
        must_have_skills = job_requirements.must_have_skills

        matched_must_have = [
            s.name for s in must_have_skills
            if s.name.lower() in candidate_skills_set
        ]
        missing_must_have = [
            s.name for s in must_have_skills
            if s.name.lower() not in candidate_skills_set
        ]

        must_have_match_pct = (
            (len(matched_must_have) / len(must_have_skills) * 100)
            if must_have_skills else 100.0
        )

        return SkillScore(
            candidate_name=candidate.name,
            matched_must_have=matched_must_have,
            matched_nice_to_have=[],
            missing_must_have=missing_must_have,
            missing_nice_to_have=[],
            additional_skills=[],
            must_have_match_percentage=round(must_have_match_pct, 1),
            nice_to_have_match_percentage=0.0,
            overall_skill_score=round(must_have_match_pct * 0.8, 1),
            skill_gap_analysis=f"Basic analysis: Matches {len(matched_must_have)}/{len(must_have_skills)} must-have skills."
        )


def skill_matcher_node(state: dict) -> dict:
    """
    LangGraph node: AI-powered skill matching for all candidates
    """
    print(" AI-powered skill matching in progress...")

    matcher = SkillMatcher()

    # Convert job_requirements dict back to model
    job_req = JobRequirements(**state["job_requirements"])

    skill_scores = []

    for candidate_data in state["candidates"]:
        candidate = Candidate(**candidate_data)
        skill_score = matcher.match_skills(candidate, job_req)
        skill_scores.append(skill_score.model_dump())

        print(f" {candidate.name}: {skill_score.overall_skill_score:.1f}% match "
              f"({len(skill_score.matched_must_have)}/{len(job_req.must_have_skills)} must-haves)")

    print(" Skill matching complete!\n")

    return {
        "skill_scores": skill_scores,
        "current_step": "skill_matching_complete"
    }


# Test independently
if __name__ == "__main__":
    from src.models import EducationRequirement, ExperienceRequirement, Project

    # Mock job requirements
    job = JobRequirements(
        job_title="AI Engineer",
        job_description="Building ML systems",
        technical_skills=[
            Skill(name="Python", priority=SkillPriority.MUST_HAVE, years_required=3),
            Skill(name="TensorFlow", priority=SkillPriority.MUST_HAVE),
            Skill(name="Docker", priority=SkillPriority.NICE_TO_HAVE),
            Skill(name="AWS", priority=SkillPriority.NICE_TO_HAVE),
        ],
        experience=ExperienceRequirement(minimum_years=3),
        education=EducationRequirement(minimum_degree="Bachelor")
    )

    # Mock candidate
    candidate = Candidate(
        name="John Doe",
        technical_skills=["Python", "PyTorch", "Kubernetes", "Git", "Linux"],
        work_experience=[],
        education=[],
        projects=[Project(name="Image Classification", description="Built CNN", technologies=["PyTorch"])]
    )

    matcher = SkillMatcher()
    score = matcher.match_skills(candidate, job)

    print("\n" + "="*60)
    print(" AI-Powered Skill Match Result:")
    print("="*60)
    print(f"Overall Score: {score.overall_skill_score}%")
    print(f"Must-Have Match: {score.must_have_match_percentage}%")
    print(f"Matched Must-Have: {score.matched_must_have}")
    print(f"Missing Must-Have: {score.missing_must_have}")
    print(f"\n{score.skill_gap_analysis}")
