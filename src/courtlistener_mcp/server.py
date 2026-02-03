#!/usr/bin/env python3
"""
CourtListener MCP Server

Provides tools for searching court opinions, fetching case text,
and looking up legal citations via the CourtListener API.
"""

import asyncio
import json
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

from .client import CourtListenerClient
from .tools import TOOLS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create server and client
server = Server("courtlistener")
client = CourtListenerClient()


@server.list_tools()
async def list_tools():
    """List available tools."""
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    try:
        if name == "search_opinions":
            result = await client.search_opinions(
                query=arguments["query"],
                court=arguments.get("court"),
                date_after=arguments.get("date_after"),
                date_before=arguments.get("date_before"),
                limit=min(arguments.get("limit", 20), 50),
                semantic=arguments.get("semantic", False),
            )

        elif name == "get_opinion":
            result = await client.get_opinion(arguments["opinion_id"])

        elif name == "lookup_citation":
            result = await client.lookup_citation(arguments["citation"])

        elif name == "list_courts":
            result = await client.list_courts()

        elif name == "get_opinion_pdf":
            result = await client.get_opinion_pdf(
                opinion_id=arguments["opinion_id"],
                save_path=arguments.get("save_path"),
            )

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

    except Exception as e:
        logger.error(f"Tool error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def run():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    """Entry point."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
