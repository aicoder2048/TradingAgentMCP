#!/usr/bin/env python3
"""
演示智能到期日优化过程的完整输出

这个脚本展示了新增的优化过程透明度功能：
- 显示所有候选到期日
- 显示筛选标准和权重
- 显示每个候选的评分详情
- 显示被淘汰候选的原因
- 显示最终选择的理由
"""

import asyncio
from datetime import datetime, timedelta
from src.mcp_server.tools.optimal_expiration_selector_tool import OptimalExpirationSelectorTool
import json


async def demo_optimization():
    """演示优化过程"""

    # 创建示例到期日数据
    sample_expirations = []
    base_date = datetime.now()

    # 生成一系列到期日（7天、14天、21天、28天、35天、42天、49天）
    for days in [7, 14, 21, 28, 35, 42, 49, 56, 63]:
        exp_date = base_date + timedelta(days=days)
        sample_expirations.append(exp_date.strftime("%Y-%m-%d"))

    print("=" * 80)
    print("智能期权到期日优化过程演示")
    print("=" * 80)
    print(f"\n股票代码: GOOG")
    print(f"策略类型: CSP (现金担保看跌)")
    print(f"可用到期日数量: {len(sample_expirations)}")
    print(f"可用到期日列表: {sample_expirations}")
    print("\n" + "=" * 80)

    # 创建工具实例
    tool = OptimalExpirationSelectorTool(tradier_client=None)

    # 执行优化
    result = await tool.execute(
        symbol="GOOG",
        available_expirations=sample_expirations,
        strategy_type="csp",
        volatility=0.3
    )

    if result['success']:
        print("\n✅ 优化成功！\n")

        # 1. 显示最优选择
        optimal = result['optimal_expiration']
        print("【最优选择】")
        print(f"  日期: {optimal['date']}")
        print(f"  天数: {optimal['days_to_expiry']}天")
        print(f"  类型: {optimal['type']}")
        print(f"  综合评分: {optimal['composite_score']:.2f}/100")
        print(f"  选择理由: {optimal['selection_reason']}")

        # 2. 显示评分详情
        print("\n【评分详情】")
        scores = result['score_details']
        print(f"  Theta效率: {scores['theta_efficiency']:.2f}/100")
        print(f"  Gamma风险控制: {scores['gamma_risk_control']:.2f}/100")
        print(f"  流动性: {scores['liquidity_score']:.2f}/100")
        print(f"  综合评分: {scores['composite_score']:.2f}/100")

        # 3. 显示优化过程
        if 'optimization_process' in result:
            process = result['optimization_process']

            print("\n" + "=" * 80)
            print("【完整优化过程】")
            print("=" * 80)

            # 3.1 筛选标准
            print("\n1. 筛选标准:")
            criteria = process['筛选标准']
            for key, value in criteria.items():
                if key == "权重配置":
                    print(f"\n   {key}:")
                    for weight_key, weight_value in value.items():
                        print(f"      - {weight_key}: {weight_value:.0%}")
                else:
                    print(f"   - {key}: {value}")

            # 3.2 所有候选评估
            print(f"\n2. 所有候选评估 (共{process['总候选数']}个):")
            print("\n   排名  日期          天数  类型      综合  Theta  Gamma  流动性  是否最优")
            print("   " + "-" * 75)

            for eval_item in process['所有候选评估']:
                optimal_mark = "✓" if eval_item['是否最优'] else " "
                print(f"   {eval_item['排名']:2d}   {eval_item['日期']}  {eval_item['天数']:3d}  "
                      f"{eval_item['类型']:8s}  {eval_item['综合评分']:5.1f}  "
                      f"{eval_item['Theta效率']:5.1f}  {eval_item['Gamma风险控制']:5.1f}  "
                      f"{eval_item['流动性']:6.1f}  {optimal_mark}")

            # 3.3 淘汰分析
            print("\n3. 候选淘汰分析 (前5个被淘汰的候选):")
            for i, rejection in enumerate(process['候选淘汰分析'][:5], 1):
                print(f"\n   候选 #{i+1}: {rejection['日期']} ({rejection['天数']}天)")
                print(f"   - 评分: {rejection['评分']:.2f}/100")
                print(f"   - 淘汰原因: {rejection['淘汰原因']}")

            # 3.4 最终选择详情
            print("\n4. 最终选择详情:")
            selection = process['最终选择详情']
            print(f"\n   选中日期: {selection['选中日期']}")
            print(f"   到期天数: {selection['到期天数']}天")
            print(f"   到期类型: {selection['到期类型']}")
            print(f"   综合评分: {selection['综合评分']:.2f}/100")
            print(f"   选择理由: {selection['选择理由']}")

            if selection['优势分析']:
                print("\n   优势分析:")
                for advantage in selection['优势分析']:
                    print(f"   {advantage}")

            # 3.5 评分方法说明
            print("\n5. 评分方法说明:")
            methods = process['评分方法说明']
            for method, desc in methods.items():
                print(f"   - {method}: {desc}")

        # 4. 显示建议
        print("\n【操作建议】")
        print(f"  {result['recommendation']}")

        # 5. 显示改进幅度
        print("\n【优化效果】")
        print(f"  相比随机选择的改进: {result['analysis']['improvement_vs_random']}")
        print(f"  使用权重: {result['analysis']['weights_used']}")

    else:
        print(f"\n❌ 优化失败: {result.get('error', 'Unknown error')}")

    print("\n" + "=" * 80)
    print("演示结束")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(demo_optimization())
