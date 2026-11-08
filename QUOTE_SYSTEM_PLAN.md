# 真实供应商报价入口 v0.1 - 开发计划

## 当前进度

✅ **Step 0: 基础修复和数据模型（已完成）**
- 修复 `update_supplier()` 缺失
- 设计报价数据模型
- 扩展数据库 schema
- 实现报价 CRUD 操作

**Commit**: c627eae - "Add quote system foundation: models, database schema and CRUD"

---

## 剩余开发任务

### Step 1: FastAPI 报价提交服务

**文件**：
- `sourcing_mvp/quote_api.py` - FastAPI 应用
- `sourcing_mvp/quote_service.py` - 业务逻辑层
- `sourcing_mvp/requirements.txt` - 添加 FastAPI, uvicorn

**核心功能**：
1. `POST /api/quote/create` - 创建报价请求（内部接口）
2. `GET /q/{token}` - 获取报价表单页面
3. `POST /api/quote/submit` - 提交报价
4. `GET /api/quote/verify/{token}` - 验证 Token 有效性

**安全要求**：
- Token 验证（哈希匹配、过期检查、撤销检查）
- 访问次数限制（防止爬虫）
- 表单数据验证（价格、MOQ、日期格式）
- CORS 配置（仅允许授权域名）

### Step 2: 移动端报价表单

**文件**：
- `sourcing_mvp/static/quote_form.html` - 响应式表单
- `sourcing_mvp/static/quote_form.js` - 表单交互
- `sourcing_mvp/static/quote_form.css` - 移动端样式

**功能要求**：
- 中英文切换
- 移动端优化（触摸友好、大按钮）
- 字段验证（实时反馈）
- 提交确认和成功提示
- Token 过期提示

**字段**：
- 单价（必填，数字验证）
- 币种（下拉选择：USD, EUR, CNY）
- MOQ（必填，整数验证）
- 交货期（必填，整数，天数）
- 贸易条款（下拉：FOB, CIF, EXW, DDP）
- 报价有效期（必填，日期选择器）
- 付款条件（可选，文本框）
- 规格差异说明（可选，文本域）

### Step 3: Token 生成和管理

**文件**：
- `sourcing_mvp/token_manager.py` - Token 生成和验证

**功能**：
1. 生成 256 位随机 Token
2. 计算 SHA-256 哈希存储
3. 验证 Token（哈希匹配、过期、撤销）
4. 撤销 Token
5. 记录访问次数

**安全**：
- 使用 `secrets.token_urlsafe(32)` 生成
- 不存储原始 Token
- 时间常量比较防止时序攻击

### Step 4: MCP 工具集成

**修改文件**：
- `sourcing_mvp/mcp_server.py` - 添加新工具
- `sourcing_mvp/tools/create_quote_request.py` - 创建报价请求
- `sourcing_mvp/tools/get_quotes.py` - 查询报价

**新增工具**：

1. **create_quote_request**
   - 输入：case_id, supplier_id, product_name, quantity, deadline
   - 输出：quote_request_id, quote_link, expires_at
   - 需要买手授权

2. **get_quotes**
   - 输入：case_id 或 quote_request_id
   - 输出：所有报价列表，结构化比较
   - 标记过期报价和规格差异

### Step 5: 部署配置

**文件**：
- `sourcing_mvp/deployment/run_api.sh` - 启动脚本
- `sourcing_mvp/deployment/Caddyfile` - HTTPS 配置
- `sourcing_mvp/deployment/.env.example` - 环境变量示例
- `sourcing_mvp/deployment/systemd/quote-api.service` - 系统服务

**环境变量**：
```bash
QUOTE_API_HOST=0.0.0.0
QUOTE_API_PORT=8000
DATABASE_PATH=/var/lib/sourcing/sourcing.db
ALLOWED_ORIGINS=https://yourdomain.com
TOKEN_EXPIRE_HOURS=72
```

**Caddy 配置**：
```caddy
sourcing.yourdomain.com {
    reverse_proxy localhost:8000
}
```

### Step 6: 端到端测试

**文件**：
- `sourcing_mvp/tests/test_quote_e2e.py` - 端到端测试

**测试流程**：
1. 创建采购案例
2. 创建报价请求
3. 生成报价链接
4. 模拟供应商访问链接
5. 提交报价
6. 通过 MCP 查询报价
7. 验证数据一致性

---

## 技术栈

- **后端**: FastAPI 0.109+
- **数据库**: SQLite (现有)
- **前端**: 原生 HTML/CSS/JS（无框架）
- **部署**: Uvicorn + Caddy
- **安全**: HTTPS, CORS, Token 哈希

---

## 开发时间估算

| 任务 | 预计时间 |
|------|---------|
| Step 1: FastAPI 服务 | 2-3 小时 |
| Step 2: 移动端表单 | 2-3 小时 |
| Step 3: Token 管理 | 1 小时 |
| Step 4: MCP 集成 | 1-2 小时 |
| Step 5: 部署配置 | 1 小时 |
| Step 6: 测试 | 1 小时 |
| **总计** | **8-11 小时** |

---

## 验收标准

### 技术验收

1. ✅ 在受控公网环境中可访问报价链接
2. ✅ 手机浏览器可正常填写和提交表单
3. ✅ Token 验证正确（过期、撤销、访问限制）
4. ✅ 报价数据正确存储到数据库
5. ✅ MCP 工具可查询到真实报价
6. ✅ 报价版本记录不可篡改

### 业务验收

**由授权测试联系人完成一次完整流程**：
1. 创建真实采购需求
2. 生成报价请求和链接
3. 在手机上访问链接
4. 填写并提交报价
5. 在 AI 对话中查看报价
6. 验证报价数据完整准确

---

## 下一步

请确认是否继续开发，或者需要：
1. 调整技术方案
2. 准备部署环境（域名、服务器）
3. 准备测试账号和联系人
4. 其他准备工作

**当前状态**：基础数据模型已完成并推送到 GitHub
