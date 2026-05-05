from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

from smm.core.config import PID_PATH, LOG_PATH, SMM_DIR, load_config
from smm.core.db import get_client, close_client
from smm.watcher.watcher import DirectoryWatcher

logger = logging.getLogger("smm.daemon")


def setup_logging() -> logging.Logger:
    SMM_DIR.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(LOG_PATH)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s %(message)s"
    ))

    root = logging.getLogger("smm")
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    root.addHandler(logging.StreamHandler(sys.stderr))

    return root


def _write_pid(cfg: dict) -> None:
    PID_PATH.write_text(json.dumps({
        "pid": os.getpid(),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "web_port": cfg["web"]["port"],
        "sse_port": cfg["mcp"]["sse_port"],
        "watch_dirs": [
            {"path": wd["path"], "collection": wd["collection"]}
            for wd in cfg.get("watch_dirs", [])
        ],
    }))


async def start_daemon(cfg: dict) -> None:
    setup_logging()
    logger.info("Starting smm daemon (PID %d)", os.getpid())
    _write_pid(cfg)

    client = get_client(cfg)
    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    def _handle_signal(sig):
        logger.info("Received signal %s, shutting down...", sig)
        stop_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: _handle_signal(s))

    # Start tasks
    tasks = []

    # 1. Web server
    from smm.server.app import create_app
    from smm.server.mcp_sse import create_mcp_sse_app
    from smm.core.db import get_or_create_collection

    app = create_app(cfg, client)
    import uvicorn
    config = uvicorn.Config(
        app=app,
        host=cfg["web"]["host"],
        port=cfg["web"]["port"],
        log_level="info",
        access_log=False,
    )
    server = uvicorn.Server(config)
    tasks.append(asyncio.create_task(server.serve()))

    # 2. File watcher
    watcher = DirectoryWatcher(client, cfg)
    tasks.append(asyncio.create_task(watcher.start()))

    # Wait for stop
    await stop_event.wait()

    # Graceful shutdown
    logger.info("Shutting down...")
    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)
    close_client()

    if PID_PATH.exists():
        PID_PATH.unlink()

    logger.info("Daemon stopped.")


if __name__ == "__main__":
    cfg = load_config()
    asyncio.run(start_daemon(cfg))
