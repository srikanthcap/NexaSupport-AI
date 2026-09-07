# =============================================================
# NexaSupport AI — Build Vector Index Script
# =============================================================
# PURPOSE:
#   Reads pre-chunked documents from data/processed/chunks.json,
#   generates embeddings, and upserts everything into ChromaDB.
#
# HOW TO RUN (from the project root directory):
#   python scripts/build_index.py
#
#   Optional flags:
#   --reset   : Delete the existing ChromaDB collection before indexing.
#               Use this when documents have changed significantly.
#               Without --reset, new chunks are added to the existing index.
#
# EXPECTED OUTPUT:
#   - Progress as chunks are embedded and indexed.
#   - Summary showing total chunks indexed and ChromaDB location.
#   - data/chroma_db/ directory created/updated.
#
# PREREQUISITES:
#   Run python scripts/ingest_documents.py first to create chunks.json
# =============================================================

import sys
import os
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from loguru import logger

from app.config import settings
from app.rag.embeddings import get_embedding_service
from app.rag.vector_store import VectorStoreService
from app.utils.text_chunker import load_chunks_from_json

logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")

console = Console()


def parse_args():
    parser = argparse.ArgumentParser(description="Build the NexaSupport AI vector index")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete and rebuild the ChromaDB collection from scratch",
    )
    parser.add_argument(
        "--chunks-path",
        default="data/processed/chunks.json",
        help="Path to the chunks JSON file (default: data/processed/chunks.json)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    console.print(Panel.fit(
        "[bold cyan]NexaSupport AI — Vector Index Builder[/bold cyan]\n"
        "[dim]Phase 4: Chunks → Embeddings → ChromaDB[/dim]",
        border_style="cyan"
    ))

    # ── Step 1: Load chunks from JSON ─────────────────────────
    console.print(f"\n[bold]Step 1:[/bold] Loading chunks from [green]{args.chunks_path}[/green]...")
    chunks = load_chunks_from_json(args.chunks_path)

    if not chunks:
        console.print(
            "[red]❌ No chunks found. Run [bold]python scripts/ingest_documents.py[/bold] first.[/red]"
        )
        sys.exit(1)

    console.print(f"  ✅ Loaded [bold]{len(chunks)}[/bold] chunk(s) from {args.chunks_path}")

    # ── Step 2: Initialize services ────────────────────────────
    console.print(f"\n[bold]Step 2:[/bold] Initializing embedding service...")
    console.print(
        f"  Provider: [yellow]{settings.EMBEDDING_PROVIDER}[/yellow] | "
        f"Model: [yellow]{settings.LOCAL_EMBEDDING_MODEL if settings.EMBEDDING_PROVIDER == 'local' else settings.GEMINI_EMBEDDING_MODEL}[/yellow]"
    )

    embedding_service = get_embedding_service()
    console.print(f"  ✅ Embedding service ready (dimension: {embedding_service.embedding_dimension})")

    vector_store = VectorStoreService()

    # ── Step 3: Reset if requested ─────────────────────────────
    if args.reset:
        console.print(
            "\n[bold yellow]⚠️  --reset flag detected.[/bold yellow] "
            "Deleting existing ChromaDB collection..."
        )
        vector_store.delete_collection()
        console.print("  ✅ Collection reset. Starting fresh index.")
    else:
        stats = vector_store.get_collection_stats()
        existing_count = stats["total_chunks"]
        if existing_count > 0:
            console.print(
                f"\n[dim]Note: Collection already has {existing_count} chunk(s). "
                f"New chunks will be upserted (existing unchanged). "
                f"Use [bold]--reset[/bold] to rebuild from scratch.[/dim]"
            )

    # ── Step 4: Index chunks ────────────────────────────────────
    console.print(f"\n[bold]Step 3:[/bold] Embedding and indexing {len(chunks)} chunks...")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Indexing chunks...", total=len(chunks))

        batch_size = 50
        total_added = 0
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c.text for c in batch]
            ids = [c.chunk_id for c in batch]
            metadatas = [c.metadata for c in batch]

            embeddings = embedding_service.embed_texts(texts)

            # Direct ChromaDB access for progress tracking
            collection = vector_store._get_collection()
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )
            total_added += len(batch)
            progress.update(task, advance=len(batch))

    # ── Step 5: Verify and show stats ──────────────────────────
    stats = vector_store.get_collection_stats()

    console.print(Panel.fit(
        f"[bold green]✅ Vector Index Built Successfully![/bold green]\n\n"
        f"  Chunks indexed      : [bold]{stats['total_chunks']}[/bold]\n"
        f"  Collection name     : [bold]{stats['collection_name']}[/bold]\n"
        f"  Storage location    : [bold]{stats['persist_directory']}[/bold]\n"
        f"  Embedding provider  : [bold]{stats['embedding_provider']}[/bold]\n"
        f"  Embedding model     : [bold]{stats['embedding_model']}[/bold]\n\n"
        f"[dim]Next step: Test with a search query by running:\n"
        f"  python -c \"from app.rag.vector_store import VectorStoreService; "
        f"r=VectorStoreService().similarity_search('VPN Error 809',k=3); "
        f"[print(x.title, x.similarity_score) for x in r]\"[/dim]",
        border_style="green"
    ))


if __name__ == "__main__":
    main()
