import operator
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """State that flows through the agent graph"""

    job_description: str
    resumes: list[bytes]
    resume_filenames: list[str] | None

    job_requirements: dict | None

    candidates: Annotated[list[dict], operator.add]

    skill_scores: list[dict] | None
    experience_scores: list[dict] | None
    education_scores: list[dict] | None

    candidate_scores: list[dict] | None
    ranked_candidates: list[dict] | None
    report: str | None
    interview_questions: dict[str, list[str]] | None

    user_question: str | None
    agent_response: str | None
    conversation_history: Annotated[list[BaseMessage], operator.add]

    current_step: str | None
    errors: Annotated[list[str], operator.add]

    tool_plan: dict | None
    company_verifications: dict | None
    github_analyses: dict | None
    skill_taxonomy_data: dict | None
    quality_check: dict | None
    reanalysis_count: int | None
    bias_analysis: dict | None
    salary_estimates: dict | None
    ats_scores: dict | None
