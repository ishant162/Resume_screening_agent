#!/usr/bin/env python3
"""
Enhanced Resume Screening Agent - CLI Runner

Usage:
    python scripts/run_enhanced_agent.py --job path/to/job.txt --resumes path/to/resume1.pdf path/to/resume2.pdf
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.graph.graph_enhanced import create_enhanced_screening_graph


def load_job_description(job_path: str) -> str:
    """Load job description from file"""
    with open(job_path, encoding="utf-8") as f:
        return f.read()


def load_resumes(resume_paths: list) -> tuple:
    """
    Load resume PDFs

    Returns:
        (resume_bytes_list, filenames_list)
    """
    resumes = []
    filenames = []

    for path in resume_paths:
        path_obj = Path(path)
        if not path_obj.exists():
            print(f"Warning: {path} not found, skipping...")
            continue

        with open(path, "rb") as f:
            resumes.append(f.read())
            filenames.append(path_obj.name)

    return resumes, filenames


def save_report(report: str, output_dir: str) -> Path:
    """Save the generated report"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = output_path / f"enhanced_screening_report_{timestamp}.md"

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    return report_file


def save_questions(questions: dict, output_dir: str) -> Path:
    """Save interview questions"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    questions_file = output_path / f"interview_questions_{timestamp}.md"

    with open(questions_file, "w", encoding="utf-8") as f:
        f.write("# Interview Questions\n\n")

        for candidate_name, question_list in questions.items():
            f.write(f"## {candidate_name}\n\n")
            for i, question in enumerate(question_list, 1):
                f.write(f"{i}. {question}\n")
            f.write("\n---\n\n")

    return questions_file


def print_summary(result: dict):
    """Print execution summary"""
    print("\n" + "=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)

    # Job info
    job_req = result.get("job_requirements", {})
    print(f"\nPosition: {job_req.get('job_title', 'N/A')}")

    # Candidates processed
    candidates = result.get("candidates", [])
    print(f"Candidates Screened: {len(candidates)}")

    # Tool usage summary
    tool_plan = result.get("tool_plan", {})
    if tool_plan:
        print("\nTool Usage:")
        web_search_count = sum(
            1 for plan in tool_plan.values() if "web_search" in plan.get("tools", [])
        )
        github_count = sum(
            1 for plan in tool_plan.values() if "github" in plan.get("tools", [])
        )
        taxonomy_count = sum(
            1
            for plan in tool_plan.values()
            if "skill_taxonomy" in plan.get("tools", [])
        )

        print(f"  Web Search: {web_search_count} candidates")
        print(f"  GitHub Analysis: {github_count} candidates")
        print(f"  Skill Taxonomy: {taxonomy_count} candidates")

    # Quality check
    quality_check = result.get("quality_check", {})
    if quality_check:
        print("\nQuality Check:")
        print(f"  Confidence: {quality_check.get('confidence', 0):.0%}")
        print(f"  Re-analysis needed: {quality_check.get('needs_reanalysis', False)}")
        reanalysis_count = result.get("reanalysis_count", 0)
        if reanalysis_count > 0:
            print(f"  Re-analysis iterations: {reanalysis_count}")

    # Bias analysis
    bias_analysis = result.get("bias_analysis", {})
    if bias_analysis:
        print("\nBias Analysis:")
        print(
            f"  Bias Score: {bias_analysis.get('bias_score', 0):.1f}/100 (lower is better)"
        )
        print(f"  Assessment: {bias_analysis.get('fairness_assessment', 'N/A')}")

    # Top candidate
    ranked = result.get("ranked_candidates", [])
    if ranked:
        top = ranked[0]
        candidate_score = top.get("candidate_score", {})
        print("\n🏆 Top Candidate:")
        print(f"   Name: {candidate_score.get('candidate_name', 'N/A')}")
        print(f"   Score: {candidate_score.get('total_score', 0):.1f}%")
        print(f"   Recommendation: {candidate_score.get('recommendation', 'N/A')}")

        # Salary estimate
        salary_estimates = result.get("salary_estimates", {})
        if candidate_score.get("candidate_name") in salary_estimates:
            salary = salary_estimates[candidate_score["candidate_name"]]
            median = salary.get("adjusted_range", {}).get("median", 0)
            print(f"   Estimated Salary: ${median:,}")

        # ATS score
        ats_scores = result.get("ats_scores", {})
        if candidate_score.get("candidate_name") in ats_scores:
            ats = ats_scores[candidate_score["candidate_name"]]
            print(f"   ATS Score: {ats.get('overall_score', 0):.1f}/100")

    # Show all rankings
    print("\nAll Rankings:")
    for rc in ranked:
        cs = rc.get("candidate_score", {})
        rank = rc.get("rank", "?")
        name = cs.get("candidate_name", "Unknown")
        score = cs.get("total_score", 0)
        rec = cs.get("recommendation", "N/A")
        print(f"   #{rank} {name}: {score:.1f}% ({rec})")

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Enhanced Agentic Resume Screening Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Screen multiple resumes with enhanced analysis
  python scripts/run_enhanced_agent.py \\
      --job data/sample_jobs/ai_engineer.txt \\
      --resumes data/sample_resumes/candidate_1.pdf data/sample_resumes/candidate_2.pdf

  # Specify custom output directory
  python scripts/run_enhanced_agent.py \\
      --job job.txt \\
      --resumes resume1.pdf resume2.pdf \\
      --output ./results
        """,
    )

    parser.add_argument(
        "--job", required=True, help="Path to job description file (.txt)"
    )

    parser.add_argument(
        "--resumes", nargs="+", required=True, help="Paths to resume PDF files"
    )

    parser.add_argument(
        "--output",
        default="data/outputs",
        help="Output directory for reports (default: data/outputs)",
    )

    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed execution logs"
    )

    args = parser.parse_args()

    # Validate inputs
    if not Path(args.job).exists():
        print(f"Error: Job description file not found: {args.job}")
        sys.exit(1)

    print("=" * 80)
    print("ENHANCED AGENTIC RESUME SCREENING AGENT")
    print("=" * 80)
    print(f"\nJob Description: {args.job}")
    print(f"Resumes to screen: {len(args.resumes)}")
    for resume in args.resumes:
        print(f"   - {resume}")
    print(f"Output directory: {args.output}")
    print("\n" + "=" * 80)
    print("STARTING ENHANCED WORKFLOW...")
    print("=" * 80 + "\n")

    try:
        # Load data
        print("Loading files...")
        job_description = load_job_description(args.job)
        resumes, filenames = load_resumes(args.resumes)

        if not resumes:
            print("Error: No valid resume files found")
            sys.exit(1)

        print(f"Loaded job description and {len(resumes)} resumes\n")

        # Create initial state
        initial_state = {
            "job_description": job_description,
            "resumes": resumes,
            "resume_filenames": filenames,
            "candidates": [],
            "errors": [],
            "reanalysis_count": 0,
        }

        # Create and run the enhanced graph
        print("Initializing enhanced agentic workflow...\n")
        app = create_enhanced_screening_graph()

        print("\n" + "=" * 80)
        print("EXECUTING ENHANCED WORKFLOW")
        print("=" * 80 + "\n")

        result = app.invoke(initial_state)

        # Check for errors
        if result.get("errors"):
            print("\nErrors encountered during execution:")
            for error in result["errors"]:
                print(f"   - {error}")
            print()

        # Save outputs
        print("\nSaving results...")

        # Save report
        report = result.get("report", "")
        if report:
            report_path = save_report(report, args.output)
            print(f"Report saved: {report_path}")

        # Save questions
        questions = result.get("interview_questions", {})
        if questions:
            questions_path = save_questions(questions, args.output)
            print(f"Interview questions saved: {questions_path}")

        # Print summary
        print_summary(result)

        print("\nEnhanced screening complete!")
        print(f"\nView results in: {args.output}/")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during execution: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
