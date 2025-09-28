#!/usr/bin/env python3
"""
分位数排名法演示
展示如何通过相对排名避免硬编码封顶线
"""

def percentile_rank_demo():
    """演示分位数排名的计算过程"""
    
    # 示例股票数据
    stocks_data = {
        'GOOG': {
            'annual_return': 0.452,      # 45.2%
            'implied_volatility': 0.325, # 32.5%
            'current_price': 247.18,
            'week_52_high': 256.70,
            'premium': 25.03,
            'strike_price': 265.0
        },
        'META': {
            'annual_return': 0.428,      # 42.8%
            'implied_volatility': 0.385, # 38.5%
            'current_price': 743.75,
            'week_52_high': 796.25,
            'premium': 54.50,
            'strike_price': 780.0
        },
        'NVDA': {
            'annual_return': 0.525,      # 52.5%
            'implied_volatility': 0.485, # 48.5%
            'current_price': 178.19,
            'week_52_high': 184.55,
            'premium': 18.25,
            'strike_price': 185.0
        },
        'TSLA': {
            'annual_return': 0.542,      # 54.2%
            'implied_volatility': 0.592, # 59.2%
            'current_price': 440.40,
            'week_52_high': 488.54,
            'premium': 71.35,
            'strike_price': 480.0
        }
    }
    
    print("=" * 80)
    print("分位数排名法演示")
    print("=" * 80)
    
    # 提取各项指标
    symbols = list(stocks_data.keys())
    returns = [stocks_data[s]['annual_return'] for s in symbols]
    ivs = [stocks_data[s]['implied_volatility'] for s in symbols]
    
    # 计算价格位置和时间价值
    positions = []
    time_values = []
    for symbol in symbols:
        data = stocks_data[symbol]
        position = 1 - data['current_price'] / data['week_52_high']
        time_value = data['premium'] / data['strike_price']
        positions.append(position)
        time_values.append(time_value)
    
    print("\n1. 原始数据:")
    print("股票\t年化收益\t隐含波动率\t价格位置\t时间价值")
    print("-" * 60)
    for i, symbol in enumerate(symbols):
        print(f"{symbol}\t{returns[i]:.1%}\t\t{ivs[i]:.1%}\t\t{positions[i]:.1%}\t\t{time_values[i]:.1%}")
    
    print("\n2. 排序后的数据:")
    print(f"年化收益排序: {sorted(returns)}")
    print(f"IV排序: {sorted(ivs)}")
    print(f"价格位置排序: {sorted(positions)}")
    print(f"时间价值排序: {sorted(time_values)}")
    
    print("\n3. 分位数排名计算过程:")
    print("-" * 60)
    
    results = {}
    
    for i, symbol in enumerate(symbols):
        print(f"\n### {symbol} 的排名计算 ###")
        
        # 年化收益排名
        return_rank = (sorted(returns).index(returns[i]) + 1) / len(returns) * 100
        print(f"年化收益 {returns[i]:.1%}: 在排序列表中位置{sorted(returns).index(returns[i]) + 1} → 得分 {return_rank:.1f}")
        
        # IV排名
        iv_rank = (sorted(ivs).index(ivs[i]) + 1) / len(ivs) * 100
        print(f"隐含波动率 {ivs[i]:.1%}: 在排序列表中位置{sorted(ivs).index(ivs[i]) + 1} → 得分 {iv_rank:.1f}")
        
        # 价格位置排名
        position_rank = (sorted(positions).index(positions[i]) + 1) / len(positions) * 100
        print(f"价格位置 {positions[i]:.1%}: 在排序列表中位置{sorted(positions).index(positions[i]) + 1} → 得分 {position_rank:.1f}")
        
        # 时间价值排名
        time_value_rank = (sorted(time_values).index(time_values[i]) + 1) / len(time_values) * 100
        print(f"时间价值 {time_values[i]:.1%}: 在排序列表中位置{sorted(time_values).index(time_values[i]) + 1} → 得分 {time_value_rank:.1f}")
        
        # 综合质量因子
        quality_score = (
            0.30 * return_rank +
            0.25 * iv_rank +
            0.25 * position_rank +
            0.20 * time_value_rank
        )
        
        print(f"质量因子 = 30%×{return_rank:.1f} + 25%×{iv_rank:.1f} + 25%×{position_rank:.1f} + 20%×{time_value_rank:.1f} = {quality_score:.2f}")
        
        results[symbol] = {
            'quality_score': quality_score,
            'return_rank': return_rank,
            'iv_rank': iv_rank,
            'position_rank': position_rank,
            'time_value_rank': time_value_rank
        }
    
    print("\n4. 最终排名结果:")
    print("-" * 60)
    sorted_results = sorted(results.items(), key=lambda x: x[1]['quality_score'], reverse=True)
    
    for rank, (symbol, data) in enumerate(sorted_results, 1):
        print(f"{rank}. {symbol}: {data['quality_score']:.2f}分")
        print(f"   └─ 年化收益:{data['return_rank']:.0f} | IV:{data['iv_rank']:.0f} | 位置:{data['position_rank']:.0f} | 时间价值:{data['time_value_rank']:.0f}")
    
    return results


def compare_with_hardcoded():
    """对比硬编码封顶线 vs 分位数排名"""
    
    print("\n" + "=" * 80)
    print("硬编码封顶线 vs 分位数排名对比")
    print("=" * 80)
    
    # 示例数据
    test_cases = [
        {
            'name': '正常市场环境',
            'stocks': {
                'A': {'return': 0.25, 'iv': 0.30},
                'B': {'return': 0.35, 'iv': 0.45},
                'C': {'return': 0.45, 'iv': 0.60},
                'D': {'return': 0.55, 'iv': 0.75}
            }
        },
        {
            'name': '高波动环境',
            'stocks': {
                'A': {'return': 0.60, 'iv': 0.80},
                'B': {'return': 0.75, 'iv': 0.95},
                'C': {'return': 0.90, 'iv': 1.10},
                'D': {'return': 1.05, 'iv': 1.25}
            }
        }
    ]
    
    for case in test_cases:
        print(f"\n### {case['name']} ###")
        print("股票\t年化收益\tIV\t硬编码得分\t分位数得分")
        print("-" * 70)
        
        symbols = list(case['stocks'].keys())
        returns = [case['stocks'][s]['return'] for s in symbols]
        ivs = [case['stocks'][s]['iv'] for s in symbols]
        
        for i, symbol in enumerate(symbols):
            ret = returns[i]
            iv = ivs[i]
            
            # 硬编码方式
            hardcoded_return = min(ret / 0.50 * 100, 100)
            hardcoded_iv = min(iv / 0.60 * 100, 100)
            hardcoded_total = (hardcoded_return + hardcoded_iv) / 2
            
            # 分位数方式
            percentile_return = (sorted(returns).index(ret) + 1) / len(returns) * 100
            percentile_iv = (sorted(ivs).index(iv) + 1) / len(ivs) * 100
            percentile_total = (percentile_return + percentile_iv) / 2
            
            print(f"{symbol}\t{ret:.1%}\t\t{iv:.1%}\t{hardcoded_total:.1f}\t\t{percentile_total:.1f}")
    
    print("\n📊 对比结论:")
    print("• 硬编码方式：在高波动环境下会出现大量满分，失去区分度")
    print("• 分位数方式：始终保持相对排名，具有良好的区分度")
    print("• 分位数方式能自动适应不同的市场环境")


def advanced_percentile_methods():
    """展示更高级的分位数方法"""
    
    print("\n" + "=" * 80)
    print("高级分位数方法")
    print("=" * 80)
    
    import numpy as np
    
    # 示例数据
    values = [0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95]
    
    print("原始数据:", values)
    print()
    
    # 方法1：简单排名
    print("方法1: 简单排名 (Rank)")
    for i, val in enumerate(values):
        rank = sorted(values).index(val) + 1
        rank_score = rank / len(values) * 100
        print(f"  {val:.2f} → 排名{rank} → 得分{rank_score:.1f}")
    
    print()
    
    # 方法2：百分位数
    print("方法2: 百分位数 (Percentile)")
    for val in values:
        percentile = (np.array(values) <= val).sum() / len(values) * 100
        print(f"  {val:.2f} → {percentile:.1f}百分位")
    
    print()
    
    # 方法3：四分位数分组
    print("方法3: 四分位数分组")
    q1, q2, q3 = np.percentile(values, [25, 50, 75])
    print(f"  Q1 (25%): {q1:.2f}")
    print(f"  Q2 (50%): {q2:.2f}") 
    print(f"  Q3 (75%): {q3:.2f}")
    
    for val in values:
        if val <= q1:
            group = "低分组 (25分)"
        elif val <= q2:
            group = "中低分组 (50分)"
        elif val <= q3:
            group = "中高分组 (75分)"
        else:
            group = "高分组 (100分)"
        print(f"  {val:.2f} → {group}")


if __name__ == "__main__":
    # 运行演示
    percentile_rank_demo()
    compare_with_hardcoded()
    advanced_percentile_methods()
    
    print("\n" + "=" * 80)
    print("总结：分位数排名法的优势")
    print("=" * 80)
    print("✅ 无硬编码参数：不需要设定任何封顶线")
    print("✅ 自动适应：能适应不同的股票池和市场环境")
    print("✅ 相对公平：基于池内相对表现，而非绝对标准")
    print("✅ 区分度好：始终能区分出高中低表现")
    print("✅ 易于理解：排名概念直观易懂")