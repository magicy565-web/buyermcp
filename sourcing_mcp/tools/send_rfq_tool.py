"""send_rfq tool implementation."""
import logging
from typing import Any
from uuid import UUID, uuid4

from mcp.types import Tool

from ..database import db
from ..models import LocalizedText, RfqStatus

logger = logging.getLogger(__name__)

TOOL_DEFINITION = Tool(
    name="send_rfq",
    description="提交 RFQ 与目标供应商名单进入人工审批队列。Agent 不能直接外发：审批通过后由运营外发，并产生 rfq.approved / dispatch.sent 事件。",
    inputSchema={
        "type": "object",
        "properties": {
            "rfq_id": {"type": "string", "format": "uuid"},
            "expected_rfq_version": {
                "type": "integer",
                "minimum": 1,
                "description": "与服务端不一致则拒绝，防止审批的版本与 agent 看到的不同。",
            },
            "supplier_ids": {
                "type": "array",
                "minItems": 1,
                "maxItems": 20,
                "items": {"type": "string", "format": "uuid"},
            },
            "buyer_note": {"type": "object"},
            "idempotency_key": {"type": "string", "minLength": 16, "maxLength": 128},
        },
        "required": ["rfq_id", "expected_rfq_version", "supplier_ids", "idempotency_key"],
    },
)


async def handler(args: dict[str, Any]) -> dict[str, Any]:
    """Handle send_rfq tool call."""
    rfq_id = UUID(args["rfq_id"])
    expected_version = args["expected_rfq_version"]
    supplier_ids = [UUID(id_) for id_ in args["supplier_ids"]]
    buyer_note_data = args.get("buyer_note")
    idempotency_key = args["idempotency_key"]

    buyer_note = LocalizedText.model_validate(buyer_note_data) if buyer_note_data else None

    # TODO: Get agent_id from authentication context
    agent_id: UUID | None = None

    async with db.transaction() as conn:
        # Check idempotency
        result = await conn.execute(
            """
            SELECT response FROM idempotency_key
            WHERE agent_id = $1 AND key = $2 AND tool = 'send_rfq'
            """,
            [agent_id, idempotency_key],
        )
        existing = await result.fetchone()
        if existing:
            logger.info(f"Returning cached response for idempotency_key: {idempotency_key}")
            return existing["response"]

        # Get and verify RFQ
        result = await conn.execute(
            "SELECT id, version, status FROM rfq WHERE id = $1",
            [rfq_id],
        )
        rfq = await result.fetchone()
        if not rfq:
            raise ValueError(f"RFQ not found: {rfq_id}")

        if rfq["version"] != expected_version:
            raise ValueError(
                f"Version mismatch: expected {expected_version}, got {rfq['version']}. "
                "RFQ may have been modified. Please review and retry."
            )

        if rfq["status"] not in [RfqStatus.DRAFT.value, RfqStatus.NEEDS_CLARIFICATION.value]:
            raise ValueError(f"RFQ cannot be submitted from status: {rfq['status']}")

        # Verify suppliers exist and are active
        result = await conn.execute(
            """
            SELECT id FROM supplier
            WHERE id = ANY($1) AND status = 'active'
            """,
            [[str(id_) for id_ in supplier_ids]],
        )
        active_suppliers = [row["id"] for row in await result.fetchall()]
        if len(active_suppliers) != len(supplier_ids):
            missing = set(str(id_) for id_ in supplier_ids) - set(str(id_) for id_ in active_suppliers)
            raise ValueError(f"Suppliers not found or inactive: {missing}")

        # Create approval record
        approval_id = uuid4()
        await conn.execute(
            """
            INSERT INTO rfq_approval (
                id, rfq_id, rfq_version, requested_by_agent_id,
                supplier_ids, buyer_note, decision
            ) VALUES ($1, $2, $3, $4, $5, $6, 'pending')
            """,
            [
                approval_id,
                rfq_id,
                expected_version,
                agent_id,
                [str(id_) for id_ in supplier_ids],
                buyer_note.original if buyer_note else None,
            ],
        )

        # Update RFQ status
        await conn.execute(
            "UPDATE rfq SET status = $1 WHERE id = $2",
            [RfqStatus.PENDING_APPROVAL.value, rfq_id],
        )

        # Create event
        await conn.execute(
            """
            INSERT INTO event (stream_type, stream_id, project_id, type, actor_type, actor_id, payload)
            VALUES ($1, $2, (SELECT project_id FROM rfq WHERE id = $2), $3, $4, $5, $6)
            """,
            [
                "project",
                rfq_id,
                "rfq.submitted_for_approval",
                "agent",
                str(agent_id) if agent_id else None,
                {
                    "rfq_id": str(rfq_id),
                    "approval_id": str(approval_id),
                    "supplier_count": len(supplier_ids),
                },
            ],
        )

        logger.info(f"RFQ {rfq_id} submitted for approval: {approval_id}")

        # Build response
        response = {
            "approval_id": str(approval_id),
            "status": "pending_approval",
            "estimated_review_hours": 4,  # Business hours estimate
        }

        # Cache response for idempotency
        await conn.execute(
            """
            INSERT INTO idempotency_key (agent_id, key, tool, request_hash, response)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (agent_id, key) DO NOTHING
            """,
            [agent_id, idempotency_key, "send_rfq", b"", response],
        )

        return response
