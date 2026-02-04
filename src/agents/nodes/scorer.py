from langchain_core.messages import HumanMessage, SystemMessage

from config.prompts import (
    CANDIDATE_RANKING_EXPLANATION_PROMPT,
    FINAL_CANDIDATE_ASSESSMENT_PROMPT,
)
from config.settings import settings
from src.llm.groq_llm import GroqLLM
from src.models import (
    Candidate,
    CandidateScore,
    EducationScore,
    ExperienceScore,
    JobRequirements,
    RankedCandidate,
    SkillScore,
)


class CandidateScorer:
    """Scores and ranks candidates using weighted scoring + LLM analysis"""

    def __init__(self):
        self.llm = GroqLLM().get_llm_model()

        # Get weights from settings
        self.skill_weight = settings.SKILL_WEIGHT
        self.experience_weight = settings.EXPERIENCE_WEIGHT
        self.education_weight = settings.EDUCATION_WEIGHT

    def score_and_rank_candidates(
        self,
        candidates: list[dict],
        job_requirements: dict,
        skill_scores: list[dict],
        experience_scores: list[dict],
        education_scores: list[dict],
    ) -> list[RankedCandidate]:
        """
        Score all candidates and rank them

        Args:
            candidates: List of candidate dicts
            job_requirements: Job requirements dict
            skill_scores: List of skill score dicts
            experience_scores: List of experience score dicts
            education_scores: List of education score dicts

        Returns:
            List of RankedCandidate objects (sorted by score)
        """
        print("Scoring and ranking candidates...")

        # Convert dicts to models
        job_req = JobRequirements(**job_requirements)
        candidate_models = [Candidate(**c) for c in candidates]
        skill_score_models = [SkillScore(**s) for s in skill_scores]
        exp_score_models = [ExperienceScore(**e) for e in experience_scores]
        edu_score_models = [EducationScore(**e) for e in education_scores]

        # Score each candidate
        candidate_scores = []
        for i, candidate in enumerate(candidate_models):
            score = self._score_candidate(
                candidate,
                job_req,
                skill_score_models[i],
                exp_score_models[i],
                edu_score_models[i],
            )
            candidate_scores.append(score)

        # Sort by total score (highest first)
        candidate_scores.sort(key=lambda x: x.total_score, reverse=True)

        # Create ranked candidates with comparative analysis
        ranked_candidates = []
        for rank, score in enumerate(candidate_scores, 1):
            comparison = self._generate_comparative_analysis(
                score, rank, len(candidate_scores), candidate_scores
            )

            ranked = RankedCandidate(
                rank=rank, candidate_score=score, comparison_notes=comparison
            )
            ranked_candidates.append(ranked)

            print(
                f"  #{rank} {score.candidate_name}: {score.total_score:.1f}% "
                f"({score.recommendation})"
            )

        return ranked_candidates

    def _score_candidate(
        self,
        candidate: Candidate,
        job_requirements: JobRequirements,
        skill_score: SkillScore,
        experience_score: ExperienceScore,
        education_score: EducationScore,
    ) -> CandidateScore:
        """
        Calculate comprehensive score for a candidate

        Weighted scoring:
        - Skills: 50% (configurable)
        - Experience: 30% (configurable)
        - Education: 20% (configurable)
        """

        # Calculate weighted scores
        weighted_skill = skill_score.overall_skill_score * self.skill_weight
        weighted_exp = experience_score.experience_match_score * self.experience_weight
        weighted_edu = education_score.education_score * self.education_weight

        # Total score
        total_score = weighted_skill + weighted_exp + weighted_edu

        # Determine recommendation level
        recommendation, confidence = self._determine_recommendation(
            total_score, skill_score, experience_score, education_score
        )

        # Identify strengths and concerns using LLM
        analysis = self._analyze_candidate_holistically(
            candidate,
            job_requirements,
            skill_score,
            experience_score,
            education_score,
            total_score,
        )

        return CandidateScore(
            candidate_name=candidate.name,
            candidate_email=candidate.email,
            skill_score=skill_score,
            experience_score=experience_score,
            education_score=education_score,
            weighted_skill_score=round(weighted_skill, 1),
            weighted_experience_score=round(weighted_exp, 1),
            weighted_education_score=round(weighted_edu, 1),
            total_score=round(total_score, 1),
            recommendation=recommendation,
            confidence_level=confidence,
            strengths=analysis["strengths"],
            concerns=analysis["concerns"],
            red_flags=analysis["red_flags"],
            detailed_analysis=analysis["detailed_analysis"],
        )

    def _determine_recommendation(
        self,
        total_score: float,
        skill_score: SkillScore,
        experience_score: ExperienceScore,
        education_score: EducationScore,
    ) -> tuple:
        """
        Determine recommendation level and confidence

        Returns:
            (recommendation, confidence_level)
        """

        # Base recommendation on total score
        if total_score >= 85:
            recommendation = "Strong Match"
            confidence = "High"
        elif total_score >= 70:
            recommendation = "Good Match"
            confidence = "High" if total_score >= 77 else "Medium"
        elif total_score >= 55:
            recommendation = "Potential Match"
            confidence = "Medium"
        else:
            recommendation = "Not Recommended"
            confidence = "High" if total_score < 40 else "Medium"

        # Check for critical disqualifiers
        if skill_score.has_critical_gaps:
            # Missing must-have skills - downgrade
            if recommendation == "Strong Match":
                recommendation = "Good Match"
                confidence = "Medium"
            elif recommendation == "Good Match":
                recommendation = "Potential Match"
                confidence = "Low"

        if not experience_score.meets_minimum_requirement:
            # Below minimum experience
            if recommendation in ["Strong Match", "Good Match"]:
                confidence = "Medium"

        return recommendation, confidence

    def _analyze_candidate_holistically(
        self,
        candidate: Candidate,
        job_requirements: JobRequirements,
        skill_score: SkillScore,
        experience_score: ExperienceScore,
        education_score: EducationScore,
        total_score: float,
    ) -> dict:
        """
        Use LLM to perform holistic candidate analysis

        Returns:
            {
                "strengths": [...],
                "concerns": [...],
                "red_flags": [...],
                "detailed_analysis": "..."
            }
        """

        prompt = FINAL_CANDIDATE_ASSESSMENT_PROMPT.format(
            job_title=job_requirements.job_title,
            candidate_name=candidate.name,
            overall_score=f"{total_score:.1f}",
            skills_score=f"{skill_score.overall_skill_score:.1f}",
            skills_weight=f"{self.skill_weight * 100:.0f}",
            must_have_match=f"{skill_score.must_have_match_percentage:.1f}",
            missing_must_have=", ".join(skill_score.missing_must_have)
            if skill_score.missing_must_have
            else "None",
            experience_score=f"{experience_score.experience_match_score:.1f}",
            experience_weight=f"{self.experience_weight * 100:.0f}",
            total_years=experience_score.total_years,
            required_years=experience_score.required_years,
            career_trajectory=experience_score.career_trajectory,
            education_score=f"{education_score.education_score:.1f}",
            education_weight=f"{self.education_weight * 100:.0f}",
            highest_degree=education_score.highest_degree or "None",
            meets_education_requirement=education_score.meets_requirement,
            skill_gap_analysis=skill_score.skill_gap_analysis,
            experience_analysis=experience_score.experience_analysis,
            education_analysis=education_score.education_analysis,
        )

        try:
            messages = [
                SystemMessage(
                    content="You are an expert recruiter providing clear, actionable candidate assessments."
                ),
                HumanMessage(content=prompt),
            ]

            response = self.llm.invoke(messages)

            # Parse JSON
            import json

            response_text = response.content.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            analysis = json.loads(response_text.strip())
            return analysis

        except Exception as e:
            print(f" LLM holistic analysis failed: {e}")
            # Fallback
            return {
                "strengths": [f"Overall score: {total_score:.1f}%"],
                "concerns": ["Unable to generate detailed analysis"],
                "red_flags": [],
                "detailed_analysis": f"{candidate.name} scored {total_score:.1f}% overall.",
            }

    def _generate_comparative_analysis(
        self,
        candidate_score: CandidateScore,
        rank: int,
        total_candidates: int,
        all_scores: list[CandidateScore],
    ) -> str:
        """
        Generate comparative analysis using LLM

        Explains why this candidate ranks where they do relative to others
        """

        # Only do comparative analysis for top 5
        if rank > 5 or total_candidates < 2:
            return ""

        # Get context of nearby candidates
        context_candidates = []

        # Add candidate above (if exists)
        if rank > 1:
            above = all_scores[rank - 2]
            context_candidates.append(
                f"Ranked #{rank - 1}: {above.candidate_name} ({above.total_score:.1f}%)"
            )

        # Add candidate below (if exists)
        if rank < total_candidates:
            below = all_scores[rank]
            context_candidates.append(
                f"Ranked #{rank + 1}: {below.candidate_name} ({below.total_score:.1f}%)"
            )

        context_str = (
            "\n".join(context_candidates)
            if context_candidates
            else "No nearby candidates"
        )

        prompt = CANDIDATE_RANKING_EXPLANATION_PROMPT.format(
            candidate_name=candidate_score.candidate_name,
            rank=rank,
            total_candidates=total_candidates,
            total_score=f"{candidate_score.total_score:.1f}",
            recommendation=candidate_score.recommendation,
            key_strengths="; ".join(candidate_score.strengths[:2]),
            key_concerns="; ".join(candidate_score.concerns[:2])
            if candidate_score.concerns
            else "None",
            context=context_str,
        )

        try:
            messages = [
                SystemMessage(
                    content="You are an expert at explaining candidate rankings clearly and comparatively."
                ),
                HumanMessage(content=prompt),
            ]

            response = self.llm.invoke(messages)
            return response.content.strip()

        except Exception as e:
            print(f" Comparative analysis failed: {e}")
            return ""


def scorer_node(state: dict) -> dict:
    """
    LangGraph node: Score and rank all candidates
    """
    print(" Scoring and ranking candidates...")

    scorer = CandidateScorer()

    ranked_candidates = scorer.score_and_rank_candidates(
        state["candidates"],
        state["job_requirements"],
        state["skill_scores"],
        state["experience_scores"],
        state["education_scores"],
    )

    # Convert to dicts for state
    candidate_scores = [rc.candidate_score.model_dump() for rc in ranked_candidates]
    ranked_dicts = [rc.model_dump() for rc in ranked_candidates]

    print(
        f" Scoring complete. Top candidate: {ranked_candidates[0].candidate_score.candidate_name} "
        f"({ranked_candidates[0].candidate_score.total_score:.1f}%)\n"
    )

    return {
        "candidate_scores": candidate_scores,
        "ranked_candidates": ranked_dicts,
        "current_step": "scoring_complete",
    }


# Test independently
if __name__ == "__main__":
    from src.models import (
        EducationRequirement,
        ExperienceRequirement,
        Skill,
        SkillPriority,
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
        education=EducationRequirement(minimum_degree="Bachelor"),
    )

    # Candidate 1
    candidate1 = Candidate(
        name="Alice Johnson",
        email="alice@example.com",
        technical_skills=["Python", "TensorFlow", "PyTorch"],
        total_experience_months=72,
        work_experience=[],
        education=[],
    )

    skill_score1 = SkillScore(
        candidate_name="Alice Johnson",
        matched_must_have=["Python", "TensorFlow"],
        missing_must_have=[],
        matched_nice_to_have=[],
        missing_nice_to_have=[],
        additional_skills=["PyTorch"],
        must_have_match_percentage=100.0,
        nice_to_have_match_percentage=100.0,
        overall_skill_score=100.0,
        skill_gap_analysis="Perfect skill match.",
    )

    exp_score1 = ExperienceScore(
        candidate_name="Alice Johnson",
        total_years=6.0,
        relevant_years=6.0,
        required_years=5,
        domain_match=True,
        relevant_domains=["AI", "ML"],
        has_role_progression=True,
        career_trajectory="upward",
        experience_match_score=95.0,
        experience_analysis="Excellent experience.",
    )

    edu_score1 = EducationScore(
        candidate_name="Alice Johnson",
        highest_degree="Master of Science",
        required_degree="Bachelor",
        meets_requirement=True,
        field_match=True,
        education_score=100.0,
        education_analysis="Exceeds requirements.",
    )

    scorer = CandidateScorer()

    # Score single candidate
    candidate_score = scorer._score_candidate(
        candidate1, job, skill_score1, exp_score1, edu_score1
    )

    print("\n" + "=" * 80)
    print(" CANDIDATE SCORE RESULT")
    print("=" * 80)
    print(f"\nCandidate: {candidate_score.candidate_name}")
    print(f"Total Score: {candidate_score.total_score:.1f}%")
    print(
        f"Recommendation: {candidate_score.recommendation} (Confidence: {candidate_score.confidence_level})"
    )
    print("\nComponent Scores:")
    print(
        f"  - Skills: {candidate_score.weighted_skill_score:.1f} ({candidate_score.skill_score.overall_skill_score:.1f}% × {settings.SKILL_WEIGHT})"
    )
    print(
        f"  - Experience: {candidate_score.weighted_experience_score:.1f} ({candidate_score.experience_score.experience_match_score:.1f}% × {settings.EXPERIENCE_WEIGHT})"
    )
    print(
        f"  - Education: {candidate_score.weighted_education_score:.1f} ({candidate_score.education_score.education_score:.1f}% × {settings.EDUCATION_WEIGHT})"
    )
    print(f"\n{'=' * 80}")
    print("STRENGTHS:")
    print("=" * 80)
    for strength in candidate_score.strengths:
        print(f" {strength}")
    print(f"\n{'=' * 80}")
    print("CONCERNS:")
    print("=" * 80)
    if candidate_score.concerns:
        for concern in candidate_score.concerns:
            print(f"  {concern}")
    else:
        print("  None")
    print(f"\n{'=' * 80}")
    print("DETAILED ANALYSIS:")
    print("=" * 80)
    print(f"\n{candidate_score.detailed_analysis}")
    print("\n" + "=" * 80)
