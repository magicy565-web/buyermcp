"""
MCP Tool: send_inquiry

发送询价邮件给供应商
"""
import logging
from typing import Any
from datetime import datetime, timedelta

from ..models import (
    SendInquiryInput,
    SendInquiryOutput,
    InquiryStatus,
)
from ..database import db

logger = logging.getLogger(__name__)


async def send_inquiry(args: dict[str, Any]) -> dict[str, Any]:
    """
    发送询价邮件

    实际发送邮件给供应商，并设置追踪。
    """
    input_data = SendInquiryInput(**args)

    if not input_data.confirm:
        raise ValueError("Buyer confirmation required to send inquiry")

    logger.info(f"Sending inquiry {input_data.inquiry_id}")

    # 获取询价信息
    inquiry = db.get_inquiry(str(input_data.inquiry_id))
    if not inquiry:
        raise ValueError(f"Inquiry not found: {input_data.inquiry_id}")

    if inquiry["status"] != InquiryStatus.DRAFT.value:
        raise ValueError(f"Inquiry already sent: {input_data.inquiry_id}")

    # 获取供应商信息
    supplier = db.get_supplier(inquiry["supplier_id"])
    if not supplier:
        raise ValueError(f"Supplier not found: {inquiry['supplier_id']}")

    # 发送邮件
    sent_at = datetime.now()
    success = await _send_email(
        to=supplier["contact"]["email"],
        subject=inquiry["email_subject"],
        body=inquiry["email_body"],
    )

    if success:
        # 更新询价状态
        follow_up_at = sent_at + timedelta(days=2)  # 2 天后自动跟进
        db.update_inquiry(str(input_data.inquiry_id), {
            "status": InquiryStatus.SENT.value,
            "sent_at": sent_at.isoformat(),
            "follow_up_at": follow_up_at.isoformat(),
        })

        # 更新案例状态
        db.update_case(inquiry["case_id"], {
            "status": "inquiring",
        })

        tracking_info = (
            f"Email sent to {supplier['name']} ({supplier['contact']['email']}). "
            f"I'll follow up in 2 business days if no response."
        )

        logger.info(f"Inquiry {input_data.inquiry_id} sent successfully")
    else:
        db.update_inquiry(str(input_data.inquiry_id), {
            "status": InquiryStatus.BOUNCED.value,
        })
        tracking_info = f"Failed to send email to {supplier['contact']['email']}"
        logger.error(tracking_info)

    output = SendInquiryOutput(
        inquiry_id=input_data.inquiry_id,
        sent=success,
        sent_at=sent_at,
        tracking_info=tracking_info,
    )

    return output.model_dump()


async def _send_email(to: str, subject: str, body: str) -> bool:
    """
    发送邮件（实际实现）

    MVP 阶段要求：
    - 不允许 Mock 或模拟成功
    - 必须实现真实邮件发送，或明确返回 False

    实现选项：
    - 方案 1：使用 SendGrid API（推荐）
    - 方案 2：使用 SMTP + Gmail/Outlook
    - 方案 3：使用 Mailgun API
    """
    # 记录邮件内容供调试
    logger.info(f"[EMAIL] To: {to}")
    logger.info(f"[EMAIL] Subject: {subject}")
    logger.info(f"[EMAIL] Body preview: {body[:200]}...")

    # TODO: 实现真实邮件发送
    # 在实现之前，返回 False 表示邮件发送未实现
    logger.error("Email sending not implemented yet - returning False")
    return False

    # 真实实现示例（使用 SendGrid）：
    # import os
    # try:
    #     import sendgrid
    #     from sendgrid.helpers.mail import Mail
    #
    #     api_key = os.environ.get('SENDGRID_API_KEY')
    #     if not api_key:
    #         logger.error("SENDGRID_API_KEY not configured")
    #         return False
    #
    #     sg = sendgrid.SendGridAPIClient(api_key=api_key)
    #     message = Mail(
    #         from_email='sourcing@yourdomain.com',
    #         to_emails=to,
    #         subject=subject,
    #         plain_text_content=body
    #     )
    #     response = sg.send(message)
    #     return response.status_code == 202
    # except Exception as e:
    #     logger.error(f"Failed to send email: {e}")
    #     return False
