# GitHub 推送指南

**仓库地址**: https://github.com/magicy565-web/buyermcp.git

---

## 🚀 方式 1: 使用推送脚本（推荐）

### Windows

```bash
# 直接双击运行
push_to_github.bat
```

或在命令行：
```bash
cd C:\Users\Administrator\Downloads\sourcing-mcp
push_to_github.bat
```

### Linux/macOS

```bash
chmod +x push_to_github.sh
./push_to_github.sh
```

---

## 📝 方式 2: 手动执行（如果脚本失败）

### Step 1: 打开命令行

```bash
cd C:\Users\Administrator\Downloads\sourcing-mcp
```

### Step 2: 初始化 Git 仓库

```bash
git init
```

### Step 3: 配置 Git 用户信息

```bash
git config user.name "magicy565-web"
git config user.email "your-email@example.com"
```

### Step 4: 添加所有文件

```bash
git add .
```

### Step 5: 创建提交

```bash
git commit -m "Initial commit: AI Sourcing Partner MVP

- Product vision: AI Sourcing Partner for Global Buyers
- 4 core MCP tools: discover, prepare, send, track
- SQLite database with 4 tables
- 5 real verified suppliers
- Complete MVP implementation (~40KB code)
- Architecture comparison and testing guide

Key changes from v0.1-v0.2:
- Removed over-engineered service layer (6 services)
- Removed complex infrastructure (Redis, ES, Neo4j)
- Simplified from 350KB to 40KB (-88%)
- Changed from RFQ-centric to Sourcing Case-centric
- Focus on business metrics over technical metrics
"
```

### Step 6: 添加远程仓库

**使用 Token（推荐）**:
```bash
git remote add origin https://<YOUR_GITHUB_TOKEN>@github.com/magicy565-web/buyermcp.git
```

**或使用 SSH**（如果已配置）:
```bash
git remote add origin git@github.com:magicy565-web/buyermcp.git
```

### Step 7: 推送到 GitHub

```bash
git branch -M main
git push -u origin main --force
```

**注意**: 使用 `--force` 会覆盖远程仓库的现有内容。

---

## ✅ 验证推送成功

### 检查本地

```bash
git status
git log --oneline
```

### 访问 GitHub

打开浏览器访问：
```
https://github.com/magicy565-web/buyermcp
```

应该看到：
- ✅ README.md 显示项目介绍
- ✅ sourcing_mvp/ 目录
- ✅ PRODUCT_VISION.md
- ✅ ARCHITECTURE_COMPARISON.md
- ✅ 其他文档

---

## 🔧 常见问题

### Q1: "remote origin already exists"

```bash
git remote remove origin
git remote add origin https://<YOUR_GITHUB_TOKEN>@github.com/magicy565-web/buyermcp.git
```

### Q2: "failed to push"

```bash
# 强制推送
git push -u origin main --force
```

### Q3: "authentication failed"

检查 Token 是否正确（用你的 GitHub Token 替换）

或使用 SSH（需要先配置 SSH key）。

### Q4: 想查看将要推送的文件

```bash
git status
git diff --cached
```

### Q5: 某些文件不想推送

编辑 `.gitignore`，然后：
```bash
git rm --cached <filename>
git commit -m "Remove unwanted file"
git push
```

---

## 📦 推送的内容

### 包含

- ✅ `sourcing_mvp/` - MVP 实现（当前使用）
- ✅ `sourcing_mcp/` - v0.1-v0.2（参考）
- ✅ `*.md` - 所有文档
- ✅ `push_to_github.*` - 推送脚本
- ✅ `.gitignore`

### 排除（在 .gitignore 中）

- ❌ `*.db` - 数据库文件
- ❌ `__pycache__/` - Python 缓存
- ❌ `.env` - 环境变量
- ❌ `*.log` - 日志文件

---

## 🎯 推送后的下一步

### 1. 添加 GitHub README 徽章

在 README.md 顶部添加：
```markdown
![Status](https://img.shields.io/badge/status-MVP-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![License](https://img.shields.io/badge/license-Proprietary-red)
```

### 2. 设置 GitHub Issues

在 GitHub 上启用 Issues，用于追踪：
- Bug 报告
- 功能请求
- 测试反馈

### 3. 添加贡献指南

创建 `CONTRIBUTING.md`（如果需要）

### 4. 保护主分支

GitHub Settings → Branches → Add rule:
- Branch name pattern: `main`
- Require pull request reviews

---

## 🔒 安全提示

### Token 已在脚本中

**重要**: 推送后，Token 会在脚本文件中可见。

**建议**：
1. 推送成功后，从 GitHub 删除或重新生成 Token
2. 使用环境变量存储 Token
3. 使用 SSH key 代替 HTTPS + Token

### 移除 Token

推送后执行：
```bash
# 编辑 push_to_github.bat，移除 Token
# 然后提交
git add push_to_github.bat
git commit -m "Remove token from script"
git push
```

---

**创建日期**: 2025-01-09  
**更新日期**: 推送成功后请删除此文件中的 Token
