"""
Option Position Rebalancer Engine MCP Server Prompt

期权仓位再平衡与风险管理引擎提示生成器。
为期权交易者提供实时的仓位监控、智能决策分析和防御性策略执行能力。

核心特性：
- 实时风险监控: P&L、Greeks、被行权概率
- 智能决策支持: Hold/Close/Roll的量化评分
- 防御性策略: Calendar/Diagonal/Triple Strike Resize Roll
- 专业执行格式: Bloomberg/IEX标准订单格式
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class PositionType(str, Enum):
    """期权仓位类型"""
    SHORT_PUT = "short_put"
    SHORT_CALL = "short_call"
    LONG_PUT = "long_put"
    LONG_CALL = "long_call"


class RiskTolerance(str, Enum):
    """风险容忍度"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


async def option_position_rebalancer_engine(
    option_symbol: str,
    position_size: int,
    entry_price: float,
    position_type: str = "short_put",
    entry_date: Optional[str] = None,
    risk_tolerance: str = "moderate",
    defensive_roll_trigger_pct: float = 15.0,
    profit_target_pct: float = 70.0,
    max_additional_capital: float = 0.0,
) -> str:
    """
    生成期权仓位再平衡策略执行提示

    Args:
        option_symbol: 期权合约符号 (例如: "TSLA250919P00390000")
        position_size: 仓位大小 (负数表示做空，例如: -100表示卖出100个合约)
        entry_price: 入场价格 (期权单价per share，例如: 13.00)
        position_type: 仓位类型 ("short_put", "short_call", "long_put", "long_call")
        entry_date: 入场日期 (可选，格式: "YYYY-MM-DD")
        risk_tolerance: 风险容忍度 ("conservative", "moderate", "aggressive")
        defensive_roll_trigger_pct: 防御性滚动触发阈值 (默认: 15%, 当亏损达到15%时触发)
        profit_target_pct: 获利目标百分比 (默认: 70%, 当权利金衰减70%时考虑平仓)
        max_additional_capital: 最大额外资金投入 (默认: 0, 用于评估是否接受需要额外资金的滚动策略)

    Returns:
        str: 综合的再平衡执行提示计划字符串

    Raises:
        ValueError: 当输入参数无效时
    """

    # 参数验证
    validation_result = _validate_rebalancer_parameters(
        option_symbol=option_symbol,
        position_size=position_size,
        entry_price=entry_price,
        position_type=position_type,
        entry_date=entry_date,
        risk_tolerance=risk_tolerance,
        defensive_roll_trigger_pct=defensive_roll_trigger_pct,
        profit_target_pct=profit_target_pct,
        max_additional_capital=max_additional_capital
    )

    if not validation_result["is_valid"]:
        raise ValueError(f"参数验证失败: {', '.join(validation_result['errors'])}")

    # 从期权符号中提取信息
    underlying_symbol = _extract_underlying_from_option_symbol(option_symbol)
    strike_price = _extract_strike_from_option_symbol(option_symbol)
    expiration_date = _extract_expiration_from_option_symbol(option_symbol)
    option_type = "put" if "P" in option_symbol else "call"

    # 计算仓位成本
    position_cost = abs(position_size) * entry_price * 100  # 每个合约100股

    # 生成结构化提示
    prompt = _generate_rebalancer_prompt(
        option_symbol=option_symbol,
        underlying_symbol=underlying_symbol,
        strike_price=strike_price,
        expiration_date=expiration_date,
        option_type=option_type,
        position_size=position_size,
        entry_price=entry_price,
        position_cost=position_cost,
        position_type=position_type,
        entry_date=entry_date,
        risk_tolerance=risk_tolerance,
        defensive_roll_trigger_pct=defensive_roll_trigger_pct,
        profit_target_pct=profit_target_pct,
        max_additional_capital=max_additional_capital
    )

    return prompt


def _validate_rebalancer_parameters(
    option_symbol: str,
    position_size: int,
    entry_price: float,
    position_type: str,
    entry_date: Optional[str],
    risk_tolerance: str,
    defensive_roll_trigger_pct: float,
    profit_target_pct: float,
    max_additional_capital: float
) -> Dict[str, Any]:
    """
    验证再平衡引擎输入参数的有效性

    Returns:
        Dict[str, Any]: 包含验证结果的字典
    """
    errors = []
    warnings = []

    # 验证期权符号
    if not option_symbol or not isinstance(option_symbol, str):
        errors.append("期权符号必须是非空字符串")
    elif len(option_symbol) < 10:
        errors.append("期权符号格式不正确，长度过短")

    # 验证仓位大小
    if not isinstance(position_size, int) or position_size == 0:
        errors.append("仓位大小必须是非零整数")

    # 验证入场价格
    if not isinstance(entry_price, (int, float)) or entry_price <= 0:
        errors.append("入场价格必须大于0")

    # 验证仓位类型
    valid_position_types = ["short_put", "short_call", "long_put", "long_call"]
    if position_type not in valid_position_types:
        errors.append(f"仓位类型必须是: {', '.join(valid_position_types)}")

    # 验证入场日期格式（如果提供）
    if entry_date:
        try:
            datetime.strptime(entry_date, "%Y-%m-%d")
        except ValueError:
            errors.append("入场日期格式必须是 YYYY-MM-DD")

    # 验证风险容忍度
    valid_risk_levels = ["conservative", "moderate", "aggressive"]
    if risk_tolerance not in valid_risk_levels:
        errors.append(f"风险容忍度必须是: {', '.join(valid_risk_levels)}")

    # 验证触发阈值
    if not isinstance(defensive_roll_trigger_pct, (int, float)) or defensive_roll_trigger_pct < 0 or defensive_roll_trigger_pct > 100:
        errors.append("防御性滚动触发阈值必须在0-100%之间")

    # 验证获利目标
    if not isinstance(profit_target_pct, (int, float)) or profit_target_pct < 0 or profit_target_pct > 100:
        errors.append("获利目标百分比必须在0-100%之间")

    # 验证最大额外资金
    if not isinstance(max_additional_capital, (int, float)) or max_additional_capital < 0:
        errors.append("最大额外资金必须≥0")

    # 逻辑验证和警告
    if position_size < 0 and position_type.startswith("long"):
        warnings.append("仓位大小为负数但类型为long，请检查是否一致")
    elif position_size > 0 and position_type.startswith("short"):
        warnings.append("仓位大小为正数但类型为short，请检查是否一致")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def _extract_underlying_from_option_symbol(option_symbol: str) -> str:
    """从期权符号提取标的股票代码"""
    # 期权符号格式: TSLA250919P00390000
    # 提取前面的字母部分
    underlying = ""
    for char in option_symbol:
        if char.isalpha():
            underlying += char
        else:
            break
    return underlying


def _extract_strike_from_option_symbol(option_symbol: str) -> float:
    """从期权符号提取行权价"""
    # 期权符号格式: TSLA250919P00390000
    # 提取最后8位数字: 前5位整数部分，后3位小数部分
    try:
        strike_str = option_symbol[-8:]
        strike = float(strike_str[:5]) + float(strike_str[5:]) / 1000
        return strike
    except:
        return 0.0


def _extract_expiration_from_option_symbol(option_symbol: str) -> str:
    """从期权符号提取到期日"""
    # 期权符号格式: TSLA250919P00390000
    # 提取日期部分: 250919 -> 2025-09-19
    try:
        # 找到字母结束的位置
        date_start = 0
        for i, char in enumerate(option_symbol):
            if not char.isalpha():
                date_start = i
                break

        # 提取6位日期
        date_str = option_symbol[date_start:date_start+6]
        year = "20" + date_str[:2]
        month = date_str[2:4]
        day = date_str[4:6]

        return f"{year}-{month}-{day}"
    except:
        return "未知"


def _generate_rebalancer_prompt(
    option_symbol: str,
    underlying_symbol: str,
    strike_price: float,
    expiration_date: str,
    option_type: str,
    position_size: int,
    entry_price: float,
    position_cost: float,
    position_type: str,
    entry_date: Optional[str],
    risk_tolerance: str,
    defensive_roll_trigger_pct: float,
    profit_target_pct: float,
    max_additional_capital: float
) -> str:
    """
    生成期权仓位再平衡结构化执行提示

    Returns:
        str: 完整的提示字符串
    """

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 根据仓位类型确定分析重点
    if position_type.startswith("short"):
        position_direction = "做空"
        primary_risk = "被行权风险和期权价格上涨"
        profit_scenario = "时间价值衰减，期权价格下跌"
    else:
        position_direction = "做多"
        primary_risk = "时间价值衰减和期权价格下跌"
        profit_scenario = "期权价格上涨"

    # 根据风险容忍度设置决策权重
    if risk_tolerance == "conservative":
        risk_weight_text = "优先风险控制（持仓权重↓，平仓/滚动权重↑）"
        assignment_threshold = 0.70
    elif risk_tolerance == "aggressive":
        risk_weight_text = "优先收益最大化（持仓权重↑，容忍更高风险）"
        assignment_threshold = 0.85
    else:
        risk_weight_text = "平衡风险与收益（标准决策权重）"
        assignment_threshold = 0.80

    prompt = f"""# 🎯 期权仓位再平衡与风险管理引擎

## 📊 当前仓位概览

**分析时间**: {current_time}
**期权合约**: {option_symbol}
**标的股票**: {underlying_symbol}
**仓位方向**: {position_direction} ({position_type})
**合约数量**: {position_size}个合约 ({abs(position_size) * 100}股标的)
**行权价格**: ${strike_price:.2f}
**到期日期**: {expiration_date}
**入场价格**: ${entry_price:.2f}/股
**入场日期**: {entry_date if entry_date else '未提供'}
**仓位成本**: ${position_cost:,.0f}

## ⚠️ 风险管理参数

**风险容忍度**: {risk_tolerance.upper()} - {risk_weight_text}
**防御触发阈值**: {defensive_roll_trigger_pct}% (亏损达到此水平时评估滚动策略)
**获利目标**: {profit_target_pct}% (权利金衰减达到此水平时考虑平仓)
**最大额外资金**: ${max_additional_capital:,.0f} (用于评估需要额外投入的滚动策略)
**被行权警戒线**: {assignment_threshold*100:.0f}% (概率超过此值时强制采取行动)

## 🔄 强制执行序列

### 第一步: 时间基准与市场状态验证
```
get_market_time_tool()
```
**验证要求**:
- 确认当前市场时间
- 验证市场开闭盘状态
- 计算距离到期日的剩余天数

### 第二步: 标的股票实时分析
```
# 获取标的股票当前状态
stock_info_tool(symbol="{underlying_symbol}")

# 获取历史价格和技术指标
stock_history_tool(
    symbol="{underlying_symbol}",
    date_range="3m",
    interval="daily",
    include_indicators=true
)
```
**分析重点**:
- 当前股价 vs 行权价位置
- 关键支撑/阻力位识别
- 技术指标趋势（RSI、MACD、均线）
- 波动率环境评估

### 第三步: 期权合约当前状态查询
```
# 获取期权链数据，查找当前持仓期权
options_chain_tool_mcp(
    symbol="{underlying_symbol}",
    expiration="{expiration_date}",
    option_type="{option_type}",
    include_greeks=true
)
```
**关键指标提取**:
- 当前Bid/Ask价格
- 最新Greeks (Delta, Gamma, Theta, Vega)
- 隐含波动率 (IV)
- 交易量和开放利益

### 第四步: 仓位盈亏与风险计算
```
# 计算当前P&L
# 对于做空期权: P&L = (入场价格 - 当前价格) × 合约数 × 100
# 对于做多期权: P&L = (当前价格 - 入场价格) × 合约数 × 100

当前期权价格 = (Bid + Ask) / 2
{'做空' if position_type.startswith('short') else '做多'}期权P&L = ({entry_price if position_type.startswith('short') else '当前价格'} - {'当前价格' if position_type.startswith('short') else entry_price}) × {abs(position_size)} × 100
P&L百分比 = (当前P&L / {position_cost}) × 100%
```

### 第五步: 被行权概率精确评估
```
option_assignment_probability_tool_mcp(
    symbol="{underlying_symbol}",
    strike_price={strike_price},
    expiration="{expiration_date}",
    option_type="{option_type}",
    include_delta_comparison=true
)
```
**关键风险指标**:
- Black-Scholes被行权概率
- Delta理论概率对比
- 剩余时间价值分析

### 第六步: 滚动策略候选评估

#### 6.1 Calendar Roll评估 (相同行权价，延长时间)
```
# 查询下一个到期周期的期权
get_next_expiration_tool_mcp(
    symbol="{underlying_symbol}",
    current_expiration="{expiration_date}",
    expiration_type="weekly"  # 或 "monthly"
)

# 获取目标到期日的期权链
options_chain_tool_mcp(
    symbol="{underlying_symbol}",
    expiration="[从上步获取的下一个到期日]",
    option_type="{option_type}",
    include_greeks=true
)

# 评估Calendar Roll的净成本/收益
# 平仓当前仓位成本 = 当前Ask价格 × {abs(position_size)} × 100
# 开新仓收入 = 新期权Bid价格 × {abs(position_size)} × 100
# 净信用/借记 = 新期权收入 - 平仓成本
```

#### 6.2 Diagonal Roll评估 (调整行权价+延长时间)
```
# 根据当前P&L决定调整方向
# 如果{'亏损' if position_type.startswith('short') else '盈利'} > {defensive_roll_trigger_pct}%:
#   - {option_type.upper()} {'降低行权价' if option_type == 'put' else '提高行权价'} (更保守)
# 否则:
#   - 小幅调整优化收益

# 计算目标行权价
调整后行权价 = {strike_price} × {'0.95' if option_type == 'put' else '1.05'} (示例调整)

# 获取调整后的期权链
options_chain_tool_mcp(
    symbol="{underlying_symbol}",
    expiration="[目标到期日]",
    option_type="{option_type}",
    include_greeks=true
)

# 筛选最接近调整后行权价的期权
# 评估净信用/借记和风险降低效果
```

#### 6.3 Triple Strike Resize评估 (大幅调整+减仓)
```
# 减少50%仓位，大幅调整行权价
新仓位大小 = {abs(position_size)} × 0.5
调整后行权价 = {strike_price} × {'0.93' if option_type == 'put' else '1.07'} (7%调整)

# 获取调整后期权数据
options_chain_tool_mcp(
    symbol="{underlying_symbol}",
    expiration="[目标到期日，通常延长到42天]",
    option_type="{option_type}",
    include_greeks=true
)

# 评估净成本/收益
# 平仓成本 = 当前Ask × {abs(position_size)} × 100
# 新仓收入 = 新期权Bid × (新仓位大小) × 100
# 净借记 = 新仓收入 - 平仓成本
# 释放资金 = ({abs(position_size)} - 新仓位大小) × 保证金需求
```

### 第七步: 智能决策引擎评分

基于以下因子生成Hold/Close/Roll决策评分:

#### Hold决策评分 (0-100分)
**基础分**: 50
**加分项**:
- 未触发止损 (+15分)
- Theta有利 (时间价值衰减方向正确) (+20分)
- P&L在10-50%之间 (+15分)
- 距离到期>7天 (+10分)
- 被行权概率<50% (+10分)

**减分项**:
- 达到获利目标{profit_target_pct}% (-30分)
- 被行权概率>{assignment_threshold*100:.0f}% (-25分)
- 距离到期≤7天 (-20分)

#### Close决策评分 (0-100分)
**基础分**: 40
**加分项**:
- 达到获利目标{profit_target_pct}% (+40分)
- 触发止损{defensive_roll_trigger_pct}% (+35分)
- 距离到期≤7天且P&L>50% (+20分)
- 流动性不足 (+15分)

**减分项**:
- P&L>-10%且距离到期>7天 (-20分)
- Theta有利且P&L>0 (-15分)

#### Roll决策评分 (0-100分)
**基础分**: 45
**加分项**:
- 距离到期≤7天 (+25分)
- 被行权概率>{assignment_threshold*100:.0f}%且滚动可降低风险40%+ (+20分)
- 滚动可获得净信用 (+15分)
- 滚动策略成功概率>70% (+15分)

**减分项**:
- 达到获利目标{profit_target_pct}% (-20分)
- 流动性不足 (-25分)
- 需要额外资金>${max_additional_capital:,.0f} (-15分)

**最终决策**: 选择得分最高的策略，并计算置信度 = 得分/100

### 第八步: 执行计划生成

根据最高评分决策生成专业执行计划:

#### 如果决策 = HOLD
```
# 持仓监控计划
监控指标:
- 被行权概率变化 (每日检查)
- P&L百分比变化 (实时监控)
- 标的股价vs行权价距离
- 隐含波动率变化

触发条件:
- 被行权概率超过{assignment_threshold*100:.0f}% → 重新评估
- 亏损达到{defensive_roll_trigger_pct}% → 触发滚动评估
- 盈利达到{profit_target_pct}% → 考虑平仓
- 距离到期3天 → 强制决策
```

#### 如果决策 = CLOSE
```
# 平仓订单格式 (JP Morgan标准)

订单类型: BUY TO CLOSE (BTC) / SELL TO CLOSE (STC)
合约符号: {option_symbol}
数量: {abs(position_size)}
订单价格: [当前Ask价格] (市价单) 或 [限价]
有效期: GTC (Good Till Cancel) 或 DAY
预估成本: [当前Ask × {abs(position_size)} × 100]
预估P&L: [最终P&L计算]

风险披露:
- 执行滑点风险
- 市场波动风险
- 流动性风险评估
```

#### 如果决策 = ROLL
```
# 滚动订单格式 (两腿订单)

【第一腿】平仓当前仓位:
订单类型: {'BUY TO CLOSE (BTC)' if position_type.startswith('short') else 'SELL TO CLOSE (STC)'}
合约符号: {option_symbol}
数量: {abs(position_size)}
订单价格: [当前Ask/Bid价格]

【第二腿】开启新仓位:
订单类型: {'SELL TO OPEN (STO)' if position_type.startswith('short') else 'BUY TO OPEN (BTO)'}
合约符号: [新期权符号]
数量: [新仓位大小]
订单价格: [新期权Bid/Ask价格]

净现金流: [第二腿收入 - 第一腿成本]
额外资金需求: [如果净现金流为负]
新仓位参数:
- 新行权价: [具体数值]
- 新到期日: [具体日期]
- 新Delta: [预期值]
- 风险降低: [百分比]

执行建议:
- 使用Spread Order确保价格锁定
- 优先在市场开盘后30分钟执行
- 设置Limit Price保护
```

## 🎯 专业输出要求

### 必需输出内容

1. **仓位状态仪表盘**
   - 当前P&L (金额和百分比)
   - 被行权概率评估
   - 剩余到期天数
   - 关键Greeks当前值

2. **风险评估报告**
   - 主要风险点识别: {primary_risk}
   - 风险等级: 低/中/高
   - 触发条件距离: 距离止损/获利目标的距离

3. **决策评分详情**
   - Hold评分: [X]/100 + 详细理由
   - Close评分: [Y]/100 + 详细理由
   - Roll评分: [Z]/100 + 详细理由
   - 最终决策: [HOLD/CLOSE/ROLL] (置信度: XX%)

4. **推荐行动计划**
   - 即时行动: [具体步骤]
   - 监控计划: [关键指标和检查频率]
   - 触发条件: [何时重新评估]
   - 备选方案: [Plan B是什么]

5. **执行检查清单**
   - [ ] 市场时间验证通过
   - [ ] 期权流动性充足 (Bid-Ask价差<10%)
   - [ ] Greeks数据获取成功
   - [ ] 被行权概率计算完成
   - [ ] 滚动策略评估完成 (如适用)
   - [ ] 资金需求评估完成
   - [ ] 订单格式验证通过

6. **风险披露声明**
   - 主要风险: {primary_risk}
   - 盈利场景: {profit_scenario}
   - 最大损失: [根据仓位类型计算]
   - 流动性风险: [基于交易量评估]

## 📈 输出格式要求

### HTML报告生成
在完成所有分析后，生成完整的HTML报告:

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>期权仓位再平衡报告 - {option_symbol}</title>
    <style>
        /* 使用GenUI标准样式 */
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        .risk-high {{ color: #e74c3c; }}
        .risk-medium {{ color: #f39c12; }}
        .risk-low {{ color: #27ae60; }}
        .decision-hold {{ background: #3498db; }}
        .decision-close {{ background: #e74c3c; }}
        .decision-roll {{ background: #f39c12; }}
    </style>
</head>
<body>
    <!-- 仓位概览 -->
    <!-- 风险评估 -->
    <!-- 决策评分 -->
    <!-- 执行计划 -->
    <!-- 监控计划 -->
</body>
</html>
```

保存到: `/tmp/cc_genui_position_rebalancer_{{underlying_symbol}}_{{timestamp}}.html`

## ⚡ 开始执行

请严格按照上述序列执行所有工具调用，重点关注:
1. **数据准确性**: 所有数值计算必须精确
2. **逻辑一致性**: 决策理由必须与评分逻辑匹配
3. **风险优先**: 风险控制始终是首要考虑
4. **可执行性**: 所有建议必须具体可操作

---
*免责声明: 本分析仅供参考，期权交易存在重大风险，可能导致全部本金损失。请根据个人风险承受能力谨慎决策，建议咨询专业财务顾问。*
"""

    return prompt


# 辅助函数用于获取使用示例
def get_rebalancer_examples() -> Dict[str, Any]:
    """
    获取期权仓位再平衡使用示例

    Returns:
        Dict[str, Any]: 包含使用示例的字典
    """
    return {
        "short_put_losing": {
            "description": "亏损的做空Put仓位",
            "example_call": {
                "option_symbol": "TSLA250919P00390000",
                "position_size": -100,
                "entry_price": 13.00,
                "position_type": "short_put",
                "entry_date": "2025-09-01",
                "risk_tolerance": "moderate",
                "defensive_roll_trigger_pct": 15.0,
                "profit_target_pct": 70.0,
                "max_additional_capital": 50000
            },
            "expected_outcome": "评估Roll策略，可能推荐Diagonal Roll降低风险",
            "use_case": "防御性滚动场景"
        },
        "short_put_winning": {
            "description": "盈利的做空Put仓位",
            "example_call": {
                "option_symbol": "AAPL251017P00220000",
                "position_size": -50,
                "entry_price": 5.50,
                "position_type": "short_put",
                "entry_date": "2025-10-01",
                "risk_tolerance": "conservative",
                "defensive_roll_trigger_pct": 15.0,
                "profit_target_pct": 70.0,
                "max_additional_capital": 0
            },
            "expected_outcome": "可能推荐Close平仓锁定利润",
            "use_case": "获利了结场景"
        },
        "short_call_defensive": {
            "description": "需要防御的做空Call仓位",
            "example_call": {
                "option_symbol": "NVDA250926C00800000",
                "position_size": -20,
                "entry_price": 15.00,
                "position_type": "short_call",
                "entry_date": "2025-09-15",
                "risk_tolerance": "conservative",
                "defensive_roll_trigger_pct": 20.0,
                "profit_target_pct": 60.0,
                "max_additional_capital": 100000
            },
            "expected_outcome": "可能推荐Triple Strike Resize降低风险敞口",
            "use_case": "高风险防御场景"
        }
    }


def get_usage_guidelines() -> List[str]:
    """
    获取使用指导原则

    Returns:
        List[str]: 使用指导列表
    """
    return [
        "🎯 风险优先: 始终将风险控制放在首位",
        "📊 量化决策: 基于评分模型而非主观判断",
        "⏰ 及时行动: 触发条件出现时立即执行",
        "📈 动态管理: 持续监控并适时调整",
        "🛡️ 防御意识: 主动采取防御性策略",
        "📋 专业执行: 使用标准化订单格式",
        "🔄 灵活应对: 根据市场变化调整策略",
        "📊 数据驱动: 所有决策基于实时数据"
    ]
