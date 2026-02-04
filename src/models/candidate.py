from datetime import date
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, field_validator


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
    employment_type: EmploymentType | None = EmploymentType.FULL_TIME
    start_date: date | None = None
    end_date: date | None = None  # None means current
    duration_months: int | None = None
    location: str | None = None
    description: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)

    @property
    def is_current(self) -> bool:
        return self.end_date is None

    @field_validator("duration_months", mode="before")
    @classmethod
    def calculate_duration(cls, v, info):
        """Auto-calculate duration if dates provided"""
        if v is None and "start_date" in info.data and info.data["start_date"]:
            start = info.data["start_date"]
            end = info.data.get("end_date") or date.today()
            months = (end.year - start.year) * 12 + (end.month - start.month)
            return max(0, months)
        return v


class Education(BaseModel):
    """Education details"""

    institution: str
    degree: str  # e.g., "Bachelor of Technology", "Master of Science"
    field_of_study: str  # e.g., "Computer Science", "Data Science"
    start_year: int | None = None
    end_year: int | None = None
    grade: str | None = None  # GPA, percentage, or grade
    location: str | None = None
    relevant_coursework: list[str] = Field(default_factory=list)
    honors: list[str] = Field(default_factory=list)

    @property
    def is_completed(self) -> bool:
        return self.end_year is not None and self.end_year <= date.today().year


class Project(BaseModel):
    """Personal or professional project"""

    name: str
    description: str
    technologies: list[str] = Field(default_factory=list)
    role: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    url: str | None = None
    github_url: str | None = None
    achievements: list[str] = Field(default_factory=list)
    team_size: int | None = None


class Certification(BaseModel):
    """Professional certifications"""

    name: str
    issuing_organization: str
    issue_date: date | None = None
    expiry_date: date | None = None
    credential_id: str | None = None
    url: str | None = None

    @property
    def is_valid(self) -> bool:
        if self.expiry_date is None:
            return True
        return self.expiry_date >= date.today()


class Candidate(BaseModel):
    """Complete candidate profile extracted from resume"""

    # Basic Information
    name: str
    email: EmailStr | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None

    # Professional Summary
    summary: str | None = None

    # Skills
    technical_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)  # Programming languages
    spoken_languages: list[str] = Field(default_factory=list)
    tools_and_technologies: list[str] = Field(default_factory=list)

    # Experience
    work_experience: list[WorkExperience] = Field(default_factory=list)
    total_experience_months: int | None = None

    # Education
    education: list[Education] = Field(default_factory=list)

    # Additional
    projects: list[Project] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    publications: list[str] = Field(default_factory=list)
    awards: list[str] = Field(default_factory=list)

    # Metadata
    resume_file_name: str | None = None
    parsed_date: date | None = Field(default_factory=date.today)

    @property
    def total_experience_years(self) -> float:
        """Calculate total years of experience"""
        if self.total_experience_months:
            return round(self.total_experience_months / 12, 1)
        return 0.0

    @property
    def all_skills(self) -> list[str]:
        """Get all skills combined"""
        return (
            self.technical_skills
            + self.soft_skills
            + self.languages
            + self.tools_and_technologies
        )

    @property
    def highest_education(self) -> Education | None:
        """Get highest education level"""
        degree_hierarchy = {
            "phd": 5,
            "doctorate": 5,
            "master": 4,
            "msc": 4,
            "mtech": 4,
            "mba": 4,
            "bachelor": 3,
            "bsc": 3,
            "btech": 3,
            "be": 3,
            "diploma": 2,
            "high school": 1,
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
                self.highest_education.degree if self.highest_education else "N/A"
            ),
            "key_skills": self.technical_skills[:5],
            "current_role": (
                self.work_experience[0].position if self.work_experience else "N/A"
            ),
        }
