"""create_rfq_draft tool implementation."""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from mcp.types import Tool

from ..database import db
from ..models import Delivery, LocalizedText, RfqItem, RfqStatus

logger = logging.getLogger(__name__)

TOOL_DEFINITION = Tool(
    name="create_rfq_draft",
    description="创建 RFQ 草稿（不会发给供应商）。未传 project_id 时自动新建项目。v0.1 仅支持 category = cnc_machining。",
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "format": "uuid"},
            "project_title": {"type": "string", "maxLength": 200},
            "title": {"type": "string", "maxLength": 200},
            "category": {"const": "cnc_machining"},
            "items": {
                "type": "array",
                "minItems": 1,
                "maxItems": 50,
                "items": {"type": "object"},  # Full schema would be inline from bundle.py
            },
            "delivery": {"type": "object"},
            "target_delivery_date": {"type": "string", "format": "date"},
            "quote_deadline": {"type": "string", "format": "date-time"},
            "certifications": {"type": "array", "items": {"type": "string"}},
            "disclose_buyer": {"type": "boolean", "default": False},
            "notes": {"type": "object"},
            "idempotency_key": {"type": "string", "minLength": 16, "maxLength": 128},
        },
        "required": ["title", "category", "items", "delivery", "idempotency_key"],
    },
)


async def handler(args: dict[str, Any]) -> dict[str, Any]:
    """Handle create_rfq_draft tool call."""

    # Parse inputs
    project_id = UUID(args["project_id"]) if args.get("project_id") else None
    project_title = args.get("project_title")
    title = args["title"]
    category = args["category"]
    items_data = args["items"]
    delivery_data = args["delivery"]
    target_delivery_date = args.get("target_delivery_date")
    quote_deadline = args.get("quote_deadline")
    certifications = args.get("certifications", [])
    disclose_buyer = args.get("disclose_buyer", False)
    notes_data = args.get("notes")
    idempotency_key = args["idempotency_key"]

    # Parse items
    items = [RfqItem.model_validate(item) for item in items_data]
    delivery = Delivery.model_validate(delivery_data)
    notes = LocalizedText.model_validate(notes_data) if notes_data else None

    # TODO: Get agent_id from authentication context (for now, mock)
    # This would come from OAuth/JWT token in production
    agent_id: UUID | None = None
    buyer_org_id = UUID("00000000-0000-0000-0000-000000000001")  # Mock for v0.1

    async with db.transaction() as conn:
        # Check idempotency
        result = await conn.execute(
            """
            SELECT response FROM idempotency_key
            WHERE agent_id = $1 AND key = $2 AND tool = 'create_rfq_draft'
            """,
            [agent_id, idempotency_key],
        )
        existing = await result.fetchone()
        if existing:
            logger.info(f"Returning cached response for idempotency_key: {idempotency_key}")
            return existing["response"]

        # Create project if needed
        if project_id is None:
            project_id = uuid4()
            await conn.execute(
                """
                INSERT INTO project (id, buyer_org_id, title, created_by_agent_id, status)
                VALUES ($1, $2, $3, $4, 'active')
                """,
                [project_id, buyer_org_id, project_title or title, agent_id],
            )
            logger.info(f"Created new project: {project_id}")

        # Create RFQ
        rfq_id = uuid4()
        await conn.execute(
            """
            INSERT INTO rfq (
                id, project_id, buyer_org_id, created_by_agent_id, status, version,
                title, category, delivery_country, delivery_city, incoterm,
                target_delivery_date, quote_deadline, certifications, disclose_buyer,
                notes_original, notes_lang
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
            """,
            [
                rfq_id,
                project_id,
                buyer_org_id,
                agent_id,
                RfqStatus.DRAFT.value,
                1,
                title,
                category,
                delivery.country,
                delivery.city,
                delivery.incoterm.value if delivery.incoterm else None,
                target_delivery_date,
                quote_deadline,
                certifications,
                disclose_buyer,
                notes.original if notes else None,
                notes.lang.value if notes else None,
            ],
        )
        logger.info(f"Created RFQ draft: {rfq_id}")

        # Create RFQ items
        for idx, item in enumerate(items):
            item_id = uuid4()
            await conn.execute(
                """
                INSERT INTO rfq_item (
                    id, rfq_id, line_no, part_name, part_number, material, material_standard,
                    tolerance_general, tolerance_critical, surface_finish, heat_treatment,
                    quantity, quantity_unit, annual_volume, target_unit_price, target_currency,
                    notes_original, notes_lang
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
                """,
                [
                    item_id,
                    rfq_id,
                    idx + 1,
                    item.part_name,
                    item.part_number,
                    item.material,
                    item.material_standard,
                    item.tolerance_general,
                    [t.model_dump() for t in item.tolerance_critical] if item.tolerance_critical else [],
                    item.surface_finish,
                    item.heat_treatment,
                    item.quantity.value,
                    item.quantity.unit.value,
                    item.annual_volume.value if item.annual_volume else None,
                    item.target_unit_price.amount if item.target_unit_price else None,
                    item.target_unit_price.currency if item.target_unit_price else None,
                    item.notes.original if item.notes else None,
                    item.notes.lang.value if item.notes else None,
                ],
            )

        # Create event
        await conn.execute(
            """
            INSERT INTO event (stream_type, stream_id, project_id, type, actor_type, actor_id, payload)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            [
                "project",
                project_id,
                project_id,
                "rfq.draft_created",
                "agent",
                str(agent_id) if agent_id else None,
                {"rfq_id": str(rfq_id), "title": title, "category": category},
            ],
        )

        # Build response
        response = {
            "rfq_id": str(rfq_id),
            "project_id": str(project_id),
            "status": RfqStatus.DRAFT.value,
            "version": 1,
            "next_step": "validate_rfq",
        }

        # Cache response for idempotency
        await conn.execute(
            """
            INSERT INTO idempotency_key (agent_id, key, tool, request_hash, response)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (agent_id, key) DO NOTHING
            """,
            [agent_id, idempotency_key, "create_rfq_draft", b"", response],
        )

        return response
