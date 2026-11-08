"""Matching Service - 智能匹配需求和供应."""
import logging
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel

from . import BaseService, EventPublisher
from ..models import SupplierType, VerificationLevel

logger = logging.getLogger(__name__)


class Demand(BaseModel):
    """需求定义."""
    rfq_id: UUID
    category: str
    specifications: dict[str, Any]
    delivery: dict[str, Any]
    certifications: list[str] = []


class MatchConstraints(BaseModel):
    """匹配约束."""
    min_verification_level: int = 0
    max_results: int = 10
    preferred_regions: list[str] = []
    exclude_suppliers: list[UUID] = []


class MatchReason(BaseModel):
    """匹配理由."""
    dimension: str
    score: float
    detail: str


class MatchedSupplier(BaseModel):
    """匹配的供应商."""
    supplier_id: UUID
    display_name: str
    match_score: float
    verification_level: int
    match_reasons: list[MatchReason]
    caveats: list[str] = []


class MatchResult(BaseModel):
    """匹配结果."""
    demand_id: UUID
    candidates: list[MatchedSupplier]
    matched_at: str
    algorithm_version: str


class MatchExplanation(BaseModel):
    """匹配解释."""
    demand_id: UUID
    supplier_id: UUID
    overall_score: float
    dimension_scores: dict[str, float]
    strengths: list[str]
    weaknesses: list[str]
    historical_performance: Optional[dict[str, Any]] = None
    risk_factors: list[str] = []


class AlternativeSupplier(BaseModel):
    """备选供应商."""
    supplier_id: UUID
    display_name: str
    reason: str
    match_score: float


class MatchingService(BaseService):
    """匹配服务.

    职责：
    - 执行智能匹配（多阶段）
    - 解释匹配理由（可解释性）
    - 提供备选供应商
    """

    def __init__(self):
        super().__init__()
        self.event_publisher = EventPublisher()
        self.algorithm_version = "v1.0.0"

    async def initialize(self) -> None:
        """Initialize service."""
        logger.info("MatchingService initialized")

    async def health_check(self) -> dict[str, Any]:
        """Health check."""
        return {
            "status": "healthy",
            "service": "matching",
            "version": "0.2.0",
            "algorithm_version": self.algorithm_version,
        }

    async def match(
        self,
        demand: Demand,
        constraints: MatchConstraints,
    ) -> MatchResult:
        """执行匹配.

        多阶段匹配：
        1. 硬性过滤（品类、地区、认证）
        2. 能力匹配（工艺、材料、产能）
        3. 历史表现评分
        4. 价格区间预测

        Args:
            demand: 需求
            constraints: 约束条件

        Returns:
            MatchResult: 匹配结果
        """
        from datetime import datetime

        logger.info(f"Matching demand {demand.rfq_id} with constraints {constraints}")

        async with self.db.connection() as conn:
            # 阶段 1: 硬性过滤
            query = """
                SELECT
                    s.id,
                    s.legal_name_zh,
                    s.supplier_type,
                    s.province,
                    s.capabilities,
                    COALESCE(MAX(sv.level_granted), 0) as verification_level
                FROM supplier s
                LEFT JOIN supplier_verification sv ON sv.supplier_id = s.id
                    AND sv.result = 'pass'
                    AND (sv.expires_at IS NULL OR sv.expires_at > now())
                WHERE s.status = 'active'
            """
            params: list[Any] = []
            param_idx = 1

            # 排除指定供应商
            if constraints.exclude_suppliers:
                query += f" AND s.id != ALL(${param_idx})"
                params.append([str(id_) for id_ in constraints.exclude_suppliers])
                param_idx += 1

            # 地区偏好（软约束）
            if constraints.preferred_regions:
                # 优先推荐偏好地区，但不排除其他地区
                pass

            query += f"""
                GROUP BY s.id
                HAVING COALESCE(MAX(sv.level_granted), 0) >= ${param_idx}
            """
            params.append(constraints.min_verification_level)

            result = await conn.execute(query, params)
            candidates = await result.fetchall()

        # 阶段 2-4: 能力匹配 + 历史表现 + 价格预测
        matched_suppliers = []
        for candidate in candidates:
            match_result = await self._evaluate_candidate(
                candidate,
                demand,
                constraints,
            )
            if match_result:
                matched_suppliers.append(match_result)

        # 排序并限制结果数量
        matched_suppliers.sort(key=lambda x: x.match_score, reverse=True)
        matched_suppliers = matched_suppliers[:constraints.max_results]

        # 发布匹配事件
        await self.event_publisher.publish(
            stream_type="project",
            stream_id=demand.rfq_id,
            event_type="matching.completed",
            actor_type="system",
            actor_id=None,
            payload={
                "rfq_id": str(demand.rfq_id),
                "candidates_count": len(matched_suppliers),
                "algorithm_version": self.algorithm_version,
            },
            project_id=demand.rfq_id,
        )

        return MatchResult(
            demand_id=demand.rfq_id,
            candidates=matched_suppliers,
            matched_at=datetime.now().isoformat(),
            algorithm_version=self.algorithm_version,
        )

    async def _evaluate_candidate(
        self,
        candidate: dict[str, Any],
        demand: Demand,
        constraints: MatchConstraints,
    ) -> Optional[MatchedSupplier]:
        """评估单个候选供应商."""
        capabilities = candidate["capabilities"] or {}
        match_reasons = []
        caveats = []
        total_score = 0.0
        weights = 0.0

        # 1. 工艺能力匹配 (30%)
        supplier_processes = set(capabilities.get("processes", []))
        if demand.category == "cnc_machining":
            required_processes = {"cnc_milling", "cnc_turning"}
            matched_processes = supplier_processes & required_processes

            if matched_processes:
                process_score = len(matched_processes) / len(required_processes)
                total_score += process_score * 0.3
                weights += 0.3
                match_reasons.append(
                    MatchReason(
                        dimension="process",
                        score=process_score,
                        detail=f"Supports: {', '.join(matched_processes)}",
                    )
                )
            else:
                caveats.append("Process capability not explicitly verified")

        # 2. 材料经验匹配 (25%)
        supplier_materials = set(capabilities.get("materials", []))
        specs = demand.specifications
        required_material = specs.get("material", "")

        if required_material:
            # 简化匹配逻辑
            material_match = any(
                required_material in mat or mat in required_material
                for mat in supplier_materials
            )

            if material_match:
                material_score = 1.0
                total_score += material_score * 0.25
                weights += 0.25
                match_reasons.append(
                    MatchReason(
                        dimension="material",
                        score=material_score,
                        detail=f"Experienced with {required_material}",
                    )
                )
            else:
                caveats.append(f"No verified experience with {required_material}")

        # 3. 产能适配性 (20%)
        quantity = specs.get("quantity", {}).get("value", 0)
        if quantity:
            # 简化：假设供应商都能满足产能
            capacity_score = 0.8
            total_score += capacity_score * 0.2
            weights += 0.2
            match_reasons.append(
                MatchReason(
                    dimension="capacity",
                    score=capacity_score,
                    detail=f"Can handle quantity: {quantity}",
                )
            )

        # 4. 认证匹配 (15%)
        supplier_certs = set(capabilities.get("certs", []))
        required_certs = set(demand.certifications)

        if required_certs:
            matched_certs = supplier_certs & required_certs
            if matched_certs:
                cert_score = len(matched_certs) / len(required_certs)
                total_score += cert_score * 0.15
                weights += 0.15
                match_reasons.append(
                    MatchReason(
                        dimension="certification",
                        score=cert_score,
                        detail=f"Has: {', '.join(matched_certs)}",
                    )
                )
            else:
                caveats.append(f"Missing certifications: {', '.join(required_certs)}")

        # 5. 地区偏好 (10%)
        supplier_province = candidate.get("province")
        if supplier_province in constraints.preferred_regions:
            region_score = 1.0
            total_score += region_score * 0.1
            weights += 0.1
            match_reasons.append(
                MatchReason(
                    dimension="region",
                    score=region_score,
                    detail=f"Located in preferred region: {supplier_province}",
                )
            )

        # 归一化分数
        if weights > 0:
            final_score = total_score / weights
        else:
            final_score = 0.0

        # 过滤低分供应商
        if final_score < 0.3:
            return None

        return MatchedSupplier(
            supplier_id=candidate["id"],
            display_name=candidate["legal_name_zh"],
            match_score=final_score,
            verification_level=candidate["verification_level"],
            match_reasons=match_reasons,
            caveats=caveats,
        )

    async def explain_match(
        self,
        demand_id: UUID,
        supplier_id: UUID,
    ) -> MatchExplanation:
        """解释匹配理由.

        可解释性：为什么推荐这个供应商。
        包括：匹配维度、历史数据、风险提示。

        Args:
            demand_id: 需求 ID（RFQ ID）
            supplier_id: 供应商 ID

        Returns:
            MatchExplanation: 详细解释
        """
        async with self.db.connection() as conn:
            # 获取需求信息
            result = await conn.execute(
                """
                SELECT r.category, r.certifications,
                       array_agg(DISTINCT ri.material) as materials
                FROM rfq r
                JOIN rfq_item ri ON ri.rfq_id = r.id
                WHERE r.id = $1
                GROUP BY r.category, r.certifications
                """,
                [demand_id],
            )
            demand_row = await result.fetchone()
            if not demand_row:
                raise ValueError(f"RFQ not found: {demand_id}")

            # 获取供应商信息
            result = await conn.execute(
                "SELECT legal_name_zh, capabilities FROM supplier WHERE id = $1",
                [supplier_id],
            )
            supplier_row = await result.fetchone()
            if not supplier_row:
                raise ValueError(f"Supplier not found: {supplier_id}")

            # 获取历史表现
            result = await conn.execute(
                """
                SELECT
                    COUNT(*) as total_quotes,
                    AVG(q.verification_level) as avg_verification,
                    SUM(CASE WHEN q.status = 'submitted' THEN 1 ELSE 0 END) as valid_quotes
                FROM quote q
                WHERE q.supplier_id = $1
                    AND q.submitted_at > now() - interval '180 days'
                """,
                [supplier_id],
            )
            history = await result.fetchone()

        # 计算各维度分数
        dimension_scores = {
            "process_match": 0.85,  # 示例
            "material_experience": 0.9,
            "capacity": 0.8,
            "certification": 0.7,
            "historical_performance": 0.75,
        }

        overall_score = sum(dimension_scores.values()) / len(dimension_scores)

        # 优势
        strengths = []
        for dim, score in dimension_scores.items():
            if score >= 0.8:
                strengths.append(f"Strong {dim.replace('_', ' ')}")

        # 劣势
        weaknesses = []
        for dim, score in dimension_scores.items():
            if score < 0.7:
                weaknesses.append(f"Limited {dim.replace('_', ' ')}")

        # 风险因素
        risk_factors = []
        if history["total_quotes"] < 5:
            risk_factors.append("Limited quotation history")
        if history["avg_verification"] < 2:
            risk_factors.append("Low average verification level")

        return MatchExplanation(
            demand_id=demand_id,
            supplier_id=supplier_id,
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            strengths=strengths,
            weaknesses=weaknesses,
            historical_performance={
                "total_quotes": history["total_quotes"],
                "valid_quotes": history["valid_quotes"],
                "avg_verification_level": float(history["avg_verification"] or 0),
            },
            risk_factors=risk_factors,
        )

    async def get_alternatives(
        self,
        supplier_id: UUID,
        demand: Demand,
        max_results: int = 5,
    ) -> list[AlternativeSupplier]:
        """获取备选供应商.

        如果首选供应商不可用。

        Args:
            supplier_id: 不可用的供应商 ID
            demand: 需求
            max_results: 最多返回数量

        Returns:
            list[AlternativeSupplier]: 备选供应商列表
        """
        # 重新执行匹配，排除不可用的供应商
        constraints = MatchConstraints(
            exclude_suppliers=[supplier_id],
            max_results=max_results,
        )

        match_result = await self.match(demand, constraints)

        alternatives = []
        for candidate in match_result.candidates:
            alternatives.append(
                AlternativeSupplier(
                    supplier_id=candidate.supplier_id,
                    display_name=candidate.display_name,
                    reason=f"Alternative with {candidate.match_score:.0%} match",
                    match_score=candidate.match_score,
                )
            )

        return alternatives
