"""
Results Dashboard Component

Displays screening results with interactive visualizations.
"""

import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.utils.state_manager import get_state, set_state


def render_results_dashboard():
    """Render the main results dashboard"""

    st.header("📊 Screening Results Dashboard")

    results = get_state("results")

    if not results:
        st.warning("⚠️ No results available. Please run screening first.")
        if st.button("← Back to Upload"):
            set_state("current_page", "upload")
            st.rerun()
        return

    ranked_candidates = results.get("ranked_candidates", [])

    if not ranked_candidates:
        st.error("No candidates were ranked")
        return

    # Summary metrics
    render_summary_metrics(results)

    st.markdown("---")

    # Candidates table
    render_candidates_table(ranked_candidates)

    st.markdown("---")

    # Visualizations
    col1, col2 = st.columns(2)

    with col1:
        render_score_distribution(ranked_candidates)

    with col2:
        render_recommendation_pie(ranked_candidates)

    # Additional analyses
    st.markdown("---")
    render_additional_analyses(results)

    # Download section
    st.markdown("---")
    render_download_section(results)


def render_summary_metrics(results: dict):
    """Render summary metrics at the top"""

    st.subheader("📈 Overview")

    col1, col2, col3, col4, col5 = st.columns(5)

    candidates = results.get("candidates", [])
    ranked = results.get("ranked_candidates", [])

    with col1:
        st.metric("📊 Total Candidates", len(candidates))

    with col2:
        strong = sum(
            1
            for rc in ranked
            if rc.get("candidate_score", {}).get("recommendation") == "Strong Match"
        )
        st.metric("🟢 Strong Matches", strong)

    with col3:
        good = sum(
            1
            for rc in ranked
            if rc.get("candidate_score", {}).get("recommendation") == "Good Match"
        )
        st.metric("🟡 Good Matches", good)

    with col4:
        if ranked:
            top_score = ranked[0].get("candidate_score", {}).get("total_score", 0)
            st.metric("🏆 Top Score", f"{top_score:.1f}%")

    with col5:
        bias_analysis = results.get("bias_analysis", {})
        bias_score = bias_analysis.get("bias_score", 0)
        st.metric("⚖️ Bias Score", f"{bias_score:.0f}/100", help="Lower is better")


def render_candidates_table(ranked_candidates: list):
    """Render interactive candidates table"""

    st.subheader("👥 Ranked Candidates")

    # Prepare table data
    table_data = []

    for rc in ranked_candidates:
        cs = rc.get("candidate_score", {})

        # Get recommendation emoji
        rec_emoji = {
            "Strong Match": "🟢",
            "Good Match": "🟡",
            "Potential Match": "🟠",
            "Not Recommended": "🔴",
        }.get(cs.get("recommendation", ""), "⚪")

        table_data.append(
            {
                "Rank": f"#{rc.get('rank')}",
                "Name": cs.get("candidate_name", "Unknown"),
                "Score": f"{cs.get('total_score', 0):.1f}%",
                "Recommendation": f"{rec_emoji} {cs.get('recommendation', 'N/A')}",
                "Skills": f"{cs.get('skill_score', {}).get('overall_skill_score', 0):.0f}%",
                "Experience": f"{cs.get('experience_score', {}).get('experience_match_score', 0):.0f}%",
                "Education": f"{cs.get('education_score', {}).get('education_score', 0):.0f}%",
            }
        )

    # Display table
    import pandas as pd

    df = pd.DataFrame(table_data)

    # Custom styling
    def highlight_top(row):
        if row["Rank"] == "#1":
            return ["background-color: #d4edda"] * len(row)
        elif row["Rank"] in ["#2", "#3"]:
            return ["background-color: #d1ecf1"] * len(row)
        else:
            return [""] * len(row)

    styled_df = df.style.apply(highlight_top, axis=1)
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # View details buttons
    st.markdown("#### 🔍 View Candidate Details")

    cols = st.columns(min(5, len(ranked_candidates)))

    for i, (col, rc) in enumerate(zip(cols, ranked_candidates[:5])):
        with col:
            candidate_name = rc.get("candidate_score", {}).get(
                "candidate_name", f"Candidate {i + 1}"
            )
            if st.button(f"#{rc.get('rank')} {candidate_name}", key=f"view_btn_{i}"):
                set_state("selected_candidate", rc)
                set_state("current_page", "details")
                st.rerun()


def render_score_distribution(ranked_candidates: list):
    """Render score distribution chart"""

    st.subheader("📊 Score Distribution")

    # Extract scores
    names = []
    total_scores = []
    skill_scores = []
    exp_scores = []
    edu_scores = []

    for rc in ranked_candidates:
        cs = rc.get("candidate_score", {})
        names.append(cs.get("candidate_name", "Unknown"))
        total_scores.append(cs.get("total_score", 0))
        skill_scores.append(cs.get("skill_score", {}).get("overall_skill_score", 0))
        exp_scores.append(
            cs.get("experience_score", {}).get("experience_match_score", 0)
        )
        edu_scores.append(cs.get("education_score", {}).get("education_score", 0))

    # Create grouped bar chart
    fig = go.Figure()

    fig.add_trace(
        go.Bar(name="Skills", x=names, y=skill_scores, marker_color="#1f77b4")
    )

    fig.add_trace(
        go.Bar(name="Experience", x=names, y=exp_scores, marker_color="#ff7f0e")
    )

    fig.add_trace(
        go.Bar(name="Education", x=names, y=edu_scores, marker_color="#2ca02c")
    )

    fig.update_layout(
        barmode="group",
        xaxis_title="Candidates",
        yaxis_title="Score (%)",
        yaxis_range=[0, 100],
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_recommendation_pie(ranked_candidates: list):
    """Render recommendation distribution pie chart"""

    st.subheader("🎯 Recommendation Distribution")

    # Count recommendations
    recommendations = {}
    for rc in ranked_candidates:
        rec = rc.get("candidate_score", {}).get("recommendation", "Unknown")
        recommendations[rec] = recommendations.get(rec, 0) + 1

    # Create pie chart
    fig = go.Figure(
        data=[
            go.Pie(
                labels=list(recommendations.keys()),
                values=list(recommendations.values()),
                marker_colors=["#2ecc71", "#3498db", "#f39c12", "#e74c3c"],
                hole=0.3,
            )
        ]
    )

    fig.update_layout(
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_additional_analyses(results: dict):
    """Render additional analysis results"""

    st.subheader("🔬 Additional Analyses")

    col1, col2, col3 = st.columns(3)

    # Bias Analysis
    with col1:
        bias_analysis = results.get("bias_analysis", {})

        if bias_analysis:
            bias_score = bias_analysis.get("bias_score", 0)

            # Color based on score
            if bias_score <= 20:
                color = "green"
            elif bias_score <= 40:
                color = "blue"
            elif bias_score <= 60:
                color = "orange"
            else:
                color = "red"

            st.markdown("#### ⚖️ Bias Analysis")
            st.markdown(f"**Score:** :{color}[{bias_score:.0f}/100]")
            st.caption(bias_analysis.get("fairness_assessment", ""))

            if bias_analysis.get("detected_biases"):
                with st.expander(
                    f"🚩 {len(bias_analysis['detected_biases'])} Bias(es) Detected"
                ):
                    for bias in bias_analysis["detected_biases"]:
                        st.warning(f"**{bias.get('type')}** ({bias.get('severity')})")
                        st.caption(bias.get("description", ""))

    # Quality Check
    with col2:
        quality_check = results.get("quality_check", {})

        if quality_check:
            confidence = quality_check.get("confidence", 0)

            st.markdown("#### ✅ Quality Check")
            st.markdown(f"**Confidence:** {confidence:.0%}")

            issues = quality_check.get("issues", [])
            if issues:
                with st.expander(f"⚠️ {len(issues)} Issue(s) Found"):
                    for issue in issues:
                        st.warning(issue)
            else:
                st.success("No issues detected")

    # Tool Usage
    with col3:
        tool_plan = results.get("tool_plan", {})

        if tool_plan:
            st.markdown("#### 🔧 Tool Usage")

            web_search_count = sum(
                1
                for plan in tool_plan.values()
                if "web_search" in plan.get("tools", [])
            )
            github_count = sum(
                1 for plan in tool_plan.values() if "github" in plan.get("tools", [])
            )
            taxonomy_count = sum(
                1
                for plan in tool_plan.values()
                if "skill_taxonomy" in plan.get("tools", [])
            )

            st.text(f"🔍 Web Search: {web_search_count}")
            st.text(f"💻 GitHub: {github_count}")
            st.text(f"🔗 Taxonomy: {taxonomy_count}")


def render_download_section(results: dict):
    """Render download section"""

    st.subheader("💾 Download Results")

    col1, col2, col3 = st.columns(3)

    with col1:
        report = results.get("report", "")
        if report:
            st.download_button(
                label="📄 Download Report (MD)",
                data=report,
                file_name="screening_report.md",
                mime="text/markdown",
                use_container_width=True,
            )

    with col2:
        questions = results.get("interview_questions", {})
        if questions:
            # Format questions as markdown
            questions_md = "# Interview Questions\n\n"
            for candidate_name, question_list in questions.items():
                questions_md += f"## {candidate_name}\n\n"
                for i, q in enumerate(question_list, 1):
                    questions_md += f"{i}. {q}\n"
                questions_md += "\n---\n\n"

            st.download_button(
                label="🎤 Download Questions (MD)",
                data=questions_md,
                file_name="interview_questions.md",
                mime="text/markdown",
                use_container_width=True,
            )

    with col3:
        # Download results as JSON
        import json

        results_json = json.dumps(results, indent=2, default=str)

        st.download_button(
            label="📦 Download Raw Data (JSON)",
            data=results_json,
            file_name="screening_results.json",
            mime="application/json",
            use_container_width=True,
        )


def show_processing_ui():
    """Show animated processing UI"""

    st.markdown("### ⚙️ Processing in Progress...")

    # Progress placeholder
    progress_placeholder = st.empty()
    status_placeholder = st.empty()

    # Simulated progress
    import time

    steps = [
        "🔍 Analyzing job description...",
        "📄 Parsing resumes...",
        "🧠 Coordinating tools...",
        "⚡ Enriching candidate data...",
        "🎯 Matching skills...",
        "💼 Analyzing experience...",
        "🎓 Verifying education...",
        "🏆 Scoring & ranking...",
        "✅ Quality checking...",
        "⚖️ Detecting biases...",
        "💰 Estimating salaries...",
        "📋 Scoring ATS compatibility...",
        "📊 Generating report...",
        "🎤 Creating interview questions...",
    ]

    for i, step in enumerate(steps):
        progress = (i + 1) / len(steps)
        progress_placeholder.progress(progress)
        status_placeholder.info(step)
        time.sleep(0.3)

    status_placeholder.success("✅ Complete!")


def show_error_ui():
    """Show error message"""

    st.error("❌ Processing failed")

    errors = get_state("errors")
    if errors:
        with st.expander("Error Details"):
            for error in errors:
                st.code(error)

    if st.button("Try Again"):
        set_state("workflow_state", "idle")
        set_state("current_page", "upload")
        st.rerun()
