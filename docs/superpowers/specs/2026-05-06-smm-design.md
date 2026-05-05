# SMM (seekdb Markdown MCP) Design Spec

## Overview

SMM is a CLI tool that indexes local documents (`.md`, `.txt`, `.rst`) into seekdb, provides MCP services for AI tool integration, watches directories for changes, and serves a web management interface.

**Architecture**: CLI + Daemon. CLI handles one-shot operations (init, import, search). Daemon handles persistent tasks (web server, file watching, SSE MCP).

## Project Structure

```
seekdb_md_mcp/
├── pyproject.toml
├── src/
│   └── smm/
│       ├── __init__.py
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py            # smm main command group
│       │   ├── init_cmd.py        # smm init
│       │   ├── import_cmd.py      # smm import /path
│       │   ├── search_cmd.py      # smm search "query"
│       │   ├── serve_cmd.py       # smm serve
│       │   ├── mcp_cmd.py         # smm mcp (stdio)
│       │   └── status_cmd.py      # smm status / smm stop
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py          # ~/.smm/config.yaml management
│       │   ├── db.py              # seekdb connection (embedded/server)
│       │   ├── chunker.py         # document chunking (semantic/fixed)
│       │   ├── indexer.py         # parse → chunk → embed → store
│       │   └── searcher.py        # vector/fulltext/hybrid search
│       ├── watcher/
│       │   ├── __init__.py
│       │   └── watcher.py         # watchfiles directory monitoring
│       ├── server/
│       │   ├── __init__.py
│       │   ├── daemon.py          # daemon lifecycle (start/stop/status)
│       │   ├── app.py             # FastAPI app (web API + static frontend)
│       │   └── mcp_sse.py         # SSE transport MCP endpoint
│       ├── mcp/
│       │   ├── __init__.py
│       │   ├── server.py          # MCP server (shared by stdio/SSE)
│       │   └── tools.py           # MCP tool definitions
│       └── skill/
│           └── SKILL.md           # Claude Code skill
├── web/                           # React + Vite + Tailwind CSS
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── App.tsx
│       ├── pages/
│       │   ├── Search.tsx
│       │   ├── Documents.tsx
│       │   ├── Settings.tsx
│       │   └── Logs.tsx
│       └── components/
└── tests/
```

## Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python 3.11 | User requirement |
| CLI | click | Mature subcommand support |
| Web framework | FastAPI | Async native, WebSocket, OpenAPI |
| File watcher | watchfiles | Rust-based, high performance |
| MCP SDK | mcp (official) | Anthropic official Python MCP SDK |
| Frontend | React + Vite + Tailwind CSS | Modern, lightweight, builds to static files |
| Config format | YAML | Human-readable, easy to edit |
| Database | seekdb (pyseekdb) | AI-native search database |

## Configuration

### Directory: `~/.smm/`

```
~/.smm/
├── config.yaml          # main configuration
├── seekdb.db            # embedded mode database file
├── daemon.pid           # daemon PID + metadata (JSON)
├── daemon.log           # daemon log
└── logs/                # rotated historical logs
```

### `config.yaml`

```yaml
database:
  mode: embedded                  # embedded | server
  embedded:
    path: ~/.smm/seekdb.db
  server:
    host: 127.0.0.1
    port: 2881
    user: root
    password: ""
    database: smm

embedding:
  provider: default               # default | openai | jina | ollama | ...
  # provider-specific config:
  # api_key: sk-xxx
  # model: text-embedding-3-small

chunking:
  strategy: semantic              # semantic | fixed
  semantic:
    md_split_by: heading
    txt_split_by: paragraph
    rst_split_by: section
  fixed:
    chunk_size: 1000
    chunk_overlap: 200
  max_chunk_size: 2000            # hard limit per chunk
  overlap: 200                    # overlap when splitting oversized chunks

watch_dirs: []
#  - path: /home/user/notes
#    collection: notes

web:
  host: 127.0.0.1
  port: 8080

mcp:
  sse_port: 6000

search:
  mode: hybrid                    # vector | fulltext | hybrid
  n_results: 10
```

### Config Priority

CLI parameters > environment variables (`SMM_*`) > `config.yaml`

### Path Normalization

All paths are stored as absolute paths. Relative paths, `~`, and symlinks are resolved on input:

```python
def normalize_path(path: str) -> str:
    return str(Path(path).expanduser().resolve())
```

## CLI Commands

| Command | Type | Description |
|---------|------|-------------|
| `smm init` | One-shot | Initialize `~/.smm/`, generate config, create seekdb collections |
| `smm import /path` | One-shot | Scan and index documents, then exit |
| `smm search "query"` | One-shot | Search and output results, then exit |
| `smm serve` | Daemon | Start web + file watcher + SSE MCP |
| `smm mcp` | Long-running | stdio MCP server for AI tools |
| `smm status` | One-shot | Show daemon status and index stats |
| `smm stop` | One-shot | Stop the daemon |

### `smm import` Details

```bash
smm import /path/to/docs                        # auto-name collection from dir name
smm import /path/to/docs --collection my_docs   # custom collection name
smm import /path/to/file.md                     # single file
smm import /path --no-recursive                  # no recursion (default: recursive)
smm import /path --no-watch                      # don't add to watch_dirs
```

- Shows progress bar (files/chunks)
- Outputs stats: added X files / Y chunks, updated Z files, skipped W files
- Auto-adds path to `config.yaml` `watch_dirs` (unless `--no-watch`)

## Collection Naming

Each `watch_dir` maps to an independent seekdb collection.

### Auto-naming Rules

1. User specified `collection` name -> use it, error on conflict
2. Not specified -> try last directory component (e.g., `/home/user/notes` -> `notes`)
3. Conflict -> prepend parent: `parent_dirname` (e.g., `work_notes`)
4. Still conflict -> prepend grandparent: `grandparent_parent_dirname`
5. Extreme case -> append numeric suffix: `dirname_2`

Auto-generated names are written back to `config.yaml` for transparency:

```yaml
watch_dirs:
  - path: /home/user/notes
    collection: notes
  - path: /home/user/work/notes
    collection: work_notes
```

## Document Processing Pipeline

### Flow

```
File Discovery → Parse → Chunk → Embed → Store in seekdb
```

### Chunk Schema in seekdb

```python
{
    "id": "sha256(file_path + chunk_index)",
    "document": "chunk text content",
    "metadata": {
        "file_path": "/absolute/path/to/doc.md",
        "file_name": "doc.md",
        "file_type": "md",
        "chunk_index": 0,
        "total_chunks": 5,
        "heading": "## Installation Guide",
        "file_hash": "abc123...",
        "indexed_at": "2026-05-06T10:30:00Z"
    }
}
```

### Semantic Chunking Strategy

| Format | Strategy | Split Points |
|--------|----------|-------------|
| `.md` | By heading | `#` / `##` / `###` boundaries, heading preserved as context |
| `.txt` | By paragraph | Consecutive blank lines |
| `.rst` | By section | reStructuredText section markers (`===`/`---`/`~~~`) |

When a single chunk exceeds `max_chunk_size` (default 2000 chars), further split at sentence boundaries with `overlap` (default 200 chars).

### Change Detection

Used by both `smm import` and the file watcher:

| Condition | Action |
|-----------|--------|
| New file (no `file_path` in seekdb) | Parse + chunk + insert |
| Modified (different `file_hash`) | Delete old chunks + re-index |
| Unchanged (same `file_hash`) | Skip |
| Deleted (in seekdb but not on disk) | Delete corresponding chunks |

## Daemon Architecture

`smm serve` runs three concurrent asyncio tasks in one process:

```
smm serve
  └─ daemon process
       ├─ [Task 1] FastAPI Web (uvicorn)
       ├─ [Task 2] File watcher (watchfiles)
       └─ [Task 3] SSE MCP endpoint (mounted on FastAPI)
```

### Daemon Management

```bash
smm serve                    # foreground (for development)
smm serve --daemon           # background, writes PID to ~/.smm/daemon.pid
smm status                   # check daemon state
smm stop                     # send SIGTERM for graceful shutdown
smm serve --restart          # stop + start --daemon
```

### `~/.smm/daemon.pid` Format

```json
{
  "pid": 12345,
  "started_at": "2026-05-06T10:30:00Z",
  "web_port": 8080,
  "sse_port": 6000,
  "watch_dirs": ["/home/user/notes", "/home/user/docs"]
}
```

### `smm status` Output

```
smm daemon: running (PID 12345, uptime 2h 15m)
  Web:       http://127.0.0.1:8080
  MCP SSE:   http://127.0.0.1:6000/sse
  Watching:
    notes  → /home/user/notes       (142 docs, 856 chunks)
    docs   → /home/user/docs        (38 docs, 203 chunks)
```

### File Watcher Behavior

```python
async def watch_directory(path: str, collection: str):
    async for changes in awatch(path, recursive=True):
        for change_type, file_path in changes:
            if not is_supported(file_path):
                continue
            match change_type:
                case Change.added:
                    await indexer.index_file(file_path, collection)
                case Change.modified:
                    await indexer.reindex_file(file_path, collection)
                case Change.deleted:
                    await indexer.remove_file(file_path, collection)
```

- 0.5s debounce window to merge rapid consecutive events on the same file
- Only processes `.md`, `.txt`, `.rst` files

### Graceful Shutdown

On SIGTERM:
1. Stop accepting new requests
2. Wait for in-progress indexing tasks (max 10s timeout)
3. Close seekdb connections
4. Delete PID file
5. Exit

## MCP Service

### Two Transport Modes, Shared Tool Definitions

```bash
smm mcp                        # stdio transport (AI tools call directly)
smm serve (includes SSE)       # SSE transport at http://host:6000/sse
```

### MCP Tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `smm_search` | `query`, `scope?`, `mode?`, `n_results?` | Search documents (vector/fulltext/hybrid) |
| `smm_list_collections` | — | List all collections with stats |
| `smm_get_document` | `file_path` or `doc_id` | Get full document content (merged chunks) |
| `smm_import` | `path`, `collection?` | Import file or directory |
| `smm_remove` | `file_path` or `collection` | Remove file index or entire collection |
| `smm_status` | — | Get daemon status and index stats |
| `smm_reindex` | `scope?` | Re-index specified collection or all |

### Search Scope

```python
@mcp_server.tool()
async def smm_search(
    query: str,
    scope: str | None = None,       # collection name(s), comma-separated
    mode: str = "hybrid",           # vector | fulltext | hybrid
    n_results: int = 10
) -> list[dict]:
    collections = resolve_scope(scope)  # None → all collections
    results = await searcher.search(
        query=query,
        collections=collections,
        mode=mode,
        n_results=n_results
    )
    return [
        {
            "content": r.document,
            "file_path": r.metadata["file_path"],
            "file_name": r.metadata["file_name"],
            "heading": r.metadata.get("heading"),
            "score": r.score,
            "collection": r.collection
        }
        for r in results
    ]
```

Cross-collection search: query all matching collections concurrently, normalize scores, merge and sort by score, return top N.

### MCP Configuration Examples

stdio (Claude Code / Cursor):
```json
{
  "mcpServers": {
    "smm": {
      "command": "smm",
      "args": ["mcp"]
    }
  }
}
```

SSE (remote / web):
```json
{
  "mcpServers": {
    "smm": {
      "type": "sse",
      "url": "http://127.0.0.1:6000/sse"
    }
  }
}
```

## Claude Code Skill

### File Location

`src/smm/skill/SKILL.md` — packaged with Python distribution.

### Installation

```bash
smm skill --install      # register skill to Claude Code plugin directory
smm skill --uninstall    # remove
```

### SKILL.md Content

```markdown
---
name: smm
description: Search and manage local documents indexed by smm
  (seekdb Markdown MCP). Supports semantic search, hybrid search,
  and document management across multiple collections.
---

## Tools (via MCP)

This skill requires the smm MCP server. Ensure it is configured:

### Quick Setup
Run `smm mcp` for stdio mode, or `smm serve` for SSE mode.

## Capabilities

- **Search documents**: Find relevant content across indexed collections
- **Scope search**: Target specific collections for focused results
- **List collections**: See all indexed directories and their stats
- **Get full document**: Retrieve complete file content by path
- **Import new docs**: Add files/directories to the index
- **Reindex**: Force re-indexing when needed

## Usage Patterns

### Search across all documents
Use smm_search with a natural language query.

### Search specific collection
Use smm_search with scope parameter matching a collection name.

### Find then read
1. smm_search to find relevant chunks
2. smm_get_document to read the full file

### Check what's indexed
Use smm_list_collections to see all available collections.
```

The skill itself is declarative — it tells Claude Code what MCP tools are available and how to combine them. All actual logic goes through MCP tools.

## Web Frontend

### Tech Stack

React + Vite + Tailwind CSS + React Router. Built static files are embedded in the Python package and served by FastAPI `StaticFiles`.

### Design Style

Inspired by seekdb M0 (https://m0.seekdb.ai/):
- Dark theme: deep purple/dark gray background
- Monospace font (JetBrains Mono / Fira Code)
- Purple accent color for highlights and active states
- Terminal-window-style cards (three dots header)
- Clean layout with generous whitespace

### Pages

#### Search Page (`/`)

Top section: Quick Integration Guide (terminal-window card style)

```
┌─────────────────────────────────────────────────────┐
│  ● ● ●                                              │
│  — Copy and Add to your AI Tool                     │
│                                                     │
│  Tab: [Claude Code] [Cursor] [Other MCP Tools]      │
│                                                     │
│  ┌─ Claude Code ──────────────────────────────┐     │
│  │ smm skill --install                        │ 📋  │
│  └────────────────────────────────────────────┘     │
│                                                     │
│  ┌─ MCP (stdio) ──────────────────────────────┐     │
│  │ { "mcpServers": { "smm": { ... } } }      │ 📋  │
│  └────────────────────────────────────────────┘     │
│                                                     │
│  ┌─ MCP (SSE) ────────────────────────────────┐     │
│  │ { "mcpServers": { "smm": { ... } } }      │ 📋  │
│  └────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘
```

- Each config block has a one-click copy button
- SSE URL dynamically generated from actual config
- Collapsible after first use

Below: Search interface with search box, mode selector, scope dropdown, and terminal-style results.

#### Documents Page (`/documents`)

- Browse by collection
- File list with chunk count, file size, last indexed time
- Manual reindex (single file or entire collection)
- Import new directory, delete collection

#### Settings Page (`/settings`)

- Form-based editing of `config.yaml`
- Database mode toggle (embedded/server)
- Embedding provider selection with dynamic config fields
- Chunking strategy configuration
- Validation before save
- Warning when embedding provider change requires reindex

#### Logs Page (`/logs`)

- Real-time log streaming via WebSocket
- Daemon status display (running/stopped, PID, uptime)
- Stop/restart daemon controls

### Web API Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/search` | Search documents |
| GET | `/api/collections` | List all collections |
| GET | `/api/collections/{name}` | Collection detail and file list |
| POST | `/api/collections/{name}/reindex` | Reindex collection |
| DELETE | `/api/collections/{name}` | Delete collection |
| POST | `/api/import` | Import new directory |
| GET | `/api/config` | Get current config |
| PUT | `/api/config` | Update config |
| GET | `/api/status` | Daemon status |
| POST | `/api/daemon/stop` | Stop daemon |
| POST | `/api/daemon/restart` | Restart daemon |
| GET | `/api/integration` | Get integration configs (MCP JSON, skill command) |
| WS | `/api/ws/logs` | WebSocket log streaming |

## Embedding Configuration

### Default

Local `all-MiniLM-L6-v2` (384 dimensions) via seekdb's `DefaultEmbeddingFunction`. No API key required.

### Supported Providers

Configurable in `config.yaml` under `embedding.provider`:

| Provider | Requires API Key | Notes |
|----------|-----------------|-------|
| default | No | Local all-MiniLM-L6-v2, 384 dim |
| openai | Yes | text-embedding-3-small/large |
| jina | Yes | jina-embeddings-v3 |
| ollama | No | Local Ollama server |
| huggingface | No | Local sentence-transformers |
| qwen | Yes | Alibaba Qwen embedding |
| cohere | Yes | embed-english-v3.0 |

Changing provider requires reindexing all collections (dimension mismatch).

## Dependencies

```
pyseekdb
click
fastapi
uvicorn
watchfiles
mcp
pyyaml
```

## `smm init` Flow

1. Create `~/.smm/` directory
2. Generate default `config.yaml`
3. Connect to seekdb (embedded or server per config)
4. Verify connection works
5. Print success message and next-step guidance

Output:

```
smm initialized successfully!

Config: ~/.smm/config.yaml
Database: embedded (~/.smm/seekdb.db)

Next steps:
  smm import /path/to/docs    Import documents
  smm serve --daemon           Start web + watcher
  smm mcp                      Start MCP server (stdio)
```

## `smm import` Single File Handling

When importing a single file (e.g., `smm import /path/to/file.md`):
- File is added to the collection of its parent directory if that directory is already a watch_dir
- Otherwise, a new collection is created from the parent directory name, and the parent directory is added to watch_dirs
- `--collection` flag overrides this behavior

## Error Handling

| Scenario | Behavior |
|----------|----------|
| seekdb connection fails | CLI prints error with troubleshooting hints, exits 1 |
| Unsupported file type in import path | Skip with warning |
| Embedding API key missing | Error on init/import, suggest configuring in `~/.smm/config.yaml` |
| Daemon already running | `smm serve` prints existing PID and exits |
| PID file stale (process dead) | Auto-cleanup PID file, allow new daemon start |
| File watcher permission denied | Log warning, skip that directory, continue others |
| Chunk embedding fails | Log error, skip that chunk, continue indexing |

## Logging

All components use Python `logging` module with consistent format:

```
2026-05-06 10:30:01 [watch] notes/new.md added
2026-05-06 10:30:02 [index] notes/new.md → 8 chunks
2026-05-06 10:31:15 [search] query="install" scope=notes mode=hybrid
```

- Daemon writes to `~/.smm/daemon.log` with daily rotation (7 days retained)
- CLI one-shot commands log to stderr
- Web logs page streams from daemon log via WebSocket
