"""
Job Application Copilot — Streamlit MVP

Upload a CV (PDF), paste a job description, and get AI-powered
tailoring suggestions grounded in your actual resume.
"""

import os

import streamlit as st
from dotenv import load_dotenv

from src.analyzer import JobApplicationAnalysis, analyze_application

# Load environment variables from .env (OPENAI_API_KEY, optional model overrides)
load_dotenv()

st.set_page_config(
    page_title="Job Application Copilot",
    page_icon="📋",
    layout="wide",
)

st.title("📋 Job Application Copilot")
st.markdown(
    "Upload your CV and paste a job description to get a match score, "
    "skill gap analysis, tailored summary, improved bullets, cover letter, "
    "and interview questions — **based only on your real CV**."
)


def render_analysis(result: JobApplicationAnalysis) -> None:
    """Display structured analysis output in labeled Streamlit sections."""
    st.header("Analysis Results")

    # 1. Match score
    st.subheader("1. Match Score")
    st.metric(label="CV ↔ Job Match", value=f"{result.match_score}%")
    st.progress(result.match_score / 100)

    # 2 & 3. Skills columns
    col_required, col_matching = st.columns(2)
    with col_required:
        st.subheader("2. Skills Required (Job)")
        if result.required_skills:
            for skill in result.required_skills:
                st.markdown(f"- {skill}")
        else:
            st.info("No required skills identified.")

    with col_matching:
        st.subheader("3. Skills Already in Your CV")
        if result.matching_skills:
            for skill in result.matching_skills:
                st.markdown(f"- ✅ {skill}")
        else:
            st.info("No direct skill matches found.")

    # 4. Missing skills
    st.subheader("4. Missing Skills / Keywords")
    if result.missing_skills:
        for skill in result.missing_skills:
            st.markdown(f"- ⚠️ {skill}")
    else:
        st.success("No major skill gaps detected.")

    # 5. Tailored summary
    st.subheader("5. Tailored Resume Summary")
    st.write(result.tailored_summary)

    # 6. Improved bullets
    st.subheader("6. Improved CV Bullet Points")
    for index, bullet in enumerate(result.improved_bullets, start=1):
        st.markdown(f"{index}. {bullet}")

    # 7. Cover letter
    st.subheader("7. Cover Letter Draft")
    st.text_area(
        label="Cover letter",
        value=result.cover_letter,
        height=280,
        label_visibility="collapsed",
    )

    # 8. Interview questions
    st.subheader("8. Interview Questions")
    for index, question in enumerate(result.interview_questions, start=1):
        st.markdown(f"{index}. {question}")


# --- Sidebar: inputs ---
with st.sidebar:
    st.header("Inputs")
    uploaded_cv = st.file_uploader(
        "Upload your CV (PDF)",
        type=["pdf"],
        help="Text-based PDFs work best. Scanned/image PDFs may fail.",
    )
    job_description = st.text_area(
        "Paste the job description",
        height=320,
        placeholder="Paste the full job posting here…",
    )
    analyze_clicked = st.button("Analyze Application", type="primary", use_container_width=True)

    st.divider()
    st.caption("Requires OPENAI_API_KEY in a `.env` file. See README for setup.")

# --- Main area: validation + analysis ---
if analyze_clicked:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key or api_key.strip() in ("", "sk-your-openai-api-key-here"):
        st.error(
            "OpenAI API key is missing. Copy `.env.example` to `.env` "
            "and set your `OPENAI_API_KEY`."
        )
    elif uploaded_cv is None:
        st.error("Please upload your CV as a PDF before analyzing.")
    elif not job_description or not job_description.strip():
        st.error("Please paste the target job description.")
    else:
        with st.spinner("Analyzing your application… (extracting CV, retrieving context, calling AI)"):
            try:
                pdf_bytes = uploaded_cv.read()
                analysis = analyze_application(
                    pdf_bytes=pdf_bytes,
                    job_description=job_description,
                    api_key=api_key,
                )
                render_analysis(analysis)
            except ValueError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Something went wrong during analysis: {exc}")
                st.caption("Check your API key, network connection, and that the PDF contains extractable text.")
else:
    st.info("Upload a CV and job description in the sidebar, then click **Analyze Application**.")
