from pydantic import BaseModel, Field, computed_field
from typing import List, Optional, Dict
from datetime import datetime


class SkillScore(BaseModel):
    """Skill matching score for a candidate"""
    candidate_name: str
    
    # Matched skills
    matched_must_have: List[str] = Field(default_factory=list)
    matched_nice_to_have: List[str] = Field(default_factory=list)
    
    # Missing skills
    missing_must_have: List[str] = Field(default_factory=list)
    missing_nice_to_have: List[str] = Field(default_factory=list)
    
    # Additional skills (not in JD but candidate has)
    additional_skills: List[str] = Field(default_factory=list)
    
    # Scoring
    must_have_match_percentage: float = 0.0
    nice_to_have_match_percentage: float = 0.0
    overall_skill_score: float = 0.0  # 0-100
    
    # Details
    skill_gap_analysis: Optional[str] = None
    
    @computed_field
    @property
    def has_critical_gaps(self) -> bool:
        """Check if candidate is missing critical skills"""
        return len(self.missing_must_have) > 0


class ExperienceScore(BaseModel):
    """Experience evaluation score"""
    candidate_name: str
    
    total_years: float
    relevant_years: float
    required_years: Optional[int]
    
    # Domain/Industry match
    domain_match: bool = False
    relevant_domains: List[str] = Field(default_factory=list)
    
    # Role progression
    has_role_progression: bool = False
    career_trajectory: Optional[str] = None  # "upward", "lateral", "downward"
    
    # Scoring
    experience_match_score: float = 0.0  # 0-100
    
    # Analysis
    experience_analysis: Optional[str] = None
    
    @computed_field
    @property
    def meets_minimum_requirement(self) -> bool:
        """Check if candidate meets minimum experience"""
        if self.required_years is None:
            return True
        return self.relevant_years >= self.required_years


class EducationScore(BaseModel):
    """Education verification score"""
    candidate_name: str
    
    highest_degree: Optional[str] = None
    required_degree: Optional[str] = None
    
    meets_requirement: bool = False
    field_match: bool = False
    
    relevant_coursework: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    
    education_score: float = 0.0  # 0-100
    
    education_analysis: Optional[str] = None


class CandidateScore(BaseModel):
    """Aggregated score for a candidate"""
    candidate_name: str
    candidate_email: Optional[str] = None
    
    # Individual scores
    skill_score: SkillScore
    experience_score: ExperienceScore
    education_score: EducationScore
    
    # Weighted scores (based on config weights)
    weighted_skill_score: float
    weighted_experience_score: float
    weighted_education_score: float
    
    # Final score
    total_score: float  # 0-100
    
    # Recommendation
    recommendation: str  # "Strong Match", "Good Match", "Potential Match", "Not Recommended"
    confidence_level: str  # "High", "Medium", "Low"
    
    # Summary
    strengths: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)
    
    # Detailed reasoning
    detailed_analysis: Optional[str] = None
    
    # Metadata
    scored_at: datetime = Field(default_factory=datetime.now)
    
    @computed_field
    @property
    def is_recommended(self) -> bool:
        """Quick check if candidate is recommended"""
        return self.recommendation in ["Strong Match", "Good Match"]
    
    def get_summary_dict(self) -> Dict:
        """Get a summary dictionary for display"""
        return {
            "name": self.candidate_name,
            "total_score": round(self.total_score, 1),
            "recommendation": self.recommendation,
            "top_strengths": self.strengths[:3],
            "key_concerns": self.concerns[:2],
        }


class RankedCandidate(BaseModel):
    """Candidate with ranking information"""
    rank: int
    candidate_score: CandidateScore
    
    # Comparative analysis
    comparison_notes: Optional[str] = None
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"#{self.rank} - {self.candidate_score.candidate_name}"