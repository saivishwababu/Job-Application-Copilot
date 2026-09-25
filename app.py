"""
Job Application Copilot — Premium Streamlit Web Application.
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
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS for modern design system
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Global enhancements */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar container styling */
    div[data-testid="stSidebar"] {
        padding-top: 1rem;
    }
    
    /* Navigation Bar styling */
    .nav-container {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid rgba(128, 128, 128, 0.2);
        flex-wrap: wrap;
    }

    /* Badges & Chips */
    .skill-chip {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.825rem;
        font-weight: 500;
        margin: 0.2rem 0.3rem 0.2rem 0;
        line-height: 1.3;
    }
    .skill-match {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.35);
    }
    .skill-missing {
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.35);
    }
    .skill-weak {
        background-color: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.35);
    }

    /* Score Card */
    .score-box {
        border-radius: 12px;
        padding: 1.25rem;
        border: 1px solid rgba(128, 128, 128, 0.2);
        background: rgba(128, 128, 128, 0.05);
        margin-bottom: 1.5rem;
    }

    /* Bullet Cards */
    .bullet-card {
        border-radius: 10px;
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(128, 128, 128, 0.2);
        background: rgba(128, 128, 128, 0.03);
    }
    .bullet-diff-orig {
        color: #888888;
        text-decoration: line-through;
        font-size: 0.95rem;
        margin-bottom: 0.4rem;
    }
    .bullet-diff-new {
        color: #10b981;
        font-weight: 500;
        font-size: 1rem;
        margin-bottom: 0.4rem;
    }
    .bullet-tag {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        background: rgba(99, 102, 241, 0.15);
        color: #6366f1;
        margin-bottom: 0.5rem;
    }

    /* Quick action buttons row */
    .action-row {
        display: flex;
        gap: 0.75rem;
        margin-top: 1.25rem;
        flex-wrap: wrap;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

STATUS_OPTIONS: list[ApplicationStatus] = [
    "planned", "applied", "interview", "rejected", "offer"
]
STATUS_LABELS = {
    "planned": "📋 Planned",
    "applied": "🚀 Applied",
    "interview": "🎯 Interview",
    "rejected": "❌ Rejected",
    "offer": "🎉 Offer",
}

NAV_TABS = [
    "Upload & Analyze",
    "Resume Tailoring",
    "Cover Letter",
    "Interview Prep",
    "Application Tracker",
from src.tracker import ApplicationTracker, SessionTracker


def get_tracker() -> SessionTracker:
    if "_session_applications" not in st.session_state:
        st.session_state._session_applications = {}
    return SessionTracker(st.session_state._session_applications)


# ---------------------------------------------------------------------------
# Session State & URL Query Parameter Synchronization
# ---------------------------------------------------------------------------

def _get_query_param(key: str) -> str | None:
    try:
        val = st.query_params.get(key)
        if isinstance(val, list):
            return val[0] if val else None
        return val
    except Exception:
        return None


def _set_query_param(key: str, val: str) -> None:
    try:
        st.query_params[key] = val
    except Exception:
        pass


def _del_query_param(key: str) -> None:
    try:
        if key in st.query_params:
            del st.query_params[key]
    except Exception:
        pass


def init_session_state() -> None:
    url_app_id = _get_query_param("app_id")
    url_tab = _get_query_param("tab")

    defaults = {
        "cv_text": None,
        "current_app_id": None,
        "company_name": "",
        "job_title": "",
        "job_description": "",
        "applications_list": [],
        "_analysis": None,
        "active_tab": NAV_TABS[0],
        "_session_applications": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if not st.session_state.applications_list:
        refresh_applications_cache()

    # Load from URL if app_id is passed and not loaded yet
    if url_app_id and url_app_id != st.session_state.current_app_id:
        record = get_tracker().get(url_app_id)
        if record:
            load_application_into_session(record, switch_tab=False)

    if url_tab and url_tab in NAV_TABS:
        st.session_state.active_tab = url_tab


def set_active_tab(tab_name: str) -> None:
    st.session_state.active_tab = tab_name
    _set_query_param("tab", tab_name)


def refresh_applications_cache() -> None:
    st.session_state.applications_list = get_tracker().list_all()


def reset_for_new_application() -> None:
    """Clear inputs to start analyzing a brand new application."""
    st.session_state.current_app_id = None
    st.session_state.company_name = ""
    st.session_state.job_title = ""
    st.session_state.job_description = ""
    st.session_state._analysis = None
    st.session_state.active_tab = "Upload & Analyze"
    _del_query_param("app_id")
    _set_query_param("tab", "Upload & Analyze")


def load_application_into_session(record: ApplicationRecord, switch_tab: bool = True, target_tab: str = "Upload & Analyze") -> None:
    st.session_state.current_app_id = record.application_id
    st.session_state.company_name = record.company_name
    st.session_state.job_title = record.job_title
    st.session_state.job_description = record.job_description_text
    if record.cv_text:
        st.session_state.cv_text = record.cv_text
    st.session_state._analysis = None
    _set_query_param("app_id", record.application_id)
    if switch_tab:
        set_active_tab(target_tab)


def get_current_record() -> ApplicationRecord | None:
    app_id = st.session_state.current_app_id
    if not app_id:
        return None
    return get_tracker().get(app_id)


def save_new_analysis(result) -> ApplicationRecord:
    record = ApplicationRecord(
        company_name=st.session_state.company_name.strip() or "Target Company",
        job_title=st.session_state.job_title.strip() or "Target Role",
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
    saved = get_tracker().save(record)
    st.session_state.current_app_id = saved.application_id
    st.session_state._analysis = result
    _set_query_param("app_id", saved.application_id)
    refresh_applications_cache()
    return saved


def save_current_record(**updates) -> ApplicationRecord:
    record = get_current_record()
    if not record:
        raise ValueError("No application selected. Run Analyze first.")
    for key, value in updates.items():
        if hasattr(record, key):
            setattr(record, key, value)
    saved = get_tracker().save(record)
    refresh_applications_cache()
    return saved


def check_api_key() -> bool:
    try:
        get_groq_api_key()
        return True
    except ValueError as exc:
        st.error(f"⚠️ {exc}")
        return False


def require_cv_and_jd() -> bool:
    if not st.session_state.cv_text:
        st.warning("📄 Please upload your CV in the sidebar.")
        return False
    if not st.session_state.job_description.strip():
        st.warning("📝 Please enter a Job Description in the sidebar.")
        return False
    if not st.session_state.current_app_id:
        st.info("💡 Run 'Analyze Application' on the **Upload & Analyze** tab first.")
        if st.button("👉 Go to Upload & Analyze", key="goto_analyze_btn"):
            set_active_tab("Upload & Analyze")
            st.rerun()
        return False
    return True


# ---------------------------------------------------------------------------
# Sidebar (Clean, Modern Redesign)
# ---------------------------------------------------------------------------

def render_sidebar() -> None:
    with st.sidebar:
        st.title("💼 Job Copilot")
        st.caption("AI-Powered Application Assistant")

        # Top Action: Create New or Pick Saved
        if st.button("➕ Start New Application", use_container_width=True, type="primary"):
            reset_for_new_application()
            st.rerun()

        st.divider()

        # Saved Applications selector
        apps = st.session_state.applications_list
        if apps:
            app_ids = [a.application_id for a in apps]
            labels = {
                a.application_id: f"{a.company_name} — {a.job_title} ({STATUS_LABELS.get(a.status, a.status)})"
                for a in apps
            }
            options = ["__new__", *app_ids]
            
            cur_idx = 0
            if st.session_state.current_app_id in app_ids:
                cur_idx = options.index(st.session_state.current_app_id)

            selected_id = st.selectbox(
                "📂 Load Saved Application",
                options=options,
                index=cur_idx,
                format_func=lambda x: "✨ [New Application]" if x == "__new__" else labels.get(x, x),
                help="Switch between saved job applications",
            )
            if selected_id != (st.session_state.current_app_id or "__new__"):
                if selected_id == "__new__":
                    reset_for_new_application()
                else:
                    rec = get_tracker().get(selected_id)
                    if rec:
                        load_application_into_session(rec, switch_tab=False)
                st.rerun()

        st.subheader("📄 Your CV / Resume")
        uploaded_cv = st.file_uploader("Upload CV (PDF)", type=["pdf"], label_visibility="collapsed")
        if uploaded_cv is not None:
            try:
                from src.cv_loader import extract_text_from_pdf
                pdf_bytes = uploaded_cv.read()
                st.session_state._pdf_bytes = pdf_bytes
                st.session_state.cv_text = extract_text_from_pdf(pdf_bytes)
                st.success("✅ CV loaded successfully")
            except Exception as exc:
                st.error(f"Error reading PDF: {exc}")
        elif st.session_state.cv_text:
            st.success("✅ CV loaded & ready")

        st.subheader("🎯 Target Job Details")
        st.session_state.company_name = st.text_input(
            "Company Name",
            value=st.session_state.company_name,
            placeholder="e.g. Google, Stripe, REWE...",
        )
        st.session_state.job_title = st.text_input(
            "Job Title",
            value=st.session_state.job_title,
            placeholder="e.g. AI Engineer, Product Manager...",
        )
        st.session_state.job_description = st.text_area(
            "Job Description (JD)",
            value=st.session_state.job_description,
            height=200,
            placeholder="Paste the full job posting requirements and responsibilities here...",
        )


# ---------------------------------------------------------------------------
# UI Components & Visualizations
# ---------------------------------------------------------------------------

def _render_fit_score(score: int, explanation: str) -> None:
    col_score, col_exp = st.columns([1, 3])
    with col_score:
        st.metric(label="Match Fit Score", value=f"{score} / 100")
        st.progress(score / 100)
    with col_exp:
        st.markdown("**Executive Analysis**")
        st.write(explanation)


def _render_skills(required: list, matching: list, missing: list, weak: list) -> None:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("##### 📌 Key Requirements")
        if required:
            for s in required:
                st.markdown(f"- {s}")
        else:
            st.caption("None extracted")

    with c2:
        st.markdown("##### ✅ Matching Skills")
        if matching:
            html = "".join([f'<span class="skill-chip skill-match">✓ {s}</span>' for s in matching])
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.caption("No direct matches found")

    with c3:
        st.markdown("##### ⚠️ Gaps & Weak Areas")
        html_gaps = "".join([f'<span class="skill-chip skill-missing">✗ {s}</span>' for s in missing])
        html_weak = "".join([f'<span class="skill-chip skill-weak">~ {s} (weak)</span>' for s in weak])
        if html_gaps or html_weak:
            st.markdown(html_gaps + html_weak, unsafe_allow_html=True)
        else:
            st.caption("No significant gaps identified")


def _render_bullet_improvements(bullets: list) -> None:
    if not bullets:
        st.caption("No bullet improvements generated yet.")
        return

    for i, item in enumerate(bullets, 1):
        if isinstance(item, str):
            st.markdown(f"**{i}.** {item}")
            continue

        section = item.get("section", "Experience")
        orig = item.get("original_bullet", "—")
        revised = item.get("revised_bullet", "—")
        reason = item.get("reason_for_change", "")

        st.markdown(
            f"""
            <div class="bullet-card">
                <span class="bullet-tag">{section}</span>
                <div class="bullet-diff-orig"><b>Original:</b> {orig}</div>
                <div class="bullet-diff-new"><b>Tailored:</b> {revised}</div>
                <small style="color: #64748b;"><b>Rationale:</b> {reason}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_cover_letter(email: str | None, letter: str | None, sections: dict | None = None) -> None:
    tab_letter, tab_email = st.tabs(["📄 Full Cover Letter", "✉️ Short Email"])

    with tab_letter:
        if sections:
            for label, key in [
                ("Greeting", "greeting"),
                ("Introduction", "introduction"),
                ("Why I Fit", "why_fit"),
                ("Relevant Skills & Projects", "relevant_skills_projects"),
                ("Closing", "closing"),
                ("Sign-off", "sign_off"),
            ]:
                if sections.get(key):
                    st.markdown(f"**{label}**")
                    st.write(sections[key])
        else:
            st.text_area("Full Letter", value=letter or "", height=350, label_visibility="collapsed")

        if letter:
            st.download_button(
                "📥 Download Cover Letter (.txt)",
                data=letter,
                file_name=f"cover_letter_{st.session_state.company_name or 'application'}.txt",
                mime="text/plain",
            )

    with tab_email:
        st.text_area("Application Email", value=email or "", height=200, label_visibility="collapsed")
        if email:
            st.download_button(
                "📥 Download Email (.txt)",
                data=email,
                file_name=f"email_{st.session_state.company_name or 'application'}.txt",
                mime="text/plain",
            )


def _render_interview(qa_list: list[dict]) -> None:
    for i, qa in enumerate(qa_list, 1):
        qtype = qa.get("question_type", "role").capitalize()
        with st.expander(f"Q{i} [{qtype}] — {qa.get('question', '')}", expanded=(i <= 2)):
            st.markdown(f"💡 **Suggested Answer Strategy:**")
            st.write(qa.get("suggested_answer", ""))


# ---------------------------------------------------------------------------
# Page Views
# ---------------------------------------------------------------------------

def page_upload_analyze() -> None:
    st.header("📊 Upload & Analyze Fit")

    if not check_api_key():
        return

    analyze_clicked = st.button("🚀 Analyze Application Fit", type="primary", use_container_width=True)

    if analyze_clicked:
        if not st.session_state.cv_text:
            st.error("Please upload your CV (PDF) in the sidebar.")
            return
        if not st.session_state.job_description.strip():
            st.error("Please paste the Job Description in the sidebar.")
            return

        with st.spinner("Analyzing CV match against Job Description..."):
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
                st.success(f"🎉 Analysis complete and saved for **{saved.company_name}**!")
                st.rerun()
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")

    # Render results if available
    result = st.session_state.get("_analysis")
    record = get_current_record()

    if result or (record and record.fit_score is not None):
        st.divider()
        fit = result.fit_analysis if result else record
        reqs = result.jd_extraction.extracted_requirements if result else (record.extracted_requirements if record else [])
        skills = result.jd_extraction.required_skills if result else (record.extracted_skills if record else [])

        _render_fit_score(fit.fit_score, fit.fit_score_explanation)
        _render_skills(skills, fit.matching_skills, fit.missing_skills, fit.weak_matches)

        if reqs:
            with st.expander("📋 Detailed Job Requirements List", expanded=False):
                for req in reqs:
                    st.markdown(f"- {req}")

        st.markdown("#### ⚡ Next Steps")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("📝 Tailor Resume Bullets", use_container_width=True):
                set_active_tab("Resume Tailoring")
                st.rerun()
        with c2:
            if st.button("✉️ Draft Cover Letter", use_container_width=True):
                set_active_tab("Cover Letter")
                st.rerun()
        with c3:
            if st.button("🎯 Prepare for Interview", use_container_width=True):
                set_active_tab("Interview Prep")
                st.rerun()


def page_resume_tailoring() -> None:
    st.header("📝 Resume Tailoring")

    if not check_api_key() or not require_cv_and_jd():
        return

    record = get_current_record()

    if st.button("⚡ Generate Tailored Summary & Bullets", type="primary", use_container_width=True):
        with st.spinner("Crafting tailored resume points..."):
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
                st.success("Resume tailoring updated!")
                st.rerun()
            except Exception as exc:
                st.error(f"Tailoring failed: {exc}")

    record = get_current_record()
    if record and record.tailored_summary:
        st.subheader("🎯 Tailored Professional Summary")
        st.info(record.tailored_summary)

        st.subheader("✨ High-Impact Tailored Bullets")
        _render_bullet_improvements(record.tailored_resume_bullets)


def page_cover_letter() -> None:
    st.header("✉️ Cover Letter & Application Email")

    if not check_api_key() or not require_cv_and_jd():
        return

    record = get_current_record()

    if st.button("⚡ Generate Custom Cover Letter", type="primary", use_container_width=True):
        with st.spinner("Writing personalized cover letter..."):
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
                st.success("Cover letter generated!")
                st.rerun()
            except Exception as exc:
                st.error(f"Cover letter generation failed: {exc}")

    record = get_current_record()
    if record and (record.cover_letter or record.cover_letter_email):
        _render_cover_letter(record.cover_letter_email, record.cover_letter)


def page_interview_prep() -> None:
    st.header("🎯 Interview Preparation")

    if not check_api_key() or not require_cv_and_jd():
        return

    record = get_current_record()

    if st.button("⚡ Generate Interview Questions & Answers", type="primary", use_container_width=True):
        with st.spinner("Predicting role questions and suggested answers..."):
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
                st.success("Interview prep generated!")
                st.rerun()
            except Exception as exc:
                st.error(f"Interview prep failed: {exc}")

    record = get_current_record()
    if record and record.interview_questions_and_answers:
        _render_interview(record.interview_questions_and_answers)


def page_application_tracker() -> None:
    st.header("📂 Application Tracker")

    apps = st.session_state.applications_list

    if not apps:
        st.info("No applications tracked yet. Start by analyzing a job on the **Upload & Analyze** page.")
        return

    # Metrics row
    c1, c2, c3, c4, c5 = st.columns(5)
    counts = {s: sum(1 for a in apps if a.status == s) for s in STATUS_OPTIONS}
    c1.metric("Total Applications", len(apps))
    c2.metric("Applied", counts["applied"])
    c3.metric("Interviews", counts["interview"])
    c4.metric("Offers", counts["offer"])
    c5.metric("Rejected", counts["rejected"])

    st.divider()

    for app in apps:
        with st.container(border=True):
            hc1, hc2, hc3 = st.columns([3, 2, 2])
            with hc1:
                st.markdown(f"### {app.company_name}")
                st.markdown(f"**{app.job_title}** · *Created: {app.date_created[:10]}*")
            with hc2:
                if app.fit_score is not None:
                    st.metric("Fit Score", f"{app.fit_score}%")
                new_status = st.selectbox(
                    "Status",
                    STATUS_OPTIONS,
                    index=STATUS_OPTIONS.index(app.status),
                    format_func=lambda s: STATUS_LABELS[s],
                    key=f"tracker_status_{app.application_id}",
                )
                if new_status != app.status:
                    get_tracker().set_status(app.application_id, new_status)
                    refresh_applications_cache()
                    st.rerun()
            with hc3:
                st.write("")
                if st.button("📂 Open Application", key=f"open_btn_{app.application_id}", use_container_width=True, type="primary"):
                    load_application_into_session(app, switch_tab=True, target_tab="Upload & Analyze")
                    st.rerun()
                if st.button("🗑️ Delete", key=f"del_btn_{app.application_id}", use_container_width=True):
                    get_tracker().delete(app.application_id)
                    if st.session_state.current_app_id == app.application_id:
                        reset_for_new_application()
                    refresh_applications_cache()
                    st.rerun()

            with st.expander("Job Description Preview"):
                st.caption(truncate(app.job_description_text, 250))
                if app.extracted_skills:
                    st.markdown("**Skills:** " + ", ".join(app.extracted_skills[:8]))

    # Export option
    st.divider()
    import json
    apps_export = [a.model_dump() for a in apps]
    st.download_button(
        "📥 Export My Tracked Applications (JSON)",
        data=json.dumps(apps_export, indent=2, ensure_ascii=False),
        file_name="my_job_applications.json",
        mime="application/json",
        help="Download your session's job applications data to your computer",
    )


# ---------------------------------------------------------------------------
# Main App Execution
# ---------------------------------------------------------------------------

def main() -> None:
    init_session_state()
    render_sidebar()

    # Interactive dynamic navigation
    if hasattr(st, "pills"):
        selected_tab = st.pills(
            "Navigation",
            options=NAV_TABS,
            default=st.session_state.active_tab if st.session_state.active_tab in NAV_TABS else NAV_TABS[0],
            label_visibility="collapsed",
        )
    elif hasattr(st, "segmented_control"):
        selected_tab = st.segmented_control(
            "Navigation",
            options=NAV_TABS,
            default=st.session_state.active_tab if st.session_state.active_tab in NAV_TABS else NAV_TABS[0],
            label_visibility="collapsed",
        )
    else:
        selected_tab = st.radio(
            "Navigation",
            options=NAV_TABS,
            index=NAV_TABS.index(st.session_state.active_tab) if st.session_state.active_tab in NAV_TABS else 0,
            horizontal=True,
            label_visibility="collapsed",
        )

    # Sync tab state if changed by user click
    if selected_tab and selected_tab != st.session_state.active_tab:
        set_active_tab(selected_tab)
        st.rerun()

    # Route to active page
    current_tab = st.session_state.active_tab

    if current_tab == "Upload & Analyze":
        page_upload_analyze()
    elif current_tab == "Resume Tailoring":
        page_resume_tailoring()
    elif current_tab == "Cover Letter":
        page_cover_letter()
    elif current_tab == "Interview Prep":
        page_interview_prep()
    elif current_tab == "Application Tracker":
        page_application_tracker()
    else:
        page_upload_analyze()


if __name__ == "__main__":
    main()
