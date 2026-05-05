from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from smm.mcp.tools import (
    smm_search,
    smm_list_collections,
    smm_get_document,
    smm_import_tool,
    smm_remove_tool,
    smm_status_tool,
    smm_reindex,
)

logger = logging.getLogger("smm.mcp")

mcp: FastMCP | None = None
_current_cfg: dict | None = None


def get_mcp_server(cfg: dict) -> FastMCP:
    global mcp, _current_cfg
    if mcp is not None:
        return mcp

    _current_cfg = cfg
    mcp = FastMCP("smm")

    mcp.add_tool(smm_search)
    mcp.add_tool(smm_list_collections)
    mcp.add_tool(smm_get_document)
    mcp.add_tool(smm_import_tool)
    mcp.add_tool(smm_remove_tool)
    mcp.add_tool(smm_status_tool)
    mcp.add_tool(smm_reindex)

    return mcp


def run_stdio_server(cfg: dict) -> None:
    server = get_mcp_server(cfg)
    server.run(transport="stdio")
