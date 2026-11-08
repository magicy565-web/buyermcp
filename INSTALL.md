# Sourcing MCP Core v0.1 - 安装与部署指南

## 系统要求

- **Python**: 3.10 或更高版本
- **PostgreSQL**: 15 或更高版本
- **操作系统**: Windows 10+, macOS 10.15+, Linux (Ubuntu 20.04+)
- **内存**: 至少 2GB RAM
- **磁盘**: 至少 1GB 可用空间

## 安装步骤

### 1. 安装 Python

确保系统已安装 Python 3.10+：

```bash
python --version
# 应输出: Python 3.10.x 或更高
```

如果未安装：
- **Windows**: 从 [python.org](https://www.python.org/downloads/) 下载安装
- **macOS**: `brew install python@3.10`
- **Linux**: `sudo apt install python3.10 python3.10-venv python3-pip`

### 2. 安装 PostgreSQL

**Windows**:
1. 下载 [PostgreSQL 安装程序](https://www.postgresql.org/download/windows/)
2. 运行安装程序，设置密码
3. 记住端口（默认 5432）

**macOS**:
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Linux**:
```bash
sudo apt install postgresql-15 postgresql-contrib
sudo systemctl start postgresql
```

**Docker** (推荐用于开发):
```bash
docker run -d \
  --name sourcing-postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=sourcing_mcp \
  -p 5432:5432 \
  postgres:15
```

### 3. 创建数据库

```bash
# 连接到 PostgreSQL
psql -U postgres

# 创建数据库
CREATE DATABASE sourcing_mcp;

# 退出
\q
```

### 4. 克隆项目（或解压）

```bash
cd C:\Users\Administrator\Downloads\sourcing-mcp
```

### 5. 创建虚拟环境（推荐）

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 6. 安装 Python 依赖

```bash
pip install -e .
```

或安装开发依赖：
```bash
pip install -e ".[dev]"
```

### 7. 初始化数据库 Schema

```bash
psql -U postgres -d sourcing_mcp -f schema.sql
```

或使用 pgAdmin / DBeaver 等图形工具执行 `schema.sql`。

### 8. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/sourcing_mcp
LOG_LEVEL=INFO
STORAGE_BACKEND=local
STORAGE_LOCAL_PATH=C:\sourcing-mcp\uploads
```

**重要**：将 `password` 替换为你的 PostgreSQL 密码。

### 9. 验证安装

运行服务器：

```bash
python -m sourcing_mcp.server
```

应该看到：
```
INFO - Starting sourcing MCP server v0.1.0
INFO - Connecting to database: localhost:5432/sourcing_mcp
INFO - Database connection pool initialized
INFO - MCP server ready
```

按 Ctrl+C 停止。

## 配置 Claude Desktop

### Windows

1. 打开文件资源管理器
2. 导航到：`%APPDATA%\Claude`
3. 创建或编辑 `claude_desktop_config.json`

### macOS

1. 打开 Finder
2. 按 `Cmd+Shift+G`
3. 输入：`~/Library/Application Support/Claude`
4. 创建或编辑 `claude_desktop_config.json`

### 配置内容

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

**如果使用虚拟环境**，指定完整路径：

```json
{
  "mcpServers": {
    "sourcing": {
      "command": "C:\\Users\\Administrator\\Downloads\\sourcing-mcp\\venv\\Scripts\\python.exe",
      "args": ["-m", "sourcing_mcp.server"],
      "env": {
        "DATABASE_URL": "postgresql://postgres:password@localhost:5432/sourcing_mcp"
      }
    }
  }
}
```

### 重启 Claude Desktop

完全退出 Claude Desktop（系统托盘），然后重新打开。

## 验证 MCP 连接

在 Claude Desktop 中输入：

```
请列出当前可用的 MCP 工具
```

应该看到：
- create_rfq_draft
- validate_rfq
- match_suppliers
- send_rfq
- get_quotes
- compare_quotes
- get_project_status

## 测试运行

```
请帮我创建一个测试询价：
- 零件：测试支架
- 材料：6061-T6
- 公差：ISO 2768-m
- 数量：100件
- 交货地：中国深圳
```

Agent 应该能够调用 `create_rfq_draft` 并返回 RFQ ID。

## 故障排除

### 问题：Python 命令找不到

**解决**：
- 确保 Python 已添加到 PATH
- Windows: 重新安装 Python，勾选 "Add Python to PATH"
- 使用完整路径：`C:\Python310\python.exe`

### 问题：psql 命令找不到

**解决**：
- 将 PostgreSQL bin 目录添加到 PATH
- Windows: `C:\Program Files\PostgreSQL\15\bin`
- 或使用 pgAdmin 图形界面

### 问题：数据库连接失败

**解决**：
1. 检查 PostgreSQL 是否运行：
   ```bash
   # Windows
   sc query postgresql-x64-15
   
   # macOS
   brew services list
   
   # Linux
   systemctl status postgresql
   ```

2. 检查端口是否正确（默认 5432）

3. 验证用户名和密码

4. 测试连接：
   ```bash
   psql -U postgres -d sourcing_mcp -c "SELECT 1"
   ```

### 问题：Claude Desktop 看不到 MCP Server

**解决**：
1. 检查配置文件路径是否正确
2. 检查 JSON 格式是否正确（使用 [jsonlint.com](https://jsonlint.com/)）
3. 查看 Claude Desktop 日志：
   - Windows: `%APPDATA%\Claude\logs`
   - macOS: `~/Library/Logs/Claude`

### 问题：MCP 工具调用失败

**解决**：
1. 检查数据库 schema 是否正确初始化
2. 查看服务器日志（如果在终端运行）
3. 检查 `.env` 文件配置

## 生产部署

### 使用 Docker

创建 `Dockerfile`：

```dockerfile
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY . .
RUN pip install --no-cache-dir .

CMD ["python", "-m", "sourcing_mcp.server"]
```

构建并运行：

```bash
docker build -t sourcing-mcp .
docker run -d \
  --name sourcing-mcp \
  -e DATABASE_URL=postgresql://user:pass@db:5432/sourcing_mcp \
  sourcing-mcp
```

### 使用 systemd (Linux)

创建 `/etc/systemd/system/sourcing-mcp.service`：

```ini
[Unit]
Description=Sourcing MCP Server
After=network.target postgresql.service

[Service]
Type=simple
User=sourcing
WorkingDirectory=/opt/sourcing-mcp
Environment="DATABASE_URL=postgresql://user:pass@localhost/sourcing_mcp"
ExecStart=/opt/sourcing-mcp/venv/bin/python -m sourcing_mcp.server
Restart=always

[Install]
WantedBy=multi-user.target
```

启动：
```bash
sudo systemctl daemon-reload
sudo systemctl enable sourcing-mcp
sudo systemctl start sourcing-mcp
```

## 下一步

- 阅读 [DEVELOPMENT.md](DEVELOPMENT.md) 了解开发指南
- 查看 [ROADMAP.md](ROADMAP.md) 了解功能路线图
- 运行测试：`pytest tests/`
