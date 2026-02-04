"""
ATS (Applicant Tracking System) Scorer

Scores how well a resume will perform in ATS systems.
"""

import re


class ATSScorer:
    """
    Score resume ATS-friendliness

    Checks:
    - Keyword density
    - Format compatibility
    - Section organization
    - Contact information
    - File structure
    """

    def __init__(self):
        self.required_sections = [
            "experience",
            "education",
            "skills",
            "work",
            "employment",
            "technical",
        ]

        self.bonus_sections = [
            "summary",
            "objective",
            "projects",
            "certifications",
            "achievements",
        ]

    def score_resume(
        self, resume_text: str, candidate_profile: dict, job_requirements: dict
    ) -> dict:
        """
        Score resume for ATS compatibility

        Returns:
            {
                "overall_score": float (0-100),
                "category_scores": {
                    "keyword_optimization": float,
                    "format_compatibility": float,
                    "section_organization": float,
                    "contact_information": float,
                    "content_density": float
                },
                "strengths": List[str],
                "improvements": List[str],
                "ats_readiness": str  # "Excellent", "Good", "Fair", "Poor"
            }
        """
        print(
            f"    📋 Scoring ATS compatibility for {candidate_profile.get('name', 'candidate')}..."
        )

        scores = {}
        strengths = []
        improvements = []

        # 1. Keyword Optimization (30 points)
        keyword_score = self._score_keywords(
            resume_text, candidate_profile, job_requirements
        )
        scores["keyword_optimization"] = keyword_score

        if keyword_score >= 25:
            strengths.append("Strong keyword optimization for ATS parsing")
        elif keyword_score < 15:
            improvements.append("Add more relevant keywords from job description")

        # 2. Format Compatibility (25 points)
        format_score = self._score_format(resume_text)
        scores["format_compatibility"] = format_score

        if format_score >= 20:
            strengths.append("Clean, ATS-friendly format")
        else:
            improvements.append(
                "Simplify formatting - avoid tables, images, and complex layouts"
            )

        # 3. Section Organization (20 points)
        section_score = self._score_sections(resume_text)
        scores["section_organization"] = section_score

        if section_score >= 16:
            strengths.append("Well-organized with clear sections")
        else:
            improvements.append(
                "Add clear section headers (Experience, Education, Skills)"
            )

        # 4. Contact Information (15 points)
        contact_score = self._score_contact_info(candidate_profile)
        scores["contact_information"] = contact_score

        if contact_score >= 12:
            strengths.append("Complete contact information")
        else:
            improvements.append("Include email, phone, and LinkedIn URL")

        # 5. Content Density (10 points)
        density_score = self._score_content_density(resume_text, candidate_profile)
        scores["content_density"] = density_score

        if density_score >= 8:
            strengths.append("Appropriate content density")
        elif density_score < 5:
            improvements.append(
                "Resume may be too sparse - add more detail about accomplishments"
            )

        # Calculate overall score
        overall_score = sum(scores.values())

        # Determine readiness level
        if overall_score >= 85:
            readiness = "Excellent"
        elif overall_score >= 70:
            readiness = "Good"
        elif overall_score >= 55:
            readiness = "Fair"
        else:
            readiness = "Poor"

        return {
            "overall_score": round(overall_score, 1),
            "category_scores": {k: round(v, 1) for k, v in scores.items()},
            "strengths": strengths,
            "improvements": improvements,
            "ats_readiness": readiness,
        }

    def _score_keywords(
        self, resume_text: str, candidate_profile: dict, job_requirements: dict
    ) -> float:
        """
        Score keyword optimization (max 30 points)

        Checks how many required skills/keywords appear in resume
        """
        if not resume_text:
            return 0.0

        resume_lower = resume_text.lower()

        # Get required keywords
        required_skills = []
        if job_requirements.get("technical_skills"):
            for skill in job_requirements["technical_skills"]:
                if isinstance(skill, dict):
                    required_skills.append(skill.get("name", ""))
                else:
                    required_skills.append(skill)

        if not required_skills:
            return 20.0  # No requirements to check against

        # Count matches
        matches = 0
        for skill in required_skills:
            if skill.lower() in resume_lower:
                matches += 1

        # Calculate score
        match_ratio = matches / len(required_skills)
        keyword_score = match_ratio * 30

        return keyword_score

    def _score_format(self, resume_text: str) -> float:
        """
        Score format compatibility (max 25 points)

        ATS-friendly formats:
        - Plain text readable
        - No complex tables
        - Standard fonts
        - Clear hierarchy
        """
        score = 25.0  # Start with perfect score, deduct for issues

        if not resume_text:
            return 0.0

        # Check for problematic patterns
        # (Note: We're working with extracted text, so some checks are limited)

        # Check for excessive special characters (indicates complex formatting)
        special_char_ratio = len(re.findall(r"[^\w\s.,;:()\-]", resume_text)) / len(
            resume_text
        )
        if special_char_ratio > 0.05:
            score -= 5

        # Check for proper line breaks (indicates structure)
        lines = resume_text.split("\n")
        if len(lines) < 20:  # Too few lines might indicate poor structure
            score -= 5

        # Check for bullet points (good for ATS)
        bullet_indicators = ["•", "●", "◦", "-", "*"]
        has_bullets = any(indicator in resume_text for indicator in bullet_indicators)
        if not has_bullets:
            score -= 3

        return max(0, score)

    def _score_sections(self, resume_text: str) -> float:
        """
        Score section organization (max 20 points)

        ATS looks for standard sections
        """
        if not resume_text:
            return 0.0

        resume_lower = resume_text.lower()
        score = 0.0

        # Check for required sections (4 points each)
        found_sections = []
        for section in self.required_sections:
            if section in resume_lower:
                found_sections.append(section)
                score += 4

        # Bonus for additional sections (2 points each, max 8)
        bonus = 0
        for section in self.bonus_sections:
            if section in resume_lower and bonus < 8:
                bonus += 2

        score += bonus

        return min(20, score)

    def _score_contact_info(self, candidate_profile: dict) -> float:
        """
        Score contact information completeness (max 15 points)
        """
        score = 0.0

        # Email (5 points)
        if candidate_profile.get("email"):
            score += 5

        # Phone (5 points)
        if candidate_profile.get("phone"):
            score += 5

        # LinkedIn or GitHub (5 points)
        if candidate_profile.get("linkedin_url") or candidate_profile.get("github_url"):
            score += 5

        return score

    def _score_content_density(
        self, resume_text: str, candidate_profile: dict
    ) -> float:
        """
        Score content density (max 10 points)

        Checks if resume has sufficient detail
        """
        if not resume_text:
            return 0.0

        score = 10.0

        # Check word count
        word_count = len(resume_text.split())
        if word_count < 200:
            score -= 5  # Too sparse
        elif word_count > 1500:
            score -= 2  # Might be too verbose

        # Check if work experience has details
        work_exp = candidate_profile.get("work_experience", [])
        if work_exp:
            total_responsibilities = sum(
                len(exp.get("responsibilities", [])) for exp in work_exp
            )
            if (
                total_responsibilities < len(work_exp) * 2
            ):  # At least 2 responsibilities per job
                score -= 3

        return max(0, score)


# Test
if __name__ == "__main__":
    scorer = ATSScorer()

    # Mock resume text
    resume_text = """
        John Doe
        john.doe@email.com | (555) 123-4567 | linkedin.com/in/johndoe

        SUMMARY
        Experienced Software Engineer with 5 years in machine learning and AI.

        EXPERIENCE
        Senior ML Engineer - Tech Corp (2020-Present)
        - Built recommendation systems using TensorFlow and Python
        - Deployed models to AWS infrastructure
        - Mentored 3 junior engineers

        ML Engineer - Startup Inc (2018-2020)
        - Developed NLP pipelines
        - Implemented deep learning models

        EDUCATION
        B.S. Computer Science - MIT (2018)

        SKILLS
        Python, TensorFlow, PyTorch, AWS, Docker, Kubernetes
    """

    candidate = {
        "name": "John Doe",
        "email": "john.doe@email.com",
        "phone": "(555) 123-4567",
        "linkedin_url": "linkedin.com/in/johndoe",
        "work_experience": [
            {
                "company": "Tech Corp",
                "responsibilities": [
                    "Built systems",
                    "Deployed models",
                    "Mentored engineers",
                ],
            }
        ],
    }

    job = {
        "technical_skills": [
            {"name": "Python"},
            {"name": "TensorFlow"},
            {"name": "AWS"},
            {"name": "Docker"},
        ]
    }

    result = scorer.score_resume(resume_text, candidate, job)

    print("\n" + "=" * 80)
    print("📋 ATS COMPATIBILITY SCORE")
    print("=" * 80)
    print(f"\nOverall Score: {result['overall_score']:.1f}/100")
    print(f"ATS Readiness: {result['ats_readiness']}")

    print("\nCategory Scores:")
    for category, score in result["category_scores"].items():
        print(f"  {category.replace('_', ' ').title()}: {score:.1f}")

    print("\n✅ Strengths:")
    for strength in result["strengths"]:
        print("  • {strength}")

    print("\n⚠️ Improvements:")
    for improvement in result["improvements"]:
        print(f"  • {improvement}")

    print("\n" + "=" * 80)
