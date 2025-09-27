"""
Covered Call Strategy MCP Tool

Provides comprehensive covered call strategy analysis for stock positions,
generating professional recommendations for income generation and position exit strategies.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from ..config.settings import settings
from ...provider.tradier.client import TradierClient
from ...strategy.covered_call import (
    CoveredCallAnalyzer,
    CoveredCallRecommendationEngine,
    CoveredCallOrderFormatter,
    export_cc_analysis_to_csv,
    get_cc_market_context,
    generate_cc_execution_notes
)
from ...option.option_expiration_selector import ExpirationSelector
from ...utils.time import get_market_time_et
from ...strategy.performance_optimizer import (
    performance_monitor,
    optimizer,
    error_manager,
    timeout_manager,
    optimize_large_position_analysis
)
from ...strategy.error_handling import error_handler, RecoveryStrategies


async def covered_call_strategy_tool(
    symbol: str,
    purpose_type: str = "income",
    duration: str = "1w",
    shares_owned: int = 100,
    avg_cost: Optional[float] = None,
    min_premium: Optional[float] = None,
    include_order_blocks: bool = True
) -> Dict[str, Any]:
    """
    Covered Call Strategy MCP Tool
    
    分析期权链以推荐最优covered call策略，用于收入生成和战略减仓。
    基于现有股票持仓，提供专业级的期权策略分析和风险评估。
    
    Args:
        symbol: 股票代码 (e.g., "AAPL", "TSLA", "NVDA")
        purpose_type: 策略目的 - "income" (收入导向) 或 "exit" (减仓导向)
        duration: 时间周期 - "1w", "2w", "1m", "3m", "6m", "1y"
        shares_owned: 持有股票数量 (必须 >= 100)
        avg_cost: 每股平均成本基础 (可选，用于税务分析)
        min_premium: 最低权利金门槛 (可选)
        include_order_blocks: 生成专业订单格式
        
    Returns:
        包含策略分析和三种风险级别建议的综合结果:
        {
            "symbol": "AAPL",
            "current_price": 150.25,
            "analysis_timestamp": "2024-01-15 14:30:00 ET",
            "strategy_parameters": {...},
            "position_validation": {
                "shares_owned": 500,
                "contracts_available": 5,
                "position_value": 75125.00
            },
            "selected_expiration": {
                "date": "2024-01-19",
                "days_to_expiry": 4,
                "type": "weekly"
            },
            "recommendations": {
                "conservative": {...},
                "balanced": {...},
                "aggressive": {...}
            },
            "market_context": {
                "implied_volatility": 0.25,
                "iv_rank": 45,
                "resistance_levels": {...}
            },
            "order_blocks": {...},
            "csv_export_path": "./data/cc_AAPL_20240115_143000.csv",
            "execution_notes": "...",
            "status": "success"
        }
    """
    
    try:
        # 参数验证
        symbol = symbol.upper().strip()
        
        # 持仓验证
        if shares_owned < 100:
            return {
                "symbol": symbol,
                "status": "insufficient_shares",
                "error": "Covered call策略需要至少100股持仓",
                "shares_owned": shares_owned,
                "shares_needed": 100,
                "message": f"当前持有{shares_owned}股，需要至少100股才能写入1份call期权合约"
            }
        
        # 策略类型验证
        valid_purposes = ["income", "exit"]
        if purpose_type not in valid_purposes:
            return {
                "symbol": symbol,
                "status": "invalid_parameters",
                "error": f"策略类型必须是 {valid_purposes} 之一",
                "provided": purpose_type
            }
        
        # 初始化组件
        client = TradierClient()
        analyzer = CoveredCallAnalyzer(
            symbol=symbol,
            purpose_type=purpose_type,
            duration=duration,
            shares_owned=shares_owned,
            avg_cost=avg_cost,
            tradier_client=client
        )
        
        # 获取当前市场数据
        print(f"获取 {symbol} 的市场数据...")
        quotes = client.get_quotes([symbol])
        if not quotes:
            return {
                "symbol": symbol,
                "status": "market_data_error",
                "error": f"无法获取 {symbol} 的市场报价",
                "message": "请检查股票代码是否正确或市场是否开放"
            }
        
        quote = quotes[0]
        underlying_price = quote.last
        
        # 持仓价值验证
        position_value = underlying_price * shares_owned
        contracts_available = shares_owned // 100
        
        print(f"当前股价: ${underlying_price:.2f}, 持仓价值: ${position_value:,.2f}")
        print(f"可写入合约数: {contracts_available}")
        
        # 选择最优到期日
        print(f"选择 {duration} 期限的最优到期日...")
        expiration_selector = ExpirationSelector(client)
        expiration_result = await expiration_selector.get_optimal_expiration(
            symbol=symbol,
            duration=duration
        )
        
        if not expiration_result:
            return {
                "symbol": symbol,
                "status": "no_expiration_available",
                "error": f"无法找到适合 {duration} 期限的期权到期日",
                "duration": duration
            }
        
        expiration = expiration_result.selected_date
        exp_metadata = expiration_result.metadata
        print(f"选定到期日: {expiration} ({exp_metadata.get('actual_days', 0)}天)")
        
        # 获取技术阻力位
        print("计算技术阻力位...")
        resistance_levels = client.calculate_resistance_levels(symbol)
        
        # 分析期权链
        print(f"分析 {purpose_type} 策略的call期权...")
        optimal_strikes = await analyzer.find_optimal_strikes(
            expiration=expiration,
            underlying_price=underlying_price,
            min_premium=min_premium
        )
        
        if not optimal_strikes:
            return {
                "symbol": symbol,
                "status": "no_suitable_options",
                "message": f"未找到符合 {purpose_type} 策略标准的call期权",
                "criteria": {
                    "purpose_type": purpose_type,
                    "duration": duration,
                    "expiration_checked": expiration,
                    "delta_range": analyzer.delta_ranges[purpose_type],
                    "min_premium": min_premium
                },
                "current_price": underlying_price,
                "shares_owned": shares_owned,
                "suggestion": "尝试调整期限或降低最低权利金要求"
            }
        
        print(f"找到 {len(optimal_strikes)} 个符合条件的期权")
        
        # 生成策略建议
        print("生成三级风险建议...")
        recommendation_engine = CoveredCallRecommendationEngine()
        recommendations = recommendation_engine.generate_three_alternatives(
            analyzed_options=optimal_strikes,
            underlying_price=underlying_price,
            purpose_type=purpose_type,
            shares_owned=shares_owned
        )
        
        if not recommendations:
            return {
                "symbol": symbol,
                "status": "no_recommendations",
                "error": "无法生成有效的策略建议",
                "analyzed_options_count": len(optimal_strikes)
            }
        
        # 生成专业订单块
        order_blocks = {}
        if include_order_blocks:
            print("生成专业订单格式...")
            formatter = CoveredCallOrderFormatter()
            for profile, rec in recommendations.items():
                try:
                    order_blocks[profile] = formatter.format_order_block(rec)
                except Exception as e:
                    print(f"生成 {profile} 订单块时出错: {e}")
                    order_blocks[profile] = f"订单格式化错误: {str(e)}"
        
        # 获取市场环境分析
        print("分析市场环境...")
        market_context = await get_cc_market_context(symbol, client, resistance_levels)
        
        # 导出CSV数据
        print("导出分析结果到CSV...")
        csv_path = await export_cc_analysis_to_csv(
            symbol=symbol,
            recommendations=recommendations,
            analyzed_options=optimal_strikes
        )
        
        # 生成执行说明
        execution_notes = generate_cc_execution_notes(
            recommendations=recommendations,
            purpose_type=purpose_type,
            shares_owned=shares_owned
        )
        
        # 构建完整结果
        result = {
            "symbol": symbol,
            "current_price": underlying_price,
            "analysis_timestamp": get_market_time_et(),
            "strategy_parameters": {
                "purpose_type": purpose_type,
                "duration": duration,
                "delta_range": analyzer.delta_ranges[purpose_type],
                "min_premium": min_premium,
                "min_liquidity_requirements": {
                    "open_interest": analyzer.min_open_interest,
                    "volume": analyzer.min_volume,
                    "max_spread_pct": analyzer.max_bid_ask_spread_pct
                }
            },
            "position_validation": {
                "shares_owned": shares_owned,
                "contracts_available": contracts_available,
                "position_value": position_value,
                "avg_cost": avg_cost,
                "unrealized_pnl": (underlying_price - avg_cost) * shares_owned if avg_cost else None
            },
            "selected_expiration": {
                "date": expiration,
                "days_to_expiry": exp_metadata.get("actual_days", 0),
                "expiration_type": exp_metadata.get("expiration_type", "unknown"),
                "selection_reason": expiration_result.selection_reason
            },
            "recommendations": recommendations,
            "order_blocks": order_blocks if include_order_blocks else None,
            "market_context": market_context,
            "technical_analysis": {
                "resistance_levels": resistance_levels,
                "options_analyzed": len(optimal_strikes),
                "suitable_strikes_found": len(recommendations)
            },
            "csv_export_path": csv_path,
            "execution_notes": execution_notes,
            "status": "success",
            "disclaimer": "此分析仅供参考，不构成投资建议。期权交易存在风险，可能导致全部投资损失。"
        }
        
        print(f"✅ Covered call分析完成: {len(recommendations)}个建议生成")
        return result
        
    except ValueError as ve:
        # 已知的验证错误
        return {
            "symbol": symbol,
            "status": "validation_error",
            "error": str(ve),
            "shares_owned": shares_owned
        }
        
    except Exception as e:
        # 未预期的错误
        print(f"Covered call策略分析出错: {e}")
        return {
            "symbol": symbol,
            "status": "analysis_error",
            "error": str(e),
            "message": "分析过程中发生错误，请稍后重试",
            "shares_owned": shares_owned,
            "parameters": {
                "purpose_type": purpose_type,
                "duration": duration,
                "min_premium": min_premium
            }
        }


def validate_cc_parameters(
    symbol: str,
    purpose_type: str,
    duration: str,
    shares_owned: int,
    avg_cost: Optional[float] = None,
    min_premium: Optional[float] = None
) -> Dict[str, Any]:
    """
    验证covered call策略参数
    
    Returns:
        验证结果字典，包含is_valid和任何错误信息
    """
    errors = []
    
    # 股票代码验证
    if not symbol or not symbol.strip():
        errors.append("股票代码不能为空")
    elif len(symbol.strip()) > 5:
        errors.append("股票代码长度不能超过5个字符")
    
    # 策略类型验证
    valid_purposes = ["income", "exit"]
    if purpose_type not in valid_purposes:
        errors.append(f"策略类型必须是 {valid_purposes} 之一")
    
    # 持股数量验证
    if shares_owned < 100:
        errors.append("covered call策略需要至少100股持仓")
    elif shares_owned % 100 != 0:
        errors.append(f"建议持股数量为100的倍数以最大化期权合约利用率 (当前: {shares_owned})")
    
    # 平均成本验证
    if avg_cost is not None and avg_cost <= 0:
        errors.append("平均成本必须为正数")
    
    # 最低权利金验证
    if min_premium is not None and min_premium <= 0:
        errors.append("最低权利金必须为正数")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": []
    }


def get_strategy_examples() -> Dict[str, Dict[str, Any]]:
    """
    获取策略使用示例
    
    Returns:
        各种场景的使用示例
    """
    return {
        "income_weekly": {
            "description": "周度收入策略 - 持有AAPL股票，每周收取权利金",
            "parameters": {
                "symbol": "AAPL",
                "purpose_type": "income",
                "duration": "1w",
                "shares_owned": 500,
                "avg_cost": 150.00
            },
            "expected_outcome": "低风险收入生成，保留大部分上涨潜力"
        },
        "exit_monthly": {
            "description": "月度减仓策略 - 在目标价位减仓TSLA",
            "parameters": {
                "symbol": "TSLA",
                "purpose_type": "exit",
                "duration": "1m",
                "shares_owned": 200,
                "avg_cost": 200.00,
                "min_premium": 5.00
            },
            "expected_outcome": "在预定价位减仓，获得额外权利金收入"
        },
        "large_position": {
            "description": "大仓位管理 - 1000股NVDA分批策略",
            "parameters": {
                "symbol": "NVDA",
                "purpose_type": "income",
                "duration": "2w",
                "shares_owned": 1000,
                "avg_cost": 450.00
            },
            "expected_outcome": "大仓位分批管理，平衡收入与风险"
        }
    }


def format_strategy_summary(result: Dict[str, Any]) -> str:
    """
    格式化策略分析摘要
    
    Args:
        result: covered_call_strategy_tool的返回结果
        
    Returns:
        格式化的中文摘要
    """
    if result.get("status") != "success":
        return f"❌ 分析失败: {result.get('error', '未知错误')}"
    
    symbol = result.get("symbol", "N/A")
    current_price = result.get("current_price", 0)
    recommendations = result.get("recommendations", {})
    position = result.get("position_validation", {})
    
    summary_lines = [
        f"📊 {symbol} Covered Call策略分析",
        f"💰 当前股价: ${current_price:.2f}",
        f"📈 持仓: {position.get('shares_owned', 0)}股 ({position.get('contracts_available', 0)}个合约)",
        "",
        "🎯 策略建议:"
    ]
    
    for profile, rec in recommendations.items():
        if rec:
            option = rec.get("option_details", {})
            pnl = rec.get("pnl_analysis", {})
            
            profile_emoji = {"conservative": "🔒", "balanced": "⚖️", "aggressive": "🚀"}.get(profile, "📋")
            summary_lines.append(
                f"  {profile_emoji} {profile.title()}: "
                f"${option.get('strike', 0):.2f}执行价, "
                f"{pnl.get('annualized_return', 0):.1f}%年化收益"
            )
    
    csv_path = result.get("csv_export_path", "")
    if csv_path:
        summary_lines.append(f"\n📄 详细分析已保存至: {csv_path}")
    
    return "\n".join(summary_lines)