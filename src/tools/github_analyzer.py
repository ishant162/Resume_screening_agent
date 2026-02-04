"""
GitHub Profile Analyzer

Analyzes GitHub profiles to validate coding skills and activity.
"""

import os
from collections import Counter

from github import Github, GithubException


class GitHubAnalyzer:
    """Analyzes GitHub profiles to validate technical skills"""

    def __init__(self, access_token: str | None = None):
        """
        Initialize GitHub analyzer

        Args:
            access_token: GitHub personal access token (optional, increases rate limit)
        """
        # Get token from env or use None (lower rate limit)
        token = access_token or os.getenv("GITHUB_TOKEN")
        self.github = Github(token) if token else Github()
        self.cache = {}

    def analyze_profile(self, github_url: str) -> dict:
        """
        Analyze a GitHub profile

        Args:
            github_url: GitHub profile URL or username

        Returns:
            {
                "username": str,
                "exists": bool,
                "public_repos": int,
                "followers": int,
                "primary_languages": List[str],
                "active_repos": List[Dict],
                "total_stars": int,
                "contribution_score": float,
                "skills_validated": List[str],
                "assessment": str
            }
        """
        # Extract username from URL
        username = self._extract_username(github_url)

        if not username:
            return self._empty_profile("Invalid GitHub URL")

        # Check cache
        if username in self.cache:
            print(f"    📋 Using cached GitHub data for {username}")
            return self.cache[username]

        print(f"    🔍 Analyzing GitHub profile: {username}")

        try:
            user = self.github.get_user(username)

            # Get basic stats
            public_repos = user.public_repos
            followers = user.followers

            # Analyze repositories
            repos = list(user.get_repos(sort="updated", direction="desc"))[
                :20
            ]  # Top 20 recent

            # Extract languages
            languages = []
            total_stars = 0
            active_repos = []

            for repo in repos:
                if not repo.fork:  # Skip forks
                    total_stars += repo.stargazers_count

                    if repo.language:
                        languages.append(repo.language)

                    # Consider "active" if updated in last year
                    if repo.updated_at:
                        from datetime import datetime, timezone

                        age_days = (datetime.now(timezone.utc) - repo.updated_at).days
                        if age_days < 365:
                            active_repos.append(
                                {
                                    "name": repo.name,
                                    "language": repo.language,
                                    "stars": repo.stargazers_count,
                                    "description": repo.description,
                                }
                            )

            # Get top languages
            language_counts = Counter(languages)
            primary_languages = [lang for lang, _ in language_counts.most_common(5)]

            # Calculate contribution score (simple heuristic)
            contribution_score = self._calculate_contribution_score(
                public_repos, followers, total_stars, len(active_repos)
            )

            # Map languages to skills
            skills_validated = self._map_languages_to_skills(primary_languages)

            # Generate assessment
            assessment = self._generate_assessment(
                username,
                public_repos,
                followers,
                total_stars,
                len(active_repos),
                primary_languages,
            )

            result = {
                "username": username,
                "exists": True,
                "public_repos": public_repos,
                "followers": followers,
                "primary_languages": primary_languages,
                "active_repos": active_repos[:5],  # Top 5 active
                "total_stars": total_stars,
                "contribution_score": round(contribution_score, 1),
                "skills_validated": skills_validated,
                "assessment": assessment,
            }

            # Cache result
            self.cache[username] = result
            return result

        except GithubException as e:
            if e.status == 404:
                return self._empty_profile(f"User {username} not found")
            else:
                return self._empty_profile(f"GitHub API error: {str(e)}")
        except Exception as e:
            print(f"    ⚠️  GitHub analysis failed: {e}")
            return self._empty_profile(f"Analysis error: {str(e)}")

    def validate_skills(self, github_url: str, claimed_skills: list[str]) -> dict:
        """
        Validate claimed skills against GitHub activity

        Returns:
            {
                "validated_skills": List[str],
                "unvalidated_skills": List[str],
                "validation_confidence": float
            }
        """
        profile = self.analyze_profile(github_url)

        if not profile["exists"]:
            return {
                "validated_skills": [],
                "unvalidated_skills": claimed_skills,
                "validation_confidence": 0.0,
            }

        validated = []
        unvalidated = []

        github_skills = set(s.lower() for s in profile["skills_validated"])

        for skill in claimed_skills:
            if skill.lower() in github_skills:
                validated.append(skill)
            else:
                unvalidated.append(skill)

        confidence = len(validated) / len(claimed_skills) if claimed_skills else 0.0

        return {
            "validated_skills": validated,
            "unvalidated_skills": unvalidated,
            "validation_confidence": round(confidence, 2),
        }

    def _extract_username(self, github_url: str) -> str | None:
        """Extract username from GitHub URL"""
        if not github_url:
            return None

        # Handle various formats
        url_lower = github_url.lower().strip()

        # Already just username
        if "github.com" not in url_lower and "/" not in url_lower:
            return github_url.strip()

        # Extract from URL
        if "github.com/" in url_lower:
            parts = github_url.split("github.com/")[-1].split("/")
            if parts and parts[0]:
                return parts[0]

        return None

    def _calculate_contribution_score(
        self, repos: int, followers: int, stars: int, active_repos: int
    ) -> float:
        """
        Calculate contribution score (0-100)

        Heuristic scoring:
        - Repos: 30 points (diminishing returns)
        - Followers: 20 points
        - Stars: 30 points
        - Activity: 20 points
        """
        import math

        # Repos score (logarithmic, max 30)
        repos_score = min(30, math.log10(repos + 1) * 15)

        # Followers score (logarithmic, max 20)
        followers_score = min(20, math.log10(followers + 1) * 10)

        # Stars score (logarithmic, max 30)
        stars_score = min(30, math.log10(stars + 1) * 15)

        # Activity score (linear, max 20)
        activity_score = min(20, active_repos * 2)

        total = repos_score + followers_score + stars_score + activity_score
        return min(100, total)

    def _map_languages_to_skills(self, languages: list[str]) -> list[str]:
        """Map programming languages to related skills"""
        skill_map = {
            "Python": ["Python", "Django", "Flask", "FastAPI", "NumPy", "Pandas"],
            "JavaScript": ["JavaScript", "React", "Node.js", "Angular", "Vue"],
            "TypeScript": ["TypeScript", "JavaScript", "React", "Angular"],
            "Java": ["Java", "Spring", "Maven"],
            "Go": ["Go", "Golang"],
            "Rust": ["Rust"],
            "C++": ["C++", "C"],
            "Jupyter Notebook": ["Python", "Data Science", "Machine Learning"],
            "HTML": ["HTML", "CSS", "Web Development"],
            "CSS": ["CSS", "HTML", "Web Development"],
        }

        skills = set()
        for lang in languages:
            if lang in skill_map:
                skills.update(skill_map[lang])
            else:
                skills.add(lang)

        return list(skills)

    def _generate_assessment(
        self,
        username: str,
        repos: int,
        followers: int,
        stars: int,
        active_repos: int,
        languages: list[str],
    ) -> str:
        """Generate human-readable assessment"""

        # Activity level
        if active_repos >= 5:
            activity = "highly active"
        elif active_repos >= 2:
            activity = "moderately active"
        else:
            activity = "limited recent activity"

        # Community engagement
        if followers > 100:
            engagement = "strong community presence"
        elif followers > 20:
            engagement = "decent community engagement"
        else:
            engagement = "growing community presence"

        # Code quality indicators
        if stars > 50:
            quality = "well-received projects"
        elif stars > 10:
            quality = "some community validation"
        else:
            quality = "early-stage projects"

        lang_str = ", ".join(languages[:3]) if languages else "various technologies"

        assessment = (
            f"{username} shows {activity} on GitHub with {repos} public repositories "
            f"primarily in {lang_str}. Profile demonstrates {engagement} with {followers} followers "
            f"and {quality} ({stars} total stars). "
        )

        if active_repos >= 3:
            assessment += "Strong evidence of consistent coding practice."
        elif active_repos >= 1:
            assessment += "Some evidence of recent development work."
        else:
            assessment += "Limited recent public contributions."

        return assessment

    def _empty_profile(self, reason: str) -> dict:
        """Return empty profile structure"""
        return {
            "username": None,
            "exists": False,
            "public_repos": 0,
            "followers": 0,
            "primary_languages": [],
            "active_repos": [],
            "total_stars": 0,
            "contribution_score": 0.0,
            "skills_validated": [],
            "assessment": reason,
        }


# Test
if __name__ == "__main__":
    analyzer = GitHubAnalyzer()

    result = analyzer.analyze_profile("ishant162")

    print("\n✅ GitHub Analysis Result:")
    print(f"Username: {result['username']}")
    print(f"Exists: {result['exists']}")
    print(f"Public Repos: {result['public_repos']}")
    print(f"Followers: {result['followers']}")
    print(f"Primary Languages: {result['primary_languages']}")
    print(f"Contribution Score: {result['contribution_score']}")
    print(f"Skills Validated: {result['skills_validated'][:5]}")
    print(f"\nAssessment: {result['assessment']}")
