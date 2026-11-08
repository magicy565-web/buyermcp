

def _format_create_quote_output(result: dict) -> str:
    """格式化创建报价请求结果"""
    lines = [
        f"✅ Quote request created",
        "",
        f"**Supplier**: {result['supplier']['name']}",
        f"**Email**: {result['supplier']['email']}",
        f"**Expires**: {result['expires_at']}",
        "",
        "📋 **Quote Link**:",
        f"{result['quote_link']}",
        "",
        result["message"],
    ]
    return "\n".join(lines)


def _format_get_quotes_output(result: dict) -> str:
    """格式化查询报价结果"""
    lines = [
        f"📊 {result['total_count']} Quote(s) Received",
        "",
        result["summary"],
    ]

    if result["quotes"]:
        lines.append("")
        lines.append("**Detailed Quotes**:")
        lines.append("")

        for i, quote in enumerate(result["quotes"], 1):
            status_emoji = "❌" if quote["is_expired"] else "✅"
            lines.append(f"{i}. {status_emoji} **{quote['supplier_name']}** (v{quote['version']})")
            lines.append(f"   Price: {quote['currency']} {quote['unit_price']}/unit")
            lines.append(f"   MOQ: {quote['moq']} units")
            lines.append(f"   Lead Time: {quote['lead_time_days']} days")
            lines.append(f"   Trade Term: {quote['trade_term']}")
            lines.append(f"   Valid Until: {quote['quote_valid_until']}")

            if quote["payment_terms"]:
                lines.append(f"   Payment: {quote['payment_terms']}")

            if quote["specification_notes"]:
                lines.append(f"   ⚠️ Spec Notes: {quote['specification_notes']}")

            lines.append(f"   Submitted: {quote['submitted_at']}")
            lines.append("")

    return "\n".join(lines)
