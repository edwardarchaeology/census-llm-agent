"""
Utility helpers for retrieving ACS documentation snippets from DuckDB.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, List
import warnings

try:
    import duckdb
except ModuleNotFoundError:  # pragma: no cover - handled gracefully at runtime
    duckdb = None

try:
    from sentence_transformers import SentenceTransformer
except ModuleNotFoundError as exc:  # pragma: no cover
    raise RuntimeError(
        "sentence-transformers is required for documentation retrieval. "
        "Install via `pip install -r requirements.txt`."
    ) from exc


DB_PATH = Path("cache/doc_index/acs_docs.duckdb")
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_connection():
    if duckdb is None:
        warnings.warn(
            "DuckDB is not installed; documentation retrieval is disabled. "
            "Install dependencies with `pip install -r requirements.txt`.",
            RuntimeWarning,
        )
        return None
    if not DB_PATH.exists():
        return None
    con = duckdb.connect(str(DB_PATH))
    try:
        con.execute("LOAD 'vss';")
    except duckdb.CatalogException:
        con.execute("INSTALL 'vss';")
        con.execute("LOAD 'vss';")
    con.execute("PRAGMA hnsw_enable_experimental_persistence=true;")
    return con


@lru_cache(maxsize=1)
def _get_model():
    return SentenceTransformer(EMBED_MODEL)


def _embed(text: str):
    model = _get_model()
    return model.encode([text], normalize_embeddings=True, convert_to_numpy=True)[0].tolist()


def search_docs(query: str, top_k: int = 3) -> List[Dict]:
    con = _get_connection()
    if con is None or not query.strip():
        return []
    vector = _embed(query)
    sql = """
        SELECT source, heading, table_id, text,
               embedding <=> ? AS distance
        FROM doc_chunks
        ORDER BY distance ASC
        LIMIT ?
    """
    rows = con.execute(sql, [vector, top_k]).fetchall()
    return [
        {
            "source": row[0],
            "heading": row[1],
            "table_id": row[2],
            "text": row[3],
            "distance": row[4],
        }
        for row in rows
    ]


def search_by_table(table_id: str, top_k: int = 2) -> List[Dict]:
    if not table_id:
        return []
    con = _get_connection()
    if con is None:
        return []
    sql = """
        SELECT source, heading, table_id, text, 0.0 AS distance
        FROM doc_chunks
        WHERE table_id = ?
        LIMIT ?
    """
    rows = con.execute(sql, [table_id, top_k]).fetchall()
    if rows:
        return [
            {"source": row[0], "heading": row[1], "table_id": row[2], "text": row[3], "distance": row[4]}
            for row in rows
        ]
    # fallback to semantic search if table not in Excel sheet
    return search_docs(table_id, top_k=top_k)
