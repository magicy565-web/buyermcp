#!/usr/bin/env python3
"""
代码自检 - 验证所有模块可以被导入
"""
import sys
import os

# 设置环境
os.environ["DATABASE_PATH"] = ":memory:"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_imports():
    """检查所有关键模块是否可以导入"""
    errors = []

    # 核心模块
    modules = [
        "sourcing_mvp.database",
        "sourcing_mvp.quote_models",
        "sourcing_mvp.token_manager",
        "sourcing_mvp.quote_service",
        "sourcing_mvp.quote_api",
        "sourcing_mvp.tools.discover",
        "sourcing_mvp.tools.prepare",
        "sourcing_mvp.tools.send",
        "sourcing_mvp.tools.track",
        "sourcing_mvp.tools.create_quote_request",
        "sourcing_mvp.tools.get_quotes",
    ]

    for module_name in modules:
        try:
            __import__(module_name)
            print(f"✅ {module_name}")
        except Exception as e:
            print(f"❌ {module_name}: {e}")
            errors.append((module_name, str(e)))

    return errors

def main():
    print("="*60)
    print("Code Self-Check - Import Validation")
    print("="*60)
    print()

    errors = check_imports()

    print()
    print("="*60)
    if errors:
        print(f"❌ {len(errors)} module(s) failed to import")
        print("="*60)
        for module, error in errors:
            print(f"\n{module}:")
            print(f"  {error}")
        return False
    else:
        print("✅ All modules import successfully")
        print("="*60)
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
