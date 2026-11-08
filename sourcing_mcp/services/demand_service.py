"""Demand Service - 需求理解和结构化."""
import logging
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel

from . import BaseService, EventPublisher
from ..models import FieldIssue, RfqItem, Delivery

logger = logging.getLogger(__name__)


class ParsedIntent(BaseModel):
    """解析后的采购意图."""
    category: str
    specifications: dict[str, Any]
    constraints: dict[str, Any]
    confidence: float = 0.0


class ValidationResult(BaseModel):
    """校验结果."""
    is_valid: bool
    issues: list[FieldIssue]
    clarifying_questions: list[dict[str, str]]


class Alternative(BaseModel):
    """可替代方案."""
    description: str
    reason: str
    cost_impact: Optional[str] = None


class PriceRange(BaseModel):
    """价格区间估算."""
    min_price: float
    max_price: float
    currency: str
    confidence: float
    data_source: str
    sample_size: int


class DemandService(BaseService):
    """采购需求服务.

    职责：
    - 解析自然语言采购意图
    - 校验规格完整性
    - 建议可替代方案
    - 估算市场价格区间
    """

    def __init__(self):
        super().__init__()
        self.event_publisher = EventPublisher()

    async def initialize(self) -> None:
        """Initialize service."""
        logger.info("DemandService initialized")

    async def health_check(self) -> dict[str, Any]:
        """Health check."""
        return {
            "status": "healthy",
            "service": "demand",
            "version": "0.2.0",
        }

    async def parse_intent(
        self,
        raw_input: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ParsedIntent:
        """从自然语言解析采购意图.

        使用 LLM 提取结构化信息。

        Args:
            raw_input: 用户的自然语言描述
            context: 上下文信息（历史对话、用户偏好等）

        Returns:
            ParsedIntent: 包含 category, specifications, constraints
        """
        # TODO: 集成 LLM (Claude/GPT) 进行意图解析
        # 这里是简化版本

        logger.info(f"Parsing intent from: {raw_input[:100]}...")

        # 简单的关键词匹配（生产环境应使用 LLM）
        intent = ParsedIntent(
            category="cnc_machining",  # 默认
            specifications={},
            constraints={},
            confidence=0.5,
        )

        # 提取材料
        if "6061" in raw_input or "铝" in raw_input:
            intent.specifications["material"] = "6061-T6"
            intent.confidence += 0.1

        # 提取数量
        if "100" in raw_input:
            intent.specifications["quantity"] = {"value": "100", "unit": "pcs"}
            intent.confidence += 0.1

        # 提取交货地
        if "深圳" in raw_input or "shenzhen" in raw_input.lower():
            intent.constraints["delivery_city"] = "Shenzhen"
            intent.confidence += 0.1

        return intent

    async def validate_specs(
        self,
        specs: dict[str, Any],
        category: str = "cnc_machining",
    ) -> ValidationResult:
        """校验规格完整性.

        Args:
            specs: 规格字典
            category: 品类

        Returns:
            ValidationResult: 缺失字段、模糊字段、需要澄清的问题
        """
        issues: list[FieldIssue] = []
        questions: list[dict[str, str]] = []

        # 检查必填字段
        required_fields = {
            "cnc_machining": [
                "material",
                "quantity",
                "tolerance_general",
                "surface_finish",
            ]
        }

        for field in required_fields.get(category, []):
            if field not in specs or not specs[field]:
                issues.append(
                    FieldIssue(
                        path=f"/specifications/{field}",
                        code="missing",
                        severity="blocking",
                        reason=f"{field} is required for {category}",
                    )
                )

                # 生成澄清问题
                field_questions = {
                    "material": {
                        "zh": "请问零件的材料是什么？（例如：6061-T6、SUS304）",
                        "en": "What material should be used? (e.g., 6061-T6, SUS304)",
                    },
                    "quantity": {
                        "zh": "需要生产多少件？",
                        "en": "What is the required quantity?",
                    },
                    "tolerance_general": {
                        "zh": "公差要求是什么？（例如：ISO 2768-m）",
                        "en": "What are the tolerance requirements? (e.g., ISO 2768-m)",
                    },
                    "surface_finish": {
                        "zh": "表面处理要求是什么？（例如：阳极氧化、喷砂）",
                        "en": "What surface finish is required? (e.g., anodizing, sandblasting)",
                    },
                }

                if field in field_questions:
                    questions.append({
                        "path": f"/specifications/{field}",
                        "question_zh": field_questions[field]["zh"],
                        "question_en": field_questions[field]["en"],
                    })

        is_valid = len([i for i in issues if i.severity == "blocking"]) == 0

        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            clarifying_questions=questions,
        )

    async def suggest_alternatives(
        self,
        specs: dict[str, Any],
        category: str = "cnc_machining",
    ) -> list[Alternative]:
        """建议可替代方案.

        基于历史数据和市场情况。

        Args:
            specs: 当前规格
            category: 品类

        Returns:
            list[Alternative]: 可替代方案列表
        """
        alternatives: list[Alternative] = []

        # 材料替代
        if specs.get("material") == "6061-T6":
            alternatives.append(
                Alternative(
                    description="使用 7075-T6 铝合金",
                    reason="强度更高，适合高应力场景",
                    cost_impact="+15% ~ +25%",
                )
            )
            alternatives.append(
                Alternative(
                    description="使用 5052-H32 铝合金",
                    reason="成本更低，适合一般强度要求",
                    cost_impact="-10% ~ -15%",
                )
            )

        # 表面处理替代
        if specs.get("surface_finish") == "阳极氧化":
            alternatives.append(
                Alternative(
                    description="使用喷砂 + 清漆",
                    reason="成本更低，外观相似",
                    cost_impact="-20% ~ -30%",
                )
            )

        # 数量优化
        quantity = specs.get("quantity", {}).get("value")
        if quantity and int(quantity) < 100:
            alternatives.append(
                Alternative(
                    description="增加订单数量至 100 件",
                    reason="达到 MOQ，单价可降低",
                    cost_impact="单价 -15% ~ -25%",
                )
            )

        return alternatives

    async def estimate_market_price(
        self,
        specs: dict[str, Any],
        category: str = "cnc_machining",
    ) -> PriceRange:
        """估算市场价格区间.

        基于历史报价数据。
        明确标注：这是估算，不是报价。

        Args:
            specs: 规格
            category: 品类

        Returns:
            PriceRange: 带置信度和数据来源
        """
        # TODO: 基于历史数据的机器学习模型
        # 这里是简化版本

        async with self.db.connection() as conn:
            # 查询相似历史报价
            result = await conn.execute(
                """
                SELECT
                    AVG(unit_price) as avg_price,
                    MIN(unit_price) as min_price,
                    MAX(unit_price) as max_price,
                    COUNT(*) as count
                FROM quote_line ql
                JOIN quote q ON q.id = ql.quote_id
                JOIN rfq_item ri ON ri.id = ql.rfq_item_id
                WHERE ri.material LIKE $1
                    AND q.status = 'submitted'
                    AND q.currency = 'CNY'
                    AND q.submitted_at > now() - interval '90 days'
                """,
                [f"%{specs.get('material', '')}%"],
            )
            row = await result.fetchone()

        if row and row["count"] > 0:
            return PriceRange(
                min_price=float(row["min_price"] or 0),
                max_price=float(row["max_price"] or 0),
                currency="CNY",
                confidence=min(0.9, row["count"] / 100),
                data_source="historical_quotes",
                sample_size=row["count"],
            )
        else:
            # 无历史数据，返回保守估算
            return PriceRange(
                min_price=50.0,
                max_price=200.0,
                currency="CNY",
                confidence=0.3,
                data_source="fallback_estimate",
                sample_size=0,
            )
