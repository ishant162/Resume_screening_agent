from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional
from datetime import date
from enum import Enum


class EmploymentType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"


class WorkExperience(BaseModel):
    """Individual work experience entry"""
    company: str
    position: str
    employment_type: Optional[EmploymentType] = EmploymentType.FULL_TIME
    start_date: Optional[date] = None
    end_date: Optional[date] = None  # None means current
    duration_months: Optional[int] = None
    location: Optional[str] = None
    description: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)

    @property
    def is_current(self) -> bool:
        return self.end_date is None

    @field_validator('duration_months', mode='before')
    @classmethod
    def calculate_duration(cls, v, info):
        """Auto-calculate duration if dates provided"""
        if v is None and 'start_date' in info.data and info.data['start_date']:
            start = info.data['start_date']
            end = info.data.get('end_date') or date.today()
            months = (end.year - start.year) * 12 + (end.month - start.month)
            return max(0, months)
        return v


class Education(BaseModel):
    """Education details"""
    institution: str
    degree: str  # e.g., "Bachelor of Technology", "Master of Science"
    field_of_study: str  # e.g., "Computer Science", "Data Science"
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    grade: Optional[str] = None  # GPA, percentage, or grade
    location: Optional[str] = None
    relevant_coursework: List[str] = Field(default_factory=list)
    honors: List[str] = Field(default_factory=list)

    @property
    def is_completed(self) -> bool:
        return self.end_year is not None and self.end_year <= date.today().year


class Project(BaseModel):
    """Personal or professional project"""
    name: str
    description: str
    technologies: List[str] = Field(default_factory=list)
    role: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    url: Optional[str] = None
    github_url: Optional[str] = None
    achievements: List[str] = Field(default_factory=list)
    team_size: Optional[int] = None


class Certification(BaseModel):
    """Professional certifications"""
    name: str
    issuing_organization: str
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = None
    url: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        if self.expiry_date is None:
            return True
        return self.expiry_date >= date.today()


class Candidate(BaseModel):
    """Complete candidate profile extracted from resume"""

    # Basic Information
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None

    # Professional Summary
    summary: Optional[str] = None

    # Skills
    technical_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)  # Programming languages
    spoken_languages: List[str] = Field(default_factory=list)
    tools_and_technologies: List[str] = Field(default_factory=list)

    # Experience
    work_experience: List[WorkExperience] = Field(default_factory=list)
    total_experience_months: Optional[int] = None

    # Education
    education: List[Education] = Field(default_factory=list)

    # Additional
    projects: List[Project] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    publications: List[str] = Field(default_factory=list)
    awards: List[str] = Field(default_factory=list)

    # Metadata
    resume_file_name: Optional[str] = None
    parsed_date: Optional[date] = Field(default_factory=date.today)

    @property
    def total_experience_years(self) -> float:
        """Calculate total years of experience"""
        if self.total_experience_months:
            return round(self.total_experience_months / 12, 1)
        return 0.0

    @property
    def all_skills(self) -> List[str]:
        """Get all skills combined"""
        return (
            self.technical_skills +
            self.soft_skills +
            self.languages +
            self.tools_and_technologies
        )

    @property
    def highest_education(self) -> Optional[Education]:
        """Get highest education level"""
        degree_hierarchy = {
            "phd": 5, "doctorate": 5,
            "master": 4, "msc": 4, "mtech": 4, "mba": 4,
            "bachelor": 3, "bsc": 3, "btech": 3, "be": 3,
            "diploma": 2,
            "high school": 1
        }

        if not self.education:
            return None

        def get_level(edu: Education) -> int:
            degree_lower = edu.degree.lower()
            for key, value in degree_hierarchy.items():
                if key in degree_lower:
                    return value
            return 0

        return max(self.education, key=get_level)

    def model_dump_summary(self) -> dict:
        """Return a summarized version for display"""
        return {
            "name": self.name,
            "email": self.email,
            "total_experience": f"{self.total_experience_years} years",
            "education": (
                self.highest_education.degree
                if self.highest_education else "N/A"
                ),
            "key_skills": self.technical_skills[:5],
            "current_role": (
                    self.work_experience[0].position
                    if self.work_experience else "N/A"
                )
        }
