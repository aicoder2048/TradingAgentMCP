"""
期权执行价格查询模块

提供期权执行价格查询、筛选和分析功能。
这些是本地函数，不作为 MCP 工具暴露。
"""

import os
from typing import List, Dict, Any, Optional
import math

from ..provider.tradier.client import TradierClient


def get_option_strikes(
    symbol: str, 
    expiration: str,
    strike_range_pct: Optional[float] = None,
    tradier_client: Optional[TradierClient] = None
) -> Dict[str, Any]:
    """
    获取指定到期日的执行价格列表。
    
    Args:
        symbol: 股票代码
        expiration: 到期日 (YYYY-MM-DD)
        strike_range_pct: 执行价格范围百分比 (例如 0.1 = ±10%)
        tradier_client: Tradier 客户端实例
    
    Returns:
        执行价格分析结果
        {
            "symbol": "AAPL",
            "expiration": "2024-01-19", 
            "underlying_price": 150.00,
            "all_strikes": [...],
            "filtered_strikes": [...],
            "atm_strike": 150.0,
            "strike_spacing": 2.5,
            "total_strikes": 45
        }
    """
    if tradier_client is None:
        tradier_client = TradierClient()
    
    try:
        # 获取当前股价
        quotes = tradier_client.get_quotes([symbol])
        if not quotes:
            raise ValueError(f"无法获取 {symbol} 的股价")
        
        underlying_price = quotes[0].last
        if underlying_price is None:
            raise ValueError(f"{symbol} 股价数据不可用")
        
        # 获取执行价格列表
        strikes = tradier_client.get_option_strikes(symbol, expiration, include_all_roots=True)
        if not strikes:
            raise ValueError(f"未找到 {symbol} 在 {expiration} 的期权执行价格")
        
        # 排序执行价格
        strikes.sort()
        
        # 查找 ATM 执行价格
        atm_strike = find_atm_strike(strikes, underlying_price)
        
        # 计算执行价格间距
        strike_spacing = _calculate_strike_spacing(strikes)
        
        # 应用范围过滤（如果指定）
        filtered_strikes = strikes
        if strike_range_pct is not None:
            filtered_strikes = filter_strikes_by_range(strikes, underlying_price, strike_range_pct)
        
        # 分类执行价格
        strike_classification = _classify_strikes_by_distance(strikes, underlying_price, atm_strike)
        
        return {
            "symbol": symbol,
            "expiration": expiration,
            "underlying_price": round(underlying_price, 2),
            "all_strikes": strikes,
            "filtered_strikes": filtered_strikes,
            "atm_strike": atm_strike,
            "strike_spacing": strike_spacing,
            "total_strikes": len(strikes),
            "filtered_count": len(filtered_strikes),
            "classification": strike_classification,
            "price_range": {
                "min_strike": min(strikes),
                "max_strike": max(strikes),
                "range_pct_below": round((underlying_price - min(strikes)) / underlying_price * 100, 1),
                "range_pct_above": round((max(strikes) - underlying_price) / underlying_price * 100, 1)
            }
        }
        
    except Exception as e:
        raise Exception(f"获取 {symbol} 在 {expiration} 的执行价格失败: {str(e)}")


def find_atm_strike(strikes: List[float], underlying_price: float) -> float:
    """
    查找最接近股价的执行价格 (At-The-Money)。
    
    Args:
        strikes: 执行价格列表
        underlying_price: 当前股价
    
    Returns:
        最接近的执行价格
    """
    if not strikes:
        raise ValueError("执行价格列表不能为空")
    
    # 找到最接近股价的执行价格
    closest_strike = min(strikes, key=lambda x: abs(x - underlying_price))
    return closest_strike


def filter_strikes_by_range(
    strikes: List[float],
    center_price: float, 
    range_pct: float
) -> List[float]:
    """
    按价格范围过滤执行价格。
    
    Args:
        strikes: 执行价格列表
        center_price: 中心价格（通常是当前股价）
        range_pct: 范围百分比 (例如 0.1 = ±10%)
    
    Returns:
        过滤后的执行价格列表
    """
    if range_pct <= 0:
        return strikes.copy()
    
    min_price = center_price * (1 - range_pct)
    max_price = center_price * (1 + range_pct)
    
    filtered = [strike for strike in strikes if min_price <= strike <= max_price]
    return sorted(filtered)


def get_strike_chain_analysis(strikes: List[float], underlying_price: float) -> Dict[str, Any]:
    """
    分析执行价格链的特征。
    
    Args:
        strikes: 执行价格列表
        underlying_price: 当前股价
    
    Returns:
        执行价格链分析结果
    """
    if not strikes:
        return {"error": "执行价格列表为空"}
    
    strikes = sorted(strikes)
    atm_strike = find_atm_strike(strikes, underlying_price)
    
    # 基本统计
    total_strikes = len(strikes)
    min_strike = min(strikes)
    max_strike = max(strikes)
    
    # 计算间距分布
    spacings = []
    for i in range(1, len(strikes)):
        spacings.append(strikes[i] - strikes[i-1])
    
    avg_spacing = sum(spacings) / len(spacings) if spacings else 0
    
    # 分类计数
    itm_calls = len([s for s in strikes if s < underlying_price])
    otm_calls = len([s for s in strikes if s > underlying_price])
    itm_puts = otm_calls  # Put ITM = Call OTM
    otm_puts = itm_calls  # Put OTM = Call ITM
    
    return {
        "total_strikes": total_strikes,
        "price_range": {
            "min": min_strike,
            "max": max_strike,
            "width": max_strike - min_strike,
            "width_pct": round((max_strike - min_strike) / underlying_price * 100, 1)
        },
        "atm_info": {
            "atm_strike": atm_strike,
            "distance_from_price": abs(atm_strike - underlying_price),
            "distance_pct": round(abs(atm_strike - underlying_price) / underlying_price * 100, 2)
        },
        "spacing": {
            "average": round(avg_spacing, 2),
            "min": min(spacings) if spacings else 0,
            "max": max(spacings) if spacings else 0,
            "distribution": _analyze_spacing_distribution(spacings)
        },
        "moneyness_distribution": {
            "itm_calls": itm_calls,
            "otm_calls": otm_calls, 
            "itm_puts": itm_puts,
            "otm_puts": otm_puts
        }
    }


def get_strikes_around_price(
    strikes: List[float], 
    center_price: float, 
    count_each_side: int = 10
) -> Dict[str, List[float]]:
    """
    获取围绕指定价格的执行价格。
    
    Args:
        strikes: 执行价格列表
        center_price: 中心价格
        count_each_side: 每一侧的执行价格数量
    
    Returns:
        分类后的执行价格
        {
            "below": [...],  # 低于中心价格的执行价格
            "above": [...],  # 高于中心价格的执行价格
            "closest": float  # 最接近的执行价格
        }
    """
    if not strikes:
        return {"below": [], "above": [], "closest": None}
    
    strikes = sorted(strikes)
    closest = find_atm_strike(strikes, center_price)
    
    below_strikes = [s for s in strikes if s < center_price][-count_each_side:]
    above_strikes = [s for s in strikes if s > center_price][:count_each_side]
    
    return {
        "below": sorted(below_strikes),
        "above": sorted(above_strikes),
        "closest": closest,
        "total_selected": len(below_strikes) + len(above_strikes)
    }


def _calculate_strike_spacing(strikes: List[float]) -> float:
    """
    计算执行价格的平均间距。
    
    Args:
        strikes: 执行价格列表（应已排序）
    
    Returns:
        平均间距
    """
    if len(strikes) < 2:
        return 0
    
    spacings = []
    for i in range(1, len(strikes)):
        spacing = strikes[i] - strikes[i-1]
        spacings.append(spacing)
    
    return round(sum(spacings) / len(spacings), 2)


def _classify_strikes_by_distance(
    strikes: List[float], 
    underlying_price: float,
    atm_strike: float
) -> Dict[str, Any]:
    """
    按与股价的距离分类执行价格。
    
    Args:
        strikes: 执行价格列表
        underlying_price: 当前股价
        atm_strike: ATM 执行价格
    
    Returns:
        分类结果
    """
    # 按距离分类
    very_close = []  # ±2% 内
    close = []       # ±5% 内
    moderate = []    # ±10% 内
    far = []         # >10%
    
    for strike in strikes:
        distance_pct = abs(strike - underlying_price) / underlying_price
        
        if distance_pct <= 0.02:
            very_close.append(strike)
        elif distance_pct <= 0.05:
            close.append(strike)
        elif distance_pct <= 0.10:
            moderate.append(strike)
        else:
            far.append(strike)
    
    return {
        "very_close": sorted(very_close),  # ±2%
        "close": sorted(close),            # ±5%
        "moderate": sorted(moderate),      # ±10%
        "far": sorted(far),               # >10%
        "counts": {
            "very_close": len(very_close),
            "close": len(close),
            "moderate": len(moderate),
            "far": len(far)
        }
    }


def _analyze_spacing_distribution(spacings: List[float]) -> Dict[str, int]:
    """
    分析执行价格间距分布。
    
    Args:
        spacings: 间距列表
    
    Returns:
        间距分布统计
    """
    if not spacings:
        return {}
    
    # 常见的执行价格间距
    distribution = {
        "0.5": 0,    # $0.50
        "1.0": 0,    # $1.00
        "2.5": 0,    # $2.50
        "5.0": 0,    # $5.00
        "10.0": 0,   # $10.00
        "other": 0   # 其他间距
    }
    
    tolerance = 0.01  # 容忍度
    
    for spacing in spacings:
        found = False
        for key in ["0.5", "1.0", "2.5", "5.0", "10.0"]:
            if abs(spacing - float(key)) <= tolerance:
                distribution[key] += 1
                found = True
                break
        
        if not found:
            distribution["other"] += 1
    
    return distribution