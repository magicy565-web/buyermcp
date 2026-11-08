"""
AI Sourcing Partner - MVP Core Models

核心概念：
- Sourcing Case（采购案例）：买手的采购意图 + 持续推进过程
- Supplier（供应商）：真实可联系的供应商
- Inquiry（询价）：发送给供应商的询价
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ============================================================================
# Sourcing Case - 采购案例（不是 RFQ）
# ============================================================================

class CaseStatus(str, Enum):
    """案例状态"""
    DISCOVERING = "discovering"      # 正在研究供应商
    INQUIRING = "inquiring"          # 已发送询价
    QUOTED = "quoted"                # 收到报价
    COMPARING = "comparing"          # 比较报价中
    DECIDED = "decided"              # 买手已决策
    CLOSED = "closed"                # 案例关闭


class SourcingCase(BaseModel):
    """采购案例 - 从一句话开始的采购过程"""
    id: UUID = Field(default_factory=uuid4)
    buyer_id: str

    # 采购意图（逐步明确）
    initial_query: str  # 买手的初始问题
    product_description: Optional[str] = None
    requirements: dict = Field(default_factory=dict)  # MOQ, budget, specs, etc.

    # 状态
    status: CaseStatus = CaseStatus.DISCOVERING

    # 发现的供应商
    discovered_suppliers: list[str] = Field(default_factory=list)  # supplier IDs

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 对话历史引用
    message_count: int = 0


# ============================================================================
# Supplier - 供应商
# ============================================================================

class SupplierContact(BaseModel):
    """供应商联系方式"""
    email: str
    wechat: Optional[str] = None
    phone: Optional[str] = None
    contact_person: Optional[str] = None


class SupplierCapabilities(BaseModel):
    """供应商能力"""
    moq_range: str  # "50-500 units"
    lead_time: str  # "20-30 days"
    certifications: list[str] = Field(default_factory=list)
    export_experience: Optional[str] = None


class SupplierVerification(BaseModel):
    """供应商核验状态"""
    business_license: bool = False
    factory_visit: bool = False
    past_orders: int = 0
    email_verified: bool = False


class Supplier(BaseModel):
    """供应商 - 真实可联系的制造商"""
    id: str  # supplier_001, supplier_002, etc.
    name: str
    contact: SupplierContact

    # 擅长品类
    categories: list[str] = Field(default_factory=list)

    # 能力
    capabilities: SupplierCapabilities

    # 核验状态
    verification: SupplierVerification = Field(default_factory=SupplierVerification)

    # 响应率（基于历史）
    response_rate: float = 0.0  # 0-1
    avg_response_time_hours: Optional[float] = None

    # 内部备注
    notes: Optional[str] = None

    # 状态
    active: bool = True


class SupplierMatch(BaseModel):
    """供应商匹配结果"""
    supplier_id: str
    supplier_name: str
    match_score: float  # 0-1
    match_reasons: list[str]  # ["擅长小家电", "MOQ 灵活"]
    caveats: list[str] = Field(default_factory=list)  # ["交期未验证"]
    confidence: str  # "high", "medium", "low"


# ============================================================================
# Inquiry - 询价
# ============================================================================

class InquiryStatus(str, Enum):
    """询价状态"""
    DRAFT = "draft"              # 草稿
    SENT = "sent"                # 已发送
    REPLIED = "replied"          # 已回复
    NO_RESPONSE = "no_response"  # 无回复
    BOUNCED = "bounced"          # 邮件退回


class InquiryResponse(BaseModel):
    """供应商回复摘要"""
    received_at: datetime

    # 提取的关键信息
    has_quote: bool = False
    fob_price: Optional[str] = None
    moq: Optional[str] = None
    lead_time: Optional[str] = None
    payment_terms: Optional[str] = None

    # 原始回复（UntrustedText）
    raw_email: str

    # 提取质量
    extraction_confidence: float = 0.0  # 0-1


class Inquiry(BaseModel):
    """询价记录"""
    id: UUID = Field(default_factory=uuid4)
    case_id: UUID
    supplier_id: str

    # 询价内容
    email_subject: str
    email_body: str
    language: str = "en"  # en, zh

    # 发送状态
    status: InquiryStatus = InquiryStatus.DRAFT
    sent_at: Optional[datetime] = None

    # 回复
    response: Optional[InquiryResponse] = None

    # 追踪
    follow_up_at: Optional[datetime] = None  # 何时自动跟进

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Message - 对话历史
# ============================================================================

class MessageRole(str, Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """对话消息"""
    id: UUID = Field(default_factory=uuid4)
    case_id: UUID
    role: MessageRole
    content: str
    created_at: datetime = Field(default_factory=datetime.now)

    # 元数据
    metadata: dict = Field(default_factory=dict)


# ============================================================================
# MCP Tool 输入输出
# ============================================================================

class DiscoverSuppliersInput(BaseModel):
    """discover_suppliers 工具输入"""
    product_description: str
    requirements: dict = Field(default_factory=dict)
    max_results: int = 5


class DiscoverSuppliersOutput(BaseModel):
    """discover_suppliers 工具输出"""
    case_id: UUID
    matches: list[SupplierMatch]
    summary: str  # AI 生成的总结


class PrepareInquiryInput(BaseModel):
    """prepare_inquiry 工具输入"""
    case_id: UUID
    supplier_id: str
    language: str = "en"  # en, zh, auto
    additional_requirements: Optional[str] = None


class PrepareInquiryOutput(BaseModel):
    """prepare_inquiry 工具输出"""
    inquiry_id: UUID
    email_subject: str
    email_body: str
    preview: str  # 预览摘要


class SendInquiryInput(BaseModel):
    """send_inquiry 工具输入"""
    inquiry_id: UUID
    confirm: bool = True  # 买手确认


class SendInquiryOutput(BaseModel):
    """send_inquiry 工具输出"""
    inquiry_id: UUID
    sent: bool
    sent_at: datetime
    tracking_info: str


class TrackResponseInput(BaseModel):
    """track_response 工具输入"""
    inquiry_id: Optional[UUID] = None
    case_id: Optional[UUID] = None  # 追踪整个案例的所有询价


class TrackResponseOutput(BaseModel):
    """track_response 工具输出"""
    inquiries: list[dict]  # 每个询价的状态
    summary: str
    has_new_responses: bool
