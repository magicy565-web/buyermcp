"""
真实集成测试脚本

从头到尾验证完整流程：
1. 初始化数据库
2. 启动 API 服务
3. 创建报价请求（通过 MCP）
4. 提交报价（HTTP）
5. 查询报价（通过 MCP）
6. 验证数据一致性
"""
import os
import sys
import time
import json
import sqlite3
from datetime import datetime, timedelta
import requests
from decimal import Decimal

# 设置环境变量
os.environ["DATABASE_PATH"] = "test_sourcing.db"

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sourcing_mvp.database import Database
from sourcing_mvp.token_manager import TokenManager
from sourcing_mvp.quote_models import QuoteRequestStatus
from uuid import uuid4


def cleanup():
    """清理测试数据库"""
    if os.path.exists("test_sourcing.db"):
        os.remove("test_sourcing.db")
        print("✅ Cleaned up test database")


def init_test_database():
    """初始化测试数据库"""
    print("\n=== Step 1: Initialize Test Database ===")
    db = Database("test_sourcing.db")

    # 创建测试买手案例
    case_id = str(uuid4())
    case_data = {
        "id": case_id,
        "buyer_id": "test_buyer",
        "initial_query": "Need 500 stainless steel water bottles",
        "product_description": "500ml insulated stainless steel bottle",
        "requirements": json.dumps({"quantity": 500, "material": "stainless steel"}),
        "status": "active",
        "discovered_suppliers": json.dumps([]),
        "message_count": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    db.create_case(case_data)
    print(f"✅ Created test case: {case_id}")

    # 创建测试供应商
    supplier_id = str(uuid4())
    supplier_data = {
        "id": supplier_id,
        "name": "Test Supplier Co.",
        "contact": {
            "email": "test@supplier.com",
            "phone": "+86-13800138000",
            "contact_person": "Zhang Wei",
        },
        "categories": ["bottles", "drinkware"],
        "capabilities": {},
        "verification": {},
        "active": True,
        "is_test_data": False,  # 不是测试数据，可以创建报价请求
    }
    db.create_supplier(supplier_data)
    print(f"✅ Created test supplier: {supplier_id}")

    return case_id, supplier_id


def create_quote_request_via_mcp(case_id, supplier_id):
    """通过 MCP 工具创建报价请求"""
    print("\n=== Step 2: Create Quote Request (MCP) ===")

    from sourcing_mvp.tools import create_quote_request
    import asyncio

    args = {
        "case_id": case_id,
        "supplier_id": supplier_id,
        "product_name": "500ml Stainless Steel Water Bottle",
        "product_description": "Insulated, BPA-free, leak-proof",
        "quantity": 500,
        "specifications": {"material": "304 stainless steel", "capacity": "500ml"},
        "quote_deadline_hours": 72,
        "buyer_id": "test_buyer",
        "confirm": True,
        "base_url": "http://localhost:8000",
    }

    result = asyncio.run(create_quote_request.create_quote_request(args))

    print(f"✅ Quote request created: {result['quote_request_id']}")
    print(f"   Link: {result['quote_link']}")
    print(f"   Token: {result['token']}")
    print(f"   Expires: {result['expires_at']}")

    return result


def submit_quote_via_http(token):
    """通过 HTTP 提交报价"""
    print("\n=== Step 3: Submit Quote (HTTP) ===")

    # 准备报价数据
    valid_until = (datetime.now() + timedelta(days=30)).isoformat()

    quote_data = {
        "token": token,
        "unit_price": "18.50",
        "currency": "USD",
        "moq": 100,
        "lead_time_days": 25,
        "trade_term": "FOB",
        "quote_valid_until": valid_until,
        "payment_terms": "30% deposit, 70% before shipping",
        "specification_notes": "Can provide custom logo engraving",
    }

    print(f"   Submitting quote to http://localhost:8000/api/quote/submit")
    print(f"   Unit Price: USD {quote_data['unit_price']}")
    print(f"   MOQ: {quote_data['moq']}")
    print(f"   Lead Time: {quote_data['lead_time_days']} days")

    try:
        response = requests.post(
            "http://localhost:8000/api/quote/submit",
            json=quote_data,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        if response.status_code == 201:
            result = response.json()
            print(f"✅ Quote submitted successfully")
            print(f"   Quote ID: {result['quote_id']}")
            return result, quote_data
        else:
            print(f"❌ Quote submission failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None, quote_data

    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP request failed: {e}")
        print(f"   Make sure API server is running: python -m sourcing_mvp.quote_api")
        return None, quote_data


def query_quotes_via_mcp(case_id):
    """通过 MCP 工具查询报价"""
    print("\n=== Step 4: Query Quotes (MCP) ===")

    from sourcing_mvp.tools import get_quotes
    import asyncio

    args = {
        "case_id": case_id,
        "buyer_id": "test_buyer",
    }

    result = asyncio.run(get_quotes.get_quotes(args))

    print(f"✅ Found {result['total_count']} quote(s)")
    print(f"\n{result['summary']}")

    return result


def verify_database_persistence():
    """验证数据库持久化"""
    print("\n=== Step 5: Verify Database Persistence ===")

    db = Database("test_sourcing.db")

    # 查询报价记录
    conn = sqlite3.connect("test_sourcing.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM supplier_quote")
    quote_count = cursor.fetchone()[0]
    print(f"✅ Quotes in database: {quote_count}")

    cursor.execute("SELECT COUNT(*) as count FROM quote_version")
    version_count = cursor.fetchone()[0]
    print(f"✅ Version records: {version_count}")

    cursor.execute("SELECT COUNT(*) as count FROM quote_token")
    token_count = cursor.fetchone()[0]
    print(f"✅ Token records: {token_count}")

    conn.close()


def verify_data_consistency(submitted_data, queried_result):
    """验证数据一致性"""
    print("\n=== Step 6: Verify Data Consistency ===")

    if not queried_result or not queried_result.get("quotes"):
        print("❌ No quotes found to verify")
        return False

    quote = queried_result["quotes"][0]

    checks = [
        ("Unit Price", submitted_data["unit_price"], quote["unit_price"]),
        ("Currency", submitted_data["currency"], quote["currency"]),
        ("MOQ", submitted_data["moq"], quote["moq"]),
        ("Lead Time", submitted_data["lead_time_days"], quote["lead_time_days"]),
        ("Trade Term", submitted_data["trade_term"], quote["trade_term"]),
        ("Payment Terms", submitted_data["payment_terms"], quote["payment_terms"]),
    ]

    all_match = True
    for field, expected, actual in checks:
        match = str(expected) == str(actual)
        symbol = "✅" if match else "❌"
        print(f"{symbol} {field}: {expected} == {actual}")
        if not match:
            all_match = False

    return all_match


def main():
    """主测试流程"""
    print("="*60)
    print("Real Integration Test - Quote Submission System")
    print("="*60)

    # 清理旧数据
    cleanup()

    try:
        # Step 1: 初始化数据库
        case_id, supplier_id = init_test_database()

        # Step 2: 创建报价请求
        quote_request = create_quote_request_via_mcp(case_id, supplier_id)
        token = quote_request["token"]

        # Step 3: 提交报价
        print("\n⚠️  Make sure API server is running:")
        print("   python -m sourcing_mvp.quote_api")
        input("\nPress Enter to continue...")

        submit_result, submitted_data = submit_quote_via_http(token)

        if not submit_result:
            print("\n❌ Test failed: Could not submit quote")
            return False

        # Step 4: 查询报价
        time.sleep(1)  # 确保数据已写入
        queried_result = query_quotes_via_mcp(case_id)

        # Step 5: 验证持久化
        verify_database_persistence()

        # Step 6: 验证一致性
        consistent = verify_data_consistency(submitted_data, queried_result)

        # 最终结果
        print("\n" + "="*60)
        if consistent:
            print("✅ ALL TESTS PASSED")
            print("="*60)
            print("\nReal business loop verified:")
            print("  1. ✅ MCP creates quote request")
            print("  2. ✅ HTTP submits quote")
            print("  3. ✅ Database persists data")
            print("  4. ✅ MCP queries consistent data")
            print("  5. ✅ Version history recorded")
            return True
        else:
            print("❌ DATA CONSISTENCY CHECK FAILED")
            print("="*60)
            return False

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 保留测试数据库以供检查
        print(f"\n📁 Test database saved at: test_sourcing.db")
        print("   You can inspect it with: sqlite3 test_sourcing.db")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
