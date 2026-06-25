"""
Job Application Copilot V1 — Streamlit application.
"""

import streamlit as st
from dotenv import load_dotenv

from src.analyzer import analyze_application
from src.cover_letter import generate_cover_letter
from src.interview_prep import generate_interview_prep
from src.llm_client import get_groq_api_key
from src.models import ApplicationRecord, ApplicationStatus
from src.tailoring import tailor_resume
from src.tracker import ApplicationTracker
from src.utils import bullets_to_storage, truncate

load_dotenv()

st.set_page_config(
    page_title="Job Application Copilot",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    div[data-testid="stSidebar"] { background-color: #f8fafc; }
    .skill-match { color: #059669; }
    .skill-missing { color: #dc2626; }
    .skill-weak { color: #d97706; }
    .bullet-card {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

STATUS_OPTIONS: list[ApplicationStatus] = [
    "planned", "applied", "interview", "rejected", "offer"
]
STATUS_LABELS = {
    "planned": "Planned",
    "applied": "Applied",
    "interview": "Interview",
    "rejected": "Rejected",
    "offer": "Offer",
}

tracker = ApplicationTracker()


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def init_session_state() -> None:
    defaults = {
        "cv_text": None,
        "current_app_id": None,
        "company_name": "",
        "job_title": "",
        "job_description": "",
        "applications_list": [],
        "_analysis": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if not st.session_state.applications_list:
        refresh_applications_cache()


def refresh_applications_cache() -> None:
    """Reload saved applications from SQLite into session state."""
    st.session_state.applications_list = tracker.list_all()


def reset_for_new_application() -> None:
    """Clear current application so the next analyze creates a new record."""
    st.session_state.current_app_id = None
    st.session_state.company_name = ""
    st.session_state.job_title = ""
    st.session_state.job_description = ""
    st.session_state._analysis = None


def load_application_into_session(record: ApplicationRecord) -> None:
    """Populate session state from a saved application."""
    st.session_state.current_app_id = record.application_id
    st.session_state.company_name = record.company_name
    st.session_state.job_title = record.job_title
    st.session_state.job_description = record.job_description_text
    if record.cv_text:
        st.session_state.cv_text = record.cv_text
    st.session_state._analysis = None


def get_current_record() -> ApplicationRecord | None:
    """Fetch the currently selected application from the database."""
    app_id = st.session_state.current_app_id
    if not app_id:
        return None
    return tracker.get(app_id)


def save_new_analysis(result) -> ApplicationRecord:
    """Always create a brand-new application record after analysis."""
    record = ApplicationRecord(
        company_name=st.session_state.company_name.strip() or "Unknown Company",
        job_title=st.session_state.job_title.strip() or "Unknown Role",
        job_description_text=st.session_state.job_description.strip(),
        cv_text=result.cv_text,
        extracted_skills=result.jd_extraction.required_skills,
        extracted_requirements=result.jd_extraction.extracted_requirements,
        matching_skills=result.fit_analysis.matching_skills,
        missing_skills=result.fit_analysis.missing_skills,
        weak_matches=result.fit_analysis.weak_matches,
        fit_score=result.fit_analysis.fit_score,
        fit_score_explanation=result.fit_analysis.fit_score_explanation,
    )
    saved = tracker.save(record)
    st.session_state.current_app_id = saved.application_id
    st.session_state._analysis = result
    refresh_applications_cache()
    return saved


def save_current_record(**updates) -> ApplicationRecord:
    """Update the currently selected application."""
    record = get_current_record()
    if not record:
        raise ValueError("No application selected. Run Analyze first.")
    for key, value in updates.items():
        if hasattr(record, key):
            setattr(record, key, value)
    saved = tracker.save(record)
    refresh_applications_cache()
    return saved


def check_api_key() -> bool:
    try:
        get_groq_api_key()
        return True
    except ValueError as exc:
        st.error(str(exc))
        return False


def require_cv_and_jd() -> bool:
    if not st.session_state.cv_text:
        st.warning("Upload your CV in the sidebar.")
        return False
    if not st.session_state.job_description.strip():
        st.warning("Enter a job description in the sidebar.")
        return False
    if not st.session_state.company_name.strip():
        st.warning("Enter the company name in the sidebar.")
        return False
    if not st.session_state.job_title.strip():
        st.warning("Enter the job title in the sidebar.")
        return False
    if not st.session_state.current_app_id:
        st.warning("Run Analyze on the Upload & Analyze tab first.")
        return False
    return True


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### Job Application Copilot")
        st.divider()

        uploaded_cv = st.file_uploader("CV (PDF)", type=["pdf"])
        if uploaded_cv is not None:
            try:
                from src.cv_loader import extract_text_from_pdf

                pdf_bytes = uploaded_cv.read()
                st.session_state._pdf_bytes = pdf_bytes
                st.session_state.cv_text = extract_text_from_pdf(pdf_bytes)
                st.success("CV loaded")
            except Exception as exc:
                st.error(str(exc))
        elif st.session_state.cv_text:
            st.caption("CV ready")

        st.divider()
        st.session_state.company_name = st.text_input(
            "Company",
            value=st.session_state.company_name,
        )
        st.session_state.job_title = st.text_input(
            "Job title",
            value=st.session_state.job_title,
        )
        st.session_state.job_description = st.text_area(
            "Job description",
            value=st.session_state.job_description,
            height=180,
        )

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("New job", use_container_width=True):
                reset_for_new_application()
                st.rerun()
        with col_b:
            if st.button("Refresh list", use_container_width=True):
                refresh_applications_cache()
                st.rerun()

        st.divider()
        st.markdown("**Saved applications**")
        apps: list[ApplicationRecord] = st.session_state.applications_list

        if apps:
            app_ids = [a.application_id for a in apps]
            labels = {
                a.application_id: f"{a.company_name} — {a.job_title} ({STATUS_LABELS[a.status]})"
                for a in apps
            }
            current_index = 0
            if st.session_state.current_app_id in app_ids:
                current_index = app_ids.index(st.session_state.current_app_id)

            picked_id = st.selectbox(
                "Select application",
                options=app_ids,
                index=current_index,
                format_func=lambda x: labels[x],
                key="sidebar_app_picker",
            )
            if picked_id != st.session_state.current_app_id:
                record = tracker.get(picked_id)
                if record:
                    load_application_into_session(record)
                    st.rerun()
        else:
            st.caption("No saved applications yet.")


# ---------------------------------------------------------------------------
# Shared render helpers
# ---------------------------------------------------------------------------

def _render_fit_score(score: int, explanation: str) -> None:
    c1, c2 = st.columns([1, 3])
    with c1:
        st.metric("Fit score", f"{score}/100")
        st.progress(score / 100)
    with c2:
        st.markdown("**Explanation**")
        st.write(explanation)


def _render_skills(required, matching, missing, weak) -> None:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Required skills**")
        for s in required:
            st.markdown(f"- {s}")
    with c2:
        st.markdown("**Matching**")
        for s in matching:
            st.markdown(f'<span class="skill-match">- {s}</span>', unsafe_allow_html=True)
    with c3:
        st.markdown("**Gaps / weak**")
        for s in missing:
            st.markdown(f'<span class="skill-missing">- {s}</span>', unsafe_allow_html=True)
        for s in weak:
            st.markdown(f'<span class="skill-weak">- {s} (weak)</span>', unsafe_allow_html=True)


def _render_bullet_improvements(bullets: list) -> None:
    """Render bullet improvements (dict or legacy string format)."""
    if not bullets:
        st.caption("No bullet improvements yet.")
        return

    for i, item in enumerate(bullets, 1):
        if isinstance(item, str):
            st.markdown(f"**{i}.** {item}")
            continue

        with st.container(border=True):
            st.markdown(f"**Bullet {i}** · Section: {item.get('section', 'Other')}")
            st.markdown(f"**Original:** {item.get('original_bullet', '—')}")
            st.markdown(f"**Revised:** {item.get('revised_bullet', '—')}")
            st.caption(f"Reason: {item.get('reason_for_change', '—')}")


def _render_cover_letter(email: str | None, letter: str | None, sections: dict | None = None) -> None:
    st.markdown("**Application email**")
    st.text_area("email", value=email or "", height=140, label_visibility="collapsed")

    st.markdown("**Cover letter**")
    if sections:
        for label, key in [
            ("Greeting", "greeting"),
            ("Introduction", "introduction"),
            ("Why I fit", "why_fit"),
            ("Relevant skills & projects", "relevant_skills_projects"),
            ("Closing", "closing"),
            ("Sign-off", "sign_off"),
        ]:
            if sections.get(key):
                st.markdown(f"*{label}*")
                st.write(sections[key])
                st.markdown("")
    else:
        st.text_area("letter", value=letter or "", height=360, label_visibility="collapsed")


def _render_interview(qa_list: list[dict]) -> None:
    for i, qa in enumerate(qa_list, 1):
        qtype = qa.get("question_type", "role")
        with st.expander(f"Q{i} [{qtype}] — {qa.get('question', '')}", expanded=(i <= 2)):
            st.markdown(f"**Answer:** {qa.get('suggested_answer', '')}")


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

def tab_upload_analyze() -> None:
    st.subheader("Upload & Analyze")

    if not check_api_key():
        return

    if st.button("Analyze application", type="primary", use_container_width=True):
        if not st.session_state.cv_text:
            st.error("Upload your CV first.")
            return
        if not st.session_state.job_description.strip():
            st.error("Enter a job description.")
            return

        with st.spinner("Analyzing…"):
            try:
                result = analyze_application(
                    job_description=st.session_state.job_description,
                    company_name=st.session_state.company_name,
                    job_title=st.session_state.job_title,
                    pdf_bytes=st.session_state.get("_pdf_bytes"),
                    cv_text=st.session_state.cv_text,
                )
                st.session_state.cv_text = result.cv_text
                saved = save_new_analysis(result)
                st.success(f"Saved: {saved.company_name} — {saved.job_title}")
                st.rerun()
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")

    result = st.session_state.get("_analysis")
    record = get_current_record()

    if result:
        fit = result.fit_analysis
        jd = result.jd_extraction
        _render_fit_score(fit.fit_score, fit.fit_score_explanation)
        _render_skills(jd.required_skills, fit.matching_skills, fit.missing_skills, fit.weak_matches)
        if jd.extracted_requirements:
            st.markdown("**Key requirements**")
            for req in jd.extracted_requirements:
                st.markdown(f"- {req}")
    elif record and record.fit_score is not None:
        _render_fit_score(record.fit_score, record.fit_score_explanation or "")
        _render_skills(
            record.extracted_skills,
            record.matching_skills,
            record.missing_skills,
            record.weak_matches,
        )
        if record.extracted_requirements:
            st.markdown("**Key requirements**")
            for req in record.extracted_requirements:
                st.markdown(f"- {req}")


def tab_resume_tailoring() -> None:
    st.subheader("Resume Tailoring")

    if not check_api_key() or not require_cv_and_jd():
        return

    record = get_current_record()

    if record and record.tailored_summary:
        st.markdown("**Tailored summary**")
        st.write(record.tailored_summary)
        st.markdown("**Bullet improvements**")
        _render_bullet_improvements(record.tailored_resume_bullets)

    if st.button("Generate tailoring", type="primary", use_container_width=True):
        with st.spinner("Tailoring resume…"):
            try:
                result = tailor_resume(
                    cv_text=st.session_state.cv_text,
                    job_description=st.session_state.job_description,
                    company_name=st.session_state.company_name,
                    job_title=st.session_state.job_title,
                    required_skills=record.extracted_skills if record else None,
                )
                bullet_dicts = bullets_to_storage(result.improved_bullets)
                save_current_record(
                    fit_score=result.fit_analysis.fit_score,
                    fit_score_explanation=result.fit_analysis.fit_score_explanation,
                    matching_skills=result.fit_analysis.matching_skills,
                    missing_skills=result.fit_analysis.missing_skills,
                    weak_matches=result.fit_analysis.weak_matches,
                    tailored_summary=result.tailored_summary,
                    tailored_resume_bullets=bullet_dicts,
                )
                st.rerun()
            except Exception as exc:
                st.error(f"Tailoring failed: {exc}")


def tab_cover_letter() -> None:
    st.subheader("Cover Letter")

    if not check_api_key() or not require_cv_and_jd():
        return

    record = get_current_record()

    if record and record.cover_letter:
        _render_cover_letter(record.cover_letter_email, record.cover_letter)

    if st.button("Generate cover letter", type="primary", use_container_width=True):
        with st.spinner("Writing cover letter…"):
            try:
                bullets_for_prompt = record.tailored_resume_bullets if record else None
                if bullets_for_prompt:
                    bullets_for_prompt = [
                        b.get("revised_bullet", b) if isinstance(b, dict) else b
                        for b in bullets_for_prompt
                    ]

                result = generate_cover_letter(
                    cv_text=st.session_state.cv_text,
                    job_description=st.session_state.job_description,
                    company_name=st.session_state.company_name,
                    job_title=st.session_state.job_title,
                    tailored_summary=record.tailored_summary if record else "",
                    tailored_bullets=bullets_for_prompt,
                )
                save_current_record(
                    cover_letter=result.full_cover_letter,
                    cover_letter_email=result.email_message,
                )
                _render_cover_letter(
                    result.email_message,
                    result.full_cover_letter,
                    result.sections.model_dump(),
                )
            except Exception as exc:
                st.error(f"Cover letter generation failed: {exc}")


def tab_interview_prep() -> None:
    st.subheader("Interview Prep")

    if not check_api_key() or not require_cv_and_jd():
        return

    record = get_current_record()

    if record and record.interview_questions_and_answers:
        _render_interview(record.interview_questions_and_answers)

    if st.button("Generate interview prep", type="primary", use_container_width=True):
        with st.spinner("Generating questions…"):
            try:
                result = generate_interview_prep(
                    cv_text=st.session_state.cv_text,
                    job_description=st.session_state.job_description,
                    company_name=st.session_state.company_name,
                    job_title=st.session_state.job_title,
                    required_skills=record.extracted_skills if record else None,
                )
                qa_list = [q.model_dump() for q in result.questions]
                save_current_record(interview_questions_and_answers=qa_list)
                st.rerun()
            except Exception as exc:
                st.error(f"Interview prep failed: {exc}")


def tab_application_tracker() -> None:
    st.subheader("Application Tracker")

    apps = st.session_state.applications_list

    if not apps:
        st.info("No applications yet. Analyze a job on the Upload & Analyze tab.")
        return

    c1, c2, c3, c4, c5 = st.columns(5)
    counts = {s: sum(1 for a in apps if a.status == s) for s in STATUS_OPTIONS}
    c1.metric("Total", len(apps))
    c2.metric("Applied", counts["applied"])
    c3.metric("Interview", counts["interview"])
    c4.metric("Offers", counts["offer"])
    c5.metric("Rejected", counts["rejected"])

    for app in apps:
        with st.container(border=True):
            hc1, hc2, hc3 = st.columns([3, 2, 1])
            with hc1:
                st.markdown(f"**{app.company_name}**")
                st.caption(f"{app.job_title} · {app.date_created[:10]}")
            with hc2:
                if app.fit_score is not None:
                    st.metric("Fit", f"{app.fit_score}/100")
                new_status = st.selectbox(
                    "Status",
                    STATUS_OPTIONS,
                    index=STATUS_OPTIONS.index(app.status),
                    format_func=lambda s: STATUS_LABELS[s],
                    key=f"status_{app.application_id}",
                )
                if new_status != app.status:
                    tracker.set_status(app.application_id, new_status)
                    refresh_applications_cache()
                    st.rerun()
            with hc3:
                if st.button("Open", key=f"open_{app.application_id}", use_container_width=True):
                    load_application_into_session(app)
                    st.rerun()
                if st.button("Delete", key=f"del_{app.application_id}", use_container_width=True):
                    tracker.delete(app.application_id)
                    if st.session_state.current_app_id == app.application_id:
                        reset_for_new_application()
                    refresh_applications_cache()
                    st.rerun()

            with st.expander("Details"):
                st.caption(truncate(app.job_description_text, 200))
                if app.extracted_skills:
                    st.markdown("Skills: " + ", ".join(app.extracted_skills[:6]))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    init_session_state()
    render_sidebar()

    st.title("Job Application Copilot")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Upload & Analyze",
        "Resume Tailoring",
        "Cover Letter",
        "Interview Prep",
        "Application Tracker",
    ])

    with tab1:
        tab_upload_analyze()
    with tab2:
        tab_resume_tailoring()
    with tab3:
        tab_cover_letter()
    with tab4:
        tab_interview_prep()
    with tab5:
        tab_application_tracker()


if __name__ == "__main__":
    main()
