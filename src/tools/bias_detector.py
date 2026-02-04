"""
Bias Detector Tool

Detects potential biases in hiring process to ensure fair evaluation.
"""

import json

from langchain_core.messages import HumanMessage, SystemMessage

from config.prompts import HIRING_BIAS_ANALYSIS_PROMPT
from src.llm.groq_llm import GroqLLM


class BiasDetector:
    """
    Detect potential biases in candidate screening

    Checks for:
    - Gender bias
    - Age discrimination
    - University prestige bias
    - Name-based bias
    - Geographic bias
    - Unconscious bias patterns
    """

    def __init__(self):
        self.llm = GroqLLM().get_llm_model()

        # Bias indicators
        self.name_patterns = {
            "gender_indicators": [
                "strong",
                "aggressive",
                "ambitious",  # Often associated with male
                "supportive",
                "collaborative",
                "nurturing",  # Often associated with female
            ],
            "age_indicators": [
                "digital native",
                "recent graduate",
                "energetic",
                "experienced",
                "seasoned",
                "mature",
            ],
        }

        self.elite_universities = [
            "harvard",
            "stanford",
            "mit",
            "yale",
            "princeton",
            "oxford",
            "cambridge",
            "berkeley",
            "caltech",
        ]

    def analyze_bias(
        self,
        candidates: list[dict],
        ranked_candidates: list[dict],
        job_requirements: dict,
    ) -> dict:
        """
        Analyze potential biases in screening results

        Args:
            candidates: List of all candidates
            ranked_candidates: Ranked candidates with scores
            job_requirements: Job requirements

        Returns:
            {
                "bias_score": float (0-100, lower is better),
                "detected_biases": List[Dict],
                "fairness_assessment": str,
                "recommendations": List[str]
            }
        """
        print("    ⚖️  Analyzing for potential hiring biases...")

        detected_biases = []

        # 1. University prestige bias
        university_bias = self._check_university_bias(candidates, ranked_candidates)
        if university_bias["detected"]:
            detected_biases.append(university_bias)

        # 2. Experience requirements bias
        experience_bias = self._check_experience_bias(
            candidates, ranked_candidates, job_requirements
        )
        if experience_bias["detected"]:
            detected_biases.append(experience_bias)

        # 3. Language/description bias in job posting
        language_bias = self._check_language_bias(job_requirements)
        if language_bias["detected"]:
            detected_biases.append(language_bias)

        # 4. Scoring consistency
        scoring_bias = self._check_scoring_consistency(ranked_candidates)
        if scoring_bias["detected"]:
            detected_biases.append(scoring_bias)

        # 5. LLM-based bias detection (comprehensive)
        llm_bias = self._llm_bias_analysis(
            candidates, ranked_candidates, job_requirements
        )
        if llm_bias.get("detected_biases"):
            detected_biases.extend(llm_bias["detected_biases"])

        # Calculate bias score (inverse - lower is better)
        bias_score = self._calculate_bias_score(detected_biases)

        # Generate recommendations
        recommendations = self._generate_recommendations(detected_biases)

        # Fairness assessment
        if bias_score <= 20:
            fairness = "Excellent - No significant biases detected"
        elif bias_score <= 40:
            fairness = "Good - Minor biases to be aware of"
        elif bias_score <= 60:
            fairness = "Fair - Some biases require attention"
        else:
            fairness = "Poor - Significant biases detected, review process"

        return {
            "bias_score": round(bias_score, 1),
            "detected_biases": detected_biases,
            "fairness_assessment": fairness,
            "recommendations": recommendations,
        }

    def _check_university_bias(
        self, candidates: list[dict], ranked_candidates: list[dict]
    ) -> dict:
        """Check if top candidates are disproportionately from elite universities"""

        # Get universities for all candidates
        all_universities = []
        for candidate in candidates:
            education = candidate.get("education", [])
            for edu in education:
                if isinstance(edu, dict):
                    all_universities.append(edu.get("institution", "").lower())

        # Get universities for top 3 candidates
        top_universities = []
        for i, ranked in enumerate(ranked_candidates[:3]):
            candidate_score = ranked.get("candidate_score", {})
            candidate_name = candidate_score.get("candidate_name", "")

            # Find matching candidate
            for candidate in candidates:
                if candidate.get("name") == candidate_name:
                    education = candidate.get("education", [])
                    for edu in education:
                        if isinstance(edu, dict):
                            top_universities.append(edu.get("institution", "").lower())

        # Check for elite university concentration
        elite_in_all = sum(
            1
            for uni in all_universities
            if any(elite in uni for elite in self.elite_universities)
        )
        elite_in_top = sum(
            1
            for uni in top_universities
            if any(elite in uni for elite in self.elite_universities)
        )

        if len(top_universities) > 0:
            top_elite_ratio = elite_in_top / len(top_universities)
        else:
            top_elite_ratio = 0

        if len(all_universities) > 0:
            all_elite_ratio = elite_in_all / len(all_universities)
        else:
            all_elite_ratio = 0

        # Flag if top candidates have disproportionately more elite universities
        detected = top_elite_ratio > all_elite_ratio * 1.5 and elite_in_top > 0

        return {
            "type": "University Prestige Bias",
            "detected": detected,
            "severity": "Medium" if detected else "None",
            "description": f"Top candidates include {elite_in_top}/{len(top_universities)} from elite universities vs {elite_in_all}/{len(all_universities)} overall"
            if detected
            else "",
            "recommendation": "Consider candidates from diverse educational backgrounds"
            if detected
            else "",
        }

    def _check_experience_bias(
        self,
        candidates: list[dict],
        ranked_candidates: list[dict],
        job_requirements: dict,
    ) -> dict:
        """Check if experience requirements are overly strict"""

        required_years = job_requirements.get("experience", {}).get("minimum_years", 0)

        if required_years == 0:
            return {"detected": False}

        # Check if anyone under requirement made it to top 3
        top_3_candidates = []
        for ranked in ranked_candidates[:3]:
            candidate_name = ranked.get("candidate_score", {}).get("candidate_name")
            for candidate in candidates:
                if candidate.get("name") == candidate_name:
                    top_3_candidates.append(candidate)

        under_requirement = [
            c
            for c in top_3_candidates
            if c.get("total_experience_months", 0) / 12 < required_years
        ]

        # If requiring senior experience but excluding good junior candidates
        detected = (
            required_years >= 7
            and len(under_requirement) == 0
            and len(candidates) > len(ranked_candidates)
        )

        return {
            "type": "Experience Requirements Bias",
            "detected": detected,
            "severity": "Low" if detected else "None",
            "description": f"Strict {required_years}+ years requirement may exclude qualified candidates"
            if detected
            else "",
            "recommendation": "Consider candidates slightly below experience threshold if skills are strong"
            if detected
            else "",
        }

    def _check_language_bias(self, job_requirements: dict) -> dict:
        """Check job description for biased language"""

        description = job_requirements.get("job_description", "").lower()

        # Gendered language
        masculine_words = ["aggressive", "competitive", "dominant", "ambitious"]

        masculine_count = sum(1 for word in masculine_words if word in description)

        # Age-biased language
        age_bias_words = ["digital native", "energetic", "recent graduate", "young"]
        age_bias_count = sum(1 for word in age_bias_words if word in description)

        detected = masculine_count >= 2 or age_bias_count >= 1

        bias_type = []
        if masculine_count >= 2:
            bias_type.append("gender-biased language")
        if age_bias_count >= 1:
            bias_type.append("age-biased language")

        return {
            "type": "Job Description Language Bias",
            "detected": detected,
            "severity": "Medium" if detected else "None",
            "description": f"Job description contains {', '.join(bias_type)}"
            if detected
            else "",
            "recommendation": "Use gender-neutral and age-neutral language in job postings"
            if detected
            else "",
        }

    def _check_scoring_consistency(self, ranked_candidates: list[dict]) -> dict:
        """Check if scoring is consistent across candidates"""

        if len(ranked_candidates) < 2:
            return {"detected": False}

        # Get scores
        scores = []
        for ranked in ranked_candidates:
            candidate_score = ranked.get("candidate_score", {})
            scores.append(candidate_score.get("total_score", 0))

        # Check for suspiciously large gaps
        if len(scores) >= 2:
            max_gap = max(scores[i] - scores[i + 1] for i in range(len(scores) - 1))

            # Flag if there's a >30 point gap between adjacent candidates
            detected = max_gap > 30

            return {
                "type": "Scoring Consistency",
                "detected": detected,
                "severity": "Low" if detected else "None",
                "description": f"Large scoring gap ({max_gap:.1f} points) between candidates"
                if detected
                else "",
                "recommendation": "Review scoring criteria for consistency"
                if detected
                else "",
            }

        return {"detected": False}

    def _llm_bias_analysis(
        self,
        candidates: list[dict],
        ranked_candidates: list[dict],
        job_requirements: dict,
    ) -> dict:
        """Use LLM to detect subtle biases"""

        # Prepare candidate summary
        top_3_summary = []
        for ranked in ranked_candidates[:3]:
            cs = ranked.get("candidate_score", {})
            name = cs.get("candidate_name", "Unknown")
            score = cs.get("total_score", 0)
            rec = cs.get("recommendation", "Unknown")

            # Find candidate details
            candidate = next((c for c in candidates if c.get("name") == name), {})
            education = candidate.get("education", [])
            edu_str = (
                education[0].get("institution", "Unknown") if education else "Unknown"
            )

            top_3_summary.append(
                f"#{ranked.get('rank')}: {name} - Score: {score:.1f}, Rec: {rec}, Education: {edu_str}"
            )

        prompt = HIRING_BIAS_ANALYSIS_PROMPT.format(
            job_title=job_requirements.get("job_title", "Unknown"),
            top_3_summary="\n".join(top_3_summary),
            total_candidates=len(candidates),
        )

        try:
            messages = [
                SystemMessage(
                    content="You are an expert in detecting unconscious bias in hiring."
                ),
                HumanMessage(content=prompt),
            ]

            response = self.llm.invoke(messages)
            response_text = response.content.strip()

            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]

            result = json.loads(response_text.strip())
            return result

        except Exception as e:
            print(f"      ⚠️  LLM bias analysis failed: {e}")
            return {"detected_biases": []}

    def _calculate_bias_score(self, detected_biases: list[dict]) -> float:
        """Calculate overall bias score (0-100, lower is better)"""

        if not detected_biases:
            return 0.0

        severity_scores = {"Low": 15, "Medium": 30, "High": 50}

        total = sum(
            severity_scores.get(bias.get("severity", "Low"), 15)
            for bias in detected_biases
        )

        return min(100, total)

    def _generate_recommendations(self, detected_biases: list[dict]) -> list[str]:
        """Generate actionable recommendations"""

        recommendations = []

        for bias in detected_biases:
            if bias.get("recommendation"):
                recommendations.append(bias["recommendation"])

        # Always add general recommendation
        if detected_biases:
            recommendations.append(
                "Review screening criteria to ensure fairness and objectivity"
            )
            recommendations.append(
                "Consider blind screening (removing names/universities) for initial review"
            )
        else:
            recommendations.append(
                "Continue current screening practices - no significant biases detected"
            )

        return list(set(recommendations))  # Remove duplicates


# Test
if __name__ == "__main__":
    detector = BiasDetector()

    # Mock data
    candidates = [
        {
            "name": "Alice Johnson",
            "total_experience_months": 72,
            "education": [{"institution": "MIT", "degree": "BS"}],
        },
        {
            "name": "Bob Smith",
            "total_experience_months": 48,
            "education": [{"institution": "State University", "degree": "BS"}],
        },
        {
            "name": "Carol Williams",
            "total_experience_months": 60,
            "education": [{"institution": "Harvard", "degree": "MS"}],
        },
    ]

    ranked = [
        {
            "rank": 1,
            "candidate_score": {
                "candidate_name": "Alice Johnson",
                "total_score": 92.0,
                "recommendation": "Strong Match",
            },
        },
        {
            "rank": 2,
            "candidate_score": {
                "candidate_name": "Carol Williams",
                "total_score": 88.0,
                "recommendation": "Strong Match",
            },
        },
        {
            "rank": 3,
            "candidate_score": {
                "candidate_name": "Bob Smith",
                "total_score": 75.0,
                "recommendation": "Good Match",
            },
        },
    ]

    job = {
        "job_title": "Senior Engineer",
        "job_description": "Looking for aggressive, competitive engineer",
        "experience": {"minimum_years": 5},
    }

    result = detector.analyze_bias(candidates, ranked, job)

    print("\n" + "=" * 80)
    print("⚖️  BIAS ANALYSIS")
    print("=" * 80)
    print(f"\nBias Score: {result['bias_score']:.1f}/100 (lower is better)")
    print(f"Fairness Assessment: {result['fairness_assessment']}")

    if result["detected_biases"]:
        print("\n🚩 Detected Biases:")
        for bias in result["detected_biases"]:
            print(f"\n  Type: {bias['type']}")
            print(f"  Severity: {bias['severity']}")
            print(f"  Description: {bias['description']}")

    print("\n💡 Recommendations:")
    for rec in result["recommendations"]:
        print(f"  • {rec}")

    print("\n" + "=" * 80)
