"""
Salary Estimator Tool

Estimates fair compensation based on skills, experience, location, and market data.
"""

import json

from langchain_core.messages import HumanMessage, SystemMessage

from config.prompts import (
    SALARY_ESTIMATE_EXPLANATION_PROMPT,
    SALARY_PREMIUM_SKILL_ANALYSIS_PROMPT,
)
from src.llm.groq_llm import GroqLLM


class SalaryEstimator:
    """
    Estimate salary ranges based on candidate profile

    Uses LLM reasoning + market knowledge to provide compensation estimates
    """

    def __init__(self):
        self.llm = GroqLLM().get_llm_model()

        # Base salary data (can be enhanced with real API data)
        self.base_salaries = {
            "Junior": {"min": 60000, "max": 85000, "median": 72000},
            "Mid-Level": {"min": 85000, "max": 120000, "median": 100000},
            "Senior": {"min": 120000, "max": 180000, "median": 145000},
            "Lead/Principal": {"min": 160000, "max": 250000, "median": 195000},
        }

        # Location multipliers (US-centric, can be expanded)
        self.location_multipliers = {
            "San Francisco": 1.4,
            "New York": 1.3,
            "Seattle": 1.25,
            "Austin": 1.1,
            "Boston": 1.2,
            "Remote": 1.0,
            "Default": 1.0,
        }

        # Industry multipliers
        self.industry_multipliers = {
            "fintech": 1.2,
            "enterprise": 1.1,
            "startup": 0.9,
            "healthcare": 1.0,
            "ecommerce": 1.0,
            "ai/ml": 1.15,
            "default": 1.0,
        }

    def estimate_salary(self, candidate_profile: dict, job_requirements: dict) -> dict:
        """
        Estimate salary range for a candidate

        Args:
            candidate_profile: Candidate data including skills, experience, education
            job_requirements: Job requirements including title, industry

        Returns:
            {
                "base_range": {"min": int, "max": int, "median": int},
                "adjusted_range": {"min": int, "max": int, "median": int},
                "factors": {
                    "experience_level": str,
                    "location_multiplier": float,
                    "industry_multiplier": float,
                    "skills_premium": float
                },
                "reasoning": str,
                "confidence": float
            }
        """
        print(
            f"    💰 Estimating salary for {candidate_profile.get('name', 'candidate')}..."
        )

        # Determine experience level
        experience_level = self._determine_experience_level(
            candidate_profile.get("total_experience_years", 0),
            job_requirements.get("job_title", ""),
        )

        # Get base salary range
        base_range = self.base_salaries.get(
            experience_level, self.base_salaries["Mid-Level"]
        )

        # Calculate multipliers
        location = candidate_profile.get("location", "Remote")
        location_mult = self._get_location_multiplier(location)

        industry = self._extract_industry(job_requirements)
        industry_mult = self.industry_multipliers.get(industry, 1.0)

        # Skills premium (LLM-based)
        skills_analysis = self._analyze_skills_premium(
            candidate_profile.get("technical_skills", []), job_requirements
        )
        skills_premium = skills_analysis["premium"]

        # Calculate adjusted range
        total_multiplier = location_mult * industry_mult * (1 + skills_premium)

        adjusted_range = {
            "min": int(base_range["min"] * total_multiplier),
            "max": int(base_range["max"] * total_multiplier),
            "median": int(base_range["median"] * total_multiplier),
        }

        # Generate reasoning using LLM
        reasoning = self._generate_salary_reasoning(
            candidate_profile,
            job_requirements,
            experience_level,
            adjusted_range,
            {
                "location": location_mult,
                "industry": industry_mult,
                "skills": skills_premium,
            },
        )

        # Confidence based on data completeness
        confidence = self._calculate_confidence(candidate_profile)

        return {
            "base_range": base_range,
            "adjusted_range": adjusted_range,
            "factors": {
                "experience_level": experience_level,
                "location_multiplier": location_mult,
                "industry_multiplier": industry_mult,
                "skills_premium": skills_premium,
            },
            "reasoning": reasoning,
            "confidence": confidence,
        }

    def _determine_experience_level(self, years: float, job_title: str) -> str:
        """Determine experience level"""
        title_lower = job_title.lower()

        # Title-based classification
        if any(word in title_lower for word in ["lead", "principal", "staff"]):
            return "Lead/Principal"
        elif any(word in title_lower for word in ["senior", "sr"]):
            return "Senior"
        elif any(word in title_lower for word in ["junior", "jr", "entry"]):
            return "Junior"

        # Years-based classification
        if years < 2:
            return "Junior"
        elif years < 5:
            return "Mid-Level"
        elif years < 8:
            return "Senior"
        else:
            return "Lead/Principal"

    def _get_location_multiplier(self, location: str) -> float:
        """Get location-based salary multiplier"""
        if not location:
            return 1.0

        location_lower = location.lower()

        for city, multiplier in self.location_multipliers.items():
            if city.lower() in location_lower:
                return multiplier

        return 1.0

    def _extract_industry(self, job_requirements: dict) -> str:
        """Extract industry from job requirements"""
        description = job_requirements.get("job_description", "").lower()

        for industry, keywords in {
            "fintech": ["finance", "banking", "fintech"],
            "healthcare": ["health", "medical", "clinical"],
            "ai/ml": ["ai", "machine learning", "ml", "artificial intelligence"],
            "startup": ["startup", "early stage"],
        }.items():
            if any(kw in description for kw in keywords):
                return industry

        return "default"

    def _analyze_skills_premium(
        self, candidate_skills: list[str], job_requirements: dict
    ) -> dict:
        """
        Use LLM to assess if candidate has premium/rare skills

        Returns skills premium as a multiplier (0.0 to 0.3)
        """
        if not candidate_skills:
            return {"premium": 0.0, "reasoning": "No skills data"}

        prompt = SALARY_PREMIUM_SKILL_ANALYSIS_PROMPT.format(
            candidate_skills=", ".join(candidate_skills[:20]),
            job_title=job_requirements.get("job_title", "Technical Role"),
        )

        try:
            messages = [
                SystemMessage(
                    content="You are a compensation analyst assessing skill premiums."
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
            print(f"      ⚠️  Skills premium analysis failed: {e}")
            return {"premium": 0.0, "reasoning": "Unable to assess"}

    def _generate_salary_reasoning(
        self,
        candidate_profile: dict,
        job_requirements: dict,
        experience_level: str,
        adjusted_range: dict,
        multipliers: dict,
    ) -> str:
        """Generate explanation for salary estimate using LLM"""

        prompt = SALARY_ESTIMATE_EXPLANATION_PROMPT.format(
            candidate_name=candidate_profile.get("name", "Candidate"),
            job_title=job_requirements.get("job_title", "Role"),
            experience_level=experience_level,
            years_of_experience=candidate_profile.get(
                "total_experience_years", "Unknown"
            ),
            location=candidate_profile.get("location", "Not specified"),
            salary_min=f"{adjusted_range['min']:,}",
            salary_max=f"{adjusted_range['max']:,}",
            salary_median=f"{adjusted_range['median']:,}",
            location_multiplier=f"{multipliers['location']:.2f}",
            industry_multiplier=f"{multipliers['industry']:.2f}",
            skills_premium=f"{multipliers['skills'] * 100:.0f}",
        )

        try:
            messages = [
                SystemMessage(
                    content="You are a compensation analyst explaining salary estimates."
                ),
                HumanMessage(content=prompt),
            ]

            response = self.llm.invoke(messages)
            return response.content.strip()

        except Exception as e:
            print(f"      ⚠️  Salary reasoning generation failed: {e}")
            return f"Estimated salary range of ${adjusted_range['min']:,} - ${adjusted_range['max']:,} based on {experience_level} level with {candidate_profile.get('total_experience_years', 0)} years experience."

    def _calculate_confidence(self, candidate_profile: dict) -> float:
        """Calculate confidence in salary estimate"""
        confidence = 1.0

        # Reduce confidence for missing data
        if not candidate_profile.get("total_experience_years"):
            confidence -= 0.2

        if not candidate_profile.get("technical_skills"):
            confidence -= 0.2

        if not candidate_profile.get("location"):
            confidence -= 0.1

        if not candidate_profile.get("education"):
            confidence -= 0.1

        return max(0.4, confidence)  # Minimum 40% confidence


# Test
if __name__ == "__main__":
    estimator = SalaryEstimator()

    # Mock candidate
    candidate = {
        "name": "Jane Doe",
        "total_experience_years": 6,
        "technical_skills": ["Python", "TensorFlow", "PyTorch", "AWS", "Docker"],
        "location": "San Francisco, CA",
        "education": [{"degree": "Master of Science"}],
    }

    # Mock job
    job = {
        "job_title": "Senior ML Engineer",
        "job_description": "Build AI/ML systems for fintech",
    }

    result = estimator.estimate_salary(candidate, job)

    print("\n" + "=" * 80)
    print("💰 SALARY ESTIMATE")
    print("=" * 80)
    print(f"\nCandidate: {candidate['name']}")
    print(f"Experience Level: {result['factors']['experience_level']}")
    print(
        f"\nBase Range: ${result['base_range']['min']:,} - ${result['base_range']['max']:,}"
    )
    print(
        f"Adjusted Range: ${result['adjusted_range']['min']:,} - ${result['adjusted_range']['max']:,}"
    )
    print(f"Median Estimate: ${result['adjusted_range']['median']:,}")
    print("\nFactors:")
    print(f"  Location: {result['factors']['location_multiplier']:.2f}x")
    print(f"  Industry: {result['factors']['industry_multiplier']:.2f}x")
    print(f"  Skills Premium: +{result['factors']['skills_premium'] * 100:.0f}%")
    print(f"\nConfidence: {result['confidence'] * 100:.0f}%")
    print(f"\nReasoning:\n{result['reasoning']}")
    print("\n" + "=" * 80)
