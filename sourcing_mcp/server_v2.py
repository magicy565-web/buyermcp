"""MCP Server with Service Layer Architecture."""
import asyncio
import logging
from collections.abc import Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from .config import config
from .database import db
from .services.integration import initialize_services, health_check_all
from .tools import (
    compare_quotes_tool,
    create_rfq_draft_tool,
    get_project_status_tool,
    get_quotes_tool,
    match_suppliers_tool,
    send_rfq_tool,
    validate_rfq_tool,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_mcp_server() -> Server:
    """Create and configure the MCP server."""
    server = Server(config.MCP_SERVER_NAME)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available MCP tools."""
        return [
            create_rfq_draft_tool.TOOL_DEFINITION,
            validate_rfq_tool.TOOL_DEFINITION,
            match_suppliers_tool.TOOL_DEFINITION,
            send_rfq_tool.TOOL_DEFINITION,
            get_quotes_tool.TOOL_DEFINITION,
            compare_quotes_tool.TOOL_DEFINITION,
            get_project_status_tool.TOOL_DEFINITION,
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> Sequence[any]:
        """Route tool calls to implementations."""
        logger.info(f"Tool called: {name}")
        logger.debug(f"Arguments: {arguments}")

        try:
            if name == "create_rfq_draft":
                result = await create_rfq_draft_tool.handler(arguments)
            elif name == "validate_rfq":
                result = await validate_rfq_tool.handler(arguments)
            elif name == "match_suppliers":
                result = await match_suppliers_tool.handler(arguments)
            elif name == "send_rfq":
                result = await send_rfq_tool.handler(arguments)
            elif name == "get_quotes":
                result = await get_quotes_tool.handler(arguments)
            elif name == "compare_quotes":
                result = await compare_quotes_tool.handler(arguments)
            elif name == "get_project_status":
                result = await get_project_status_tool.handler(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

            logger.info(f"Tool {name} completed successfully")
            return [{"type": "text", "text": str(result)}]

        except Exception as e:
            logger.error(f"Tool {name} failed: {e}", exc_info=True)
            raise

    # Health check endpoint
    @server.list_prompts()
    async def list_prompts():
        """List available prompts (including health check)."""
        return []

    return server


async def main() -> None:
    """Main entry point."""
    logger.info(f"Starting {config.MCP_SERVER_NAME} MCP server v0.2.0 (with Service Layer)")

    # Connect to database
    await db.connect()

    # Initialize service layer
    logger.info("Initializing service layer...")
    await initialize_services()

    # Run health checks
    health_status = await health_check_all()
    logger.info(f"Service health check: {health_status}")

    try:
        # Create and run server
        server = create_mcp_server()
        async with stdio_server() as (read_stream, write_stream):
            logger.info("MCP server ready (v0.2.0 - Service Layer Architecture)")
            await server.run(read_stream, write_stream, server.create_initialization_options())
    finally:
        # Clean up
        await db.close()
        logger.info("MCP server stopped")


if __name__ == "__main__":
    asyncio.run(main())
