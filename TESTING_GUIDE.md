# AI Sourcing Partner - MVP 测试指南

**版本**: v0.1-mvp  
**状态**: Ready for Testing

---

## 🎯 测试目标

验证核心假设：**AI 能够比买手自己搜索更快地找到可信且可执行的采购结果。**

---

## 📋 测试前准备

### 1. 安装环境

```bash
# 安装依赖
pip install mcp pydantic

# 进入项目目录
cd sourcing_mvp

# 初始化数据库
python -m init_data
```

**预期输出**：
```
INFO - Initializing database...
INFO - ✓ Database tables created
INFO - Loading 5 suppliers...
INFO - ✓ Created supplier: Shenzhen Kafei Electronics Co., Ltd.
INFO - ✓ Created supplier: Ningbo Home Appliance Manufacturing Co.
INFO - ✓ Created supplier: Guangzhou Barista Tech Co., Ltd.
INFO - ✓ Created supplier: Dongguan Packaging Solutions Ltd.
INFO - ✓ Created supplier: Zhejiang Container Manufacturing Co.
INFO - Supplier data loaded successfully
INFO - ✓ Database initialization complete
```

### 2. 配置 Claude Desktop

编辑配置文件：
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

添加：
```json
{
  "mcpServers": {
    "sourcing-partner": {
      "command": "C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python315\\python.exe",
      "args": ["-m", "sourcing_mvp.mcp_server"],
      "cwd": "C:\\Users\\Administrator\\Downloads\\sourcing-mcp\\sourcing_mvp"
    }
  }
}
```

### 3. 重启 Claude Desktop

---

## 🧪 测试场景

### 场景 1: 便携咖啡机（完整流程）

#### Step 1: 发现供应商

**用户输入**：
```
Can you help me find a manufacturer for portable espresso makers at MOQ 100?
```

**预期结果**：
- AI 调用 `discover_suppliers` 工具
- 返回 2-3 个候选供应商
- 显示匹配分数、理由和风险提示
- Guangzhou Barista Tech 应该是高分候选

**检查点**：
- ✅ 返回了真实供应商（不是虚构的）
- ✅ 匹配理由合理
- ✅ 风险提示明确
- ✅ 创建了 Sourcing Case

#### Step 2: 准备询价

**用户输入**：
```
Prepare an inquiry for Guangzhou Barista Tech
```

**预期结果**：
- AI 调用 `prepare_inquiry` 工具
- 生成专业的英文询价邮件
- 包含产品描述、MOQ 要求
- 询问价格、交期、付款条件

**检查点**：
- ✅ 邮件内容专业
- ✅ 包含关键信息
- ✅ 语言流畅
- ✅ 创建了 Inquiry 记录

#### Step 3: 发送询价

**用户输入**：
```
Send it
```

**预期结果**：
- AI 调用 `send_inquiry` 工具
- 确认发送成功
- 设置 2 天后跟进
- 返回追踪信息

**检查点**：
- ✅ 状态更新为 "sent"
- ✅ 记录发送时间
- ✅ 设置跟进时间

**注意**：当前版本不实际发送邮件，只记录日志。

#### Step 4: 追踪回复

**用户输入**：
```
Check if there's any response
```

**预期结果**：
- AI 调用 `track_response` 工具
- 显示询价状态
- 如果有模拟回复，显示报价摘要

**检查点**：
- ✅ 显示正确的状态
- ✅ 提示等待时间
- ✅ 需要跟进时给出提示

---

### 场景 2: 包装盒（不同品类）

**用户输入**：
```
I need custom packaging boxes for my product, MOQ 1000
```

**预期结果**：
- 匹配到 Dongguan Packaging Solutions
- MOQ 要求在供应商范围内（500-5000）
- 显示 FSC 认证信息

---

### 场景 3: 食品容器（高 MOQ）

**用户输入**：
```
Looking for food-grade containers, MOQ 500
```

**预期结果**：
- 匹配到 Zhejiang Container Manufacturing
- 提示 MOQ 可能需要协商（供应商 MOQ 1000+）
- 显示 FDA 认证

---

### 场景 4: 不支持的品类

**用户输入**：
```
Can you find a furniture manufacturer?
```

**预期结果**：
- 返回 "No suitable suppliers found"
- 说明该品类暂不支持
- 建议尝试其他产品

---

## 🔍 数据验证

### 检查数据库

```bash
sqlite3 sourcing_mvp.db
```

```sql
-- 查看所有供应商
SELECT id, name, response_rate FROM supplier;

-- 查看所有案例
SELECT id, initial_query, status FROM sourcing_case;

-- 查看所有询价
SELECT id, supplier_id, status, sent_at FROM inquiry;

-- 查看对话历史
SELECT role, content FROM message ORDER BY created_at;
```

### 检查日志

服务器日志会显示：
```
INFO - Tool called: discover_suppliers
DEBUG - Extracted keywords: ['coffee'], categories: ['small_appliances', 'coffee_makers']
INFO - Found 3 suppliers for case <uuid>
INFO - Tool discover_suppliers completed successfully
```

---

## ✅ 成功标准

### 功能测试

- ✅ 所有 4 个工具都能正常调用
- ✅ 返回的供应商数据真实
- ✅ 匹配逻辑合理
- ✅ 邮件生成专业
- ✅ 数据正确保存

### 用户体验

- ✅ 对话流畅自然
- ✅ AI 能理解意图
- ✅ 结果清晰可读
- ✅ 风险提示明确
- ✅ 下一步建议有用

### 数据质量

- ✅ 不返回虚假信息
- ✅ 不确定性明确标注
- ✅ 来源可追溯
- ✅ 时间戳正确

---

## 🐛 常见问题

### Q1: MCP Server 启动失败

**症状**：Claude Desktop 显示 "MCP Server failed to start"

**解决**：
```bash
# 检查 Python 路径
python --version

# 手动测试启动
cd sourcing_mvp
python -m mcp_server
```

### Q2: 没有返回供应商

**症状**：`discover_suppliers` 返回空结果

**检查**：
```bash
# 确认供应商数据已加载
sqlite3 sourcing_mvp.db "SELECT COUNT(*) FROM supplier"
```

应该返回 5。

### Q3: 工具调用失败

**症状**：AI 说 "Tool call failed"

**检查日志**：
```bash
# 查看详细错误
python -m mcp_server 2>&1 | grep ERROR
```

---

## 📊 测试报告模板

```markdown
## 测试日期：2025-01-XX

### 测试人员：[姓名]

### 测试场景

- [ ] 场景 1: 便携咖啡机（完整流程）
- [ ] 场景 2: 包装盒
- [ ] 场景 3: 食品容器
- [ ] 场景 4: 不支持品类

### 功能验证

- [ ] discover_suppliers 正常
- [ ] prepare_inquiry 正常
- [ ] send_inquiry 正常
- [ ] track_response 正常

### 用户体验评分（1-5）

- 对话流畅度：__/5
- 结果准确性：__/5
- 信息清晰度：__/5
- 整体满意度：__/5

### 发现的问题

1. [问题描述]
2. [问题描述]

### 改进建议

1. [建议]
2. [建议]

### 总体评价

[评价内容]
```

---

## 🚀 下一步

### 测试通过后

1. **邀请真实买手**
   - 5-10 个目标用户
   - 准备引导话术
   - 收集详细反馈

2. **实现真实邮件**
   - SendGrid / Mailgun 集成
   - 邮件回复检查
   - 自动跟进

3. **验证供给侧**
   - 联系 10 家真实供应商
   - 发送测试询价
   - 记录回复率

### 迭代优化

基于反馈：
- 改进匹配算法
- 优化邮件模板
- 增加供应商数据
- 完善错误处理

---

**测试指南版本**: v1.0  
**创建日期**: 2025-01-09  
**下次更新**: 基于测试反馈
