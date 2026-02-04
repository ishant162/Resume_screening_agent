"""
Quality Checker Node

Self-reflection mechanism where the agent reviews its own analysis
and decides if re-analysis is needed.

This is what makes the system truly agentic!
"""

import json

from langchain_core.messages import HumanMessage, SystemMessage

from config.prompts import ANALYSIS_QUALITY_ASSURANCE_PROMPT
from src.llm.groq_llm import GroqLLM


class QualityChecker:
    """
    Self-reflection and quality assurance

    The agent reviews its own work and decides:
    - Is the analysis confident and complete?
    - Should any candidates be re-analyzed?
    - Are there inconsistencies or red flags?
    """

    def __init__(self):
        self.llm = GroqLLM().get_llm_model()

        # Quality thresholds
        self.confidence_threshold = 0.7
        self.score_gap_threshold = 25  # Large gaps between candidates

    def check_quality(
        self,
        candidates: list[dict],
        ranked_candidates: list[dict],
        job_requirements: dict,
        reanalysis_count: int = 0
    ) -> dict:
        """
        Perform quality check on analysis results

        Args:
            candidates: Original candidates
            ranked_candidates: Ranked candidates with scores
            job_requirements: Job requirements
            reanalysis_count: How many times we've already re-analyzed

        Returns:
            {
                "confidence": float (0-1),
                "needs_reanalysis": bool,
                "issues": List[str],
                "recommendations": List[str],
                "candidates_to_reanalyze": List[str]
            }
        """
        print("Quality Checker: Agent reviewing its own work...\n")

        issues = []
        recommendations = []
        candidates_to_reanalyze = []

        # Check 1: Data completeness
        completeness_issues = self._check_data_completeness(candidates)
        issues.extend(completeness_issues)

        # Check 2: Scoring consistency
        consistency_issues = self._check_scoring_consistency(ranked_candidates)
        issues.extend(consistency_issues)

        # Check 3: Confidence levels
        confidence_issues = self._check_confidence_levels(ranked_candidates)
        issues.extend(confidence_issues)

        # Check 4: LLM-based self-reflection
        reflection = self._llm_self_reflection(
            candidates,
            ranked_candidates,
            job_requirements,
            issues
        )

        # Aggregate findings
        overall_confidence = reflection.get("overall_confidence", 0.8)
        llm_issues = reflection.get("issues", [])
        llm_recommendations = reflection.get("recommendations", [])

        issues.extend(llm_issues)
        recommendations.extend(llm_recommendations)

        # Determine if reanalysis is needed
        needs_reanalysis = (
            overall_confidence < self.confidence_threshold and
            reanalysis_count < 2  # Maximum 2 reanalysis attempts
        )

        if needs_reanalysis:
            # Identify which candidates need reanalysis
            candidates_to_reanalyze = self._identify_reanalysis_candidates(
                ranked_candidates,
                issues
            )

        # Print quality check results
        print(f"  Overall Confidence: {overall_confidence:.0%}")
        print(f"  Issues Found: {len(issues)}")

        if issues:
            print("Issues:")
            for issue in issues[:3]:
                print(f"    - {issue}")

        if needs_reanalysis:
            print(f"Re-analysis needed for: {', '.join(candidates_to_reanalyze)}")
        else:
            print(" Analysis quality acceptable")

        print()

        return {
            "confidence": round(overall_confidence, 2),
            "needs_reanalysis": needs_reanalysis,
            "issues": issues,
            "recommendations": recommendations,
            "candidates_to_reanalyze": candidates_to_reanalyze
        }

    def _check_data_completeness(self, candidates: list[dict]) -> list[str]:
        """Check if candidate data is complete enough"""
        issues = []

        for candidate in candidates:
            name = candidate.get("name", "Unknown")

            # Check for missing critical data
            if not candidate.get("technical_skills"):
                issues.append(f"{name}: No technical skills found")

            if not candidate.get("work_experience"):
                issues.append(f"{name}: No work experience found")

            if candidate.get("total_experience_months", 0) == 0:
                issues.append(f"{name}: Experience duration not calculated")

        return issues

    def _check_scoring_consistency(self, ranked_candidates: list[dict]) -> list[str]:
        """Check for scoring inconsistencies"""
        issues = []

        if len(ranked_candidates) < 2:
            return issues

        # Extract scores
        scores = []
        for ranked in ranked_candidates:
            cs = ranked.get("candidate_score", {})
            scores.append({
                "name": cs.get("candidate_name", "Unknown"),
                "total": cs.get("total_score", 0),
                "skill": cs.get("skill_score", {}).get("overall_skill_score", 0),
                "experience": cs.get("experience_score", {}).get("experience_match_score", 0),
                "education": cs.get("education_score", {}).get("education_score", 0)
            })

        # Check for large gaps
        for i in range(len(scores) - 1):
            gap = scores[i]["total"] - scores[i+1]["total"]
            if gap > self.score_gap_threshold:
                issues.append(
                    f"Large score gap ({gap:.1f} points) between "
                    f"{scores[i]['name']} and {scores[i+1]['name']}"
                )

        # Check for suspicious perfect scores
        for score in scores:
            if score["total"] >= 98:
                issues.append(
                    f"{score['name']} has suspiciously high score ({score['total']:.1f}%) - "
                    "verify this is accurate"
                )

        # Check for all low scores
        if all(s["total"] < 60 for s in scores):
            issues.append(
                "All candidates scored below 60% - job requirements may be too strict"
            )

        return issues

    def _check_confidence_levels(self, ranked_candidates: list[dict]) -> list[str]:
        """Check confidence levels in recommendations"""
        issues = []

        for ranked in ranked_candidates[:5]:  # Check top 5
            cs = ranked.get("candidate_score", {})
            name = cs.get("candidate_name", "Unknown")
            confidence = cs.get("confidence_level", "High")
            recommendation = cs.get("recommendation", "Unknown")

            # Flag low confidence on top candidates
            if ranked.get("rank", 99) <= 3 and confidence == "Low":
                issues.append(
                    f"Top candidate {name} has low confidence - needs verification"
                )

            # Flag mismatches between score and recommendation
            total_score = cs.get("total_score", 0)
            if total_score >= 85 and recommendation not in ["Strong Match", "Good Match"]:
                issues.append(
                    f"{name}: High score ({total_score:.1f}%) but weak recommendation ({recommendation})"
                )

        return issues

    def _llm_self_reflection(
        self,
        candidates: list[dict],
        ranked_candidates: list[dict],
        job_requirements: dict,
        issues: list[str]
    ) -> dict:
        """
        Use LLM for comprehensive self-reflection

        This is the core of the self-reflection mechanism!
        """

        # Prepare summary
        top_3_summary = []
        for ranked in ranked_candidates[:3]:
            cs = ranked.get("candidate_score", {})
            top_3_summary.append(
                f"#{ranked.get('rank')}: {cs.get('candidate_name')} - "
                f"{cs.get('total_score', 0):.1f}% ({cs.get('recommendation')})"
            )

        current_issues = "\n".join([f"- {issue}" for issue in issues]) if issues else "None detected"

        prompt = ANALYSIS_QUALITY_ASSURANCE_PROMPT.format(
            job_title=job_requirements.get("job_title", "Unknown Position"),
            candidates_screened=len(candidates),
            top_3_summary="\n".join(top_3_summary),
            current_issues=current_issues,
        )

        try:
            messages = [
                SystemMessage(content="You are a quality assurance expert performing self-reflection on analysis results."),
                HumanMessage(content=prompt)
            ]

            response = self.llm.invoke(messages)
            response_text = response.content.strip()

            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]

            reflection = json.loads(response_text.strip())
            return reflection

        except Exception as e:
            print(f"Self-reflection failed: {e}")
            return {
                "overall_confidence": 0.7,
                "issues": [],
                "recommendations": [],
                "assessment": "Unable to perform self-reflection."
            }

    def _identify_reanalysis_candidates(
        self,
        ranked_candidates: list[dict],
        issues: list[str]
    ) -> list[str]:
        """Identify which candidates should be re-analyzed"""

        candidates_to_reanalyze = []

        # Re-analyze candidates mentioned in issues
        for issue in issues:
            for ranked in ranked_candidates[:5]:  # Focus on top 5
                cs = ranked.get("candidate_score", {})
                name = cs.get("candidate_name", "")

                if name in issue:
                    if name not in candidates_to_reanalyze:
                        candidates_to_reanalyze.append(name)

        # If no specific candidates, re-analyze top candidate
        if not candidates_to_reanalyze and ranked_candidates:
            top_candidate = ranked_candidates[0].get("candidate_score", {}).get("candidate_name")
            if top_candidate:
                candidates_to_reanalyze.append(top_candidate)

        return candidates_to_reanalyze[:2]  # Max 2 candidates


def quality_checker_node(state: dict) -> dict:
    """
    LangGraph node: Self-reflection and quality checking

    This enables the agent to review its own work and request re-analysis!
    """
    print("="*80)
    print("QUALITY CHECKER - SELF-REFLECTION")
    print("="*80 + "\n")

    checker = QualityChecker()

    reanalysis_count = state.get("reanalysis_count", 0)

    quality_check = checker.check_quality(
        state["candidates"],
        state["ranked_candidates"],
        state["job_requirements"],
        reanalysis_count
    )

    # Update reanalysis count if we're triggering reanalysis
    new_reanalysis_count = reanalysis_count
    if quality_check["needs_reanalysis"]:
        new_reanalysis_count += 1

    return {
        "quality_check": quality_check,
        "reanalysis_count": new_reanalysis_count,
        "current_step": "quality_check_complete"
    }


# Test
if __name__ == "__main__":
    print("Testing quality checker...")

    # Mock data
    candidates = [
        {"name": "Alice", "technical_skills": ["Python"], "work_experience": [], "total_experience_months": 60}
    ]

    ranked = [
        {
            "rank": 1,
            "candidate_score": {
                "candidate_name": "Alice",
                "total_score": 55.0,
                "confidence_level": "Low",
                "recommendation": "Potential Match",
                "skill_score": {"overall_skill_score": 60},
                "experience_score": {"experience_match_score": 50},
                "education_score": {"education_score": 55}
            }
        }
    ]

    job = {"job_title": "Senior Engineer"}

    checker = QualityChecker()
    result = checker.check_quality(candidates, ranked, job)

    print("\n" + "="*80)
    print("QUALITY CHECK RESULT")
    print("="*80)
    print(f"Confidence: {result['confidence']:.0%}")
    print(f"Needs Reanalysis: {result['needs_reanalysis']}")
    print(f"\nIssues: {len(result['issues'])}")
    for issue in result['issues']:
        print(f"  - {issue}")
