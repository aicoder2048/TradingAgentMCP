# Reference Implementation for Income Generation CSP Engine

```python
"""
🎯 Premium Income CSP Engine - Cash-Secured Put Yield Engine prompt for Options Trading Toolkit.

SELECTION GUIDANCE:
=================
Use this prompt when the user wants to:
✅ Collect option premium as PRIMARY income source
✅ Generate high annualized returns (≥50%) from CSP strategies
✅ AVOID stock assignment - premium collection is the goal
✅ Quick turnover strategies (7-28 days typical)
✅ Focus on out-of-the-money puts with low Delta (0.10-0.30)

Keywords that indicate this prompt:
- "generate income", "collect premium", "yield from options"
- "avoid assignment", "don't want the stock", "premium income"
- "high return CSP", "income strategy", "option yield"

DO NOT USE when user wants to:
❌ Build stock positions or "acquire shares at discount"
❌ Get assigned stock ownership
❌ "Build up position" in a company
❌ Long-term equity accumulation strategies
"""

from ..modules.utils.task_progress_tracker import CSP_YIELD_ENGINE_STEPS, TaskProgressTracker


async def cash_secured_put_yield_engine(
    tickers: list,
    cash_usd: float,
    min_days: int = 7,
    max_days: int = 28,
    target_apy_pct: float = 50,
    min_winrate_pct: float = 70,
    confidence_pct: float = 90,
) -> str:
    """Generate a comprehensive cash-secured put yield engine with high probability income strategies."""

    tickers_str = ", ".join(tickers) if tickers else "SPY, QQQ, AAPL, MSFT, NVDA"

    # Initialize progress tracker
    tracker = TaskProgressTracker("现金担保PUT收益引擎", CSP_YIELD_ENGINE_STEPS)

    return f"""# 💵 现金担保 PUT 收益引擎

## 🔄 实时进度跟踪
**重要**: 以下包含可执行的实时进度跟踪代码。在执行每个步骤时，请运行相应的进度更新命令来显示实时进度。

```python
# 进度跟踪器实时初始化
from datetime import datetime
import sys, os
sys.path.append('/Users/szou/Python/Playground/MCP4Claude')
from src.mcp_server_options.modules.utils.task_progress_tracker import TaskProgressTracker, CSP_YIELD_ENGINE_STEPS

# 创建实时跟踪器
live_tracker = TaskProgressTracker("💵 CSP收益引擎 - {tickers_str.split(',')[0].strip() if tickers_str else 'SPY'}", CSP_YIELD_ENGINE_STEPS)
print("🎯 CSP收益策略分析开始...")
print(live_tracker.get_progress_summary())
```

{tracker.get_progress_summary()}

## 约束与目标
- **标的池**: {tickers_str}
- **资金**: ${cash_usd:,.0f}
- **到期窗口**: {min_days}~{max_days} 天
- **收益目标**: 年化≥{target_apy_pct}%、胜率≥{min_winrate_pct}%、统计置信度≥{confidence_pct}%

## ⚠️ CRITICAL: 时间基准验证要求
**期权分析对时间极度敏感！必须严格遵循以下时间验证协议：**

### 强制性时间验证步骤
1. **首先调用时间基准工具**：`get_current_us_east_datetime_tool()`
2. **验证日期合理性**：确保返回的日期是当前有效日期（检查年份≥当前年，月份1-12，日期合理）
3. **声明时间基准**：在所有后续分析中明确引用步骤1获得的准确时间
4. **期权到期日验证**：确保所有期权到期日期晚于当前日期

## 必需工具执行顺序

**执行前请注意**: 每完成一个步骤后，使用以下格式更新进度：
```
# 开始步骤
{tracker.start_step(0)}  # 步骤索引从0开始

# 完成步骤
{tracker.complete_step(0, "步骤执行结果")}  # 第0步：时间验证
```

1) **步骤1: 时间基准验证** - 实时跟踪版:
   ```python
   # 🔄 STEP 1: CRITICAL时间基准验证 - 实时进度跟踪
   print("\\n" + "="*60)
   print("🕐 开始执行: 时间基准验证")
   print(live_tracker.start_step(0))

   # 执行实际工具调用
   current_time_info = get_current_us_east_datetime_tool()
   # 验证：确保返回的日期合理（年份≥当前年，日期格式正确），如异常则立即报错

   # 🎯 实时进度完成更新
   print(live_tracker.complete_step(0, f"时间基准: {{current_time_info['current_datetime']['date']}}"))
   print("\\n📊 当前进度状态:")
   print(live_tracker.get_progress_summary())
   ```

2) **步骤2-4: 市场基础数据获取**（并行执行所有标的）:
   ```
   # {tracker.start_step(1)} - 获取资产信息

   for ticker in {tickers_str.split(', ')[:3]}:  # 限制前3个标的以优化性能
       get_asset_info_tool(symbol=ticker)  # {tracker.complete_step(1, "资产信息获取完成")}
       get_historical_data_tool(symbol=ticker, timeframe="1Day", days=252)  # {tracker.complete_step(2, "历史数据获取完成")}
       calculate_technical_indicators_tool(symbol=ticker, indicators=["ATR", "BOLLINGER", "RSI", "SUPPORT_RESISTANCE"])  # {tracker.complete_step(3, "技术指标计算完成")}
   ```

3) **步骤5: 期权链筛选与分析** ({tracker.start_step(4)}) - 基于步骤1的准确时间基准:
   ```
   for ticker in qualified_tickers:
       get_option_chain_tool(symbol=ticker,
                            min_expiration_days={min_days},
                            max_expiration_days={max_days},
                            strike_range=0.15)  # 聚焦OTM Put区域

   # CRITICAL: 验证期权到期日期
   # 确保所有期权expiration_date > current_time_info['current_datetime']['date']
   # 如发现到期日期早于或等于当前日期，立即报错并停止分析
   # 完成后：{tracker.complete_step(4, "期权链分析完成")}
   ```

4) **步骤6: 希腊字母计算与风险评估** ({tracker.start_step(5)}):
   ```
   calculate_greeks_tool(contracts=otm_put_candidates)  # 关注Delta 0.10~0.30范围
   calculate_risk_tool(strategy_legs=cash_secured_put_candidates, scenarios=["历史波动回测", "压力测试", "最大回撤"])
   # 完成后：{tracker.complete_step(5, "Greeks计算完成")}
   ```

5) **步骤7: 策略构建与优化** ({tracker.start_step(6)}):
   ```
   # 尝试构建CSP策略
   csp_result = construct_wheel_strategy_tool(symbol=best_ticker, delta_range_min=-0.30, delta_range_max=-0.10)

   # 评估CSP是否满足要求
   if csp_meets_requirements(csp_result, target_apy={target_apy_pct}, min_winrate={min_winrate_pct}):
       # CSP符合条件，继续验证
       proceed_with_csp = True
   else:
       # CSP不符合条件，尝试备选策略
       construct_bull_put_spread_tool(symbol=ticker, target_profit_percentage=0.50)
       proceed_with_csp = False
   # 完成后：{tracker.complete_step(6, "策略构建完成")}
   ```

6) **步骤8: 风险分析** ({tracker.start_step(7)}) 和 **步骤9: 精确PnL验证** ({tracker.start_step(8)}) 🎯:
   ```
   analyze_option_strategy_tool(strategy_type="cash_secured_put", underlying_symbol=ticker, underlying_price=[步骤2获得], strike=[步骤7获得的行权价], put_premium=[步骤7获得的权利金], contracts=[步骤7建议的张数], include_scenarios=true, include_position_sizing=true, total_capital={cash_usd}, max_risk_pct=0.05)
   # {tracker.complete_step(7, "风险分析完成")} 然后 {tracker.complete_step(8, "PnL验证完成")}

   analyze_option_strategy_tool(strategy_type="bull_put_spread", underlying_symbol=ticker, underlying_price=[步骤2获得], short_strike=[步骤7获得], long_strike=[步骤7获得], short_premium=[步骤7获得], long_premium=[步骤7获得], contracts=[步骤7建议], include_scenarios=true, include_position_sizing=true, total_capital={cash_usd})
   ```

7) **步骤10: 备选策略评估** ({tracker.start_step(9)}) 🚀 (条件性执行):
   ```
   # 仅当CSP不满足条件时，寻找替代策略
   if not proceed_with_csp:
       print("CSP策略不满足收益/风险要求，寻找替代方案...")
       alternatives = recommend_option_strategies_tool(
           underlying_price=[步骤2获得],
           market_outlook=market_outlook['market_outlook'],  # 使用量化评估结果
           volatility_outlook=market_outlook['volatility_outlook'],  # 动态波动预期
           capital_available={cash_usd},
           risk_tolerance="moderate"
       )
       # 从推荐中选择最优策略并验证
       selected_strategy = select_best_alternative(alternatives)
       analyze_option_strategy_tool(strategy_type=selected_strategy.type, ...)
   # 完成后：{tracker.complete_step(9, "备选策略评估完成")}
   ```

## 🎯 筛选与排名标准

### 一级筛选 - 基础门槛
- **流动性**: Bid-Ask价差 ≤ 权利金的10%，OI ≥ 500，Volume ≥ 50
- **Delta范围**: 0.10 ≤ |Delta| ≤ 0.30（优先0.15~0.25）
- **技术支撑**: 行权价位于关键支撑位下方5~15%
- **IV等级**: IV Rank ≥ 30百分位（避免过低波动率环境）

### 二级评分 - 效率优化
1. **年化收益率** (40%权重):
   - 计算公式: (权利金/现金占用) × (365/到期天数) × 100%
   - 目标: ≥{target_apy_pct}% 满分，递减评分

2. **胜率估计** (35%权重):
   - 历史回测: 过去252天内跌破行权价的概率
   - Delta近似: 以当前Delta作为理论到期胜率
   - 技术面确认: RSI、支撑位强度修正
   - 目标: ≥{min_winrate_pct}% 满分

3. **风险调整收益** (25%权重):
   - 夏普比率修正: 收益率/最大历史回撤
   - 凯利公式: f* = (bp - q)/b，其中b=收益率，p=胜率
   - VaR @ {confidence_pct}%置信度

## 📊 输出规格

### 🕐 强制性时间基准声明
**所有分析必须明确声明时间基准**：
- "**分析基准时间**: [从get_current_us_east_datetime_tool()获得的完整时间]"
- "**当前日期**: [YYYY-MM-DD格式]"
- "**时间验证状态**: ✅ 已验证日期格式和合理性"

### 候选策略对比表
| 标的 | 到期日 | 行权价 | 权利金 | 张数 | 现金占用 | 年化收益 | 估计胜率 | 安全边际 | 最大风险 | 流动性评分 |
|------|--------|--------|--------|------|----------|----------|----------|----------|----------|-----------|
| {tickers_str.split(', ')[0] if tickers else 'SPY'} | YYYY-MM-DD | $XXX | $X.XX | XXX | $XXX,XXX | XX.X% | XX.X% | XX.X% | $XXX,XXX | A/B/C |

### 管理剧本与风控
**开仓条件确认**:
- [ ] IV Rank > 30百分位
- [ ] 技术面确认支撑位有效
- [ ] 距离财报日期 > 7天（避免事件风险）
- [ ] 市场VIX < 30（避免高波动环境）

**持仓期管理触发器**:
- **获利了结**: 权利金回落50%时考虑平仓
- **滚动调整**: Delta漂移至-0.35时滚动至下月或更低行权价
- **止损线**: 标的跌破行权价超过5%时评估是否接受股票分配
- **加仓机会**: 若其他高质量标的出现更优参数时重新配置

**轮式策略整合**:
- 若被分配股票，立即评估Covered Call加轮策略
- 目标: 通过备兑看涨将成本基础降至行权价-85%
- 滚动管理: 结合技术分析择时进出

## ⚠️ 风险与降级处理

### 失败路径处理
- **无符合标的**: 降低目标年化至35%或延长到期至35~45天
- **流动性不足**: 扩大Bid-Ask容忍度至15%或减少仓位规模
- **波动率异常**: 使用HV+ATR替代IV进行胜率估算
- **支撑位不明**: 改用百分位数法（如20日低点下方10%）

### 市场环境适应
- **牛市**: 优选高贝塔成长股，Delta偏向-0.20~-0.25
- **熊市**: 优选防御性标的，Delta偏向-0.10~-0.15
- **震荡市**: 聚焦高IV标的，频繁滚动获取时间价值

## 📋 复现执行清单

**注意**: 执行每个步骤时需要相应地更新进度跟踪器

```bash
# 第一阶段: 市场扫描与前景量化分析 🌍
1. get_current_us_east_datetime_tool()  # {tracker.start_step(0)} -> {tracker.complete_step(0)}
2. market_outlook = assess_market_outlook_tool(primary_symbol="{tickers_str.split(', ')[0] if tickers else 'AAPL'}", benchmark_symbols=["SPY", "QQQ", "VIX"], lookback_days=30, sector_analysis=True, include_sentiment=True)  # 量化市场前景评估 {tracker.start_step(1)}
3. get_asset_info_tool(symbol="SPY")  # 市场基准确认
4. get_asset_info_tool(symbol="{tickers_str.split(', ')[0] if tickers else 'AAPL'}")  # {tracker.complete_step(1)}
5. get_historical_data_tool(symbol="{tickers_str.split(', ')[0] if tickers else 'AAPL'}", days=252)  # {tracker.start_step(2)} -> {tracker.complete_step(2)}
6. calculate_technical_indicators_tool(symbol="{tickers_str.split(', ')[0] if tickers else 'AAPL'}", indicators=["ATR", "RSI", "BOLLINGER"])  # {tracker.start_step(3)} -> {tracker.complete_step(3)}

# 第二阶段: 期权分析
6. get_option_chain_tool(symbol="{tickers_str.split(', ')[0] if tickers else 'AAPL'}", min_expiration_days={min_days}, max_expiration_days={max_days}, strike_range=0.15)  # {tracker.start_step(4)} -> {tracker.complete_step(4)}
7. calculate_greeks_tool(contracts=[从步骤6筛选的OTM Put合约])  # {tracker.start_step(5)} -> {tracker.complete_step(5)}
8. calculate_risk_tool(strategy_legs=[cash_secured_put_candidates], underlying_price=[当前价], scenarios=["历史回测", "压力测试"])

# 第三阶段: 策略构建与评估
9. csp_result = construct_wheel_strategy_tool(symbol="{tickers_str.split(', ')[0] if tickers else 'AAPL'}", buying_power_limit={min(cash_usd * 0.8, 100000)})  # {tracker.start_step(6)}
# 评估CSP是否满足条件 (年化≥{target_apy_pct}%, 胜率≥{min_winrate_pct}%)
if csp_meets_requirements:
    10. # CSP符合条件，继续使用CSP策略  # {tracker.complete_step(6)}
else:
    10. construct_bull_put_spread_tool(symbol="{tickers_str.split(', ')[0] if tickers else 'AAPL'}", buying_power_limit={min(cash_usd * 0.6, 80000)})  # {tracker.complete_step(6)}

# 第四阶段: 精确PnL验证与风险分析 🎯
11. analyze_option_strategy_tool(strategy_type="cash_secured_put", underlying_symbol="{tickers_str.split(', ')[0] if tickers else 'AAPL'}", underlying_price=[步骤2获得], strike=[步骤9获得的行权价], put_premium=[步骤9获得的权利金], contracts=[步骤9建议的张数], include_scenarios=true, include_position_sizing=true, total_capital={cash_usd}, max_risk_pct=0.05)  # {tracker.start_step(7)} -> {tracker.complete_step(7)} -> {tracker.start_step(8)} -> {tracker.complete_step(8)}

12. analyze_option_strategy_tool(strategy_type="bull_put_spread", underlying_symbol="{tickers_str.split(', ')[0] if tickers else 'AAPL'}", underlying_price=[步骤2获得], short_strike=[步骤10获得], long_strike=[步骤10获得], short_premium=[步骤10获得], long_premium=[步骤10获得], contracts=[步骤10建议], include_scenarios=true, include_position_sizing=true, total_capital={cash_usd})

# 第五阶段: 条件性备选方案 🚀
if not csp_meets_requirements:
    13. recommend_option_strategies_tool(underlying_price=[步骤2获得], market_outlook=market_outlook['market_outlook'], volatility_outlook=market_outlook['volatility_outlook'], capital_available={cash_usd}, risk_tolerance="moderate")  # {tracker.start_step(9)}
    # 从推荐中选择替代策略
    14. analyze_option_strategy_tool(strategy_type=[选定的替代策略], ...)  # {tracker.complete_step(9)}
else:
    13. # 使用CSP策略，无需额外推荐  # {tracker.complete_step(9)}

# 第六阶段: 策略筛选与结果输出
15. # 根据所有结果进行最终筛选  # {tracker.start_step(10)} -> {tracker.complete_step(10)}
16. # 生成最终输出报告  # {tracker.start_step(11)} -> {tracker.complete_step(11)}
```

**进度监控**: 在执行过程中，使用 {tracker.get_progress_summary()} 随时查看进度状态。

---

## 🎯 期望输出

### 推荐策略
**Top 1**: [标的] Cash-Secured Put @ $[行权价] 到期 [日期]
- **配置**: [张数]张 × $[权利金] = $[总权利金收入]
- **年化**: [XX]% | **胜率**: [XX]% | **现金占用**: $[金额]
- **管理**: 50%获利平仓 | Delta > -0.35滚动 | 支撑跌破5%评估接股

### 🔖 交易票据

**Tickets**
```text
Sell to Open {tickers_str.split(', ')[0] if tickers else 'AAPL'}YYMMDDP00XXX000 Qty [N] Px [price] TIF GTC
Bundle: Net Credit [value]; Cash Secured $[amount]; APY [XX.X]%; Est Win Rate [XX]%; TIF GTC
```

**Notes**
- 现金担保PUT：优选技术支撑位下方，收取丰厚时间价值
- 目标胜率{min_winrate_pct}%基于历史回测+Delta理论值
- 触发滚动：Delta漂移或支撑跌破时主动管理

---

# Begin Execution
执行上述工具序列，生成高胜率现金担保PUT组合，确保年化收益≥{target_apy_pct}%且风险可控。
"""

```
