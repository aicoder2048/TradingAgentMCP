"""
Income Generation Cash-Secured Put Engine MCP Server Prompt

专注于收入生成的现金担保看跌期权策略提示生成器。
为TradingAgent MCP用户提供高收益、低分配风险的期权策略执行计划。

核心特性：
- 年化收益率目标 ≥50%
- Delta范围优化 (0.10-0.30) 避免股票分配
- 快速周转策略 (7-28天)
- 专业订单格式化和风险管理协议
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import json
import ast


async def income_generation_csp_engine(
    tickers: str,  # 修改：现在只接受字符串，内部处理所有格式
    cash_usd: float,
    target_apy_pct: float = 50,
    min_winrate_pct: float = 70,
    confidence_pct: float = 90,
) -> str:
    """
    生成收入导向的现金担保看跌期权策略执行提示
    
    Args:
        tickers: 目标股票代码字符串 - 支持多种格式:
            - JSON字符串: "[\"TSLA\", \"GOOG\", \"META\"]" 或 "['TSLA','GOOG','META']"  
            - 空格分隔: "TSLA GOOG META"
            - 逗号分隔: "TSLA,GOOG,META"
            - 单个ticker: "TSLA"
            (默认: [\"SPY\", \"QQQ\", \"AAPL\", \"MSFT\", \"NVDA\"])
        cash_usd: 可用资金
        target_apy_pct: 目标年化收益率百分比 (默认: 50%)
        min_winrate_pct: 最小目标胜率百分比 (默认: 70%)
        confidence_pct: 统计置信度百分比 (默认: 90%)
        
    Returns:
        str: 综合的执行提示计划字符串
        
    Raises:
        ValueError: 当输入参数无效时
    """
    
    # DEBUG: 记录函数入口的原始参数
    try:
        from ..utils.debug_logger import debug_param, debug_parse_result
        debug_param(
            "income_generation_csp_engine:ENTRY",
            "tickers_raw",
            tickers,
            f"Type: {type(tickers).__name__}, ID: {id(tickers)}"
        )
    except:
        pass
    
    # 首先处理和清理输入的tickers
    tickers_list = _parse_tickers_input(tickers)
    
    # DEBUG: 记录解析后的结果
    try:
        debug_parse_result(tickers, tickers_list)
        debug_param(
            "income_generation_csp_engine:AFTER_PARSE",
            "tickers_parsed",
            tickers_list,
            f"Length: {len(tickers_list) if tickers_list else 0}"
        )
    except:
        pass
    
    if tickers_list:
        # 清理每个ticker的空格并去除空字符串
        tickers_list = [ticker.strip() for ticker in tickers_list if ticker and ticker.strip()]
    
    # 处理默认股票列表
    if not tickers_list:
        tickers_list = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA"]
    
    # 参数验证（在清理后进行）
    validation_result = _validate_parameters(
        tickers_list, cash_usd, target_apy_pct, min_winrate_pct, confidence_pct
    )
    
    if not validation_result["is_valid"]:
        raise ValueError(f"参数验证失败: {', '.join(validation_result['errors'])}")
    
    # 限制股票数量以优化性能
    if len(tickers_list) > 10:
        tickers_list = tickers_list[:10]
    
    # 构建股票字符串
    tickers_str = ", ".join(tickers_list)
    primary_ticker = tickers_list[0]
    
    # 生成结构化提示
    prompt = _generate_structured_prompt(
        tickers=tickers_list,
        tickers_str=tickers_str,
        primary_ticker=primary_ticker,
        cash_usd=cash_usd,
        target_apy_pct=target_apy_pct,
        min_winrate_pct=min_winrate_pct,
        confidence_pct=confidence_pct
    )
    
    return prompt


def _validate_parameters(
    tickers: List[str],
    cash_usd: float,
    target_apy_pct: float,
    min_winrate_pct: float,
    confidence_pct: float
) -> Dict[str, Any]:
    """
    验证输入参数的有效性
    
    Returns:
        Dict[str, Any]: 包含验证结果的字典
    """
    errors = []
    warnings = []
    
    # 验证股票代码列表（此时已经清理过）
    if tickers:
        if len(tickers) > 10:
            warnings.append("股票列表超过10个，将截取前10个")
        
        for ticker in tickers:
            if not ticker or not isinstance(ticker, str):
                errors.append("股票代码必须是非空字符串")
            elif len(ticker) > 10:
                errors.append(f"股票代码 '{ticker}' 过长")
    
    # 验证资金金额
    if not isinstance(cash_usd, (int, float)) or cash_usd <= 0:
        errors.append("资金金额必须大于0")
    elif cash_usd < 1000:
        warnings.append("资金金额较小，可能无法找到合适的期权")
    elif cash_usd > 1000000:
        warnings.append("资金金额很大，建议分散投资")
    
    # 天数范围由智能到期日选择器决定，无需验证固定范围
    
    # 验证百分比参数
    for param_name, param_value in [
        ("目标年化收益率", target_apy_pct),
        ("最小胜率", min_winrate_pct),
        ("置信度", confidence_pct)
    ]:
        if not isinstance(param_value, (int, float)) or param_value < 0 or param_value > 100:
            errors.append(f"{param_name}必须在0-100%之间")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def _generate_structured_prompt(
    tickers: List[str],
    tickers_str: str,
    primary_ticker: str,
    cash_usd: float,
    target_apy_pct: float,
    min_winrate_pct: float,
    confidence_pct: float
) -> str:
    """
    生成结构化的执行提示
    
    Returns:
        str: 完整的提示字符串
    """
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    prompt = f"""# 💵 收入生成现金担保PUT策略引擎

## 🎯 策略目标与约束参数

**分析时间**: {current_time}
**目标股票池**: {tickers_str}
**可用资金**: ${cash_usd:,.0f}
**期权到期策略**: 智能优化选择（以收益为导向）
**收益目标**: 年化≥{target_apy_pct}%、胜率≥{min_winrate_pct}%、统计置信度≥{confidence_pct}%

## ⚠️ 关键执行原则

**收入优先策略 - 避免股票分配**:
- 🎯 **核心目标**: 收取期权权利金，NOT 购买股票
- 📊 **Delta范围**: 严格控制在 0.10~0.30 (优先 0.15~0.25)
- ⏰ **快速周转**: 优化到期日选择，最大化时间价值衰减
- 💰 **高收益筛选**: 年化收益率≥{target_apy_pct}%，胜率≥{min_winrate_pct}%

## 🔄 强制执行序列 - 按顺序执行以下工具

### 第一步: 时间基准验证 (关键!)
```
get_market_time_tool()
```
**验证要求**: 确保返回有效市场时间，检查:
- 日期格式正确 (YYYY-MM-DD)
- 时间合理性 (年份≥当前年)
- 市场状态验证

### 第二步: 股票基础分析 (并行执行)
对每个目标股票执行以下分析:

```
# 主要股票 {primary_ticker} 详细分析
stock_info_tool(symbol="{primary_ticker}")
stock_history_tool(symbol="{primary_ticker}", date_range="3m", interval="daily", include_indicators=true)
```

### 第三步: 智能到期日优化选择 (科学化核心!)
```
# 智能选择最优到期日 - 基于客观数学指标
# 不设固定天数范围，让算法针对收益策略自动优化
optimal_expiration_selector_tool_mcp(
    symbol="{primary_ticker}",
    strategy_type="csp",  # 现金担保PUT策略
    volatility=None,  # 自动检测当前隐含波动率
    weights={{
        "theta_efficiency": 0.40,    # Theta效率曲线权重(30-45天最优)
        "gamma_risk": 0.25,         # Gamma风险控制(<21天惩罚)
        "liquidity": 0.20,          # 流动性评分(周期权/月期权优先)
        "event_buffer": 0.15        # 事件缓冲(避开财报等事件)
    }}
)
```

### 第四步: 收入导向CSP策略生成
```
cash_secured_put_strategy_tool_mcp(
    symbol="{primary_ticker}",
    purpose_type="income",  # 关键: 收入导向策略
    duration="[从第三步获得的最优到期日区间]",
    capital_limit={min(cash_usd * 0.8, 100000)},
    include_order_blocks=true,
    min_premium=1.0,  # 最小权利金要求
    max_delta=-0.30   # 最大Delta限制 (避免分配)
)
```

### 第五步: 期权链深度分析
```
options_chain_tool_mcp(
    symbol="{primary_ticker}",
    expiration="[从第三步获得的最优到期日]",
    option_type="put",
    include_greeks=true
)
```

### 第六步: 分配概率精确计算
```
option_assignment_probability_tool_mcp(
    symbol="{primary_ticker}",
    strike_price="[从第四步获得的推荐执行价]",
    expiration="[最优到期日]",
    option_type="put",
    include_delta_comparison=true
)
```

### 第七步: 科学化投资组合配置 (使用夏普比率优化)
```
# 收集所有分析过的策略数据
strategies_data = [
    # 将每个股票的CSP策略结果整理成列表
]

portfolio_optimization_tool_mcp_tool(
    strategies_data=strategies_data,
    total_capital={cash_usd},
    optimization_method="sharpe",  # 使用夏普比率加权
    risk_free_rate=0.048,  # 当前无风险利率4.8%
    constraints={{
        "min_allocation": 0.00,  # 最小仓位0%（允许不配置）
        "max_allocation": 0.80,  # 最大仓位80%（允许集中投资）
        "min_positions": 1       # 至少1个仓位（允许单一最优）
    }}
)
```

## 📊 收入优化筛选标准

### 一级筛选 - 基础门槛
- **流动性要求**: Bid-Ask价差 ≤ 权利金的10%
- **交易量**: 开放利益(OI) ≥ 500，成交量 ≥ 50
- **Delta范围**: 0.10 ≤ |Delta| ≤ 0.30 (收入导向)
- **技术支撑**: 执行价位于关键支撑位下方5~15%
- **IV环境**: IV Rank ≥ 30百分位

### 二级优化 - 收入效率排序
1. **年化收益率优先** (40%权重):
   - 公式: (权利金/现金占用) × (365/到期天数) × 100%
   - 目标: ≥{target_apy_pct}% 满分

2. **胜率估算** (35%权重):
   - Delta理论概率 + 历史回测验证
   - 目标: ≥{min_winrate_pct}% 满分

3. **风险调整收益** (25%权重):
   - 夏普比率: (年化收益率 - 无风险利率) / 波动率
   - 凯利公式优化: f* = (bp - q)/b
   - 使用portfolio_optimization_tool_mcp_tool进行科学配置

### 三级验证 - 到期日优化确认
- **Theta效率**: 验证选择的到期日是否在30-45天黄金窗口
- **Gamma风险**: 确保避开<21天的高Gamma风险期
- **事件避让**: 确保避开财报、分红除权等重大事件
- **流动性验证**: 优先选择周期权和月期权（流动性最佳）

## 🎯 专业输出规格要求

### 必需输出格式
1. **时间基准声明**: 明确声明分析基准时间
2. **到期日优化报告**: 展示智能选择器的评分过程和最终选择理由
3. **推荐策略对比表**: 包含至少3个风险级别的建议
4. **专业订单格式**: JP Morgan风格的交易指令
5. **风险管理剧本**: 开仓、持仓、平仓的具体触发条件
6. **分配避免协议**: Delta漂移和支撑跌破的应对措施

### 风险控制检查清单
- [ ] 所有推荐期权的Delta < -0.30
- [ ] 年化收益率≥{target_apy_pct}%
- [ ] 估计胜率≥{min_winrate_pct}%
- [ ] 流动性评分 ≥ B级
- [ ] 距离财报日期 > 7天
- [ ] 市场VIX < 35 (避免高波动环境)
- [ ] 最优到期日评分 ≥ 70分

## 💡 执行管理触发器

**获利了结条件**:
- 权利金回落至50%时考虑平仓获利
- Delta衰减至-0.10以下时评估早期平仓

**调整滚动条件**:
- Delta漂移至-0.35时强制滚动到下月或更低执行价
- 标的跌破执行价5%时评估是否接受分配 (但要避免!)

**止损保护条件**:
- 期权价值增长超过200%时考虑止损
- 标的技术面严重恶化时主动平仓

## 🔚 最终验证与总结要求

执行完所有工具后，请提供:

1. **策略有效性确认**: 所有推荐是否满足收入导向目标
2. **到期日优化验证**: 智能选择器的评分过程和选择依据
3. **分配风险评估**: 每个推荐的具体分配概率
4. **资金配置建议**: 基于夏普比率的科学化仓位分配
   - 明确说明每个股票的配置权重计算方法
   - 展示夏普比率计算过程
   - 解释为什么某些股票获得更高权重
5. **执行时机建议**: 考虑市场环境的最佳开仓时间
6. **监控检查点**: 需要日常监控的关键指标
7. **数学逻辑验证**: 确保所有数学比较和结论正确
   - 验证收益率vs目标比较的准确性
   - 避免出现"34.8%超过50%"的逻辑错误

## ⚡ 开始执行

请严格按照上述序列执行所有工具，重点关注**收入生成**而非股票获取，确保所有推荐策略的年化收益≥{target_apy_pct}%且分配概率<30%。特别注意使用智能到期日选择器替代主观判断。

---
*免责声明: 本分析仅供参考，期权交易存在重大风险。请根据个人风险承受能力谨慎决策。*
"""

    return prompt


def _get_duration_from_days(min_days: int, max_days: int) -> str:
    """
    根据天数范围转换为duration参数
    
    Returns:
        str: duration参数值
    """
    avg_days = (min_days + max_days) / 2
    
    if avg_days <= 9:
        return "1w"
    elif avg_days <= 18:
        return "2w"
    elif avg_days <= 35:
        return "1m"
    elif avg_days <= 100:
        return "3m"
    elif avg_days <= 190:
        return "6m"
    else:
        return "1y"


# 辅助函数用于获取策略示例和使用指导

def get_income_csp_examples() -> Dict[str, Any]:
    """
    获取收入生成CSP策略使用示例
    
    Returns:
        Dict[str, Any]: 包含使用示例的字典
    """
    return {
        "conservative_income": {
            "description": "保守收入策略",
            "example_call": {
                "tickers": ["SPY", "QQQ"],
                "cash_usd": 25000,
                "min_days": 7,
                "max_days": 14,
                "target_apy_pct": 40,
                "min_winrate_pct": 80
            },
            "expected_outcome": "低风险、稳定收入，Delta 0.10-0.20",
            "use_case": "风险厌恶投资者的稳定收入策略"
        },
        "balanced_income": {
            "description": "平衡收入策略",
            "example_call": {
                "tickers": ["AAPL", "MSFT", "NVDA"],
                "cash_usd": 50000,
                "min_days": 14,
                "max_days": 28,
                "target_apy_pct": 50,
                "min_winrate_pct": 70
            },
            "expected_outcome": "中等风险、良好收入，Delta 0.15-0.25",
            "use_case": "平衡收入与风险的中等策略"
        },
        "aggressive_income": {
            "description": "激进收入策略",
            "example_call": {
                "tickers": ["TSLA", "AMD", "NVDA"],
                "cash_usd": 100000,
                "min_days": 7,
                "max_days": 21,
                "target_apy_pct": 60,
                "min_winrate_pct": 65
            },
            "expected_outcome": "高风险、高收入，Delta 0.20-0.30",
            "use_case": "追求高收益的激进收入策略"
        }
    }


def _parse_tickers_input(tickers_input: Union[List[str], str]) -> List[str]:
    """
    解析不同格式的tickers输入
    
    支持的格式:
    - Python列表: ['TSLA', 'GOOG', 'META']
    - JSON字符串: ["TSLA", "GOOG", "META"]
    - 空格分隔: "TSLA GOOG META"
    - 逗号分隔: "TSLA,GOOG,META"
    - 单个ticker: "TSLA"
    
    Args:
        tickers_input: 输入的tickers，可以是列表或字符串
        
    Returns:
        List[str]: 解析后的ticker列表
    """
    # DEBUG: 记录函数入口
    try:
        from ..utils.debug_logger import debug_parse_step, debug_param
        debug_param(
            "_parse_tickers_input:ENTRY", 
            "tickers_input", 
            tickers_input,
            f"Initial type: {type(tickers_input).__name__}"
        )
    except:
        pass
    
    # 如果已经是列表，直接返回
    if isinstance(tickers_input, list):
        try:
            debug_parse_step(
                "_parse_tickers_input",
                "CHECK_IS_LIST",
                tickers_input,
                tickers_input,
                success=True
            )
        except:
            pass
        return tickers_input
    
    # 如果不是字符串，转换为字符串
    if not isinstance(tickers_input, str):
        result = [str(tickers_input)]
        try:
            debug_parse_step(
                "_parse_tickers_input",
                "CONVERT_TO_STRING",
                tickers_input,
                result,
                success=True
            )
        except:
            pass
        return result
    
    # 去除首尾空格
    tickers_str = tickers_input.strip()
    
    try:
        debug_param(
            "_parse_tickers_input:STRIPPED",
            "tickers_str",
            tickers_str,
            f"After strip, length: {len(tickers_str)}"
        )
    except:
        pass
    
    # 如果为空字符串
    if not tickers_str:
        try:
            debug_parse_step(
                "_parse_tickers_input",
                "EMPTY_STRING",
                tickers_str,
                [],
                success=True
            )
        except:
            pass
        return []
    
    # 方法1: 尝试JSON解析
    try:
        result = json.loads(tickers_str)
        if isinstance(result, list):
            try:
                debug_parse_step(
                    "_parse_tickers_input",
                    "JSON_PARSE_LIST",
                    tickers_str,
                    result,
                    success=True
                )
            except:
                pass
            return result
        elif isinstance(result, str):
            result_list = [result]
            try:
                debug_parse_step(
                    "_parse_tickers_input",
                    "JSON_PARSE_STRING",
                    tickers_str,
                    result_list,
                    success=True
                )
            except:
                pass
            return result_list
    except Exception as e:
        try:
            debug_parse_step(
                "_parse_tickers_input",
                "JSON_PARSE_FAILED",
                tickers_str,
                None,
                success=False,
                error=str(e)
            )
        except:
            pass
    
    # 方法2: 尝试Python ast解析
    try:
        result = ast.literal_eval(tickers_str)
        if isinstance(result, list):
            try:
                debug_parse_step(
                    "_parse_tickers_input",
                    "AST_PARSE_LIST",
                    tickers_str,
                    result,
                    success=True
                )
            except:
                pass
            return result
        elif isinstance(result, str):
            result_list = [result]
            try:
                debug_parse_step(
                    "_parse_tickers_input",
                    "AST_PARSE_STRING",
                    tickers_str,
                    result_list,
                    success=True
                )
            except:
                pass
            return result_list
    except Exception as e:
        try:
            debug_parse_step(
                "_parse_tickers_input",
                "AST_PARSE_FAILED",
                tickers_str,
                None,
                success=False,
                error=str(e)
            )
        except:
            pass
    
    # 方法3: 检查是否是逗号分隔（优先于空格）
    if ',' in tickers_str:
        result = [s.strip() for s in tickers_str.split(',') if s.strip()]
        try:
            debug_parse_step(
                "_parse_tickers_input",
                "COMMA_SPLIT",
                tickers_str,
                result,
                success=True
            )
        except:
            pass
        return result
    
    # 方法4: 检查是否是空格分隔
    if ' ' in tickers_str:
        result = [s.strip() for s in tickers_str.split() if s.strip()]
        try:
            debug_parse_step(
                "_parse_tickers_input",
                "SPACE_SPLIT",
                tickers_str,
                result,
                success=True
            )
        except:
            pass
        return result
    
    # 方法5: 作为单个ticker
    result = [tickers_str]
    try:
        debug_parse_step(
            "_parse_tickers_input",
            "SINGLE_TICKER",
            tickers_str,
            result,
            success=True
        )
    except:
        pass
    return result


def get_usage_guidelines() -> List[str]:
    """
    获取使用指导原则
    
    Returns:
        List[str]: 使用指导列表
    """
    return [
        "💰 收入优先: 始终以权利金收取为主要目标，避免股票分配",
        "📊 Delta控制: 严格控制Delta在0.10-0.30范围内",
        "⏰ 快速周转: 优选7-28天期权，最大化时间价值衰减",
        "📈 高收益筛选: 目标年化收益率≥50%，胜率≥70%",
        "🛡️ 风险管理: 设置明确的调整和止损触发条件",
        "📋 专业执行: 使用专业订单格式和执行检查清单",
        "🔄 动态调整: 根据市场环境调整策略参数",
        "📊 数据驱动: 基于历史数据和技术分析进行决策"
    ]