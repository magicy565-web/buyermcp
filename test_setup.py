"""Quick test script to validate the MCP server setup."""
import asyncio
import sys

async def test_server():
    """Test basic server components."""
    print("Testing Sourcing MCP Core v0.1...")
    print("-" * 50)

    # Test imports
    print("✓ Testing imports...")
    try:
        from sourcing_mcp import __version__
        from sourcing_mcp.config import config
        from sourcing_mcp.database import db
        from sourcing_mcp.models import RfqStatus, VerificationLevel
        from sourcing_mcp.tools import (
            create_rfq_draft_tool,
            validate_rfq_tool,
            match_suppliers_tool,
            send_rfq_tool,
            get_quotes_tool,
            compare_quotes_tool,
            get_project_status_tool,
        )
        print(f"  Version: {__version__}")
        print(f"  Config loaded: {config.MCP_SERVER_NAME}")
        print("  ✓ All imports successful")
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False

    # Test tool definitions
    print("\n✓ Testing tool definitions...")
    tools = [
        create_rfq_draft_tool.TOOL_DEFINITION,
        validate_rfq_tool.TOOL_DEFINITION,
        match_suppliers_tool.TOOL_DEFINITION,
        send_rfq_tool.TOOL_DEFINITION,
        get_quotes_tool.TOOL_DEFINITION,
        compare_quotes_tool.TOOL_DEFINITION,
        get_project_status_tool.TOOL_DEFINITION,
    ]
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:50]}...")
    print(f"  ✓ {len(tools)} tools loaded")

    # Test database connection (skip if no PostgreSQL)
    print("\n✓ Testing database connection...")
    try:
        await db.connect()
        print("  ✓ Database connection successful")
        await db.close()
    except Exception as e:
        print(f"  ⚠ Database connection skipped: {e}")
        print("  (PostgreSQL not required for this test)")

    print("\n" + "=" * 50)
    print("✓ All tests passed!")
    print("\nNext steps:")
    print("1. Install PostgreSQL if not already installed")
    print("2. Run: psql -U postgres -d sourcing_mcp -f schema.sql")
    print("3. Configure .env file with DATABASE_URL")
    print("4. Configure Claude Desktop (see INSTALL.md)")
    print("5. Test: python -m sourcing_mcp.server")
    return True

if __name__ == "__main__":
    result = asyncio.run(test_server())
    sys.exit(0 if result else 1)
