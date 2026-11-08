"""
验证 P1 修复：MOQ 解析、空结果、启动说明
"""
import sys
from pathlib import Path

# 添加 sourcing_mvp 到路径
sys.path.insert(0, str(Path(__file__).parent))

from sourcing_mvp.tools.discover import _score_supplier


def test_moq_parsing():
    """测试 MOQ 解析能否正确处理范围格式"""
    print("测试 1: MOQ 解析修复")

    # 模拟供应商数据
    supplier = {
        "id": "test_supplier",
        "name": "Test Supplier",
        "categories": ["coffee_makers"],
        "capabilities": {
            "moq_range": "50-500 units",  # 范围格式
            "lead_time": "20-30 days"
        },
        "verification": {
            "business_license": True
        }
    }

    # 测试场景 1：买手要求 100 units（应该匹配）
    score1, reasons1, caveats1 = _score_supplier(
        supplier,
        "coffee maker",
        {"moq": 100}
    )

    # 检查是否正确提取了 min_moq = 50
    moq_matched = any("MOQ flexible (from 50 units)" in r for r in reasons1)
    assert moq_matched, f"❌ 失败：MOQ 解析未能正确处理 '50-500 units'。Reasons: {reasons1}"
    print("  ✅ 正确解析 '50-500 units'，识别最小 MOQ = 50")

    # 测试场景 2：买手要求 30 units（小于最小 MOQ，应该有警告）
    score2, reasons2, caveats2 = _score_supplier(
        supplier,
        "coffee maker",
        {"moq": 30}
    )

    has_caveat = any("MOQ may be higher" in c for c in caveats2)
    assert has_caveat, f"❌ 失败：未正确警告 MOQ 过低。Caveats: {caveats2}"
    print("  ✅ 正确警告 MOQ 要求过低")

    print("✅ 测试 1 通过：MOQ 解析修复有效\n")


def test_empty_result_has_case_id():
    """测试空结果是否包含 case_id"""
    print("测试 2: 空结果包含 case_id")

    # 这个测试需要数据库访问，我们验证代码逻辑
    # 检查 discover.py 中空结果分支是否返回 case_id

    from pathlib import Path
    discover_file = Path(__file__).parent / "sourcing_mvp" / "tools" / "discover.py"
    content = discover_file.read_text(encoding="utf-8")

    # 验证空结果分支包含 case_id
    empty_result_section = content[content.find("if not all_suppliers:"):content.find("if not all_suppliers:") + 500]

    has_case_id = '"case_id": case_id' in empty_result_section or "'case_id': case_id" in empty_result_section
    assert has_case_id, "❌ 失败：空结果分支未返回 case_id"

    print("  ✅ 空结果分支正确返回 case_id")
    print("✅ 测试 2 通过：空结果修复有效\n")


def test_confirm_default_is_false():
    """测试 confirm 默认值是否为 False"""
    print("测试 3: 审批机制 - confirm 默认值")

    from sourcing_mvp.models import SendInquiryInput
    from uuid import uuid4

    # 创建 SendInquiryInput 实例，不传 confirm
    input_without_confirm = SendInquiryInput(inquiry_id=uuid4())

    assert input_without_confirm.confirm is False, \
        f"❌ 失败：confirm 默认值应为 False，实际为 {input_without_confirm.confirm}"

    print("  ✅ confirm 默认值正确设置为 False（需要明确同意）")
    print("✅ 测试 3 通过：审批机制修复有效\n")


def test_suppliers_marked_as_test_data():
    """测试供应商是否正确标记为测试数据"""
    print("测试 4: 供应商标记为测试数据")

    import json
    suppliers_file = Path(__file__).parent / "sourcing_mvp" / "data" / "suppliers.json"
    suppliers = json.loads(suppliers_file.read_text(encoding="utf-8"))

    for supplier in suppliers:
        assert supplier.get("is_test_data") is True, \
            f"❌ 失败：供应商 {supplier['id']} 未标记为测试数据"
        assert supplier.get("active") is False, \
            f"❌ 失败：供应商 {supplier['id']} 应设为 active=false"
        assert "example.com" in supplier["contact"]["email"], \
            f"❌ 失败：供应商 {supplier['id']} 邮箱应包含 example.com"
        assert supplier["verification"]["email_verified"] is False, \
            f"❌ 失败：供应商 {supplier['id']} 应设为 email_verified=false"

    print(f"  ✅ 全部 {len(suppliers)} 个供应商正确标记为测试数据")
    print("  ✅ 全部供应商设为 active=false")
    print("  ✅ 全部邮箱使用 example.com 域名")
    print("✅ 测试 4 通过：供应商数据修复有效\n")


def main():
    print("=" * 60)
    print("P1 修复验证测试")
    print("=" * 60 + "\n")

    try:
        test_moq_parsing()
        test_empty_result_has_case_id()
        test_confirm_default_is_false()
        test_suppliers_marked_as_test_data()

        print("=" * 60)
        print("✅ 所有 P1 测试通过")
        print("=" * 60)
        print("\n修复内容:")
        print("1. MOQ 解析：正确处理 '50-500 units' 范围格式")
        print("2. 空结果：无匹配供应商时返回 case_id")
        print("3. 审批机制：confirm 默认值改为 False")
        print("4. 供应商数据：全部标记为测试数据，不可用于生产")
        return 0

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 意外错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
