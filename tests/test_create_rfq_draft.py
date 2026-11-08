"""Tests for create_rfq_draft tool."""
import pytest
from uuid import uuid4


@pytest.mark.asyncio
async def test_create_rfq_draft_basic():
    """Test basic RFQ draft creation."""
    from sourcing_mcp.tools import create_rfq_draft_tool

    # TODO: Implement with test database
    pass


@pytest.mark.asyncio
async def test_create_rfq_draft_with_project():
    """Test RFQ draft creation with existing project."""
    # TODO: Implement
    pass


@pytest.mark.asyncio
async def test_create_rfq_draft_idempotency():
    """Test idempotency key handling."""
    # TODO: Implement
    pass
