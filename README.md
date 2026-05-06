# SMM — seekdb Markdown MCP

[中文文档](README_zh.md)

> Zero Config, Auto-Indexing, Semantic Search, Infinite Evolution.

Index your local Markdown, TXT, and RST documents into [seekdb](https://github.com/oceanbase/seekdb). Provide MCP service for AI tool integration with real-time file watching and a full-featured web dashboard.

## Features

- **Semantic Search** — Vector-based semantic search with hybrid, vector, and fulltext modes
- **Real-time Sync** — Watch directories for changes with 0.5s debounce, auto-index new/modified/deleted files
- **MCP Integration** — Exposes MCP service via stdio and SSE transports, works with Claude Code, Cursor, and any MCP-compatible tool
- **Smart Chunking** — Markdown by headings, TXT by paragraphs, RST by sections with automatic oversized-text splitting
- **Multi-Collection** — Each watched directory maps to an independent collection with scoped or cross-collection search
- **Web Dashboard** — Full-featured React UI with search, document management, config editing, and real-time log streaming

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Initialize configuration
smm init

# Import documents
smm import ~/my-notes

# Start web UI with file watcher
smm serve --daemon

# Or start MCP server for AI tools
smm mcp

# Search from CLI
smm search "how to deploy" --mode hybrid

# Check daemon status
smm status
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `smm init` | Create config directory and initialize database |
| `smm import <path>` | Index documents from a directory |
| `smm search <query>` | Search indexed documents (vector/fulltext/hybrid) |
| `smm serve` | Start web UI + file watcher daemon |
| `smm serve --daemon` | Run in background |
| `smm mcp` | Start MCP server (stdio mode) |
| `smm status` | Check daemon status |
| `smm stop` | Stop running daemon |
| `smm skill` | Display Claude Code skill configuration |

## Architecture

```
CLI                           Daemon
 smm init ──────────────────> FastAPI Web UI + File Watcher + SSE MCP
 smm import ────────────────> seekdb (HNSW vector + fulltext index)
 smm search ────────────────> MCP: search / import / get_document / ...
 smm serve ─────────────────> Web Dashboard (React + Vite + Tailwind)
```

## Configuration

Config lives in `~/.smm/config.yaml`:

```yaml
database:
  path: ~/.smm/seekdb.db
  mode: embedded  # embedded or server
embedding:
  model: text-embedding-3-small
  dimension: 1536
chunking:
  max_tokens: 512
  overlap: 50
search:
  top_k: 10
  mode: hybrid
web:
  host: 127.0.0.1
  port: 8080
mcp:
  sse_port: 8081
watch_dirs:
  - path: ~/my-notes
    collection: notes
```

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, Uvicorn, click, watchfiles
- **Database**: seekdb (pyseekdb) — HNSW vector index + fulltext index
- **Frontend**: React 18, Vite, Tailwind CSS
- **MCP**: MCP SDK with stdio + SSE transports
- **Config**: YAML with env variable overrides

## Development

```bash
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## License

Apache 2.0
