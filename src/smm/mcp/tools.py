from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from smm.core.config import load_config, resolve_collection_name, add_watch_dir
from smm.core.db import get_client, close_client, get_or_create_collection
from smm.core.searcher import search as do_search
from smm.core.indexer import index_directory, index_file

logger = logging.getLogger("smm.mcp.tools")


def _get_cfg() -> dict:
    from smm.mcp.server import _current_cfg
    return _current_cfg or load_config()


async def smm_search(
    query: str,
    scope: str | None = None,
    mode: str = "hybrid",
    n_results: int = 10,
) -> list[dict]:
    """Search indexed documents. scope is collection name(s), comma-separated."""
    cfg = _get_cfg()
    client = get_client(cfg)
    try:
        if scope:
            collections = [s.strip() for s in scope.split(",") if s.strip()]
        else:
            collections = [wd["collection"] for wd in cfg.get("watch_dirs", [])]

        results = await do_search(client, query, collections, cfg, mode, n_results)
        return [
            {
                "content": r["content"],
                "file_path": r["metadata"].get("file_path", "?"),
                "file_name": r["metadata"].get("file_name", "?"),
                "heading": r["metadata"].get("heading"),
                "score": round(r["score"], 4),
                "collection": r.get("collection", "?"),
            }
            for r in results
        ]
    finally:
        close_client()


async def smm_list_collections() -> list[dict]:
    """List all collections with document and chunk counts."""
    cfg = _get_cfg()
    client = get_client(cfg)
    try:
        result = []
        for wd in cfg.get("watch_dirs", []):
            coll_name = wd["collection"]
            try:
                collection = get_or_create_collection(client, coll_name, cfg)
                count = collection.count()
                result.append({
                    "collection": coll_name,
                    "path": wd["path"],
                    "total_chunks": count,
                })
            except Exception as e:
                result.append({
                    "collection": coll_name,
                    "path": wd["path"],
                    "error": str(e),
                })
        return result
    finally:
        close_client()


async def smm_get_document(file_path: str) -> dict | None:
    """Get full document content by file path."""
    cfg = _get_cfg()
    client = get_client(cfg)
    try:
        for wd in cfg.get("watch_dirs", []):
            collection = get_or_create_collection(client, wd["collection"], cfg)
            result = collection.get(
                where={"file_path": {"$eq": file_path}},
                include=["documents"],
            )
            if result and result.get("documents"):
                docs = result["documents"]
                if isinstance(docs, list):
                    return {"file_path": file_path, "content": "\n\n".join(docs)}
                return {"file_path": file_path, "content": docs}
        return None
    finally:
        close_client()


async def smm_import_tool(path: str, collection: str | None = None) -> dict:
    """Import a file or directory into seekdb."""
    cfg = _get_cfg()
    client = get_client(cfg)
    try:
        abs_path = str(Path(path).resolve())
        coll_name = collection or resolve_collection_name(abs_path, cfg)
        add_watch_dir(cfg, abs_path, coll_name)

        if Path(abs_path).is_dir():
            stats = await index_directory(client, abs_path, coll_name, cfg)
            return {"action": "imported_directory", "path": abs_path, "collection": coll_name, **stats}
        else:
            stats = await index_file(client, abs_path, coll_name, cfg)
            return {"action": "imported_file", "path": abs_path, "collection": coll_name, **stats}
    finally:
        close_client()


async def smm_remove_tool(file_path: str | None = None, collection: str | None = None) -> dict:
    """Remove a file's index or an entire collection."""
    cfg = _get_cfg()
    client = get_client(cfg)
    try:
        if collection:
            client.delete_collection(collection)
            cfg["watch_dirs"] = [
                wd for wd in cfg.get("watch_dirs", [])
                if wd["collection"] != collection
            ]
            from smm.core.config import save_config
            save_config(cfg)
            return {"action": "removed_collection", "collection": collection}
        elif file_path:
            for wd in cfg.get("watch_dirs", []):
                collection = get_or_create_collection(client, wd["collection"], cfg)
                result = collection.get(
                    where={"file_path": {"$eq": file_path}},
                    include=[],
                )
                if result and result.get("ids"):
                    collection.delete(ids=result["ids"])
                    return {"action": "removed_file", "file_path": file_path}
            return {"action": "not_found", "file_path": file_path}
        return {"error": "Provide file_path or collection"}
    finally:
        close_client()


async def smm_status_tool() -> dict:
    """Get daemon status and index statistics."""
    import json
    from smm.core.config import PID_PATH
    cfg = _get_cfg()

    running = False
    pid = None
    if PID_PATH.exists():
        data = json.loads(PID_PATH.read_text())
        pid = data["pid"]
        try:
            import os
            os.kill(pid, 0)
            running = True
        except OSError:
            running = False

    return {
        "running": running,
        "pid": pid,
        "web_port": cfg["web"]["port"],
        "sse_port": cfg["mcp"]["sse_port"],
        "watch_dirs": cfg.get("watch_dirs", []),
    }


async def smm_reindex(scope: str | None = None) -> dict:
    """Re-index all documents in a collection or all collections."""
    cfg = _get_cfg()
    client = get_client(cfg)
    try:
        if scope:
            collections = [s.strip() for s in scope.split(",") if s.strip()]
        else:
            collections = [wd["collection"] for wd in cfg.get("watch_dirs", [])]

        total = 0
        for coll_name in collections:
            for wd in cfg.get("watch_dirs", []):
                if wd["collection"] == coll_name:
                    dir_path = wd["path"]
                    if Path(dir_path).is_dir():
                        stats = await index_directory(client, dir_path, coll_name, cfg)
                        total += stats.get("added_chunks", 0)
                    break

        return {"action": "reindexed", "collections": collections, "total_chunks": total}
    finally:
        close_client()
