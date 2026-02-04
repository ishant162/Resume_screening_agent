"""
ATS Scorer Node

Wraps the ATSScorer tool in a LangGraph node.
"""


from src.tools import ATSScorer
from src.tools.pdf_extractor import PDFExtractor


def ats_scorer_node(state: dict) -> dict:
    """
    LangGraph node: Score resumes for ATS compatibility

    Helps candidates understand how their resumes will perform
    in Applicant Tracking Systems.
    """
    print("="*80)
    print("ATS SCORER - RESUME OPTIMIZATION ANALYSIS")
    print("="*80 + "\n")

    scorer = ATSScorer()
    pdf_extractor = PDFExtractor()

    ats_scores = {}

    # Get resume texts
    resume_texts = {}
    for resume_bytes, filename in zip(
        state.get("resumes", []),
        state.get("resume_filenames", [])
    ):
        text = pdf_extractor.extract_text(resume_bytes)
        resume_texts[filename] = text

    # Score each candidate
    for candidate_data in state["candidates"]:
        candidate_name = candidate_data.get("name", "Unknown")
        resume_filename = candidate_data.get("resume_file_name", "")

        print(f"  Scoring ATS compatibility for {candidate_name}...")

        # Get resume text
        resume_text = resume_texts.get(resume_filename, "")

        # Score
        score_result = scorer.score_resume(
            resume_text,
            candidate_data,
            state["job_requirements"]
        )

        ats_scores[candidate_name] = score_result

        print(f" ATS Score: {score_result['overall_score']:.1f}/100 "
              f"({score_result['ats_readiness']})")

    print(f"\nATS scoring complete for {len(ats_scores)} candidates\n")

    return {
        "ats_scores": ats_scores,
        "current_step": "ats_scoring_complete"
    }


# Test
if __name__ == "__main__":
    print("Testing ATS scorer node...")

    # Mock state
    state = {
        "candidates": [
            {
                "name": "Alice",
                "email": "alice@email.com",
                "phone": "555-1234",
                "technical_skills": ["Python", "TensorFlow"],
                "work_experience": [
                    {"company": "Tech Corp", "responsibilities": ["Built systems"]}
                ],
                "resume_file_name": "alice.pdf"
            }
        ],
        "resumes": [b"mock pdf data"],
        "resume_filenames": ["alice.pdf"],
        "job_requirements": {
            "technical_skills": [
                {"name": "Python"},
                {"name": "TensorFlow"}
            ]
        }
    }

    result = ats_scorer_node(state)
    print("\nATS scoring complete")

    for name, score in result["ats_scores"].items():
        print(f"\n{name}:")
        print(f"  Overall: {score['overall_score']:.1f}/100")
        print(f"  Readiness: {score['ats_readiness']}")
