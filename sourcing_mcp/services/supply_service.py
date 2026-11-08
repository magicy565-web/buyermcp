"""Supply Service - 供应商管理和能力查询."""
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel

from . import BaseService, EventPublisher
from ..models import SupplierType, VerificationLevel

logger = logging.getLogger(__name__)


class SearchCriteria(BaseModel):
    """搜索条件."""
    category: str
    processes: list[str] = []
    materials: list[str] = []
    region: Optional[str] = None
    certifications: list[str] = []


class SupplierFilters(BaseModel):
    """过滤条件."""
    min_verification_level: int = 0
    supplier_type: Optional[SupplierType] = None
    provinces: list[str] = []
    exclude_supplier_ids: list[UUID] = []
    max_results: int = 10


class SupplierProfile(BaseModel):
    """供应商档案."""
    supplier_id: UUID
    display_name: str
    supplier_type: SupplierType
    province: Optional[str] = None
    verification_level: int
    match_score: float
    capabilities: dict[str, Any]


class VerificationStatus(BaseModel):
    """核验状态."""
    supplier_id: UUID
    supplier_type: SupplierType
    overall_level: int
    checks: list[dict[str, Any]]
    caveats: list[str] = []


class VerificationTask(BaseModel):
    """核验任务."""
    task_id: UUID
    supplier_id: UUID
    check_type: str
    status: str
    created_at: datetime


class CapabilityMatrix(BaseModel):
    """供应商能力矩阵."""
    supplier_id: UUID
    processes: list[str]
    materials: list[str]
    equipment: list[str]
    capacity_range: dict[str, Any]
    certifications: list[str]
    case_studies: list[dict[str, Any]]


class SupplyService(BaseService):
    """供应商服务.

    职责：
    - 搜索供应商（多维度）
    - 获取供应商核验状态
    - 请求人工核验
    - 获取供应商能力矩阵
    """

    def __init__(self):
        super().__init__()
        self.event_publisher = EventPublisher()

    async def initialize(self) -> None:
        """Initialize service."""
        logger.info("SupplyService initialized")

    async def health_check(self) -> dict[str, Any]:
        """Health check."""
        return {
            "status": "healthy",
            "service": "supply",
            "version": "0.2.0",
        }

    async def search_suppliers(
        self,
        criteria: SearchCriteria,
        filters: SupplierFilters,
    ) -> list[SupplierProfile]:
        """搜索供应商.

        支持多维度搜索：工艺、材料、地区、认证
        返回带匹配度分数的结果。

        Args:
            criteria: 搜索条件
            filters: 过滤条件

        Returns:
            list[SupplierProfile]: 带匹配度分数的供应商列表
        """
        async with self.db.connection() as conn:
            # 构建查询
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

            # 应用过滤器
            if filters.supplier_type:
                query += f" AND s.supplier_type = ${param_idx}"
                params.append(filters.supplier_type.value)
                param_idx += 1

            if filters.provinces:
                query += f" AND s.province = ANY(${param_idx})"
                params.append(filters.provinces)
                param_idx += 1

            if filters.exclude_supplier_ids:
                query += f" AND s.id != ALL(${param_idx})"
                params.append([str(id_) for id_ in filters.exclude_supplier_ids])
                param_idx += 1

            query += f"""
                GROUP BY s.id
                HAVING COALESCE(MAX(sv.level_granted), 0) >= ${param_idx}
                ORDER BY verification_level DESC
                LIMIT ${param_idx + 1}
            """
            params.extend([filters.min_verification_level, filters.max_results])

            result = await conn.execute(query, params)
            rows = await result.fetchall()

        # 构建结果并计算匹配度
        profiles = []
        for row in rows:
            capabilities = row["capabilities"] or {}
            match_score = self._calculate_match_score(capabilities, criteria)

            profiles.append(
                SupplierProfile(
                    supplier_id=row["id"],
                    display_name=row["legal_name_zh"],
                    supplier_type=row["supplier_type"],
                    province=row["province"],
                    verification_level=row["verification_level"],
                    match_score=match_score,
                    capabilities=capabilities,
                )
            )

        # 按匹配度排序
        profiles.sort(key=lambda p: p.match_score, reverse=True)

        return profiles

    def _calculate_match_score(
        self,
        capabilities: dict[str, Any],
        criteria: SearchCriteria,
    ) -> float:
        """计算匹配度分数 (0-1)."""
        score = 0.0
        total_weight = 0.0

        # 工艺匹配 (40%)
        if criteria.processes:
            supplier_processes = set(capabilities.get("processes", []))
            required_processes = set(criteria.processes)
            if required_processes:
                match_ratio = len(supplier_processes & required_processes) / len(required_processes)
                score += match_ratio * 0.4
            total_weight += 0.4

        # 材料匹配 (30%)
        if criteria.materials:
            supplier_materials = set(capabilities.get("materials", []))
            required_materials = set(criteria.materials)
            if required_materials:
                match_ratio = len(supplier_materials & required_materials) / len(required_materials)
                score += match_ratio * 0.3
            total_weight += 0.3

        # 认证匹配 (20%)
        if criteria.certifications:
            supplier_certs = set(capabilities.get("certs", []))
            required_certs = set(criteria.certifications)
            if required_certs:
                match_ratio = len(supplier_certs & required_certs) / len(required_certs)
                score += match_ratio * 0.2
            total_weight += 0.2

        # 地区匹配 (10%)
        if criteria.region:
            if capabilities.get("province") == criteria.region:
                score += 0.1
            total_weight += 0.1

        # 归一化
        if total_weight > 0:
            return score / total_weight
        else:
            return 0.5  # 默认中等匹配

    async def get_verification_status(
        self,
        supplier_id: UUID,
    ) -> VerificationStatus:
        """获取供应商核验状态.

        返回各项核验的结果、时间、有效期。
        明确标注未核验项。

        Args:
            supplier_id: 供应商 ID

        Returns:
            VerificationStatus: 核验状态详情
        """
        async with self.db.connection() as conn:
            # 获取供应商基本信息
            result = await conn.execute(
                "SELECT id, supplier_type FROM supplier WHERE id = $1",
                [supplier_id],
            )
            supplier = await result.fetchone()
            if not supplier:
                raise ValueError(f"Supplier not found: {supplier_id}")

            # 获取所有核验记录
            result = await conn.execute(
                """
                SELECT
                    check_type,
                    result,
                    level_granted,
                    verified_at,
                    expires_at,
                    detail
                FROM supplier_verification
                WHERE supplier_id = $1
                ORDER BY verified_at DESC
                """,
                [supplier_id],
            )
            verification_rows = await result.fetchall()

        # 构建核验结果
        checks = []
        overall_level = 0
        caveats = []

        # 所有可能的核验类型
        all_check_types = [
            "business_registry",
            "phone_callback",
            "wecom_contact",
            "certificate",
            "factory_audit",
            "sample_confirmed",
            "sanctions_screening",
        ]

        # 已执行的核验
        performed_checks = {row["check_type"] for row in verification_rows}

        for check_type in all_check_types:
            if check_type in performed_checks:
                # 找到最新的核验记录
                check_row = next(r for r in verification_rows if r["check_type"] == check_type)

                checks.append({
                    "check_type": check_type,
                    "result": check_row["result"],
                    "level_granted": check_row["level_granted"],
                    "verified_at": check_row["verified_at"].isoformat() if check_row["verified_at"] else None,
                    "expires_at": check_row["expires_at"].isoformat() if check_row["expires_at"] else None,
                })

                # 更新整体等级
                if check_row["result"] == "pass" and check_row["level_granted"]:
                    overall_level = max(overall_level, check_row["level_granted"])

                # 检查是否过期
                if check_row["expires_at"] and check_row["expires_at"] < datetime.now():
                    caveats.append(f"{check_type} verification has expired")
            else:
                # 未执行的核验
                checks.append({
                    "check_type": check_type,
                    "result": "not_performed",
                })
                caveats.append(f"{check_type} not yet verified")

        return VerificationStatus(
            supplier_id=supplier_id,
            supplier_type=supplier["supplier_type"],
            overall_level=overall_level,
            checks=checks,
            caveats=caveats,
        )

    async def request_verification(
        self,
        supplier_id: UUID,
        check_type: str,
        requester_id: Optional[UUID] = None,
    ) -> VerificationTask:
        """请求人工核验.

        创建核验任务，进入运营队列。

        Args:
            supplier_id: 供应商 ID
            check_type: 核验类型
            requester_id: 请求者 ID

        Returns:
            VerificationTask: 核验任务
        """
        from uuid import uuid4

        task_id = uuid4()

        # TODO: 创建核验任务记录（需要新表）
        # 这里简化处理

        # 发布事件
        await self.event_publisher.publish(
            stream_type="supplier",
            stream_id=supplier_id,
            event_type="verification.requested",
            actor_type="agent" if requester_id else "system",
            actor_id=str(requester_id) if requester_id else None,
            payload={
                "task_id": str(task_id),
                "check_type": check_type,
                "status": "pending",
            },
        )

        logger.info(f"Verification task {task_id} created for supplier {supplier_id}, type {check_type}")

        return VerificationTask(
            task_id=task_id,
            supplier_id=supplier_id,
            check_type=check_type,
            status="pending",
            created_at=datetime.now(),
        )

    async def get_capability_matrix(
        self,
        supplier_id: UUID,
    ) -> CapabilityMatrix:
        """获取供应商能力矩阵.

        包括：
        - 工艺列表
        - 材料列表
        - 设备列表
        - 产能范围
        - 历史项目案例

        Args:
            supplier_id: 供应商 ID

        Returns:
            CapabilityMatrix: 能力矩阵
        """
        async with self.db.connection() as conn:
            result = await conn.execute(
                "SELECT capabilities FROM supplier WHERE id = $1",
                [supplier_id],
            )
            row = await result.fetchone()
            if not row:
                raise ValueError(f"Supplier not found: {supplier_id}")

        capabilities = row["capabilities"] or {}

        # TODO: 查询历史项目案例
        case_studies = []

        return CapabilityMatrix(
            supplier_id=supplier_id,
            processes=capabilities.get("processes", []),
            materials=capabilities.get("materials", []),
            equipment=capabilities.get("machines", []),
            capacity_range=capabilities.get("max_part_size_mm", {}),
            certifications=capabilities.get("certs", []),
            case_studies=case_studies,
        )
