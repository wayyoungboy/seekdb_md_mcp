from __future__ import annotations

import logging
from typing import Any

from smm.core.db import get_or_create_collection

logger = logging.getLogger("smm.searcher")


async def search(
    client,
    query: str,
    collections: list[str],
    cfg: dict,
    mode: str = "hybrid",
    n_results: int = 10,
) -> list[dict]:
    results = []
    for coll_name in collections:
        try:
            collection = get_or_create_collection(client, coll_name, cfg)
            coll_results = _search_collection(collection, query, mode, n_results)
            for r in coll_results:
                r["collection"] = coll_name
                results.append(r)
        except Exception as e:
            logger.warning("Search failed for collection '%s': %s", coll_name, e)

    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return results[:n_results]


def _search_collection(collection, query: str, mode: str, n_results: int) -> list[dict]:
    if mode == "hybrid":
        try:
            return _hybrid_search(collection, query, n_results)
        except Exception:
            return _vector_search(collection, query, n_results)
    elif mode == "fulltext":
        return _fulltext_search(collection, query, n_results)
    else:
        return _vector_search(collection, query, n_results)


def _vector_search(collection, query: str, n_results: int) -> list[dict]:
    result = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    return _format_results(result)


def _fulltext_search(collection, query: str, n_results: int) -> list[dict]:
    result = collection.get(
        where_document={"$contains": query},
        include=["documents", "metadatas"],
    )
    items = _format_results(result)
    return items[:n_results]


def _hybrid_search(collection, query: str, n_results: int) -> list[dict]:
    try:
        result = collection.hybrid_search(
            query={
                "where_document": {"$contains": query},
                "n_results": n_results,
            },
            knn={
                "query_texts": [query],
                "n_results": n_results,
            },
            rank={"rrf": {}},
            n_results=n_results,
        )
        return _format_results(result)
    except Exception:
        return _vector_search(collection, query, n_results)


def _format_results(result: Any) -> list[dict]:
    ids = result.get("ids", []) or []
    documents = result.get("documents") or []
    metadatas = result.get("metadatas") or []
    distances = result.get("distances") or []

    items = []
    for i in range(len(ids)):
        items.append(
            {
                "id": ids[i] if isinstance(ids, list) else ids,
                "content": documents[i] if isinstance(documents, list) else documents,
                "metadata": metadatas[i] if metadatas else {},
                "score": 1.0 - distances[i] if isinstance(distances, list) and distances else 0.5,
            }
        )
    return items
