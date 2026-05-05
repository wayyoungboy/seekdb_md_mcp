from __future__ import annotations

import os
import signal
import time

import click

from smm.core.config import PID_PATH, LOG_PATH


@click.command()
def status() -> None:
    """Show daemon status and index stats."""
    if not PID_PATH.exists():
        click.echo("smm daemon: not running")
        click.echo("Start with: smm serve --daemon")
        return

    import json
    data = json.loads(PID_PATH.read_text())
    pid = data["pid"]

    try:
        os.kill(pid, 0)
    except OSError:
        PID_PATH.unlink()
        click.echo("smm daemon: stopped (stale PID file cleaned)")
        return

    started = data.get("started_at", "?")
    web_port = data.get("web_port", "?")
    sse_port = data.get("sse_port", "?")
    watch_dirs = data.get("watch_dirs", [])

    click.echo(f"smm daemon: running (PID {pid}, started {started})")
    click.echo(f"  Web:     http://127.0.0.1:{web_port}")
    click.echo(f"  MCP SSE: http://127.0.0.1:{sse_port}/sse")
    if watch_dirs:
        click.echo("  Watching:")
        for wd in watch_dirs:
            click.echo(f"    {wd.get('collection', '?')}  →  {wd.get('path', '?')}")


@click.command()
def stop() -> None:
    """Stop the running daemon."""
    if not PID_PATH.exists():
        click.echo("Daemon is not running.")
        return

    import json
    data = json.loads(PID_PATH.read_text())
    pid = data["pid"]

    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        PID_PATH.unlink()
        click.echo("Daemon was not running (stale PID file cleaned).")
        return

    for _ in range(20):
        try:
            os.kill(pid, 0)
            time.sleep(0.5)
        except OSError:
            break
    else:
        click.echo("Warning: daemon did not stop gracefully. Stale PID removed.")

    if PID_PATH.exists():
        PID_PATH.unlink()
    click.echo("Daemon stopped.")
