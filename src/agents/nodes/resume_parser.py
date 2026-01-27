from langchain_core.messages import HumanMessage, SystemMessage
from config.prompts import RESUME_PARSING_PROMPT
from src.llm.groq_llm import GroqLLM
from src.models import Candidate, WorkExperience, Education, Project
from src.tools.pdf_extractor import PDFExtractor
from src.tools.text_processor import TextProcessor
import json
from typing import Dict
from datetime import date, datetime


class ResumeParser:
    """Parses resume PDFs and extracts structured candidate information"""
    
    def __init__(self):
        self.llm = GroqLLM().get_llm_model()
        self.pdf_extractor = PDFExtractor()
        self.text_processor = TextProcessor()
    
    def parse_resume(self, resume_bytes: bytes, filename: str = "resume.pdf") -> Candidate:
        """
        Parse a single resume PDF
        
        Args:
            resume_bytes: PDF file as bytes
            filename: Original filename (for metadata)
            
        Returns:
            Candidate object with parsed information
        """
        print(f"  📄 Parsing resume: {filename}")
        
        # Step 1: Extract text from PDF
        resume_text = self.pdf_extractor.extract_text(resume_bytes)
        
        if not resume_text or len(resume_text) < 100:
            print(f"  ⚠️  Warning: Very little text extracted from {filename}")
            return self._create_empty_candidate(filename)
        
        # Step 2: Use text processor to extract basic info (as a helper)
        extracted_skills = self.text_processor.extract_skills(resume_text)
        extracted_emails = self.text_processor.extract_emails(resume_text)
        extracted_names = self.text_processor.extract_names(resume_text)
        
        # Step 3: Use LLM for comprehensive parsing
        candidate_data = self._llm_parse(resume_text)
        
        # Step 4: Merge LLM results with text processor results
        # (LLM might miss some skills, text processor catches them)
        if extracted_skills:
            candidate_data["technical_skills"] = list(set(
                candidate_data.get("technical_skills", []) + extracted_skills
            ))
        
        if not candidate_data.get("email") and extracted_emails:
            candidate_data["email"] = extracted_emails[0]
        
        if not candidate_data.get("name") and extracted_names:
            candidate_data["name"] = extracted_names[0]
        
        # Step 5: Convert to Candidate model
        candidate = self._convert_to_model(candidate_data, filename)
        
        print(f"  ✅ Parsed: {candidate.name} - {len(candidate.technical_skills)} skills found")
        return candidate
    
    def _llm_parse(self, resume_text: str) -> Dict:
        """Use LLM to parse resume text into structured data"""
        
        prompt = RESUME_PARSING_PROMPT.format(resume_text=resume_text)
        
        messages = [
            SystemMessage(content="You are an expert at parsing resumes. Extract all information accurately."),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        try:
            # Extract JSON from response
            response_text = response.content
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            candidate_data = json.loads(response_text.strip())
            return candidate_data
            
        except json.JSONDecodeError as e:
            print(f"  ⚠️  Error parsing LLM response: {e}")
            return {}
    
    def _convert_to_model(self, candidate_data: Dict, filename: str) -> Candidate:
        """Convert raw JSON to Candidate Pydantic model"""
        
        # Parse work experience
        work_experience = []
        for exp_data in candidate_data.get("work_experience", []):
            try:
                # Parse dates
                start_date = self._parse_date(exp_data.get("start_date"))
                end_date = self._parse_date(exp_data.get("end_date"))
                
                work_experience.append(WorkExperience(
                    company=exp_data.get("company", "Unknown"),
                    position=exp_data.get("position", "Unknown"),
                    start_date=start_date,
                    end_date=end_date,
                    description=exp_data.get("description"),
                    responsibilities=exp_data.get("responsibilities", []),
                    technologies=exp_data.get("technologies", [])
                ))
            except Exception as e:
                print(f"    Warning: Could not parse work experience entry: {e}")
                continue
        
        # Parse education
        education = []
        for edu_data in candidate_data.get("education", []):
            try:
                education.append(Education(
                    institution=edu_data.get("institution", "Unknown"),
                    degree=edu_data.get("degree", "Unknown"),
                    field_of_study=edu_data.get("field_of_study", "Unknown"),
                    start_year=edu_data.get("start_year"),
                    end_year=edu_data.get("end_year"),
                    grade=edu_data.get("grade"),
                    relevant_coursework=edu_data.get("relevant_coursework", [])
                ))
            except Exception as e:
                print(f"    Warning: Could not parse education entry: {e}")
                continue
        
        # Parse projects
        projects = []
        for proj_data in candidate_data.get("projects", []):
            try:
                projects.append(Project(
                    name=proj_data.get("name", "Unnamed Project"),
                    description=proj_data.get("description", ""),
                    technologies=proj_data.get("technologies", []),
                    role=proj_data.get("role"),
                    url=proj_data.get("url"),
                    github_url=proj_data.get("github_url")
                ))
            except Exception as e:
                print(f"    Warning: Could not parse project entry: {e}")
                continue
        
        # Calculate total experience
        total_months = sum(
            exp.duration_months for exp in work_experience 
            if exp.duration_months
        )
        
        # Create Candidate object
        return Candidate(
            name=candidate_data.get("name", "Unknown Candidate"),
            email=candidate_data.get("email"),
            phone=candidate_data.get("phone"),
            location=candidate_data.get("location"),
            linkedin_url=candidate_data.get("linkedin_url"),
            github_url=candidate_data.get("github_url"),
            summary=candidate_data.get("summary"),
            technical_skills=candidate_data.get("technical_skills", []),
            soft_skills=candidate_data.get("soft_skills", []),
            languages=candidate_data.get("languages", []),
            tools_and_technologies=candidate_data.get("tools_and_technologies", []),
            work_experience=work_experience,
            total_experience_months=total_months,
            education=education,
            projects=projects,
            certifications=[],  # Can be added later
            resume_file_name=filename
        )
    
    def _parse_date(self, date_str) -> date:
        """Parse date string to date object"""
        if not date_str or date_str == "null" or date_str == "present":
            return None
        
        try:
            # Try multiple date formats
            for fmt in ["%Y-%m-%d", "%Y-%m", "%Y", "%m/%Y", "%m/%d/%Y"]:
                try:
                    return datetime.strptime(str(date_str), fmt).date()
                except ValueError:
                    continue
            
            # If all fail, try to extract just the year
            if isinstance(date_str, int) or date_str.isdigit():
                return date(int(date_str), 1, 1)
            
            return None
        except:
            return None
    
    def _create_empty_candidate(self, filename: str) -> Candidate:
        """Create an empty candidate when parsing fails"""
        return Candidate(
            name=f"Unknown ({filename})",
            resume_file_name=filename
        )


def resume_parser_node(state: Dict) -> Dict:
    """
    LangGraph node: Parse all resumes
    
    This node processes multiple resumes in parallel (conceptually)
    and returns all parsed candidates.
    """
    print("📚 Parsing resumes...")
    
    parser = ResumeParser()
    candidates = []
    
    resumes = state.get("resumes", [])
    filenames = state.get("resume_filenames", [f"resume_{i}.pdf" for i in range(len(resumes))])
    
    for resume_bytes, filename in zip(resumes, filenames):
        try:
            candidate = parser.parse_resume(resume_bytes, filename)
            candidates.append(candidate.model_dump())
        except Exception as e:
            print(f"  ❌ Error parsing {filename}: {e}")
            # Add empty candidate so we don't lose track
            empty = parser._create_empty_candidate(filename)
            candidates.append(empty.model_dump())
    
    print(f"✅ Parsed {len(candidates)} resumes")
    
    return {
        "candidates": candidates,
        "current_step": "resume_parsing_complete"
    }


# Test independently
if __name__ == "__main__":
    # Test with a sample resume
    parser = ResumeParser()
    
    with open("data/sample_resumes/candidate_1.pdf", "rb") as f:
        resume_bytes = f.read()
    
    candidate = parser.parse_resume(resume_bytes, "test_resume.pdf")
    
    print("\nParsed Candidate:")
    print(f"Name: {candidate.name}")
    print(f"Email: {candidate.email}")
    print(f"Skills: {candidate.technical_skills[:10]}")
    print(f"Experience: {candidate.total_experience_years} years")
    print(f"Education: {candidate.highest_education.degree if candidate.highest_education else 'N/A'}")