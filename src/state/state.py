from typing import TypedDict, List, Dict, Optional, Annotated
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    """State that flows through the agent graph"""

    # === INPUTS ===
    job_description: str  # Raw job description text
    resumes: List[bytes]  # List of PDF resume files as bytes
    resume_filenames: Optional[List[str]]  # Original filenames

    # === PROCESSED JOB INFO ===
    # Parsed job requirements (will be JobRequirements model)
    job_requirements: Optional[Dict]

    # === PROCESSED CANDIDATES ===
    candidates: Annotated[List[Dict], operator.add]

    # === SCORING RESULTS ===
    skill_scores: Optional[List[Dict]]  # SkillScore for each candidate
    # ExperienceScore for each candidate
    experience_scores: Optional[List[Dict]]
    education_scores: Optional[List[Dict]]  # EducationScore for each candidate

    # === FINAL OUTPUTS ===
    candidate_scores: Optional[List[Dict]]  # CandidateScore for each candidate
    ranked_candidates: Optional[List[Dict]]  # RankedCandidate list (sorted)
    report: Optional[str]  # Final markdown report
    # {candidate_name: [questions]}
    interview_questions: Optional[Dict[str, List[str]]]

    # === INTERACTIVE Q&A ===
    user_question: Optional[str]  # User's follow-up question
    agent_response: Optional[str]  # Agent's response to question
    # Chat history
    conversation_history: Annotated[List[BaseMessage], operator.add]

    # === METADATA ===
    current_step: Optional[str]  # Track which node we're in
    errors: Annotated[List[str], operator.add]  # Collect any errors
