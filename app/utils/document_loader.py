# =============================================================
# NexaSupport AI — Document Loader
# =============================================================
# PURPOSE:
#   Loads raw IT knowledge documents from the data/documents/ folder.
#   Currently supports Markdown (.md) and plain text (.txt) files.
#   Returns a list of Document objects, each containing the raw text
#   and metadata (filename, title, source_type, file_path).
#
# CONCEPT — Why do we need this?
#   Before we can search our IT knowledge base with AI, we need to
#   read all the documents. This module is the "file reader" step.
#   It isolates all file-reading logic in one place so the rest of
#   the pipeline never has to think about file formats.
#
# HOW IT FITS:
#   load_documents() → text_chunker.py → embeddings.py → ChromaDB
# =============================================================

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from loguru import logger


@dataclass
class Document:
    """
    A single loaded document.
    
    Attributes:
        doc_id     : A unique identifier (derived from filename).
        text       : The full raw text content of the document.
        title      : Human-readable title (from first # heading or filename).
        source_file: The original filename (e.g., '01_vpn_troubleshooting.md').
        file_path  : Absolute path to the file.
        source_type: File format — 'markdown', 'text', or 'pdf'.
        metadata   : Any extra key-value pairs we want to attach.
    """
    doc_id: str
    text: str
    title: str
    source_file: str
    file_path: str
    source_type: str
    metadata: dict = field(default_factory=dict)


def _extract_title_from_markdown(text: str, fallback: str) -> str:
    """
    Extract the first H1 heading from a markdown document as the title.
    If no heading is found, return the fallback (filename without extension).
    
    Example:
        text = "# VPN Troubleshooting Guide\n\nOverview..."
        → returns "VPN Troubleshooting Guide"
    """
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback


def load_markdown_file(file_path: Path) -> Optional[Document]:
    """
    Load a single Markdown (.md) or text (.txt) file.
    
    Returns a Document object or None if the file cannot be read.
    """
    try:
        text = file_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return None

    # Derive a clean document ID from the filename (no extension, no spaces)
    doc_id = file_path.stem.replace(" ", "_").lower()

    # Try to extract a proper title from the markdown heading
    fallback_title = file_path.stem.replace("_", " ").title()
    source_type = "markdown" if file_path.suffix == ".md" else "text"
    title = (
        _extract_title_from_markdown(text, fallback_title)
        if source_type == "markdown"
        else fallback_title
    )

    logger.debug(f"Loaded document: '{title}' ({len(text)} chars) from {file_path.name}")

    return Document(
        doc_id=doc_id,
        text=text,
        title=title,
        source_file=file_path.name,
        file_path=str(file_path.resolve()),
        source_type=source_type,
        metadata={
            "filename": file_path.name,
            "title": title,
            "source_type": source_type,
        },
    )


def load_documents(documents_dir: str = "data/documents") -> list[Document]:
    """
    Load all supported documents from the specified directory.
    
    Supported file types: .md, .txt
    (PDF support via PyMuPDF can be added in a later phase)
    
    Args:
        documents_dir: Path to the folder containing raw IT documents.
                       Can be relative (to the project root) or absolute.
    
    Returns:
        A list of Document objects. Empty list if no documents are found.
    
    Example usage:
        docs = load_documents("data/documents")
        for doc in docs:
            print(doc.title, len(doc.text))
    """
    docs_path = Path(documents_dir)

    if not docs_path.exists():
        logger.warning(f"Documents directory not found: {docs_path.resolve()}")
        return []

    # Collect all supported files, sorted alphabetically for reproducibility
    supported_extensions = {".md", ".txt"}
    files = sorted(
        [f for f in docs_path.iterdir() if f.is_file() and f.suffix in supported_extensions]
    )

    if not files:
        logger.warning(f"No supported documents (.md, .txt) found in {docs_path.resolve()}")
        return []

    logger.info(f"Found {len(files)} document(s) in {docs_path.resolve()}")

    documents = []
    for file_path in files:
        doc = load_markdown_file(file_path)
        if doc is not None:
            documents.append(doc)

    logger.info(f"Successfully loaded {len(documents)}/{len(files)} document(s)")
    return documents
