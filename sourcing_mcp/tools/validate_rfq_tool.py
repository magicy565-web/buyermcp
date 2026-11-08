"""validate_rfq tool implementation."""
import logging
from typing import Any
from uuid import UUID

from mcp.types import Tool

from ..database import db
from ..models import FieldIssue, RfqStatus

logger = logging.getLogger(__name__)

TOOL_DEFINITION = Tool(
    name="validate_rfq",
    description="检查 RFQ 是否可提交，返回缺失/模糊字段和需要向买方澄清的问题。存在 blocking 问题时 RFQ 状态置为 needs_clarification。",
    inputSchema={
        "type": "object",
        "properties": {
            "rfq_id": {"type": "string", "format": "uuid"},
        },
        "required": ["rfq_id"],
    },
)


async def handler(args: dict[str, Any]) -> dict[str, Any]:
    """Handle validate_rfq tool call."""
    rfq_id = UUID(args["rfq_id"])

    async with db.transaction() as conn:
        # Get RFQ
        result = await conn.execute(
            """
            SELECT id, status, version, title, category, delivery_country, incoterm
            FROM rfq WHERE id = $1
            """,
            [rfq_id],
        )
        rfq = await result.fetchone()
        if not rfq:
            raise ValueError(f"RFQ not found: {rfq_id}")

        # Get items
        result = await conn.execute(
            """
            SELECT id, part_name, material, tolerance_general, surface_finish,
                   quantity, quantity_unit, drawing_evidence_ids
            FROM rfq_item WHERE rfq_id = $1 ORDER BY line_no
            """,
            [rfq_id],
        )
        items = await result.fetchall()

        # Validation logic
        issues: list[dict[str, Any]] = []
        clarifying_questions: list[dict[str, Any]] = []

        # Check delivery info
        if not rfq["delivery_country"]:
            issues.append({
                "path": "/delivery/country",
                "code": "missing",
                "severity": "blocking",
                "reason": "Delivery country is required",
            })
            clarifying_questions.append({
                "path": "/delivery/country",
                "question_zh": "请问交货国家是哪里？",
                "question_en": "What is the delivery country?",
            })

        if not rfq["incoterm"]:
            issues.append({
                "path": "/delivery/incoterm",
                "code": "missing",
                "severity": "warning",
                "reason": "Incoterm not specified, defaulting to EXW may increase cost uncertainty",
            })

        # Check each item
        for idx, item in enumerate(items):
            base_path = f"/items/{idx}"

            # Check tolerance
            if not item["tolerance_general"]:
                issues.append({
                    "path": f"{base_path}/tolerance_general",
                    "code": "missing",
                    "severity": "blocking",
                    "reason": "General tolerance standard is required for CNC machining",
                })
                clarifying_questions.append({
                    "path": f"{base_path}/tolerance_general",
                    "question_zh": f"{item['part_name']} 的公差要求是什么？（例如：ISO 2768-m）",
                    "question_en": f"What is the tolerance requirement for {item['part_name']}? (e.g., ISO 2768-m)",
                })

            # Check surface finish
            if not item["surface_finish"]:
                issues.append({
                    "path": f"{base_path}/surface_finish",
                    "code": "missing",
                    "severity": "warning",
                    "reason": "Surface finish not specified, suppliers may quote conservatively",
                })

            # Check drawings
            drawing_ids = item.get("drawing_evidence_ids") or []
            if not drawing_ids:
                issues.append({
                    "path": f"{base_path}/drawing_evidence_ids",
                    "code": "missing",
                    "severity": "blocking",
                    "reason": "Technical drawing is required for accurate quotation",
                })
                clarifying_questions.append({
                    "path": f"{base_path}/drawing_evidence_ids",
                    "question_zh": f"请上传 {item['part_name']} 的技术图纸（PDF、STEP 或 DXF 格式）",
                    "question_en": f"Please upload technical drawing for {item['part_name']} (PDF, STEP, or DXF format)",
                })

        # Determine if ready
        blocking_issues = [i for i in issues if i["severity"] == "blocking"]
        ready_to_submit = len(blocking_issues) == 0

        # Update RFQ status if needed
        new_status = rfq["status"]
        if blocking_issues and rfq["status"] == RfqStatus.DRAFT.value:
            new_status = RfqStatus.NEEDS_CLARIFICATION.value
            await conn.execute(
                "UPDATE rfq SET status = $1, missing_fields = $2 WHERE id = $3",
                [new_status, issues, rfq_id],
            )
            logger.info(f"RFQ {rfq_id} status changed to needs_clarification")

        # Create event
        await conn.execute(
            """
            INSERT INTO event (stream_type, stream_id, project_id, type, actor_type, payload)
            VALUES ($1, $2, (SELECT project_id FROM rfq WHERE id = $2), $3, $4, $5)
            """,
            [
                "project",
                rfq_id,
                "rfq.validated",
                "agent",
                {
                    "rfq_id": str(rfq_id),
                    "ready_to_submit": ready_to_submit,
                    "issues_count": len(issues),
                    "blocking_count": len(blocking_issues),
                },
            ],
        )

        return {
            "ready_to_submit": ready_to_submit,
            "status": new_status,
            "version": rfq["version"],
            "issues": issues,
            "clarifying_questions": clarifying_questions,
        }
