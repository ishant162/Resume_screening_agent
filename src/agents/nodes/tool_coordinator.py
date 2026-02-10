"""
Tool Coordinator Node

LLM-powered coordinator that intelligently decides which tools to use for each candidate.
This is the "brain" of the agentic system.
"""

import json

from langchain_core.messages import HumanMessage, SystemMessage

from config.prompts import VERIFICATION_TOOL_SELECTION_PROMPT
from src.llm.groq_llm import GroqLLM


class ToolCoordinator:
    """
    Intelligent tool selection coordinator

    Analyzes each candidate and decides which enrichment tools to use:
    - Web search for company verification
    - GitHub analysis for skill validation
    - Skill taxonomy for semantic matching
    """

    def __init__(self):
        self.llm = GroqLLM().get_llm_model()

    def create_tool_plan(self, candidates: list[dict], job_requirements: dict) -> dict:
        """
        Create a tool execution plan for all candidates

        Args:
            candidates: List of parsed candidates
            job_requirements: Job requirements

        Returns:
            {
                "candidate_name": {
                    "tools": ["web_search", "github", "skill_taxonomy"],
                    "reasoning": "explanation",
                    "priority": "high|medium|low"
                }
            }
        """
        print(" Tool Coordinator: Analyzing candidates and planning tool usage...\n")

        tool_plan = {}

        for candidate in candidates:
            candidate_name = candidate.get("name", "Unknown")
            print(f" Planning tools for {candidate_name}...")

            # Let LLM decide which tools to use
            plan = self._decide_tools_for_candidate(candidate, job_requirements)
            tool_plan[candidate_name] = plan

            tools_str = ", ".join(plan["tools"]) if plan["tools"] else "None"
            print(f"    Tools: {tools_str}")
            print(f"    Reasoning: {plan['reasoning']}")

        print(f"\n Tool coordination complete for {len(candidates)} candidates\n")

        return tool_plan

    def _decide_tools_for_candidate(
        self, candidate: dict, job_requirements: dict
    ) -> dict:
        """
        Use LLM to decide which tools to use for a specific candidate

        This is where the agent makes intelligent decisions!
        """

        # Prepare candidate summary
        candidate_summary = self._format_candidate_summary(candidate)

        # Prepare available tools description
        tools_description = """
            Available Tools:
            1. web_search: Search the web to verify companies, understand tech stacks, validate claims
            - Use when: Company is unfamiliar, want to understand their technology environment

            2. github: Analyze GitHub profile to validate coding skills and activity
            - Use when: Candidate provides GitHub URL and claims to be a developer

            3. skill_taxonomy: Use semantic understanding to match related skills
            - Use when: Job has many technical requirements, skills need nuanced matching
        """

        prompt = VERIFICATION_TOOL_SELECTION_PROMPT.format(
            job_title=job_requirements.get("job_title", "Technical Role"),
            candidate_summary=candidate_summary,
            tools_description=tools_description,
        )

        try:
            messages = [
                SystemMessage(
                    content="You are an intelligent hiring coordinator making strategic tool selection decisions."
                ),
                HumanMessage(content=prompt),
            ]

            response = self.llm.invoke(messages)
            response_text = response.content.strip()

            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            plan = json.loads(response_text.strip())

            # Validate tools list
            valid_tools = ["web_search", "github", "skill_taxonomy"]
            plan["tools"] = [t for t in plan.get("tools", []) if t in valid_tools]

            return plan

        except Exception as e:
            print(f" Tool planning failed for {candidate.get('name')}: {e}")
            # Default fallback: use skill taxonomy for everyone
            return {
                "tools": ["skill_taxonomy"],
                "reasoning": "Using default tool set due to planning error",
                "priority": "medium",
            }

    def _format_candidate_summary(self, candidate: dict) -> str:
        """Format candidate info for LLM"""

        summary = []

        # Basic info
        summary.append(f"Name: {candidate.get('name', 'Unknown')}")
        summary.append(
            f"Experience: {candidate.get('total_experience_months', 0) / 12:.1f} years"
        )

        # Skills
        skills = candidate.get("technical_skills", [])
        if skills:
            summary.append(f"Skills: {', '.join(skills[:10])}")

        # Work history
        work_exp = candidate.get("work_experience", [])
        if work_exp:
            companies = [exp.get("company", "Unknown") for exp in work_exp[:3]]
            summary.append(f"Recent Companies: {', '.join(companies)}")

        # GitHub
        github_url = candidate.get("github_url")
        if github_url:
            summary.append(f"GitHub: {github_url}")
        else:
            summary.append("GitHub: Not provided")

        # Education
        education = candidate.get("education", [])
        if education:
            edu = education[0]
            summary.append(
                f"Education: {edu.get('degree', 'Unknown')} from {edu.get('institution', 'Unknown')}"
            )

        return "\n".join(summary)


def tool_coordinator_node(state: dict) -> dict:
    """
    LangGraph node: Create tool execution plan

    This is where the agent becomes intelligent - it decides
    which tools to use for each candidate rather than blindly
    running all tools for everyone.
    """
    print("=" * 80)
    print(" TOOL COORDINATOR - AGENTIC DECISION MAKING")
    print("=" * 80 + "\n")

    coordinator = ToolCoordinator()

    candidates = state["candidates"]
    job_requirements = state["job_requirements"]

    tool_plan = coordinator.create_tool_plan(candidates, job_requirements)

    return {"tool_plan": tool_plan, "current_step": "tool_coordination_complete"}


# Test
if __name__ == "__main__":
    from src.data_models import (
        Candidate,
        EducationRequirement,
        ExperienceRequirement,
        JobRequirements,
    )

    # Mock candidates
    candidates = [
        Candidate(
            name="Alice Developer",
            technical_skills=["Python", "TensorFlow", "React"],
            github_url="github.com/alice",
            total_experience_months=60,
            work_experience=[],
            education=[],
        ).model_dump(),
        Candidate(
            name="Bob Manager",
            technical_skills=["Leadership", "Strategy"],
            github_url=None,
            total_experience_months=120,
            work_experience=[],
            education=[],
        ).model_dump(),
    ]

    job = JobRequirements(
        job_title="Senior ML Engineer",
        job_description="Build ML systems",
        technical_skills=[],
        experience=ExperienceRequirement(minimum_years=5),
        education=EducationRequirement(minimum_degree="Bachelor"),
    ).model_dump()

    coordinator = ToolCoordinator()
    plan = coordinator.create_tool_plan(candidates, job)

    print("\n" + "=" * 80)
    print("TOOL PLAN RESULT")
    print("=" * 80)
    for candidate_name, candidate_plan in plan.items():
        print(f"\n{candidate_name}:")
        print(f"  Tools: {candidate_plan['tools']}")
        print(f"  Priority: {candidate_plan['priority']}")
        print(f"  Reasoning: {candidate_plan['reasoning']}")
