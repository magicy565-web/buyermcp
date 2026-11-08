"""
MCP Tool: prepare_inquiry

准备询价邮件草稿
"""
import logging
from typing import Any
from uuid import uuid4
from datetime import datetime

from ..models import (
    PrepareInquiryInput,
    PrepareInquiryOutput,
    Inquiry,
    InquiryStatus,
)
from ..database import db

logger = logging.getLogger(__name__)


async def prepare_inquiry(args: dict[str, Any]) -> dict[str, Any]:
    """
    准备询价邮件

    生成专业的询价邮件草稿，等待买手确认。
    """
    input_data = PrepareInquiryInput(**args)

    logger.info(f"Preparing inquiry for case {input_data.case_id}, supplier {input_data.supplier_id}")

    # 获取案例信息
    case = db.get_case(str(input_data.case_id))
    if not case:
        raise ValueError(f"Case not found: {input_data.case_id}")

    # 获取供应商信息
    supplier = db.get_supplier(input_data.supplier_id)
    if not supplier:
        raise ValueError(f"Supplier not found: {input_data.supplier_id}")

    # 生成邮件内容
    if input_data.language == "auto":
        # 简化：根据供应商位置判断
        language = "zh" if "China" in supplier.get("notes", "") else "en"
    else:
        language = input_data.language

    if language == "zh":
        subject, body = _generate_email_zh(case, supplier, input_data.additional_requirements)
    else:
        subject, body = _generate_email_en(case, supplier, input_data.additional_requirements)

    # 创建询价记录（草稿状态）
    inquiry_id = str(uuid4())
    inquiry_data = {
        "id": inquiry_id,
        "case_id": str(input_data.case_id),
        "supplier_id": input_data.supplier_id,
        "email_subject": subject,
        "email_body": body,
        "language": language,
        "status": InquiryStatus.DRAFT.value,
        "created_at": datetime.now().isoformat(),
    }

    db.create_inquiry(inquiry_data)

    # 生成预览
    preview = f"To: {supplier['name']}\nSubject: {subject}\n\n{body[:200]}..."

    output = PrepareInquiryOutput(
        inquiry_id=uuid4(),  # 使用新的 UUID
        email_subject=subject,
        email_body=body,
        preview=preview,
    )

    # 更新实际 inquiry_id
    output.inquiry_id = inquiry_id

    logger.info(f"Inquiry {inquiry_id} prepared for case {input_data.case_id}")

    return output.model_dump()


def _generate_email_en(
    case: dict,
    supplier: dict,
    additional_requirements: str = None,
) -> tuple[str, str]:
    """生成英文询价邮件"""
    product = case.get("product_description", "your products")
    requirements = case.get("requirements", {})

    # Subject
    subject = f"Product Inquiry - {product[:50]}"

    # Body
    body_parts = [
        f"Dear {supplier['name']},",
        "",
        "We are interested in sourcing the following product:",
        f"Product: {product}",
        "",
    ]

    # 添加需求
    if requirements:
        body_parts.append("Requirements:")
        if requirements.get("moq"):
            body_parts.append(f"- MOQ: {requirements['moq']} units")
        if requirements.get("budget"):
            body_parts.append(f"- Target price: {requirements['budget']}")
        if requirements.get("delivery"):
            body_parts.append(f"- Delivery: {requirements['delivery']}")
        body_parts.append("")

    # 询问内容
    body_parts.extend([
        "Could you please provide:",
        "- FOB unit price for the specified quantity",
        "- Minimum order quantity (MOQ)",
        "- Lead time after order confirmation",
        "- Payment terms",
        "- Available customization options",
        "- Sample availability and cost",
        "",
    ])

    if additional_requirements:
        body_parts.extend([
            "Additional requirements:",
            additional_requirements,
            "",
        ])

    body_parts.extend([
        "We are looking to move forward quickly with the right supplier.",
        "",
        "Best regards,",
        "[Your name will be added]",
    ])

    body = "\n".join(body_parts)

    return subject, body


def _generate_email_zh(
    case: dict,
    supplier: dict,
    additional_requirements: str = None,
) -> tuple[str, str]:
    """生成中文询价邮件"""
    product = case.get("product_description", "贵司产品")
    requirements = case.get("requirements", {})

    # Subject
    subject = f"产品询价 - {product[:50]}"

    # Body
    body_parts = [
        f"{supplier['name']} 您好，",
        "",
        "我们有意采购以下产品：",
        f"产品：{product}",
        "",
    ]

    # 添加需求
    if requirements:
        body_parts.append("采购需求：")
        if requirements.get("moq"):
            body_parts.append(f"- 起订量：{requirements['moq']} 件")
        if requirements.get("budget"):
            body_parts.append(f"- 目标价格：{requirements['budget']}")
        if requirements.get("delivery"):
            body_parts.append(f"- 交货：{requirements['delivery']}")
        body_parts.append("")

    # 询问内容
    body_parts.extend([
        "烦请提供：",
        "- FOB 单价（基于上述数量）",
        "- 最小起订量（MOQ）",
        "- 生产周期",
        "- 付款条件",
        "- 可定制选项",
        "- 样品价格及寄送方式",
        "",
    ])

    if additional_requirements:
        body_parts.extend([
            "其他要求：",
            additional_requirements,
            "",
        ])

    body_parts.extend([
        "我们希望尽快与合适的供应商推进合作。",
        "",
        "此致",
        "敬礼",
        "[您的姓名将自动添加]",
    ])

    body = "\n".join(body_parts)

    return subject, body
