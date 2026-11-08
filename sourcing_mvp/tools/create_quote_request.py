"""
MCP Tool: create_quote_request

创建报价请求并生成专属链接
"""
import logging
import os
from typing import Any
from datetime import datetime, timedelta
from uuid import uuid4

from ..quote_models import QuoteRequestStatus
from ..token_manager import TokenManager
from ..database import db

logger = logging.getLogger(__name__)


async def create_quote_request(args: dict[str, Any]) -> dict[str, Any]:
    """
    创建报价请求

    为指定供应商创建报价请求，生成专属访问链接
    """
    # 解析参数
    case_id = args.get("case_id")
    supplier_id = args.get("supplier_id")
    product_name = args.get("product_name")
    product_description = args.get("product_description", "")
    quantity = args.get("quantity")
    specifications = args.get("specifications", {})
    quote_deadline_hours = args.get("quote_deadline_hours", 72)
    buyer_id = args.get("buyer_id", "demo_buyer")
    confirm = args.get("confirm", False)

    # 验证必填参数
    if not all([case_id, supplier_id, product_name, quantity]):
        raise ValueError("Missing required parameters: case_id, supplier_id, product_name, quantity")

    # 需要买手确认
    if not confirm:
        raise ValueError("Buyer confirmation required (confirm=True)")

    logger.info(f"Creating quote request for case {case_id}, supplier {supplier_id}")

    # 验证案例存在且属于该买手
    case = db.get_case(case_id)
    if not case:
        raise ValueError(f"Case not found: {case_id}")

    if case["buyer_id"] != buyer_id:
        raise ValueError("Access denied: not your case")

    # 验证供应商存在且可用
    supplier = db.get_supplier(supplier_id)
    if not supplier:
        raise ValueError(f"Supplier not found: {supplier_id}")

    # 生产环境拒绝测试供应商
    if supplier.get("is_test_data", False):
        raise ValueError("Cannot create quote request for test supplier in production")

    if not supplier.get("active", True):
        raise ValueError("Supplier is inactive")

    # 创建报价请求
    now = datetime.now()
    deadline = now + timedelta(hours=quote_deadline_hours)

    request_data = {
        "id": str(uuid4()),
        "case_id": case_id,
        "supplier_id": supplier_id,
        "product_name": product_name,
        "product_description": product_description,
        "quantity": quantity,
        "specifications": specifications,
        "quote_deadline": deadline.isoformat(),
        "currency": "USD",
        "status": QuoteRequestStatus.ACTIVE.value,
        "buyer_id": buyer_id,
        "approved_by": buyer_id,
        "approved_at": now.isoformat(),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    request_id = db.create_quote_request(request_data)

    # 生成专属 Token
    token, token_hash = TokenManager.generate_token()

    token_record = TokenManager.create_token_record(
        quote_request_id=request_id,
        supplier_id=supplier_id,
        token=token,
        token_hash=token_hash,
        expire_hours=quote_deadline_hours,
    )

    db.create_quote_token(token_record)

    # 生成访问链接
    base_url = args.get("base_url", "http://localhost:8000")
    quote_link = f"{base_url}/q/{token}"

    logger.info(f"Quote request created: {request_id}")

    return {
        "quote_request_id": request_id,
        "quote_link": quote_link,
        "token": token,  # 仅用于开发测试，生产环境不应返回
        "expires_at": token_record["expires_at"],
        "supplier": {
            "id": supplier["id"],
            "name": supplier["name"],
            "email": supplier["contact"]["email"],
        },
        "message": f"Quote request created for {supplier['name']}. Share the link to collect their quotation.",
    }
