---
name: smm
description: Search and manage local documents indexed by smm (seekdb Markdown MCP). Supports semantic search, hybrid search, and document management across multiple collections.
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
