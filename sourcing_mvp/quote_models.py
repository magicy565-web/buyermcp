"""
报价系统数据模型

真实供应商报价入口的核心模型
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field


# ============================================================================
# 报价请求 - Quote Request
# ============================================================================

class QuoteRequestStatus(str, Enum):
    """报价请求状态"""
    DRAFT = "draft"              # 草稿
    ACTIVE = "active"            # 已发送，等待报价
    RECEIVED = "received"        # 已收到报价
    EXPIRED = "expired"          # 已过期
    CANCELLED = "cancelled"      # 已取消


class QuoteRequest(BaseModel):
    """报价请求"""
    id: UUID = Field(default_factory=uuid4)
    case_id: UUID                # 关联的采购案例
    supplier_id: str             # 供应商 ID

    # 产品信息
    product_name: str
    product_description: str
    quantity: int                # 采购数量
    specifications: dict = Field(default_factory=dict)

    # 报价要求
    quote_deadline: datetime     # 报价截止时间
    currency: str = "USD"        # 期望币种

    # 状态
    status: QuoteRequestStatus = QuoteRequestStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 授权记录
    buyer_id: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


# ============================================================================
# 报价 Token - Quote Token
# ============================================================================

class QuoteToken(BaseModel):
    """报价专属访问 Token"""
    id: UUID = Field(default_factory=uuid4)
    token_hash: str              # Token 哈希值（不存储原始 token）

    # 关联信息
    quote_request_id: UUID
    supplier_id: str

    # 有效期和状态
    expires_at: datetime
    is_revoked: bool = False
    revoked_at: Optional[datetime] = None

    # 访问控制
    access_count: int = 0        # 访问次数
    last_accessed_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# 供应商报价 - Supplier Quote
# ============================================================================

class TradeTerm(str, Enum):
    """贸易条款"""
    FOB = "FOB"
    CIF = "CIF"
    EXW = "EXW"
    DDP = "DDP"
    OTHER = "OTHER"


class QuoteStatus(str, Enum):
    """报价状态"""
    SUBMITTED = "submitted"      # 已提交
    UPDATED = "updated"          # 已更新
    EXPIRED = "expired"          # 已过期
    WITHDRAWN = "withdrawn"      # 已撤回


class SupplierQuote(BaseModel):
    """供应商报价记录"""
    id: UUID = Field(default_factory=uuid4)
    quote_request_id: UUID
    supplier_id: str
    version: int = 1             # 报价版本号

    # 报价内容
    unit_price: float
    currency: str
    moq: int                     # 最小起订量
    lead_time_days: int          # 交货期（天）
    trade_term: TradeTerm

    # 额外信息
    quote_valid_until: datetime  # 报价有效期
    payment_terms: Optional[str] = None
    specification_notes: Optional[str] = None  # 规格差异说明

    # 元数据
    status: QuoteStatus = QuoteStatus.SUBMITTED
    submitted_at: datetime = Field(default_factory=datetime.now)
    submitted_via: str = "quote_portal"  # 提交渠道

    # 原始数据（用于审计）
    raw_data: dict = Field(default_factory=dict)


# ============================================================================
# 报价版本历史 - Quote Version History
# ============================================================================

class QuoteVersion(BaseModel):
    """报价版本历史（不可变记录）"""
    id: UUID = Field(default_factory=uuid4)
    quote_id: UUID
    version: int

    # 完整报价快照
    snapshot: dict

    # 变更记录
    changed_fields: list[str] = Field(default_factory=list)
    change_reason: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# MCP 工具输入输出
# ============================================================================

class CreateQuoteRequestInput(BaseModel):
    """创建报价请求输入"""
    case_id: UUID
    supplier_id: str
    product_name: str
    product_description: str
    quantity: int
    specifications: dict = Field(default_factory=dict)
    quote_deadline_hours: int = 72  # 默认72小时


class CreateQuoteRequestOutput(BaseModel):
    """创建报价请求输出"""
    quote_request_id: UUID
    quote_link: str              # 专属报价链接
    expires_at: datetime
    message: str


class GetQuotesInput(BaseModel):
    """查询报价输入"""
    case_id: Optional[UUID] = None
    quote_request_id: Optional[UUID] = None


class GetQuotesOutput(BaseModel):
    """查询报价输出"""
    quotes: list[dict]
    summary: str
    has_valid_quotes: bool
