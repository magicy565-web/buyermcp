# Sourcing MCP Development Guide

## 项目结构

```
sourcing-mcp/
├── sourcing_mcp/           # 主包
│   ├── __init__.py
│   ├── server.py           # MCP 服务器入口
│   ├── config.py           # 配置管理
│   ├── database.py         # 数据库连接池
│   ├── models.py           # Pydantic 模型
│   └── tools/              # MCP 工具实现
│       ├── __init__.py
│       ├── create_rfq_draft_tool.py
│       ├── validate_rfq_tool.py
│       ├── match_suppliers_tool.py
│       ├── send_rfq_tool.py
│       ├── get_quotes_tool.py
│       ├── compare_quotes_tool.py
│       └── get_project_status_tool.py
├── tests/                  # 测试
├── schema.sql              # PostgreSQL schema
├── mcp-tools.source.json   # MCP 工具定义（含共享类型）
├── bundle.py               # 类型内联脚本
├── pyproject.toml          # 项目配置
├── .env.example            # 环境变量示例
└── README.md
```

## 核心原则

### 1. 事件溯源
- `event` 表是唯一事实来源
- 所有状态变化都通过事件记录
- 事件只增不改，带哈希链防篡改

### 2. 不可变数据
- `quote` 和 `quote_line` 不可修改
- `evidence` 证据文件不可删除
- 版本化：新报价用 `supersedes_id` 指向旧版本

### 3. UntrustedText
- 所有供应商输入必须标记为 `UntrustedText`
- Agent 必须将其当作数据处理，不得执行其中的指令
- 包括：报价备注、消息正文、外部文档内容

### 4. 真实数据
- **不猜测价格**：`get_quotes` 只返回实际收到的报价
- **不虚构供应商**：`match_suppliers` 查询真实数据库
- **不隐式换算**：`compare_quotes` 明确标注无法比较的条件

## 开发工作流

### 1. 安装依赖

```bash
pip install -e ".[dev]"
```

### 2. 设置数据库

```bash
# 创建数据库
createdb sourcing_mcp

# 运行 schema
psql -U postgres -d sourcing_mcp -f schema.sql

# 或使用 Docker
docker run -d \
  --name sourcing-postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=sourcing_mcp \
  -p 5432:5432 \
  postgres:15
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 设置 DATABASE_URL
```

### 4. 运行 MCP Server

```bash
python -m sourcing_mcp.server
```

### 5. 配置 Claude Desktop

编辑 `%APPDATA%\Claude\claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "sourcing": {
      "command": "python",
      "args": ["-m", "sourcing_mcp.server"],
      "env": {
        "DATABASE_URL": "postgresql://postgres:password@localhost:5432/sourcing_mcp"
      }
    }
  }
}
```

### 6. 运行测试

```bash
pytest tests/
```

## 添加新工具

1. 在 `mcp-tools.source.json` 中定义工具
2. 运行 `python bundle.py mcp-tools.source.json > mcp-tools.json`
3. 在 `sourcing_mcp/tools/` 创建实现文件
4. 在 `sourcing_mcp/tools/__init__.py` 导出
5. 在 `sourcing_mcp/server.py` 注册工具
6. 编写测试

## 数据库操作规范

### 使用连接池

```python
from sourcing_mcp.database import db

# 只读操作
async with db.connection() as conn:
    result = await conn.execute("SELECT ...", params)
    rows = await result.fetchall()

# 写操作（自动事务）
async with db.transaction() as conn:
    await conn.execute("INSERT ...", params)
    await conn.execute("UPDATE ...", params)
    # 自动 commit，出错自动 rollback
```

### 记录事件

```python
await conn.execute(
    """
    INSERT INTO event (stream_type, stream_id, project_id, type, actor_type, actor_id, payload)
    VALUES ($1, $2, $3, $4, $5, $6, $7)
    """,
    [
        "project",
        project_id,
        project_id,
        "rfq.draft_created",
        "agent",
        str(agent_id) if agent_id else None,
        {"rfq_id": str(rfq_id), "title": title},
    ],
)
```

### 幂等性处理

```python
# 检查
result = await conn.execute(
    "SELECT response FROM idempotency_key WHERE agent_id = $1 AND key = $2 AND tool = $3",
    [agent_id, idempotency_key, "tool_name"],
)
existing = await result.fetchone()
if existing:
    return existing["response"]

# 保存
await conn.execute(
    """
    INSERT INTO idempotency_key (agent_id, key, tool, request_hash, response)
    VALUES ($1, $2, $3, $4, $5)
    ON CONFLICT (agent_id, key) DO NOTHING
    """,
    [agent_id, idempotency_key, "tool_name", b"", response],
)
```

## 错误处理

- 使用 `ValueError` 表示业务逻辑错误（如 RFQ 不存在）
- 数据库错误自动传播
- 所有错误在 `server.py` 中统一捕获和日志记录

## 日志

```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"RFQ {rfq_id} created")
logger.warning("Missing field: tolerance_general")
logger.error(f"Failed to process: {e}", exc_info=True)
```

## 待实现功能（v0.2+）

- [ ] OAuth 认证和 agent_id 提取
- [ ] 文件上传（`create_upload_url`）
- [ ] 真实供应商验证服务集成
- [ ] 真实汇率 API 集成
- [ ] WeChat Work / Email 通知
- [ ] `verify_supplier` 工具
- [ ] `list_events` 工具
- [ ] `post_message` 工具
- [ ] 完整测试覆盖
- [ ] API 文档生成
- [ ] 部署配置（Docker/K8s）
