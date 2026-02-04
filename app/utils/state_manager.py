"""
Session State Manager

Manages Streamlit session state for the application.
"""

from typing import Any

import streamlit as st


def initialize_session_state():
    """Initialize all session state variables"""

    defaults = {
        # Navigation
        "current_page": "upload",
        # Workflow state
        "workflow_state": "idle",  # idle, processing, complete, error
        # Inputs
        "job_description": None,
        "resume_files": None,
        "workflow_type": "Enhanced (Full Analysis)",
        "config": {},
        # Processing
        "processing_status": {},
        "current_node": None,
        "progress": 0,
        # Results
        "results": None,
        "ranked_candidates": None,
        "report": None,
        "interview_questions": None,
        # Selected candidate for details view
        "selected_candidate": None,
        # Errors
        "errors": [],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_state(key: str) -> Any:
    """Get value from session state"""
    return st.session_state.get(key)


def set_state(key: str, value: Any):
    """Set value in session state"""
    st.session_state[key] = value


def clear_results():
    """Clear all results from session state"""
    set_state("results", None)
    set_state("ranked_candidates", None)
    set_state("report", None)
    set_state("interview_questions", None)
    set_state("workflow_state", "idle")
    set_state("processing_status", {})
    set_state("current_node", None)
    set_state("progress", 0)
