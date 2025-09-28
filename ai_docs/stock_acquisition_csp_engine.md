# Reference Implementation of Stock Acquisition CSP Engine MCP Server Prompt

```python
"""
🏗️ Stock Building CSP Engine - Stock Acquisition Cash-Secured Put Engine prompt for Options Trading Toolkit.

SELECTION GUIDANCE:
=================
Use this prompt when the user wants to:
✅ BUILD STOCK POSITIONS as the PRIMARY goal
✅ ACQUIRE quality shares at DISCOUNT prices through assignment
✅ WELCOME stock assignment - ownership is desired outcome
✅ Long-term equity accumulation (21-60+ days typical)
✅ Focus on in-the-money/at-the-money puts with higher Delta (0.30-0.50)
✅ Lower annualized returns (15-35%) but effective stock acquisition

Keywords that indicate this prompt:
- "build position", "acquire stock", "get assigned"
- "own shares", "build up position", "stock accumulation"
- "discount entry", "value investing", "long-term holdings"
- "I want the stock", "assignment welcome", "equity building"

DO NOT USE when user wants to:
❌ Pure income generation from option premiums
❌ Avoid stock ownership/assignment
❌ High-yield quick turnover strategies
❌ Premium collection as primary objective
"""

from ..modules.utils.task_progress_tracker import STOCK_ACQUISITION_STEPS, TaskProgressTracker

# Default high-quality stocks suitable for CSP stock acquisition strategy
DEFAULT_TICKERS = ["TSLA", "GOOGL", "NVDA", "META", "MSFT", "AMZN", "AAPL"]


async def stock_acquisition_csp_engine(
    tickers: list | None,
    cash_usd: float,
    target_allocation_probability: float = 65.0,
    max_single_position_pct: float = 25.0,
    min_days: int = 21,
    max_days: int = 60,
    target_annual_return_pct: float = 25.0,
    preferred_sectors: list | None = None,
) -> str:
    """Generate a comprehensive stock acquisition strategy using cash-secured puts to build equity positions at discount prices."""

    # Use user-provided tickers or default high-quality CSP candidates
    target_tickers = tickers if tickers else DEFAULT_TICKERS
    tickers_str = ", ".join(target_tickers)
    sectors_str = (
        ", ".join(preferred_sectors) if preferred_sectors else "Technology, Healthcare, Consumer Discretionary"
    )
    max_position_size = cash_usd * (max_single_position_pct / 100.0)

    # Initialize progress tracker
    tracker = TaskProgressTracker("股票建仓CSP引擎", STOCK_ACQUISITION_STEPS)

    # Generate the main report content with LIVE progress tracking
    report_content = f"""# 🎯 股票建仓现金担保PUT引擎

## 🔄 实时进度跟踪
**注意**: 以下进度跟踪器将在分析过程中实时更新。请在每个步骤执行后主动调用相应的进度更新方法。

```python
# 进度跟踪器初始化（在分析开始时执行一次）
from datetime import datetime
import sys
import os
sys.path.append('/Users/szou/Python/Playground/MCP4Claude')
from src.mcp_server_options.modules.utils.task_progress_tracker import TaskProgressTracker, STOCK_ACQUISITION_STEPS

# 创建实时跟踪器实例
live_tracker = TaskProgressTracker("🏗️ {target_tickers[0] if target_tickers else 'STOCK'} 股票建仓CSP引擎", STOCK_ACQUISITION_STEPS)
print("📊 🍎 股票建仓分析开始...")
print(live_tracker.get_progress_summary())
```

{tracker.get_progress_summary()}

## 战略目标与约束
- **核心目标**: 以折扣价获得优质股票仓位，权利金收益为次要考虑
- **标的池**: {tickers_str}
- **投资资金**: ${cash_usd:,.0f}
- **分配目标概率**: {target_allocation_probability}%（期望被分配股票）
- **单股仓位限制**: {max_single_position_pct}%（最大${max_position_size:,.0f}）
- **到期窗口**: {min_days}~{max_days}天（给股价调整充足时间）
- **年化收益补偿**: ≥{target_annual_return_pct}%（合理的等待成本）
- **偏好行业**: {sectors_str}

## ⚠️ CRITICAL: 时间基准验证要求
**股票建仓策略对时间极度敏感！必须严格遵循以下时间验证协议：**

### 强制性时间验证步骤
1. **首先调用时间基准工具**：`get_current_us_east_datetime_tool()`
2. **验证日期合理性**：确保返回的日期是当前有效日期（检查年份≥当前年，月份1-12，日期合理）
3. **声明时间基准**：在所有后续分析中明确引用步骤1获得的准确时间
4. **期权到期日验证**：确保所有期权到期日期晚于当前日期
5. **财报窗口检查**：避免在财报前7天内建仓（降低事件风险）

## 股票建仓策略核心理念

### 与传统CSP收益策略的差异
| 策略维度 | 传统CSP收益引擎 | 股票建仓CSP引擎 |
|----------|-----------------|-----------------|
| **主要目标** | 收取权利金，避免分配 | 期望分配，获得股票 |
| **Delta选择** | 0.10~0.30（低概率） | 0.30~0.50（高概率） |
| **年化目标** | ≥50%（激进） | 15~35%（合理补偿） |
| **持仓期间** | 7~28天（快周转） | 21~60天（耐心等待） |
| **股票筛选** | 高IV，流动性优先 | 基本面优质，估值合理 |
| **分配态度** | 尽量避免 | 积极欢迎 |

### 建仓逻辑核心原则
1. **价值导向**：只对基本面健康、估值合理的股票建仓
2. **技术确认**：选择接近技术支撑位的进入点
3. **分散风险**：单个股票仓位控制在总资金的{max_single_position_pct}%以内
4. **耐心等待**：给股价充分调整时间，避免过度频繁操作

## 必需工具执行顺序

### 阶段一: 时间基准与市场环境验证 🕐
```python
# 🔄 STEP 1: 时间基准验证 - LIVE进度跟踪
print("\\n" + "="*50)
print("🕐 开始步骤1: 时间基准验证")
print(live_tracker.start_step(0))

# 执行实际工具调用
current_time_info = get_current_us_east_datetime_tool()
# 验证：确保返回的日期合理（年份≥当前年，日期格式正确），如异常则立即报错

# 🎯 实时进度更新
print(live_tracker.complete_step(0, f"时间基准验证完成: {{current_time_info['current_datetime']['date']}}"))
print(live_tracker.get_progress_summary())

# STEP 2: 市场整体环境评估与前景分析 🌍
# 重要：使用新的量化市场前景评估工具替代主观判断
market_outlook = assess_market_outlook_tool(
    primary_symbol="{target_tickers[0]}" if target_tickers else "SPY",
    benchmark_symbols=["SPY", "QQQ", "VIX"],
    lookback_days=30,
    sector_analysis=True,
    include_sentiment=True
)
# {tracker.complete_step(1, "市场前景评估完成")}

get_asset_info_tool(symbol="SPY")  # 市场基准确认
get_asset_info_tool(symbol="QQQ")  # 科技股基准
get_historical_data_tool(symbol="SPY", timeframe="1Day", days=252)
calculate_technical_indicators_tool(symbol="SPY", indicators=["RSI", "ATR", "SMA", "BOLLINGER"])
```

### 阶段二: 候选股票基本面与技术面分析 📊 ({tracker.start_step(2)})
```python
for ticker in {target_tickers[:4]}:  # 限制前4个标的优化性能
    # 基础信息获取
    get_asset_info_tool(symbol=ticker)  # {tracker.complete_step(2, "技术分析完成")}
    get_historical_data_tool(symbol=ticker, timeframe="1Day", days=504)  # 2年历史数据

    # 技术指标分析（重点关注估值和趋势）
    calculate_technical_indicators_tool(
        symbol=ticker,
        indicators=["RSI", "ATR", "SMA", "EMA", "BOLLINGER", "SUPPORT_RESISTANCE"],
        period_days=252  # 1年期技术分析
    )

    # 财报日历检查（避免事件风险）
    get_earnings_calendar_tool(symbol=ticker)
    # CRITICAL: 确保下个财报日期 > 当前日期 + 7天
```

### 阶段三: 期权链分析与Delta目标筛选 🎯 ({tracker.start_step(3)})
```python
# 基于步骤1的准确时间基准进行期权分析
for ticker in qualified_tickers:
    get_option_chain_tool(
        symbol=ticker,
        min_expiration_days={min_days},
        max_expiration_days={max_days},
        strike_range=0.25  # 扩大范围以包含0.30~0.50 Delta区域
    )

    # CRITICAL: 验证期权到期日期
    # 确保所有期权expiration_date > current_time_info['current_datetime']['date']
    # 确保期权到期日期 > 下个财报日期（避免财报事件风险）
```

### 阶段四: Greeks计算与建仓参数优化 🔬
```python
# 专注于ITM和ATM附近的PUT期权（Delta 0.30~0.50）
calculate_greeks_tool(
    option_price=[候选期权的mid价格],
    underlying_price=[当前股价],
    strike_price=[目标行权价格],
    days_to_expiry=[实际到期天数],
    option_type="put",
    risk_free_rate=0.045  # 当前Fed Rate
)

# 组合风险分析
calculate_risk_tool(
    strategy_legs=[
        {{
            "action": "sell",
            "option_type": "put",
            "strike": target_strike,
            "expiration": target_expiry,
            "quantity": suggested_contracts
        }}
    ],
    underlying_price=[当前价格]
)
```

### 阶段五: 股票建仓策略构建 🏗️
```python
# 主策略：轮式策略（以建仓为目标）
csp_wheel_result = construct_wheel_strategy_tool(
    symbol=best_ticker,
    buying_power_limit={max_position_size},
    delta_range_min=-0.50,  # 更激进的Delta范围
    delta_range_max=-0.30,  # 目标：30-50%分配概率
    oi_threshold=300,
    risk_free_rate=0.045
)

# 评估策略是否符合建仓目标
assignment_probability = abs(csp_wheel_result['recommended_delta'])
if assignment_probability >= {target_allocation_probability/100.0}:
    proceed_with_csp = True
    strategy_type = "stock_acquisition_csp"
else:
    # 如果分配概率不足，考虑调整参数或选择其他标的
    proceed_with_csp = False
    strategy_type = "alternative_strategy"
```

### 阶段六: 精确PnL验证与建仓分析 🎯 (数学精确计算)
```python
# 主要策略验证：现金担保PUT
analyze_option_strategy_tool(
    strategy_type="cash_secured_put",
    underlying_symbol=best_ticker,
    underlying_price=[步骤2获得的股价],
    strike=[步骤5获得的行权价],
    put_premium=[步骤5获得的权利金],
    contracts=[步骤5建议的张数],
    expiration_days=[实际到期天数],
    include_scenarios=True,
    include_position_sizing=True,
    total_capital={cash_usd},
    max_risk_pct=0.30  # 允许更高风险敞口用于建仓
)

# 分配后管理策略预演
if proceed_with_csp:
    # 模拟分配后的备兑看涨策略
    analyze_option_strategy_tool(
        strategy_type="covered_call",
        underlying_symbol=best_ticker,
        underlying_price=[行权价作为成本基础],
        strike=[行权价+5~10%作为CC target],
        call_premium=[预估CC权利金],
        contracts=[相同张数],
        include_scenarios=True
    )
```

### 阶段七: 基本面价值评估与风险检查 📈
```python
# 获取更多基本面数据用于价值判断
get_historical_data_tool(
    symbol=best_ticker,
    timeframe="1Day",
    days=1260,  # 5年历史数据
    include_records=True,
    max_records=1260
)

# 多维度技术分析确认
calculate_technical_indicators_tool(
    symbol=best_ticker,
    indicators=["RSI", "MACD", "BOLLINGER", "ATR", "SMA", "EMA", "SUPPORT_RESISTANCE", "PIVOT"],
    period_days=504,  # 2年期综合分析
    sma_period=50,
    ema_period=200
)
```

### 阶段八: 策略推荐与风险管理建议 🚀
```python
# 智能策略推荐系统验证（基于量化市场前景分析）
recommend_option_strategies_tool(
    underlying_price=[当前股价],
    market_outlook=market_outlook['market_outlook'],  # 使用量化评估结果
    volatility_outlook=market_outlook['volatility_outlook'],  # 动态波动预期
    capital_available={max_position_size},
    risk_tolerance="moderate_aggressive"  # 建仓需要承担更多风险
)

# 策略类型确认
identify_option_strategy_tool(
    legs=[
        {{
            "action": "sell",
            "option_type": "put",
            "strike": recommended_strike,
            "expiration": recommended_expiry,
            "premium": recommended_premium,
            "quantity": recommended_contracts
        }}
    ]
)
```

## 🎯 股票筛选与评估标准

### 一级筛选：基本面健康度
- **财务健康**：ROE ≥ 15%，负债率 ≤ 40%，现金流为正
- **盈利稳定性**：近5年连续盈利，增长率 ≥ 5%
- **市场地位**：行业前5，市值 ≥ 500亿美元
- **分红历史**：稳定分红记录（可选加分项）

### 二级筛选：估值合理性
- **PE估值**：当前PE ≤ 5年平均PE × 1.2
- **PB估值**：PB ≤ 行业平均 × 1.5
- **PEG比率**：PEG ≤ 1.5（成长性与估值平衡）
- **相对估值**：与同行业龙头对比不过度溢价

### 三级筛选：技术面确认
- **趋势位置**：股价接近50日或200日均线支撑
- **RSI水平**：30 ≤ RSI ≤ 65（避免超买超卖极端）
- **成交量确认**：近期成交量正常，无异常放量下跌
- **支撑位强度**：目标行权价接近关键技术支撑位

### 四级评分：建仓优先级
1. **分配概率** (40%权重)：
   - 目标Delta 0.35~0.45为满分
   - 历史波动率支持的分配概率
   - 技术支撑位强度修正

2. **价值折扣** (35%权重)：
   - 行权价相对当前价格的折扣幅度
   - 相对内在价值的安全边际
   - 预期分配成本的吸引力

3. **基本面质量** (25%权重)：
   - 财务健康度评分
   - 长期成长前景
   - 行业竞争优势

## 📊 输出规格

### 🕐 强制性时间基准声明
**所有股票建仓分析必须明确声明时间基准**：
- \"**分析基准时间**: [从get_current_us_east_datetime_tool()获得的完整时间]\"
- \"**当前日期**: [YYYY-MM-DD格式]\"
- \"**时间验证状态**: ✅ 已验证日期格式和合理性\"
- \"**财报窗口检查**: [下个财报日期] (距今X天，安全状态)\"

### 🎯 专业报告生成 (NEW)
**重要**: 所有股票建仓分析将自动生成专业Markdown报告，包含：
- **动态数据驱动**: 基于实际分析结果的真实数据
- **完整报告结构**: 执行摘要、技术分析、策略详情、风险评估、执行建议
- **专业格式**: 包含表格、图表、风险指标等专业元素
- **保存位置**: reports目录下，文件名格式：[SYMBOL]_CSP_Strategy_Report_[TIMESTAMP].md
- **替代说明**: 本功能已替代原有的简单模板保存方式，提供真正有价值的分析报告

### 候选建仓策略对比表
| 标的 | 当前价 | 目标行权价 | 有效折扣 | 权利金 | 分配概率 | 年化补偿 | 基本面评级 | 最大仓位 | 财报距离 | 推荐度 |
|------|--------|------------|----------|--------|----------|----------|------------|----------|----------|---------|
| {target_tickers[0]} | $XXX.XX | $XXX.XX | X.X% | $X.XX | XX% | XX.X% | A+/A/B | $XX,XXX | XX天 | ⭐⭐⭐⭐⭐ |

### 股票建仓执行方案

**📍 推荐建仓策略**
**标的**: [股票代码] - [公司名称]
**建仓方式**: Cash-Secured Put @ $[行权价] 到期 [日期]
**配置**: [张数]张 × $[权利金] = $[总收入]
**有效成本**: $[行权价 - 权利金] ([相对当前价X.X%折扣])
**分配概率**: [XX]% | **年化补偿**: [XX.X]% | **最大占用**: $[金额]

### 基本面投资价值分析
**财务健康度**: ROE [XX]% | 负债率 [XX]% | 现金流 $[金额]B
**估值吸引力**: PE [XX.X]x (5年均值[XX.X]x) | PB [X.X]x | PEG [X.X]
**行业地位**: [行业] 第[X]位 | 市值 $[XXX]B | 护城河评级 [A/B/C]
**技术位置**: 距50日均线[±X.X]% | RSI [XX] | 支撑位$[XXX] (强度[高/中/低])

### 建仓后管理剧本 📋

**🎯 分配预期管理** (分配概率{target_allocation_probability}%)：
- **分配欢迎条件**: 基本面无重大变化，估值依然吸引
- **平均成本**: $[行权价-权利金] vs 当前价$[当前价]
- **备兑看涨计划**: 月度CC @ $[目标价格] (成本基础上涨8~12%)
- **长期持股目标**: [1~3年] 持有期，目标总回报[15~25]%

**⚡ 权利金收取管理** (概率{100-target_allocation_probability}%)：
- **平仓时机**: 权利金衰减70%或剩余7天到期
- **滚动策略**: 延长到期至下月同行权价或降低行权价5%
- **再次建仓**: 等待技术回调至新的支撑位重新评估

**🛡️ 风险控制触发器**：
- **基本面恶化**: ROE下降30%或负债率超50%立即平仓
- **技术破位**: 跌破关键支撑位5%评估是否接受分配
- **市场环境**: VIX > 35或市场恐慌时暂停新建仓
- **组合风险**: 单股占比超{max_single_position_pct+5}%时强制减仓

### 风险声明与投资建议 ⚠️

**风险提示**：
- 股票建仓策略优先考虑获得股票而非短期收益
- 需要充足资金承受股票分配和潜在浮亏
- 建议仓位控制在总投资组合的50-70%以内
- 需要长期投资视角，不适合纯短线交易者

**适合投资者类型**：
- 长期价值投资导向
- 对选定股票有充分研究和信心
- 有足够现金流应对分配
- 能够承受股票价格波动

## 📋 复现执行清单

```bash
# 阶段一: 时间基准与市场环境 (CRITICAL)
1. get_current_us_east_datetime_tool()
2. get_asset_info_tool(symbol="SPY")
3. get_asset_info_tool(symbol="QQQ")

# 阶段二: 候选股票分析
4. get_asset_info_tool(symbol="{target_tickers[0]}")
5. get_historical_data_tool(symbol="{target_tickers[0]}", timeframe="1Day", days=504)
6. calculate_technical_indicators_tool(symbol="{target_tickers[0]}", indicators=["RSI", "SMA", "EMA", "BOLLINGER", "SUPPORT_RESISTANCE"])
7. get_earnings_calendar_tool(symbol="{target_tickers[0]}")

# 阶段三: 期权链与Delta分析
8. get_option_chain_tool(symbol="{target_tickers[0]}", min_expiration_days={min_days}, max_expiration_days={max_days}, strike_range=0.25)
9. calculate_greeks_tool(option_price=[从步骤8获得], underlying_price=[从步骤4获得], strike_price=[目标ITM行权价], days_to_expiry=[实际天数], option_type="put")

# 阶段四: 建仓策略构建
10. construct_wheel_strategy_tool(symbol="{target_tickers[0]}", buying_power_limit={max_position_size}, delta_range_min=-0.50, delta_range_max=-0.30)

# 阶段五: 精确PnL验证 🎯
11. analyze_option_strategy_tool(strategy_type="cash_secured_put", underlying_symbol="{target_tickers[0]}", underlying_price=[步骤4获得], strike=[步骤10推荐], put_premium=[步骤10获得], contracts=[建议张数], include_scenarios=true, include_position_sizing=true, total_capital={cash_usd}, max_risk_pct=0.30)

# 阶段六: 分配后策略预演
12. analyze_option_strategy_tool(strategy_type="covered_call", underlying_symbol="{target_tickers[0]}", underlying_price=[行权价], strike=[行权价+8%], call_premium=[预估值], contracts=[相同张数])

# 阶段七: 策略推荐验证 🚀
13. recommend_option_strategies_tool(underlying_price=[步骤4获得], market_outlook=market_outlook['market_outlook'], volatility_outlook=market_outlook['volatility_outlook'], capital_available={max_position_size}, risk_tolerance="moderate_aggressive")

# 阶段八: 数据导出与记录
14. export_historical_csv_tool(symbol="{target_tickers[0]}", days=1260, output_dir="stock_acquisition_analysis")

# 阶段九: 专业报告生成 🎯
15. generate_strategy_report_tool(symbol="{target_tickers[0]}", current_price=[步骤4获得], technical_data=[步骤6的JSON结果], strategy_data=[步骤10的JSON结果], risk_data=[步骤11的JSON结果], strategy_type="cash_secured_put", capital={cash_usd}, output_dir="reports")

# 重要说明：步骤15的数据传递
# - technical_data: 来自步骤6 calculate_technical_indicators_tool的完整输出
# - strategy_data: 来自步骤10 construct_wheel_strategy_tool的完整输出
# - risk_data: 来自步骤11 analyze_option_strategy_tool的完整输出
# - MCP工具会自动处理JSON字符串到Dict对象的转换
```

---

## 🎯 期望输出示例

### 最终推荐
**🎯 Top 1 股票建仓策略**: AAPL @ $165.00 到期 2024-03-15
- **建仓配置**: 6张CSP × $4.20权利金 = $2,520总收入
- **有效成本**: $160.80 (较当前价$168.50折扣4.6%)
- **分配概率**: 68% | **年化补偿**: 28.5% | **资金占用**: $99,000
- **基本面**: A+评级 (ROE 28%, PE 24.5x合理, 现金$165B健康)
- **管理**: 欢迎分配→长期持股+月度CC @ $175策略

### 🔖 交易票据

**Tickets**
```text
Sell to Open AAPL240315P165000 Qty 6 Px 4.20 TIF GTC
Bundle: Net Credit 4.20; Cash Secured $99000; Target Assignment 68%; Effective Cost $160.80; TIF GTC
```

**Notes**
- 股票建仓导向：期望68%概率分配获得AAPL@$160.80成本
- 基本面优质：科技龙头+财务健康+估值合理组合
- 后续管理：分配后执行月度备兑看涨，目标年化15%总回报

---

# Begin Execution
执行上述工具序列，以{target_allocation_probability}%分配概率构建优质股票仓位，重点关注长期价值而非短期收益。

"""

    # Return the report content
    return report_content

```
