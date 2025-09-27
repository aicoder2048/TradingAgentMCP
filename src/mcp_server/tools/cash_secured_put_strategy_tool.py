"""
现金担保看跌期权策略MCP工具

为Claude Code提供专业级的现金担保看跌期权策略分析功能，包括：
- 基于目的的策略选择（收入vs折价买入）
- 智能期权筛选和评分
- 三级风险建议（保守、平衡、激进）
- 专业订单格式化
- 综合市场分析和风险评估
"""

import os
import asyncio
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from ..config.settings import settings
from ...provider.tradier.client import TradierClient
from ...strategy.cash_secured_put import (
    CashSecuredPutAnalyzer,
    StrategyRecommendationEngine,
    ProfessionalOrderFormatter,
    export_csp_analysis_to_csv,
    get_market_context,
    generate_execution_notes
)
from ...option.option_expiration_selector import ExpirationSelector
from ...utils.time import get_market_time_et


async def cash_secured_put_strategy_tool(
    symbol: str,
    purpose_type: str = "income",
    duration: str = "1w", 
    capital_limit: Optional[float] = None,
    include_order_blocks: bool = True,
    min_premium: Optional[float] = None,
    max_delta: Optional[float] = None
) -> Dict[str, Any]:
    """
    现金担保看跌期权策略MCP工具
    
    分析期权链以推荐基于目的（收入vs折价）和时间跨度的最优现金担保看跌期权策略。
    提供专业级的风险分析、P&L建模和执行指导。
    
    Args:
        symbol: 股票代码 (例如: "AAPL", "TSLA", "NVDA")
        purpose_type: 策略目的
            - "income": 收入策略，Delta 10-30%，专注于权利金收取
            - "discount": 折价策略，Delta 30-70%，接受分配风险以折价买入
        duration: 时间跨度
            - "1w": 1周 (5-9天，偏好周度期权)
            - "2w": 2周 (10-18天，偏好周度期权)  
            - "1m": 1月 (25-35天，偏好月度期权)
            - "3m": 3月 (80-100天，偏好月度期权)
            - "6m": 6月 (170-190天，偏好季度期权)
            - "1y": 1年 (350-380天，LEAPS期权)
        capital_limit: 最大资金投入 (可选)
        include_order_blocks: 是否生成专业订单格式
        min_premium: 最小权利金要求 (可选)
        max_delta: 最大Delta限制 (可选)
        
    Returns:
        综合策略分析结果，包含三个风险级别的建议：
        {
            "symbol": "AAPL",
            "current_price": 150.25,
            "analysis_timestamp": "2024-01-15 14:30:00 ET",
            "strategy_parameters": {
                "purpose_type": "income",
                "duration": "1w", 
                "delta_range": {"min": -0.30, "max": -0.10},
                "capital_limit": 50000.00
            },
            "selected_expiration": {
                "date": "2024-01-19",
                "days_to_expiry": 4,
                "type": "weekly",
                "selection_reason": "流动性优秀的周度期权"
            },
            "recommendations": {
                "conservative": {
                    "profile": "conservative",
                    "option_details": {...},
                    "pnl_analysis": {...},
                    "risk_metrics": {...},
                    "recommendation_reasoning": "..."
                },
                "balanced": {...},
                "aggressive": {...}
            },
            "order_blocks": {
                "conservative": "专业订单格式...",
                "balanced": "...",
                "aggressive": "..."
            },
            "market_context": {
                "historical_volatility": 0.23,
                "technical_levels": {...},
                "volatility_regime": "normal"
            },
            "execution_notes": "执行建议和注意事项...",
            "csv_export_path": "./data/csp_AAPL_20240115_143000.csv",
            "status": "success"
        }
    """
    
    try:
        # 参数验证
        symbol = symbol.upper().strip()
        purpose_type = purpose_type.lower().strip()
        duration = duration.lower().strip()
        
        if purpose_type not in ["income", "discount"]:
            return {
                "symbol": symbol,
                "status": "error",
                "error": "invalid_purpose_type",
                "message": "目的类型必须是 'income' 或 'discount'"
            }
        
        if duration not in ["1w", "2w", "1m", "3m", "6m", "1y"]:
            return {
                "symbol": symbol, 
                "status": "error",
                "error": "invalid_duration",
                "message": "持续时间必须是 '1w', '2w', '1m', '3m', '6m', '1y' 之一"
            }
        
        # 初始化组件
        client = TradierClient()
        analyzer = CashSecuredPutAnalyzer(
            symbol=symbol,
            purpose_type=purpose_type,
            duration=duration,
            tradier_client=client
        )
        
        # 获取当前市场数据
        print(f"🔍 获取 {symbol} 的市场数据...")
        quotes = client.get_quotes([symbol])
        if not quotes:
            return {
                "symbol": symbol,
                "status": "error", 
                "error": "no_quote_data",
                "message": f"无法获取 {symbol} 的市场报价数据"
            }
        
        underlying_price = quotes[0].last
        if not underlying_price or underlying_price <= 0:
            return {
                "symbol": symbol,
                "status": "error",
                "error": "invalid_price",
                "message": f"{symbol} 的价格数据无效或为零"
            }
        
        print(f"💰 {symbol} 当前价格: ${underlying_price:.2f}")
        
        # 选择最优到期日
        print(f"📅 为 {duration} 策略选择最优到期日...")
        expiration_selector = ExpirationSelector(client)
        expiration_result = await expiration_selector.get_optimal_expiration(
            symbol=symbol,
            duration=duration
        )
        
        selected_expiration = expiration_result.selected_date
        exp_metadata = expiration_result.metadata
        
        print(f"✅ 选择到期日: {selected_expiration} ({exp_metadata['actual_days']}天)")
        
        # 应用自定义限制
        if max_delta:
            delta_range = analyzer.delta_ranges[purpose_type]
            analyzer.delta_ranges[purpose_type] = {
                "min": delta_range["min"],
                "max": min(delta_range["max"], max_delta)
            }
        
        # 分析期权链
        print(f"🔬 分析 {symbol} {selected_expiration} 期权链...")
        optimal_strikes = await analyzer.find_optimal_strikes(
            expiration=selected_expiration,
            underlying_price=underlying_price,
            capital_limit=capital_limit
        )
        
        # 应用权利金过滤
        if min_premium and optimal_strikes:
            optimal_strikes = [
                opt for opt in optimal_strikes 
                if opt.get("premium", 0) >= min_premium
            ]
        
        if not optimal_strikes:
            return {
                "symbol": symbol,
                "status": "no_suitable_options",
                "message": f"未找到符合{purpose_type}策略和{duration}期限要求的期权",
                "details": {
                    "current_price": underlying_price,
                    "checked_expiration": selected_expiration,
                    "delta_range": analyzer.delta_ranges[purpose_type],
                    "capital_limit": capital_limit,
                    "min_premium": min_premium,
                    "filters_applied": {
                        "capital_limit": capital_limit is not None,
                        "min_premium": min_premium is not None,
                        "max_delta": max_delta is not None
                    }
                }
            }
        
        print(f"🎯 找到 {len(optimal_strikes)} 个符合条件的期权")
        
        # 生成三级策略推荐
        print("🏗️ 生成策略推荐...")
        recommendation_engine = StrategyRecommendationEngine()
        recommendations = recommendation_engine.generate_three_alternatives(
            analyzed_options=optimal_strikes,
            underlying_price=underlying_price,
            purpose_type=purpose_type
        )
        
        if not recommendations:
            return {
                "symbol": symbol,
                "status": "no_recommendations",
                "message": "无法生成有效的策略推荐",
                "raw_options_count": len(optimal_strikes)
            }
        
        print(f"📊 生成了 {len(recommendations)} 个策略推荐")
        
        # 生成专业订单格式
        order_blocks = {}
        if include_order_blocks:
            print("📝 生成专业订单格式...")
            formatter = ProfessionalOrderFormatter()
            for profile, rec in recommendations.items():
                try:
                    order_blocks[profile] = formatter.format_order_block(rec)
                except Exception as e:
                    print(f"⚠️ 生成{profile}订单格式时出错: {e}")
                    order_blocks[profile] = f"订单格式生成错误: {str(e)}"
        
        # 获取市场上下文
        print("🌍 获取市场上下文信息...")
        market_context = await get_market_context(symbol, client)
        
        # 导出CSV数据
        print("💾 导出分析数据到CSV...")
        csv_path = await export_csp_analysis_to_csv(
            symbol=symbol,
            recommendations=recommendations,
            analyzed_options=optimal_strikes
        )
        
        # 生成执行说明
        execution_notes = generate_execution_notes(recommendations, purpose_type)
        
        # 构建完整响应
        result = {
            "symbol": symbol,
            "current_price": underlying_price,
            "analysis_timestamp": get_market_time_et(),
            "strategy_parameters": {
                "purpose_type": purpose_type,
                "duration": duration,
                "delta_range": analyzer.delta_ranges[purpose_type],
                "capital_limit": capital_limit,
                "min_premium": min_premium,
                "max_delta": max_delta
            },
            "selected_expiration": {
                "date": selected_expiration,
                "days_to_expiry": exp_metadata["actual_days"],
                "type": exp_metadata.get("expiration_type", "unknown"),
                "selection_reason": expiration_result.selection_reason,
                "liquidity_score": exp_metadata.get("liquidity_score"),
                "alternative_count": len(expiration_result.alternatives)
            },
            "recommendations": recommendations,
            "order_blocks": order_blocks if include_order_blocks else None,
            "market_context": market_context,
            "execution_notes": execution_notes,
            "csv_export_path": csv_path,
            "analysis_summary": {
                "total_options_analyzed": len(optimal_strikes),
                "recommendations_generated": len(recommendations),
                "best_recommendation": max(recommendations.keys(), 
                    key=lambda k: recommendations[k]["option_details"]["composite_score"]) if recommendations else None,
                "avg_annualized_return": sum(
                    rec["pnl_analysis"]["annualized_return"] for rec in recommendations.values()
                ) / len(recommendations) if recommendations else 0,
                "avg_assignment_probability": sum(
                    rec["risk_metrics"]["assignment_probability"] for rec in recommendations.values()
                ) / len(recommendations) if recommendations else 0
            },
            "status": "success"
        }
        
        print(f"✅ {symbol} CSP策略分析完成")
        return result
        
    except Exception as e:
        # 详细错误处理
        error_trace = traceback.format_exc()
        print(f"❌ CSP策略工具错误: {str(e)}")
        print(f"错误堆栈: {error_trace}")
        
        return {
            "symbol": symbol if 'symbol' in locals() else "UNKNOWN",
            "status": "error",
            "error": type(e).__name__,
            "message": f"生成CSP策略推荐时发生错误: {str(e)}",
            "error_details": {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": error_trace if settings.debug else None
            },
            "analysis_timestamp": datetime.now().isoformat()
        }


# 辅助函数

async def validate_csp_parameters(
    symbol: str,
    purpose_type: str,
    duration: str,
    capital_limit: Optional[float] = None
) -> Dict[str, Any]:
    """
    验证CSP策略参数
    
    Args:
        symbol: 股票代码
        purpose_type: 策略目的
        duration: 时间跨度
        capital_limit: 资金限制
        
    Returns:
        验证结果字典
    """
    errors = []
    warnings = []
    
    # 验证股票代码
    if not symbol or len(symbol.strip()) == 0:
        errors.append("股票代码不能为空")
    elif len(symbol.strip()) > 10:
        errors.append("股票代码过长")
    
    # 验证目的类型
    if purpose_type not in ["income", "discount"]:
        errors.append("目的类型必须是 'income' 或 'discount'")
    
    # 验证持续时间
    valid_durations = ["1w", "2w", "1m", "3m", "6m", "1y"]
    if duration not in valid_durations:
        errors.append(f"持续时间必须是 {valid_durations} 之一")
    
    # 验证资金限制
    if capital_limit is not None:
        if capital_limit <= 0:
            errors.append("资金限制必须大于0")
        elif capital_limit < 1000:
            warnings.append("资金限制过小，可能无法找到合适的期权")
        elif capital_limit > 1000000:
            warnings.append("资金限制很大，建议分散投资")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def get_strategy_examples() -> Dict[str, Any]:
    """
    获取CSP策略示例
    
    Returns:
        策略示例字典
    """
    return {
        "income_strategies": {
            "conservative_weekly": {
                "purpose_type": "income",
                "duration": "1w",
                "description": "保守周度收入策略",
                "target_delta": "10-20%",
                "expected_return": "年化8-15%",
                "risk_profile": "低",
                "use_case": "稳定收入，低分配概率"
            },
            "balanced_monthly": {
                "purpose_type": "income", 
                "duration": "1m",
                "description": "平衡月度收入策略",
                "target_delta": "15-25%",
                "expected_return": "年化12-20%",
                "risk_profile": "中等",
                "use_case": "收入与增长平衡"
            }
        },
        "discount_strategies": {
            "aggressive_weekly": {
                "purpose_type": "discount",
                "duration": "1w", 
                "description": "激进周度折价策略",
                "target_delta": "30-50%",
                "expected_return": "年化15-25%",
                "risk_profile": "高",
                "use_case": "寻求以折价买入优质股票"
            },
            "patient_monthly": {
                "purpose_type": "discount",
                "duration": "1m",
                "description": "耐心月度折价策略", 
                "target_delta": "35-45%",
                "expected_return": "年化18-28%",
                "risk_profile": "中高",
                "use_case": "长期投资者的入场策略"
            }
        },
        "usage_tips": [
            "收入策略适合不想被分配股票的投资者",
            "折价策略适合愿意持有股票的长期投资者",
            "周度期权流动性更好但时间衰减更快",
            "月度期权提供更多权利金但流动性稍差",
            "建议根据市场波动率调整策略频率"
        ]
    }


def format_strategy_summary(result: Dict[str, Any]) -> str:
    """
    格式化策略摘要
    
    Args:
        result: CSP策略分析结果
        
    Returns:
        格式化的摘要字符串
    """
    if result.get("status") != "success":
        return f"策略分析失败: {result.get('message', '未知错误')}"
    
    symbol = result["symbol"]
    price = result["current_price"]
    purpose = result["strategy_parameters"]["purpose_type"]
    duration = result["strategy_parameters"]["duration"]
    
    summary_lines = [
        f"🎯 {symbol} 现金担保看跌期权策略分析",
        f"📊 当前价格: ${price:.2f}",
        f"🔄 策略类型: {purpose} | 期限: {duration}",
        ""
    ]
    
    recommendations = result.get("recommendations", {})
    if recommendations:
        summary_lines.append("💡 推荐策略:")
        for profile, rec in recommendations.items():
            opt = rec["option_details"]
            pnl = rec["pnl_analysis"]
            
            profile_name = {"conservative": "保守", "balanced": "平衡", "aggressive": "激进"}[profile]
            summary_lines.append(
                f"  {profile_name}: ${opt['strike']:.2f} 执行价, "
                f"{pnl['annualized_return']:.1f}% 年化收益, "
                f"{rec['risk_metrics']['assignment_probability']:.1f}% 分配概率"
            )
    
    execution_notes = result.get("execution_notes", "")
    if execution_notes:
        summary_lines.extend(["", "📋 执行要点:", execution_notes])
    
    return "\n".join(summary_lines)