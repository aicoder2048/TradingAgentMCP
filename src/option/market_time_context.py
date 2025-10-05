"""
市场时间上下文计算模块

计算第一个交易日的有效交易时间比例，用于限价单成交概率预测。
支持盘前、盘中、盘后不同时段的准确建模。
"""

from datetime import datetime, time
from typing import Dict, Any

from src.market.hours import get_market_status, is_trading_day
from src.market.config import MARKET_CONFIG


def calculate_first_day_context(eastern_time: datetime) -> Dict[str, Any]:
    """
    计算第一交易日的市场时间上下文

    根据当前市场时间（盘前/盘中/盘后/休市），计算第一个交易日的
    有效交易时间比例。这对于准确预测限价单成交概率至关重要。

    Args:
        eastern_time: 美东时间 datetime 对象

    Returns:
        {
            "first_day_fraction": float,      # 0.0-1.0，第一交易日的有效时间比例
            "first_day_is_today": bool,       # 第一交易日是否是今天
            "market_session": str,            # 当前市场时段
            "explanation": str,               # 人类可读的说明
            "remaining_hours": float,         # 剩余交易小时数（仅盘中）
            "total_trading_hours": float      # 总交易小时数
        }

    Examples:
        # 盘前 8:00 AM
        >>> ctx = calculate_first_day_context(datetime(2025, 10, 5, 8, 0))
        >>> ctx["first_day_fraction"]
        1.0
        >>> ctx["first_day_is_today"]
        True

        # 盘中 12:00 PM (noon)
        >>> ctx = calculate_first_day_context(datetime(2025, 10, 5, 12, 0))
        >>> ctx["first_day_fraction"]
        0.615  # 剩余 4 小时 / 6.5 小时

        # 盘后 6:00 PM
        >>> ctx = calculate_first_day_context(datetime(2025, 10, 5, 18, 0))
        >>> ctx["first_day_fraction"]
        1.0
        >>> ctx["first_day_is_today"]
        False
    """
    # 获取当前市场状态
    market_status = get_market_status(eastern_time)
    is_today_trading = is_trading_day(eastern_time)

    # 解析配置时间
    market_open = time.fromisoformat(MARKET_CONFIG["market_open"])      # 09:30
    market_close = time.fromisoformat(MARKET_CONFIG["market_close"])    # 16:00

    # 计算总交易时间（小时）
    total_hours = (market_close.hour - market_open.hour) + \
                  (market_close.minute - market_open.minute) / 60.0  # 6.5 小时

    # 计算总交易分钟数
    total_minutes = (market_close.hour - market_open.hour) * 60 + \
                    (market_close.minute - market_open.minute)  # 390 分钟

    # 情况 1: 非交易日或休市 → 第一交易日是下一个交易日（完整）
    if not is_today_trading or market_status == "closed":
        return {
            "first_day_fraction": 1.0,
            "first_day_is_today": False,
            "market_session": market_status,
            "explanation": "第一交易日是下一交易日（完整交易日）",
            "remaining_hours": total_hours,
            "total_trading_hours": total_hours,
            "trading_hours_display": {
                "label": "下一交易日可用时间",
                "value": total_hours,
                "full_text": f"下一交易日可用时间: {total_hours}小时"
            }
        }

    current_time = eastern_time.time()

    # 情况 2: 盘前 → 今天是第一交易日，完整时间
    if market_status == "pre-market":
        return {
            "first_day_fraction": 1.0,
            "first_day_is_today": True,
            "market_session": "pre-market",
            "explanation": "第一交易日是今天（完整交易日，盘前）",
            "remaining_hours": total_hours,
            "total_trading_hours": total_hours,
            "trading_hours_display": {
                "label": "今日完整交易时间",
                "value": total_hours,
                "full_text": f"今日完整交易时间: {total_hours}小时"
            }
        }

    # 情况 3: 盘中 → 今天是第一交易日，计算剩余时间
    elif market_status == "market":
        # 计算当前时间的分钟数（从午夜开始）
        current_minutes = current_time.hour * 60 + current_time.minute
        market_open_minutes = market_open.hour * 60 + market_open.minute
        market_close_minutes = market_close.hour * 60 + market_close.minute

        # 计算剩余分钟数
        remaining_minutes = market_close_minutes - current_minutes

        # 计算剩余时间比例
        fraction = remaining_minutes / total_minutes

        # 计算剩余小时数
        remaining_hours = remaining_minutes / 60.0

        return {
            "first_day_fraction": max(0.0, min(1.0, fraction)),  # 确保在 [0, 1] 范围内
            "first_day_is_today": True,
            "market_session": "market",
            "explanation": f"第一交易日是今天（剩余 {fraction*100:.0f}% 交易时间，约 {remaining_hours:.1f} 小时）",
            "remaining_hours": max(0.0, remaining_hours),
            "total_trading_hours": total_hours,
            "trading_hours_display": {
                "label": "今日剩余交易时间",
                "value": max(0.0, remaining_hours),
                "full_text": f"今日剩余交易时间: {max(0.0, remaining_hours):.1f}小时"
            }
        }

    # 情况 4: 盘后 → 今天已结束，第一交易日是下一个交易日
    else:  # after-hours
        return {
            "first_day_fraction": 1.0,
            "first_day_is_today": False,
            "market_session": "after-hours",
            "explanation": "第一交易日是下一交易日（完整交易日，盘后）",
            "remaining_hours": total_hours,
            "total_trading_hours": total_hours,
            "trading_hours_display": {
                "label": "下一交易日可用时间",
                "value": total_hours,
                "full_text": f"下一交易日可用时间: {total_hours}小时"
            }
        }


def format_market_context_summary(context: Dict[str, Any]) -> str:
    """
    格式化市场上下文为人类可读的摘要

    Args:
        context: calculate_first_day_context() 的返回结果

    Returns:
        格式化的摘要字符串

    Example:
        >>> summary = format_market_context_summary(context)
        >>> print(summary)
        📅 市场状态: 盘中交易
        📍 第一交易日: 今天（剩余 62% 交易时间，约 4.0 小时）
    """
    session_names = {
        "pre-market": "盘前",
        "market": "盘中交易",
        "after-hours": "盘后",
        "closed": "休市"
    }

    session_display = session_names.get(context["market_session"], context["market_session"])

    summary_parts = [
        f"📅 市场状态: {session_display}",
        f"📍 {context['explanation']}"
    ]

    return "\n".join(summary_parts)
