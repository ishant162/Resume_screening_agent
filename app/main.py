"""
Resume Screening Agent - Streamlit UI

A beautiful, interactive interface for the agentic resume screening system.
"""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.components.candidate_details import render_candidate_details
from app.components.processing_status import render_processing_status
from app.components.results_dashboard import render_results_dashboard
from app.components.upload_section import render_upload_section
from app.utils.state_manager import get_state, initialize_session_state, set_state

# Page configuration
st.set_page_config(
    page_title="Resume Screening AI Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    /* Main container */
    .main {
        padding: 2rem;
    }

    /* Headers */
    h1 {
        color: #1f77b4;
        font-weight: 700;
        margin-bottom: 1rem;
    }

    h2 {
        color: #2c3e50;
        font-weight: 600;
        margin-top: 2rem;
    }

    /* Candidate cards */
    .candidate-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }

    .candidate-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }

    /* Score badges */
    .score-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 1.1rem;
    }

    .score-excellent {
        background: #d4edda;
        color: #155724;
    }

    .score-good {
        background: #d1ecf1;
        color: #0c5460;
    }

    .score-fair {
        background: #fff3cd;
        color: #856404;
    }

    .score-poor {
        background: #f8d7da;
        color: #721c24;
    }

    /* Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: 600;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }

    /* Progress */
    .stProgress > div > div {
        background-color: #1f77b4;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 1.1rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


def main():
    """Main Streamlit application"""

    # Initialize session state
    initialize_session_state()

    # Sidebar
    render_sidebar()

    # Main content area
    st.title("🤖 Resume Screening AI Agent")
    st.markdown("### Intelligent, Fair, and Comprehensive Candidate Evaluation")
    st.markdown("---")

    # Get current page
    page = get_state("current_page")

    # Render appropriate page
    if page == "upload":
        render_upload_page()
    elif page == "processing":
        render_processing_page()
    elif page == "results":
        render_results_page()
    elif page == "details":
        render_details_page()
    else:
        render_upload_page()


def render_sidebar():
    """Render sidebar navigation"""

    with st.sidebar:
        st.image(
            "https://via.placeholder.com/150x50/1f77b4/ffffff?text=AI+Agent",
            use_container_width=True,
        )
        st.markdown("## 🎯 Navigation")

        # Current state
        state = get_state("workflow_state")

        # Navigation buttons
        if st.button("📤 Upload & Configure", use_container_width=True):
            set_state("current_page", "upload")
            st.rerun()

        # Show other pages only after upload
        if state in ["processing", "complete"]:
            if st.button("⚙️ Processing Status", use_container_width=True):
                set_state("current_page", "processing")
                st.rerun()

        if state == "complete":
            if st.button("📊 Results Dashboard", use_container_width=True):
                set_state("current_page", "results")
                st.rerun()

            if st.button("👤 Candidate Details", use_container_width=True):
                set_state("current_page", "details")
                st.rerun()

        st.markdown("---")

        # Settings expander
        with st.expander("⚙️ Settings"):
            st.markdown("#### Scoring Weights")

            skill_weight = st.slider(
                "Skills Weight",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.05,
                key="skill_weight",
            )

            exp_weight = st.slider(
                "Experience Weight",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.05,
                key="exp_weight",
            )

            edu_weight = st.slider(
                "Education Weight",
                min_value=0.0,
                max_value=1.0,
                value=0.2,
                step=0.05,
                key="edu_weight",
            )

            total = skill_weight + exp_weight + edu_weight
            if abs(total - 1.0) > 0.01:
                st.warning(f"⚠️ Weights must sum to 1.0 (currently {total:.2f})")

        # Info
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown("""
        **Agentic Features:**
        - 🧠 Intelligent tool selection
        - ✅ Self-reflection & quality checks
        - 🔍 Company & GitHub verification
        - ⚖️ Bias detection
        - 💰 Salary estimation
        """)

        st.markdown("---")
        st.caption("Built with LangGraph & GPT-4")


def render_upload_page():
    """Render upload and configuration page"""
    render_upload_section()


def render_processing_page():
    """Render processing status page"""
    render_processing_status()


def render_results_page():
    """Render results dashboard page"""
    render_results_dashboard()


def render_details_page():
    """Render candidate details page"""
    render_candidate_details()


if __name__ == "__main__":
    main()
