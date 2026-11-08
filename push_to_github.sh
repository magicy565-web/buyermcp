#!/bin/bash
# Git 推送脚本 - AI Sourcing Partner MVP

echo "=================================================="
echo "Pushing to GitHub: buyermcp"
echo "=================================================="

# 1. 初始化 Git 仓库
echo "[1/6] Initializing Git repository..."
git init

# 2. 添加所有文件
echo "[2/6] Adding files..."
git add .

# 3. 创建初始提交
echo "[3/6] Creating initial commit..."
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

# 4. 设置远程仓库
echo "[4/6] Setting up remote repository..."
git remote add origin https://github.com/magicy565-web/buyermcp.git

# 5. 推送到 GitHub
echo "[5/6] Pushing to GitHub..."
git branch -M main
git push -u origin main --force

echo "[6/6] Done!"
echo ""
echo "Repository URL: https://github.com/magicy565-web/buyermcp"
echo "=================================================="
