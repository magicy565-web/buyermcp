"""
真实端到端测试 - 简化版

验证核心修复：
1. SQL 参数匹配
2. 时区处理
3. 数据库统一
"""
import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

# 设置测试数据库
TEST_DB = "test_e2e.db"
os.environ["DATABASE_PATH"] = TEST_DB

# 确保在项目根目录
project_root = Path(__file__).parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))

def cleanup():
    """清理测试数据库"""
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    print(f"✅ Cleaned up {TEST_DB}")

def test_database_initialization():
    """测试 1: 数据库初始化"""
    print("\n=== Test 1: Database Initialization ===")
    from sourcing_mvp.database import Database

    db = Database(TEST_DB)
    print("✅ Database initialized")

    # 验证表结构
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(supplier)")
    columns = [col[1] for col in cursor.fetchall()]

    assert "is_test_data" in columns, "is_test_data column missing"
    print(f"✅ Supplier table has {len(columns)} columns including is_test_data")

    # 验证外键
    cursor.execute("PRAGMA foreign_keys")
    fk = cursor.fetchone()[0]
    assert fk == 1, "Foreign keys not enabled"
    print("✅ Foreign keys enabled")

    conn.close()
    return db

def test_create_supplier(db):
    """测试 2: 创建供应商（验证 SQL 参数匹配）"""
    print("\n=== Test 2: Create Supplier (14 params) ===")
    from uuid import uuid4

    supplier_id = str(uuid4())
    supplier_data = {
        "id": supplier_id,
        "name": "Test Supplier Ltd",
        "contact": {
            "email": "test@supplier.com",
            "phone": "+86-13800138000",
        },
        "categories": ["electronics"],
        "active": True,
        "is_test_data": False,
    }

    # 这里会触发 SQL 参数错误如果没修复
    result_id = db.create_supplier(supplier_data)
    print(f"✅ Supplier created: {result_id}")

    # 验证写入
    supplier = db.get_supplier(supplier_id)
    assert supplier is not None, "Supplier not found"
    assert supplier["name"] == "Test Supplier Ltd"
    assert supplier["is_test_data"] == False
    print("✅ Supplier data persisted correctly")

    return supplier_id

def test_timezone_handling(db, supplier_id):
    """测试 3: 时区处理（验证 UTC 时间比较）"""
    print("\n=== Test 3: Timezone Handling ===")
    from uuid import uuid4
    from sourcing_mvp.quote_models import QuoteRequestStatus

    # 创建测试 case
    case_id = str(uuid4())
    case_data = {
        "id": case_id,
        "buyer_id": "test_buyer",
        "initial_query": "Need electronics",
        "product_description": "Test product",
        "requirements": json.dumps({}),
        "status": "active",
        "discovered_suppliers": json.dumps([]),
        "message_count": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    db.create_case(case_data)
    print(f"✅ Case created: {case_id}")

    # 创建报价请求
    request_id = str(uuid4())
    now = datetime.now(timezone.utc)
    deadline = now + timedelta(hours=72)

    request_data = {
        "id": request_id,
        "case_id": case_id,
        "supplier_id": supplier_id,
        "product_name": "Test Product",
        "product_description": "Test description",
        "quantity": 100,
        "specifications": json.dumps({}),
        "quote_deadline": deadline.isoformat(),
        "currency": "USD",
        "status": QuoteRequestStatus.ACTIVE.value,
        "buyer_id": "test_buyer",
        "approved_by": "test_buyer",
        "approved_at": now.isoformat(),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    db.create_quote_request(request_data)
    print(f"✅ Quote request created: {request_id}")

    # 创建报价（带 UTC 时间）
    quote_id = str(uuid4())
    valid_until = now + timedelta(days=30)

    quote_data = {
        "id": quote_id,
        "quote_request_id": request_id,
        "supplier_id": supplier_id,
        "version": 1,
        "unit_price": "25.50",
        "currency": "USD",
        "moq": 50,
        "lead_time_days": 20,
        "trade_term": "FOB",
        "quote_valid_until": valid_until.isoformat(),  # UTC format
        "payment_terms": "50% deposit",
        "specification_notes": None,
        "status": "submitted",
        "submitted_at": now.isoformat(),
        "submitted_via": "test",
        "raw_data": json.dumps({}),
    }

    conn = sqlite3.connect(TEST_DB)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("""
        INSERT INTO supplier_quote (
            id, quote_request_id, supplier_id, version,
            unit_price, currency, moq, lead_time_days, trade_term,
            quote_valid_until, payment_terms, specification_notes,
            status, submitted_at, submitted_via, raw_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        quote_data["id"],
        quote_data["quote_request_id"],
        quote_data["supplier_id"],
        quote_data["version"],
        quote_data["unit_price"],
        quote_data["currency"],
        quote_data["moq"],
        quote_data["lead_time_days"],
        quote_data["trade_term"],
        quote_data["quote_valid_until"],
        quote_data["payment_terms"],
        quote_data["specification_notes"],
        quote_data["status"],
        quote_data["submitted_at"],
        quote_data["submitted_via"],
        quote_data["raw_data"],
    ))
    conn.commit()
    conn.close()
    print(f"✅ Quote created with UTC timestamp: {quote_id}")

    # 验证查询（这里会触发时区错误如果没修复）
    import asyncio
    from sourcing_mvp.tools import get_quotes

    result = asyncio.run(get_quotes.get_quotes({
        "case_id": case_id,
        "buyer_id": "test_buyer",
    }))

    assert result["total_count"] == 1, f"Expected 1 quote, got {result['total_count']}"
    assert not result["quotes"][0]["is_expired"], "Quote should not be expired"
    print("✅ Timezone comparison works correctly")
    print(f"   Quote valid until: {result['quotes'][0]['quote_valid_until']}")

    return case_id, request_id

def test_unified_database():
    """测试 4: 数据库统一（验证所有工具使用同一实例）"""
    print("\n=== Test 4: Unified Database Instance ===")

    from sourcing_mvp.database import db as global_db
    from sourcing_mvp.mcp_server import db as mcp_db
    from sourcing_mvp.quote_api import db as api_db

    # 验证路径一致
    assert global_db.db_path == TEST_DB, f"global_db path mismatch: {global_db.db_path}"
    assert mcp_db.db_path == TEST_DB, f"mcp_db path mismatch: {mcp_db.db_path}"
    assert api_db.db_path == TEST_DB, f"api_db path mismatch: {api_db.db_path}"

    print(f"✅ All database instances use: {TEST_DB}")
    print(f"   - sourcing_mvp.database.db")
    print(f"   - sourcing_mvp.mcp_server.db")
    print(f"   - sourcing_mvp.quote_api.db")

def main():
    """主测试流程"""
    print("="*60)
    print("Real E2E Test - Core Fixes Verification")
    print("="*60)

    cleanup()

    try:
        # Test 1: 数据库初始化
        db = test_database_initialization()

        # Test 2: 创建供应商（SQL 参数）
        supplier_id = test_create_supplier(db)

        # Test 3: 时区处理
        case_id, request_id = test_timezone_handling(db, supplier_id)

        # Test 4: 数据库统一
        test_unified_database()

        # 最终验证
        print("\n" + "="*60)
        print("✅ ALL CORE FIXES VERIFIED")
        print("="*60)
        print("\nVerified fixes:")
        print("  1. ✅ SQL INSERT has 14 params matching 14 columns")
        print("  2. ✅ Timezone-aware datetime comparison works")
        print("  3. ✅ All tools use unified database instance")
        print("\nTest database preserved for inspection:")
        print(f"  sqlite3 {TEST_DB}")

        return True

    except Exception as e:
        print("\n" + "="*60)
        print("❌ TEST FAILED")
        print("="*60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
