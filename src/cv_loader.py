"""
CV PDF loading and text chunking.

Extracts text from uploaded PDFs and splits it into chunks suitable
for embedding and retrieval (RAG).
"""

from io import BytesIO

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract plain text from a PDF file.

    Args:
        pdf_bytes: Raw bytes of the uploaded PDF.

    Returns:
        Full CV text joined across all pages.

    Raises:
        ValueError: If no text could be extracted (e.g. scanned image PDF).
    """
    reader = PdfReader(BytesIO(pdf_bytes))
    page_texts: list[str] = []

    for page in reader.pages:
        text = page.extract_text()
        if text and text.strip():
            page_texts.append(text.strip())

    full_text = "\n\n".join(page_texts).strip()
    if not full_text:
        raise ValueError(
            "Could not extract text from the PDF. "
            "The file may be empty, password-protected, or image-only (scanned)."
        )
    return full_text


def split_cv_into_chunks(
    cv_text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
) -> list[str]:
    """
    Split CV text into overlapping chunks for vector embedding.

    Uses paragraph and sentence boundaries when possible so chunks
    stay semantically coherent.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(cv_text)
    return [chunk.strip() for chunk in chunks if chunk.strip()]
