# =============================================================
# NexaSupport AI — Text Chunker
# =============================================================
# PURPOSE:
#   Takes a loaded Document and splits its text into smaller, 
#   overlapping chunks suitable for embedding and vector search.
#
# CONCEPT — Why do we chunk?
#   LLMs and embedding models have a maximum input length (context window).
#   A full IT policy document might be 5,000 words — too long to embed as one
#   piece and too long to send to an LLM as context. Instead, we split
#   documents into smaller overlapping pieces (~500 characters each).
#
#   OVERLAP explained simply:
#     "The VPN gateway IP is 10.0.0.1. | Connect using SSL mode."
#     If chunk 1 ends at "10.0.0.1" and chunk 2 starts at "Connect",
#     we lose the connection. With overlap, chunk 2 starts a bit earlier
#     so it still includes "VPN gateway IP" — preserving context across
#     chunk boundaries.
#
# HOW IT FITS:
#   document_loader.py → [this file] → embeddings.py → ChromaDB
# =============================================================

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger

from app.utils.document_loader import Document


@dataclass
class Chunk:
    """
    A single text chunk produced from a Document.

    Attributes:
        chunk_id      : A unique, deterministic ID (hash of content).
        text          : The raw text content of this chunk.
        doc_id        : The ID of the parent document.
        source_file   : The original filename.
        title         : The document title.
        chunk_index   : Position of this chunk within the document (0-indexed).
        total_chunks  : Total number of chunks from the same document.
        char_count    : Number of characters in this chunk.
        metadata      : All searchable metadata (used by ChromaDB for filtering).
    """
    chunk_id: str
    text: str
    doc_id: str
    source_file: str
    title: str
    chunk_index: int
    total_chunks: int
    char_count: int
    metadata: dict = field(default_factory=dict)


def _generate_chunk_id(doc_id: str, chunk_index: int, text: str) -> str:
    """
    Generate a deterministic, unique ID for a chunk.
    
    We use a short hash of the content so:
    1. The same document always produces the same chunk IDs (reproducible indexing).
    2. IDs are short enough to be readable.
    
    Format: "{doc_id}_{index}_{short_hash}"
    Example: "01_vpn_troubleshooting_0_a3f9b2"
    """
    content_hash = hashlib.md5(text.encode()).hexdigest()[:6]
    return f"{doc_id}_{chunk_index}_{content_hash}"


def chunk_document(
    document: Document,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
) -> list[Chunk]:
    """
    Split a single Document into a list of Chunks.
    
    Args:
        document    : A Document object from document_loader.py.
        chunk_size  : Target size of each chunk in characters.
                      512 chars ≈ 100–130 tokens (LLM-friendly size).
        chunk_overlap: Number of characters to overlap between consecutive chunks.
                      50 chars ≈ 1–2 sentences, enough to preserve context.
    
    Returns:
        A list of Chunk objects.
    
    Why RecursiveCharacterTextSplitter?
        It tries to split on natural boundaries in this order:
        paragraph breaks → sentence breaks → word breaks → character breaks.
        This produces more semantically coherent chunks than splitting at
        exact character counts.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        # Try these separators in order: paragraphs → lines → sentences → words
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    # Split the raw text
    raw_chunks = splitter.split_text(document.text)

    if not raw_chunks:
        logger.warning(f"No chunks produced for document: {document.doc_id}")
        return []

    total = len(raw_chunks)
    chunks = []

    for idx, chunk_text in enumerate(raw_chunks):
        chunk_text = chunk_text.strip()
        if not chunk_text:
            continue  # Skip empty chunks (can happen with repeated whitespace)

        chunk_id = _generate_chunk_id(document.doc_id, idx, chunk_text)

        # Build metadata — everything useful for filtering and citation
        metadata = {
            "chunk_id": chunk_id,
            "doc_id": document.doc_id,
            "source_file": document.source_file,
            "title": document.title,
            "chunk_index": idx,
            "total_chunks": total,
            "source_type": document.source_type,
        }
        # Merge any extra metadata from the document itself
        metadata.update(document.metadata)

        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                text=chunk_text,
                doc_id=document.doc_id,
                source_file=document.source_file,
                title=document.title,
                chunk_index=idx,
                total_chunks=total,
                char_count=len(chunk_text),
                metadata=metadata,
            )
        )

    logger.debug(
        f"Document '{document.title}' → {len(chunks)} chunks "
        f"(avg {sum(c.char_count for c in chunks) // max(len(chunks), 1)} chars/chunk)"
    )
    return chunks


def chunk_documents(
    documents: list[Document],
    chunk_size: int = 512,
    chunk_overlap: int = 50,
) -> list[Chunk]:
    """
    Chunk all documents in a list.
    
    Args:
        documents   : List of Document objects.
        chunk_size  : Target chunk size in characters.
        chunk_overlap: Overlap in characters.
    
    Returns:
        A flat list of all Chunks across all documents.
    """
    all_chunks: list[Chunk] = []
    for doc in documents:
        chunks = chunk_document(doc, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        all_chunks.extend(chunks)

    logger.info(
        f"Chunking complete: {len(documents)} document(s) → {len(all_chunks)} total chunk(s)"
    )
    return all_chunks


def save_chunks_to_json(chunks: list[Chunk], output_path: str = "data/processed/chunks.json") -> None:
    """
    Save all chunks to a JSON file for inspection and caching.
    
    This lets us:
    1. Inspect what the chunker produced without re-running it.
    2. Cache the output so the indexing step (build_index.py) doesn't
       need to re-read and re-chunk the documents every time.
    
    Args:
        chunks     : List of Chunk objects.
        output_path: Path to write the JSON file.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Convert Chunk dataclasses to plain dicts for JSON serialization
    data = [
        {
            "chunk_id": c.chunk_id,
            "text": c.text,
            "doc_id": c.doc_id,
            "source_file": c.source_file,
            "title": c.title,
            "chunk_index": c.chunk_index,
            "total_chunks": c.total_chunks,
            "char_count": c.char_count,
            "metadata": c.metadata,
        }
        for c in chunks
    ]

    with open(output, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(chunks)} chunks to {output.resolve()}")


def load_chunks_from_json(input_path: str = "data/processed/chunks.json") -> list[Chunk]:
    """
    Load previously saved chunks from a JSON file.
    
    Used by build_index.py to avoid re-chunking documents on every run.
    
    Returns:
        A list of Chunk objects reconstructed from the saved JSON.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        logger.error(f"Chunks file not found: {input_file.resolve()}")
        return []

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunks = [
        Chunk(
            chunk_id=item["chunk_id"],
            text=item["text"],
            doc_id=item["doc_id"],
            source_file=item["source_file"],
            title=item["title"],
            chunk_index=item["chunk_index"],
            total_chunks=item["total_chunks"],
            char_count=item["char_count"],
            metadata=item["metadata"],
        )
        for item in data
    ]

    logger.info(f"Loaded {len(chunks)} chunks from {input_file.resolve()}")
    return chunks
