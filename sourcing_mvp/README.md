# Sourcing MVP - AI Sourcing Partner

极简采购助手 MVP 实现。

## 快速启动

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

或使用 uv（推荐）：

```bash
uv pip install -e .
```

### 2. 初始化数据库

```bash
# 从项目根目录运行
python -m sourcing_mvp.init_data
```

### 3. 启动 MCP Server

```bash
# 从项目根目录运行
python -m sourcing_mvp.mcp_server
```

或配置到 Claude Desktop：

```json
{
  "mcpServers": {
    "sourcing": {
      "command": "python",
      "args": ["-m", "sourcing_mvp.mcp_server"],
      "cwd": "/path/to/sourcing-mcp"
    }
  }
}
```

## 核心工具

1. **discover_suppliers** - 发现供应商
2. **prepare_inquiry** - 准备询价邮件
3. **send_inquiry** - 发送询价（需要实现真实邮件发送）
4. **track_response** - 追踪回复（需要实现真实邮件检查）

## ⚠️ 重要提示

### 测试数据

`data/suppliers.json` 中的供应商数据**全部为测试数据**：
- 邮箱使用 `example.com` 域名
- 未经过真实验证
- `active: false` 表示不可用于生产环境
- `is_test_data: true` 标记为测试数据

### 未实现功能

以下功能当前**未实现**，会返回失败或空结果：

1. **邮件发送** (`send.py`): 返回 `False`
2. **邮件回复检查** (`track.py`): 返回 `None`

### 启动说明

所有模块启动必须从项目根目录使用 `-m` 参数：

```bash
# ✅ 正确
cd /path/to/sourcing-mcp
python -m sourcing_mvp.init_data
python -m sourcing_mvp.mcp_server

# ❌ 错误（会遇到相对导入问题）
cd sourcing_mvp
python init_data.py
python mcp_server.py
```

## 架构

```
sourcing_mvp/
├── models.py          # 数据模型
├── database.py        # SQLite 数据库
├── mcp_server.py      # MCP Server 入口
├── init_data.py       # 初始化脚本
├── tools/             # 4 个 MCP 工具
│   ├── discover.py
│   ├── prepare.py
│   ├── send.py
│   └── track.py
└── data/
    └── suppliers.json # 供应商数据（测试）
```

## 下一步

要让系统真正可用，需要：

1. 实现真实邮件发送（SendGrid/SMTP）
2. 实现真实回复检查（Gmail API/IMAP）
3. 替换测试供应商为真实已验证供应商
4. 添加买手身份验证和授权
5. 进行端到端业务测试
