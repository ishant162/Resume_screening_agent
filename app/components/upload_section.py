"""
Upload Section Component

Handles file uploads and workflow configuration.
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from app.utils.state_manager import set_state


def render_upload_section():
    """Render the upload and configuration section"""

    st.header("📤 Upload Job Description & Resumes")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📋 Job Description")
        st.markdown("Upload the job description or paste it below")

        # Option 1: Upload file
        job_file = st.file_uploader(
            "Upload Job Description",
            type=["txt", "pdf", "docx"],
            help="Upload job description as .txt, .pdf, or .docx",
            key="job_file_uploader",
        )

        # Option 2: Paste text
        job_text = st.text_area(
            "Or Paste Job Description",
            height=300,
            placeholder="Paste job description here...",
            key="job_text_area",
        )

        # Process job description
        final_job_text = None

        if job_file:
            if job_file.type == "text/plain":
                final_job_text = job_file.read().decode("utf-8")
            elif job_file.type == "application/pdf":
                from src.tools.pdf_extractor import PDFExtractor

                extractor = PDFExtractor()
                final_job_text = extractor.extract_text(job_file.read())

            if final_job_text:
                st.success(f"✅ Loaded from file: {job_file.name}")
                with st.expander("Preview Job Description"):
                    st.text(
                        final_job_text[:500] + "..."
                        if len(final_job_text) > 500
                        else final_job_text
                    )

        elif job_text:
            final_job_text = job_text
            st.info("✏️ Using pasted job description")

    with col2:
        st.subheader("📄 Resumes")
        st.markdown("Upload candidate resumes (PDF format)")

        # Multiple file upload
        resume_files = st.file_uploader(
            "Upload Resumes",
            type=["pdf"],
            accept_multiple_files=True,
            help="Upload one or more PDF resumes",
            key="resume_uploader",
        )

        if resume_files:
            st.success(f"✅ {len(resume_files)} resume(s) uploaded")

            # Show uploaded files
            with st.expander(f"📁 Uploaded Files ({len(resume_files)})"):
                for i, file in enumerate(resume_files, 1):
                    st.text(f"{i}. {file.name} ({file.size / 1024:.1f} KB)")

    st.markdown("---")

    # Configuration options
    st.subheader("⚙️ Configuration")

    col1, col2, col3 = st.columns(3)

    with col1:
        workflow_type = st.radio(
            "Workflow Type",
            options=["Enhanced (Full Analysis)", "Basic (Fast)"],
            index=0,
            help="Enhanced includes web search, GitHub analysis, bias detection, etc.",
        )

    with col2:
        enable_github = st.checkbox(
            "GitHub Analysis",
            value=True,
            help="Analyze GitHub profiles to validate skills",
        )

    with col3:
        enable_web_search = st.checkbox(
            "Company Verification", value=True, help="Search web to verify companies"
        )

    # Advanced options
    with st.expander("🔧 Advanced Options"):
        col1, col2 = st.columns(2)

        with col1:
            enable_bias_detection = st.checkbox("Bias Detection", value=True)
            enable_salary_estimation = st.checkbox("Salary Estimation", value=True)

        with col2:
            enable_ats_scoring = st.checkbox("ATS Scoring", value=True)
            enable_quality_check = st.checkbox("Quality Self-Check", value=True)

    st.markdown("---")

    # Start button
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        start_button = st.button(
            "🚀 Start Screening",
            type="primary",
            use_container_width=True,
            disabled=not (final_job_text and resume_files),
        )

        if not final_job_text:
            st.warning("⚠️ Please provide a job description")
        if not resume_files:
            st.warning("⚠️ Please upload at least one resume")

    # Handle start button
    if start_button and final_job_text and resume_files:
        # Save to session state
        set_state("job_description", final_job_text)
        set_state("resume_files", resume_files)
        set_state("workflow_type", workflow_type)
        set_state(
            "config",
            {
                "enable_github": enable_github,
                "enable_web_search": enable_web_search,
                "enable_bias_detection": enable_bias_detection,
                "enable_salary_estimation": enable_salary_estimation,
                "enable_ats_scoring": enable_ats_scoring,
                "enable_quality_check": enable_quality_check,
            },
        )

        # Update state to processing
        set_state("workflow_state", "processing")
        set_state("current_page", "processing")

        # Trigger processing
        st.rerun()

    # Show example
    st.markdown("---")
    with st.expander("💡 Need sample data?"):
        st.markdown("""
        ### Sample Job Description

        Create a file `data/sample_jobs/ml_engineer.txt`:
```
        Senior Machine Learning Engineer

        We're seeking an experienced ML Engineer to build production AI systems.

        Requirements:
        - 5+ years Python experience
        - Strong TensorFlow or PyTorch knowledge
        - Experience deploying models to production
        - Bachelor's in CS or related field

        Nice to have:
        - LangChain/LangGraph experience
        - AWS/Cloud experience
```

        ### Sample Resumes
        Place sample PDF resumes in `data/sample_resumes/`
        """)
