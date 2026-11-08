@echo off
REM Git 推送脚本 - AI Sourcing Partner MVP

echo ==================================================
echo Pushing to GitHub: buyermcp
echo ==================================================
echo.

cd /d C:\Users\Administrator\Downloads\sourcing-mcp

REM 1. 初始化 Git 仓库
echo [1/6] Initializing Git repository...
git init
echo.

REM 2. 配置 Git 凭据（使用 Personal Access Token）
echo [2/6] Configuring Git credentials...
git config user.name "magicy565-web"
git config user.email "your-email@example.com"
echo.

REM 3. 添加所有文件
echo [3/6] Adding files...
git add .
echo.

REM 4. 创建初始提交
echo [4/6] Creating initial commit...
git commit -m "Initial commit: AI Sourcing Partner MVP" -m "- Product vision: AI Sourcing Partner for Global Buyers" -m "- 4 core MCP tools: discover, prepare, send, track" -m "- SQLite database with 4 tables" -m "- 5 real verified suppliers" -m "- Complete MVP implementation (~40KB code)" -m "- Architecture comparison and testing guide" -m "" -m "Key changes from v0.1-v0.2:" -m "- Removed over-engineered service layer (6 services)" -m "- Removed complex infrastructure (Redis, ES, Neo4j)" -m "- Simplified from 350KB to 40KB (-88%%)" -m "- Changed from RFQ-centric to Sourcing Case-centric" -m "- Focus on business metrics over technical metrics"
echo.

REM 5. 设置远程仓库（使用 Token）
echo [5/6] Setting up remote repository...
git remote add origin https://<YOUR_GITHUB_TOKEN>@github.com/magicy565-web/buyermcp.git
echo.

REM 6. 推送到 GitHub
echo [6/6] Pushing to GitHub...
git branch -M main
git push -u origin main --force
echo.

echo ==================================================
echo Done!
echo ==================================================
echo.
echo Repository URL: https://github.com/magicy565-web/buyermcp
echo.
pause
