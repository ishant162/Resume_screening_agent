"""
UI Components
"""

from .candidate_details import render_candidate_details
from .processing_status import render_processing_status
from .results_dashboard import render_results_dashboard
from .upload_section import render_upload_section

__all__ = [
    "render_upload_section",
    "render_processing_status",
    "results_dashboard",
    "render_candidate_details",
    "render_results_dashboard",
]
