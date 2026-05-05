from __future__ import annotations

import click

from smm.core.config import load_config
from smm.mcp.server import run_stdio_server


@click.command()
def mcp() -> None:
    """Start MCP server in stdio mode for AI tool integration."""
    cfg = load_config()
    run_stdio_server(cfg)
