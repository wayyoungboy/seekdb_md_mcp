from __future__ import annotations

import logging
from typing import Any

import pyseekdb

from smm.core.config import normalize_path

logger = logging.getLogger("smm.db")

_client: pyseekdb.Client | None = None
_admin: pyseekdb.AdminClient | None = None


def get_client(cfg: dict[str, Any]) -> pyseekdb.Client:
    global _client
    if _client is not None:
        return _client

    mode = cfg["database"]["mode"]
    if mode == "embedded":
        path = normalize_path(cfg["database"]["embedded"]["path"])
        _client = pyseekdb.Client(path=path)
        logger.info("Connected to seekdb (embedded: %s)", path)
    elif mode == "server":
        srv = cfg["database"]["server"]
        _client = pyseekdb.Client(
            host=srv["host"],
            port=srv["port"],
            user=srv["user"],
            password=srv["password"],
            database=srv["database"],
        )
        logger.info("Connected to seekdb (server: %s:%s)", srv["host"], srv["port"])
    else:
        raise ValueError(f"Unknown database mode: {mode}")

    return _client


def get_admin(cfg: dict[str, Any]) -> pyseekdb.AdminClient | None:
    global _admin
    if _admin is not None:
        return _admin

    mode = cfg["database"]["mode"]
    if mode == "embedded":
        path = normalize_path(cfg["database"]["embedded"]["path"])
        _admin = pyseekdb.AdminClient(path=path)
    return _admin


def close_client() -> None:
    global _client, _admin
    _client = None
    _admin = None


def get_or_create_collection(
    client: pyseekdb.Client,
    name: str,
    cfg: dict[str, Any],
) -> Any:
    embedding_fn = _build_embedding_function(cfg)
    config = _build_collection_config(cfg, embedding_fn)
    return client.get_or_create_collection(
        name=name,
        configuration=config,
        embedding_function=embedding_fn,
    )


def _build_embedding_function(cfg: dict[str, Any]) -> Any:
    provider = cfg["embedding"]["provider"]
    if provider == "default":
        return pyseekdb.DefaultEmbeddingFunction()

    ef_cfg = cfg["embedding"]
    if provider == "openai":
        from pyseekdb.embedding_functions import OpenAIEmbeddingFunction

        return OpenAIEmbeddingFunction(
            api_key=ef_cfg["api_key"],
            model_name=ef_cfg.get("model", "text-embedding-3-small"),
        )
    elif provider == "ollama":
        from pyseekdb.embedding_functions import OllamaEmbeddingFunction

        return OllamaEmbeddingFunction(
            model_name=ef_cfg.get("model", "all-minilm"),
            url=ef_cfg.get("url", "http://localhost:11434"),
        )
    elif provider == "jina":
        from pyseekdb.embedding_functions import JinaEmbeddingFunction

        return JinaEmbeddingFunction(
            api_key=ef_cfg["api_key"],
            model_name=ef_cfg.get("model", "jina-embeddings-v3"),
        )
    elif provider == "huggingface":
        from pyseekdb.embedding_functions import HuggingFaceEmbeddingFunction

        return HuggingFaceEmbeddingFunction(
            model_name=ef_cfg.get("model", "all-MiniLM-L6-v2"),
        )
    else:
        logger.warning("Unknown embedding provider '%s', falling back to default", provider)
        return pyseekdb.DefaultEmbeddingFunction()


def _build_collection_config(cfg: dict[str, Any], embedding_fn: Any) -> Any:
    dim = getattr(embedding_fn, "dimension", 384) if embedding_fn else 384
    hnsw_config = pyseekdb.HNSWConfiguration(dimension=dim, distance="cosine")
    try:
        fulltext_config = pyseekdb.FulltextIndexConfig(
            analyzer="ik",
            properties={"ik_mode": "max_words"},
        )
        return pyseekdb.Configuration(hnsw=hnsw_config, fulltext_config=fulltext_config)
    except Exception:
        return hnsw_config
