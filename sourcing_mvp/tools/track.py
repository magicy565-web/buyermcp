"""
MCP Tool: track_response

追踪询价回复状态
"""
import logging
from typing import Any
from datetime import datetime

from ..models import (
    TrackResponseInput,
    TrackResponseOutput,
    InquiryStatus,
)
from ..database import db

logger = logging.getLogger(__name__)


async def track_response(args: dict[str, Any]) -> dict[str, Any]:
    """
    追踪询价回复

    检查供应商是否已回复，并提取关键信息。
    """
    input_data = TrackResponseInput(**args)

    if input_data.inquiry_id:
        # 追踪单个询价
        inquiries = [db.get_inquiry(str(input_data.inquiry_id))]
    elif input_data.case_id:
        # 追踪整个案例的所有询价
        inquiries = db.get_case_inquiries(str(input_data.case_id))
    else:
        raise ValueError("Either inquiry_id or case_id is required")

    # 检查每个询价的状态
    inquiry_statuses = []
    has_new_responses = False

    for inquiry in inquiries:
        if not inquiry:
            continue

        # 获取供应商信息
        supplier = db.get_supplier(inquiry["supplier_id"])
        supplier_name = supplier["name"] if supplier else "Unknown"

        status_info = {
            "inquiry_id": inquiry["id"],
            "supplier_id": inquiry["supplier_id"],
            "supplier_name": supplier_name,
            "status": inquiry["status"],
            "sent_at": inquiry.get("sent_at"),
        }

        if inquiry["status"] == InquiryStatus.SENT.value:
            # 检查是否有新回复
            # TODO: 实现邮件回复检查
            # 这里暂时模拟
            new_response = await _check_for_response(inquiry["id"])

            if new_response:
                # 更新询价状态
                db.update_inquiry(inquiry["id"], {
                    "status": InquiryStatus.REPLIED.value,
                    "response": new_response,
                })
                status_info["status"] = InquiryStatus.REPLIED.value
                status_info["response"] = new_response
                has_new_responses = True
            else:
                # 检查是否需要跟进
                follow_up_at = inquiry.get("follow_up_at")
                if follow_up_at:
                    follow_up_time = datetime.fromisoformat(follow_up_at)
                    if datetime.now() > follow_up_time:
                        status_info["needs_follow_up"] = True

        elif inquiry["status"] == InquiryStatus.REPLIED.value:
            status_info["response"] = inquiry.get("response")

        inquiry_statuses.append(status_info)

    # 生成摘要
    summary = _generate_tracking_summary(inquiry_statuses, has_new_responses)

    output = TrackResponseOutput(
        inquiries=inquiry_statuses,
        summary=summary,
        has_new_responses=has_new_responses,
    )

    return output.model_dump()


async def _check_for_response(inquiry_id: str) -> dict | None:
    """
    检查邮件回复

    MVP 阶段要求：
    - 不允许随机生成伪造报价
    - 必须实现真实邮件检查，或明确返回 None

    实现选项：
    - 方案 1：使用 Gmail API 读取收件箱（推荐）
    - 方案 2：使用 IMAP 读取邮件
    - 方案 3：供应商通过 Webhook 提交
    """
    # TODO: 实现真实邮件检查
    # 在实现之前，返回 None 表示无回复
    logger.debug(f"Checking response for inquiry {inquiry_id} - email checking not implemented yet")
    return None

    # 真实实现示例（使用 Gmail API）：
    # import os
    # try:
    #     from google.oauth2.credentials import Credentials
    #     from googleapiclient.discovery import build
    #
    #     token_file = os.environ.get('GMAIL_TOKEN_FILE', 'token.json')
    #     if not os.path.exists(token_file):
    #         logger.error("Gmail credentials not configured")
    #         return None
    #
    #     creds = Credentials.from_authorized_user_file(token_file)
    #     service = build('gmail', 'v1', credentials=creds)
    #
    #     # 获取询价信息以匹配邮件
    #     inquiry = db.get_inquiry(inquiry_id)
    #     if not inquiry:
    #         return None
    #
    #     # 搜索相关邮件
    #     results = service.users().messages().list(
    #         userId='me',
    #         q=f'subject:"Re: {inquiry["email_subject"]}"',
    #         maxResults=1
    #     ).execute()
    #
    #     messages = results.get('messages', [])
    #     if messages:
    #         msg = service.users().messages().get(
    #             userId='me',
    #             id=messages[0]['id']
    #         ).execute()
    #
    #         # 提取邮件内容
    #         email_body = _extract_email_body(msg)
    #
    #         # 使用 LLM 提取报价信息
    #         quote_info = await _extract_quote_info(email_body)
    #
    #         return {
    #             "received_at": datetime.now().isoformat(),
    #             "has_quote": quote_info.get("has_quote", False),
    #             "fob_price": quote_info.get("price"),
    #             "moq": quote_info.get("moq"),
    #             "lead_time": quote_info.get("lead_time"),
    #             "payment_terms": quote_info.get("payment_terms"),
    #             "raw_email": email_body,
    #             "extraction_confidence": quote_info.get("confidence", 0),
    #         }
    #
    #     return None
    # except Exception as e:
    #     logger.error(f"Failed to check email: {e}")
    #     return None


def _generate_tracking_summary(
    inquiry_statuses: list[dict],
    has_new_responses: bool,
) -> str:
    """生成追踪摘要"""
    if not inquiry_statuses:
        return "No inquiries to track."

    total = len(inquiry_statuses)
    sent = sum(1 for i in inquiry_statuses if i["status"] == InquiryStatus.SENT.value)
    replied = sum(1 for i in inquiry_statuses if i["status"] == InquiryStatus.REPLIED.value)

    summary_parts = [f"Tracking {total} inquir{'y' if total == 1 else 'ies'}:"]

    if replied > 0:
        summary_parts.append(f"✅ {replied} replied")

    if sent > 0:
        summary_parts.append(f"⏱️ {sent} waiting")

    if has_new_responses:
        summary_parts.append("\n🔔 New response received!")

    needs_follow_up = sum(1 for i in inquiry_statuses if i.get("needs_follow_up"))
    if needs_follow_up > 0:
        summary_parts.append(f"\n📬 {needs_follow_up} need follow-up")

    return " ".join(summary_parts)
