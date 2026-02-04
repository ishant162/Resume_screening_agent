
from langchain_core.messages import HumanMessage, SystemMessage

from config.prompts import INTERVIEW_QUESTION_GENERATION_PROMPT
from src.llm.groq_llm import GroqLLM
from src.models import Candidate, CandidateScore, JobRequirements


class QuestionGenerator:
    """Generates personalized interview questions for candidates"""

    def __init__(self):
        self.llm = GroqLLM().get_llm_model()

    def generate_questions_for_candidates(
        self,
        candidates: list[dict],
        job_requirements: dict,
        candidate_scores: list[dict]
    ) -> dict[str, list[str]]:
        """
        Generate personalized interview questions for all candidates

        Args:
            candidates: List of candidate dicts
            job_requirements: Job requirements dict
            candidate_scores: List of candidate score dicts

        Returns:
            Dictionary mapping candidate names to question lists
        """
        print("Generating personalized interview questions...")

        job_req = JobRequirements(**job_requirements)
        candidate_models = [Candidate(**c) for c in candidates]
        score_models = [CandidateScore(**cs) for cs in candidate_scores]

        all_questions = {}

        for candidate, score in zip(candidate_models, score_models):
            questions = self._generate_questions_for_candidate(
                candidate,
                job_req,
                score
            )
            all_questions[candidate.name] = questions

            print(f"Generated {len(questions)} questions for {candidate.name}")

        return all_questions

    def _generate_questions_for_candidate(
        self,
        candidate: Candidate,
        job_requirements: JobRequirements,
        candidate_score: CandidateScore
    ) -> list[str]:
        """
        Generate personalized questions for a single candidate

        Questions should:
        - Test required skills
        - Probe skill gaps
        - Explore experience relevance
        - Assess cultural fit
        - Be specific to their background
        """

        # Prepare candidate context
        work_summary = self._format_work_experience(candidate.work_experience[:2])

        prompt = INTERVIEW_QUESTION_GENERATION_PROMPT.format(
            job_title=job_requirements.job_title,
            candidate_name=candidate.name,
            candidate_skills=", ".join(candidate.technical_skills[:15]),
            total_experience_years=candidate.total_experience_years,
            highest_education=(
                candidate.highest_education.degree
                if candidate.highest_education else "Not specified"
            ),
            work_summary=work_summary,
            overall_score=f"{candidate_score.total_score:.1f}",
            skills_match_score=f"{candidate_score.skill_score.overall_skill_score:.1f}",
            missing_critical_skills=", ".join(candidate_score.skill_score.missing_must_have)
                if candidate_score.skill_score.missing_must_have else "None",
            career_trajectory=candidate_score.experience_score.career_trajectory,
            key_strengths=self._format_list(candidate_score.strengths[:3]),
            key_concerns=(
                self._format_list(candidate_score.concerns[:3])
                if candidate_score.concerns else "None"
            ),
        )
        try:
            messages = [
                SystemMessage(content="You are an expert technical interviewer who creates insightful, personalized questions."),
                HumanMessage(content=prompt)
            ]

            response = self.llm.invoke(messages)

            # Parse JSON
            import json
            response_text = response.content.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            questions = json.loads(response_text.strip())

            # Validate it's a list
            if isinstance(questions, list):
                return questions
            else:
                print(" LLM returned non-list format")
                return self._generate_fallback_questions(candidate, job_requirements)

        except Exception as e:
            print(f" Question generation failed: {e}")
            return self._generate_fallback_questions(candidate, job_requirements)

    def _generate_fallback_questions(
        self,
        candidate: Candidate,
        job_requirements: JobRequirements
    ) -> list[str]:
        """Generate basic fallback questions"""

        questions = [
            f"Tell me about your experience with {candidate.technical_skills[0] if candidate.technical_skills else 'the technologies'} mentioned in your resume.",
            f"Can you walk me through a challenging project from your time at {candidate.work_experience[0].company if candidate.work_experience else 'your previous company'}?",
            "How do you approach learning new technologies or skills?",
            f"What interests you about the {job_requirements.job_title} role?",
            "Describe a time when you had to debug a complex technical issue.",
            "How do you handle working with tight deadlines?",
            "Tell me about a time you collaborated with a team on a technical project.",
            "What's your approach to code quality and testing?",
            "How do you stay updated with industry trends and new technologies?",
            "Can you describe your development workflow and tools you prefer?"
        ]

        return questions

    def _format_work_experience(self, experiences: list) -> str:
        """Format work experience for prompt"""
        if not experiences:
            return "No work experience listed"

        summary = []
        for exp in experiences:
            summary.append(f"- {exp.position} at {exp.company}")
            if exp.responsibilities:
                summary.append(f"  Responsibilities: {'; '.join(exp.responsibilities[:2])}")

        return "\n".join(summary)

    def _format_list(self, items: list[str]) -> str:
        """Format list for prompt"""
        return "\n".join(f"- {item}" for item in items)


def question_generator_node(state: dict) -> dict:
    """
    LangGraph node: Generate interview questions for all candidates
    """
    print("Generating personalized interview questions...")

    generator = QuestionGenerator()

    questions = generator.generate_questions_for_candidates(
        state["candidates"],
        state["job_requirements"],
        state["candidate_scores"]
    )

    print(f"Generated questions for {len(questions)} candidates\n")

    return {
        "interview_questions": questions,
        "current_step": "question_generation_complete"
    }


# Test independently
if __name__ == "__main__":
    from datetime import date

    from src.models import (
        EducationRequirement,
        EducationScore,
        ExperienceRequirement,
        ExperienceScore,
        Skill,
        SkillPriority,
        SkillScore,
        WorkExperience,
    )

    # Mock data
    job = JobRequirements(
        job_title="Senior AI Engineer",
        job_description="Build AI systems",
        technical_skills=[
            Skill(name="Python", priority=SkillPriority.MUST_HAVE),
            Skill(name="TensorFlow", priority=SkillPriority.MUST_HAVE),
        ],
        experience=ExperienceRequirement(minimum_years=5),
        education=EducationRequirement(minimum_degree="Bachelor")
    )

    candidate = Candidate(
        name="Sarah Chen",
        technical_skills=["Python", "TensorFlow", "Docker", "AWS"],
        total_experience_months=72,
        work_experience=[
            WorkExperience(
                company="Tech Startup",
                position="ML Engineer",
                start_date=date(2019, 1, 1),
                end_date=date(2024, 1, 1),
                responsibilities=[
                    "Built recommendation systems",
                    "Deployed models to production"
                ],
                technologies=["Python", "TensorFlow", "AWS"]
            )
        ],
        education=[]
    )

    # Mock score
    candidate_score = CandidateScore(
        candidate_name="Sarah Chen",
        candidate_email="sarah@example.com",
        skill_score=SkillScore(
            candidate_name="Sarah Chen",
            matched_must_have=["Python", "TensorFlow"],
            missing_must_have=[],
            matched_nice_to_have=[],
            missing_nice_to_have=[],
            additional_skills=["Docker", "AWS"],
            must_have_match_percentage=100.0,
            nice_to_have_match_percentage=100.0,
            overall_skill_score=100.0,
            skill_gap_analysis="Strong skills"
        ),
        experience_score=ExperienceScore(
            candidate_name="Sarah Chen",
            total_years=6.0,
            relevant_years=6.0,
            required_years=5,
            domain_match=True,
            relevant_domains=["ML"],
            has_role_progression=True,
            career_trajectory="upward",
            experience_match_score=95.0,
            experience_analysis="Excellent"
        ),
        education_score=EducationScore(
            candidate_name="Sarah Chen",
            highest_degree="Bachelor",
            required_degree="Bachelor",
            meets_requirement=True,
            field_match=True,
            education_score=90.0,
            education_analysis="Good"
        ),
        weighted_skill_score=50.0,
        weighted_experience_score=28.5,
        weighted_education_score=18.0,
        total_score=96.5,
        recommendation="Strong Match",
        confidence_level="High",
        strengths=["Excellent Python skills", "Production ML experience"],
        concerns=[],
        red_flags=[],
        detailed_analysis="Strong candidate"
    )

    generator = QuestionGenerator()
    questions = generator._generate_questions_for_candidate(candidate, job, candidate_score)

    print("\n" + "="*80)
    print(f"INTERVIEW QUESTIONS FOR {candidate.name}")
    print("="*80)
    print(f"\nGenerated {len(questions)} personalized questions:\n")

    for i, q in enumerate(questions, 1):
        print(f"{i}. {q}\n")

    print("="*80)
