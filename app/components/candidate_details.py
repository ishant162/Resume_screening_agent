"""
Candidate Details Component

Shows detailed profile for selected candidate.
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.utils.state_manager import get_state, set_state


def render_candidate_details():
    """Render detailed candidate profile"""

    st.header("👤 Candidate Details")

    selected = get_state("selected_candidate")

    if not selected:
        st.warning("⚠️ No candidate selected")
        if st.button("← Back to Results"):
            set_state("current_page", "results")
            st.rerun()
        return

    cs = selected.get("candidate_score", {})
    candidate_name = cs.get("candidate_name", "Unknown")

    # Back button
    if st.button("← Back to Results"):
        set_state("current_page", "results")
        st.rerun()

    st.markdown("---")

    # Header with score
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"## {candidate_name}")

        # Recommendation badge
        recommendation = cs.get("recommendation", "Unknown")
        rec_color = {
            "Strong Match": "green",
            "Good Match": "blue",
            "Potential Match": "orange",
            "Not Recommended": "red",
        }.get(recommendation, "gray")

        st.markdown(f"### :{rec_color}[{recommendation}]")

    with col2:
        total_score = cs.get("total_score", 0)
        st.metric(
            "Overall Score",
            f"{total_score:.1f}%",
            help="Weighted average of all component scores",
        )

    st.markdown("---")

    # Tabs for different sections
    tabs = st.tabs(
        [
            "📊 Overview",
            "🎯 Skills Analysis",
            "💼 Experience",
            "🎓 Education",
            "🎤 Interview Questions",
            "💰 Compensation",
        ]
    )

    # Tab 1: Overview
    with tabs[0]:
        render_overview_tab(cs)

    # Tab 2: Skills
    with tabs[1]:
        render_skills_tab(cs)

    # Tab 3: Experience
    with tabs[2]:
        render_experience_tab(cs)

    # Tab 4: Education
    with tabs[3]:
        render_education_tab(cs)

    # Tab 5: Interview Questions
    with tabs[4]:
        render_questions_tab(candidate_name)

    # Tab 6: Compensation
    with tabs[5]:
        render_compensation_tab(candidate_name)


def render_overview_tab(cs: dict):
    """Render overview tab"""

    st.subheader("📋 Executive Summary")

    # Component scores
    col1, col2, col3 = st.columns(3)

    with col1:
        skill_score = cs.get("skill_score", {}).get("overall_skill_score", 0)
        st.metric("Skills Match", f"{skill_score:.1f}%")

    with col2:
        exp_score = cs.get("experience_score", {}).get("experience_match_score", 0)
        st.metric("Experience Match", f"{exp_score:.1f}%")

    with col3:
        edu_score = cs.get("education_score", {}).get("education_score", 0)
        st.metric("Education Match", f"{edu_score:.1f}%")

    st.markdown("---")

    # Strengths
    st.markdown("#### ✅ Key Strengths")
    strengths = cs.get("strengths", [])
    if strengths:
        for strength in strengths:
            st.success(f"• {strength}")
    else:
        st.info("No specific strengths identified")

    # Concerns
    concerns = cs.get("concerns", [])
    if concerns:
        st.markdown("#### ⚠️ Areas of Concern")
        for concern in concerns:
            st.warning(f"• {concern}")

    # Red flags
    red_flags = cs.get("red_flags", [])
    if red_flags:
        st.markdown("#### 🚩 Red Flags")
        for flag in red_flags:
            st.error(f"• {flag}")

    # Detailed analysis
    st.markdown("---")
    st.markdown("#### 📝 Comprehensive Analysis")
    detailed = cs.get("detailed_analysis", "No detailed analysis available")
    st.info(detailed)


def render_skills_tab(cs: dict):
    """Render skills analysis tab"""

    st.subheader("🎯 Skills Analysis")

    skill_score = cs.get("skill_score", {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### ✅ Matched Skills")

        matched_must = skill_score.get("matched_must_have", [])
        if matched_must:
            st.success(f"**Must-Have ({len(matched_must)}):**")
            for skill in matched_must:
                st.markdown(f"- {skill}")

        matched_nice = skill_score.get("matched_nice_to_have", [])
        if matched_nice:
            st.info(f"**Nice-to-Have ({len(matched_nice)}):**")
            for skill in matched_nice:
                st.markdown(f"- {skill}")

    with col2:
        st.markdown("#### ❌ Missing Skills")

        missing_must = skill_score.get("missing_must_have", [])
        if missing_must:
            st.error(f"**Critical Gaps ({len(missing_must)}):**")
            for skill in missing_must:
                st.markdown(f"- {skill}")
        else:
            st.success("No critical skill gaps!")

        missing_nice = skill_score.get("missing_nice_to_have", [])
        if missing_nice:
            st.warning(f"**Nice-to-Have Gaps ({len(missing_nice)}):**")
            for skill in missing_nice[:5]:
                st.markdown(f"- {skill}")

    # Additional skills
    additional = skill_score.get("additional_skills", [])
    if additional:
        st.markdown("---")
        st.markdown("#### ➕ Additional Skills")
        st.info(
            f"Candidate brings {len(additional)} additional skills beyond requirements:"
        )
        st.markdown(", ".join(additional[:15]))

    # Gap analysis
    st.markdown("---")
    st.markdown("#### 🔍 Detailed Gap Analysis")
    gap_analysis = skill_score.get("skill_gap_analysis", "No analysis available")
    st.text_area("", value=gap_analysis, height=200, disabled=True)


def render_experience_tab(cs: dict):
    """Render experience analysis tab"""

    st.subheader("💼 Experience Analysis")

    exp_score = cs.get("experience_score", {})

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Years", f"{exp_score.get('total_years', 0):.1f}")

    with col2:
        st.metric("Relevant Years", f"{exp_score.get('relevant_years', 0):.1f}")

    with col3:
        st.metric("Required Years", exp_score.get("required_years", "N/A"))

    with col4:
        trajectory = exp_score.get("career_trajectory", "unknown")
        st.metric("Trajectory", trajectory.title())

    # Domain match
    st.markdown("---")
    domain_match = exp_score.get("domain_match", False)

    if domain_match:
        st.success("✅ **Domain Match:** Worked in relevant industries")
        domains = exp_score.get("relevant_domains", [])
        if domains:
            st.markdown(f"**Relevant Domains:** {', '.join(domains)}")
    else:
        st.warning("⚠️ **Domain Match:** Limited experience in target domain")

    # Analysis
    st.markdown("---")
    st.markdown("#### 📝 Detailed Experience Analysis")
    exp_analysis = exp_score.get("experience_analysis", "No analysis available")
    st.text_area("", value=exp_analysis, height=200, disabled=True)


def render_education_tab(cs: dict):
    """Render education tab"""

    st.subheader("🎓 Education Analysis")

    edu_score = cs.get("education_score", {})

    col1, col2, col3 = st.columns(3)

    with col1:
        highest = edu_score.get("highest_degree", "Not specified")
        st.metric("Highest Degree", highest)

    with col2:
        required = edu_score.get("required_degree", "Not specified")
        st.metric("Required Degree", required)

    with col3:
        meets = edu_score.get("meets_requirement", False)
        st.metric("Meets Requirement", "✅ Yes" if meets else "❌ No")

    st.markdown("---")

    # Field match
    field_match = edu_score.get("field_match", False)
    if field_match:
        st.success("✅ Field of study is relevant to the role")
    else:
        st.warning("⚠️ Field of study may not be directly relevant")

    # Certifications
    certs = edu_score.get("certifications", [])
    if certs:
        st.markdown("#### 📜 Certifications")
        for cert in certs:
            st.markdown(f"- {cert}")

    # Analysis
    st.markdown("---")
    st.markdown("#### 📝 Detailed Education Analysis")
    edu_analysis = edu_score.get("education_analysis", "No analysis available")
    st.text_area("", value=edu_analysis, height=150, disabled=True)


def render_questions_tab(candidate_name: str):
    """Render interview questions tab"""

    st.subheader("🎤 Personalized Interview Questions")

    questions = get_state("interview_questions") or {}
    candidate_questions = questions.get(candidate_name, [])

    if not candidate_questions:
        st.info("No interview questions generated for this candidate")
        return

    st.markdown(
        f"**{len(candidate_questions)} questions generated specifically for {candidate_name}**"
    )

    st.markdown("---")

    # Display questions
    for i, question in enumerate(candidate_questions, 1):
        with st.container():
            st.markdown(f"**Question {i}:**")
            st.info(question)

            # Copy button
            if st.button("📋 Copy", key=f"copy_q_{i}"):
                st.toast("Copied to clipboard!")

    # Download questions
    st.markdown("---")
    questions_text = "\n\n".join(
        [f"{i}. {q}" for i, q in enumerate(candidate_questions, 1)]
    )

    st.download_button(
        label="💾 Download Questions",
        data=questions_text,
        file_name=f"interview_questions_{candidate_name.replace(' ', '_')}.txt",
        mime="text/plain",
    )


def render_compensation_tab(candidate_name: str):
    """Render compensation analysis tab"""

    st.subheader("💰 Compensation Analysis")

    results = get_state("results")
    salary_estimates = results.get("salary_estimates", {}) if results else {}
    ats_scores = results.get("ats_scores", {}) if results else {}

    # Salary estimate
    if candidate_name in salary_estimates:
        salary = salary_estimates[candidate_name]

        st.markdown("#### 💵 Estimated Salary Range")

        adjusted_range = salary.get("adjusted_range", {})

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Minimum", f"${adjusted_range.get('min', 0):,}")

        with col2:
            st.metric("Median", f"${adjusted_range.get('median', 0):,}")

        with col3:
            st.metric("Maximum", f"${adjusted_range.get('max', 0):,}")

        # Confidence
        confidence = salary.get("confidence", 0)
        st.progress(confidence, text=f"Confidence: {confidence:.0%}")

        # Reasoning
        st.markdown("---")
        st.markdown("#### 📊 Estimation Reasoning")
        reasoning = salary.get("reasoning", "No reasoning available")
        st.info(reasoning)

        # Factors
        with st.expander("🔍 View Adjustment Factors"):
            factors = salary.get("factors", {})
            st.json(factors)
    else:
        st.info("Salary estimate not available for this candidate")

    st.markdown("---")

    # ATS Score
    if candidate_name in ats_scores:
        ats = ats_scores[candidate_name]

        st.markdown("#### 📋 ATS Compatibility")

        overall_score = ats.get("overall_score", 0)
        readiness = ats.get("ats_readiness", "Unknown")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("ATS Score", f"{overall_score:.1f}/100")

        with col2:
            st.metric("Readiness", readiness)

        # Category scores
        st.markdown("**Category Breakdown:**")
        category_scores = ats.get("category_scores", {})

        for category, score in category_scores.items():
            st.progress(
                score / 100, text=f"{category.replace('_', ' ').title()}: {score:.0f}%"
            )

        # Improvements
        improvements = ats.get("improvements", [])
        if improvements:
            with st.expander("💡 Suggested Improvements"):
                for improvement in improvements:
                    st.warning(f"• {improvement}")
    else:
        st.info("ATS score not available for this candidate")
