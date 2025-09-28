"""
期权到期日管理MCP工具
提供期权到期日查询、筛选和管理功能的MCP接口。
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from ...option.option_expiration_dates import (
    get_option_expiration_dates,
    get_next_expiration_date,
    get_weekly_expirations,
    get_monthly_expirations,
    filter_expirations_by_days,
    summarize_expirations
)


async def get_option_expirations_tool(
    symbol: str,
    min_days: Optional[int] = None,
    max_days: Optional[int] = None
) -> Dict[str, Any]:
    """
    获取期权到期日列表，支持按天数过滤。
    
    Args:
        symbol: 股票代码 (例如: "AAPL", "TSLA", "NVDA")
        min_days: 最小到期天数过滤 (可选)
        max_days: 最大到期天数过滤 (可选)
    
    Returns:
        包含到期日信息列表和统计摘要的字典
    """
    try:
        # 使用异步包装器运行同步函数
        loop = asyncio.get_event_loop()
        expirations = await loop.run_in_executor(
            None,
            get_option_expiration_dates,
            symbol,
            min_days,
            max_days,
            None  # tradier_client 将使用默认实例
        )
        
        # 生成统计摘要
        summary = summarize_expirations(expirations)
        
        return {
            "status": "success",
            "symbol": symbol,
            "filters": {
                "min_days": min_days,
                "max_days": max_days
            },
            "expirations": expirations,
            "summary": summary,
            "timestamp": datetime.now().isoformat(),
            "建议": [
                "使用返回的到期日列表进行期权策略分析",
                "注意检查 days_to_expiration 字段来选择合适的时间窗口",
                "expiration_type 字段标识标准期权或周期权",
                "available_strikes 提供该到期日可用的执行价格列表"
            ]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "symbol": symbol,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "建议": [
                "请检查股票代码是否正确",
                "请确认该股票有可用的期权",
                "请检查 Tradier API 访问令牌是否有效",
                "如果问题持续，请稍后重试"
            ]
        }


async def get_next_expiration_tool(symbol: str) -> Dict[str, Any]:
    """
    获取下一个最近的期权到期日。
    
    Args:
        symbol: 股票代码 (例如: "AAPL", "TSLA", "NVDA")
    
    Returns:
        包含下一个到期日信息的字典
    """
    try:
        loop = asyncio.get_event_loop()
        next_date = await loop.run_in_executor(
            None,
            get_next_expiration_date,
            symbol,
            None  # tradier_client
        )
        
        if next_date is None:
            return {
                "status": "no_data",
                "symbol": symbol,
                "message": f"未找到 {symbol} 的可用期权到期日",
                "timestamp": datetime.now().isoformat()
            }
        
        # 获取详细信息
        expirations = await loop.run_in_executor(
            None,
            get_option_expiration_dates,
            symbol,
            0,  # min_days
            7,  # max_days - 只获取一周内的
            None
        )
        
        next_exp_details = None
        for exp in expirations:
            if exp["date"] == next_date:
                next_exp_details = exp
                break
        
        return {
            "status": "success",
            "symbol": symbol,
            "next_expiration": {
                "date": next_date,
                "details": next_exp_details
            },
            "timestamp": datetime.now().isoformat(),
            "建议": [
                f"下一个到期日是 {next_date}",
                "可以使用此日期调用 options_chain_tool 获取期权链数据",
                "建议检查该到期日的流动性和可用执行价格"
            ]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "symbol": symbol,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def get_weekly_expirations_tool(
    symbol: str,
    weeks: int = 4
) -> Dict[str, Any]:
    """
    获取未来几周的周期权到期日。
    
    Args:
        symbol: 股票代码 (例如: "AAPL", "TSLA", "NVDA")
        weeks: 获取未来几周的到期日 (默认: 4)
    
    Returns:
        包含周期权到期日列表的字典
    """
    try:
        loop = asyncio.get_event_loop()
        weekly_exps = await loop.run_in_executor(
            None,
            get_weekly_expirations,
            symbol,
            weeks,
            None  # tradier_client
        )
        
        summary = summarize_expirations(weekly_exps)
        
        return {
            "status": "success",
            "symbol": symbol,
            "weeks_requested": weeks,
            "weekly_expirations": weekly_exps,
            "summary": summary,
            "timestamp": datetime.now().isoformat(),
            "说明": {
                "周期权特点": "通常在每周五到期，提供更灵活的时间选择",
                "适用策略": "短期收入策略、时间衰减策略、事件驱动策略",
                "建议用途": "7-28天的现金担保PUT或备兑看涨策略"
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "symbol": symbol,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def get_monthly_expirations_tool(
    symbol: str,
    months: int = 6
) -> Dict[str, Any]:
    """
    获取未来几个月的月期权到期日。
    
    Args:
        symbol: 股票代码 (例如: "AAPL", "TSLA", "NVDA")
        months: 获取未来几个月的到期日 (默认: 6)
    
    Returns:
        包含月期权到期日列表的字典
    """
    try:
        loop = asyncio.get_event_loop()
        monthly_exps = await loop.run_in_executor(
            None,
            get_monthly_expirations,
            symbol,
            months,
            None  # tradier_client
        )
        
        summary = summarize_expirations(monthly_exps)
        
        return {
            "status": "success",
            "symbol": symbol,
            "months_requested": months,
            "monthly_expirations": monthly_exps,
            "summary": summary,
            "timestamp": datetime.now().isoformat(),
            "说明": {
                "月期权特点": "通常在每月第三个周五到期，流动性较好",
                "适用策略": "中长期投资策略、波动率策略、资产配置",
                "建议用途": "30天以上的期权策略，更适合机构投资者"
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "symbol": symbol,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def filter_expirations_by_days_tool(
    symbol: str,
    min_days: int = 7,
    max_days: int = 28
) -> Dict[str, Any]:
    """
    获取指定天数范围内的期权到期日。
    
    这是一个针对特定策略优化的工具，特别适合收入生成策略。
    
    Args:
        symbol: 股票代码 (例如: "AAPL", "TSLA", "NVDA")
        min_days: 最小天数 (默认: 7)
        max_days: 最大天数 (默认: 28)
    
    Returns:
        包含过滤后期权到期日的字典
    """
    try:
        loop = asyncio.get_event_loop()
        
        # 先获取所有到期日
        all_expirations = await loop.run_in_executor(
            None,
            get_option_expiration_dates,
            symbol,
            None,
            None,
            None
        )
        
        # 应用天数过滤
        filtered_exps = filter_expirations_by_days(
            all_expirations,
            min_days,
            max_days
        )
        
        summary = summarize_expirations(filtered_exps)
        
        # 为收入策略提供额外建议
        strategy_advice = []
        if 7 <= min_days <= 14 and 21 <= max_days <= 35:
            strategy_advice.extend([
                "🎯 此时间窗口适合高频收入策略",
                "⚡ 时间衰减较快，适合卖出期权收取权利金",
                "💰 建议选择Delta 0.15-0.25的期权以平衡收入和风险"
            ])
        elif max_days <= 7:
            strategy_advice.extend([
                "⚠️ 极短期策略，风险较高",
                "🎲 适合经验丰富的交易者",
                "📊 需要密切监控市场变化"
            ])
        
        return {
            "status": "success",
            "symbol": symbol,
            "filter_criteria": {
                "min_days": min_days,
                "max_days": max_days
            },
            "filtered_expirations": filtered_exps,
            "summary": summary,
            "strategy_advice": strategy_advice,
            "timestamp": datetime.now().isoformat(),
            "next_steps": [
                f"使用返回的到期日调用 options_chain_tool 获取期权链",
                "分析每个到期日的流动性和价差",
                "选择最符合策略目标的到期日进行深入分析"
            ]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "symbol": symbol,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }