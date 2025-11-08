"""
Build a DuckDB-based vector index for ACS documentation.

Usage:
    python scripts/build_doc_index.py --docs-dir acs_docs
"""
from __future__ import annotations

import argparse
import itertools
from pathlib import Path
from typing import Iterable, List, Tuple

import duckdb
import pandas as pd
from pdfminer.high_level import extract_text
from sentence_transformers import SentenceTransformer


DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DOC_TYPES = ("pdf", "excel")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest ACS docs into DuckDB vector store")
    parser.add_argument("--docs-dir", type=Path, default=Path("acs_docs"), help="Directory containing ACS docs")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=Path("cache/doc_index/acs_docs.duckdb"),
        help="Path to DuckDB database file",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="SentenceTransformer model name")
    parser.add_argument("--chunk-size", type=int, default=1200, help="Chunk size in characters for PDFs")
    parser.add_argument("--overlap", type=int, default=200, help="Overlap between PDF chunks")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of chunks per document (for debugging)")
    return parser.parse_args()


def normalize_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    return " ".join(line for line in lines if line)


def chunk_text(text: str, chunk_size: int, overlap: int) -> Iterable[str]:
    if not text:
        return []
    start = 0
    length = len(text)
    while start < length:
        end = min(length, start + chunk_size)
        yield text[start:end]
        if end >= length:
            break
        start = max(0, end - overlap)


def load_pdf_chunks(path: Path, chunk_size: int, overlap: int, limit: int | None) -> List[Tuple[str, str]]:
    raw_text = extract_text(str(path))
    normalized = normalize_text(raw_text)
    chunks = list(chunk_text(normalized, chunk_size, overlap))
    if limit:
        chunks = chunks[:limit]
    return [(str(path.name), chunk) for chunk in chunks]


def load_excel_rows(path: Path) -> List[Tuple[str, str, str]]:
    df = pd.read_excel(path)
    rows = []
    for _, row in df.iterrows():
        table_id = str(row.get("Table ID") or row.get("TableID") or "").strip()
        subject = str(row.get("Subject Area") or row.get("Subject", "")).strip()
        title = str(row.get("Table Title") or row.get("Title", "")).strip()
        universe = str(row.get("Universe", "")).strip()
        description = " | ".join(filter(None, [subject, universe, title]))
        if not description:
            continue
        rows.append((table_id or None, description, f"{table_id} - {title}" if table_id else title))
    return rows


def ensure_schema(con: duckdb.DuckDBPyConnection, dim: int):
    con.execute("INSTALL 'vss';")
    con.execute("LOAD 'vss';")
    con.execute("PRAGMA hnsw_enable_experimental_persistence=true;")
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS doc_chunks (
            id BIGINT PRIMARY KEY,
            doc_type TEXT,
            source TEXT,
            location TEXT,
            heading TEXT,
            table_id TEXT,
            text TEXT,
            embedding FLOAT[%s]
        )
        """
        % dim
    )


def next_ids(con: duckdb.DuckDBPyConnection, count: int) -> Iterable[int]:
    start = con.execute("SELECT COALESCE(MAX(id) + 1, 1) FROM doc_chunks").fetchone()[0]
    return itertools.count(start, 1)


def insert_rows(con: duckdb.DuckDBPyConnection, rows: List[tuple], dim: int):
    if not rows:
        return
    con.executemany(
        """
        INSERT OR REPLACE INTO doc_chunks (id, doc_type, source, location, heading, table_id, text, embedding)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    con.execute("PRAGMA hnsw_enable_experimental_persistence=true;")
    con.execute(
        """
        CREATE INDEX IF NOT EXISTS doc_chunks_hnsw
        ON doc_chunks USING HNSW (embedding)
        """
    )


def ingest_docs(args: argparse.Namespace):
    docs_dir: Path = args.docs_dir
    db_path: Path = args.db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)

    model = SentenceTransformer(args.model)
    dim = model.get_sentence_embedding_dimension()

    con = duckdb.connect(str(db_path))
    ensure_schema(con, dim)

    rows_to_insert: List[tuple] = []
    id_iter = next_ids(con, 1)

    # PDFs
    for pdf_file in docs_dir.glob("*.pdf"):
        print(f"Ingesting PDF: {pdf_file.name}")
        con.execute("DELETE FROM doc_chunks WHERE source = ?", [pdf_file.name])
        chunks = load_pdf_chunks(pdf_file, args.chunk_size, args.overlap, args.limit)
        if not chunks:
            continue
        embeddings = model.encode([chunk for _, chunk in chunks], convert_to_numpy=True, normalize_embeddings=True)
        for (source, chunk), emb in zip(chunks, embeddings):
            chunk_id = next(id_iter)
            rows_to_insert.append(
                (
                    chunk_id,
                    "pdf",
                    source,
                    "",
                    "",
                    None,
                    chunk,
                    emb.tolist(),
                )
            )

    # Excel file(s)
    for xls_file in docs_dir.glob("*.xls*"):
        print(f"Ingesting Excel: {xls_file.name}")
        con.execute("DELETE FROM doc_chunks WHERE source = ?", [xls_file.name])
        rows = load_excel_rows(xls_file)
        texts = [row[1] for row in rows]
        if not texts:
            continue
        embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        for row, emb in zip(rows, embeddings):
            table_id, chunk_text_value, heading = row
            chunk_id = next(id_iter)
            rows_to_insert.append(
                (
                    chunk_id,
                    "excel",
                    xls_file.name,
                    "",
                    heading,
                    table_id,
                    chunk_text_value,
                    emb.tolist(),
                )
            )

    insert_rows(con, rows_to_insert, dim)
    print(f"Inserted {len(rows_to_insert)} chunks into {db_path}")


def main():
    args = parse_args()
    ingest_docs(args)


if __name__ == "__main__":
    main()
