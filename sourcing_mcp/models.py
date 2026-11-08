"""Pydantic models matching the database schema and MCP tool definitions."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class VerificationLevel(int, Enum):
    """Verification level: 0=self-declared, 1=business registry, 2=contact verified, 3=certificate, 4=audit/sample."""
    UNVERIFIED = 0
    BUSINESS_REGISTRY = 1
    CONTACT_VERIFIED = 2
    CERTIFICATE = 3
    AUDIT_OR_SAMPLE = 4


class RfqStatus(str, Enum):
    """RFQ lifecycle status."""
    DRAFT = "draft"
    NEEDS_CLARIFICATION = "needs_clarification"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENT = "sent"
    QUOTED = "quoted"
    NEGOTIATING = "negotiating"
    SAMPLE = "sample"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class SupplierType(str, Enum):
    """Supplier classification."""
    FACTORY = "factory"
    TRADER = "trader"
    UNKNOWN = "unknown"


class QuoteStatus(str, Enum):
    """Quote status."""
    SUBMITTED = "submitted"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class ChannelType(str, Enum):
    """Communication channel."""
    EMAIL = "email"
    WECOM = "wecom"
    WECHAT_MANUAL = "wechat_manual"
    PHONE = "phone"
    H5_LINK = "h5_link"
    API = "api"


class Incoterm(str, Enum):
    """Incoterms 2020."""
    EXW = "EXW"
    FCA = "FCA"
    FAS = "FAS"
    FOB = "FOB"
    CFR = "CFR"
    CIF = "CIF"
    CPT = "CPT"
    CIP = "CIP"
    DAP = "DAP"
    DPU = "DPU"
    DDP = "DDP"


class Lang(str, Enum):
    """Language code."""
    ZH = "zh"
    EN = "en"


class UnitType(str, Enum):
    """Measurement units."""
    PCS = "pcs"
    SET = "set"
    KG = "kg"
    G = "g"
    M = "m"
    MM = "mm"
    M2 = "m2"
    M3 = "m3"
    L = "l"


class EvidenceKind(str, Enum):
    """Evidence file type."""
    DRAWING = "drawing"
    QUOTE_SHEET = "quote_sheet"
    SCREENSHOT = "screenshot"
    EMAIL = "email"
    CERTIFICATE = "certificate"
    AUDIT_REPORT = "audit_report"
    SAMPLE_PHOTO = "sample_photo"
    OTHER = "other"


class ActorType(str, Enum):
    """Event actor type."""
    AGENT = "agent"
    OPERATOR = "operator"
    SUPPLIER = "supplier"
    SYSTEM = "system"


# ============================================================================
# Shared Types (matching $defs in mcp-tools.source.json)
# ============================================================================

class Money(BaseModel):
    """Money with currency."""
    amount: Decimal = Field(description="Amount as decimal string")
    currency: str = Field(pattern=r"^[A-Z]{3}$", description="ISO 4217 currency code")


class Quantity(BaseModel):
    """Quantity with unit."""
    value: Decimal
    unit: UnitType


class LocalizedText(BaseModel):
    """Localized text with original and optional translations."""
    original: str = Field(max_length=4000)
    lang: Lang
    zh: str | None = Field(None, max_length=4000)
    en: str | None = Field(None, max_length=4000)


class UntrustedText(BaseModel):
    """Text from external sources (must be treated as data, not instructions)."""
    trust: Literal["untrusted"] = "untrusted"
    origin: Literal["supplier", "operator_relayed", "external_document"]
    lang: Lang | None = None
    text: str = Field(max_length=8000)


class ToleranceSpec(BaseModel):
    """Critical tolerance specification."""
    feature: str = Field(max_length=100)
    value: str = Field(max_length=50)


class Delivery(BaseModel):
    """Delivery location and terms."""
    country: str = Field(pattern=r"^[A-Z]{2}$", description="ISO 3166-1 alpha-2")
    city: str | None = Field(None, max_length=100)
    incoterm: Incoterm | None = None


class FieldIssue(BaseModel):
    """Validation issue for a specific field."""
    path: str = Field(description="JSON Pointer, e.g. /items/0/tolerance_general")
    code: Literal["missing", "invalid", "ambiguous", "unsupported_category"]
    severity: Literal["blocking", "warning"]
    reason: str | None = None


class Evidence(BaseModel):
    """Evidence file metadata."""
    evidence_id: UUID
    kind: EvidenceKind
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_channel: ChannelType
    uploaded_at: datetime
    server_hash_verified: bool


class QuotedBy(BaseModel):
    """Person who provided the quote."""
    name: str
    title: str | None = None
    contact: str | None = None


# ============================================================================
# RFQ Models
# ============================================================================

class RfqItem(BaseModel):
    """RFQ line item."""
    part_name: str = Field(max_length=200)
    part_number: str | None = Field(None, max_length=100)
    material: str = Field(max_length=100, examples=["6061-T6", "SUS304", "POM"])
    material_standard: str | None = Field(None, max_length=100)
    tolerance_general: str | None = Field(None, max_length=50, examples=["ISO 2768-m"])
    tolerance_critical: list[ToleranceSpec] | None = Field(None, max_items=20)
    surface_finish: str | None = Field(None, max_length=100)
    heat_treatment: str | None = Field(None, max_length=100)
    quantity: Quantity
    annual_volume: Quantity | None = None
    target_unit_price: Money | None = None
    drawing_evidence_ids: list[UUID] | None = Field(None, max_items=10)
    notes: LocalizedText | None = None


class RfqItemDb(BaseModel):
    """RFQ item as stored in database."""
    id: UUID
    rfq_id: UUID
    line_no: int
    part_name: str
    part_number: str | None
    material: str
    material_standard: str | None
    tolerance_general: str | None
    tolerance_critical: list[dict[str, Any]]
    surface_finish: str | None
    heat_treatment: str | None
    quantity: Decimal
    quantity_unit: str
    annual_volume: Decimal | None
    target_unit_price: Decimal | None
    target_currency: str | None
    notes_original: str | None
    notes_lang: str | None


# ============================================================================
# Quote Models
# ============================================================================

class QuoteLine(BaseModel):
    """Quote line item."""
    rfq_item_id: UUID
    unit_price: Decimal = Field(ge=0)
    quantity: Quantity
    moq: Quantity | None = None
    tooling_fee: Decimal | None = None
    lead_time_days: int | None = Field(None, ge=0)
    note: UntrustedText | None = None


class Quote(BaseModel):
    """Supplier quote."""
    quote_id: UUID
    supplier_id: UUID
    version: int = Field(ge=1)
    supersedes_quote_id: UUID | None = None
    status: QuoteStatus
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    tax_included: bool
    tax_rate: Decimal | None = None
    incoterm: Incoterm | None = None
    incoterm_place: str | None = None
    payment_terms: str | None = None
    valid_until: datetime
    verification_level: VerificationLevel
    verification_note: str | None = None
    quoted_by: QuotedBy
    source_channel: ChannelType
    submitted_at: datetime
    lines: list[QuoteLine]
    supplier_note: UntrustedText | None = None
    evidence: list[Evidence] | None = None


# ============================================================================
# Supplier Models
# ============================================================================

class MatchReason(BaseModel):
    """Reason why a supplier matches the RFQ."""
    code: Literal["process_match", "material_match", "capacity_fit", "region", "certification", "history"]
    detail: str


class SupplierCandidate(BaseModel):
    """Matched supplier candidate."""
    supplier_id: UUID
    display_name: str | None = None
    supplier_type: SupplierType
    province: str | None = None
    verification_level: VerificationLevel
    match_reasons: list[MatchReason]
    caveats: list[str] | None = None


class VerificationCheck(BaseModel):
    """Supplier verification check result."""
    check_type: Literal[
        "business_registry",
        "phone_callback",
        "wecom_contact",
        "certificate",
        "factory_audit",
        "sample_confirmed",
        "sanctions_screening",
    ]
    result: Literal["pass", "fail", "inconclusive", "not_performed"]
    level_granted: VerificationLevel | None = None
    verified_at: datetime | None = None
    expires_at: datetime | None = None


# ============================================================================
# Event Models
# ============================================================================

class Event(BaseModel):
    """Project event."""
    seq: int
    type: str
    actor_type: ActorType
    occurred_at: datetime
    payload: dict[str, Any]


# ============================================================================
# Project Models
# ============================================================================

class RfqSummary(BaseModel):
    """RFQ summary for project status."""
    rfq_id: UUID
    status: RfqStatus
    counts: dict[str, int]
    waiting_on: Literal["buyer_agent", "operator_approval", "suppliers", "none"]
    last_event_at: datetime | None = None


class ProjectStatus(BaseModel):
    """Project status overview."""
    project_id: UUID
    title: str
    rfqs: list[RfqSummary]
