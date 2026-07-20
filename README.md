<p align="center">
  <img src="docs/assets/banner.png" alt="Noplag Engine" width="100%">
</p>

<h1 align="center">Noplag Engine</h1>

<p align="center">
  <strong>The open-source plagiarism detection engine.</strong><br>
  Read the code, fork it, run it on your own hardware.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-Apache--2.0-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/python-3.12+-brightgreen.svg" alt="Python">
  <img src="https://img.shields.io/badge/self--hostable-yes-success.svg" alt="Self-hostable">
</p>

---

Twelve years of plagiarism detection, rebuilt in the open. This is the verbatim
and near-verbatim core that powers [noplag.com](https://noplag.com) —
winnowing-fingerprint matching over a corpus **you** control, with every match
tracing back to its source.

We built it on one belief: **auditable beats black-box.** Trust shouldn't
require taking our word for it.

### Three commitments

- **Auditable** — Apache-2.0. Read it, fork it, self-host it. No black box.
- **Honest** — every match shows its source, and we don't claim accuracy we
  can't measure. This engine detects **verbatim and near-verbatim** copying;
  paraphrase, semantic, and AI-writing detection are on the
  [public roadmap](https://noplag.com/roadmap) — not pretended-present.
- **Yours** — your documents are never used for training. Runs entirely on your
  own infrastructure.

### Try it in two minutes

```sh
git clone https://github.com/NoplagLabs/noplag-engine
cd noplag-engine
docker compose up
```

First start migrates the schema and indexes the bundled sample corpus
(~1,000 Wikipedia articles, a couple of minutes). Then:

- **http://localhost:8000** — demo page. Paste a paragraph from a well-known
  Wikipedia article (say, the lead of *Albert Einstein*) and run a check: you
  get a similarity score, highlighted passages, and the matched articles.
- **http://localhost:8000/docs** — interactive OpenAPI docs for the `/v1` API.

The demo page is deliberately bare — the API is the product here. Build your
own UI on `POST /v1/checks` → `GET /v1/checks/{id}/report`.

## How it works

Documents are split into sentence-window chunks, each chunk is reduced to
[winnowing fingerprints](https://theory.stanford.edu/~aiken/publications/papers/sigmod03.pdf)
(a GIN-indexed `bigint[]` in Postgres), candidate sources are retrieved by
fingerprint overlap, and matches are refined to exact character ranges with a
seed-and-extend aligner. The result is a report with per-source similarity,
per-passage character offsets on both sides, and honest coverage accounting.

The hosted product additionally searches the live web; the open-source engine
matches against your local corpus only.

## Bring your own corpus

The engine matches against what you index. Three ways to feed it:

```sh
# a folder of .txt / .md / .pdf / .docx
DATABASE_URL=... python scripts/ingest_folder.py /path/to/documents

# one file over HTTP
curl -F "file=@paper.pdf" http://localhost:8000/v1/corpus/documents
```

or call `ingest_platform_document` / `fingerprint_document` from
`noplag_engine.workflows.corpus` in your own pipeline. See
[docs/self-hosting.md](docs/self-hosting.md) for corpus design, scaling notes,
and the tuning knobs that matter past ~10M chunks.

## API in 30 seconds

```sh
# submit
curl -s -X POST http://localhost:8000/v1/checks \
  -H 'Content-Type: application/json' \
  -d '{"query_text": "Text to check, at least a few sentences long..."}'
# -> {"check_id": "...", "status_url": ..., "report_url": ...}

# poll status, then fetch the report
curl -s http://localhost:8000/v1/checks/<id>
curl -s http://localhost:8000/v1/checks/<id>/report
```

The full surface (uploads, SSE progress, corpus management) is documented in
[docs/api.md](docs/api.md) and served live at `/docs`.

Note: the API ships with **no authentication** — it is a single-tenant
backend service. Run it on a trusted network or put your own auth in front.

## Development

Requires **Python 3.12 or newer**. On a system whose default `python3` is
older, create the virtualenv with an explicit interpreter — `pip install`
otherwise fails with an unhelpful version error.

```sh
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
docker compose up postgres -d   # tests skip DB-bound suites without it
ruff check .
pytest -q
```

## Benchmarks

The engine is evaluated with the standard plagdet metric on
[PAN-PC-11](https://zenodo.org/records/3250095); the harness lives in
[eval/](eval/). Read the numbers with the engine's scope in mind:

- On **verbatim and lightly-obfuscated** material (the harness's synthetic
  PAN-style set, and the verbatim portion of PAN-PC-11), plagdet lands
  around **0.8+** with precision ≥ 0.95.
- On the **full PAN-PC-11**, which is dominated by heavy paraphrase,
  summarization, and cross-language obfuscation, an L0/L1 engine scores
  **near zero by design** — fingerprints only match text that is actually
  reused near-verbatim. That gap is exactly what the roadmap's paraphrase
  (L2) and semantic (L3) layers exist to close; do not read any single
  plagdet figure here as general-purpose detection accuracy.

See [eval/datasets/pan_pc_11/README.md](eval/datasets/pan_pc_11/README.md)
for how to fetch the corpus and reproduce the numbers.

## Layout

- `src/noplag_engine/` — package source: `chunking`, `fingerprinting`,
  `retrieval`, `alignment`, `workflows` (the check pipeline), `api`
- `migrations/` — Alembic schema
- `scripts/` — corpus ingestion + maintenance CLIs
- `eval/` — PAN-PC-11 benchmark harness
- `data/` — bundled sample corpus (CC BY-SA, see
  [data/SAMPLE_CORPUS_LICENSE.md](data/SAMPLE_CORPUS_LICENSE.md))

## License

[Apache-2.0](LICENSE). The sample corpus texts are from English Wikipedia and
remain CC BY-SA 4.0.
