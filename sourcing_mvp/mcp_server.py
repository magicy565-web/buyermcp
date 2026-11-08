"""
AI Sourcing Partner - MVP MCP Server

6 个核心工具：
1. discover_suppliers - 发现供应商
2. prepare_inquiry - 准备询价
3. send_inquiry - 发送询价
4. track_response - 追踪回复
5. create_quote_request - 创建报价请求
6. get_quotes - 查询报价
"""
import asyncio
import logging
import os
from collections.abc import Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .database import Database
from .tools import discover, prepare, send, track
from .tools import create_quote_request, get_quotes
from .mcp_format_helpers import _format_create_quote_output, _format_get_quotes_output

# 全局数据库实例 - 统一路径
DB_PATH = os.environ.get("DATABASE_PATH", "sourcing_mvp.db")
db = Database(DB_PATH)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_server() -> Server:
    """创建 MCP Server"""
    server = Server("sourcing-partner")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """列出可用工具"""
        return [
            Tool(
                name="discover_suppliers",
                description=(
                    "从买手的采购意图找到 2-5 个合适的供应商。"
                    "返回真实供应商，带匹配理由和风险提示。"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "product_description": {
                            "type": "string",
                            "description": "产品描述（可以是一句话）",
                        },
                        "requirements": {
                            "type": "object",
                            "description": "采购需求（可选：moq, budget, delivery 等）",
                            "properties": {
                                "moq": {"type": "integer", "description": "最小订单量"},
                                "budget": {"type": "string", "description": "预算"},
                                "delivery": {"type": "string", "description": "交货要求"},
                            },
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "最多返回供应商数量",
                            "default": 5,
                        },
                        "buyer_id": {
                            "type": "string",
                            "description": "买手 ID（内部使用）",
                        },
                    },
                    "required": ["product_description"],
                },
            ),
            Tool(
                name="prepare_inquiry",
                description=(
                    "为选定的供应商准备询价邮件草稿。"
                    "生成专业的询价邮件，等待买手确认后发送。"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "case_id": {
                            "type": "string",
                            "description": "采购案例 ID",
                        },
                        "supplier_id": {
                            "type": "string",
                            "description": "供应商 ID",
                        },
                        "language": {
                            "type": "string",
                            "enum": ["en", "zh", "auto"],
                            "description": "邮件语言",
                            "default": "en",
                        },
                        "additional_requirements": {
                            "type": "string",
                            "description": "额外要求（可选）",
                        },
                    },
                    "required": ["case_id", "supplier_id"],
                },
            ),
            Tool(
                name="send_inquiry",
                description=(
                    "发送询价邮件给供应商。"
                    "买手确认后，实际发送邮件并开始追踪回复。"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "inquiry_id": {
                            "type": "string",
                            "description": "询价 ID",
                        },
                        "confirm": {
                            "type": "boolean",
                            "description": "买手确认发送（必须明确设为 true）",
                            "default": False,
                        },
                    },
                    "required": ["inquiry_id"],
                },
            ),
            Tool(
                name="track_response",
                description=(
                    "追踪询价回复状态。"
                    "检查供应商是否已回复，提取报价信息。"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "inquiry_id": {
                            "type": "string",
                            "description": "单个询价 ID（可选）",
                        },
                        "case_id": {
                            "type": "string",
                            "description": "追踪整个案例（可选）",
                        },
                    },
                },
            ),
            Tool(
                name="create_quote_request",
                description=(
                    "创建报价请求并生成专属链接。"
                    "买手授权后，生成供应商专属报价链接。"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "case_id": {
                            "type": "string",
                            "description": "采购案例 ID",
                        },
                        "supplier_id": {
                            "type": "string",
                            "description": "供应商 ID",
                        },
                        "product_name": {
                            "type": "string",
                            "description": "产品名称",
                        },
                        "product_description": {
                            "type": "string",
                            "description": "产品描述",
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "采购数量",
                        },
                        "specifications": {
                            "type": "object",
                            "description": "规格要求（可选）",
                        },
                        "quote_deadline_hours": {
                            "type": "integer",
                            "description": "报价截止时间（小时，默认72）",
                            "default": 72,
                        },
                        "confirm": {
                            "type": "boolean",
                            "description": "买手确认（必须明确设为 true）",
                            "default": False,
                        },
                        "base_url": {
                            "type": "string",
                            "description": "服务器地址（用于生成链接）",
                        },
                    },
                    "required": ["case_id", "supplier_id", "product_name", "quantity"],
                },
            ),
            Tool(
                name="get_quotes",
                description=(
                    "查询报价。"
                    "查询某个案例或报价请求的所有供应商报价。"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "case_id": {
                            "type": "string",
                            "description": "采购案例 ID（与 quote_request_id 二选一）",
                        },
                        "quote_request_id": {
                            "type": "string",
                            "description": "报价请求 ID（与 case_id 二选一）",
                        },
                    },
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> Sequence[TextContent]:
        """调用工具"""
        logger.info(f"Tool called: {name}")
        logger.debug(f"Arguments: {arguments}")

        try:
            if name == "discover_suppliers":
                result = await discover.discover_suppliers(arguments)
            elif name == "prepare_inquiry":
                result = await prepare.prepare_inquiry(arguments)
            elif name == "send_inquiry":
                result = await send.send_inquiry(arguments)
            elif name == "track_response":
                result = await track.track_response(arguments)
            elif name == "create_quote_request":
                result = await create_quote_request.create_quote_request(arguments)
            elif name == "get_quotes":
                result = await get_quotes.get_quotes(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

            logger.info(f"Tool {name} completed successfully")

            # 格式化输出
            if name == "discover_suppliers":
                formatted = _format_discover_output(result)
            elif name == "prepare_inquiry":
                formatted = _format_prepare_output(result)
            elif name == "send_inquiry":
                formatted = _format_send_output(result)
            elif name == "track_response":
                formatted = _format_track_output(result)
            elif name == "create_quote_request":
                formatted = _format_create_quote_output(result)
            elif name == "get_quotes":
                formatted = _format_get_quotes_output(result)
            else:
                formatted = str(result)

            return [TextContent(type="text", text=formatted)]

        except Exception as e:
            logger.error(f"Tool {name} failed: {e}", exc_info=True)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    return server


def _format_discover_output(result: dict) -> str:
    """格式化供应商发现结果"""
    lines = [
        f"🔍 Found {len(result['matches'])} suppliers",
        "",
        result["summary"],
        "",
    ]

    for i, match in enumerate(result["matches"], 1):
        confidence_emoji = {
            "high": "⭐⭐⭐⭐⭐",
            "medium": "⭐⭐⭐",
            "low": "⭐⭐",
        }.get(match["confidence"], "⭐")

        lines.append(f"{i}. **{match['supplier_name']}** {confidence_emoji}")
        lines.append(f"   Score: {match['match_score']:.0%}")

        if match["match_reasons"]:
            lines.append("   Reasons:")
            for reason in match["match_reasons"]:
                lines.append(f"   - {reason}")

        if match["caveats"]:
            lines.append("   ⚠️ Caveats:")
            for caveat in match["caveats"]:
                lines.append(f"   - {caveat}")

        lines.append("")

    lines.append(f"Case ID: {result['case_id']}")

    return "\n".join(lines)


def _format_prepare_output(result: dict) -> str:
    """格式化询价准备结果"""
    lines = [
        "📧 Inquiry email prepared:",
        "",
        f"**Subject:** {result['email_subject']}",
        "",
        "**Body:**",
        "```",
        result['email_body'],
        "```",
        "",
        f"Inquiry ID: {result['inquiry_id']}",
        "",
        "Would you like to:",
        "- Send this now (call send_inquiry)",
        "- Edit the message",
        "- Add more details",
    ]

    return "\n".join(lines)


def _format_send_output(result: dict) -> str:
    """格式化发送结果"""
    if result["sent"]:
        return f"""
✅ Email sent successfully!

{result['tracking_info']}

Inquiry ID: {result['inquiry_id']}
Sent at: {result['sent_at']}

You can track responses with: track_response(inquiry_id="{result['inquiry_id']}")
"""
    else:
        return f"""
❌ Failed to send email

{result['tracking_info']}

Please check the supplier contact information and try again.
"""


def _format_track_output(result: dict) -> str:
    """格式化追踪结果"""
    lines = [
        result["summary"],
        "",
    ]

    if result["inquiries"]:
        lines.append("Details:")
        for inquiry in result["inquiries"]:
            status_emoji = {
                "sent": "⏱️",
                "replied": "✅",
                "no_response": "❌",
                "bounced": "⚠️",
            }.get(inquiry["status"], "❓")

            lines.append(f"{status_emoji} {inquiry['supplier_name']}")
            lines.append(f"   Status: {inquiry['status']}")

            if inquiry.get("sent_at"):
                lines.append(f"   Sent: {inquiry['sent_at']}")

            if inquiry.get("response"):
                response = inquiry["response"]
                lines.append("   📬 Response:")
                if response.get("has_quote"):
                    if response.get("fob_price"):
                        lines.append(f"      Price: {response['fob_price']}")
                    if response.get("moq"):
                        lines.append(f"      MOQ: {response['moq']}")
                    if response.get("lead_time"):
                        lines.append(f"      Lead time: {response['lead_time']}")

            if inquiry.get("needs_follow_up"):
                lines.append("   📬 Needs follow-up")

            lines.append("")

    return "\n".join(lines)


async def main():
    """主入口"""
    logger.info("Starting AI Sourcing Partner MCP Server (MVP)")

    server = create_server()

    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP Server ready - 4 core tools available")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
