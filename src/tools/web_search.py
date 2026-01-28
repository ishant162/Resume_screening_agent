"""
Web Search Tool for Company Verification

Uses DuckDuckGo to verify companies and gather tech stack information.
"""

from duckduckgo_search import DDGS
from typing import Dict
import time


class WebSearchTool:
    """Web search tool for company verification and research"""
    
    def __init__(self):
        self.ddgs = DDGS()
        self.cache = {}  # Simple in-memory cache
    
    def search_company(self, company_name: str, max_results: int = 3) -> Dict:
        """
        Search for information about a company
        
        Args:
            company_name: Name of the company
            max_results: Maximum search results to return
            
        Returns:
            {
                "exists": bool,
                "description": str,
                "tech_stack": List[str],
                "industry": str,
                "sources": List[str]
            }
        """
        # Check cache
        cache_key = f"company:{company_name.lower()}"
        if cache_key in self.cache:
            print(f"    📋 Using cached data for {company_name}")
            return self.cache[cache_key]
        
        print(f"    🔍 Searching web for: {company_name}")
        
        try:
            # Search for company
            query = f"{company_name} company technology stack"
            results = list(self.ddgs.text(query, max_results=max_results))
            
            if not results:
                return {
                    "exists": False,
                    "description": "No information found",
                    "tech_stack": [],
                    "industry": "Unknown",
                    "sources": []
                }
            
            # Extract information
            exists = True
            description = results[0].get("body", "")
            sources = [r.get("href", "") for r in results]
            
            # Try to identify tech stack (simple heuristic)
            tech_keywords = [
                "Python", "Java", "JavaScript", "React", "Angular", "Vue",
                "AWS", "Azure", "GCP", "Docker", "Kubernetes",
                "TensorFlow", "PyTorch", "Machine Learning", "AI",
                "Node.js", "Django", "Flask", "Spring", "MongoDB", "PostgreSQL"
            ]
            
            tech_stack = []
            combined_text = " ".join([r.get("body", "") for r in results]).lower()
            
            for tech in tech_keywords:
                if tech.lower() in combined_text:
                    tech_stack.append(tech)
            
            # Try to identify industry
            industry = self._identify_industry(combined_text)
            
            result = {
                "exists": exists,
                "description": description[:300],  # First 300 chars
                "tech_stack": list(set(tech_stack)),  # Remove duplicates
                "industry": industry,
                "sources": sources
            }
            
            # Cache result
            self.cache[cache_key] = result
            
            time.sleep(1)  # Rate limiting
            return result
            
        except Exception as e:
            print(f"    ⚠️  Search failed for {company_name}: {e}")
            return {
                "exists": False,
                "description": f"Search error: {str(e)}",
                "tech_stack": [],
                "industry": "Unknown",
                "sources": []
            }
    
    def search_technology(self, technology: str) -> Dict:
        """
        Get information about a technology/skill
        
        Useful for understanding if a skill is relevant
        """
        cache_key = f"tech:{technology.lower()}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            query = f"{technology} programming technology what is"
            results = list(self.ddgs.text(query, max_results=2))
            
            if results:
                result = {
                    "name": technology,
                    "description": results[0].get("body", ""),
                    "category": self._categorize_technology(technology),
                    "related_skills": []
                }
                self.cache[cache_key] = result
                return result
            
        except Exception as e:
            print(f"    ⚠️  Tech search failed: {e}")
        
        return {
            "name": technology,
            "description": "No information available",
            "category": "Unknown",
            "related_skills": []
        }
    
    def _identify_industry(self, text: str) -> str:
        """Identify industry from text"""
        industries = {
            "fintech": ["finance", "banking", "payment", "trading"],
            "healthcare": ["health", "medical", "hospital", "clinical"],
            "ecommerce": ["ecommerce", "retail", "shopping", "marketplace"],
            "enterprise": ["enterprise", "b2b", "saas", "software"],
            "consumer": ["consumer", "social", "mobile app", "b2c"],
            "ai/ml": ["artificial intelligence", "machine learning", "ai", "ml"],
        }
        
        text_lower = text.lower()
        for industry, keywords in industries.items():
            if any(kw in text_lower for kw in keywords):
                return industry
        
        return "Technology"
    
    def _categorize_technology(self, tech: str) -> str:
        """Categorize a technology"""
        categories = {
            "programming_language": ["python", "java", "javascript", "c++", "go", "rust"],
            "ml_framework": ["tensorflow", "pytorch", "keras", "scikit-learn"],
            "web_framework": ["react", "angular", "vue", "django", "flask"],
            "cloud": ["aws", "azure", "gcp", "cloud"],
            "database": ["sql", "mongodb", "postgresql", "mysql", "redis"],
            "devops": ["docker", "kubernetes", "jenkins", "ci/cd"]
        }
        
        tech_lower = tech.lower()
        for category, items in categories.items():
            if any(item in tech_lower for item in items):
                return category
        
        return "general"


# Test
if __name__ == "__main__":
    tool = WebSearchTool()
    
    # Test company search
    result = tool.search_company("Atlassian")
    print("\n✅ Company Search Result:")
    print(f"Exists: {result['exists']}")
    print(f"Industry: {result['industry']}")
    print(f"Tech Stack: {result['tech_stack'][:5]}")
    print(f"Description: {result['description'][:200]}")