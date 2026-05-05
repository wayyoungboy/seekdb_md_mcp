from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from smm.mcp.server import get_mcp_server

logger = logging.getLogger("smm.mcp_sse")


def create_mcp_sse_app(cfg: dict):
    """Create SSE MCP endpoint for FastAPI mounting."""
    server = get_mcp_server(cfg)
    from mcp.server.sse import SseServerTransport
    from starlette.routing import Mount, Route
    from starlette.applications import Starlette

    sse = SseServerTransport("/messages/")

    async def handle_sse(scope, receive, send):
        async with sse.connect_sse(scope, receive, send) as streams:
            await server.run(streams[0], streams[1], server.create_initialization_options())

    app = Starlette(routes=[
        Route("/sse", endpoint=handle_sse),
        Mount("/messages/", app=sse.handle_post_message),
    ])
    return app
