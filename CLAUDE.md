# Project instructions for Claude

This project follows the rules of the portfolio master plan:

1. No client code or data — synthetic only (see `src/doc_extraction/generator/`).
2. No committed secrets — use `.env` (gitignored) and keep `.env.example` up to
   date. `gitleaks` runs on pre-commit and in CI.
3. Every project reports numeric evaluation metrics — see `evals/results.md`.
4. Everything runs with a single command: `docker compose up` or `make run`.
5. README in English, with a short "Resumo em português" section at the end.
6. Small, descriptive commits using Conventional Commits.
7. Prefer simplicity — Claude API used directly via the `anthropic` SDK, no
   agent framework.

## Layout

- `src/doc_extraction/` — schemas, business validators, extraction pipeline,
  synthetic document generator, FastAPI app, Streamlit demo.
- `tests/` — unit tests for validators and schemas (no API calls).
- `evals/` — `run_eval.py` calls the real Claude API and writes
  `results.json`/`results.md`; costs real money, not part of CI.
- `evals/dataset/` — generated synthetic documents (images + ground truth).
