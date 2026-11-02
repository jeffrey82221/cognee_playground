# cognee_playground
Experiment with cognee - the AI memory layer.

`cognee_ingest_demo.py` is a single-file demo that ingests several file types
(txt, md, csv, json, html – plus any pdf/docx/image/audio you pass in), builds a
knowledge graph and queries it. Everything (SQLite, LanceDB, Kuzu) is stored
locally, so it runs on a Mac with no extra services; only an LLM API key is needed.

## Run (macOS)
```bash
python3 -m venv .venv && source .venv/bin/activate   # Python 3.10–3.13
pip install -r requirements.txt
export LLM_API_KEY="sk-..."                          # OpenAI key (default provider)
python cognee_ingest_demo.py                         # sample files
python cognee_ingest_demo.py ~/docs/report.pdf ~/docs/spec.docx   # your files
```

## Pipeline stages (for porting to Airflow)
| Function | cognee call | Airflow task idea |
|---|---|---|
| `ingest_files(paths)` | `cognee.add(path, dataset_name=...)` | one task per file / batch |
| `build_graph()` | `cognee.cognify(datasets=[...])` | one task after all ingests |
| `query(question)` | `cognee.search(query_text=..., query_type=SearchType.GRAPH_COMPLETION)` | downstream consumer |

Notes for migrating:
- All functions are `async`; wrap with `asyncio.run(...)` inside a `@task` / `PythonOperator` callable.
- Provide `LLM_API_KEY` (and optionally `LLM_PROVIDER`, `LLM_MODEL`) via Airflow Connections/env vars.
- Set `DATA_ROOT_DIRECTORY` / `SYSTEM_ROOT_DIRECTORY` to a persistent path shared by workers, or configure Postgres/Neo4j/Qdrant etc. per the cognee docs.
- The `prune` calls in `main()` wipe all data; drop them in a real pipeline.
- Re-running `add` on unchanged files is deduplicated by content hash.
