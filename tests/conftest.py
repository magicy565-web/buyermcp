"""Test configuration and fixtures."""
import pytest
import pytest_asyncio
from uuid import uuid4

from sourcing_mcp.database import db


@pytest_asyncio.fixture
async def test_db():
    """Provide a test database connection."""
    # TODO: Set up test database with proper isolation
    await db.connect()
    yield db
    await db.close()


@pytest.fixture
def sample_rfq_item():
    """Sample RFQ item for testing."""
    return {
        "part_name": "Test Bracket",
        "material": "6061-T6",
        "tolerance_general": "ISO 2768-m",
        "surface_finish": "Ra 3.2",
        "quantity": {"value": "100", "unit": "pcs"},
    }


@pytest.fixture
def sample_delivery():
    """Sample delivery info for testing."""
    return {
        "country": "CN",
        "city": "Shenzhen",
        "incoterm": "FOB",
    }
