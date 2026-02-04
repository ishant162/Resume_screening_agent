import re

import spacy


class TextProcessor:
    """NLP utilities for text processing"""

    def __init__(self):
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            print("Downloading spaCy model...")
            import os

            os.system("python -m spacy download en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

        # Common tech skills (you can expand this)
        self.tech_skills_database = {
            # Programming Languages
            "python",
            "java",
            "javascript",
            "typescript",
            "c++",
            "c#",
            "go",
            "rust",
            "ruby",
            "php",
            "swift",
            "kotlin",
            "scala",
            "r",
            "matlab",
            # Frameworks
            "react",
            "angular",
            "vue",
            "django",
            "flask",
            "fastapi",
            "spring",
            "express",
            "nodejs",
            "node.js",
            ".net",
            "laravel",
            "rails",
            # ML/AI
            "tensorflow",
            "pytorch",
            "keras",
            "scikit-learn",
            "pandas",
            "numpy",
            "opencv",
            "nlp",
            "computer vision",
            "deep learning",
            "machine learning",
            "neural networks",
            "transformers",
            "llm",
            "langchain",
            "langgraph",
            # Databases
            "sql",
            "mysql",
            "postgresql",
            "mongodb",
            "redis",
            "elasticsearch",
            "cassandra",
            "dynamodb",
            "oracle",
            # Cloud & DevOps
            "aws",
            "azure",
            "gcp",
            "docker",
            "kubernetes",
            "jenkins",
            "gitlab",
            "terraform",
            "ansible",
            "ci/cd",
            # Other
            "git",
            "linux",
            "api",
            "rest",
            "graphql",
            "microservices",
            "agile",
            "html",
            "css",
            "tailwind",
            "bootstrap",
        }

    def extract_skills(self, text: str) -> list[str]:
        """Extract technical skills from text"""
        text_lower = text.lower()
        found_skills = set()

        # Look for exact matches
        for skill in self.tech_skills_database:
            # Use word boundaries to avoid partial matches
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, text_lower):
                found_skills.add(skill.title())

        return sorted(list(found_skills))

    def extract_emails(self, text: str) -> list[str]:
        """Extract email addresses"""
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        return re.findall(email_pattern, text)

    def extract_phone_numbers(self, text: str) -> list[str]:
        """Extract phone numbers"""
        # Simple pattern - can be improved
        phone_pattern = r"[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]"
        return re.findall(phone_pattern, text)

    def extract_urls(self, text: str) -> list[str]:
        """Extract URLs"""
        url_pattern = r"https?://[^\s]+"
        return re.findall(url_pattern, text)

    def extract_names(self, text: str, max_chars: int = 500) -> list[str]:
        """Extract potential names using spaCy NER"""
        # Only process first part of text for efficiency
        doc = self.nlp(text[:max_chars])
        names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
        return names[:5]  # Return top 5


# Quick test
if __name__ == "__main__":
    processor = TextProcessor()

    sample_text = """
    John Doe
    Email: john.doe@email.com
    Phone: +1-234-567-8900

    Skills: Python, TensorFlow, React, AWS, Docker, PostgreSQL

    Experience with deep learning and NLP projects.
    """

    print("Skills:", processor.extract_skills(sample_text))
    print("Emails:", processor.extract_emails(sample_text))
    print("Names:", processor.extract_names(sample_text))
