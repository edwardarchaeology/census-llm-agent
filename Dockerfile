FROM python:3.13-slim AS base

ENV UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY . /app

RUN uv pip install -r requirements.txt \
 && uv run python scripts/build_doc_index.py --docs-dir acs_docs

EXPOSE 8501
CMD ["uv", "run", "streamlit", "run", "gui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
