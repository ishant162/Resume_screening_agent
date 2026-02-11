"""
Enhanced Skill Matcher Node

Uses skill taxonomy for semantic/intelligent matching.
Understands that TensorFlow ≈ PyTorch, React → Vue, etc.
"""

from langchain_core.messages import HumanMessage, SystemMessage

from config.prompts import SEMANTIC_SKILL_MATCH_ANALYSIS_PROMPT
from src.data_models import Candidate, JobRequirements, SkillScore
from src.llm.groq_llm import GroqLLM
from src.tools import SkillTaxonomy


class EnhancedSkillMatcher:
    """Enhanced skill matching with semantic understanding"""

    def __init__(self):
        self.taxonomy = SkillTaxonomy()
        self.llm = GroqLLM().get_llm_model()

    def match_skills(
        self,
        candidate: Candidate,
        job_requirements: JobRequirements,
    ) -> SkillScore:
        """
        Enhanced skill matching using taxonomy

        Args:
            candidate: Candidate model
            job_requirements: Job requirements model
            taxonomy_data: Pre-computed taxonomy data (optional, currently unused)

        Returns:
            SkillScore with enhanced matching
        """
        # Match must-have skills
        matched_must_have, missing_must_have, equivalent_matches = (
            self._match_skill_list(
                required_skills=job_requirements.must_have_skills,
                candidate_skills=candidate.technical_skills,
                threshold=0.7,
            )
        )

        # Match nice-to-have skills
        matched_nice_to_have, missing_nice_to_have, _ = self._match_skill_list(
            required_skills=job_requirements.nice_to_have_skills,
            candidate_skills=candidate.technical_skills,
            threshold=0.6,
        )

        # Find additional skills
        all_required_skill_names = set(
            s.name.lower() for s in job_requirements.technical_skills
        )
        additional_skills = [
            skill
            for skill in candidate.technical_skills
            if skill.lower() not in all_required_skill_names
        ]

        # Calculate scores
        must_have_match_pct = self._calculate_percentage(
            matched_must_have, job_requirements.must_have_skills
        )
        nice_to_have_match_pct = self._calculate_percentage(
            matched_nice_to_have, job_requirements.nice_to_have_skills
        )

        # Overall score with bonus for equivalent matches
        base_score = (must_have_match_pct * 0.8) + (nice_to_have_match_pct * 0.2)
        equiv_bonus = min(5, len(equivalent_matches) * 2)
        overall_score = min(100, base_score + equiv_bonus)

        # Generate gap analysis
        gap_analysis = self._generate_gap_analysis(
            candidate=candidate,
            matched_must=matched_must_have,
            missing_must=missing_must_have,
            equivalent_matches=equivalent_matches,
            matched_nice=matched_nice_to_have,
            additional=additional_skills,
        )

        return SkillScore(
            candidate_name=candidate.name,
            matched_must_have=matched_must_have,
            matched_nice_to_have=matched_nice_to_have,
            missing_must_have=missing_must_have,
            missing_nice_to_have=missing_nice_to_have,
            additional_skills=additional_skills[:10],
            must_have_match_percentage=round(must_have_match_pct, 1),
            nice_to_have_match_percentage=round(nice_to_have_match_pct, 1),
            overall_skill_score=round(overall_score, 1),
            skill_gap_analysis=gap_analysis,
        )

    def _match_skill_list(
        self, required_skills: list, candidate_skills: list[str], threshold: float
    ) -> tuple[list[str], list[str], dict]:
        """
        Match a list of required skills against candidate skills

        Args:
            required_skills: List of required skill objects
            candidate_skills: List of candidate's technical skills
            candidate_all_skills: Set of all candidate skills (lowercase)
            threshold: Match score threshold for equivalence

        Returns:
            Tuple of (matched_skills, missing_skills, equivalent_matches)
        """
        matched = []
        missing = []
        equivalent_matches = {}

        for required_skill in required_skills:
            required_skill_lower = required_skill.name.lower()
            # Check exact match first (case-insensitive) in ALL skills
            exact_match_found = False
            for cand_skill in candidate_skills:
                if required_skill_lower == cand_skill.lower():
                    matched.append(required_skill.name)
                    exact_match_found = True
                    break
            if exact_match_found:
                continue

            # Check for equivalent skills using taxonomy
            match_found = False
            for cand_skill in candidate_skills:
                is_equiv, score, reasoning = self.taxonomy.are_skills_equivalent(
                    required_skill.name, cand_skill, threshold=threshold
                )
                if is_equiv:
                    matched.append(required_skill.name)
                    equivalent_matches[required_skill.name] = {
                        "candidate_skill": cand_skill,
                        "match_score": score,
                        "reasoning": reasoning,
                    }
                    match_found = True
                    break

            if not match_found:
                missing.append(required_skill.name)

        return matched, missing, equivalent_matches

    def _calculate_percentage(self, matched: list, required: list) -> float:
        """Calculate match percentage"""
        if not required:
            return 100.0
        return (len(matched) / len(required)) * 100

    def _generate_gap_analysis(
        self,
        candidate: Candidate,
        matched_must: list[str],
        missing_must: list[str],
        equivalent_matches: dict,
        matched_nice: list[str],
        additional: list[str],
    ) -> str:
        """Generate gap analysis using LLM"""
        prompt = SEMANTIC_SKILL_MATCH_ANALYSIS_PROMPT.format(
            candidate_name=candidate.name,
            matched_must_have=", ".join(matched_must) if matched_must else "None",
            matched_nice_to_have=", ".join(matched_nice) if matched_nice else "None",
            equivalent_skills=self._format_equivalent_matches(equivalent_matches),
            missing_critical_skills=", ".join(missing_must) if missing_must else "None",
            additional_skills=", ".join(additional[:5]) if additional else "None",
        )

        try:
            messages = [
                SystemMessage(
                    content="You are an expert technical recruiter with deep understanding of skill relationships."
                ),
                HumanMessage(content=prompt),
            ]
            response = self.llm.invoke(messages)
            return response.content.strip()

        except Exception as e:
            print(f"Gap analysis failed: {e}")
            return self._generate_fallback_analysis(
                candidate.name, matched_must, equivalent_matches, missing_must
            )

    def _generate_fallback_analysis(
        self,
        candidate_name: str,
        matched_must: list[str],
        equivalent_matches: dict,
        missing_must: list[str],
    ) -> str:
        """Generate simple fallback analysis if LLM fails"""
        analysis = f"Skill Analysis for {candidate_name}:\n\n"
        if matched_must:
            analysis += f"✓ Matches {len(matched_must)} critical skills.\n"
        if equivalent_matches:
            analysis += f"✓ Has {len(equivalent_matches)} equivalent skills that transfer well.\n"
        if missing_must:
            analysis += f"✗ Missing {len(missing_must)} must-have skills: {', '.join(missing_must)}.\n"
        return analysis

    def _format_equivalent_matches(self, equivalent_matches: dict) -> str:
        """Format equivalent matches for display"""
        if not equivalent_matches:
            return "None"

        return "\n".join(
            f"- {required} ≈ {info['candidate_skill']} (match: {info['match_score']:.0%})"
            for required, info in equivalent_matches.items()
        )


def skill_matcher_enhanced_node(state: dict) -> dict:
    """LangGraph node: Enhanced skill matching with taxonomy"""
    print("Enhanced Skill Matcher: Semantic matching with taxonomy...\n")

    matcher = EnhancedSkillMatcher()
    job_req = JobRequirements(**state["job_requirements"])

    skill_scores = []
    for candidate_data in state["candidates"]:
        candidate = Candidate(**candidate_data)

        print(f"Analyzing {candidate.name}...")
        skill_score = matcher.match_skills(candidate, job_req)
        skill_scores.append(skill_score.model_dump())

        print(f"    {candidate.name}: {skill_score.overall_skill_score:.1f}% match")

    print("Enhanced skill matching complete\n")

    return {"skill_scores": skill_scores, "current_step": "skill_matching_complete"}
