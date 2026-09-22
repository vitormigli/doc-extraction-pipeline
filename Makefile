.PHONY: run test eval lint dataset

dataset:
	uv run python -m doc_extraction.generator.dataset --output evals/dataset --per-type 15

run:
	uv run uvicorn doc_extraction.api:app --host 0.0.0.0 --port 8000 --reload

demo:
	uv run streamlit run src/doc_extraction/streamlit_app.py

test:
	uv run pytest

eval: dataset
	uv run python evals/run_eval.py

lint:
	uv run ruff check .
