"""
RAG (Retrieval-Augmented Generation) for CV context.

Embeds CV chunks with a local HuggingFace model (Groq has no embeddings API),
stores them in an ephemeral ChromaDB collection, and retrieves the most
relevant excerpts for a job description.
"""

import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document


def build_cv_vectorstore(
    chunks: list[str],
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> Chroma:
    """
    Create an in-memory Chroma vector store from CV text chunks.

    Uses a local sentence-transformers model for embeddings (free, no API key).
    EphemeralClient keeps everything in memory for the session.
    """
    if not chunks:
        raise ValueError("No CV chunks available to embed.")

    documents = [
        Document(page_content=chunk, metadata={"source": "cv", "chunk_index": i})
        for i, chunk in enumerate(chunks)
    ]

    embeddings = HuggingFaceEmbeddings(model_name=embedding_model)

    client = chromadb.EphemeralClient()
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        client=client,
        collection_name="cv_chunks",
    )
    return vectorstore


def retrieve_relevant_cv_context(
    vectorstore: Chroma,
    job_description: str,
    k: int = 6,
) -> str:
    """
    Retrieve the top-k CV chunks most similar to the job description.

    Returns formatted text blocks ready to inject into the LLM prompt.
    """
    docs = vectorstore.similarity_search(job_description, k=k)
    if not docs:
        return ""

    sections: list[str] = []
    for index, doc in enumerate(docs, start=1):
        sections.append(f"[CV excerpt {index}]\n{doc.page_content}")
    return "\n\n".join(sections)
