from __future__ import annotations

import click

from smm.core.config import init_config, save_config


@click.command()
def init() -> None:
    """Initialize ~/.smm/ directory and configuration."""
    cfg = init_config()
    mode = cfg["database"]["mode"]

    if mode == "embedded":
        db_info = f"embedded ({cfg['database']['embedded']['path']})"
    else:
        srv = cfg["database"]["server"]
        db_info = f"server ({srv['host']}:{srv['port']})"

    click.echo("\nsmm initialized successfully!")
    click.echo(f"\nConfig: ~/.smm/config.yaml")
    click.echo(f"Database: {db_info}")
    click.echo("\nNext steps:")
    click.echo("  smm import /path/to/docs    Import documents")
    click.echo("  smm serve --daemon          Start web + watcher")
    click.echo("  smm mcp                     Start MCP server (stdio)")
