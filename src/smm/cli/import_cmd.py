from __future__ import annotations

import asyncio
from pathlib import Path

import click
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from smm.core.config import (
    load_config,
    resolve_collection_name,
    add_watch_dir,
)
from smm.core.db import get_client, close_client
from smm.core.indexer import index_file, index_directory


@click.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--collection", "-c", default=None, help="Collection name (auto-generated if omitted)"
)
@click.option(
    "--no-recursive", "-n", is_flag=True, default=False, help="Don't recurse into subdirectories"
)
@click.option("--no-watch", is_flag=True, default=False, help="Don't add to watch_dirs")
def import_docs(path: str, collection: str | None, no_recursive: bool, no_watch: bool) -> None:
    """Import documents from a file or directory into seekdb."""
    abs_path = str(Path(path).resolve())
    cfg = load_config()

    is_dir = Path(abs_path).is_dir()
    collection_name = collection or resolve_collection_name(abs_path, cfg)

    if not no_watch:
        cfg = add_watch_dir(cfg, abs_path, collection_name)

    client = get_client(cfg)

    try:
        if is_dir:
            _import_dir(client, abs_path, collection_name, cfg, not no_recursive)
        else:
            _import_file(client, abs_path, collection_name, cfg)
    finally:
        close_client()


def _import_dir(client, dir_path: str, collection: str, cfg: dict, recursive: bool) -> None:
    total = _count_files(dir_path, recursive)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        task = progress.add_task(f"Indexing {dir_path}", total=total)

        def on_progress(done: int, total: int, name: str) -> None:
            progress.update(task, completed=done)
            progress.update(task, description=f"Indexing {name}")

        stats = asyncio.run(
            index_directory(
                client,
                dir_path,
                collection,
                cfg,
                recursive,
                on_progress,
            )
        )

    click.echo(f"\nDone: {stats['added_chunks']} chunks indexed, {stats['skipped']} unchanged")


def _import_file(client, file_path: str, collection: str, cfg: dict) -> None:
    result = asyncio.run(index_file(client, file_path, collection, cfg))
    if result["skipped"]:
        click.echo(f"Unchanged: {file_path}")
    else:
        click.echo(f"Indexed {file_path} → {result['added_chunks']} chunks")


def _count_files(dir_path: str, recursive: bool) -> int:
    pattern = "**/*" if recursive else "*"
    from smm.core.indexer import _is_supported

    return sum(1 for f in Path(dir_path).glob(pattern) if f.is_file() and _is_supported(str(f)))
