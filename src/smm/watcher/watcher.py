from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path

from watchfiles import Change, awatch, DefaultFilter

from smm.core.config import normalize_path
from smm.core.indexer import index_file, reindex_file, remove_file, _is_supported

logger = logging.getLogger("smm.watcher")


class WatchFilesFilter(DefaultFilter):
    def __init__(self, allow_dirs: tuple[str, ...] = (), ignore_paths: tuple[str, ...] = ()):
        super().__init__(allow_dirs=allow_dirs, ignore_paths=ignore_paths)
        self._allowed = allow_dirs

    def __call__(self, change: Change, path: str) -> bool:
        if not _is_supported(path):
            return False
        return super().__call__(change, path)


class DirectoryWatcher:
    def __init__(self, client, cfg: dict):
        self.client = client
        self.cfg = cfg
        self._debounce: dict[str, tuple[float, set]] = {}
        self._debounce_interval = 0.5
        self._running = False

    async def start(self) -> None:
        self._running = True
        watch_dirs = self.cfg.get("watch_dirs", [])
        if not watch_dirs:
            logger.info("No directories to watch")
            return

        tasks = []
        for wd in watch_dirs:
            path = wd["path"]
            collection = wd["collection"]
            if Path(normalize_path(path)).exists():
                tasks.append(self._watch_one_dir(path, collection))
            else:
                logger.warning("Watch directory not found: %s", path)

        if tasks:
            await asyncio.gather(*tasks)

    def stop(self) -> None:
        self._running = False

    async def _watch_one_dir(self, path: str, collection: str) -> None:
        abs_path = normalize_path(path)
        filter = WatchFilesFilter(allow_dirs=(abs_path,))

        async for changes in awatch(abs_path, watch_filter=filter, recursive=True):
            if not self._running:
                break

            batch: dict[str, set] = {}
            for change_type, file_path in changes:
                batch.setdefault(file_path, set()).add(change_type)

            for file_path, change_types in batch.items():
                if not self._running:
                    break
                await self._handle_changes(file_path, change_types, collection)

    async def _handle_changes(
        self, file_path: str, change_types: set, collection: str
    ) -> None:
        now = time.monotonic()

        key = file_path
        if key not in self._debounce:
            self._debounce[key] = (now, set())

        prev_time, prev_types = self._debounce[key]
        self._debounce[key] = (now, prev_types | change_types)

        if now - prev_time < self._debounce_interval:
            return

        self._debounce.pop(key, None)
        final_types = prev_types | change_types

        try:
            if Change.deleted in final_types and Change.added not in final_types:
                await remove_file(self.client, file_path, collection, self.cfg)
                logger.info("[watch] %s deleted", file_path)
            elif Change.modified in final_types or Change.added in final_types:
                await reindex_file(self.client, file_path, collection, self.cfg)
                logger.info("[watch] %s updated", file_path)
        except Exception as e:
            logger.error("[watch] Error processing %s: %s", file_path, e)
