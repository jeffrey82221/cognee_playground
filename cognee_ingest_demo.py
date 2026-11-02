"""Minimal cognee demo: ingest several file types, build the knowledge graph, search it.

The three pipeline stages (add -> cognify -> search) map directly onto
Airflow tasks; see `ingest_files()`, `build_graph()` and `query()`.

Usage:
    export LLM_API_KEY="sk-..."          # OpenAI key (cognee default provider)
    python cognee_ingest_demo.py                       # uses generated sample files
    python cognee_ingest_demo.py path/a.pdf path/b.docx  # or your own files
"""
import asyncio
import csv
import json
import os
import sys
from pathlib import Path

import cognee
from cognee import SearchType

DATASET = "demo_dataset"
SAMPLE_DIR = Path(__file__).parent / "sample_data"


def make_sample_files() -> list[str]:
    """Create small txt / md / csv / json / html files to ingest."""
    SAMPLE_DIR.mkdir(exist_ok=True)
    files = {
        "intro.txt": "Alice is a data engineer at Acme Corp. She maintains the Airflow pipelines.",
        "notes.md": "# Team notes\n\nBob leads the analytics team at Acme Corp and works with Alice.\n",
        "page.html": "<html><body><h1>Acme Corp</h1><p>Acme Corp is based in Berlin.</p></body></html>",
    }
    for name, content in files.items():
        (SAMPLE_DIR / name).write_text(content, encoding="utf-8")
    with open(SAMPLE_DIR / "employees.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerows([["name", "role"], ["Alice", "Data Engineer"], ["Bob", "Analytics Lead"]])
    (SAMPLE_DIR / "project.json").write_text(
        json.dumps({"project": "Orion", "owner": "Alice", "company": "Acme Corp"}), encoding="utf-8"
    )
    return sorted(str(p) for p in SAMPLE_DIR.iterdir())


async def ingest_files(paths: list[str], dataset: str = DATASET) -> None:
    """Stage 1: add raw files (pdf, docx, txt, md, csv, json, html, images, audio...)."""
    for p in paths:
        await cognee.add(os.path.abspath(p), dataset_name=dataset)


async def build_graph(dataset: str = DATASET) -> None:
    """Stage 2: LLM-based extraction into the knowledge graph + vector index."""
    await cognee.cognify(datasets=[dataset])


async def query(question: str):
    """Stage 3: search the memory."""
    return await cognee.search(query_text=question, query_type=SearchType.GRAPH_COMPLETION)


async def main() -> None:
    if not os.getenv("LLM_API_KEY"):
        sys.exit("Set LLM_API_KEY first (e.g. export LLM_API_KEY=sk-...)")
    paths = sys.argv[1:] or make_sample_files()
    # Start from a clean state so the demo is repeatable; remove in production.
    await cognee.prune.prune_data()
    await cognee.prune.prune_system(metadata=True)
    await ingest_files(paths)
    await build_graph()
    for q in ["Who works at Acme Corp and what do they do?", "Where is Acme Corp based?"]:
        print(f"\nQ: {q}")
        for answer in await query(q):
            print("A:", answer)


if __name__ == "__main__":
    asyncio.run(main())
