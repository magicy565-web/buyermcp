#!/bin/bash
# Sourcing MCP Core v0.1 - Quick Start Script for Linux/macOS

set -e

echo "========================================"
echo "Sourcing MCP Core v0.1 - Quick Start"
echo "========================================"
echo ""

# Check Python
echo "[1/5] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found"
    echo "Please install Python 3.10+ first"
    exit 1
fi

PYTHON=$(which python3)
echo "Python: $PYTHON"
$PYTHON --version
echo ""

# Check dependencies
echo "[2/5] Checking dependencies..."
if ! $PYTHON -c "import sourcing_mcp" 2>/dev/null; then
    echo "Dependencies not installed. Installing now..."
    $PYTHON -m pip install -e .
fi
$PYTHON -c "import sourcing_mcp; print(f'Sourcing MCP v{sourcing_mcp.__version__} installed')"
echo ""

# Check configuration
echo "[3/5] Checking configuration..."
if [ ! -f .env ]; then
    echo "WARNING: .env file not found"
    echo "Creating from .env.example..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Please edit .env and set your DATABASE_URL"
    echo "Example: DATABASE_URL=postgresql://postgres:password@localhost:5432/sourcing_mcp"
    echo ""
    read -p "Press Enter to continue..."
fi
echo ""

# Run setup test
echo "[4/5] Running setup test..."
$PYTHON test_setup.py
echo ""

# Summary
echo "[5/5] Configuration summary..."
echo "Python: $PYTHON"
echo "Config: $(pwd)/.env"
echo "Schema: $(pwd)/schema.sql"
echo ""

echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Install PostgreSQL if not already installed"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "   brew install postgresql@15"
    echo "   brew services start postgresql@15"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "   sudo apt install postgresql-15"
    echo "   sudo systemctl start postgresql"
fi
echo ""
echo "2. Create database and run schema:"
echo "   createdb sourcing_mcp"
echo "   psql -U postgres -d sourcing_mcp -f schema.sql"
echo ""
echo "3. Edit .env file and set DATABASE_URL"
echo ""
echo "4. Configure Claude Desktop:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "   File: ~/Library/Application Support/Claude/claude_desktop_config.json"
else
    echo "   File: ~/.config/Claude/claude_desktop_config.json"
fi
echo "   Template: claude_desktop_config.example.json"
echo ""
echo "5. Restart Claude Desktop"
echo ""
echo "6. Test by asking Claude:"
echo '   "请列出当前可用的 MCP 工具"'
echo ""
echo "Documentation:"
echo "- README.md - Project overview"
echo "- INSTALL.md - Detailed installation guide"
echo "- DEVELOPMENT.md - Development guide"
echo "- ROADMAP.md - Project roadmap"
echo ""
