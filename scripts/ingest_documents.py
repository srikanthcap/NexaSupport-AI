# =============================================================
# NexaSupport AI — Document Ingestion Script
# =============================================================
# PURPOSE:
#   Loads all IT knowledge documents, chunks them, and saves
#   the output to data/processed/chunks.json.
#
# HOW TO RUN (from the project root directory):
#   python scripts/ingest_documents.py
#
# EXPECTED OUTPUT:
#   - Summary table showing each document and how many chunks it produced.
#   - data/processed/chunks.json created with all chunk data.
#
# WHEN TO RUN:
#   - After adding new documents to data/documents/
#   - After changing chunk_size or chunk_overlap settings
#   - Before running build_index.py (which creates the vector database)
# =============================================================

import sys
import os

# Add the project root to sys.path so Python can find the 'app' package.
# This is necessary when running the script directly (python scripts/ingest_documents.py)
# rather than as a module.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from loguru import logger

from app.config import settings
from app.utils.document_loader import load_documents
from app.utils.text_chunker import chunk_documents, save_chunks_to_json

# Configure loguru to show only INFO and above in the console
logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")

console = Console()


def main():
    console.print(Panel.fit(
        "[bold cyan]NexaSupport AI — Document Ingestion Pipeline[/bold cyan]\n"
        "[dim]Phase 3: Loading → Chunking → Saving[/dim]",
        border_style="cyan"
    ))

    # ── Step 1: Load documents ─────────────────────────────────
    console.print("\n[bold]Step 1:[/bold] Loading documents from [green]data/documents/[/green]...")
    documents = load_documents("data/documents")

    if not documents:
        console.print("[red]❌ No documents found. Add .md or .txt files to data/documents/[/red]")
        sys.exit(1)

    console.print(f"  ✅ Loaded [bold]{len(documents)}[/bold] document(s)")

    # ── Step 2: Chunk documents ────────────────────────────────
    console.print(f"\n[bold]Step 2:[/bold] Chunking documents...")
    console.print(f"  Settings: chunk_size=[yellow]{settings.CHUNK_SIZE}[/yellow], "
                  f"chunk_overlap=[yellow]{settings.CHUNK_OVERLAP}[/yellow]")

    all_chunks = chunk_documents(
        documents,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )

    if not all_chunks:
        console.print("[red]❌ No chunks produced. Check document content.[/red]")
        sys.exit(1)

    # ── Step 3: Display summary table ─────────────────────────
    console.print(f"\n[bold]Step 3:[/bold] Summary")

    table = Table(title="Chunking Results", border_style="cyan", show_lines=True)
    table.add_column("Document", style="cyan", no_wrap=True)
    table.add_column("Source File", style="dim")
    table.add_column("Chunks", justify="right", style="green")
    table.add_column("Avg Chars/Chunk", justify="right")
    table.add_column("Total Chars", justify="right")

    # Group chunks by document
    doc_chunk_map: dict[str, list] = {}
    for chunk in all_chunks:
        doc_chunk_map.setdefault(chunk.doc_id, []).append(chunk)

    for doc in documents:
        doc_chunks = doc_chunk_map.get(doc.doc_id, [])
        avg_chars = sum(c.char_count for c in doc_chunks) // max(len(doc_chunks), 1)
        total_chars = sum(c.char_count for c in doc_chunks)
        table.add_row(
            doc.title[:45] + ("…" if len(doc.title) > 45 else ""),
            doc.source_file,
            str(len(doc_chunks)),
            str(avg_chars),
            str(total_chars),
        )

    # Totals row
    table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]{len(documents)} docs[/bold]",
        f"[bold]{len(all_chunks)}[/bold]",
        f"[bold]{sum(c.char_count for c in all_chunks) // len(all_chunks)}[/bold]",
        f"[bold]{sum(c.char_count for c in all_chunks)}[/bold]",
    )
    console.print(table)

    # ── Step 4: Save to JSON ───────────────────────────────────
    output_path = "data/processed/chunks.json"
    console.print(f"\n[bold]Step 4:[/bold] Saving chunks to [green]{output_path}[/green]...")
    save_chunks_to_json(all_chunks, output_path)

    console.print(Panel.fit(
        f"[bold green]✅ Ingestion Complete![/bold green]\n\n"
        f"  Documents loaded : [bold]{len(documents)}[/bold]\n"
        f"  Total chunks     : [bold]{len(all_chunks)}[/bold]\n"
        f"  Output file      : [bold]{output_path}[/bold]\n\n"
        f"[dim]Next step: Run [bold]python scripts/build_index.py[/bold] to embed and index chunks into ChromaDB[/dim]",
        border_style="green"
    ))


if __name__ == "__main__":
    main()
