# 架构重构对比 - v0.1 企业级 vs MVP 产品化

**日期**: 2025-01-09  
**决策**: 废弃过度工程化的 v0.2，重新聚焦 MVP

---

## 📊 核心对比

| 维度 | v0.1-v0.2 (企业级) | MVP (产品化) |
|------|-------------------|-------------|
| **产品定位** | 企业采购管理系统 | AI Sourcing Partner |
| **核心用户** | 采购系统操作员 | 海外买手 |
| **交互方式** | 填写 RFQ 表单 | 自然语言对话 |
| **数据中心** | RFQ（询价单） | Sourcing Case（采购案例） |
| **工具数量** | 7 个（计划 15+） | 4 个（够用） |
| **服务层** | 6 个微服务 | 无（直接实现） |
| **数据库** | PG + Redis + ES + Neo4j | SQLite |
| **代码量** | ~350 KB | ~40 KB |
| **文件数** | 47 个 | 15 个 |
| **启动时间** | 需要初始化 6 个服务 | 立即运行 |
| **供应商数据** | 计划 10,000 家 | 5 家真实验证 |

---

## 🎯 产品定位转变

### 之前（错误）

**"可信采购基础设施"**

- 建设 Event Sourcing + CQRS 架构
- 9 类业务服务
- 支持 5+ 品类，10,000 家供应商
- 6 个月技术路线图
- 买手需要填写完整 RFQ 表单

**问题**：
- 过度工程化
- 技术驱动，而非产品驱动
- 没有验证商业假设
- 忽略供给侧可行性

### 现在（正确）

**"AI Sourcing Partner for Global Buyers"**

- 从买手的一句话开始
- 4 个核心工具覆盖完整流程
- 5 家真实供应商验证
- 先证明一个场景可行
- 买手不需要填表单

**优势**：
- 聚焦核心价值
- 快速验证假设
- 真实供给网络
- 产品驱动

---

## 🔧 技术架构对比

### v0.1-v0.2 架构（废弃）

```
MCP Tools (7-15 个)
    ↓
Service Layer (6 个服务)
    ↓
Data Layer (4 种数据库)
    ↓
External Integration
```

**服务**：
- Demand Service - 需求理解
- Supply Service - 供应商管理
- Matching Service - 智能匹配
- Workflow Service - 流程编排
- Quote Service - 报价管理
- Evidence Service - 证据管理

**数据库**：
- PostgreSQL - 主数据
- Redis - 缓存
- Elasticsearch - 搜索
- Neo4j - 图关系

**问题**：
- 复杂度远超需求
- 难以快速迭代
- 需要大量基础设施
- 验证成本高

### MVP 架构（当前）

```
MCP Tools (4 个)
    ↓
SQLite
    ↓
真实供应商（邮件）
```

**工具**：
1. `discover_suppliers` - 发现供应商
2. `prepare_inquiry` - 准备询价
3. `send_inquiry` - 发送询价
4. `track_response` - 追踪回复

**数据库**：
- SQLite - 够用

**优势**：
- 简单直接
- 快速迭代
- 容易部署
- 低成本验证

---

## 📝 核心概念转变

### RFQ（询价单）→ Sourcing Case（采购案例）

**之前（RFQ 中心）**：
```python
class RFQ:
    id: UUID
    project_id: UUID
    buyer_org_id: UUID
    items: list[RfqItem]  # 必须完整填写
    certifications: list[str]
    delivery: Delivery  # 必须完整
    status: RfqStatus  # 复杂状态机
    version: int
```

买手必须：
1. 创建项目
2. 填写完整 RFQ 表单
3. 校验通过
4. 提交审批
5. 等待供应商回复

**现在（Sourcing Case 中心）**：
```python
class SourcingCase:
    id: UUID
    buyer_id: str
    initial_query: str  # 一句话开始！
    product_description: Optional[str]
    requirements: dict  # 逐步补充
    status: CaseStatus  # 简单状态
    discovered_suppliers: list[str]
```

买手只需：
1. 一句话："Can you find..."
2. AI 逐步补充信息
3. 推荐供应商
4. 确认后发送
5. 追踪回复

---

## 🛠️ 工具设计对比

### v0.1 工具（7 个，计划 15+）

1. `create_rfq_draft` - 创建 RFQ 草稿
2. `validate_rfq` - 校验 RFQ
3. `match_suppliers` - 匹配供应商
4. `send_rfq` - 提交审批
5. `get_quotes` - 获取报价
6. `compare_quotes` - 比较报价
7. `get_project_status` - 项目状态

**问题**：
- 太多步骤
- 类似采购 ERP
- 买手负担重

### MVP 工具（4 个，够用）

1. `discover_suppliers` - 从意图到候选
2. `prepare_inquiry` - 生成询价邮件
3. `send_inquiry` - 发送并追踪
4. `track_response` - 检查回复

**优势**：
- 完整闭环
- 减少摩擦
- AI 承担更多

---

## 📊 数据量对比

### v0.1-v0.2

- **代码**: ~350 KB / 47 files
- **数据库表**: 19 张
- **服务**: 3/6 实现
- **文档**: 11 个 MD（150+ 页）
- **供应商**: 计划 10,000 家
- **开发时间**: 6 个月计划

### MVP

- **代码**: ~40 KB / 15 files
- **数据库表**: 4 张
- **服务**: 0（直接实现）
- **文档**: 2 个 MD（简洁）
- **供应商**: 5 家真实验证
- **开发时间**: 2 周验证

**减少**：
- 代码量: -88%
- 文件数: -68%
- 复杂度: -90%
- 验证成本: -95%

---

## 🎯 成功指标转变

### v0.1-v0.2 指标（技术指标）

- ❌ 供应商数据库大小
- ❌ MCP 工具数量
- ❌ 服务架构完整性
- ❌ 代码覆盖率
- ❌ QPS 性能

### MVP 指标（业务指标）

- ✅ **真实询价数**（每周 5+）
- ✅ **供应商回复率**（>60%）
- ✅ **报价有效性**（>80%）
- ✅ **买手满意度**（NPS > 50）
- ✅ **重复使用率**（30%）

---

## 🚀 下一步行动

### 立即可做（Week 1）

1. **验证供给侧**（最关键）
   - 找 10 家真实供应商
   - 手动发送 3-5 个询价
   - 记录回复率和质量

2. **完善 MVP**
   - 实现真实邮件发送
   - 实现邮件回复检查
   - 测试完整流程

3. **邀请测试买手**
   - 5-10 个真实买手
   - 收集反馈
   - 迭代优化

### 成功标准（2 周后）

- ✅ 5+ 真实买手试用
- ✅ 10+ 真实询价发送
- ✅ 60%+ 供应商回复
- ✅ 3+ 有效报价获得
- ✅ 买手愿意推荐

如果达到：继续第二阶段  
如果未达到：重新审视假设

---

## 💡 关键教训

### 1. 技术债务是可以接受的

**只要产品假设未验证，技术债务就是次要的。**

先证明：
- 买手愿意用
- 供应商愿意配合
- 能拿到有效报价

再考虑：
- 性能优化
- 架构升级
- 技术栈替换

### 2. 供给侧比技术更重要

**10 家真实配合的供应商 > 10,000 家数据库记录**

- 真实的回复
- 有效的报价
- 愿意合作

### 3. 产品定位决定一切

**不是采购系统，是采购伙伴**

- 买手不想填表单
- 买手想要建议
- 买手需要信任

### 4. 从最小场景开始

**一个完整闭环 > 10 个半成品功能**

杂志 → 提问 → 推荐 → 询价 → 回复

### 5. 够用就好

**SQLite > PostgreSQL + Redis + Elasticsearch**

- 直到有性能问题
- 直到数据量真的大
- 直到架构限制业务

---

## 📁 文件清单

### 废弃的文件（保留作参考）

```
sourcing_mcp/
├── services/              # 过度设计的服务层
├── server_v2.py           # 微服务架构
├── V02_SERVICE_LAYER_GUIDE.md
├── LONGTERM_ROADMAP.md
└── ARCHITECTURE_LONGTERM.md
```

### MVP 文件（当前使用）

```
sourcing_mvp/              # 新的 MVP 实现
├── models.py              # 简化的数据模型
├── database.py            # SQLite
├── mcp_server.py          # 4 个工具
├── init_data.py           # 初始化
├── tools/
│   ├── discover.py
│   ├── prepare.py
│   ├── send.py
│   └── track.py
├── data/
│   └── suppliers.json     # 5 家真实供应商
├── README.md
└── pyproject.toml
```

### 核心文档

```
PRODUCT_VISION.md          # 产品愿景（新）
ARCHITECTURE_COMPARISON.md # 本文档
README.md                  # 项目概览（更新）
```

---

## ✅ 决策总结

1. **废弃** v0.2 服务层架构
2. **保留** v0.1 的可信采购原则
3. **重新定义** 产品为 AI Sourcing Partner
4. **重新实现** MVP（4 工具 + SQLite）
5. **优先验证** 供给侧可行性
6. **聚焦指标** 真实询价和回复率

---

**架构对比版本**: v1.0  
**创建日期**: 2025-01-09  
**决策人**: Product Team  
**状态**: ✅ MVP 开发完成，待验证
