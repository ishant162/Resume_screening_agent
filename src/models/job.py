from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


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
    level: Optional[SkillLevel] = None
    priority: SkillPriority = SkillPriority.MUST_HAVE
    years_required: Optional[int] = None
    # Similar/acceptable skills
    alternatives: List[str] = Field(default_factory=list)

    def matches(self, candidate_skill: str) -> bool:
        """Check if candidate skill matches this requirement"""
        candidate_skill_lower = candidate_skill.lower()
        name_lower = self.name.lower()

        # Direct match
        if candidate_skill_lower == name_lower:
            return True

        # Alternative match
        return any(
            alt.lower() == candidate_skill_lower for alt in self.alternatives
        )


class ExperienceRequirement(BaseModel):
    """Experience requirements"""
    minimum_years: Optional[int] = None
    maximum_years: Optional[int] = None
    preferred_years: Optional[int] = None
    specific_domains: List[str] = Field(default_factory=list)
    # e.g., "Software Engineer", "Data Scientist"
    role_types: List[str] = Field(default_factory=list)


class EducationRequirement(BaseModel):
    """Education requirements"""
    minimum_degree: str  # e.g., "Bachelor", "Master"
    preferred_degree: Optional[str] = None
    fields_of_study: List[str] = Field(default_factory=list)
    required: bool = True


class JobRequirements(BaseModel):
    """Complete job requirements extracted from JD"""

    # Basic Info
    job_title: str
    department: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None  # Full-time, Contract, etc.

    # Description
    job_description: str
    responsibilities: List[str] = Field(default_factory=list)

    # Requirements
    technical_skills: List[Skill] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    tools_and_technologies: List[str] = Field(default_factory=list)

    experience: ExperienceRequirement
    education: EducationRequirement

    certifications: List[str] = Field(default_factory=list)

    # Nice to have
    preferred_qualifications: List[str] = Field(default_factory=list)

    # Company info
    company_name: Optional[str] = None
    company_description: Optional[str] = None

    # Metadata
    source_file: Optional[str] = None

    @property
    def must_have_skills(self) -> List[Skill]:
        """Get only must-have skills"""
        return [
            s for s in self.technical_skills
            if s.priority == SkillPriority.MUST_HAVE
        ]

    @property
    def nice_to_have_skills(self) -> List[Skill]:
        """Get nice-to-have skills"""
        return [
            s for s in self.technical_skills
            if s.priority == SkillPriority.NICE_TO_HAVE
        ]

    @property
    def all_required_skill_names(self) -> List[str]:
        """Get list of all skill names"""
        return [skill.name for skill in self.technical_skills]
