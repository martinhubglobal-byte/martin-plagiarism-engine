# Contributing

Thanks for your interest in noplag-engine.

## Scope

The engine's job is verbatim / near-verbatim detection against a local
corpus: chunking, winnowing fingerprints, L1 retrieval, L0 alignment, and the
`/v1` API around them. Good contributions make that pipeline faster, more
accurate, easier to operate, or better documented.

Paraphrase detection, semantic matching, and AI-writing detection are on the
product roadmap but intentionally not in this codebase yet — please open an
issue to discuss before investing in a large feature in those directions.

## Setup

```sh
pip install -e ".[dev]"
docker compose up postgres -d
ruff check .
pytest -q
```

Postgres-backed tests skip automatically when no database is reachable at
`DATABASE_URL` (default `postgresql+psycopg://noplag:noplag@localhost:5432/noplag`).

## Pull requests

- Keep changes focused; separate refactors from behavior changes.
- Add or update tests for anything behavioral. The suite must pass with a
  local Postgres.
- Run `ruff check .` before pushing.
- Detection-quality changes (chunking, fingerprinting, retrieval, alignment)
  should include before/after numbers from the PAN-PC-11 harness in `eval/`
  — see `eval/datasets/pan_pc_11/README.md` for how to fetch the corpus and
  run it.
- A change to fingerprinting parameters or the winnowing algorithm breaks
  compatibility with existing corpora (fingerprints only match when the
  corpus side and query side agree). Call that out explicitly in the PR.

## Reporting issues

Include the engine version (or commit), how you're running it (compose /
bare), the corpus size, and — for detection-quality issues — a minimal
query text + corpus document pair that reproduces the problem.
