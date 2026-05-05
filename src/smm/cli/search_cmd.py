from __future__ import annotations

import asyncio

import click
from rich.table import Table
from rich.console import Console

from smm.core.config import load_config
from smm.core.db import get_client, close_client
from smm.core.searcher import search


@click.command()
@click.argument("query")
@click.option("--scope", "-s", default=None, help="Collection name(s), comma-separated")
@click.option("--mode", "-m", default=None, type=click.Choice(["vector", "fulltext", "hybrid"]),
              help="Search mode (default from config)")
@click.option("--n-results", "-n", default=None, type=int, help="Number of results")
def search_cmd(query: str, scope: str | None, mode: str | None, n_results: int | None) -> None:
    """Search indexed documents."""
    cfg = load_config()
    client = get_client(cfg)

    try:
        search_mode = mode or cfg["search"]["mode"]
        n = n_results or cfg["search"]["n_results"]

        if scope:
            collections = [s.strip() for s in scope.split(",") if s.strip()]
        else:
            collections = [wd["collection"] for wd in cfg.get("watch_dirs", [])]

        if not collections:
            click.echo("No collections to search. Import documents first with 'smm import'.")
            return

        results = asyncio.run(search(client, query, collections, cfg, search_mode, n))

        if not results:
            click.echo("No results found.")
            return

        console = Console()
        table = Table(title=f"Search results for '{query}' ({search_mode})")
        table.add_column("#", style="dim")
        table.add_column("File", style="cyan")
        table.add_column("Heading", style="green")
        table.add_column("Collection", style="yellow")
        table.add_column("Score", style="magenta")
        table.add_column("Content", style="white")

        for i, r in enumerate(results, 1):
            table.add_row(
                str(i),
                r["metadata"].get("file_name", "?"),
                r["metadata"].get("heading", "-"),
                r.get("collection", "-"),
                f"{r['score']:.2f}",
                r["content"][:120] + "..." if len(r["content"]) > 120 else r["content"],
            )

        console.print(table)
    finally:
        close_client()
