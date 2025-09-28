#!/usr/bin/env python3
"""
测试简化分配工具的MCP集成
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append('/Users/szou/Python/Playground/TradingAgentMCP')

from src.mcp_server.tools.simplified_stock_allocation_tool import simplified_stock_allocation_tool


async def test_simplified_allocation_mcp():
    """测试简化分配工具的MCP集成"""
    
    print("=" * 80)
    print("🚀 测试极简股票建仓分配工具 MCP集成")
    print("=" * 80)
    
    # 测试数据：GOOG, TSLA, META, NVDA
    test_stocks = [
        {
            "symbol": "GOOG",
            "assignment_prob": 0.678,
            "strike_price": 265.0,
            "current_price": 247.18,
            "premium": 25.03
        },
        {
            "symbol": "TSLA",
            "assignment_prob": 0.659,
            "strike_price": 480.0,
            "current_price": 440.40,
            "premium": 71.35
        },
        {
            "symbol": "META",
            "assignment_prob": 0.712,
            "strike_price": 780.0,
            "current_price": 743.75,
            "premium": 54.50
        },
        {
            "symbol": "NVDA",
            "assignment_prob": 0.665,
            "strike_price": 185.0,
            "current_price": 178.19,
            "premium": 18.25
        }
    ]
    
    print("📊 输入数据:")
    print(f"股票数量: {len(test_stocks)}")
    for stock in test_stocks:
        print(f"  {stock['symbol']}: 分配概率{stock['assignment_prob']:.1%}, "
              f"执行价${stock['strike_price']}, 当前价${stock['current_price']}, 权利金${stock['premium']}")
    
    # 调用简化分配工具
    result = await simplified_stock_allocation_tool(test_stocks)
    
    if result['success']:
        print(f"\n✅ 计算成功!")
        print(f"⚡ 核心公式: {result['model_info']['core_formula']}")
        print(f"🎯 模型复杂度: {result['summary']['model_complexity']}")
        
        # 权重分配结果
        print(f"\n📈 权重分配结果:")
        weights = result['allocation_results']['weights']
        for symbol, weight in weights.items():
            print(f"  {symbol}: {weight:.2%}")
        
        # 组合指标
        portfolio_metrics = result['allocation_results']['portfolio_analysis']['portfolio_metrics']
        print(f"\n📊 组合指标:")
        print(f"  加权分配概率: {portfolio_metrics['weighted_assignment_prob']:.1%}")
        print(f"  加权折扣率: {portfolio_metrics['weighted_discount_rate']:.2%}")
        print(f"  分散化程度: {portfolio_metrics['diversification_level']} 只股票")
        
        # 详细评分
        print(f"\n🔍 详细评分:")
        scores = result['allocation_results']['detailed_scores']
        for score in scores:
            print(f"  {score['symbol']}: 总分{score['total_score']:.1f} = "
                  f"{score['assignment_score']:.1f}(分配) + {score['discount_score']:.1f}(折扣)")
        
        # 执行顺序
        print(f"\n⭐ 建议执行顺序:")
        for order in result['execution_order']:
            print(f"  {order['priority']}. {order['symbol']} ({order['weight']:.1%}) - {order['reason']}")
            print(f"     分配概率: {order['assignment_prob']}, 折扣率: {order['discount_rate']}, 有效成本: {order['effective_cost']}")
        
        # 模型特征
        model_chars = result['allocation_results']['portfolio_analysis']['model_characteristics']
        print(f"\n🎯 模型特征:")
        print(f"  类型: {model_chars['model_type']}")
        print(f"  主观参数: {model_chars['subjective_parameters']} 个")
        print(f"  硬编码封顶线: {model_chars['hardcoded_caps']} 个")
        print(f"  数据字段需求: {model_chars['data_fields_required']} 个")
        
        # 验证权重和为100%
        total_weight = sum(weights.values())
        print(f"\n✅ 权重验证: 总和 = {total_weight:.4f} (应为1.0000)")
        
        return result
    else:
        print(f"❌ 计算失败: {result['error']}")
        return None


async def test_different_parameters():
    """测试不同参数配置"""
    
    print("\n" + "=" * 80)
    print("🔧 测试不同参数配置")
    print("=" * 80)
    
    test_stocks = [
        {
            "symbol": "TSLA",
            "assignment_prob": 0.659,
            "strike_price": 480.0,
            "current_price": 440.40,
            "premium": 71.35
        },
        {
            "symbol": "NVDA",
            "assignment_prob": 0.665,
            "strike_price": 185.0,
            "current_price": 178.19,
            "premium": 18.25
        }
    ]
    
    # 测试不同权重配比
    test_configs = [
        {"assignment_weight": 0.6, "discount_weight": 0.4, "name": "默认配置 (60%:40%)"},
        {"assignment_weight": 0.7, "discount_weight": 0.3, "name": "更重视分配概率 (70%:30%)"},
        {"assignment_weight": 0.5, "discount_weight": 0.5, "name": "均等权重 (50%:50%)"},
        {"assignment_weight": 0.4, "discount_weight": 0.6, "name": "更重视折扣 (40%:60%)"}
    ]
    
    for config in test_configs:
        print(f"\n📊 {config['name']}")
        print("-" * 50)
        
        result = await simplified_stock_allocation_tool(
            test_stocks,
            assignment_weight=config['assignment_weight'],
            discount_weight=config['discount_weight'],
            include_detailed_report=False
        )
        
        if result['success']:
            weights = result['allocation_results']['weights']
            metrics = result['allocation_results']['portfolio_analysis']['portfolio_metrics']
            
            print(f"  TSLA: {weights['TSLA']:.1%} | NVDA: {weights['NVDA']:.1%}")
            print(f"  加权分配概率: {metrics['weighted_assignment_prob']:.1%}")
            print(f"  加权折扣率: {metrics['weighted_discount_rate']:.2%}")
        else:
            print(f"  ❌ 错误: {result['error']}")


async def test_edge_cases():
    """测试边缘情况"""
    
    print("\n" + "=" * 80)
    print("🧪 测试边缘情况")
    print("=" * 80)
    
    # 测试1: 空数据
    print("📝 测试1: 空股票数据")
    result = await simplified_stock_allocation_tool([])
    print(f"  结果: {'✅成功' if result['success'] else '❌失败'} - {result.get('error', '无错误')}")
    
    # 测试2: 权重和不等于1
    print("\n📝 测试2: 权重和不等于1")
    test_data = [{"symbol": "TEST", "assignment_prob": 0.7, "strike_price": 100, "current_price": 95, "premium": 5}]
    result = await simplified_stock_allocation_tool(test_data, assignment_weight=0.7, discount_weight=0.4)
    print(f"  结果: {'✅成功' if result['success'] else '❌失败'} - {result.get('error', '无错误')}")
    
    # 测试3: 缺少必需字段
    print("\n📝 测试3: 缺少必需字段")
    invalid_data = [{"symbol": "TEST", "assignment_prob": 0.7}]  # 缺少其他字段
    result = await simplified_stock_allocation_tool(invalid_data)
    print(f"  结果: {'✅成功' if result['success'] else '❌失败'} - {result.get('error', '无错误')}")
    
    # 测试4: 分配概率过低
    print("\n📝 测试4: 分配概率过低")
    low_prob_data = [{
        "symbol": "LOWPROB",
        "assignment_prob": 0.5,  # 低于65%阈值
        "strike_price": 100,
        "current_price": 95,
        "premium": 5
    }]
    result = await simplified_stock_allocation_tool(low_prob_data)
    if result['success']:
        score = result['allocation_results']['detailed_scores'][0]
        print(f"  分配概率得分: {score['assignment_score']:.1f} (应为0)")
        print(f"  总得分: {score['total_score']:.1f}")


if __name__ == "__main__":
    async def main():
        # 运行所有测试
        await test_simplified_allocation_mcp()
        await test_different_parameters()
        await test_edge_cases()
        
        print("\n" + "=" * 80)
        print("🎉 所有测试完成!")
        print("=" * 80)
    
    asyncio.run(main())