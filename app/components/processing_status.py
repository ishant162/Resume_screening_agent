"""
Processing Status Component

Shows real-time progress during workflow execution.
"""

import sys
import time
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.utils.state_manager import get_state, set_state


def render_processing_status():
    """Render processing status with real-time updates"""

    st.header("⚙️ Processing Resumes")

    # Check if we should start processing
    if get_state("workflow_state") == "processing" and not get_state("results"):
        run_workflow()

    # Show progress
    workflow_state = get_state("workflow_state")

    if workflow_state == "processing":
        show_processing_ui()
    elif workflow_state == "complete":
        show_completion_ui()
    elif workflow_state == "error":
        show_error_ui()
    else:
        st.info("No processing in progress")


def run_workflow():
    """Run the screening workflow"""

    st.info("🚀 Starting workflow execution...")

    # Get inputs
    job_description = get_state("job_description")
    resume_files = get_state("resume_files")
    workflow_type = get_state("workflow_type")

    if not job_description or not resume_files:
        st.error("❌ Missing job description or resumes")
        set_state("workflow_state", "error")
        return

    # Prepare data
    resumes = []
    filenames = []

    for resume_file in resume_files:
        resumes.append(resume_file.read())
        filenames.append(resume_file.name)

    # Create initial state
    initial_state = {
        "job_description": job_description,
        "resumes": resumes,
        "resume_filenames": filenames,
        "candidates": [],
        "errors": [],
        "reanalysis_count": 0,
    }

    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Choose workflow based on selection
    if "Enhanced" in workflow_type:
        nodes = [
            "Job Analysis",
            "Resume Parsing",
            "Tool Coordination",
            "Candidate Enrichment",
            "Skill Matching",
            "Experience Analysis",
            "Education Verification",
            "Scoring & Ranking",
            "Quality Check",
            "Bias Detection",
            "Salary Estimation",
            "ATS Scoring",
            "Report Generation",
            "Question Generation",
        ]
    else:  # Basic workflow
        nodes = [
            "Job Analysis",
            "Resume Parsing",
            "Skill Matching",
            "Experience Analysis",
            "Education Verification",
            "Scoring & Ranking",
            "Report Generation",
            "Question Generation",
        ]

    try:
        # Create graph based on workflow type
        status_text.text("🤖 Initializing AI agent...")

        if "Enhanced" in workflow_type:
            from src.agents.graph.graph_enhanced import create_enhanced_screening_graph

            app = create_enhanced_screening_graph()
        else:
            from src.agents.graph.graph_builder import create_screening_graph

            app = create_screening_graph()

        # Execute workflow
        status_text.text("▶️ Executing workflow...")

        # Run with progress updates (simulated)
        for i, node_name in enumerate(nodes):
            progress = (i + 1) / len(nodes)
            progress_bar.progress(progress)
            status_text.text(f"⚙️ {node_name}...")
            time.sleep(0.2)  # Brief delay for visual feedback

        # Actually run the workflow
        result = app.invoke(initial_state)

        # Save results
        set_state("results", result)
        set_state("ranked_candidates", result.get("ranked_candidates", []))
        set_state("report", result.get("report", ""))
        set_state("interview_questions", result.get("interview_questions", {}))
        set_state("workflow_state", "complete")

        progress_bar.progress(1.0)
        status_text.text("✅ Processing complete!")

        time.sleep(1)
        st.rerun()

    except Exception as e:
        st.error(f"❌ Error during processing: {str(e)}")
        set_state("workflow_state", "error")
        set_state("errors", [str(e)])

        # Show error details in expander
        with st.expander("🔍 Error Details"):
            st.exception(e)


def show_processing_ui():
    """Show processing in progress UI"""

    st.info("⚙️ Workflow is running... This may take 2-3 minutes.")

    # Animated spinner
    with st.spinner("Processing candidates..."):
        st.write("")

    # Show node status
    st.markdown("### 📊 Workflow Progress")

    nodes_status = [
        ("Job Analysis", True),
        ("Resume Parsing", True),
        ("Tool Coordination", True),
        ("Candidate Enrichment", True),
        ("Skill Matching", False),
        ("Experience Analysis", False),
        ("Education Verification", False),
        ("Scoring & Ranking", False),
        ("Quality Check", False),
        ("Report Generation", False),
    ]

    for node, completed in nodes_status:
        if completed:
            st.success(f"✅ {node}")
        else:
            st.info(f"⏳ {node}")


def show_completion_ui():
    """Show completion message"""

    st.success("✅ **Processing Complete!**")

    results = get_state("results")

    if results:
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)

        candidates = results.get("candidates", [])
        ranked = results.get("ranked_candidates", [])

        with col1:
            st.metric("Candidates Screened", len(candidates))

        with col2:
            strong_matches = sum(
                1
                for rc in ranked
                if rc.get("candidate_score", {}).get("recommendation") == "Strong Match"
            )
            st.metric("Strong Matches", strong_matches)

        with col3:
            if ranked:
                top_score = ranked[0].get("candidate_score", {}).get("total_score", 0)
                st.metric("Top Score", f"{top_score:.1f}%")

        with col4:
            reanalysis_count = results.get("reanalysis_count", 0)
            st.metric("Re-analysis Iterations", reanalysis_count)

        st.markdown("---")

        # View results button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "📊 View Results Dashboard", type="primary", use_container_width=True
            ):
                set_state("current_page", "results")
                st.rerun()


def show_error_ui():
    """Show error UI"""

    st.error("❌ **Processing Failed**")

    errors = get_state("errors")

    if errors:
        for error in errors:
            st.error(error)

    if st.button("🔄 Try Again"):
        set_state("workflow_state", "idle")
        set_state("current_page", "upload")
        st.rerun()
