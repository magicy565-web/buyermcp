"""Service layer integration and initialization."""
from .demand_service import DemandService
from .supply_service import SupplyService
from .matching_service import MatchingService

# TODO: Implement remaining services
# from .workflow_service import WorkflowService
# from .quote_service import QuoteService
# from .evidence_service import EvidenceService

from . import registry

__all__ = [
    "DemandService",
    "SupplyService",
    "MatchingService",
    "registry",
]


async def initialize_services() -> None:
    """Initialize all services and register them."""
    # Initialize Demand Service
    demand_service = DemandService()
    await demand_service.initialize()
    registry.register("demand", demand_service)

    # Initialize Supply Service
    supply_service = SupplyService()
    await supply_service.initialize()
    registry.register("supply", supply_service)

    # Initialize Matching Service
    matching_service = MatchingService()
    await matching_service.initialize()
    registry.register("matching", matching_service)

    # TODO: Initialize remaining services
    # workflow_service = WorkflowService()
    # await workflow_service.initialize()
    # registry.register("workflow", workflow_service)
    #
    # quote_service = QuoteService()
    # await quote_service.initialize()
    # registry.register("quote", quote_service)
    #
    # evidence_service = EvidenceService()
    # await evidence_service.initialize()
    # registry.register("evidence", evidence_service)


async def get_service(name: str):
    """Get a service by name."""
    return registry.get(name)


async def health_check_all() -> dict:
    """Run health checks on all services."""
    return await registry.health_check_all()
