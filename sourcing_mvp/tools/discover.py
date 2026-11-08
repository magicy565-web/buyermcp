"""
MCP Tool: discover_suppliers

从买手的采购意图找到合适的供应商
"""
import logging
from typing import Any
from uuid import uuid4

from ..models import (
    DiscoverSuppliersInput,
    DiscoverSuppliersOutput,
    SupplierMatch,
    SourcingCase,
    CaseStatus,
)
from ..database import db

logger = logging.getLogger(__name__)


async def discover_suppliers(args: dict[str, Any]) -> dict[str, Any]:
    """
    发现供应商工具

    根据产品描述和需求，从数据库中找到 2-5 个合适的供应商。

    重点：
    - 真实供应商，不虚构
    - 明确匹配理由
    - 标注风险和不确定性
    """
    # 解析输入
    input_data = DiscoverSuppliersInput(**args)

    logger.info(f"Discovering suppliers for: {input_data.product_description[:100]}...")

    # 提取关键词（简化版，生产环境应使用 LLM）
    keywords = _extract_keywords(input_data.product_description)
    categories = _map_to_categories(keywords)

    logger.debug(f"Extracted keywords: {keywords}, categories: {categories}")

    # 搜索供应商
    all_suppliers = db.search_suppliers(categories=categories, active_only=True)

    if not all_suppliers:
        # 没有找到供应商
        logger.warning(f"No suppliers found for categories: {categories}")

        # 创建空案例记录无匹配情况
        case_id = _create_or_update_case(
            buyer_id=args.get("buyer_id", "demo_buyer"),
            product_description=input_data.product_description,
            requirements=input_data.requirements,
            discovered_suppliers=[],
        )

        return {
            "case_id": case_id,
            "matches": [],
            "summary": "Sorry, I couldn't find suitable suppliers in our network yet. "
                      "This product category is not covered. Could you try a different product?",
        }

    # 评分和排序
    scored_suppliers = []
    for supplier in all_suppliers:
        score, reasons, caveats = _score_supplier(
            supplier,
            input_data.product_description,
            input_data.requirements,
        )

        if score > 0.3:  # 只保留分数 > 0.3 的
            scored_suppliers.append({
                "supplier": supplier,
                "score": score,
                "reasons": reasons,
                "caveats": caveats,
            })

    # 排序并限制数量
    scored_suppliers.sort(key=lambda x: x["score"], reverse=True)
    top_suppliers = scored_suppliers[:input_data.max_results]

    # 构建匹配结果
    matches = []
    for item in top_suppliers:
        supplier = item["supplier"]

        # 判断置信度
        if item["score"] >= 0.8:
            confidence = "high"
        elif item["score"] >= 0.6:
            confidence = "medium"
        else:
            confidence = "low"

        match = SupplierMatch(
            supplier_id=supplier["id"],
            supplier_name=supplier["name"],
            match_score=item["score"],
            match_reasons=item["reasons"],
            caveats=item["caveats"],
            confidence=confidence,
        )
        matches.append(match)

    # 创建或更新 Sourcing Case
    case_id = _create_or_update_case(
        buyer_id=args.get("buyer_id", "demo_buyer"),
        product_description=input_data.product_description,
        requirements=input_data.requirements,
        discovered_suppliers=[m.supplier_id for m in matches],
    )

    # 生成摘要
    summary = _generate_summary(matches, input_data.requirements)

    output = DiscoverSuppliersOutput(
        case_id=case_id,
        matches=matches,
        summary=summary,
    )

    logger.info(f"Found {len(matches)} suppliers for case {case_id}")

    return output.model_dump()


def _extract_keywords(description: str) -> list[str]:
    """提取关键词（简化版）"""
    keywords = []
    description_lower = description.lower()

    # 产品类型
    if "coffee" in description_lower or "espresso" in description_lower:
        keywords.append("coffee")
    if "portable" in description_lower or "travel" in description_lower:
        keywords.append("portable")
    if "electronic" in description_lower or "usb" in description_lower:
        keywords.append("electronic")
    if "bottle" in description_lower or "container" in description_lower:
        keywords.append("container")
    if "packaging" in description_lower or "box" in description_lower:
        keywords.append("packaging")

    return keywords


def _map_to_categories(keywords: list[str]) -> list[str]:
    """映射到品类"""
    category_mapping = {
        "coffee": ["small_appliances", "coffee_makers"],
        "portable": ["portable_electronics", "small_appliances"],
        "electronic": ["electronics", "portable_electronics"],
        "container": ["packaging", "containers"],
        "packaging": ["packaging", "printing"],
    }

    categories = set()
    for keyword in keywords:
        if keyword in category_mapping:
            categories.update(category_mapping[keyword])

    return list(categories) if categories else ["general"]


def _score_supplier(
    supplier: dict,
    product_description: str,
    requirements: dict,
) -> tuple[float, list[str], list[str]]:
    """
    评分供应商

    返回：(分数, 匹配理由, 注意事项)
    """
    score = 0.0
    reasons = []
    caveats = []

    # 1. 品类匹配 (40%)
    product_lower = product_description.lower()
    category_match = False
    for category in supplier["categories"]:
        if category in product_lower or any(
            keyword in category for keyword in ["coffee", "appliance", "electronic"]
        ):
            category_match = True
            reasons.append(f"Specializes in {category.replace('_', ' ')}")
            score += 0.4
            break

    if not category_match:
        caveats.append("Product category not explicitly verified")

    # 2. MOQ 匹配 (25%)
    required_moq = requirements.get("moq")
    if required_moq:
        moq_str = supplier["capabilities"].get("moq_range", "")
        if moq_str:
            try:
                # "50-500 units" -> 提取数字，处理范围格式
                # 移除 "units" 等单位词
                moq_str_cleaned = moq_str.lower().replace("units", "").replace("unit", "").strip()

                # 处理范围格式 "50-500" 或 "50 - 500"
                numbers = []
                for part in moq_str_cleaned.replace("-", " ").split():
                    part_cleaned = part.strip()
                    if part_cleaned.isdigit():
                        numbers.append(int(part_cleaned))

                if numbers:
                    min_moq = min(numbers)
                    if required_moq >= min_moq:
                        score += 0.25
                        reasons.append(f"MOQ flexible (from {min_moq} units)")
                    else:
                        caveats.append(f"MOQ may be higher than your requirement ({min_moq}+)")
            except Exception as e:
                logger.warning(f"Failed to parse MOQ '{moq_str}': {e}")
                pass
    else:
        # 没有 MOQ 要求，给一半分
        score += 0.125

    # 3. 核验状态 (20%)
    verification = supplier.get("verification", {})
    if verification.get("email_verified"):
        score += 0.1
        reasons.append("Contact verified")
    else:
        caveats.append("Contact not yet verified")

    if verification.get("past_orders", 0) > 0:
        score += 0.1
        reasons.append(f"{verification['past_orders']} past orders")

    # 4. 响应率 (15%)
    response_rate = supplier.get("response_rate")
    if response_rate is not None:
        score += response_rate * 0.15

        if response_rate >= 0.7:
            reasons.append(f"Good response rate ({response_rate:.0%})")
        elif response_rate < 0.5:
            caveats.append("Limited response history")
    else:
        # response_rate 为 None（测试数据或新供应商），不加分也不扣分
        caveats.append("No response history available")

    # 5. 加分项
    capabilities = supplier.get("capabilities", {})
    if capabilities.get("certifications"):
        certs = capabilities["certifications"]
        if any(cert in ["CE", "FCC", "ISO9001"] for cert in certs):
            reasons.append(f"Certified: {', '.join(certs[:2])}")

    if capabilities.get("export_experience"):
        reasons.append(capabilities["export_experience"])

    return score, reasons, caveats


def _create_or_update_case(
    buyer_id: str,
    product_description: str,
    requirements: dict,
    discovered_suppliers: list[str],
) -> str:
    """创建或更新采购案例"""
    from datetime import datetime

    # 简化：总是创建新案例
    case_id = str(uuid4())

    case_data = {
        "id": case_id,
        "buyer_id": buyer_id,
        "initial_query": product_description,
        "product_description": product_description,
        "requirements": requirements,
        "status": CaseStatus.DISCOVERING.value,
        "discovered_suppliers": discovered_suppliers,
        "message_count": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    db.create_case(case_data)

    return case_id


def _generate_summary(matches: list[SupplierMatch], requirements: dict) -> str:
    """生成摘要文本"""
    if not matches:
        return "No suitable suppliers found."

    count = len(matches)
    high_conf = sum(1 for m in matches if m.confidence == "high")

    summary = f"I found {count} suitable supplier{'s' if count > 1 else ''}. "

    if high_conf > 0:
        summary += f"{high_conf} with high confidence match. "

    summary += "Which one would you like me to contact?"

    return summary
