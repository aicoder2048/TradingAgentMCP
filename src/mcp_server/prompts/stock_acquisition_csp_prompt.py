"""
Stock Acquisition Cash-Secured Put Engine MCP Server Prompt

专注于股票建仓的现金担保看跌期权策略提示生成器。
为TradingAgent MCP用户提供以折扣价获得优质股票的期权策略执行计划。

核心特性：
- 年化收益率目标 15-35%（合理等待成本）
- Delta范围优化 (0.30-0.50) 欢迎股票分配
- 耐心建仓策略 (21-60天)
- 专业订单格式化和投资组合管理
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import json
import ast


async def stock_acquisition_csp_engine(
    tickers: str,
    cash_usd: float,
    target_allocation_probability: float = 65.0,
    max_single_position_pct: Optional[float] = None,
    target_annual_return_pct: float = 25.0,
    preferred_sectors: Optional[str] = None,
) -> str:
    """
    生成股票建仓导向的现金担保看跌期权策略执行提示
    
    Args:
        tickers: 目标股票代码字符串 - 支持多种格式:
            - JSON字符串: "[\"TSLA\", \"GOOG\", \"META\"]" 或 "['TSLA','GOOG','META']"  
            - 空格分隔: "TSLA GOOG META"
            - 逗号分隔: "TSLA,GOOG,META"
            - 单个ticker: "TSLA"
            (默认: [\"AAPL\", \"MSFT\", \"GOOGL\", \"TSLA\", \"NVDA\"])
        cash_usd: 可用资金
        target_allocation_probability: 目标分配概率百分比 (默认: 65%)
        max_single_position_pct: 单股票最大仓位百分比 (可选，默认无限制，由智能分配决定)
        target_annual_return_pct: 目标年化收益率百分比 (默认: 25%)
        preferred_sectors: 偏好行业 (可选，默认: "Technology,Healthcare,Consumer Discretionary")
        
    Returns:
        str: 综合的股票建仓执行提示计划字符串
        
    Raises:
        ValueError: 当输入参数无效时
    """
    
    # DEBUG: 记录函数入口的原始参数
    try:
        from ..utils.debug_logger import debug_param, debug_parse_result
        debug_param(
            "stock_acquisition_csp_engine:ENTRY",
            "tickers_raw",
            tickers,
            f"Type: {type(tickers).__name__}, ID: {id(tickers)}"
        )
    except:
        pass
    
    # 处理和清理输入的tickers
    tickers_list = _parse_tickers_input(tickers)
    
    # DEBUG: 记录解析后的结果
    try:
        debug_parse_result(tickers, tickers_list)
        debug_param(
            "stock_acquisition_csp_engine:AFTER_PARSE",
            "tickers_parsed",
            tickers_list,
            f"Length: {len(tickers_list) if tickers_list else 0}"
        )
    except:
        pass
    
    if tickers_list:
        # 清理每个ticker的空格并去除空字符串
        tickers_list = [ticker.strip() for ticker in tickers_list if ticker and ticker.strip()]
    
    # 处理默认股票列表（适合建仓的优质股票）
    if not tickers_list:
        tickers_list = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
    
    # 参数验证
    validation_result = _validate_stock_acquisition_parameters(
        tickers_list, cash_usd, target_allocation_probability, 
        max_single_position_pct, target_annual_return_pct, preferred_sectors
    )
    
    if not validation_result["is_valid"]:
        raise ValueError(f"参数验证失败: {', '.join(validation_result['errors'])}")
    
    # 限制股票数量以优化性能
    if len(tickers_list) > 8:
        tickers_list = tickers_list[:8]
    
    # 构建股票字符串
    tickers_str = ", ".join(tickers_list)
    primary_ticker = tickers_list[0]
    
    # 处理偏好行业
    if not preferred_sectors:
        preferred_sectors = "Technology,Healthcare,Consumer Discretionary"
    
    # 生成结构化提示
    prompt = _generate_stock_acquisition_prompt(
        tickers=tickers_list,
        tickers_str=tickers_str,
        primary_ticker=primary_ticker,
        cash_usd=cash_usd,
        target_allocation_probability=target_allocation_probability,
        max_single_position_pct=max_single_position_pct,
        target_annual_return_pct=target_annual_return_pct,
        preferred_sectors=preferred_sectors
    )
    
    return prompt


def _validate_stock_acquisition_parameters(
    tickers: List[str],
    cash_usd: float,
    target_allocation_probability: float,
    max_single_position_pct: Optional[float],
    target_annual_return_pct: float,
    preferred_sectors: Optional[str]
) -> Dict[str, Any]:
    """
    验证股票建仓策略输入参数的有效性
    
    Returns:
        Dict[str, Any]: 包含验证结果的字典
    """
    errors = []
    warnings = []
    
    # 验证股票代码列表
    if tickers:
        if len(tickers) > 10:
            warnings.append("股票列表超过10个，将截取前8个以优化性能")
        
        for ticker in tickers:
            if not ticker or not isinstance(ticker, str):
                errors.append("股票代码必须是非空字符串")
            elif len(ticker) > 10:
                errors.append(f"股票代码 '{ticker}' 过长")
    
    # 验证资金金额
    if not isinstance(cash_usd, (int, float)) or cash_usd <= 0:
        errors.append("资金金额必须大于0")
    elif cash_usd < 10000:
        warnings.append("资金金额较小，可能无法进行有效的股票建仓")
    elif cash_usd > 5000000:
        warnings.append("资金金额很大，建议分散建仓降低风险")
    
    # 验证分配概率
    if not isinstance(target_allocation_probability, (int, float)) or target_allocation_probability < 0 or target_allocation_probability > 100:
        errors.append("目标分配概率必须在0-100%之间")
    elif target_allocation_probability < 30:
        warnings.append("分配概率较低，可能不适合股票建仓策略")
    elif target_allocation_probability > 90:
        warnings.append("分配概率很高，风险较大")
    
    # 验证单仓位限制（如果提供）
    if max_single_position_pct is not None:
        if not isinstance(max_single_position_pct, (int, float)) or max_single_position_pct < 0 or max_single_position_pct > 100:
            errors.append("单股票仓位百分比必须在0-100%之间")
        elif max_single_position_pct > 50:
            warnings.append("单股票仓位过高，建议控制在50%以内")
    
    # 天数范围由智能到期日选择器决定，无需验证固定范围
    
    # 验证年化收益率
    if not isinstance(target_annual_return_pct, (int, float)) or target_annual_return_pct < 0 or target_annual_return_pct > 100:
        errors.append("目标年化收益率必须在0-100%之间")
    elif target_annual_return_pct > 50:
        warnings.append("年化收益率目标过高，可能难以实现")
    
    # 验证偏好行业
    if preferred_sectors and not isinstance(preferred_sectors, str):
        errors.append("偏好行业必须是字符串格式")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def _generate_stock_acquisition_prompt(
    tickers: List[str],
    tickers_str: str,
    primary_ticker: str,
    cash_usd: float,
    target_allocation_probability: float,
    max_single_position_pct: Optional[float],
    target_annual_return_pct: float,
    preferred_sectors: str
) -> str:
    """
    生成股票建仓结构化的执行提示
    
    Returns:
        str: 完整的提示字符串
    """
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 设置智能仓位管理
    if max_single_position_pct is not None:
        max_position_size = cash_usd * (max_single_position_pct / 100.0)
        position_constraint_text = f"单股票≤{max_single_position_pct}%"
    else:
        max_position_size = cash_usd * 0.8  # 默认最大80%用于单个策略
        position_constraint_text = "智能分配权重"
    
    prompt = f"""# 🏗️ 股票建仓现金担保PUT引擎

## 🎯 策略目标与约束参数

**分析时间**: {current_time}
**目标股票池**: {tickers_str}
**可用资金**: ${cash_usd:,.0f}
**期权到期策略**: 智能优化选择（股票获取主题：30-60天最优范围）
**建仓目标**: 分配概率≥{target_allocation_probability}%、年化补偿≥{target_annual_return_pct}%、{position_constraint_text}
**偏好行业**: {preferred_sectors}

## ⚠️ 关键执行原则

**股票获取优先策略 - 欢迎股票分配**:
- 🎯 **核心目标**: 以折扣价获得优质股票，权利金为次要考虑
- 📊 **Delta范围**: 偏好 0.30~0.50 (目标分配概率{target_allocation_probability}%)
- ⏰ **耐心建仓**: 智能优化到期日，给股价充分调整时间
- 💰 **合理补偿**: 年化收益{target_annual_return_pct}%，作为等待成本补偿

## 🔄 强制执行序列 - 按顺序执行以下工具

### 第一步: 时间基准验证 (关键!)
```
get_market_time_tool()
```
**验证要求**: 确保返回有效市场时间，检查:
- 日期格式正确 (YYYY-MM-DD)
- 时间合理性 (年份≥当前年)
- 市场状态验证

### 第二步: 股票基本面分析 (并行执行)
对主要目标股票执行深度分析:

```
# 主要股票 {primary_ticker} 详细分析
stock_info_tool(symbol="{primary_ticker}")
stock_history_tool(symbol="{primary_ticker}", date_range="6m", interval="daily", include_indicators=true)
```

### 第三步: 智能到期日优化选择 (科学化核心!)
```
# 智能选择最优到期日 - 专门针对股票建仓CSP策略优化
# 使用专门的股票获取导向策略主题，自动优化30-60天范围
optimal_expiration_selector_tool_mcp(
    symbol="{primary_ticker}",
    strategy_type="stock_acquisition_csp_theme",  # 专门的股票获取CSP策略主题
    volatility=None  # 自动检测当前隐含波动率，权重由策略主题自动配置
)
```

### 第四步: 股票建仓导向CSP策略生成
⚠️ **关键**: 使用第三步智能优化器的结果，不要硬编码duration参数
```
# 基于智能优化器推荐的到期日，手动计算对应的duration参数
# 例如: 如果optimal_expiration_selector推荐59天，应该使用相应的duration
# 30-45天 -> "1m", 45-75天 -> "3m", 等等

cash_secured_put_strategy_tool_mcp(
    symbol="{primary_ticker}",
    purpose_type="discount",  # 关键: 股票获取模式
    duration="[根据第三步智能优化结果选择: 1m/3m/6m等]",
    capital_limit={min(max_position_size, 200000)},
    include_order_blocks=true,
    min_premium=None,  # 不限制最小权利金
    max_delta=-0.30   # 允许更高Delta获取分配
)
```

### 第五步: 期权链深度分析
⚠️ **关键**: 使用智能优化器推荐的具体到期日
```
options_chain_tool_mcp(
    symbol="{primary_ticker}",
    expiration="[使用第三步返回的optimal_expiration.date，如: 2025-11-27]",
    option_type="put", 
    include_greeks=true
)
```

### 第六步: 分配概率精确计算
⚠️ **关键**: 使用智能优化器推荐的具体到期日
```
option_assignment_probability_tool_mcp(
    symbol="{primary_ticker}",
    strike_price="[从第四步获得的推荐执行价]",
    expiration="[使用第三步返回的optimal_expiration.date，如: 2025-11-27]",
    option_type="put",
    include_delta_comparison=true
)
```

### 第七步: 科学化股票建仓组合配置
```
# 收集所有分析过的策略数据
strategies_data = [
    # 将每个股票的CSP策略结果整理成列表
]

# 使用简化股票分配工具进行科学化建仓权重配置
simplified_stock_allocation_tool_mcp(
    stocks_data=strategies_data,  # 包含分配概率、执行价、当前价格、权利金
    assignment_weight=0.6,        # 分配概率权重60%（更重视获得股票的概率）
    discount_weight=0.4,          # 折扣深度权重40%（适度考虑折扣幅度）
    include_detailed_report=true
)
```

## 🎯 股票建仓专用筛选标准

### 一级筛选 - 基本面健康度
- **财务健康**: ROE ≥ 15%，负债率 ≤ 40%，现金流为正
- **盈利稳定性**: 近5年连续盈利，增长率 ≥ 5%
- **市场地位**: 行业前5，市值 ≥ 500亿美元
- **分红历史**: 稳定分红记录（加分项）

### 二级筛选 - 估值合理性
- **PE估值**: 当前PE ≤ 5年平均PE × 1.2
- **PB估值**: PB ≤ 行业平均 × 1.5
- **PEG比率**: PEG ≤ 1.5（成长性与估值平衡）

### 三级筛选 - 技术面确认
- **趋势位置**: 股价接近50日或200日均线支撑
- **RSI水平**: 30 ≤ RSI ≤ 65（避免超买超卖极端）
- **成交量确认**: 近期成交量正常，无异常放量下跌
- **支撑位强度**: 目标行权价接近关键技术支撑位

### 四级评分 - 建仓优先级
1. **分配概率** (40%权重): 目标Delta 0.35~0.45为满分
2. **价值折扣** (35%权重): 行权价相对当前价格的折扣幅度  
3. **基本面质量** (25%权重): 财务健康度评分

## 📊 股票建仓优化筛选标准

### 建仓导向期权筛选
- **流动性要求**: Bid-Ask价差 ≤ 权利金的15%
- **交易量**: 开放利益(OI) ≥ 300，成交量 ≥ 30
- **Delta范围**: 0.30 ≤ |Delta| ≤ 0.50 (建仓导向)
- **技术支撑**: 执行价位于关键支撑位下方10~20%
- **IV环境**: IV Rank ≥ 25百分位

### 建仓效率排序
1. **分配概率优先** (40%权重):
   - Delta理论概率 + 历史回测验证
   - 目标: ≥{target_allocation_probability}% 满分

2. **折扣获取价值** (35%权重):
   - 有效成本 = 行权价 - 权利金
   - 相对当前价格的折扣幅度
   - 相对内在价值的安全边际

3. **风险调整收益** (25%权重):
   - 年化补偿率: (权利金/现金占用) × (365/到期天数) × 100%
   - 目标: ≥{target_annual_return_pct}% 满分

### 股票获取导向到期日优化验证
- **策略主题匹配**: 验证选择的到期日是否在30-60天建仓优化窗口
- **建仓时间窗口**: 确保给股价充分调整时间达到执行价位
- **事件风险缓冲**: 避开财报等重大事件，但允许合理的市场波动
- **流动性保障**: 优先选择月期权（建仓策略需要更好的流动性）
- **行权概率优化**: 确保Delta范围适合提高股票分配概率

## 🎯 专业输出规格要求

### 必需输出格式
1. **时间基准声明**: 明确声明分析基准时间
2. **到期日优化报告**: 展示智能选择器针对建仓策略的优化过程
3. **建仓策略对比表**: 包含至少3个风险级别的建议
4. **专业订单格式**: JP Morgan风格的交易指令
5. **分配后管理剧本**: 获得股票后的covered call策略
6. **投资组合配置**: 科学化的仓位分配建议

### 股票建仓控制检查清单
- [ ] 所有推荐期权的Delta ≥ -0.50
- [ ] 分配概率≥{target_allocation_probability}%
- [ ] 年化补偿率≥{target_annual_return_pct}%
- [ ] 流动性评分 ≥ B级
- [ ] 距离财报日期 > 7天
- [ ] 智能仓位分配科学合理
- [ ] 最优到期日评分 ≥ 70分

## 💡 建仓执行管理触发器

**欢迎分配条件** (概率{target_allocation_probability}%):
- 基本面无重大变化，估值依然吸引
- 平均成本优于当前市价
- 启动后续covered call策略计划

**权利金管理条件** (概率{100-target_allocation_probability}%):
- 权利金回落至50%时考虑平仓获利
- 滚动到下月同行权价或调低行权价5%

**风险控制触发器**:
- 基本面恶化时强制平仓
- 技术破位时评估是否接受分配
- 根据智能分配结果动态管理仓位风险

## 🔚 最终验证与建仓总结要求

执行完所有工具后，请提供:

1. **建仓策略有效性确认**: 所有推荐是否满足股票获取目标
2. **策略主题验证**: 确认使用了 stock_acquisition_csp_theme 并在30-60天最优范围内
3. **到期日优化验证**: 智能选择器针对建仓策略的评分、数学推理和选择理由
3. **分配概率评估**: 每个推荐的具体分配概率
4. **科学化资金配置**: 基于夏普比率的仓位分配
   - 明确说明每个股票的配置权重计算方法
   - 展示夏普比率计算过程
   - 解释为什么某些股票获得更高权重
5. **建仓时机建议**: 考虑市场环境的最佳开仓时间
6. **分配后管理计划**: covered call策略的执行路径
7. **数学逻辑验证**: 确保所有数学比较和结论正确

## ⚡ 开始执行

请严格按照上述序列执行所有工具，重点关注**股票获取**而非权利金收取，确保所有推荐策略的分配概率≥{target_allocation_probability}%且年化补偿≥{target_annual_return_pct}%。特别注意使用智能到期日选择器优化建仓时机。

---
*免责声明: 本分析仅供参考，期权交易存在重大风险。股票建仓策略涉及资金占用和分配风险，请根据个人风险承受能力谨慎决策。*
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


# 复用现有的tickers解析函数（从income引擎）
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


# 辅助函数用于获取策略示例和使用指导
def get_stock_acquisition_examples() -> Dict[str, Any]:
    """
    获取股票建仓CSP策略使用示例
    
    Returns:
        Dict[str, Any]: 包含使用示例的字典
    """
    return {
        "conservative_acquisition": {
            "description": "保守股票建仓策略",
            "example_call": {
                "tickers": ["SPY", "QQQ", "AAPL"],
                "cash_usd": 50000,
                "target_allocation_probability": 60.0,
                "max_single_position_pct": 20.0,
                "min_days": 30,
                "max_days": 60,
                "target_annual_return_pct": 20.0
            },
            "expected_outcome": "稳健建仓、分配概率60%、年化补偿20%",
            "use_case": "稳健投资者的长期股票积累策略"
        },
        "balanced_acquisition": {
            "description": "平衡股票建仓策略",
            "example_call": {
                "tickers": ["AAPL", "MSFT", "GOOGL"],
                "cash_usd": 100000,
                "target_allocation_probability": 65.0,
                "max_single_position_pct": 25.0,
                "min_days": 21,
                "max_days": 45,
                "target_annual_return_pct": 25.0
            },
            "expected_outcome": "平衡建仓、分配概率65%、年化补偿25%",
            "use_case": "平衡风险收益的股票获取策略"
        },
        "aggressive_acquisition": {
            "description": "激进股票建仓策略",
            "example_call": {
                "tickers": ["TSLA", "NVDA", "AMD"],
                "cash_usd": 200000,
                "target_allocation_probability": 75.0,
                "max_single_position_pct": 35.0,
                "min_days": 21,
                "max_days": 30,
                "target_annual_return_pct": 30.0
            },
            "expected_outcome": "激进建仓、分配概率75%、年化补偿30%",
            "use_case": "追求高分配概率的积极建仓策略"
        }
    }


def get_usage_guidelines() -> List[str]:
    """
    获取股票建仓使用指导原则
    
    Returns:
        List[str]: 使用指导列表
    """
    return [
        "🏗️ 建仓优先: 以获得优质股票为主要目标，权利金为次要考虑",
        "📊 Delta控制: 偏好Delta在0.30-0.50范围内，欢迎分配",
        "⏰ 耐心建仓: 优选21-60天期权，给股价充分调整时间",
        "📈 合理补偿: 目标年化收益率15-35%，作为等待成本",
        "🛡️ 风险管理: 设置明确的仓位控制和分配后管理",
        "📋 专业执行: 使用专业订单格式和执行检查清单",
        "🔄 组合优化: 基于科学方法进行资金配置",
        "📊 数据驱动: 基于基本面和技术分析进行股票筛选"
    ]