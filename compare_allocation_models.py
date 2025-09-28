#!/usr/bin/env python3
"""
对比有质量因子 vs 无质量因子的分配模型结果
"""

import sys
import asyncio
from simplified_allocation_model import SimplifiedAllocationModel, SimpleStockData

# 导入原始模型
sys.path.append('src/mcp_server/tools')
try:
    from portfolio_allocation_model import StockData, StockAcquisitionAllocationModel
except ImportError:
    print("无法导入原始模型，跳过对比")
    sys.exit(1)

def compare_allocation_models():
    """对比两种分配模型的结果"""
    
    # 测试数据
    test_data = [
        {
            "symbol": "GOOG",
            "assignment_prob": 0.678,
            "strike_price": 265.0,
            "current_price": 247.18,
            "premium": 25.03,
            "annual_return": 0.452,
            "implied_volatility": 0.325,
            "week_52_high": 256.70,
            "days_to_expiry": 82,
            "delta": -0.621,
            "theta": -0.098
        },
        {
            "symbol": "TSLA",
            "assignment_prob": 0.659,
            "strike_price": 480.0,
            "current_price": 440.40,
            "premium": 71.35,
            "annual_return": 0.542,
            "implied_volatility": 0.592,
            "week_52_high": 488.54,
            "days_to_expiry": 82,
            "delta": -0.546,
            "theta": -0.323
        },
        {
            "symbol": "META",
            "assignment_prob": 0.712,
            "strike_price": 780.0,
            "current_price": 743.75,
            "premium": 54.50,
            "annual_return": 0.428,
            "implied_volatility": 0.385,
            "week_52_high": 796.25,
            "days_to_expiry": 82,
            "delta": -0.632,
            "theta": -0.245
        },
        {
            "symbol": "NVDA",
            "assignment_prob": 0.665,
            "strike_price": 185.0,
            "current_price": 178.19,
            "premium": 18.25,
            "annual_return": 0.525,
            "implied_volatility": 0.485,
            "week_52_high": 184.55,
            "days_to_expiry": 82,
            "delta": -0.578,
            "theta": -0.189
        }
    ]
    
    print("=" * 100)
    print("有质量因子 vs 无质量因子分配模型对比")
    print("=" * 100)
    
    # === 1. 原始模型 (有质量因子) ===
    print("\n🔧 原始模型 (有质量因子)")
    print("-" * 50)
    
    # 转换为原始模型的数据格式
    original_stocks = [
        StockData(
            symbol=data['symbol'],
            assignment_prob=data['assignment_prob'],
            strike_price=data['strike_price'],
            current_price=data['current_price'],
            premium=data['premium'],
            annual_return=data['annual_return'],
            implied_volatility=data['implied_volatility'],
            week_52_high=data['week_52_high'],
            days_to_expiry=data['days_to_expiry'],
            delta=data['delta'],
            theta=data['theta']
        )
        for data in test_data
    ]
    
    original_model = StockAcquisitionAllocationModel()
    original_weights, original_scores = original_model.calculate_portfolio_weights(original_stocks)
    
    print(f"模型公式: {original_model.alpha:.2f}×assignment_prob + {original_model.beta:.2f}×discount_depth + {original_model.gamma:.2f}×quality_factor")
    print("权重分配:")
    for symbol, weight in original_weights.items():
        print(f"  {symbol}: {weight:.2%}")
    
    print("\n详细评分:")
    for score in original_scores:
        print(f"{score['symbol']}: 总分{score['total_score']:.1f} = "
              f"分配{score['prob_score']:.1f} + 折扣{score['discount_score']:.1f} + 质量{score['quality_score']:.1f}")
    
    # === 2. 简化模型 (无质量因子) ===
    print("\n\n⚡ 简化模型 (无质量因子)")
    print("-" * 50)
    
    # 转换为简化模型的数据格式
    simple_stocks = [
        SimpleStockData(
            symbol=data['symbol'],
            assignment_prob=data['assignment_prob'],
            strike_price=data['strike_price'],
            current_price=data['current_price'],
            premium=data['premium']
        )
        for data in test_data
    ]
    
    simple_model = SimplifiedAllocationModel()
    simple_weights, simple_scores = simple_model.calculate_portfolio_weights(simple_stocks)
    
    print(f"模型公式: {simple_model.alpha:.1f}×assignment_prob + {simple_model.beta:.1f}×discount_depth")
    print("权重分配:")
    for symbol, weight in simple_weights.items():
        print(f"  {symbol}: {weight:.2%}")
    
    print("\n详细评分:")
    for score in simple_scores:
        print(f"{score['symbol']}: 总分{score['total_score']:.1f} = "
              f"分配{score['prob_score']:.1f} + 折扣{score['discount_score']:.1f}")
    
    # === 3. 对比分析 ===
    print("\n\n📊 对比分析")
    print("-" * 50)
    
    print(f"{'股票':<8} {'原始权重':<10} {'简化权重':<10} {'权重差异':<10} {'排名变化'}")
    print("-" * 60)
    
    # 计算排名
    original_ranking = {score['symbol']: i+1 for i, score in enumerate(original_scores)}
    simple_ranking = {score['symbol']: i+1 for i, score in enumerate(simple_scores)}
    
    for symbol in ['GOOG', 'TSLA', 'META', 'NVDA']:
        orig_weight = original_weights[symbol]
        simp_weight = simple_weights[symbol]
        weight_diff = simp_weight - orig_weight
        
        orig_rank = original_ranking[symbol]
        simp_rank = simple_ranking[symbol]
        rank_change = orig_rank - simp_rank  # 正数表示排名上升
        
        print(f"{symbol:<8} {orig_weight:.2%}        {simp_weight:.2%}        {weight_diff:+.2%}     "
              f"{orig_rank}→{simp_rank} ({rank_change:+d})")
    
    # === 4. 主观成分对比 ===
    print("\n\n🎯 主观成分对比")
    print("-" * 50)
    
    print("原始模型主观成分:")
    print("  ❌ 年化收益50%封顶线")
    print("  ❌ 隐含波动率60%封顶线") 
    print("  ❌ 时间价值15%封顶线")
    print("  ❌ 质量因子4个子项权重(30%:25%:25%:20%)")
    print("  ❌ 三大因子权重(45%:35%:20%)")
    print("  📊 主观参数总数: 8个")
    
    print("\n简化模型主观成分:")
    print("  ✅ 无任何封顶线")
    print("  ✅ 无质量因子")
    print("  ✅ 只有2个权重参数(60%:40%)")
    print("  📊 主观参数总数: 2个")
    
    print(f"\n主观成分减少: {(8-2)/8*100:.0f}%")
    
    # === 5. 模型透明度对比 ===
    print("\n\n🔍 模型透明度对比")
    print("-" * 50)
    
    print("原始模型复杂度:")
    print("  - 需要年化收益、隐含波动率、52周高点等多项数据")
    print("  - 涉及8个主观参数设定")
    print("  - 质量因子计算逻辑复杂")
    print("  - 硬编码封顶线难以解释")
    
    print("\n简化模型透明度:")
    print("  - 只需要分配概率、价格、执行价、权利金4项基础数据")
    print("  - 只有2个权重参数")
    print("  - 计算逻辑清晰：分配概率 + 折扣深度")
    print("  - 完全基于客观数据计算")
    
    # === 6. 投资逻辑对比 ===
    print("\n\n💡 投资逻辑对比")
    print("-" * 50)
    
    print("原始模型投资逻辑:")
    print("  🎯 建仓概率 + 折扣幅度 + 股票质量")
    print("  📈 考虑股票基本面因素")
    print("  ⚠️  包含大量主观判断")
    
    print("\n简化模型投资逻辑:")
    print("  🎯 建仓概率 + 折扣幅度")
    print("  💰 专注于CSP策略核心：获得股票的概率和折扣")
    print("  ✅ 完全客观，易于解释和复现")
    
    return {
        'original_weights': original_weights,
        'simple_weights': simple_weights,
        'original_scores': original_scores,
        'simple_scores': simple_scores
    }


if __name__ == "__main__":
    compare_allocation_models()