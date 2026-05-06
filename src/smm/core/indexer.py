from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

from smm.core.chunker import chunk_document
from smm.core.db import get_or_create_collection

logger = logging.getLogger("smm.indexer")

SUPPORTED_EXTENSIONS = {".md", ".txt", ".rst"}


def _file_type(path: str) -> str:
    ext = Path(path).suffix.lower()
    return ext.lstrip(".") if ext.lstrip(".") in SUPPORTED_EXTENSIONS else ""


def _file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_supported(path: str) -> bool:
    return _file_type(path) != ""


async def index_file(
    client,
    path: str,
    collection_name: str,
    cfg: dict,
) -> dict:
    """Index a single file. Returns stats."""
    if not _is_supported(path):
        return {"skipped": 1, "added_chunks": 0, "updated_chunks": 0}

    abs_path = str(Path(path).resolve())
    content = Path(abs_path).read_text(encoding="utf-8")
    content_hash = _file_hash(abs_path)
    file_type = _file_type(abs_path)

    collection = get_or_create_collection(client, collection_name, cfg)

    existing = _get_existing_chunks(collection, abs_path)
    existing_hash = existing[0].get("file_hash") if existing else None

    if existing_hash == content_hash:
        return {"skipped": 1, "added_chunks": 0, "updated_chunks": 0}

    chunks = chunk_document(content, file_type, cfg)
    total = len(chunks)
    now = datetime.now(timezone.utc).isoformat()
    file_name = Path(abs_path).name

    ids = []
    documents = []
    metadatas = []

    for ch in chunks:
        chunk_id = hashlib.sha256(f"{abs_path}:{ch.index}".encode()).hexdigest()
        ids.append(chunk_id)
        documents.append(ch.text)
        metadatas.append(
            {
                "file_path": abs_path,
                "file_name": file_name,
                "file_type": file_type,
                "chunk_index": ch.index,
                "total_chunks": total,
                "heading": ch.heading,
                "file_hash": content_hash,
                "indexed_at": now,
            }
        )

    if existing:
        existing_ids = [d["id"] for d in existing]
        collection.delete(ids=existing_ids)

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    logger.info("Indexed %s → %d chunks", abs_path, total)
    return {"skipped": 0, "added_chunks": total, "updated_chunks": 0}


async def reindex_file(
    client,
    path: str,
    collection_name: str,
    cfg: dict,
) -> dict:
    return await index_file(client, path, collection_name, cfg)


async def remove_file(
    client,
    path: str,
    collection_name: str,
    cfg: dict,
) -> dict:
    abs_path = str(Path(path).resolve())
    collection = get_or_create_collection(client, collection_name, cfg)
    existing = _get_existing_chunks(collection, abs_path)
    if existing:
        existing_ids = [d["id"] for d in existing]
        collection.delete(ids=existing_ids)
        logger.info("Removed %s (%d chunks)", abs_path, len(existing_ids))
        return {"deleted_chunks": len(existing_ids)}
    return {"deleted_chunks": 0}


def _get_existing_chunks(collection, file_path: str) -> list:
    result = collection.get(
        where={"file_path": {"$eq": file_path}},
        include=["metadatas"],
    )
    if not result or not result.get("metadatas"):
        return []
    ids = result.get("ids", []) or []
    metadatas = result.get("metadatas") or []
    return [{"id": ids[i], "file_hash": metadatas[i].get("file_hash")} for i in range(len(ids))]


async def index_directory(
    client,
    dir_path: str,
    collection_name: str,
    cfg: dict,
    recursive: bool = True,
    on_progress=None,
) -> dict:
    """Index all supported files in a directory. Returns aggregate stats."""
    stats = {"added": 0, "updated": 0, "skipped": 0, "added_chunks": 0}
    dir_path = str(Path(dir_path).resolve())
    pattern = "**/*" if recursive else "*"

    files = list(Path(dir_path).glob(pattern))
    files = [f for f in files if f.is_file() and _is_supported(str(f))]

    for i, f in enumerate(files):
        result = await index_file(client, str(f), collection_name, cfg)
        stats["skipped"] += result["skipped"]
        stats["added_chunks"] += result["added_chunks"]
        if on_progress:
            on_progress(i + 1, len(files), str(f))

    return stats
