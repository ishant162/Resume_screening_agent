"""
Candidate Enricher Node

Executes the tool plan by running selected tools for each candidate.
Enriches candidate profiles with additional data.
"""

from src.tools import GitHubAnalyzer, SkillTaxonomy, WebSearchTool


class CandidateEnricher:
    """
    Execute tool plan and enrich candidate profiles

    Runs the tools selected by the Tool Coordinator
    """

    def __init__(self):
        self.web_search = WebSearchTool()
        self.github_analyzer = GitHubAnalyzer()
        self.skill_taxonomy = SkillTaxonomy()

        self.enrichment_cache = {"companies": {}, "github": {}, "skills": {}}

    def enrich_candidates(self, candidates: list[dict], tool_plan: dict) -> dict:
        """
        Enrich all candidates based on tool plan

        Args:
            candidates: List of candidate dicts
            tool_plan: Tool execution plan from coordinator

        Returns:
            {
                "company_verifications": {...},
                "github_analyses": {...},
                "skill_taxonomy_data": {...}
            }
        """
        print("⚡ Candidate Enricher: Executing tool plan...\n")

        company_verifications = {}
        github_analyses = {}
        skill_taxonomy_data = {}

        for candidate in candidates:
            candidate_name = candidate.get("name", "Unknown")

            # Get tools for this candidate
            plan = tool_plan.get(candidate_name, {})
            tools = plan.get("tools", [])

            if not tools:
                print(f" Skipping {candidate_name} - no tools needed")
                continue

            print(f" Enriching {candidate_name} with tools: {', '.join(tools)}")

            # Execute web search
            if "web_search" in tools:
                company_data = self._run_web_search(candidate)
                if company_data:
                    company_verifications[candidate_name] = company_data

            # Execute GitHub analysis
            if "github" in tools:
                github_data = self._run_github_analysis(candidate)
                if github_data:
                    github_analyses[candidate_name] = github_data

            # Execute skill taxonomy
            if "skill_taxonomy" in tools:
                taxonomy_data = self._run_skill_taxonomy(candidate)
                if taxonomy_data:
                    skill_taxonomy_data[candidate_name] = taxonomy_data

        print("\nEnrichment complete:")
        print(f"  - Companies verified: {len(company_verifications)}")
        print(f"  - GitHub profiles analyzed: {len(github_analyses)}")
        print(f"  - Skills taxonomized: {len(skill_taxonomy_data)}")
        print()

        return {
            "company_verifications": company_verifications,
            "github_analyses": github_analyses,
            "skill_taxonomy_data": skill_taxonomy_data,
        }

    def _run_web_search(self, candidate: dict) -> dict:
        """Run web search for companies"""
        work_exp = candidate.get("work_experience", [])
        if not work_exp:
            return {}

        company_data = {}

        # Search for each company (limit to top 3 most recent)
        for exp in work_exp[:3]:
            company_name = exp.get("company")
            if not company_name:
                continue

            # Check cache
            if company_name in self.enrichment_cache["companies"]:
                company_data[company_name] = self.enrichment_cache["companies"][
                    company_name
                ]
                continue

            # Search
            result = self.web_search.search_company(company_name)
            company_data[company_name] = result
            self.enrichment_cache["companies"][company_name] = result

        return company_data

    def _run_github_analysis(self, candidate: dict) -> dict:
        """Run GitHub analysis"""
        github_url = candidate.get("github_url")
        if not github_url:
            return {}

        # Check cache
        if github_url in self.enrichment_cache["github"]:
            return self.enrichment_cache["github"][github_url]

        # Analyze
        result = self.github_analyzer.analyze_profile(github_url)
        self.enrichment_cache["github"][github_url] = result

        return result

    def _run_skill_taxonomy(self, candidate: dict) -> dict:
        """Run skill taxonomy analysis"""
        skills = candidate.get("technical_skills", [])
        if not skills:
            return {}

        taxonomy_data = {}

        # Get related skills for top skills
        for skill in skills[:10]:  # Top 10 skills
            cache_key = skill.lower()

            if cache_key in self.enrichment_cache["skills"]:
                taxonomy_data[skill] = self.enrichment_cache["skills"][cache_key]
                continue

            related = self.skill_taxonomy.find_related_skills(skill, max_results=3)
            taxonomy_data[skill] = related
            self.enrichment_cache["skills"][cache_key] = related

        return taxonomy_data


def candidate_enricher_node(state: dict) -> dict:
    """
    LangGraph node: Enrich candidates with tool data

    Executes the tool plan created by the coordinator.
    """
    print("=" * 80)
    print("CANDIDATE ENRICHER - EXECUTING TOOLS")
    print("=" * 80 + "\n")

    enricher = CandidateEnricher()

    enrichment_data = enricher.enrich_candidates(
        state["candidates"], state.get("tool_plan", {})
    )

    return {**enrichment_data, "current_step": "enrichment_complete"}


# Test
if __name__ == "__main__":
    print("Testing candidate enricher...")

    # Mock data
    candidates = [
        {
            "name": "Alice",
            "technical_skills": ["Python", "TensorFlow"],
            "github_url": "gvanrossum",
            "work_experience": [{"company": "Google"}],
        }
    ]

    tool_plan = {
        "Alice": {
            "tools": ["web_search", "github", "skill_taxonomy"],
            "priority": "high",
        }
    }

    enricher = CandidateEnricher()
    result = enricher.enrich_candidates(candidates, tool_plan)

    print("\nEnrichment Result:")
    print(f"Companies: {list(result['company_verifications'].keys())}")
    print(f"GitHub: {list(result['github_analyses'].keys())}")
    print(f"Taxonomy: {list(result['skill_taxonomy_data'].keys())}")
