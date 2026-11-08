"""get_project_status tool implementation."""
import logging
from typing import Any
from uuid import UUID

from mcp.types import Tool

from ..database import db

logger = logging.getLogger(__name__)

TOOL_DEFINITION = Tool(
    name="get_project_status",
    description="返回项目下各 RFQ 的状态、外发/回复/报价计数，以及当前等待谁的动作。",
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "format": "uuid"},
        },
        "required": ["project_id"],
    },
)


async def handler(args: dict[str, Any]) -> dict[str, Any]:
    """Handle get_project_status tool call."""
    project_id = UUID(args["project_id"])

    async with db.connection() as conn:
        # Get project
        result = await conn.execute(
            "SELECT id, title FROM project WHERE id = $1",
            [project_id],
        )
        project = await result.fetchone()
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        # Get RFQs
        result = await conn.execute(
            """
            SELECT id, status, title
            FROM rfq
            WHERE project_id = $1
            ORDER BY created_at DESC
            """,
            [project_id],
        )
        rfq_rows = await result.fetchall()

        rfqs = []
        for rfq in rfq_rows:
            rfq_id = rfq["id"]

            # Get dispatch counts
            result = await conn.execute(
                """
                SELECT
                    COUNT(*) FILTER (WHERE status IN ('queued', 'sent', 'opened', 'responded')) as dispatched,
                    COUNT(*) FILTER (WHERE status = 'opened') as opened,
                    COUNT(*) FILTER (WHERE status = 'responded') as responded,
                    COUNT(*) FILTER (WHERE status = 'declined') as declined
                FROM rfq_dispatch
                WHERE rfq_id = $1
                """,
                [rfq_id],
            )
            dispatch_stats = await result.fetchone() or {}

            # Get valid quotes count
            result = await conn.execute(
                """
                SELECT COUNT(*) as count
                FROM quote
                WHERE rfq_id = $1
                    AND status IN ('submitted', 'superseded')
                    AND valid_until > now()
                """,
                [rfq_id],
            )
            valid_quotes = (await result.fetchone())["count"]

            # Determine who is waiting
            status = rfq["status"]
            if status in ["draft", "needs_clarification"]:
                waiting_on = "buyer_agent"
            elif status == "pending_approval":
                waiting_on = "operator_approval"
            elif status in ["sent", "quoted"]:
                waiting_on = "suppliers"
            else:
                waiting_on = "none"

            # Get last event time
            result = await conn.execute(
                """
                SELECT occurred_at
                FROM event
                WHERE stream_type = 'project' AND stream_id = $1
                ORDER BY seq DESC LIMIT 1
                """,
                [rfq_id],
            )
            last_event = await result.fetchone()

            rfqs.append({
                "rfq_id": str(rfq_id),
                "status": status,
                "counts": {
                    "dispatched": dispatch_stats.get("dispatched", 0),
                    "opened": dispatch_stats.get("opened", 0),
                    "responded": dispatch_stats.get("responded", 0),
                    "declined": dispatch_stats.get("declined", 0),
                    "valid_quotes": valid_quotes,
                },
                "waiting_on": waiting_on,
                "last_event_at": last_event["occurred_at"].isoformat() if last_event else None,
            })

        logger.info(f"Retrieved status for project {project_id} with {len(rfqs)} RFQs")

        return {
            "project_id": str(project_id),
            "title": project["title"],
            "rfqs": rfqs,
        }
