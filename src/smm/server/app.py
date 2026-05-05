from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from smm.core.config import (
    load_config, save_config, resolve_collection_name, add_watch_dir,
    normalize_path, SMM_DIR, PID_PATH,
)
from smm.core.db import get_client, close_client, get_or_create_collection
from smm.core.searcher import search as do_search
from smm.core.indexer import index_directory, index_file, remove_file

logger = logging.getLogger("smm.server")


class SearchRequest(BaseModel):
    query: str
    scope: str | None = None
    mode: str = "hybrid"
    n_results: int = 10


class ImportRequest(BaseModel):
    path: str
    collection: str | None = None


class ConfigUpdate(BaseModel):
    config: dict


def create_app(cfg: dict, client) -> FastAPI:
    app = FastAPI(title="smm", version="0.1.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"])

    # Shared state
    _cfg: dict = cfg
    _client = client

    # Log broadcaster for WebSocket
    _log_subscribers: list[WebSocket] = []
    _log_buffer: list[str] = []
    MAX_BUFFER = 500

    def broadcast_log(msg: str) -> None:
        _log_buffer.append(msg)
        if len(_log_buffer) > MAX_BUFFER:
            _log_buffer.pop(0)
        dead = []
        for ws in _log_subscribers:
            try:
                asyncio.create_task(ws.send_text(msg))
            except Exception:
                dead.append(ws)
        for ws in dead:
            _log_subscribers.remove(ws)

    # --- Install custom log handler ---
    class WSLogHandler(logging.Handler):
        def emit(self, record):
            broadcast_log(self.format(record))

    handler = WSLogHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s %(message)s"))
    logging.getLogger("smm").addHandler(handler)

    # --- API Routes ---

    @app.get("/api/search")
    async def api_search(query: str, scope: str | None = None, mode: str = "hybrid", n_results: int = 10):
        collections = resolve_collections(scope, _cfg)
        results = await do_search(_client, query, collections, _cfg, mode, n_results)
        broadcast_log(f"[search] query=\"{query}\" scope={scope or 'all'} mode={mode}")
        return results

    @app.get("/api/collections")
    async def api_list_collections():
        result = []
        for wd in _cfg.get("watch_dirs", []):
            coll_name = wd["collection"]
            try:
                collection = get_or_create_collection(_client, coll_name, _cfg)
                count = collection.count()
                result.append({
                    "collection": coll_name,
                    "path": wd["path"],
                    "total_chunks": count,
                })
            except Exception as e:
                result.append({"collection": coll_name, "path": wd["path"], "error": str(e)})
        return result

    @app.get("/api/collections/{name}")
    async def api_collection_detail(name: str):
        collection = get_or_create_collection(_client, name, _cfg)
        result = collection.get(include=["documents", "metadatas"])
        files: dict[str, dict] = {}
        if result and result.get("metadatas"):
            metadatas = result["metadatas"] or []
            ids = result.get("ids", []) or []
            for i, meta in enumerate(metadatas):
                fp = meta.get("file_path", "unknown")
                if fp not in files:
                    files[fp] = {
                        "file_path": fp,
                        "file_name": meta.get("file_name", "?"),
                        "chunks": 0,
                        "indexed_at": meta.get("indexed_at", "?"),
                    }
                files[fp]["chunks"] += 1

        return {"collection": name, "files": list(files.values())}

    @app.post("/api/collections/{name}/reindex")
    async def api_reindex_collection(name: str):
        for wd in _cfg.get("watch_dirs", []):
            if wd["collection"] == name:
                dir_path = wd["path"]
                if Path(dir_path).is_dir():
                    stats = await index_directory(_client, dir_path, name, _cfg)
                    broadcast_log(f"[reindex] {name} → {stats.get('added_chunks', 0)} chunks")
                    return stats
        return {"error": "Collection not found"}

    @app.delete("/api/collections/{name}")
    async def api_delete_collection(name: str):
        _client.delete_collection(name)
        _cfg["watch_dirs"] = [
            wd for wd in _cfg.get("watch_dirs", [])
            if wd["collection"] != name
        ]
        save_config(_cfg)
        broadcast_log(f"[delete] collection {name} removed")
        return {"status": "deleted"}

    @app.post("/api/import")
    async def api_import(req: ImportRequest):
        abs_path = normalize_path(req.path)
        coll_name = req.collection or resolve_collection_name(abs_path, _cfg)
        add_watch_dir(_cfg, abs_path, coll_name)

        if Path(abs_path).is_dir():
            stats = await index_directory(_client, abs_path, coll_name, _cfg)
            broadcast_log(f"[import] {abs_path} → {coll_name}")
            return {"action": "imported_directory", **stats}
        else:
            stats = await index_file(_client, abs_path, coll_name, _cfg)
            broadcast_log(f"[import] {abs_path}")
            return {"action": "imported_file", **stats}

    @app.get("/api/config")
    async def api_get_config():
        return _cfg

    @app.put("/api/config")
    async def api_update_config(req: ConfigUpdate):
        nonlocal _cfg
        _cfg = req.config
        save_config(_cfg)
        return _cfg

    @app.get("/api/status")
    async def api_status():
        running = False
        pid_data = {}
        if PID_PATH.exists():
            try:
                pid_data = json.loads(PID_PATH.read_text())
                os.kill(pid_data["pid"], 0)
                running = True
            except (OSError, json.JSONDecodeError):
                pass

        return {
            "running": running,
            "pid": pid_data.get("pid"),
            "started_at": pid_data.get("started_at"),
            "web_port": _cfg["web"]["port"],
            "sse_port": _cfg["mcp"]["sse_port"],
            "watch_dirs": _cfg.get("watch_dirs", []),
        }

    @app.post("/api/daemon/stop")
    async def api_stop_daemon():
        if PID_PATH.exists():
            import json
            data = json.loads(PID_PATH.read_text())
            os.kill(data["pid"], 15)
        return {"status": "stopping"}

    @app.post("/api/daemon/restart")
    async def api_restart_daemon():
        if PID_PATH.exists():
            import json
            data = json.loads(PID_PATH.read_text())
            os.kill(data["pid"], 15)
        return {"status": "restarting"}

    @app.get("/api/integration")
    async def api_integration():
        return {
            "stdio": {"command": "smm", "args": ["mcp"]},
            "sse": {
                "type": "sse",
                "url": f"http://{_cfg['web']['host']}:{_cfg['mcp']['sse_port']}/sse",
            },
            "skill": "smm skill --install",
        }

    @app.websocket("/api/ws/logs")
    async def ws_logs(websocket: WebSocket):
        await websocket.accept()
        _log_subscribers.append(websocket)
        for msg in _log_buffer[-50:]:
            await websocket.send_text(msg)
        try:
            while True:
                await websocket.receive_text()
        except Exception:
            if websocket in _log_subscribers:
                _log_subscribers.remove(websocket)

    # --- Static files ---
    web_dist = Path(__file__).parent.parent.parent.parent / "web" / "dist"
    if web_dist.exists():
        app.mount("/static", StaticFiles(directory=str(web_dist)), name="static")
        app.mount("/assets", StaticFiles(directory=str(web_dist / "assets")), name="assets")

        @app.get("/{path:path}")
        async def serve_frontend(path: str):
            file_path = web_dist / path
            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(web_dist / "index.html")
    else:
        @app.get("/")
        async def root():
            return HTMLResponse("<h1>SMM</h1><p>Frontend not built. Run: cd web && npm run build</p>")

    return app


def resolve_collections(scope: str | None, cfg: dict) -> list[str]:
    if scope:
        return [s.strip() for s in scope.split(",") if s.strip()]
    return [wd["collection"] for wd in cfg.get("watch_dirs", [])]
