"""
Skill Taxonomy Engine

Provides semantic understanding of skill relationships and equivalencies.
"""

import json

from fuzzywuzzy import fuzz
from langchain_core.messages import HumanMessage, SystemMessage

from src.llm.groq_llm import GroqLLM


class SkillTaxonomy:
    """
    Intelligent skill taxonomy with semantic understanding

    Understands:
    - Skill equivalencies (TensorFlow ≈ PyTorch)
    - Skill hierarchies (Python > Django > REST APIs)
    - Skill adjacencies (React → Vue, AWS → Azure)
    """

    def __init__(self):
        self.llm = GroqLLM().get_llm_model()

        # Pre-defined skill relationships (fast lookup)
        self.equivalencies = {
            "tensorflow": ["pytorch", "keras"],
            "pytorch": ["tensorflow", "keras"],
            "react": ["vue", "angular"],
            "vue": ["react", "angular"],
            "angular": ["react", "vue"],
            "aws": ["azure", "gcp", "google cloud"],
            "azure": ["aws", "gcp"],
            "gcp": ["aws", "azure"],
            "mysql": ["postgresql", "mariadb"],
            "postgresql": ["mysql", "mariadb"],
            "docker": ["kubernetes", "containerization"],
            "kubernetes": ["docker", "k8s"],
        }

        self.hierarchies = {
            "python": ["django", "flask", "fastapi", "pandas", "numpy"],
            "javascript": ["react", "vue", "angular", "node.js", "express"],
            "machine learning": [
                "deep learning",
                "nlp",
                "computer vision",
                "tensorflow",
                "pytorch",
            ],
            "deep learning": ["cnn", "rnn", "lstm", "transformer"],
        }

        self.categories = {
            "ml_frameworks": [
                "tensorflow",
                "pytorch",
                "keras",
                "scikit-learn",
                "xgboost",
            ],
            "web_frameworks": ["react", "angular", "vue", "django", "flask", "spring"],
            "cloud_platforms": ["aws", "azure", "gcp", "google cloud"],
            "databases": ["mysql", "postgresql", "mongodb", "redis", "cassandra"],
            "programming_languages": [
                "python",
                "java",
                "javascript",
                "typescript",
                "go",
                "rust",
            ],
        }

    def are_skills_equivalent(
        self, skill1: str, skill2: str, threshold: float = 0.7
    ) -> tuple[bool, float, str]:
        """
        Check if two skills are equivalent or highly related

        Returns:
            (is_equivalent, similarity_score, reasoning)
        """
        skill1_lower = skill1.lower().strip()
        skill2_lower = skill2.lower().strip()

        # Exact match
        if skill1_lower == skill2_lower:
            return True, 1.0, "Exact match"

        # Check pre-defined equivalencies
        if skill1_lower in self.equivalencies:
            if skill2_lower in self.equivalencies[skill1_lower]:
                return (
                    True,
                    0.9,
                    f"{skill1} and {skill2} are considered equivalent frameworks",
                )

        # Fuzzy string matching
        fuzzy_score = fuzz.ratio(skill1_lower, skill2_lower) / 100.0
        if fuzzy_score >= 0.85:
            return True, fuzzy_score, f"Very similar naming: {skill1} ≈ {skill2}"

        # Check if they're in same category
        for category, skills in self.categories.items():
            if skill1_lower in skills and skill2_lower in skills:
                return True, 0.7, f"Both are {category.replace('_', ' ')}"

        # Use LLM for semantic similarity (slower but more accurate)
        if threshold > 0.6:  # Only use LLM for closer matches
            semantic_result = self._llm_skill_similarity(skill1, skill2)
            if semantic_result["score"] >= threshold:
                return True, semantic_result["score"], semantic_result["reasoning"]

        return False, 0.0, "Not equivalent"

    def find_related_skills(self, skill: str, max_results: int = 5) -> list[dict]:
        """
        Find skills related to the given skill

        Returns:
            [
                {"skill": "PyTorch", "relationship": "equivalent", "score": 0.9},
                ...
            ]
        """
        skill_lower = skill.lower().strip()
        related = []

        # Check equivalencies
        if skill_lower in self.equivalencies:
            for equiv in self.equivalencies[skill_lower]:
                related.append(
                    {"skill": equiv.title(), "relationship": "equivalent", "score": 0.9}
                )

        # Check hierarchies (parent/child)
        for parent, children in self.hierarchies.items():
            if skill_lower == parent:
                for child in children[:max_results]:
                    related.append(
                        {
                            "skill": child.title(),
                            "relationship": "child_skill",
                            "score": 0.7,
                        }
                    )
            elif skill_lower in children:
                related.append(
                    {
                        "skill": parent.title(),
                        "relationship": "parent_skill",
                        "score": 0.7,
                    }
                )

        # Find same-category skills
        for category, skills in self.categories.items():
            if skill_lower in skills:
                for s in skills:
                    if s != skill_lower and len(related) < max_results:
                        related.append(
                            {
                                "skill": s.title(),
                                "relationship": "same_category",
                                "score": 0.6,
                            }
                        )

        return related[:max_results]

    def enhance_skill_matching(
        self, required_skill: str, candidate_skills: list[str]
    ) -> dict:
        """
        Enhanced matching that considers equivalencies and relationships

        Returns:
            {
                "exact_match": bool,
                "equivalent_matches": List[str],
                "related_matches": List[str],
                "match_score": float,
                "reasoning": str
            }
        """
        exact_match = required_skill.lower() in [s.lower() for s in candidate_skills]

        equivalent_matches = []
        related_matches = []

        for cand_skill in candidate_skills:
            is_equiv, score, reasoning = self.are_skills_equivalent(
                required_skill, cand_skill
            )

            if is_equiv and score >= 0.85:
                equivalent_matches.append(cand_skill)
            elif is_equiv and score >= 0.6:
                related_matches.append(cand_skill)

        # Calculate overall match score
        if exact_match:
            match_score = 1.0
            reasoning = f"Candidate has exact skill: {required_skill}"
        elif equivalent_matches:
            match_score = 0.9
            reasoning = (
                f"Candidate has equivalent skill(s): {', '.join(equivalent_matches)}"
            )
        elif related_matches:
            match_score = 0.7
            reasoning = f"Candidate has related skill(s): {', '.join(related_matches)}"
        else:
            match_score = 0.0
            reasoning = f"No match found for {required_skill}"

        return {
            "exact_match": exact_match,
            "equivalent_matches": equivalent_matches,
            "related_matches": related_matches,
            "match_score": match_score,
            "reasoning": reasoning,
        }

    def _llm_skill_similarity(self, skill1: str, skill2: str):
        """Use LLM to assess semantic similarity between skills"""

        prompt = f"""Are these two technical skills equivalent or highly related?

            Skill 1: {skill1}
            Skill 2: {skill2}

            Consider:
            - Are they direct alternatives? (e.g., TensorFlow vs PyTorch)
            - Are they in the same domain? (e.g., React vs Vue - both frontend frameworks)
            - Would experience in one translate to the other?

            Return ONLY a JSON object with no markdown formatting:
            {{
                "score": 0.85,
                "reasoning": "Both are deep learning frameworks with similar capabilities"
            }}

            Score should be 0.0 to 1.0 where 1.0 means completely equivalent.
        """

        try:
            messages = [
                SystemMessage(
                    content="You are an expert at understanding technical skill relationships. Return ONLY valid JSON, no markdown code blocks."
                ),
                HumanMessage(content=prompt),
            ]

            response = self.llm.invoke(messages)
            response_text = response.content.strip()

            # Debug: Print what we got
            # print(f"    DEBUG - Raw response: {response_text[:100]}")

            # Remove any markdown code blocks
            if "```json" in response_text:
                response_text = (
                    response_text.split("```json")[1].split("```")[0].strip()
                )
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            # Remove any leading/trailing whitespace
            response_text = response_text.strip()

            # If response is empty, return default
            if not response_text:
                print(f" Empty LLM response for {skill1} vs {skill2}")
                return {"score": 0.0, "reasoning": "Empty response from LLM"}

            # Try to parse JSON
            result = json.loads(response_text)

            # Validate structure
            if "score" not in result or "reasoning" not in result:
                print(f" Invalid JSON structure for {skill1} vs {skill2}")
                return {"score": 0.0, "reasoning": "Invalid response structure"}

            return result

        except json.JSONDecodeError as e:
            print(f" JSON parse error for {skill1} vs {skill2}: {e}")
            print(
                f"    Response was: {response_text[:200] if 'response_text' in locals() else 'No response'}"
            )
            return {"score": 0.0, "reasoning": "Unable to parse LLM response"}
        except Exception as e:
            print(f" LLM similarity check failed for {skill1} vs {skill2}: {e}")
            return {"score": 0.0, "reasoning": "Unable to assess"}


# Test
if __name__ == "__main__":
    taxonomy = SkillTaxonomy()

    # Test equivalency
    print("\n✅ Skill Equivalency Tests:")

    tests = [
        ("TensorFlow", "PyTorch"),
        ("React", "Vue"),
        ("AWS", "Azure"),
        ("Python", "Java"),  # Should be low
    ]

    for skill1, skill2 in tests:
        is_equiv, score, reasoning = taxonomy.are_skills_equivalent(skill1, skill2)
        print(f"\n{skill1} vs {skill2}:")
        print(f"  Equivalent: {is_equiv}")
        print(f"  Score: {score:.2f}")
        print(f"  Reasoning: {reasoning}")

    # Test related skills
    print("\n\n✅ Related Skills:")
    related = taxonomy.find_related_skills("TensorFlow")
    for r in related:
        print(f"  - {r['skill']} ({r['relationship']}, score: {r['score']})")
