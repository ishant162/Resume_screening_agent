from enum import Enum

from pydantic import BaseModel, Field


class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class SkillPriority(str, Enum):
    MUST_HAVE = "must_have"
    NICE_TO_HAVE = "nice_to_have"
    PREFERRED = "preferred"


class Skill(BaseModel):
    """Required skill with metadata"""

    name: str
    level: SkillLevel | None = None
    priority: SkillPriority = SkillPriority.MUST_HAVE
    years_required: int | None = None
    # Similar/acceptable skills
    alternatives: list[str] = Field(default_factory=list)

    def matches(self, candidate_skill: str) -> bool:
        """Check if candidate skill matches this requirement"""
        candidate_skill_lower = candidate_skill.lower()
        name_lower = self.name.lower()

        # Direct match
        if candidate_skill_lower == name_lower:
            return True

        # Alternative match
        return any(alt.lower() == candidate_skill_lower for alt in self.alternatives)


class ExperienceRequirement(BaseModel):
    """Experience requirements"""

    minimum_years: int | None = None
    maximum_years: int | None = None
    preferred_years: int | None = None
    specific_domains: list[str] = Field(default_factory=list)
    # e.g., "Software Engineer", "Data Scientist"
    role_types: list[str] = Field(default_factory=list)


class EducationRequirement(BaseModel):
    """Education requirements"""

    minimum_degree: str  # e.g., "Bachelor", "Master"
    preferred_degree: str | None = None
    fields_of_study: list[str] = Field(default_factory=list)
    required: bool = True


class JobRequirements(BaseModel):
    """Complete job requirements extracted from JD"""

    # Basic Info
    job_title: str
    department: str | None = None
    location: str | None = None
    job_type: str | None = None  # Full-time, Contract, etc.

    # Description
    job_description: str
    responsibilities: list[str] = Field(default_factory=list)

    # Requirements
    technical_skills: list[Skill] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    tools_and_technologies: list[str] = Field(default_factory=list)

    experience: ExperienceRequirement
    education: EducationRequirement

    certifications: list[str] = Field(default_factory=list)

    # Nice to have
    preferred_qualifications: list[str] = Field(default_factory=list)

    # Company info
    company_name: str | None = None
    company_description: str | None = None

    # Metadata
    source_file: str | None = None

    @property
    def must_have_skills(self) -> list[Skill]:
        """Get only must-have skills"""
        return [
            s for s in self.technical_skills if s.priority == SkillPriority.MUST_HAVE
        ]

    @property
    def nice_to_have_skills(self) -> list[Skill]:
        """Get nice-to-have skills"""
        return [
            s for s in self.technical_skills if s.priority == SkillPriority.NICE_TO_HAVE
        ]

    @property
    def all_required_skill_names(self) -> list[str]:
        """Get list of all skill names"""
        return [skill.name for skill in self.technical_skills]
