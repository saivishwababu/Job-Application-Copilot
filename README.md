# Job Application Copilot V1

A Streamlit app that helps students and job seekers manage job applications end-to-end: analyze fit, tailor resumes, write cover letters, prepare for interviews, and track every application.

## Features (V1)

| Tab | What it does |
|-----|--------------|
| **Upload & Analyze** | Extract JD skills/requirements, compare against CV, fit score + gaps |
| **Resume Tailoring** | Tailored summary + 5 improved bullets grounded in your CV |
| **Cover Letter** | Short application email + full cover letter |
| **Interview Prep** | Technical, behavioral, and role questions with suggested answers |
| **Application Tracker** | SQLite-backed tracker with status pipeline |

## Prerequisites

- Python 3.10+
- [Groq API key](https://console.groq.com/keys)

## Installation

```bash
cd job-application-copilot

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env and set GROQ_API_KEY=gsk-...
```

## Run

```bash
streamlit run app.py
```

Open `http://localhost:8501`.

## Environment variables

| Variable | Required | Default |
|----------|----------|---------|
| `GROQ_API_KEY` | Yes | — |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` |
| `EMBEDDING_MODEL` | No | `sentence-transformers/all-MiniLM-L6-v2` |

## Project structure

```
job-application-copilot/
├── app.py                  # Streamlit UI (5 tabs)
├── requirements.txt
├── .env.example
├── README.md
├── data/                   # SQLite DB (auto-created, gitignored)
└── src/
    ├── llm_client.py       # Centralized Groq client
    ├── cv_loader.py        # PDF extraction + chunking
    ├── cv_context.py       # RAG context builder
    ├── rag.py              # Chroma + local embeddings
    ├── jd_parser.py        # JD skill/requirement extraction
    ├── analyzer.py         # Upload & Analyze pipeline
    ├── tailoring.py        # Resume tailoring
    ├── cover_letter.py     # Email + cover letter
    ├── interview_prep.py   # Interview Q&A
    ├── tracker.py          # Application tracker API
    ├── storage.py          # SQLite persistence
    ├── models.py           # Pydantic schemas
    ├── prompts.py          # All LLM prompts
    └── utils.py            # Shared helpers
```

## Workflow

1. **Upload CV** (sidebar) and enter company, title, and job description.
2. **Upload & Analyze** — run analysis; results are saved to SQLite automatically.
3. **Resume Tailoring** — generate/regenerate tailored summary and bullets.
4. **Cover Letter** — generate email + full letter (uses tailored content if available).
5. **Interview Prep** — generate questions with CV-grounded answers.
6. **Application Tracker** — view all apps, update status (`planned → applied → interview → rejected/offer`), reopen or delete.

## Persistence

Applications are stored in `data/applications.db` (SQLite). Each record includes company, role, JD, fit score, tailored content, cover letter, and interview prep.

## License

MIT
