# AI Sourcing Partner - 产品愿景

**定位**: AI Sourcing Partner for Global Buyers  
**版本**: v0.1-mvp  
**状态**: 重新聚焦

---

## 我们不是什么

- ❌ **不是 Alibaba 搜索替代品** - 不做供应商黄页
- ❌ **不是采购 ERP** - 不做流程管理系统
- ❌ **不是自动化工具** - 不卖软件许可
- ❌ **不是采购管理平台** - 不让买手填表单

## 我们是什么

✅ **AI 买手伙伴** - 一个可以持续研究、筛选、联系和推进采购的 AI Partner

### 核心价值主张

**当买手提出一个采购需求时，我们能够比他自己搜索、发邮件、比较供应商更快地拿到可信且可执行的结果。**

---

## 用户体验：买手视角

### 场景 1：从杂志发现产品

买手在 Buyer Magazine 看到一个有趣的产品：

> **Portable Espresso Maker**  
> Compact design, USB-C charging, 15 bar pressure

点击 **"Find suppliers for this"** 或直接提问：

```
Can you find a manufacturer for this at MOQ 100?
```

### AI 开始工作

买手看到：

```
🔍 Researching manufacturers...

I found 3 suitable suppliers for portable espresso makers:

1. **Shenzhen Kafei Electronics** ⭐⭐⭐⭐
   - Specializes in portable coffee makers
   - MOQ: 100 units (flexible)
   - Past projects: 5 similar products exported to EU
   - ⚠️ Lead time not verified
   
2. **Ningbo Home Appliance Co.** ⭐⭐⭐
   - General small appliances manufacturer
   - MOQ: 200 units (may negotiate to 100)
   - ISO 9001, BSCI certified
   - ⚠️ No verified espresso maker experience
   
3. **Guangzhou Barista Tech** ⭐⭐⭐⭐⭐
   - Premium coffee equipment specialist
   - MOQ: 50 units
   - 3 successful EU/US buyers
   - ✅ All specs verified

Which one would you like me to contact?
Or should I look for more options?
```

### 买手决策

```
Contact Guangzhou Barista Tech
```

### AI 准备询价

```
📧 I've prepared an inquiry email:

Subject: Product inquiry - Portable Espresso Maker (MOQ 100)

Dear Guangzhou Barista Tech,

We are interested in your portable espresso maker products.
Could you please provide:
- FOB price for 100 units
- Technical specifications (pressure, battery capacity)
- Lead time and payment terms
- Available customization options

We are looking to place a trial order soon.

Best regards,
[Buyer name]

Would you like to:
- Send this now
- Edit the message
- Add more details
```

### 买手确认

```
Send it
```

### AI 追踪进度

```
✅ Email sent to Guangzhou Barista Tech
⏱️ I'll follow up in 2 business days if no response

You can:
- Track this inquiry
- Contact other suppliers
- Refine your requirements
```

### 3 天后

```
📬 New response from Guangzhou Barista Tech!

Quote Summary:
- FOB Price: $18.50/unit (MOQ 100)
- Lead time: 25 days after deposit
- Payment: 30% deposit, 70% before shipping
- Samples: $45/unit + shipping

Key points:
✅ Within your budget range
✅ MOQ matches your requirement
⚠️ Lead time longer than average (industry avg: 20 days)

What would you like to do?
- Request a sample
- Ask for better pricing
- Compare with other suppliers
- Move forward with this quote
```

---

## 产品架构：三层结构

```
┌─────────────────────────────────────────┐
│         Buyer Experience Layer          │
│  Buyer Magazine · Chat · Discoveries    │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│            Buyer Agent                  │
│  理解意图 · 调用工具 · 主动跟进 · 建议  │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Sourcing Core MCP               │
│  discover · prepare · send · track      │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│          Supply Network                 │
│  供应商数据库 · 邮件 · 飞书 · Webhook   │
└─────────────────────────────────────────┘
```

### 核心概念：Sourcing Case（不是 RFQ）

**Sourcing Case** = 一个买手的采购意图 + 持续推进的过程

- 从一句话开始："Can you find..."
- 逐步明确需求
- 追踪所有互动
- 积累采购知识

**不是** 一个需要填写完整的 RFQ 表单。

---

## MVP 范围

### 目标场景

**完整闭环**：买手从杂志发现产品 → 对话表达意图 → AI 找到供应商 → 发送询价 → 追踪回复 → 交付可执行选择

### 必须实现

1. **产品发现** ✅
   - Buyer Magazine（精选产品）
   - "Find suppliers for this" 按钮

2. **对话式采购** ✅
   - 自然语言输入
   - 意图理解
   - 渐进式补充信息

3. **供应商推荐** ✅
   - 2-5 个候选供应商
   - 匹配理由
   - 风险提示
   - 可信度标记

4. **询价协调** ✅
   - 自动生成询价邮件
   - 买手确认后发送
   - 真实邮件发送

5. **回复追踪** ✅
   - 自动追踪回复
   - 提取关键信息
   - 通知买手

### 不在 MVP 范围

- ❌ 自动议价
- ❌ 样品管理
- ❌ 订单追踪
- ❌ 供应商评分系统
- ❌ 多轮报价对比
- ❌ 复杂的工作流引擎

---

## 技术架构：极简版

### 4 个核心 MCP 工具

```python
1. discover_suppliers(product, constraints)
   → 2-5 个候选供应商 + 匹配理由 + 风险

2. prepare_inquiry(product, supplier, requirements)
   → 询价邮件草稿（中英文）

3. send_inquiry(email_draft, supplier_contact)
   → 发送确认 + 追踪 ID

4. track_response(tracking_id)
   → 回复状态 + 报价摘要
```

### 后端架构

```
sourcing_mvp/
├── api/
│   ├── main.py              # FastAPI 入口
│   └── routes/
│       ├── chat.py          # 对话 API
│       ├── suppliers.py     # 供应商 API
│       └── inquiries.py     # 询价 API
├── mcp/
│   ├── server.py            # MCP Server
│   └── tools/
│       ├── discover.py      # discover_suppliers
│       ├── prepare.py       # prepare_inquiry
│       ├── send.py          # send_inquiry
│       └── track.py         # track_response
├── services/
│   ├── supplier_search.py   # 供应商搜索逻辑
│   ├── email_service.py     # 邮件发送
│   └── llm_service.py       # Claude/GPT 集成
├── models/
│   ├── sourcing_case.py     # Sourcing Case 模型
│   ├── supplier.py          # 供应商模型
│   └── inquiry.py           # 询价模型
├── data/
│   ├── suppliers.json       # 初始供应商数据
│   └── products.json        # 产品目录
└── database.py              # SQLite
```

### 数据库设计（极简）

```sql
-- Sourcing Cases（采购案例）
CREATE TABLE sourcing_case (
  id TEXT PRIMARY KEY,
  buyer_id TEXT NOT NULL,
  product_description TEXT,
  requirements JSONB,
  status TEXT,  -- discovering, inquiring, quoted, closed
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Suppliers（供应商）
CREATE TABLE supplier (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  contact_email TEXT,
  contact_wechat TEXT,
  categories TEXT[],  -- ["small_appliances", "coffee_makers"]
  capabilities JSONB,
  response_rate REAL,  -- 0-1
  verified BOOLEAN DEFAULT false
);

-- Inquiries（询价）
CREATE TABLE inquiry (
  id TEXT PRIMARY KEY,
  case_id TEXT REFERENCES sourcing_case(id),
  supplier_id TEXT REFERENCES supplier(id),
  email_subject TEXT,
  email_body TEXT,
  sent_at TIMESTAMP,
  status TEXT,  -- sent, replied, no_response, bounced
  response_received_at TIMESTAMP,
  response_summary JSONB
);

-- Messages（对话历史）
CREATE TABLE message (
  id TEXT PRIMARY KEY,
  case_id TEXT REFERENCES sourcing_case(id),
  role TEXT,  -- user, assistant, system
  content TEXT,
  created_at TIMESTAMP
);
```

---

## 供应商数据：从真实开始

### 初始数据规模

- **目标**: 10-20 家**真实**供应商
- **品类**: 2-3 个验证品类（小家电、包装、简单五金）
- **数据来源**: 人工收集 + 验证

### 每家供应商需要

```json
{
  "id": "supplier_001",
  "name": "Shenzhen Kafei Electronics Co., Ltd.",
  "contact": {
    "email": "sales@kafei-electronics.com",
    "wechat": "kafei_export",
    "phone": "+86 755 1234 5678"
  },
  "categories": ["small_appliances", "coffee_makers", "portable_electronics"],
  "capabilities": {
    "moq_range": "50-500 units",
    "lead_time": "20-30 days",
    "certifications": ["CE", "FCC", "RoHS"],
    "export_experience": "5+ years to EU/US"
  },
  "verified": {
    "business_license": true,
    "factory_visit": false,
    "past_orders": 3
  },
  "response_rate": 0.85,
  "notes": "快速响应，MOQ 灵活，适合小批量试单"
}
```

### 验证流程

**在添加任何供应商之前**：

1. ✅ 人工验证邮箱有效
2. ✅ 发送测试邮件，确认回复
3. ✅ 记录回复时间和态度
4. ✅ 确认是否接受小批量询价

**不合格的供应商不添加**，即使他们在 Alibaba 上排名很高。

---

## 成功指标

### 不看的指标（虚荣指标）

- ❌ 供应商数据库大小
- ❌ MCP 工具数量
- ❌ 代码行数
- ❌ 技术栈复杂度

### 核心指标（北极星指标）

1. **真实询价数**
   - 目标：每周 5+ 个真实买手发起的询价
   - 证明：买手愿意提出真实需求

2. **供应商回复率**
   - 目标：>60% 在 48 小时内回复
   - 证明：供应商网络有效

3. **报价有效性**
   - 目标：>80% 的报价是完整且可执行的
   - 证明：质量大于数量

4. **买手满意度**
   - 目标：NPS > 50
   - 测量：每次交付后询问

5. **重复使用率**
   - 目标：30% 的买手发起 2+ 次询价
   - 证明：产品有价值

---

## 三阶段发展路径

### 第一阶段：发现（当前 MVP）

**目标**: 验证买手是否愿意提出真实需求

**交付**:
- ✅ Buyer Magazine（10-20 个精选产品）
- ✅ 对话式采购界面
- ✅ 供应商推荐（2-5 个候选）
- ✅ 询价邮件生成和发送
- ✅ 回复追踪

**成功标准**:
- 10+ 真实买手试用
- 20+ 真实询价发送
- 60%+ 供应商回复率
- 8/10 买手愿意推荐

### 第二阶段：对接

**目标**: 验证能否获得有效报价并促成对接

**新增功能**:
- 多轮报价比较
- 样品请求协调
- 自动跟进提醒
- 供应商画像完善

**成功标准**:
- 50+ 有效报价
- 10+ 样品发送
- 5+ 实际成交（追踪）

### 第三阶段：采购代理

**目标**: 验证买手是否愿意持续使用和付费

**新增功能**:
- 议价辅助
- 订单进度追踪
- 质检协调
- 长期采购管理

**成功标准**:
- GMV > $100K/月
- 付费转化率 > 20%
- 续费率 > 70%

---

## 技术原则：够用就好

### 用什么

- ✅ **Python 3.11+** - 主语言
- ✅ **FastAPI** - API 框架
- ✅ **SQLite** - 数据库（早期）
- ✅ **Claude API** - LLM
- ✅ **SMTP/Gmail API** - 邮件发送
- ✅ **Pydantic** - 数据验证
- ✅ **pytest** - 测试

### 不用什么（暂时）

- ❌ Redis - 不需要缓存
- ❌ Elasticsearch - 数据量太小
- ❌ Kafka - 不需要消息队列
- ❌ Kubernetes - 不需要容器编排
- ❌ 微服务 - 单体够用
- ❌ GraphQL - REST API 够用

### 保留的 v0.1 原则

- ✅ **Event Sourcing** - 所有采购活动可追溯
- ✅ **幂等性** - 避免重复发送
- ✅ **UntrustedText** - 供应商输入标记
- ✅ **审计日志** - 所有操作记录

### 技术债务是可以接受的

**只要产品假设未验证，技术债务就是次要的。**

先证明：
1. 买手愿意用
2. 供应商愿意配合
3. 能拿到有效报价

再考虑：
1. 性能优化
2. 架构升级
3. 技术栈替换

---

## 立即行动计划

### Week 1: 核心能力

**Day 1-2**: 极简 MCP Server
- 4 个工具的基本实现
- SQLite 数据库
- 基础测试

**Day 3**: 供应商数据
- 收集 10 家真实供应商
- 人工验证联系方式
- 测试邮件沟通

**Day 4-5**: Agent 集成
- Claude API 集成
- 意图理解
- 邮件生成

### Week 2: 端到端测试

**Day 1-2**: 简单前端
- 对话界面
- 供应商展示
- 询价确认

**Day 3**: 完整流程测试
- 模拟买手对话
- 真实邮件发送
- 回复处理

**Day 4-5**: 修复和优化
- Bug 修复
- 体验优化
- 准备演示

### Week 3: 真实测试

**目标**: 5-10 个真实买手试用

**准备**:
- 邀请买手
- 准备引导话术
- 收集反馈

---

## 最终目标

**不是构建最完善的采购系统，而是证明一个核心假设：**

> AI 能够比买手自己搜索更快地找到可信且可执行的采购结果。

如果这个假设成立，后续的技术升级、功能扩展、商业模式都会水到渠成。

如果这个假设不成立，再复杂的技术架构也没有意义。

---

**文档版本**: v0.1-mvp  
**创建日期**: 2025-01-09  
**下次审查**: 2 周后（基于真实反馈）
