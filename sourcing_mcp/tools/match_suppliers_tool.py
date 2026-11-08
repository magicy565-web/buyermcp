"""match_suppliers tool implementation."""
import logging
from typing import Any
from uuid import UUID

from mcp.types import Tool

from ..database import db
from ..models import SupplierType, VerificationLevel

logger = logging.getLogger(__name__)

TOOL_DEFINITION = Tool(
    name="match_suppliers",
    description="按品类、工艺、材料、地区、产能匹配候选供应商，返回验证等级和匹配理由。不返回联系方式；供应商名称是否展示取决于运营配置。",
    inputSchema={
        "type": "object",
        "properties": {
            "rfq_id": {"type": "string", "format": "uuid"},
            "max_results": {"type": "integer", "minimum": 1, "maximum": 30, "default": 10},
            "filters": {
                "type": "object",
                "properties": {
                    "min_verification_level": {"type": "integer", "minimum": 0, "maximum": 4},
                    "supplier_type": {"type": "string", "enum": ["factory", "trader", "unknown"]},
                    "provinces": {"type": "array", "items": {"type": "string"}},
                    "exclude_supplier_ids": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "required": ["rfq_id"],
    },
)


async def handler(args: dict[str, Any]) -> dict[str, Any]:
    """Handle match_suppliers tool call."""
    rfq_id = UUID(args["rfq_id"])
    max_results = args.get("max_results", 10)
    filters = args.get("filters", {})

    min_verification_level = filters.get("min_verification_level", 0)
    supplier_type_filter = filters.get("supplier_type")
    provinces = filters.get("provinces", [])
    exclude_ids = [UUID(id_) for id_ in filters.get("exclude_supplier_ids", [])]

    async with db.connection() as conn:
        # Get RFQ details
        result = await conn.execute(
            """
            SELECT r.category, array_agg(DISTINCT ri.material) as materials
            FROM rfq r
            JOIN rfq_item ri ON ri.rfq_id = r.id
            WHERE r.id = $1
            GROUP BY r.category
            """,
            [rfq_id],
        )
        rfq_info = await result.fetchone()
        if not rfq_info:
            raise ValueError(f"RFQ not found: {rfq_id}")

        category = rfq_info["category"]
        materials = rfq_info["materials"] or []

        # Build query
        query = """
            SELECT
                s.id,
                s.legal_name_zh,
                s.supplier_type,
                s.province,
                COALESCE(MAX(sv.level_granted), 0) as verification_level,
                s.capabilities
            FROM supplier s
            LEFT JOIN supplier_verification sv ON sv.supplier_id = s.id
                AND sv.result = 'pass'
                AND (sv.expires_at IS NULL OR sv.expires_at > now())
            WHERE s.status = 'active'
        """
        params: list[Any] = []
        param_idx = 1

        # Apply filters
        if supplier_type_filter:
            query += f" AND s.supplier_type = ${param_idx}"
            params.append(supplier_type_filter)
            param_idx += 1

        if provinces:
            query += f" AND s.province = ANY(${param_idx})"
            params.append(provinces)
            param_idx += 1

        if exclude_ids:
            query += f" AND s.id != ALL(${param_idx})"
            params.append([str(id_) for id_ in exclude_ids])
            param_idx += 1

        query += f"""
            GROUP BY s.id
            HAVING COALESCE(MAX(sv.level_granted), 0) >= ${param_idx}
            ORDER BY verification_level DESC, random()
            LIMIT ${param_idx + 1}
        """
        params.extend([min_verification_level, max_results])

        result = await conn.execute(query, params)
        suppliers = await result.fetchall()

        # Build candidates
        candidates = []
        for supplier in suppliers:
            capabilities = supplier["capabilities"] or {}
            match_reasons = []
            caveats = []

            # Check process match
            processes = capabilities.get("processes", [])
            if category == "cnc_machining" and "cnc_milling" in processes:
                match_reasons.append({
                    "code": "process_match",
                    "detail": "Supplier has CNC milling capability",
                })

            # Check material match
            supplier_materials = capabilities.get("materials", [])
            matched_materials = [m for m in materials if m in supplier_materials]
            if matched_materials:
                match_reasons.append({
                    "code": "material_match",
                    "detail": f"Supplier works with: {', '.join(matched_materials)}",
                })
            elif materials:
                caveats.append(f"Material experience not verified for: {', '.join(materials)}")

            # Region
            if supplier["province"]:
                match_reasons.append({
                    "code": "region",
                    "detail": f"Located in {supplier['province']}",
                })

            # Capacity fit (simplified for v0.1)
            if capabilities.get("max_part_size_mm"):
                match_reasons.append({
                    "code": "capacity_fit",
                    "detail": "Has suitable production capacity",
                })

            candidates.append({
                "supplier_id": str(supplier["id"]),
                "display_name": supplier["legal_name_zh"],
                "supplier_type": supplier["supplier_type"],
                "province": supplier["province"],
                "verification_level": supplier["verification_level"],
                "match_reasons": match_reasons,
                "caveats": caveats if caveats else None,
            })

        logger.info(f"Matched {len(candidates)} suppliers for RFQ {rfq_id}")

        return {"candidates": candidates}
