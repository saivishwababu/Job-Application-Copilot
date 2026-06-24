# Job Application Copilot

A Streamlit MVP that helps students and job seekers tailor job applications using LangChain, OpenAI, and RAG (Retrieval-Augmented Generation).

Upload your CV (PDF), paste a job description, and get:

1. **Match score** — how well your CV aligns with the role  
2. **Required skills** — from the job description  
3. **Matching skills** — already present in your CV  
4. **Missing skills** — gaps to address  
5. **Tailored resume summary**  
6. **5 improved CV bullet points** (grounded in your real experience)  
7. **Cover letter draft**  
8. **10 interview questions** tailored to the job and your CV  

## How it works

```
CV PDF → extract text → chunk → embed → ChromaDB
                                              ↓
Job description → retrieve relevant CV chunks (RAG)
                                              ↓
                    LLM structured analysis → Streamlit UI
```

The app **never invents experience** — prompts require the model to use only facts from your uploaded CV.

## Prerequisites

- Python 3.10+
- An [OpenAI API key](https://platform.openai.com/api-keys)

## Installation

```bash
# Clone or navigate to the project folder
cd job-application-copilot

# Create and activate a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...
```

## Run the app

```bash
streamlit run app.py
```

Open the URL shown in the terminal (usually `http://localhost:8501`).

## Project structure

```
job-application-copilot/
├── app.py              # Streamlit UI
├── requirements.txt
├── .env.example
├── README.md
└── src/
    ├── cv_loader.py    # PDF extraction and text chunking
    ├── rag.py          # Embeddings + Chroma retrieval
    ├── prompts.py      # LangChain prompt templates
    └── analyzer.py     # Analysis pipeline + structured output
```

## Environment variables

| Variable | Required | Default |
|----------|----------|---------|
| `OPENAI_API_KEY` | Yes | — |
| `OPENAI_MODEL` | No | `gpt-4o-mini` |
| `OPENAI_EMBEDDING_MODEL` | No | `text-embedding-3-small` |

## MVP scope (included)

- PDF CV upload  
- Job description input  
- RAG over CV chunks  
- Structured AI analysis  
- Clean Streamlit output sections  

## Out of scope (future)

- User login / accounts  
- Dashboard  
- Gmail / calendar integration  
- Database persistence  

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Could not extract text from PDF" | Use a text-based PDF, not a scanned image |
| Missing API key error | Create `.env` from `.env.example` and set `OPENAI_API_KEY` |
| Slow first run | Chroma and LangChain may download models on first use |

## License

MIT — use freely for learning and personal projects.
