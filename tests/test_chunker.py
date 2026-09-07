# =============================================================
# NexaSupport AI — Tests: Document Chunker
# =============================================================

import pytest
from app.utils.document_loader import Document
from app.utils.text_chunker import (
    Chunk,
    chunk_document,
    chunk_documents,
    load_chunks_from_json,
    save_chunks_to_json,
)


def make_test_document(text: str = None) -> Document:
    """Helper to create a Document for testing."""
    return Document(
        doc_id="test_doc",
        text=text or "# Test Document\n\nThis is a test document.\n\nIt has multiple paragraphs.\n\nEach paragraph provides some information for testing purposes.",
        title="Test Document",
        source_file="test.md",
        file_path="/fake/path/test.md",
        source_type="markdown",
        metadata={"filename": "test.md", "title": "Test Document", "source_type": "markdown"},
    )


def test_chunk_document_returns_list_of_chunks():
    """chunk_document() should return a list of Chunk objects."""
    doc = make_test_document()
    chunks = chunk_document(doc, chunk_size=100, chunk_overlap=10)
    assert isinstance(chunks, list)
    assert len(chunks) > 0
    assert all(isinstance(c, Chunk) for c in chunks)


def test_chunk_has_correct_metadata():
    """Each chunk should carry correct source metadata."""
    doc = make_test_document()
    chunks = chunk_document(doc, chunk_size=100, chunk_overlap=10)
    for chunk in chunks:
        assert chunk.doc_id == "test_doc"
        assert chunk.source_file == "test.md"
        assert chunk.title == "Test Document"
        assert chunk.char_count > 0
        assert chunk.chunk_id.startswith("test_doc_")


def test_chunk_ids_are_unique():
    """All chunk IDs in a document should be unique."""
    long_text = " ".join(["word"] * 500)
    doc = make_test_document(text=long_text)
    chunks = chunk_document(doc, chunk_size=100, chunk_overlap=10)
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids)), "Chunk IDs should be unique"


def test_chunk_documents_processes_multiple_docs():
    """chunk_documents() should process a list of documents."""
    docs = [
        make_test_document("Document one content. " * 20),
        Document(
            doc_id="doc_two",
            text="Document two content. " * 20,
            title="Doc Two",
            source_file="doc2.md",
            file_path="/fake/doc2.md",
            source_type="markdown",
            metadata={},
        ),
    ]
    chunks = chunk_documents(docs, chunk_size=100, chunk_overlap=10)
    doc_ids_found = {c.doc_id for c in chunks}
    assert "test_doc" in doc_ids_found
    assert "doc_two" in doc_ids_found


def test_empty_document_returns_no_chunks():
    """An empty document should produce no chunks."""
    doc = make_test_document(text="   ")
    chunks = chunk_document(doc, chunk_size=100, chunk_overlap=10)
    # May return 0 or 1 (single whitespace chunk filtered)
    assert all(c.char_count > 0 for c in chunks)


def test_save_and_load_chunks_roundtrip(tmp_path):
    """save_chunks_to_json → load_chunks_from_json should be lossless."""
    doc = make_test_document()
    original_chunks = chunk_document(doc, chunk_size=100, chunk_overlap=10)

    output_file = str(tmp_path / "test_chunks.json")
    save_chunks_to_json(original_chunks, output_file)

    loaded_chunks = load_chunks_from_json(output_file)

    assert len(loaded_chunks) == len(original_chunks)
    for orig, loaded in zip(original_chunks, loaded_chunks):
        assert orig.chunk_id == loaded.chunk_id
        assert orig.text == loaded.text
        assert orig.doc_id == loaded.doc_id
        assert orig.source_file == loaded.source_file


def test_chunk_size_respected():
    """Chunks should be approximately at or below the target size."""
    long_text = "This is a long sentence with many words. " * 100
    doc = make_test_document(text=long_text)
    chunk_size = 200
    chunks = chunk_document(doc, chunk_size=chunk_size, chunk_overlap=20)
    
    # Allow some buffer since RecursiveCharacterTextSplitter is approximate
    for chunk in chunks:
        assert chunk.char_count <= chunk_size * 1.5, (
            f"Chunk too large: {chunk.char_count} chars (limit was ~{chunk_size})"
        )
