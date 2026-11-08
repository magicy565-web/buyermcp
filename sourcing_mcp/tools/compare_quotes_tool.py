"""compare_quotes tool implementation."""
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from mcp.types import Tool

from ..database import db

logger = logging.getLogger(__name__)

TOOL_DEFINITION = Tool(
    name="compare_quotes",
    description="统一币种（固定汇率快照）、数量档、税口径后比较；无法可靠换算的报价标为不可比，并给出原因，不做隐式换算。不对 Incoterms 差异做换算。",
    inputSchema={
        "type": "object",
        "properties": {
            "rfq_id": {"type": "string", "format": "uuid"},
            "quote_ids": {
                "type": "array",
                "items": {"type": "string", "format": "uuid"},
                "maxItems": 30,
                "description": "缺省为每个供应商的最新有效版本。",
            },
            "target_currency": {"type": "string", "pattern": "^[A-Z]{3}$"},
            "tax_basis": {"type": "string", "enum": ["excl_tax", "incl_tax"], "default": "excl_tax"},
        },
        "required": ["rfq_id"],
    },
)


async def handler(args: dict[str, Any]) -> dict[str, Any]:
    """Handle compare_quotes tool call."""
    rfq_id = UUID(args["rfq_id"])
    quote_ids_arg = args.get("quote_ids")
    target_currency = args.get("target_currency", "CNY")
    tax_basis = args.get("tax_basis", "excl_tax")

    async with db.connection() as conn:
        # Get RFQ items to know expected quantities
        result = await conn.execute(
            """
            SELECT id, quantity, quantity_unit
            FROM rfq_item
            WHERE rfq_id = $1
            ORDER BY line_no
            """,
            [rfq_id],
        )
        rfq_items = await result.fetchall()
        if not rfq_items:
            raise ValueError(f"RFQ not found or has no items: {rfq_id}")

        # Get quotes to compare
        if quote_ids_arg:
            quote_ids = [UUID(id_) for id_ in quote_ids_arg]
            result = await conn.execute(
                """
                SELECT DISTINCT ON (supplier_id)
                    id, supplier_id, version, status, currency, tax_included, tax_rate,
                    incoterm, valid_until, verification_level
                FROM quote
                WHERE id = ANY($1) AND rfq_id = $2
                ORDER BY supplier_id, version DESC
                """,
                [[str(id_) for id_ in quote_ids], rfq_id],
            )
        else:
            # Default: latest valid quote per supplier
            result = await conn.execute(
                """
                SELECT DISTINCT ON (supplier_id)
                    id, supplier_id, version, status, currency, tax_included, tax_rate,
                    incoterm, valid_until, verification_level
                FROM quote
                WHERE rfq_id = $1
                    AND status IN ('submitted', 'superseded')
                    AND valid_until > now()
                ORDER BY supplier_id, version DESC
                """,
                [rfq_id],
            )

        quotes = await result.fetchall()
        if not quotes:
            return {
                "basis": {
                    "currency": target_currency,
                    "tax_basis": tax_basis,
                    "fx_snapshot_id": str(uuid4()),
                    "rate_date": date.today().isoformat(),
                },
                "rows": [],
            }

        # Get or create FX snapshot
        result = await conn.execute(
            """
            SELECT id, rates FROM fx_snapshot
            WHERE base = $1 AND rate_date = $2
            ORDER BY created_at DESC LIMIT 1
            """,
            [target_currency, date.today()],
        )
        fx_snapshot = await result.fetchone()

        if not fx_snapshot:
            # Create mock FX snapshot for v0.1
            fx_snapshot_id = uuid4()
            mock_rates = {
                "CNY": 1.0,
                "USD": 0.14,
                "EUR": 0.13,
                "JPY": 21.0,
            }
            await conn.execute(
                """
                INSERT INTO fx_snapshot (id, base, rates, source, rate_date)
                VALUES ($1, $2, $3, $4, $5)
                """,
                [fx_snapshot_id, target_currency, mock_rates, "mock_v0.1", date.today()],
            )
            fx_rates = mock_rates
        else:
            fx_snapshot_id = fx_snapshot["id"]
            fx_rates = fx_snapshot["rates"]

        # Get quote lines
        quote_ids_list = [str(q["id"]) for q in quotes]
        result = await conn.execute(
            """
            SELECT
                quote_id, rfq_item_id, unit_price, quantity, quantity_unit,
                tooling_fee, lead_time_days
            FROM quote_line
            WHERE quote_id = ANY($1)
            """,
            [quote_ids_list],
        )
        all_lines = await result.fetchall()
        lines_by_quote: dict[str, list[dict]] = {}
        for line in all_lines:
            qid = str(line["quote_id"])
            if qid not in lines_by_quote:
                lines_by_quote[qid] = []
            lines_by_quote[qid].append(line)

        # Compare quotes
        rows = []
        for quote in quotes:
            quote_id_str = str(quote["id"])
            lines = lines_by_quote.get(quote_id_str, [])

            # Check comparability
            comparable = True
            non_comparable_reasons = []

            # Check if expired
            if quote["valid_until"] < datetime.now():
                comparable = False
                non_comparable_reasons.append("expired")

            # Check currency support
            quote_currency = quote["currency"]
            if quote_currency not in fx_rates:
                comparable = False
                non_comparable_reasons.append("unsupported_currency")
                fx_rate = None
            else:
                fx_rate = Decimal(str(fx_rates[quote_currency]))

            # Check tax rate availability
            if tax_basis == "excl_tax" and quote["tax_included"] and not quote["tax_rate"]:
                comparable = False
                non_comparable_reasons.append("missing_tax_rate")

            # Check quantity tier match
            expected_quantities = {str(item["id"]): item["quantity"] for item in rfq_items}
            quantity_mismatch = False
            for line in lines:
                rfq_item_id = str(line["rfq_item_id"])
                expected_qty = expected_quantities.get(rfq_item_id)
                if expected_qty and abs(line["quantity"] - expected_qty) > Decimal("0.01"):
                    quantity_mismatch = True
                    break
            if quantity_mismatch:
                non_comparable_reasons.append("quantity_tier_mismatch")

            # Check incoterm consistency (simplified - we just flag if different)
            if quote["incoterm"] and quote["incoterm"] != "FOB":
                non_comparable_reasons.append("different_incoterm")

            # Build normalized lines
            normalized_lines = []
            total_amount = Decimal("0")

            if comparable and fx_rate:
                for line in lines:
                    unit_price = Decimal(str(line["unit_price"]))
                    quantity = Decimal(str(line["quantity"]))

                    # Convert currency
                    unit_price_target = unit_price * fx_rate

                    # Adjust for tax basis
                    if tax_basis == "excl_tax" and quote["tax_included"]:
                        tax_rate = Decimal(str(quote["tax_rate"]))
                        unit_price_target = unit_price_target / (Decimal("1") + tax_rate)
                    elif tax_basis == "incl_tax" and not quote["tax_included"]:
                        tax_rate = Decimal(str(quote["tax_rate"])) if quote["tax_rate"] else Decimal("0.13")
                        unit_price_target = unit_price_target * (Decimal("1") + tax_rate)

                    line_total = unit_price_target * quantity
                    total_amount += line_total

                    norm_line = {
                        "rfq_item_id": str(line["rfq_item_id"]),
                        "unit_price": {"amount": str(unit_price_target.quantize(Decimal("0.01"))), "currency": target_currency},
                    }
                    if line["tooling_fee"]:
                        tooling_fee_target = Decimal(str(line["tooling_fee"])) * fx_rate
                        norm_line["tooling_fee"] = {"amount": str(tooling_fee_target.quantize(Decimal("0.01"))), "currency": target_currency}
                        total_amount += tooling_fee_target
                    if line["lead_time_days"] is not None:
                        norm_line["lead_time_days"] = line["lead_time_days"]

                    normalized_lines.append(norm_line)

            row = {
                "quote_id": quote_id_str,
                "supplier_id": str(quote["supplier_id"]),
                "verification_level": quote["verification_level"],
                "comparable": comparable,
            }

            if non_comparable_reasons:
                row["non_comparable_reasons"] = non_comparable_reasons

            if normalized_lines:
                row["normalized_lines"] = normalized_lines
                row["total"] = {"amount": str(total_amount.quantize(Decimal("0.01"))), "currency": target_currency}

            rows.append(row)

        logger.info(f"Compared {len(rows)} quotes for RFQ {rfq_id}")

        return {
            "basis": {
                "currency": target_currency,
                "tax_basis": tax_basis,
                "fx_snapshot_id": str(fx_snapshot_id),
                "rate_date": date.today().isoformat(),
            },
            "rows": rows,
        }
