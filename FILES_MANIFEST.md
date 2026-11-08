# Sourcing MCP Core v0.1 - 完整文件清单

## 📁 项目文件列表

### 核心代码 (17 files, ~70 KB)

#### Python 源文件
```
sourcing_mcp/
├── __init__.py                     # 91 bytes - 版本信息
├── server.py                       # 3,223 bytes - MCP 服务器入口
├── config.py                       # 1,763 bytes - 配置管理
├── database.py                     # 1,859 bytes - 数据库连接池
├── models.py                       # 9,499 bytes - Pydantic 模型（40+）
└── tools/
    ├── __init__.py                 # 419 bytes - 工具导出
    ├── create_rfq_draft_tool.py    # 7,784 bytes - 创建 RFQ 草稿
    ├── validate_rfq_tool.py        # 5,975 bytes - 校验 RFQ
    ├── match_suppliers_tool.py     # 5,946 bytes - 匹配供应商
    ├── send_rfq_tool.py            # 5,731 bytes - 提交审批
    ├── get_quotes_tool.py          # 7,690 bytes - 获取报价
    ├── compare_quotes_tool.py      # 9,891 bytes - 比较报价
    └── get_project_status_tool.py  # 4,124 bytes - 项目状态
```

### 数据库 (1 file, 16 KB)

```
schema.sql                          # 16,430 bytes
├── 19 张表
├── Event sourcing 架构
├── 状态机约束
├── 哈希链触发器
└── 幂等性支持
```

### 配置文件 (5 files, ~60 KB)

```
pyproject.toml                      # 1,394 bytes - Python 项目配置
.env.example                        # 1,029 bytes - 环境变量模板
.gitignore                          # ~500 bytes - Git 忽略规则
mcp-tools.source.json               # 26,647 bytes - 工具定义（源）
mcp-tools-bundled.json              # 54,547 bytes - 工具定义（打包）
claude_desktop_config.example.json  # 305 bytes - Claude 配置示例
```

### 测试文件 (3 files, ~3.5 KB)

```
tests/
├── __init__.py                     # 63 bytes
├── conftest.py                     # 824 bytes - 测试配置
└── test_create_rfq_draft.py        # 590 bytes - 单元测试示例

test_setup.py                       # 2,405 bytes - 安装验证脚本
```

### 脚本文件 (3 files, ~5 KB)

```
bundle.py                           # 1,205 bytes - 类型内联脚本
quick_start.bat                     # ~2 KB - Windows 快速开始
quick_start.sh                      # ~2 KB - Linux/macOS 快速开始
```

### 文档文件 (8 files, ~80 KB)

```
README.md                           # 3,309 bytes - 项目概览
INSTALL.md                          # 6,454 bytes - 安装指南
DEVELOPMENT.md                      # 5,275 bytes - 开发指南
ROADMAP.md                          # 3,548 bytes - 路线图
PROJECT_SUMMARY.md                  # 7,002 bytes - 项目总结
ARCHITECTURE_LONGTERM.md            # ~50 KB - 长期架构设计
DELIVERY_REPORT.md                  # ~18 KB - 交付报告
FILES_MANIFEST.md                   # 本文件
```

---

## 📊 统计汇总

### 按类型统计

| 类型 | 文件数 | 总大小 |
|------|--------|--------|
| Python 源文件 | 17 | ~70 KB |
| SQL | 1 | 16 KB |
| JSON 配置 | 3 | ~82 KB |
| TOML 配置 | 1 | 1.4 KB |
| 环境配置 | 1 | 1 KB |
| 测试文件 | 4 | ~3.5 KB |
| 脚本 | 3 | ~5 KB |
| 文档 | 8 | ~80 KB |
| **总计** | **38** | **~260 KB** |

### 按功能统计

| 功能模块 | 文件数 | 代码量 |
|----------|--------|--------|
| MCP 工具实现 | 7 | ~50 KB |
| 核心架构 | 5 | ~17 KB |
| 数据库 | 1 | 16 KB |
| 配置与部署 | 6 | ~60 KB |
| 测试 | 4 | ~3.5 KB |
| 文档 | 8 | ~80 KB |
| 工具脚本 | 3 | ~5 KB |
| **总计** | **34** | **~232 KB** |

---

## 🎯 核心交付物说明

### 1. MCP Server (sourcing_mcp/)

**用途**: 核心 MCP 服务器实现

**关键文件**:
- `server.py` - 服务器入口，工具注册
- `database.py` - 数据库连接池
- `models.py` - Pydantic 数据模型
- `config.py` - 配置管理

**依赖**:
- mcp >= 0.9.0
- psycopg[binary] >= 3.1.0
- pydantic >= 2.0.0

### 2. MCP 工具 (sourcing_mcp/tools/)

**用途**: 7 个 P0 优先级工具

**已实现**:
1. `create_rfq_draft_tool.py` - 创建询价草稿
2. `validate_rfq_tool.py` - 校验完整性
3. `match_suppliers_tool.py` - 匹配供应商
4. `send_rfq_tool.py` - 提交审批
5. `get_quotes_tool.py` - 获取报价
6. `compare_quotes_tool.py` - 比较报价
7. `get_project_status_tool.py` - 项目状态

**特性**:
- 完整的输入输出验证
- 幂等性支持
- 事件记录
- 错误处理

### 3. 数据库 Schema (schema.sql)

**用途**: PostgreSQL 数据库结构定义

**包含**:
- 19 张表
- Event sourcing 架构
- 状态机约束（RFQ 流转）
- 哈希链触发器（防篡改）
- 幂等性表
- 审计日志

**关键表**:
- `rfq` - 询价单
- `rfq_item` - 询价明细
- `quote` - 报价（不可变）
- `supplier` - 供应商
- `event` - 事件日志（哈希链）

### 4. 工具定义 (mcp-tools.*.json)

**用途**: MCP 工具的 JSON Schema 定义

**文件**:
- `mcp-tools.source.json` - 源定义（含共享类型）
- `mcp-tools-bundled.json` - 打包定义（类型内联）

**生成方式**:
```bash
python bundle.py mcp-tools.source.json > mcp-tools-bundled.json
```

### 5. 配置文件

**pyproject.toml**:
- Python 项目元数据
- 依赖声明
- 构建配置
- 工具配置（black, ruff, pytest）

**.env.example**:
- 环境变量模板
- 数据库连接
- 外部服务配置
- 功能开关

**claude_desktop_config.example.json**:
- Claude Desktop MCP 配置
- Python 路径
- 环境变量

### 6. 测试框架 (tests/)

**用途**: 单元测试和集成测试

**已有**:
- `conftest.py` - pytest 配置和 fixtures
- `test_create_rfq_draft.py` - 示例测试
- `test_setup.py` - 安装验证

**待补充**:
- 每个工具的完整测试
- E2E 测试
- 性能测试

### 7. 文档系统

**用户文档**:
- `README.md` - 快速开始
- `INSTALL.md` - 详细安装
- `ROADMAP.md` - 产品路线图

**开发文档**:
- `DEVELOPMENT.md` - 开发规范
- `ARCHITECTURE_LONGTERM.md` - 架构设计
- `PROJECT_SUMMARY.md` - 项目总结
- `DELIVERY_REPORT.md` - 交付报告

---

## 🔍 文件依赖关系

```
┌─────────────────────────────────────┐
│      Claude Desktop                 │
│  (读取 claude_desktop_config.json)  │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│     sourcing_mcp.server             │
│     (server.py)                     │
└────────────┬────────────────────────┘
             │
             ├→ config.py (读取 .env)
             ├→ database.py (连接 PostgreSQL)
             ├→ models.py (数据模型)
             └→ tools/ (7 个工具)
                  │
                  ├→ create_rfq_draft_tool.py
                  ├→ validate_rfq_tool.py
                  ├→ match_suppliers_tool.py
                  ├→ send_rfq_tool.py
                  ├→ get_quotes_tool.py
                  ├→ compare_quotes_tool.py
                  └→ get_project_status_tool.py
                       │
                       └→ database.py → schema.sql
```

---

## 📋 使用检查清单

### 开发环境设置

- [ ] Python 3.10+ 已安装
- [ ] PostgreSQL 15+ 已安装
- [ ] 克隆/解压项目到本地
- [ ] 运行 `pip install -e .`
- [ ] 运行 `python test_setup.py` 验证安装

### 数据库设置

- [ ] 创建数据库：`createdb sourcing_mcp`
- [ ] 运行 schema：`psql -U postgres -d sourcing_mcp -f schema.sql`
- [ ] 验证表创建：`psql -U postgres -d sourcing_mcp -c "\dt"`

### 配置设置

- [ ] 复制 `.env.example` 为 `.env`
- [ ] 设置 `DATABASE_URL`
- [ ] 设置其他环境变量（可选）

### Claude Desktop 集成

- [ ] 找到配置文件位置
  - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
  - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- [ ] 添加 MCP 服务器配置（参考 `claude_desktop_config.example.json`）
- [ ] 设置正确的 Python 路径
- [ ] 设置 DATABASE_URL
- [ ] 重启 Claude Desktop

### 功能验证

- [ ] 在 Claude 中询问："请列出可用的 MCP 工具"
- [ ] 应该看到 7 个工具
- [ ] 尝试创建测试询价
- [ ] 检查数据库中的数据

---

## 🚀 快速命令参考

### 安装

```bash
# Windows
quick_start.bat

# Linux/macOS
chmod +x quick_start.sh
./quick_start.sh
```

### 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/

# 代码格式化
black sourcing_mcp/
ruff check sourcing_mcp/

# 类型检查
mypy sourcing_mcp/
```

### 数据库

```bash
# 创建数据库
createdb sourcing_mcp

# 运行 schema
psql -U postgres -d sourcing_mcp -f schema.sql

# 连接数据库
psql -U postgres -d sourcing_mcp

# 查看表
\dt

# 查看事件
SELECT * FROM event ORDER BY seq DESC LIMIT 10;
```

### 运行

```bash
# 直接运行
python -m sourcing_mcp.server

# 使用环境变量
DATABASE_URL=postgresql://... python -m sourcing_mcp.server

# 查看日志
LOG_LEVEL=DEBUG python -m sourcing_mcp.server
```

---

## 📦 打包与分发

### 创建分发包

```bash
# 构建 wheel
python -m build

# 生成的文件在 dist/
# - sourcing_mcp-0.1.0-py3-none-any.whl
# - sourcing_mcp-0.1.0.tar.gz
```

### Docker 镜像（待实现）

```bash
# 构建镜像
docker build -t sourcing-mcp:v0.1.0 .

# 运行容器
docker run -d \
  --name sourcing-mcp \
  -e DATABASE_URL=postgresql://... \
  sourcing-mcp:v0.1.0
```

---

## 🔐 安全注意事项

### 敏感文件

**不要提交到版本控制**:
- `.env` - 包含真实凭证
- `*.log` - 可能包含敏感数据
- `__pycache__/` - 编译缓存
- `*.pyc` - 编译文件

**已在 .gitignore 中**:
- `.env`
- `__pycache__/`
- `*.py[cod]`
- `*.log`

### 凭证管理

- ✅ 使用环境变量，不硬编码
- ✅ `.env.example` 只包含示例
- ✅ 生产环境使用密钥管理服务
- ✅ 定期轮换数据库密码

---

## 📞 获取帮助

### 文档位置

- **快速开始**: README.md
- **详细安装**: INSTALL.md
- **开发指南**: DEVELOPMENT.md
- **路线图**: ROADMAP.md
- **架构设计**: ARCHITECTURE_LONGTERM.md
- **项目总结**: PROJECT_SUMMARY.md
- **交付报告**: DELIVERY_REPORT.md

### 常见问题

见 DELIVERY_REPORT.md 的"常见问题"章节

### 联系方式

（待补充）

---

**清单版本**: v1.0  
**更新日期**: 2025-01-09  
**文件总数**: 38  
**总大小**: ~260 KB
