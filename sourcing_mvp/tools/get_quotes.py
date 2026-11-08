"""
MCP Tool: get_quotes

查询报价（带买手权限验证）
"""
import logging
from typing import Any, Optional
from datetime import datetime
from decimal import Decimal

from ..database import db

logger = logging.getLogger(__name__)


async def get_quotes(args: dict[str, Any]) -> dict[str, Any]:
    """
    查询报价

    按案例或报价请求查询，验证买手访问权限
    """
    case_id = args.get("case_id")
    quote_request_id = args.get("quote_request_id")
    buyer_id = args.get("buyer_id", "demo_buyer")

    if not case_id and not quote_request_id:
        raise ValueError("Either case_id or quote_request_id is required")

    logger.info(f"Getting quotes for buyer {buyer_id}")

    # 查询报价
    if quote_request_id:
        # 查询特定报价请求
        request = db.get_quote_request(quote_request_id)
        if not request:
            raise ValueError(f"Quote request not found: {quote_request_id}")

        # 验证权限
        case = db.get_case(request["case_id"])
        if not case or case["buyer_id"] != buyer_id:
            raise ValueError("Access denied: not your quote request")

        quotes = db.get_supplier_quotes(quote_request_id)

    else:
        # 查询整个案例的报价
        case = db.get_case(case_id)
        if not case:
            raise ValueError(f"Case not found: {case_id}")

        # 验证权限
        if case["buyer_id"] != buyer_id:
            raise ValueError("Access denied: not your case")

        quotes = db.get_quotes_by_case(case_id)

    # 格式化报价数据
    formatted_quotes = []
    for quote in quotes:
        # 获取供应商信息
        supplier = db.get_supplier(quote["supplier_id"])

        # 检查报价是否过期
        valid_until = datetime.fromisoformat(quote["quote_valid_until"])
        is_expired = valid_until < datetime.now()

        formatted_quote = {
            "quote_id": quote["id"],
            "supplier_name": supplier["name"] if supplier else "Unknown",
            "supplier_id": quote["supplier_id"],
            "version": quote["version"],
            "unit_price": quote["unit_price"],
            "currency": quote["currency"],
            "moq": quote["moq"],
            "lead_time_days": quote["lead_time_days"],
            "trade_term": quote["trade_term"],
            "quote_valid_until": quote["quote_valid_until"],
            "is_expired": is_expired,
            "payment_terms": quote["payment_terms"],
            "specification_notes": quote["specification_notes"],
            "status": quote["status"],
            "submitted_at": quote["submitted_at"],
            "submitted_via": quote["submitted_via"],
        }

        formatted_quotes.append(formatted_quote)

    # 生成摘要
    summary = _generate_quotes_summary(formatted_quotes)

    return {
        "quotes": formatted_quotes,
        "total_count": len(formatted_quotes),
        "summary": summary,
        "has_valid_quotes": any(not q["is_expired"] for q in formatted_quotes),
    }


def _generate_quotes_summary(quotes: list[dict]) -> str:
    """生成报价摘要"""
    if not quotes:
        return "No quotes received yet. Waiting for supplier responses."

    total = len(quotes)
    valid = sum(1 for q in quotes if not q["is_expired"])
    expired = total - valid

    # 按供应商分组
    suppliers = {}
    for quote in quotes:
        supplier_id = quote["supplier_id"]
        if supplier_id not in suppliers:
            suppliers[supplier_id] = {
                "name": quote["supplier_name"],
                "versions": []
            }
        suppliers[supplier_id]["versions"].append(quote)

    summary_parts = [f"Received {total} quote(s) from {len(suppliers)} supplier(s):"]

    for supplier_id, info in suppliers.items():
        latest = info["versions"][0]  # Assuming sorted by version DESC
        price_str = f"{latest['currency']} {latest['unit_price']}"
        status_emoji = "❌" if latest["is_expired"] else "✅"

        supplier_summary = (
            f"{status_emoji} {info['name']}: "
            f"{price_str}/unit, MOQ {latest['moq']}, "
            f"{latest['lead_time_days']} days, {latest['trade_term']}"
        )

        if latest["specification_notes"]:
            supplier_summary += f" (⚠️ Has spec differences)"

        summary_parts.append(supplier_summary)

    if expired > 0:
        summary_parts.append(f"\n⚠️ {expired} quote(s) expired")

    return "\n".join(summary_parts)
