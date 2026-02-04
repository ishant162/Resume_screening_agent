"""
Enhanced Skill Matcher Node

Uses skill taxonomy for semantic/intelligent matching.
Understands that TensorFlow ≈ PyTorch, React → Vue, etc.
"""

from langchain_core.messages import HumanMessage, SystemMessage

from config.prompts import SEMANTIC_SKILL_MATCH_ANALYSIS_PROMPT
from src.llm.groq_llm import GroqLLM
from src.models import Candidate, JobRequirements, SkillScore
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
        taxonomy_data: dict = None,
    ) -> SkillScore:
        """
        Enhanced skill matching using taxonomy

        Args:
            candidate: Candidate model
            job_requirements: Job requirements model
            taxonomy_data: Pre-computed taxonomy data (optional)

        Returns:
            SkillScore with enhanced matching
        """
        candidate_skills_set = set(skill.lower() for skill in candidate.all_skills)

        must_have_skills = job_requirements.must_have_skills
        nice_to_have_skills = job_requirements.nice_to_have_skills

        # Enhanced matching with taxonomy
        matched_must_have = []
        missing_must_have = []
        equivalent_matches = {}  # Track equivalent skills

        for required_skill in must_have_skills:
            # Check exact match first
            if required_skill.name.lower() in candidate_skills_set:
                matched_must_have.append(required_skill.name)
            else:
                # Check for equivalent/related skills using taxonomy
                match_found = False

                for cand_skill in candidate.technical_skills:
                    enhancement = self.taxonomy.enhance_skill_matching(
                        required_skill.name, [cand_skill]
                    )

                    if enhancement["match_score"] >= 0.7:  # 70% threshold
                        matched_must_have.append(required_skill.name)
                        equivalent_matches[required_skill.name] = {
                            "candidate_skill": cand_skill,
                            "match_score": enhancement["match_score"],
                            "reasoning": enhancement["reasoning"],
                        }
                        match_found = True
                        break

                if not match_found:
                    missing_must_have.append(required_skill.name)

        # Match nice-to-have skills
        matched_nice_to_have = []
        missing_nice_to_have = []

        for required_skill in nice_to_have_skills:
            if required_skill.name.lower() in candidate_skills_set:
                matched_nice_to_have.append(required_skill.name)
            else:
                # Quick taxonomy check
                for cand_skill in candidate.technical_skills:
                    is_equiv, score, _ = self.taxonomy.are_skills_equivalent(
                        required_skill.name, cand_skill, threshold=0.6
                    )
                    if is_equiv:
                        matched_nice_to_have.append(required_skill.name)
                        break
                else:
                    missing_nice_to_have.append(required_skill.name)

        # Find additional skills
        all_required_skill_names = set(
            s.name.lower() for s in job_requirements.technical_skills
        )
        additional_skills = [
            skill
            for skill in candidate.technical_skills
            if skill.lower() not in all_required_skill_names
        ]

        # Calculate match percentages
        must_have_match_pct = (
            (len(matched_must_have) / len(must_have_skills) * 100)
            if must_have_skills
            else 100.0
        )

        nice_to_have_match_pct = (
            (len(matched_nice_to_have) / len(nice_to_have_skills) * 100)
            if nice_to_have_skills
            else 100.0
        )

        # Overall skill score with taxonomy bonus
        base_score = (must_have_match_pct * 0.8) + (nice_to_have_match_pct * 0.2)

        # Bonus for equivalent matches (shows adaptability)
        equiv_bonus = min(5, len(equivalent_matches) * 2)
        overall_score = min(100, base_score + equiv_bonus)

        # Generate enhanced gap analysis
        gap_analysis = self._generate_enhanced_gap_analysis(
            candidate,
            matched_must_have,
            missing_must_have,
            equivalent_matches,
            matched_nice_to_have,
            additional_skills,
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

    def _generate_enhanced_gap_analysis(
        self,
        candidate: Candidate,
        matched_must: list[str],
        missing_must: list[str],
        equivalent_matches: dict,
        matched_nice: list[str],
        additional: list[str],
    ) -> str:
        """Generate enhanced gap analysis mentioning equivalent skills"""

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
            print(f" Enhanced gap analysis failed: {e}")
            # Fallback
            analysis = f"Skill Analysis for {candidate.name}:\n\n"
            if matched_must:
                analysis += f" Matches {len(matched_must)} critical skills.\n"
            if equivalent_matches:
                analysis += f" Has {len(equivalent_matches)} equivalent skills that transfer well.\n"
            if missing_must:
                analysis += f" Missing {len(missing_must)} must-have skills: {', '.join(missing_must)}.\n"
            return analysis

    def _format_equivalent_matches(self, equivalent_matches: dict) -> str:
        """Format equivalent matches for display"""
        if not equivalent_matches:
            return "None"

        lines = []
        for required, match_info in equivalent_matches.items():
            cand_skill = match_info["candidate_skill"]
            score = match_info["match_score"]
            lines.append(f"- {required} ≈ {cand_skill} (match: {score:.0%})")

        return "\n".join(lines)


def skill_matcher_enhanced_node(state: dict) -> dict:
    """
    LangGraph node: Enhanced skill matching with taxonomy
    """
    print(" Enhanced Skill Matcher: Semantic matching with taxonomy...\n")

    matcher = EnhancedSkillMatcher()

    job_req = JobRequirements(**state["job_requirements"])
    taxonomy_data = state.get("skill_taxonomy_data", {})

    skill_scores = []

    for candidate_data in state["candidates"]:
        candidate = Candidate(**candidate_data)

        # Get taxonomy data for this candidate
        candidate_taxonomy = taxonomy_data.get(candidate.name, {})

        print(f"  Analyzing {candidate.name}...")
        skill_score = matcher.match_skills(candidate, job_req, candidate_taxonomy)
        skill_scores.append(skill_score.model_dump())

        print(f" {candidate.name}: {skill_score.overall_skill_score:.1f}% match")

    print(" Enhanced skill matching complete\n")

    return {"skill_scores": skill_scores, "current_step": "skill_matching_complete"}
