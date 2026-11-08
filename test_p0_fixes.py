"""
验证 P0 修复：确保不会谎报成功或伪造数据
"""
import asyncio
import sys
from pathlib import Path

# 添加 sourcing_mvp 到路径
sys.path.insert(0, str(Path(__file__).parent / "sourcing_mvp"))

from sourcing_mvp.tools.send import _send_email
from sourcing_mvp.tools.track import _check_for_response


async def test_send_email_does_not_fake_success():
    """测试：邮件发送不应该谎报成功"""
    print("测试 1: 邮件发送不应该谎报成功")

    result = await _send_email(
        to="test@example.com",
        subject="Test Inquiry",
        body="This is a test"
    )

    # 在未实现真实发送之前，应该返回 False
    assert result is False, "❌ 失败：邮件发送函数在未实现时应返回 False，而不是谎报成功"
    print("✅ 通过：邮件发送正确返回 False（未实现）")


async def test_track_does_not_fake_responses():
    """测试：追踪不应该伪造供应商回复"""
    print("\n测试 2: 追踪不应该伪造供应商回复")

    # 运行多次检查，确保不会随机生成假数据
    for i in range(20):
        result = await _check_for_response(f"test-inquiry-{i}")

        # 在未实现真实检查之前，应该总是返回 None
        assert result is None, f"❌ 失败：第 {i+1} 次检查返回了伪造的数据: {result}"

    print("✅ 通过：20 次检查均正确返回 None（无伪造数据）")


async def main():
    print("=" * 60)
    print("P0 修复验证测试")
    print("=" * 60)

    try:
        await test_send_email_does_not_fake_success()
        await test_track_does_not_fake_responses()

        print("\n" + "=" * 60)
        print("✅ 所有 P0 测试通过")
        print("=" * 60)
        print("\n修复内容:")
        print("1. send.py: _send_email() 现在返回 False 而不是谎报成功")
        print("2. track.py: _check_for_response() 现在返回 None 而不是伪造报价")
        print("\n这确保了系统不会:")
        print("- 让买手误以为邮件已发送（实际未发送）")
        print("- 展示不存在的供应商报价（随机生成的假数据）")
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
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
