from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..utils.logger import get_logger

logger = get_logger(__name__)


class MetadataDB:
    """
    SQLite wrapper for chunk-level metadata with artifact/version identity.
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    artifact_id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_path TEXT,
                    file_size INTEGER,
                    latest_version_id TEXT NOT NULL,
                    doc_type TEXT,
                    project_name TEXT,
                    author TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    schema_version TEXT DEFAULT '1.0'
                );

                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    artifact_id TEXT NOT NULL,
                    version_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    file_path TEXT,
                    doc_type TEXT,
                    section_type TEXT,
                    chunk_type TEXT NOT NULL,
                    calculation_type TEXT,
                    text TEXT NOT NULL,
                    normalized_text TEXT,
                    style_frequency INTEGER DEFAULT 0,
                    quality_score REAL,
                    is_pinned INTEGER DEFAULT 0,
                    page_number INTEGER,
                    section_number TEXT,
                    heading TEXT,
                    project_name TEXT,
                    author TEXT,
                    reviewer TEXT,
                    tags TEXT,
                    parent_artifact_id TEXT,
                    related_chunks TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    schema_version TEXT DEFAULT '1.0',
                    FOREIGN KEY (artifact_id) REFERENCES documents(artifact_id)
                );

                CREATE INDEX IF NOT EXISTS idx_chunks_artifact ON chunks(artifact_id);
                CREATE INDEX IF NOT EXISTS idx_chunks_company ON chunks(company_id);
                CREATE INDEX IF NOT EXISTS idx_chunks_doc_type ON chunks(doc_type);
                CREATE INDEX IF NOT EXISTS idx_chunks_section_type ON chunks(section_type);
                CREATE INDEX IF NOT EXISTS idx_chunks_created ON chunks(created_at);
                CREATE INDEX IF NOT EXISTS idx_chunks_norm_text ON chunks(normalized_text);
                CREATE INDEX IF NOT EXISTS idx_docs_company ON documents(company_id);
                """
            )
            conn.commit()

    def insert_chunk_metadata(self, record: Dict[str, Any]) -> str:
        chunk_id = record.get("chunk_id") or str(uuid4())
        now = datetime.utcnow().isoformat()
        payload = {
            "chunk_id": chunk_id,
            "artifact_id": record.get("artifact_id"),
            "version_id": record.get("version_id"),
            "company_id": record.get("company_id"),
            "source": record.get("source", "upload"),
            "file_path": record.get("file_path"),
            "doc_type": record.get("doc_type"),
            "section_type": record.get("section_type"),
            "chunk_type": record.get("chunk_type"),
            "calculation_type": record.get("calculation_type"),
            "text": record.get("text"),
            "normalized_text": record.get("normalized_text"),
            "style_frequency": int(record.get("style_frequency", 0) or 0),
            "quality_score": record.get("quality_score"),
            "is_pinned": int(bool(record.get("is_pinned", False))),
            "page_number": record.get("page_number"),
            "section_number": record.get("section_number"),
            "heading": record.get("heading"),
            "project_name": record.get("project_name"),
            "author": record.get("author"),
            "reviewer": record.get("reviewer"),
            "tags": json.dumps(record.get("tags", [])),
            "parent_artifact_id": record.get("parent_artifact_id"),
            "related_chunks": json.dumps(record.get("related_chunks", [])),
            "created_at": record.get("created_at", now),
            "modified_at": record.get("modified_at", now),
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO chunks
                (chunk_id, artifact_id, version_id, company_id, source, file_path, doc_type, section_type, chunk_type,
                 calculation_type, text, normalized_text, style_frequency, quality_score, is_pinned, page_number, section_number, heading, project_name, author, reviewer, tags,
                 parent_artifact_id, related_chunks, created_at, modified_at)
                VALUES (:chunk_id, :artifact_id, :version_id, :company_id, :source, :file_path, :doc_type, :section_type,
                        :chunk_type, :calculation_type, :text, :normalized_text, :style_frequency, :quality_score, :is_pinned,
                        :page_number, :section_number, :heading, :project_name,
                        :author, :reviewer, :tags, :parent_artifact_id, :related_chunks, :created_at, :modified_at)
                """,
                payload,
            )
            conn.commit()
        return chunk_id

    def insert_document(self, record: Dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO documents
                (artifact_id, company_id, file_name, file_path, file_size, latest_version_id, doc_type, project_name, author)
                VALUES (:artifact_id, :company_id, :file_name, :file_path, :file_size, :latest_version_id, :doc_type, :project_name, :author)
                """,
                {
                    "artifact_id": record.get("artifact_id"),
                    "company_id": record.get("company_id"),
                    "file_name": record.get("file_name"),
                    "file_path": record.get("file_path"),
                    "file_size": record.get("file_size"),
                    "latest_version_id": record.get("latest_version_id"),
                    "doc_type": record.get("doc_type"),
                    "project_name": record.get("project_name"),
                    "author": record.get("author"),
                },
            )
            conn.commit()

    def list_recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM chunks ORDER BY datetime(created_at) DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [self._row_to_dict(row) for row in rows]

    def fetch_by_artifact(self, artifact_id: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM chunks WHERE artifact_id = ?", (artifact_id,)).fetchall()
            return [self._row_to_dict(row) for row in rows]

    def fetch_by_version(self, version_id: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM chunks WHERE version_id = ?", (version_id,)).fetchall()
            return [self._row_to_dict(row) for row in rows]

    def get_style_frequency(self, normalized_text: str, section_type: Optional[str] = None) -> int:
        if not normalized_text:
            return 0
        query = "SELECT COUNT(*) FROM chunks WHERE normalized_text = ? AND chunk_type = 'style'"
        params: list[Any] = [normalized_text]
        if section_type:
            query += " AND section_type = ?"
            params.append(section_type)
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
            return int(row[0]) if row else 0

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        data = {key: row[key] for key in row.keys()}
        data["tags"] = json.loads(data.get("tags") or "[]")
        data["related_chunks"] = json.loads(data.get("related_chunks") or "[]")
        return data
