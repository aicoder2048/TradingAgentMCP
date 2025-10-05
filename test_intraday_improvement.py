"""
测试日内波动改进效果

使用TSLA 435 PUT的真实案例测试改进后的限价订单成交概率预测。
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.mcp_server.tools.option_limit_order_probability_tool import option_limit_order_probability_tool


async def test_intraday_improvement():
    """
    测试日内波动改进

    用户案例：
    - TSLA 435 PUT
    - 当前市价: $15.10
    - 限价: $10.00
    - 到期日: 2025-10-10
    - 上一交易日的期权价格日内区间: $8.10 - $24.00
    """

    print("=" * 80)
    print("日内波动改进效果测试")
    print("=" * 80)
    print()
    print("测试场景：TSLA 435 PUT 限价订单")
    print("  - 当前市价: $15.10")
    print("  - 限价: $10.00")
    print("  - 到期日: 2025-10-10")
    print("  - 历史日内区间: $8.10 - $24.00")
    print()
    print("🚀 运行改进后的分析...")
    print()

    try:
        result = await option_limit_order_probability_tool(
            symbol="TSLA",
            strike_price=435.0,
            expiration="2025-10-10",
            option_type="put",
            current_price=15.10,
            limit_price=10.00,
            order_side="buy"
        )

        if result.get("status") == "success":
            print("✅ 分析成功完成！")
            print()
            print("=" * 80)
            print("核心结果对比")
            print("=" * 80)
            print()

            # 提取关键结果
            fill_prob = result["fill_probability"]
            fill_prob_close_only = result.get("fill_probability_close_only")
            improvement = result.get("probability_improvement")
            improvement_pct = result.get("improvement_percentage")
            uses_intraday = result.get("uses_intraday_detection", False)

            if uses_intraday and fill_prob_close_only is not None:
                print(f"📊 仅收盘价方法:")
                print(f"   成交概率: {fill_prob_close_only*100:.2f}%")
                print()
                print(f"✨ 日内波动改进方法:")
                print(f"   成交概率: {fill_prob*100:.2f}%")
                print()
                print(f"📈 改进效果:")
                print(f"   绝对提升: {improvement*100:.2f}个百分点")
                print(f"   相对提升: {improvement_pct:.2f}%")
                print()
            else:
                print(f"成交概率: {fill_prob*100:.2f}%")
                print()

            print("=" * 80)
            print("详细分析")
            print("=" * 80)
            print()

            # 首日成交概率
            first_day_prob = result.get("first_day_fill_probability", 0)
            print(f"首日成交概率: {first_day_prob*100:.2f}%")

            # 预期成交时间
            expected_days = result.get("expected_days_to_fill")
            if expected_days:
                print(f"预期成交时间: {expected_days:.2f}天")

            # 中位成交时间
            median_days = result.get("median_days_to_fill")
            if median_days:
                print(f"中位成交时间: {median_days:.0f}天")

            print()

            # 建议
            print("=" * 80)
            print("智能建议")
            print("=" * 80)
            print()

            for rec in result.get("recommendations", []):
                print(f"• {rec}")

            print()

            # 替代限价
            print("=" * 80)
            print("替代限价方案")
            print("=" * 80)
            print()

            for alt in result.get("alternative_limits", []):
                print(f"限价: ${alt['limit_price']:.2f}")
                print(f"  成交概率: {alt['fill_probability']*100:.0f}%")
                print(f"  预期天数: {alt['expected_days']:.1f}天")
                print(f"  方案: {alt['scenario']}")
                print()

            print("=" * 80)
            print("测试完成")
            print("=" * 80)

        else:
            print(f"❌ 分析失败: {result.get('error')}")
            if result.get('error_trace'):
                print()
                print("错误详情:")
                print(result['error_trace'])

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_intraday_improvement())
