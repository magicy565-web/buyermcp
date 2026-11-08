# Sourcing MCP v0.2 - 服务层架构实现指南

**版本**: v0.2.0  
**架构**: 微服务分层架构（Service Layer）  
**状态**: 🔄 部分实现（3/6 服务）

---

## 🎯 v0.2 架构升级

### 从 v0.1 到 v0.2 的变化

**v0.1 架构**（单体）:
```
MCP Tools → Database
```

**v0.2 架构**（服务层）:
```
MCP Tools → Service Layer → Database
           ↓
    [Demand, Supply, Matching, Workflow, Quote, Evidence]
```

---

## ✅ 已实现的服务

### 1. Demand Service（需求服务）

**文件**: `sourcing_mcp/services/demand_service.py`

**功能**:
- ✅ `parse_intent()` - 从自然语言解析采购意图
- ✅ `validate_specs()` - 校验规格完整性
- ✅ `suggest_alternatives()` - 建议可替代方案
- ✅ `estimate_market_price()` - 估算市场价格区间

**特性**:
- LLM 集成准备（占位符）
- 基于历史数据的价格估算
- 完整的验证逻辑
- 可扩展的意图解析

**使用示例**:
```python
from sourcing_mcp.services.integration import get_service

demand_service = await get_service("demand")

# 解析意图
intent = await demand_service.parse_intent(
    raw_input="需要 100 件 6061-T6 铝合金零件，交货到深圳"
)

# 校验规格
validation = await demand_service.validate_specs(
    specs=intent.specifications,
    category=intent.category
)

# 价格估算
price_range = await demand_service.estimate_market_price(
    specs=intent.specifications,
    category=intent.category
)
```

---

### 2. Supply Service（供应商服务）

**文件**: `sourcing_mcp/services/supply_service.py`

**功能**:
- ✅ `search_suppliers()` - 多维度搜索供应商
- ✅ `get_verification_status()` - 获取核验状态
- ✅ `request_verification()` - 请求人工核验
- ✅ `get_capability_matrix()` - 获取能力矩阵

**特性**:
- 多维度搜索（工艺、材料、地区、认证）
- 匹配度评分算法
- 完整的核验状态追踪
- 事件发布集成

**使用示例**:
```python
supply_service = await get_service("supply")

# 搜索供应商
from sourcing_mcp.services.supply_service import SearchCriteria, SupplierFilters

criteria = SearchCriteria(
    category="cnc_machining",
    processes=["cnc_milling"],
    materials=["6061-T6"],
    region="Guangdong"
)

filters = SupplierFilters(
    min_verification_level=2,
    max_results=10
)

suppliers = await supply_service.search_suppliers(criteria, filters)

# 获取核验状态
status = await supply_service.get_verification_status(supplier_id)

# 获取能力矩阵
matrix = await supply_service.get_capability_matrix(supplier_id)
```

---

### 3. Matching Service（匹配服务）

**文件**: `sourcing_mcp/services/matching_service.py`

**功能**:
- ✅ `match()` - 执行智能匹配（多阶段）
- ✅ `explain_match()` - 解释匹配理由
- ✅ `get_alternatives()` - 获取备选供应商

**特性**:
- 多阶段匹配算法：
  1. 硬性过滤（品类、地区、认证）
  2. 能力匹配（工艺、材料、产能）
  3. 历史表现评分
  4. 价格区间预测
- 可解释的匹配结果
- 维度化评分（工艺 30%、材料 25%、产能 20%、认证 15%、地区 10%）
- 备选方案推荐

**使用示例**:
```python
matching_service = await get_service("matching")

# 执行匹配
from sourcing_mcp.services.matching_service import Demand, MatchConstraints

demand = Demand(
    rfq_id=rfq_id,
    category="cnc_machining",
    specifications={"material": "6061-T6", "quantity": {"value": "100", "unit": "pcs"}},
    delivery={"country": "CN", "city": "Shenzhen"},
    certifications=["ISO9001"]
)

constraints = MatchConstraints(
    min_verification_level=1,
    max_results=10,
    preferred_regions=["Guangdong", "Zhejiang"]
)

result = await matching_service.match(demand, constraints)

# 解释匹配
explanation = await matching_service.explain_match(rfq_id, supplier_id)

# 获取备选
alternatives = await matching_service.get_alternatives(supplier_id, demand)
```

**匹配算法**:
```python
def _calculate_match_score(capabilities, criteria):
    score = 0.0
    
    # 工艺匹配 (40%)
    process_match = len(supplier_processes & required_processes) / len(required_processes)
    score += process_match * 0.4
    
    # 材料匹配 (30%)
    material_match = len(supplier_materials & required_materials) / len(required_materials)
    score += material_match * 0.3
    
    # 认证匹配 (20%)
    cert_match = len(supplier_certs & required_certs) / len(required_certs)
    score += cert_match * 0.2
    
    # 地区匹配 (10%)
    if supplier_region == preferred_region:
        score += 0.1
    
    return score
```

---

## ⏳ 待实现的服务

### 4. Workflow Service（工作流服务）

**职责**:
- 启动询价工作流
- 管理工作流状态
- 处理工作流事件
- 升级到人工

**计划文件**: `sourcing_mcp/services/workflow_service.py`

**关键方法**:
```python
class WorkflowService(BaseService):
    async def start_rfq_workflow(rfq_id, workflow_type)
    async def get_workflow_state(workflow_id)
    async def handle_event(workflow_id, event)
    async def escalate(workflow_id, reason)
```

---

### 5. Quote Service（报价服务）

**职责**:
- 接收供应商报价
- 核验报价
- 归一化报价
- 多维度对比

**计划文件**: `sourcing_mcp/services/quote_service.py`

**关键方法**:
```python
class QuoteService(BaseService):
    async def receive_quote(quote_data)
    async def verify_quote(quote_id)
    async def normalize_quote(quote_id, target_basis)
    async def compare_quotes(quote_ids, dimensions)
    async def negotiate(quote_id, target_terms)
```

---

### 6. Evidence Service（证据服务）

**职责**:
- 生成上传凭证
- 验证上传文件
- 提取文件元数据
- 管理访问权限

**计划文件**: `sourcing_mcp/services/evidence_service.py`

**关键方法**:
```python
class EvidenceService(BaseService):
    async def create_upload_url(metadata)
    async def verify_upload(evidence_id)
    async def extract_metadata(evidence_id)
    async def get_access_url(evidence_id, requester)
```

---

## 🏗️ 服务层基础设施

### Base Service

**文件**: `sourcing_mcp/services/__init__.py`

**组件**:
1. **BaseService** - 所有服务的基类
2. **EventPublisher** - 事件发布器
3. **ServiceRegistry** - 服务注册表

**使用**:
```python
from sourcing_mcp.services import BaseService, EventPublisher

class MyService(BaseService):
    def __init__(self):
        super().__init__()
        self.event_publisher = EventPublisher()
    
    async def initialize(self) -> None:
        # 初始化逻辑
        pass
    
    async def health_check(self) -> dict:
        return {"status": "healthy", "service": "my_service"}
```

### Service Registry

**功能**:
- 注册服务
- 获取服务
- 批量初始化
- 批量健康检查

**使用**:
```python
from sourcing_mcp.services.integration import initialize_services, get_service

# 初始化所有服务
await initialize_services()

# 获取服务
demand_service = await get_service("demand")

# 健康检查
health = await health_check_all()
# {
#   "demand": {"status": "healthy", ...},
#   "supply": {"status": "healthy", ...},
#   "matching": {"status": "healthy", ...}
# }
```

---

## 🔄 工具层集成

### 当前状态

**v0.1 工具**（直接访问数据库）:
```python
# tools/create_rfq_draft_tool.py
async def handler(args):
    async with db.transaction() as conn:
        # 直接数据库操作
        await conn.execute("INSERT INTO rfq ...")
```

**v0.2 迁移路径**（通过服务层）:
```python
# tools/create_rfq_draft_tool_v2.py
async def handler(args):
    # 使用需求服务
    demand_service = await get_service("demand")
    
    # 解析意图
    intent = await demand_service.parse_intent(args["raw_input"])
    
    # 校验规格
    validation = await demand_service.validate_specs(intent.specifications)
    
    # 然后才创建 RFQ
    async with db.transaction() as conn:
        await conn.execute("INSERT INTO rfq ...")
```

### 迁移计划

1. **阶段 1**（当前）: v0.1 工具继续工作，v0.2 服务并行存在
2. **阶段 2**: 逐步迁移工具到服务层
3. **阶段 3**: 废弃直接数据库访问，强制通过服务层

---

## 📊 架构对比

### v0.1 vs v0.2

| 维度 | v0.1 | v0.2 |
|------|------|------|
| **架构** | 单体 | 服务层 |
| **数据访问** | 工具直接访问 DB | 通过服务层 |
| **业务逻辑** | 分散在工具中 | 集中在服务中 |
| **可测试性** | 低 | 高 |
| **可扩展性** | 低 | 高 |
| **代码复用** | 低 | 高 |
| **职责分离** | 模糊 | 清晰 |

### 代码量对比

| 组件 | v0.1 | v0.2 |
|------|------|------|
| **工具层** | ~50 KB | ~50 KB（保持） |
| **服务层** | 0 | ~15 KB（3 服务）|
| **基础设施** | ~20 KB | ~25 KB |
| **总计** | ~70 KB | ~90 KB |

---

## 🚀 运行 v0.2

### 方法 1: 使用新服务器

```bash
# 运行 v0.2 服务器（带服务层）
python -m sourcing_mcp.server_v2
```

### 方法 2: 保持向后兼容

```bash
# 运行 v0.1 服务器（原版）
python -m sourcing_mcp.server
```

### 配置 Claude Desktop (v0.2)

```json
{
  "mcpServers": {
    "sourcing": {
      "command": "C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python315\\python.exe",
      "args": ["-m", "sourcing_mcp.server_v2"],
      "env": {
        "DATABASE_URL": "postgresql://postgres:password@localhost:5432/sourcing_mcp"
      }
    }
  }
}
```

### 测试服务层

```python
# test_services.py
import asyncio
from sourcing_mcp.database import db
from sourcing_mcp.services.integration import initialize_services, get_service

async def test():
    await db.connect()
    await initialize_services()
    
    # 测试 Demand Service
    demand_service = await get_service("demand")
    intent = await demand_service.parse_intent("100 件铝合金零件")
    print(f"Intent: {intent}")
    
    # 测试 Supply Service
    supply_service = await get_service("supply")
    # ... 测试代码
    
    await db.close()

asyncio.run(test())
```

---

## 📝 下一步开发

### 短期（1-2 周）

1. ✅ **完成剩余 3 个服务**
   - Workflow Service
   - Quote Service
   - Evidence Service

2. ✅ **工具层迁移**
   - 更新现有工具使用服务层
   - 保持 API 兼容性

3. ✅ **测试覆盖**
   - 服务层单元测试
   - 集成测试

### 中期（1-3 个月）

1. ✅ **缓存层**
   - Redis 集成
   - 智能缓存策略

2. ✅ **搜索增强**
   - Elasticsearch 集成
   - 全文搜索

3. ✅ **API Gateway**
   - 认证/授权
   - 限流
   - 审计日志

### 长期（3-6 个月）

1. ✅ **真正的微服务**
   - 服务拆分为独立进程
   - 消息队列（RabbitMQ/Kafka）
   - 服务发现

2. ✅ **容器化**
   - Docker 镜像
   - Kubernetes 部署
   - Helm Charts

3. ✅ **可观测性**
   - OpenTelemetry
   - Prometheus + Grafana
   - ELK Stack

---

## 🎓 学习资源

### 服务层设计模式

- **领域驱动设计 (DDD)**: 服务按业务领域划分
- **CQRS**: 读写分离（未来）
- **Event Sourcing**: 已在 v0.1 实现
- **Repository Pattern**: 数据访问抽象

### 参考代码

- `sourcing_mcp/services/demand_service.py` - 需求服务实现
- `sourcing_mcp/services/supply_service.py` - 供应商服务实现
- `sourcing_mcp/services/matching_service.py` - 匹配服务实现
- `sourcing_mcp/services/__init__.py` - 基础设施
- `sourcing_mcp/server_v2.py` - v0.2 服务器

---

## ✅ 验收标准

### v0.2 功能验收

- [x] 3 个核心服务实现
- [x] 服务注册和发现
- [x] 健康检查机制
- [x] 事件发布集成
- [ ] 6 个服务全部实现
- [ ] 工具层迁移完成
- [ ] 单元测试 >80% 覆盖

### v0.2 质量验收

- [x] 服务可独立测试
- [x] 清晰的职责分离
- [x] 可扩展的架构
- [ ] 完整的错误处理
- [ ] 性能基准测试

---

**文档版本**: v0.2.0  
**更新日期**: 2025-01-09  
**架构状态**: 🔄 部分实现（50%）
