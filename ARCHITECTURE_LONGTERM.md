# Sourcing MCP - 长期架构设计

## 设计理念

### 核心原则

1. **可信优先** - Trust First
   - 每个数据源都有可验证的来源
   - 供应商信息分级核验（L0-L4）
   - 报价必须带证据链
   - 操作审计完整可追溯

2. **Agent 友好** - Agent-Friendly
   - 工具粒度适中，职责单一
   - 返回结构化数据，带明确的不确定性标记
   - 错误信息可操作（告诉 Agent 下一步该做什么）
   - 支持流式响应（长时间操作）

3. **运营可控** - Operation Controlled
   - Agent 不能直接触达供应商
   - 关键操作需人工审批
   - 异常自动升级到人工
   - 完整的人工介入接口

4. **渐进增强** - Progressive Enhancement
   - 从简单场景开始（CNC 加工）
   - 逐步支持更多品类
   - 能力分层（从匹配到议价到履约）
   - 向后兼容

---

## 架构分层

```
┌─────────────────────────────────────────────────────────────┐
│                      Agent Layer                            │
│  (Claude, GPT-4, OpenMausBot, Custom Agents)                │
└─────────────────────────────────────────────────────────────┘
                           ↓ MCP Protocol
┌─────────────────────────────────────────────────────────────┐
│                   MCP Gateway Layer                         │
│  - Authentication (OAuth2 + API Key)                        │
│  - Rate Limiting (per agent, per org)                       │
│  - Request Validation                                       │
│  - Response Transformation                                  │
│  - Audit Logging                                            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer                             │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Demand     │  │   Supply     │  │   Matching   │     │
│  │   Service    │  │   Service    │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │     RFQ      │  │    Quote     │  │  Workflow    │     │
│  │   Service    │  │   Service    │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Verification │  │   Evidence   │  │   Payment    │     │
│  │   Service    │  │   Service    │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer                                │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  PostgreSQL  │  │    Redis     │  │  S3/MinIO    │     │
│  │ (Core Data)  │  │   (Cache)    │  │  (Evidence)  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Elasticsearch│  │   TimeSeries │  │   Message    │     │
│  │   (Search)   │  │  (Metrics)   │  │    Queue     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│               External Integration Layer                     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   企查查     │  │   天眼查     │  │   工商API    │     │
│  │ (Registry)   │  │ (Registry)   │  │  (Official)  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   企业微信   │  │    邮件      │  │    短信      │     │
│  │   (WeChat)   │  │   (Email)    │  │    (SMS)     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   汇率API    │  │   支付网关   │  │   物流API    │     │
│  │   (FX Rate)  │  │   (Payment)  │  │  (Logistics) │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心服务设计

### 1. Demand Service（需求服务）

**职责**：理解和结构化采购需求

```python
class DemandService:
    """采购需求服务"""
    
    async def parse_intent(self, raw_input: str, context: dict) -> ParsedIntent:
        """从自然语言解析采购意图"""
        # 使用 LLM 提取结构化信息
        # 返回 ParsedIntent 包含：category, specifications, constraints
        pass
    
    async def validate_specs(self, specs: dict) -> ValidationResult:
        """校验规格完整性"""
        # 返回缺失字段、模糊字段、需要澄清的问题
        pass
    
    async def suggest_alternatives(self, specs: dict) -> list[Alternative]:
        """建议可替代方案"""
        # 基于历史数据和市场情况
        pass
    
    async def estimate_market_price(self, specs: dict) -> PriceRange:
        """估算市场价格区间"""
        # 基于历史报价数据
        # 明确标注：这是估算，不是报价
        pass
```

**设计要点**：
- 不直接修改数据库，只返回建议
- 所有 LLM 调用都有 fallback
- 价格估算带置信度和数据来源

---

### 2. Supply Service（供给服务）

**职责**：管理供应商数据和能力

```python
class SupplyService:
    """供应商服务"""
    
    async def search_suppliers(
        self, 
        criteria: SearchCriteria,
        filters: SupplierFilters
    ) -> list[SupplierProfile]:
        """搜索供应商"""
        # 支持多维度搜索：工艺、材料、地区、认证
        # 返回带匹配度分数的结果
        pass
    
    async def get_verification_status(
        self, 
        supplier_id: UUID
    ) -> VerificationStatus:
        """获取供应商核验状态"""
        # 返回各项核验的结果、时间、有效期
        # 明确标注未核验项
        pass
    
    async def request_verification(
        self, 
        supplier_id: UUID,
        check_type: CheckType
    ) -> VerificationTask:
        """请求人工核验"""
        # 创建核验任务，进入运营队列
        pass
    
    async def get_capability_matrix(
        self, 
        supplier_id: UUID
    ) -> CapabilityMatrix:
        """获取供应商能力矩阵"""
        # 工艺列表、材料列表、设备列表、产能范围
        # 历史项目案例
        pass
```

**设计要点**：
- 供应商数据分层：公开信息 / 核验信息 / 敏感信息
- 联系方式只在授权后才返回
- 支持供应商自主更新（需审核）

---

### 3. Matching Service（匹配服务）

**职责**：智能匹配需求和供应

```python
class MatchingService:
    """匹配服务"""
    
    async def match(
        self, 
        demand: Demand,
        constraints: MatchConstraints
    ) -> MatchResult:
        """执行匹配"""
        # 多阶段匹配：
        # 1. 硬性过滤（品类、地区、认证）
        # 2. 能力匹配（工艺、材料、产能）
        # 3. 历史表现评分
        # 4. 价格区间预测
        pass
    
    async def explain_match(
        self, 
        demand_id: UUID,
        supplier_id: UUID
    ) -> MatchExplanation:
        """解释匹配理由"""
        # 可解释性：为什么推荐这个供应商
        # 包括：匹配维度、历史数据、风险提示
        pass
    
    async def get_alternatives(
        self, 
        supplier_id: UUID,
        demand: Demand
    ) -> list[AlternativeSupplier]:
        """获取备选供应商"""
        # 如果首选供应商不可用
        pass
```

**设计要点**：
- 匹配算法可配置（规则 / ML模型 / 混合）
- 所有推荐都可解释
- 支持负反馈学习（匹配不当的案例）

---

### 4. Workflow Service（工作流服务）

**职责**：编排复杂业务流程

```python
class WorkflowService:
    """工作流服务"""
    
    async def start_rfq_workflow(
        self, 
        rfq_id: UUID,
        workflow_type: WorkflowType
    ) -> WorkflowInstance:
        """启动询价工作流"""
        # 标准流程：创建 → 校验 → 匹配 → 审批 → 外发 → 跟进 → 收集 → 对比
        # 快速流程：跳过某些步骤
        # 定制流程：特殊行业/客户
        pass
    
    async def get_workflow_state(
        self, 
        workflow_id: UUID
    ) -> WorkflowState:
        """获取工作流状态"""
        # 当前节点、已完成节点、等待节点
        # 责任人、超时时间
        pass
    
    async def handle_event(
        self, 
        workflow_id: UUID,
        event: WorkflowEvent
    ) -> WorkflowTransition:
        """处理工作流事件"""
        # 事件驱动状态机
        # 自动触发后续步骤
        pass
    
    async def escalate(
        self, 
        workflow_id: UUID,
        reason: str
    ) -> EscalationTicket:
        """升级到人工"""
        # 工作流卡住时升级
        pass
```

**设计要点**：
- 工作流定义与执行分离
- 支持条件分支和并行
- 每个节点可重试、回滚
- 长时间操作支持暂停/恢复

---

### 5. Quote Service（报价服务）

**职责**：管理报价生命周期

```python
class QuoteService:
    """报价服务"""
    
    async def receive_quote(
        self, 
        quote_data: QuoteSubmission
    ) -> QuoteRecord:
        """接收供应商报价"""
        # 解析、校验、存储
        # 自动提取关键信息（价格、交期、MOQ）
        # 计算完整度分数
        pass
    
    async def verify_quote(
        self, 
        quote_id: UUID
    ) -> VerificationResult:
        """核验报价"""
        # 价格合理性检查（vs 历史数据）
        # 规格匹配度检查
        # 证据完整性检查
        # 可疑标记（异常低价、不完整等）
        pass
    
    async def normalize_quote(
        self, 
        quote_id: UUID,
        target_basis: NormalizationBasis
    ) -> NormalizedQuote:
        """归一化报价"""
        # 统一币种、税率、数量档
        # 计算 TCO（Total Cost of Ownership）
        # 标注不可比因素
        pass
    
    async def compare_quotes(
        self, 
        quote_ids: list[UUID],
        comparison_dimensions: list[str]
    ) -> QuoteComparison:
        """多维度对比报价"""
        # 价格、交期、品质、服务、历史表现
        # 生成决策建议
        pass
    
    async def negotiate(
        self, 
        quote_id: UUID,
        target_terms: dict
    ) -> NegotiationThread:
        """启动议价"""
        # Agent 不直接议价，创建议价任务
        # 可以给出议价策略建议
        pass
```

**设计要点**：
- 报价版本化，不可修改
- 每次修改都是新版本 + supersedes 关系
- 报价带生命周期（submitted → verified → compared → selected/rejected）
- 支持部分报价（不是所有条目都报）

---

### 6. Evidence Service（证据服务）

**职责**：管理证据文件

```python
class EvidenceService:
    """证据服务"""
    
    async def create_upload_url(
        self, 
        metadata: EvidenceMetadata
    ) -> UploadCredentials:
        """生成上传凭证"""
        # 预签名 URL + 上传要求
        # 限制文件类型、大小
        pass
    
    async def verify_upload(
        self, 
        evidence_id: UUID
    ) -> VerificationResult:
        """验证上传文件"""
        # SHA-256 校验
        # 病毒扫描
        # 格式校验（PDF、图纸等）
        pass
    
    async def extract_metadata(
        self, 
        evidence_id: UUID
    ) -> ExtractedMetadata:
        """提取文件元数据"""
        # OCR 提取文本
        # 图纸解析（尺寸、材料等）
        # 报价单解析
        pass
    
    async def generate_thumbnail(
        self, 
        evidence_id: UUID
    ) -> str:
        """生成缩略图"""
        pass
    
    async def get_access_url(
        self, 
        evidence_id: UUID,
        requester: UUID
    ) -> str:
        """获取访问链接"""
        # 权限检查
        # 时限 URL
        pass
```

**设计要点**：
- 证据不可删除，只能标记废弃
- 所有证据带水印（来源、时间）
- 敏感信息自动脱敏
- 支持证据链（A 证明 B，B 证明 C）

---

## 数据模型演进

### Event Sourcing 增强

```sql
-- 事件表增加 saga_id 支持长事务
CREATE TABLE event (
  seq bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  stream_type text NOT NULL,
  stream_id uuid NOT NULL,
  saga_id uuid,  -- 新增：关联长事务
  type text NOT NULL,
  actor_type text NOT NULL,
  actor_id text,
  payload jsonb NOT NULL,
  metadata jsonb DEFAULT '{}',  -- 新增：扩展元数据
  correlation_id uuid,  -- 新增：请求追踪
  causation_id uuid,  -- 新增：因果关系
  idempotency_key text,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  prev_hash bytea,
  hash bytea NOT NULL,
  
  -- 新增索引
  INDEX idx_event_saga (saga_id) WHERE saga_id IS NOT NULL,
  INDEX idx_event_correlation (correlation_id) WHERE correlation_id IS NOT NULL
);

-- 物化视图：当前状态
CREATE MATERIALIZED VIEW rfq_current_state AS
SELECT 
  stream_id as rfq_id,
  jsonb_object_agg(
    key, 
    value ORDER BY seq DESC
  ) FILTER (WHERE rn = 1) as state
FROM (
  SELECT 
    stream_id,
    seq,
    key,
    value,
    ROW_NUMBER() OVER (
      PARTITION BY stream_id, key 
      ORDER BY seq DESC
    ) as rn
  FROM event, 
       jsonb_each(payload)
  WHERE stream_type = 'rfq'
) t
WHERE rn = 1
GROUP BY stream_id;
```

### 时序数据

```sql
-- 供应商表现时序数据（TimescaleDB）
CREATE TABLE supplier_metrics (
  time timestamptz NOT NULL,
  supplier_id uuid NOT NULL,
  metric_type text NOT NULL,
  value numeric NOT NULL,
  dimensions jsonb DEFAULT '{}',
  PRIMARY KEY (time, supplier_id, metric_type)
);

SELECT create_hypertable('supplier_metrics', 'time');

-- 示例查询：供应商最近 30 天准时交付率
SELECT 
  supplier_id,
  AVG(value) FILTER (WHERE metric_type = 'on_time_delivery') as otd_rate
FROM supplier_metrics
WHERE time > now() - interval '30 days'
GROUP BY supplier_id;
```

### 图数据库（Neo4j）

用于复杂关系查询：

```cypher
// 供应商能力图谱
CREATE (s:Supplier {id: $supplier_id, name: $name})
CREATE (p:Process {name: 'CNC铣削'})
CREATE (m:Material {name: '6061-T6'})
CREATE (c:Certification {name: 'ISO 9001'})

CREATE (s)-[:CAN_PERFORM]->(p)
CREATE (s)-[:WORKS_WITH]->(m)
CREATE (s)-[:HAS_CERT]->(c)

// 查询：能做 CNC + 用 6061-T6 + 有 ISO 9001 的供应商
MATCH (s:Supplier)-[:CAN_PERFORM]->(:Process {name: 'CNC铣削'})
MATCH (s)-[:WORKS_WITH]->(:Material {name: '6061-T6'})
MATCH (s)-[:HAS_CERT]->(:Certification {name: 'ISO 9001'})
RETURN s
```

---

## MCP 工具演进

### 工具分层

**L1 - 基础工具**（v0.1 已实现）
- create_rfq_draft
- validate_rfq
- match_suppliers
- send_rfq
- get_quotes
- compare_quotes
- get_project_status

**L2 - 增强工具**（v0.2-v0.3）
- `refine_demand` - 需求细化（Agent 与用户多轮对话）
- `verify_supplier_deep` - 深度供应商调查
- `request_sample` - 样品请求
- `track_delivery` - 物流跟踪
- `record_acceptance` - 验收记录
- `rate_supplier` - 供应商评价

**L3 - 智能工具**（v0.4-v0.5）
- `suggest_optimization` - 采购方案优化建议
- `predict_lead_time` - 交期预测（基于历史数据）
- `detect_risk` - 风险检测（供应商异常、价格异常）
- `recommend_alternatives` - 备选方案推荐
- `generate_report` - 采购报告生成

**L4 - 协同工具**（v0.6+）
- `multi_agent_negotiation` - 多 Agent 协同议价
- `supplier_agent_chat` - 与供应商 Agent 对接
- `cross_project_learning` - 跨项目学习
- `market_intelligence` - 市场情报

### 工具设计模式

#### 1. 长时间操作 - Async Pattern

```python
# 工具返回 task_id，Agent 可轮询
{
  "name": "send_rfq_async",
  "inputSchema": {
    "type": "object",
    "properties": {
      "rfq_id": {"type": "string"},
      "supplier_ids": {"type": "array"},
      "webhook_url": {"type": "string"}  # 可选：完成后回调
    }
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "task_id": {"type": "string"},
      "status": {"const": "processing"},
      "estimated_completion": {"type": "string"}
    }
  }
}

# 查询任务状态
{
  "name": "get_task_status",
  "inputSchema": {
    "properties": {
      "task_id": {"type": "string"}
    }
  },
  "outputSchema": {
    "properties": {
      "status": {"enum": ["processing", "completed", "failed"]},
      "progress": {"type": "number"},
      "result": {"type": "object"}  # status = completed 时
    }
  }
}
```

#### 2. 流式响应 - Streaming Pattern

```python
# 大量数据分批返回
{
  "name": "list_historical_quotes",
  "inputSchema": {
    "properties": {
      "filters": {"type": "object"},
      "limit": {"type": "integer", "default": 100},
      "cursor": {"type": "string"}  # 分页游标
    }
  },
  "outputSchema": {
    "properties": {
      "quotes": {"type": "array"},
      "next_cursor": {"type": "string"},
      "has_more": {"type": "boolean"}
    }
  }
}
```

#### 3. 批量操作 - Batch Pattern

```python
{
  "name": "validate_rfqs_batch",
  "inputSchema": {
    "properties": {
      "rfq_ids": {
        "type": "array",
        "maxItems": 100
      }
    }
  },
  "outputSchema": {
    "properties": {
      "results": {
        "type": "array",
        "items": {
          "properties": {
            "rfq_id": {"type": "string"},
            "status": {"type": "string"},
            "issues": {"type": "array"}
          }
        }
      }
    }
  }
}
```

#### 4. 交互式工具 - Interactive Pattern

```python
# Agent 需要逐步收集信息
{
  "name": "guided_rfq_creation",
  "inputSchema": {
    "properties": {
      "session_id": {"type": "string"},
      "answers": {"type": "object"}  # 上一轮问题的答案
    }
  },
  "outputSchema": {
    "properties": {
      "session_id": {"type": "string"},
      "next_questions": {
        "type": "array",
        "items": {
          "properties": {
            "id": {"type": "string"},
            "question": {"type": "string"},
            "type": {"enum": ["text", "choice", "number"]},
            "options": {"type": "array"}
          }
        }
      },
      "is_complete": {"type": "boolean"},
      "rfq_draft": {"type": "object"}  # is_complete = true 时
    }
  }
}
```

---

## 安全与权限

### 多租户隔离

```sql
-- 租户级别隔离
CREATE TABLE tenant (
  id uuid PRIMARY KEY,
  name text NOT NULL,
  tier text NOT NULL,  -- free, pro, enterprise
  settings jsonb DEFAULT '{}',
  created_at timestamptz DEFAULT now()
);

-- 所有业务表加 tenant_id
ALTER TABLE rfq ADD COLUMN tenant_id uuid REFERENCES tenant(id);
ALTER TABLE supplier ADD COLUMN tenant_id uuid REFERENCES tenant(id);

-- RLS (Row Level Security)
ALTER TABLE rfq ENABLE ROW LEVEL SECURITY;

CREATE POLICY rfq_tenant_isolation ON rfq
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

### 细粒度权限

```sql
-- RBAC
CREATE TABLE role (
  id uuid PRIMARY KEY,
  tenant_id uuid REFERENCES tenant(id),
  name text NOT NULL,
  permissions jsonb NOT NULL,  -- {"rfq": ["create", "read"], "quote": ["read"]}
  UNIQUE (tenant_id, name)
);

CREATE TABLE user_role (
  user_id uuid REFERENCES "user"(id),
  role_id uuid REFERENCES role(id),
  PRIMARY KEY (user_id, role_id)
);

-- Agent 权限
CREATE TABLE agent_permission (
  agent_id uuid REFERENCES agent(id),
  resource_type text NOT NULL,
  actions text[] NOT NULL,
  constraints jsonb DEFAULT '{}',  -- {"max_rfq_value": 100000, "approved_suppliers_only": true}
  PRIMARY KEY (agent_id, resource_type)
);
```

### 数据脱敏

```python
class DataMasking:
    """数据脱敏"""
    
    @staticmethod
    def mask_supplier_contact(contact: SupplierContact, level: int) -> SupplierContact:
        """根据权限级别脱敏供应商联系方式"""
        if level < 2:  # 低权限
            contact.phone = contact.phone[:3] + "****" + contact.phone[-4:]
            contact.email = "***@" + contact.email.split('@')[1]
            contact.wechat_id = None
        return contact
    
    @staticmethod
    def mask_quote_details(quote: Quote, level: int) -> Quote:
        """脱敏报价细节"""
        if level < 3:  # 未授权查看精确报价
            quote.unit_price = round(quote.unit_price, -2)  # 精确到百位
            quote.supplier_note = None  # 隐藏备注
        return quote
```

---

## 可观测性

### 分布式追踪

```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

tracer = trace.get_tracer(__name__)

class RfqService:
    @tracer.start_as_current_span("create_rfq")
    async def create_rfq(self, data: dict) -> UUID:
        span = trace.get_current_span()
        span.set_attribute("rfq.category", data["category"])
        span.set_attribute("rfq.items_count", len(data["items"]))
        
        # 业务逻辑
        rfq_id = await self._save_rfq(data)
        
        span.set_attribute("rfq.id", str(rfq_id))
        return rfq_id
```

### 结构化日志

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "rfq_created",
    rfq_id=str(rfq_id),
    buyer_org_id=str(buyer_org_id),
    category=category,
    items_count=len(items),
    agent_id=str(agent_id)
)
```

### 业务指标

```python
from prometheus_client import Counter, Histogram, Gauge

# 计数器
rfq_created_total = Counter(
    'rfq_created_total',
    'Total RFQs created',
    ['category', 'tenant_id']
)

# 直方图
quote_response_time = Histogram(
    'quote_response_time_seconds',
    'Time from RFQ sent to quote received',
    buckets=[3600, 86400, 259200, 604800]  # 1h, 1d, 3d, 7d
)

# 仪表盘
active_rfqs = Gauge(
    'active_rfqs',
    'Number of active RFQs',
    ['status']
)
```

---

## 部署架构

### Kubernetes 部署

```yaml
# MCP Gateway
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-gateway
  template:
    metadata:
      labels:
        app: mcp-gateway
    spec:
      containers:
      - name: gateway
        image: sourcing-mcp/gateway:v0.2
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5

---
# Service
apiVersion: v1
kind: Service
metadata:
  name: mcp-gateway
spec:
  selector:
    app: mcp-gateway
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
```

### 数据库高可用

```yaml
# PostgreSQL with Patroni
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgres-config
data:
  patroni.yml: |
    scope: sourcing-mcp
    namespace: /service/
    name: postgres-0
    
    restapi:
      listen: 0.0.0.0:8008
      connect_address: postgres-0:8008
    
    postgresql:
      listen: 0.0.0.0:5432
      connect_address: postgres-0:5432
      data_dir: /var/lib/postgresql/data
      parameters:
        max_connections: 200
        shared_buffers: 2GB
        effective_cache_size: 6GB
        work_mem: 16MB
        maintenance_work_mem: 512MB
        
    bootstrap:
      dcs:
        ttl: 30
        loop_wait: 10
        retry_timeout: 10
        maximum_lag_on_failover: 1048576
```

### 缓存层

```yaml
# Redis Cluster
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
spec:
  serviceName: redis
  replicas: 6
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
          name: client
        - containerPort: 16379
          name: gossip
        command:
        - redis-server
        - --cluster-enabled yes
        - --cluster-config-file /data/nodes.conf
        - --cluster-node-timeout 5000
        - --appendonly yes
```

---

## 成本优化

### 1. 智能缓存

```python
from functools import lru_cache
from redis import Redis
import hashlib

class SmartCache:
    """智能缓存"""
    
    def __init__(self, redis: Redis):
        self.redis = redis
    
    async def get_or_compute(
        self, 
        key: str, 
        compute_fn: callable,
        ttl: int = 3600,
        cost_threshold: float = 0.1
    ):
        """获取缓存或计算"""
        # 检查缓存
        cached = await self.redis.get(key)
        if cached:
            return cached
        
        # 计算成本估算
        estimated_cost = self._estimate_cost(compute_fn)
        
        if estimated_cost > cost_threshold:
            # 高成本操作：先检查是否有其他请求正在计算
            lock_key = f"lock:{key}"
            if not await self.redis.set(lock_key, "1", nx=True, ex=30):
                # 等待其他请求完成
                for _ in range(30):
                    cached = await self.redis.get(key)
                    if cached:
                        return cached
                    await asyncio.sleep(1)
        
        # 计算并缓存
        result = await compute_fn()
        await self.redis.setex(key, ttl, result)
        return result
```

### 2. 查询优化

```sql
-- 物化视图：常用聚合查询
CREATE MATERIALIZED VIEW supplier_performance_summary AS
SELECT 
  supplier_id,
  COUNT(*) as total_quotes,
  AVG((quote_data->>'unit_price')::numeric) as avg_unit_price,
  AVG(lead_time_days) as avg_lead_time,
  SUM(CASE WHEN selected THEN 1 ELSE 0 END)::float / COUNT(*) as win_rate
FROM quote
WHERE submitted_at > now() - interval '90 days'
GROUP BY supplier_id;

-- 定时刷新
CREATE OR REPLACE FUNCTION refresh_supplier_performance()
RETURNS void AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY supplier_performance_summary;
END;
$$ LANGUAGE plpgsql;

-- 每小时刷新
SELECT cron.schedule('refresh-supplier-perf', '0 * * * *', 'SELECT refresh_supplier_performance()');
```

### 3. 按需计算

```python
class LazyComputation:
    """延迟计算"""
    
    @staticmethod
    async def get_quote_comparison(
        rfq_id: UUID,
        detail_level: str = "summary"
    ):
        """分级返回报价对比"""
        
        if detail_level == "summary":
            # 只返回价格区间、供应商数量
            return await db.fetch_one("""
                SELECT 
                  COUNT(*) as quote_count,
                  MIN(unit_price) as min_price,
                  MAX(unit_price) as max_price
                FROM quote
                WHERE rfq_id = $1
            """, rfq_id)
        
        elif detail_level == "basic":
            # 返回每个供应商的总价
            return await db.fetch_all("""
                SELECT 
                  supplier_id,
                  SUM(unit_price * quantity) as total
                FROM quote q
                JOIN quote_line ql ON ql.quote_id = q.id
                WHERE q.rfq_id = $1
                GROUP BY supplier_id
            """, rfq_id)
        
        elif detail_level == "full":
            # 完整对比（成本最高）
            return await compare_quotes_full(rfq_id)
```

---

## AI 集成增强

### 1. Agent 能力探测

```python
class AgentCapabilityDetection:
    """检测 Agent 的能力"""
    
    async def detect_capabilities(self, agent_context: dict) -> AgentCapabilities:
        """探测 Agent 支持的功能"""
        
        capabilities = AgentCapabilities()
        
        # 检测是否支持结构化输出
        if "response_format" in agent_context:
            capabilities.structured_output = True
        
        # 检测是否支持流式
        if "streaming" in agent_context:
            capabilities.streaming = True
        
        # 检测是否支持多模态
        if "vision" in agent_context.get("models", []):
            capabilities.vision = True
        
        # 检测推理能力（通过测试问题）
        test_result = await self._test_reasoning(agent_context)
        capabilities.reasoning_level = test_result.level
        
        return capabilities
    
    async def adapt_response(
        self, 
        data: dict,
        capabilities: AgentCapabilities
    ) -> dict:
        """根据 Agent 能力调整响应"""
        
        if capabilities.structured_output:
            return data  # 返回结构化 JSON
        else:
            return {"text": self._format_as_text(data)}  # 降级为文本
```

### 2. 提示词模板

```python
PROMPTS = {
    "parse_demand": """
你是一个采购需求分析专家。请从用户的描述中提取以下结构化信息：

用户描述：
{user_input}

请提取：
1. 产品类别（category）
2. 关键规格（specifications）
   - 材料（material）
   - 尺寸（dimensions）
   - 公差要求（tolerance）
   - 表面处理（surface_finish）
3. 数量（quantity）
4. 交货要求（delivery）

如果有字段无法确定，请在 missing_fields 中列出，并生成需要向用户澄清的问题。

返回 JSON 格式：
{{
  "category": "...",
  "specifications": {{...}},
  "quantity": {{...}},
  "delivery": {{...}},
  "missing_fields": [...],
  "clarifying_questions": [...]
}}
""",
    
    "explain_match": """
请解释为什么推荐这个供应商：

供应商信息：
{supplier_profile}

需求：
{demand_specs}

历史数据：
{historical_data}

请从以下维度分析：
1. 工艺能力匹配度
2. 材料经验
3. 产能适配性
4. 历史表现
5. 潜在风险

用简洁、专业的语言回答，不超过 200 字。
"""
}
```

### 3. 多模态支持

```python
class MultiModalService:
    """多模态服务"""
    
    async def analyze_drawing(
        self, 
        image_url: str
    ) -> DrawingAnalysis:
        """分析技术图纸（图片）"""
        
        # 调用 Vision API
        analysis = await vision_api.analyze(
            image_url,
            prompt="""
            这是一个机械零件的技术图纸。请提取：
            1. 零件名称
            2. 材料标注
            3. 主要尺寸
            4. 公差标注
            5. 表面处理要求
            
            返回 JSON 格式。
            """
        )
        
        return DrawingAnalysis.parse(analysis)
    
    async def verify_evidence(
        self, 
        evidence_id: UUID
    ) -> VerificationResult:
        """验证证据文件（图片）"""
        
        evidence = await self.get_evidence(evidence_id)
        
        if evidence.kind == "quote_sheet":
            # OCR + LLM 提取报价单信息
            extracted = await self.extract_quote_from_image(evidence.url)
            
            # 与数据库中的报价对比
            stored_quote = await self.get_quote(evidence.owner_id)
            
            # 检查一致性
            consistency = self.check_consistency(extracted, stored_quote)
            
            return VerificationResult(
                verified=consistency.score > 0.9,
                confidence=consistency.score,
                details=consistency.details
            )
```

---

## 总结

### 核心设计决策

1. **Event Sourcing + CQRS**
   - 所有状态变化通过事件记录
   - 读写分离，优化查询性能
   - 完整审计追踪

2. **微服务 + DDD**
   - 按业务能力划分服务
   - 领域驱动设计
   - 服务间通过事件通信

3. **多租户 SaaS**
   - 租户级别隔离
   - 分级定价
   - 可配置工作流

4. **Agent-First API**
   - 工具粒度适中
   - 结构化输出
   - 可解释性

5. **运营可控**
   - 关键操作需审批
   - 异常自动升级
   - 人工介入接口

### 技术栈选择

**后端**：
- Python 3.11+ (主服务)
- Go (高性能网关)
- Rust (核心算法库)

**数据库**：
- PostgreSQL (主数据)
- TimescaleDB (时序数据)
- Redis (缓存)
- Elasticsearch (搜索)
- Neo4j (图关系)

**消息队列**：
- RabbitMQ (可靠消息)
- Kafka (事件流)

**部署**：
- Kubernetes
- Istio (服务网格)
- ArgoCD (GitOps)

**可观测性**：
- Prometheus + Grafana
- Jaeger (分布式追踪)
- ELK Stack (日志)

### 未来展望

**v1.0** (6 个月)
- 支持 5+ 品类
- 10000+ 供应商
- 基础自动化

**v2.0** (12 个月)
- AI 辅助议价
- 智能推荐
- 供应链优化

**v3.0** (18 个月)
- 多 Agent 协同
- 全流程自动化
- 预测性采购

---

**设计版本**: v1.0  
**更新日期**: 2025-01-09  
**负责人**: Architecture Team
