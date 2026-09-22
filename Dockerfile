FROM python:3.11-slim

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock* README.md ./
RUN uv sync --no-install-project || true

COPY . .
RUN uv sync

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "doc_extraction.api:app", "--host", "0.0.0.0", "--port", "8000"]
