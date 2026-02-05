# Resume Screening Agentic System

An advanced, agentic AI system for automated resume screening that uses LangGraph, multiple LLMs, and intelligent tool orchestration to evaluate candidates fairly, comprehensively, and efficiently.

## Business Problem Being Solved

### Current Challenges

Manual resume screening is a time-consuming and often biased process. Recruiters and hiring managers are inundated with applications, making it difficult to give each resume the attention it deserves. This can lead to qualified candidates being overlooked and potential biases influencing decisions.

### Value Delivered

This project automates and enhances the resume screening process, delivering significant value by:

*   **Increasing Efficiency:** Automates the initial screening process, freeing up human recruiters to focus on more strategic tasks.
*   **Improving Fairness:** Reduces bias by using a standardized and objective evaluation process.
*   **Enhancing Accuracy:** Provides a comprehensive analysis of each candidate, including skill matching, experience evaluation, and education verification.

## Technical Architecture

The system is built on a modular and scalable architecture that leverages a variety of technologies to provide a comprehensive solution.

### **High-Level Workflow**
<img width="3121" height="7578" alt="resume_screening_architecture_v3" src="https://github.com/user-attachments/assets/c4531d35-1ce8-4d1b-bd40-efd29551db23" />

## Key Features

*   **Automated Resume Parsing:** Extracts structured data from PDF resumes.
*   **Intelligent Skill Matching:** Understands the semantic relationship between skills (e.g., TensorFlow ≈ PyTorch).
*   **Experience Analysis:** Evaluates career trajectory and relevance.
*   **Education Verification:** Handles global degrees and equivalencies.
*   **Scoring & Ranking:** Multi-factor weighted scoring system.
*   **Comprehensive Reports:** Professional markdown reports with detailed analysis.
*   **Interview Questions:** Generates personalized questions for each candidate.

### **Workflow Features**
- **Conditional Routing** - Self-reflection can loop back for deeper analysis
- **Adaptive Processing** - Different candidates take different paths based on data quality
- **Error Handling** - Graceful fallbacks throughout the pipeline
- **Scalable Architecture** - Modular design for easy extension

## Tech Stack

*   **Framework:** LangGraph, Langchain
*   **LLM:** Agnostic (configurable)
*   **PDF Processing:** PyPDF2, pdfplumber
*   **Web Search:** DuckDuckGo Search
*   **GitHub API:** PyGithub
*   **Data Models:** Pydantic v2

## Getting Started/Usage

### Prerequisites

*   Python 3.9+
*   Any LLM API key
*   (Optional) GitHub Personal Access Token for higher rate limits

### Installation

1.  Clone the repository:
    ```bash
    git clone <your-repo-url>
    cd resume-screening-agent
    ```
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Set up environment variables:
    ```bash
    cp .env.example .env
    ```
    Edit the `.env` file to add your API keys.

### Usage

*   **Basic Workflow (Fast, no tools):**
    ```bash
    python scripts/run_agent.py \
     --job data/sample_jobs/ai_engineer.txt \
     --resumes data/sample_resumes/*.pdf
    ```
*   **Enhanced Agentic Workflow (Full analysis with tools):**
    ```bash
    python scripts/run_enhanced_agent.py \
     --job data/sample_jobs/ai_engineer.txt \
     --resumes data/sample_resumes/*.pdf
    ```
*   **With Streamlit UI**
    ```bash
    streamlit run app/main.py
    ```
  
## **Author**

**[Ishant Thakare]**
- LinkedIn: [https://linkedin.com/in/ishant-thakare-04074519b]
- GitHub: [ishant162]

---

**Built with ❤️ by [Ishant Thakare]**

*Showcasing the power of agentic AI for real-world applications*

---

**If you found this project helpful, please star the repository!**
