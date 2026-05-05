from __future__ import annotations

import os
import signal
import subprocess
import sys

import click

from smm.core.config import load_config, PID_PATH
from smm.server.daemon import start_daemon


@click.command()
@click.option("--daemon", "-d", is_flag=True, default=False, help="Run in background")
@click.option("--port", "-p", default=None, type=int, help="Web server port")
@click.option("--restart", "-r", is_flag=True, default=False, help="Restart daemon")
def serve(daemon: bool, port: int | None, restart: bool) -> None:
    """Start web UI, file watcher, and SSE MCP endpoint."""
    cfg = load_config()

    if port:
        cfg["web"]["port"] = port

    if restart:
        _stop_daemon()

    if PID_PATH.exists():
        click.echo("Daemon is already running. Use 'smm stop' first or 'smm serve --restart'.")
        return

    if daemon:
        _start_background(cfg)
    else:
        start_daemon(cfg)


def _start_background(cfg: dict) -> None:
    cmd = [sys.executable, "-m", "smm.cli.main", "serve"]
    proc = subprocess.Popen(
        cmd,
        start_new_session=True,
        stdout=open("/dev/null", "w"),
        stderr=subprocess.STDOUT,
    )
    click.echo(f"Daemon started in background (PID {proc.pid})")
    click.echo(f"Web:    http://{cfg['web']['host']}:{cfg['web']['port']}")
    click.echo(f"MCP SSE: http://{cfg['web']['host']}:{cfg['mcp']['sse_port']}/sse")
