# **Resume Screening Agentic System**

An advanced, agentic AI system for automated resume screening that uses LangGraph, multiple LLMs, and intelligent tool orchestration to evaluate candidates fairly, comprehensively, and efficiently.

---

## **Project Overview**

This project demonstrates a **production-grade agentic AI system** that goes beyond simple automation. The agent:

- **Makes intelligent decisions** about which tools to use for each candidate
- **Enriches data** using web search, GitHub analysis, and semantic skill matching
- **Reviews its own work** through self-reflection and can trigger re-analysis
- **Ensures fairness** with bias detection and ethical screening practices
- **Provides comprehensive insights** including salary estimates and ATS scoring

---

## **Key Features**

### **Core Capabilities**
- **Automated Resume Parsing** - Extracts structured data from PDF resumes
- **Intelligent Skill Matching** - Semantic understanding (e.g., TensorFlow ≈ PyTorch)
- **Experience Analysis** - Evaluates career trajectory and relevance
- **Education Verification** - Handles global degrees and equivalencies
- **Scoring & Ranking** - Multi-factor weighted scoring system
- **Comprehensive Reports** - Professional markdown reports with detailed analysis
- **Interview Questions** - Personalized questions for each candidate

### **Agentic Enhancements** 🚀
- **Tool Coordinator** - LLM decides which tools to use per candidate (not all candidates need all tools)
- **Company Verification** - Web search to validate companies and understand tech stacks
- **GitHub Analysis** - Validates coding skills through repository analysis
- **Skill Taxonomy** - Semantic matching for related skills
- **Quality Checker** - Self-reflection mechanism that can trigger re-analysis
- **Bias Detection** - Identifies potential hiring biases
- **Salary Estimation** - Provides compensation benchmarking
- **ATS Scoring** - Evaluates resume optimization for Applicant Tracking Systems

### **Workflow Features**
- **Conditional Routing** - Self-reflection can loop back for deeper analysis
- **Adaptive Processing** - Different candidates take different paths based on data quality
- **Error Handling** - Graceful fallbacks throughout the pipeline
- **Scalable Architecture** - Modular design for easy extension

---

## **Architecture**

### **High-Level Workflow**
```
START
  ↓
1. Job Analyzer (extracts requirements)
  ↓
2. Resume Parser (parses PDFs)
  ↓
3. Tool Coordinator (LLM decides tools) ← AGENTIC
  ↓
4. Candidate Enricher (runs tools)
  ├─→ Web Search
  ├─→ GitHub Analysis
  └─→ Skill Taxonomy
  ↓
5. Enhanced Skill Matcher
  ↓
6. Enhanced Experience Analyzer
  ↓
7. Education Verifier
  ↓
8. Scorer & Ranker
  ↓
9. Quality Checker (self-reflection) ← AGENTIC
  ↓
  [Conditional: Re-analyze OR Continue]
  ↓
10. Bias Detector
  ↓
11. Salary Estimator
  ↓
12. ATS Scorer
  ↓
13. Report Generator
  ↓
14. Question Generator
  ↓
END
```

### **Tech Stack**

- **Framework**: LangGraph (for agentic workflows)
- **LLM**: OpenAI GPT-4 Turbo (configurable)
- **PDF Processing**: PyPDF2, pdfplumber
- **NLP**: spaCy
- **Web Search**: DuckDuckGo Search
- **GitHub API**: PyGithub
- **Data Models**: Pydantic v2
- **Document Generation**: python-docx, markdown

---

## **Getting Started**

### **Prerequisites**

- Python 3.9+
- OpenAI API key
- (Optional) GitHub Personal Access Token for higher rate limits

### **Installation**

1. **Clone the repository**
```bash
   git clone <your-repo-url>
   cd resume-screening-agent
```

2. **Create virtual environment**
```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
```

4. **Set up environment variables**
```bash
   cp .env.example .env
```
   
   Edit `.env` and add your API keys:
```env
   OPENAI_API_KEY=your_openai_api_key_here
   GITHUB_TOKEN=your_github_token_here  # Optional
   
   MODEL_NAME=gpt-4-turbo-preview
   TEMPERATURE=0.3
   
   SKILL_WEIGHT=0.5
   EXPERIENCE_WEIGHT=0.3
   EDUCATION_WEIGHT=0.2
```

5. **Prepare sample data**
   
   Create a job description file in `data/sample_jobs/`:
```bash
   mkdir -p data/sample_jobs data/sample_resumes data/outputs
```
   
   Add your job description and resume PDFs to the respective folders.

---

## **Usage**

### **Basic Workflow** (Fast, no tools)
```bash
python scripts/run_agent.py \
    --job data/sample_jobs/ai_engineer.txt \
    --resumes data/sample_resumes/*.pdf
```

### **Enhanced Agentic Workflow** (Full analysis with tools)
```bash
python scripts/run_enhanced_agent.py \
    --job data/sample_jobs/ai_engineer.txt \
    --resumes data/sample_resumes/*.pdf
```

### **With Custom Output Directory**
```bash
python scripts/run_enhanced_agent.py \
    --job data/sample_jobs/ai_engineer.txt \
    --resumes data/sample_resumes/*.pdf \
    --output results
```

### **With Verbose Logging**
```bash
python scripts/run_enhanced_agent.py \
    --job data/sample_jobs/ai_engineer.txt \
    --resumes data/sample_resumes/*.pdf \
    --verbose
```

---

## **Output**

The agent generates two main files in the output directory:

### **1. Screening Report** (`screening_report_YYYYMMDD_HHMMSS.md`)

A comprehensive markdown report containing:
- Executive summary
- Top candidates at a glance (comparison table)
- Detailed candidate profiles with:
  - Overall scores and recommendations
  - Skills analysis (matches, gaps, equivalents)
  - Experience assessment (with company context)
  - Education verification
  - Salary estimates
  - ATS compatibility scores
  - Bias analysis results
- Hiring recommendations
- Next steps

### **2. Interview Questions** (`interview_questions_YYYYMMDD_HHMMSS.md`)

Personalized interview questions for each candidate, organized by:
- Technical skills (4-5 questions)
- Skill gaps (2-3 questions)
- Experience deep-dive (3-4 questions)
- Behavioral/cultural fit (2-3 questions)

---

## **Configuration**

### **Scoring Weights**

Adjust in `.env` or `config/settings.py`:
```python
SKILL_WEIGHT=0.5        # 50% weight
EXPERIENCE_WEIGHT=0.3   # 30% weight
EDUCATION_WEIGHT=0.2    # 20% weight
```

### **LLM Settings**
```python
MODEL_NAME=gpt-4-turbo-preview  # or gpt-4, claude-sonnet-4, etc.
TEMPERATURE=0.3                  # Lower = more deterministic
```

### **Tool Thresholds**

Edit in respective tool files:
- `SkillTaxonomy`: Similarity thresholds
- `QualityChecker`: Confidence thresholds
- `BiasDetector`: Bias severity levels

---

## **Key Agentic Features Explained**

### **1. Tool Coordinator (Intelligent Tool Selection)**

Instead of running all tools for all candidates, the LLM decides:
- "This candidate has a GitHub URL and claims to be a developer → Run GitHub analysis"
- "This company is unfamiliar → Run web search to verify"
- "Job has complex skill requirements → Use skill taxonomy"

**Why it matters**: Saves time and API costs by being strategic.

### **2. Quality Checker (Self-Reflection)**

The agent reviews its own work:
- Checks confidence levels
- Identifies inconsistencies
- Can trigger re-analysis if needed (up to 2 iterations)

**Why it matters**: Ensures high-quality results through self-improvement.

### **3. Skill Taxonomy (Semantic Understanding)**

Understands that:
- TensorFlow ≈ PyTorch (90% equivalent)
- React → Vue (related frameworks)
- Python > Django (hierarchical relationship)

**Why it matters**: Fairer evaluation, doesn't penalize candidates for using equivalent technologies.

### **4. Company Verification**

Uses web search to:
- Verify company exists
- Understand tech stack
- Identify industry/domain

**Why it matters**: Provides context for experience evaluation.

---

## **Performance & Scalability**

- **Processing Time**: ~2-3 minutes per candidate (with full tools)
- **Parallelization**: Candidate enrichment can be parallelized
- **Caching**: Company and GitHub data are cached to avoid redundant API calls
- **Rate Limiting**: Built-in delays to respect API limits

---

## **Ethical Considerations**

### **Bias Detection**

The system actively checks for:
- University prestige bias
- Age-biased language
- Gender-biased language
- Scoring inconsistencies

### **Fair Evaluation**

- Recognizes global degrees (BTech = BS, etc.)
- Values non-traditional education (bootcamps, self-taught)
- Considers experience as education substitute
- Uses semantic skill matching (doesn't penalize for using equivalent tools)

### **Transparency**

- All decisions are explained
- Scores are broken down by category
- Reasoning is provided for rankings

---

## **Author**

**[Ishant Thakare]**
- LinkedIn: [https://linkedin.com/in/ishant-thakare-04074519b]
- GitHub: [ishant162]

---

**Built with ❤️ by [Ishant Thakare]**

*Showcasing the power of agentic AI for real-world applications*

---

**If you found this project helpful, please star the repository!**