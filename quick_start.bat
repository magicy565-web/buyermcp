@echo off
REM Sourcing MCP Core v0.1 - Quick Start Script for Windows

echo ========================================
echo Sourcing MCP Core v0.1 - Quick Start
echo ========================================
echo.

REM Set Python path
set PYTHON=C:\Users\Administrator\AppData\Local\Programs\Python\Python315\python.exe

REM Check if Python exists
if not exist "%PYTHON%" (
    echo ERROR: Python not found at %PYTHON%
    echo Please install Python 3.10+ and update this script
    pause
    exit /b 1
)

echo [1/5] Checking Python version...
%PYTHON% --version
echo.

echo [2/5] Checking dependencies...
%PYTHON% -c "import sourcing_mcp; print(f'Sourcing MCP v{sourcing_mcp.__version__} installed')"
if errorlevel 1 (
    echo.
    echo Dependencies not installed. Installing now...
    %PYTHON% -m pip install -e .
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)
echo.

echo [3/5] Checking configuration...
if not exist .env (
    echo WARNING: .env file not found
    echo Creating from .env.example...
    copy .env.example .env
    echo.
    echo IMPORTANT: Please edit .env and set your DATABASE_URL
    echo Example: DATABASE_URL=postgresql://postgres:password@localhost:5432/sourcing_mcp
    echo.
    pause
)
echo.

echo [4/5] Running setup test...
%PYTHON% test_setup.py
if errorlevel 1 (
    echo.
    echo ERROR: Setup test failed
    echo Please check the error messages above
    pause
    exit /b 1
)
echo.

echo [5/5] Configuration summary...
echo Python: %PYTHON%
echo Config: %CD%\.env
echo Schema: %CD%\schema.sql
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo.
echo 1. Install PostgreSQL if not already installed
echo    Download: https://www.postgresql.org/download/windows/
echo.
echo 2. Create database and run schema:
echo    createdb sourcing_mcp
echo    psql -U postgres -d sourcing_mcp -f schema.sql
echo.
echo 3. Edit .env file and set DATABASE_URL
echo.
echo 4. Configure Claude Desktop:
echo    File: %%APPDATA%%\Claude\claude_desktop_config.json
echo    Template: claude_desktop_config.example.json
echo.
echo 5. Restart Claude Desktop
echo.
echo 6. Test by asking Claude:
echo    "请列出当前可用的 MCP 工具"
echo.
echo Documentation:
echo - README.md - Project overview
echo - INSTALL.md - Detailed installation guide
echo - DEVELOPMENT.md - Development guide
echo - ROADMAP.md - Project roadmap
echo.
pause
