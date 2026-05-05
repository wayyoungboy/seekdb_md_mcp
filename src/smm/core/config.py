from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

SMM_DIR = Path(os.environ.get("SMM_HOME", "~/.smm")).expanduser()
CONFIG_PATH = SMM_DIR / "config.yaml"
PID_PATH = SMM_DIR / "daemon.pid"
LOG_PATH = SMM_DIR / "daemon.log"

DEFAULT_CONFIG: dict[str, Any] = {
    "database": {
        "mode": "embedded",
        "embedded": {
            "path": str(SMM_DIR / "seekdb.db"),
        },
        "server": {
            "host": "127.0.0.1",
            "port": 2881,
            "user": "root",
            "password": "",
            "database": "smm",
        },
    },
    "embedding": {
        "provider": "default",
    },
    "chunking": {
        "strategy": "semantic",
        "semantic": {
            "md_split_by": "heading",
            "txt_split_by": "paragraph",
            "rst_split_by": "section",
        },
        "fixed": {
            "chunk_size": 1000,
            "chunk_overlap": 200,
        },
        "max_chunk_size": 2000,
        "overlap": 200,
    },
    "watch_dirs": [],
    "web": {
        "host": "127.0.0.1",
        "port": 8080,
    },
    "mcp": {
        "sse_port": 6000,
    },
    "search": {
        "mode": "hybrid",
        "n_results": 10,
    },
}


def normalize_path(path: str) -> str:
    return str(Path(path).expanduser().resolve())


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load_config() -> dict[str, Any]:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            user_cfg = yaml.safe_load(f) or {}
        cfg = _deep_merge(DEFAULT_CONFIG, user_cfg)
    else:
        cfg = DEFAULT_CONFIG.copy()

    _apply_env_overrides(cfg)
    return cfg


def _apply_env_overrides(cfg: dict[str, Any]) -> None:
    env_map = {
        "SMM_DB_MODE": ("database", "mode"),
        "SMM_DB_HOST": ("database", "server", "host"),
        "SMM_DB_PORT": ("database", "server", "port"),
        "SMM_DB_USER": ("database", "server", "user"),
        "SMM_DB_PASSWORD": ("database", "server", "password"),
        "SMM_DB_DATABASE": ("database", "server", "database"),
        "SMM_EMBEDDING_PROVIDER": ("embedding", "provider"),
        "SMM_WEB_HOST": ("web", "host"),
        "SMM_WEB_PORT": ("web", "port"),
        "SMM_MCP_SSE_PORT": ("mcp", "sse_port"),
    }
    for env_key, path in env_map.items():
        val = os.environ.get(env_key)
        if val is not None:
            obj = cfg
            for p in path[:-1]:
                obj = obj[p]
            key = path[-1]
            if isinstance(obj.get(key), int):
                val = int(val)
            obj[key] = val


def save_config(cfg: dict[str, Any]) -> None:
    SMM_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def init_config() -> dict[str, Any]:
    SMM_DIR.mkdir(parents=True, exist_ok=True)
    (SMM_DIR / "logs").mkdir(exist_ok=True)
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
    return load_config()


def get_watch_dir_config(cfg: dict[str, Any], collection_name: str) -> dict | None:
    for wd in cfg.get("watch_dirs", []):
        if wd.get("collection") == collection_name:
            return wd
    return None


def add_watch_dir(cfg: dict[str, Any], path: str, collection: str) -> dict[str, Any]:
    abs_path = normalize_path(path)
    for wd in cfg.get("watch_dirs", []):
        if normalize_path(wd["path"]) == abs_path:
            return cfg

    cfg.setdefault("watch_dirs", []).append({
        "path": abs_path,
        "collection": collection,
    })
    save_config(cfg)
    return cfg


def resolve_collection_name(path: str, cfg: dict[str, Any]) -> str:
    abs_path = normalize_path(path)
    p = Path(abs_path)

    for wd in cfg.get("watch_dirs", []):
        if normalize_path(wd["path"]) == abs_path:
            return wd["collection"]

    existing = {wd["collection"] for wd in cfg.get("watch_dirs", [])}

    candidate = p.name
    if candidate not in existing:
        return candidate

    candidate = f"{p.parent.name}_{p.name}"
    if candidate not in existing:
        return candidate

    candidate = f"{p.parent.parent.name}_{p.parent.name}_{p.name}"
    if candidate not in existing:
        return candidate

    base = p.name
    suffix = 2
    while f"{base}_{suffix}" in existing:
        suffix += 1
    return f"{base}_{suffix}"
