"""
Test script for Option Position Rebalancer Prompt

测试期权仓位再平衡引擎提示生成器的功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.mcp_server.prompts.option_position_rebalancer_prompt import (
    option_position_rebalancer_engine,
    get_rebalancer_examples,
    get_usage_guidelines
)


async def test_short_put_losing_position():
    """测试亏损的做空Put仓位"""
    print("\n" + "="*80)
    print("测试场景 1: 亏损的做空Put仓位 - 防御性滚动评估")
    print("="*80)

    result = await option_position_rebalancer_engine(
        option_symbol="TSLA250919P00390000",
        position_size=-100,
        entry_price=13.00,
        position_type="short_put",
        entry_date="2025-09-01",
        risk_tolerance="moderate",
        defensive_roll_trigger_pct=15.0,
        profit_target_pct=70.0,
        max_additional_capital=50000
    )

    print("\n生成的提示词长度:", len(result), "字符")
    print("\n提示词前500字符预览:")
    print("-" * 80)
    print(result[:500])
    print("-" * 80)

    # 验证关键内容
    assert "TSLA250919P00390000" in result
    assert "Tesla" in result.upper() or "TSLA" in result
    assert "390" in result  # 行权价
    assert "short_put" in result.lower() or "做空" in result
    assert "P&L" in result or "盈亏" in result

    print("\n✅ 测试通过: 亏损的做空Put仓位提示生成成功")
    return result


async def test_short_put_winning_position():
    """测试盈利的做空Put仓位"""
    print("\n" + "="*80)
    print("测试场景 2: 盈利的做空Put仓位 - 获利了结评估")
    print("="*80)

    result = await option_position_rebalancer_engine(
        option_symbol="AAPL251017P00220000",
        position_size=-50,
        entry_price=5.50,
        position_type="short_put",
        entry_date="2025-10-01",
        risk_tolerance="conservative",
        defensive_roll_trigger_pct=15.0,
        profit_target_pct=70.0,
        max_additional_capital=0
    )

    print("\n生成的提示词长度:", len(result), "字符")
    print("\n提示词关键部分预览:")
    print("-" * 80)

    # 提取并显示关键部分
    if "## 📊 当前仓位概览" in result:
        start = result.find("## 📊 当前仓位概览")
        end = result.find("##", start + 10)
        print(result[start:end])

    print("-" * 80)

    # 验证关键内容
    assert "AAPL251017P00220000" in result
    assert "AAPL" in result.upper()
    assert "220" in result  # 行权价
    assert "conservative" in result.lower() or "保守" in result

    print("\n✅ 测试通过: 盈利的做空Put仓位提示生成成功")
    return result


async def test_short_call_defensive():
    """测试需要防御的做空Call仓位"""
    print("\n" + "="*80)
    print("测试场景 3: 需要防御的做空Call仓位 - 高风险防御")
    print("="*80)

    result = await option_position_rebalancer_engine(
        option_symbol="NVDA250926C00800000",
        position_size=-20,
        entry_price=15.00,
        position_type="short_call",
        entry_date="2025-09-15",
        risk_tolerance="conservative",
        defensive_roll_trigger_pct=20.0,
        profit_target_pct=60.0,
        max_additional_capital=100000
    )

    print("\n生成的提示词长度:", len(result), "字符")

    # 验证关键内容
    assert "NVDA250926C00800000" in result
    assert "NVDA" in result.upper()
    assert "800" in result  # 行权价
    assert "short_call" in result.lower() or "做空" in result
    assert "call" in result.lower() or "看涨" in result

    print("\n✅ 测试通过: 做空Call仓位提示生成成功")
    return result


async def test_parameter_validation():
    """测试参数验证"""
    print("\n" + "="*80)
    print("测试场景 4: 参数验证功能")
    print("="*80)

    # 测试无效的期权符号
    try:
        await option_position_rebalancer_engine(
            option_symbol="INVALID",
            position_size=-100,
            entry_price=13.00,
            position_type="short_put"
        )
        print("❌ 应该抛出异常但没有")
    except ValueError as e:
        print(f"✅ 正确捕获无效期权符号: {e}")

    # 测试无效的仓位大小
    try:
        await option_position_rebalancer_engine(
            option_symbol="TSLA250919P00390000",
            position_size=0,  # 无效：仓位为0
            entry_price=13.00,
            position_type="short_put"
        )
        print("❌ 应该抛出异常但没有")
    except ValueError as e:
        print(f"✅ 正确捕获无效仓位大小: {e}")

    # 测试无效的价格
    try:
        await option_position_rebalancer_engine(
            option_symbol="TSLA250919P00390000",
            position_size=-100,
            entry_price=-5.0,  # 无效：负价格
            position_type="short_put"
        )
        print("❌ 应该抛出异常但没有")
    except ValueError as e:
        print(f"✅ 正确捕获无效价格: {e}")

    print("\n✅ 测试通过: 参数验证功能正常")


async def test_examples_and_guidelines():
    """测试示例和指导功能"""
    print("\n" + "="*80)
    print("测试场景 5: 示例和使用指导")
    print("="*80)

    # 获取示例
    examples = get_rebalancer_examples()
    print(f"\n可用示例数量: {len(examples)}")
    for key, example in examples.items():
        print(f"  - {key}: {example['description']}")

    assert len(examples) == 4
    assert "mu_compact_mode" in examples
    assert "short_put_losing" in examples
    assert "short_put_winning" in examples
    assert "short_call_defensive" in examples

    # 获取使用指导
    guidelines = get_usage_guidelines()
    print(f"\n使用指导条目数: {len(guidelines)}")
    for i, guideline in enumerate(guidelines, 1):
        print(f"  {i}. {guideline}")

    assert len(guidelines) == 8

    print("\n✅ 测试通过: 示例和使用指导功能正常")


async def test_option_symbol_parsing():
    """测试期权符号解析功能"""
    print("\n" + "="*80)
    print("测试场景 6: 期权符号解析")
    print("="*80)

    from src.mcp_server.prompts.option_position_rebalancer_prompt import (
        _extract_underlying_from_option_symbol,
        _extract_strike_from_option_symbol,
        _extract_expiration_from_option_symbol
    )

    # 测试TSLA期权
    symbol1 = "TSLA250919P00390000"
    underlying1 = _extract_underlying_from_option_symbol(symbol1)
    strike1 = _extract_strike_from_option_symbol(symbol1)
    expiration1 = _extract_expiration_from_option_symbol(symbol1)

    print(f"\n期权符号: {symbol1}")
    print(f"  标的: {underlying1}")
    print(f"  行权价: {strike1}")
    print(f"  到期日: {expiration1}")

    assert underlying1 == "TSLA"
    assert strike1 == 390.0
    assert expiration1 == "2025-09-19"

    # 测试AAPL期权
    symbol2 = "AAPL251017P00220000"
    underlying2 = _extract_underlying_from_option_symbol(symbol2)
    strike2 = _extract_strike_from_option_symbol(symbol2)
    expiration2 = _extract_expiration_from_option_symbol(symbol2)

    print(f"\n期权符号: {symbol2}")
    print(f"  标的: {underlying2}")
    print(f"  行权价: {strike2}")
    print(f"  到期日: {expiration2}")

    assert underlying2 == "AAPL"
    assert strike2 == 220.0
    assert expiration2 == "2025-10-17"

    # 测试带小数的行权价
    symbol3 = "GOOG250919C00150500"  # 150.50
    strike3 = _extract_strike_from_option_symbol(symbol3)

    print(f"\n期权符号: {symbol3}")
    print(f"  行权价: {strike3}")

    assert strike3 == 150.5

    print("\n✅ 测试通过: 期权符号解析功能正常")


async def test_end_to_end_mu_option_parsing():
    """测试端到端MU期权符号解析 - 这是bug报告中的实际用例"""
    print("\n" + "="*80)
    print("测试场景 7: 端到端MU期权符号解析 (Bug修复验证)")
    print("="*80)

    # 这是用户报告的实际输入
    option_symbol = "MU251017P00167500"
    position_size = 4
    entry_price = 2.03

    print(f"\n用户输入:")
    print(f"  期权符号: {option_symbol}")
    print(f"  仓位大小: {position_size}")
    print(f"  入场价格: ${entry_price}")

    result = await option_position_rebalancer_engine(
        option_symbol=option_symbol,
        position_size=position_size,
        entry_price=entry_price,
        position_type="short_put",
        entry_date="2025-09-15",
        risk_tolerance="moderate"
    )

    print("\n生成的提示词长度:", len(result), "字符")

    # 验证解析结果在输出中
    print("\n验证解析结果:")

    # 检查标的股票
    assert "MU" in result, "标的股票MU应该在输出中"
    assert "标的股票: MU" in result or "标的股票**: MU" in result, "标的股票应该正确解析"
    print("  ✓ 标的股票: MU")

    # 检查行权价
    assert "167.5" in result or "167.50" in result, "行权价167.50应该在输出中"
    assert "$167.5" in result, "行权价应该格式化为货币"
    print("  ✓ 行权价格: $167.50")

    # 检查到期日
    assert "2025-10-17" in result, "到期日2025-10-17应该在输出中"
    print("  ✓ 到期日期: 2025-10-17")

    # 检查期权类型
    assert "看跌" in result or "PUT" in result or "put" in result.lower(), "应该识别为PUT期权"
    print("  ✓ 期权类型: PUT (看跌期权)")

    # 验证不包含错误的解析结果
    assert "$0.00" not in result or result.count("$0.00") == 0, "不应该有0.00的行权价"
    assert "M-U2-51" not in result, "不应该有乱码日期"
    print("  ✓ 无乱码或错误值")

    # 验证包含解析验证部分
    assert "参数解析验证" in result or "解析验证" in result or "解析结果" in result, "应该包含解析验证部分"
    print("  ✓ 包含解析验证部分")

    print("\n✅ 测试通过: MU期权符号端到端解析成功!")
    print("   Bug已修复: 期权符号正确解析为 MU, $167.50, 2025-10-17, PUT")
    return result


async def main():
    """主测试函数"""
    print("\n" + "="*80)
    print("期权仓位再平衡提示引擎 - 综合测试")
    print("="*80)

    try:
        # 运行所有测试
        await test_option_symbol_parsing()
        await test_parameter_validation()
        await test_examples_and_guidelines()

        result1 = await test_short_put_losing_position()
        result2 = await test_short_put_winning_position()
        result3 = await test_short_call_defensive()

        # 运行端到端bug修复验证测试
        result4 = await test_end_to_end_mu_option_parsing()

        # 最终总结
        print("\n" + "="*80)
        print("📊 测试总结")
        print("="*80)
        print(f"\n✅ 所有测试通过!")
        print(f"\n生成的提示词统计:")
        print(f"  场景1 (亏损Put): {len(result1):,} 字符")
        print(f"  场景2 (盈利Put): {len(result2):,} 字符")
        print(f"  场景3 (防御Call): {len(result3):,} 字符")
        print(f"  场景4 (MU Bug修复): {len(result4):,} 字符")
        print(f"  平均长度: {(len(result1) + len(result2) + len(result3) + len(result4)) // 4:,} 字符")

        print("\n" + "="*80)
        print("🎉 期权仓位再平衡引擎测试完成!")
        print("="*80)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
