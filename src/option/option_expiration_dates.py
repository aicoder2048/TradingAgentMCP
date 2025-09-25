"""
期权到期日管理模块

提供期权到期日查询、筛选和管理功能。
这些是本地函数，不作为 MCP 工具暴露。
"""

import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from zoneinfo import ZoneInfo

from ..provider.tradier.client import TradierClient, OptionExpiration


def get_option_expiration_dates(
    symbol: str,
    min_days: Optional[int] = None,
    max_days: Optional[int] = None,
    tradier_client: Optional[TradierClient] = None
) -> List[Dict[str, Any]]:
    """
    获取期权到期日列表，支持按天数过滤。
    
    Args:
        symbol: 股票代码
        min_days: 最小到期天数过滤
        max_days: 最大到期天数过滤  
        tradier_client: Tradier 客户端实例
    
    Returns:
        到期日信息列表，包含日期、天数、类型等信息
        [{
            "date": "2024-01-19",
            "days_to_expiration": 30,
            "expiration_type": "standard", 
            "contract_size": 100,
            "available_strikes": [...]
        }]
    """
    if tradier_client is None:
        tradier_client = TradierClient()
    
    try:
        # 获取详细的到期日信息
        expirations = tradier_client.get_option_expirations(
            symbol=symbol,
            include_all_roots=True,
            include_strikes=True,
            include_details=True
        )
        
        today = date.today()
        processed_expirations = []
        
        for exp in expirations:
            # 解析到期日
            try:
                exp_date = datetime.strptime(exp.date, "%Y-%m-%d").date()
            except ValueError:
                continue
                
            # 计算到期天数
            days_to_exp = (exp_date - today).days
            
            # 跳过已经过期的期权
            if days_to_exp < 0:
                continue
            
            # 应用天数过滤器
            if min_days is not None and days_to_exp < min_days:
                continue
            if max_days is not None and days_to_exp > max_days:
                continue
            
            expiration_info = {
                "date": exp.date,
                "days_to_expiration": days_to_exp,
                "expiration_type": exp.expiration_type,
                "contract_size": exp.contract_size,
                "available_strikes": exp.strikes,
                "strikes_count": len(exp.strikes)
            }
            
            processed_expirations.append(expiration_info)
        
        # 按到期日排序
        processed_expirations.sort(key=lambda x: x["date"])
        
        return processed_expirations
        
    except Exception as e:
        raise Exception(f"获取 {symbol} 期权到期日失败: {str(e)}")


def get_next_expiration_date(symbol: str, tradier_client: Optional[TradierClient] = None) -> Optional[str]:
    """
    获取下一个最近的到期日。
    
    Args:
        symbol: 股票代码
        tradier_client: Tradier 客户端实例
    
    Returns:
        下一个到期日的日期字符串 (YYYY-MM-DD)，如果没有找到则返回 None
    """
    try:
        expirations = get_option_expiration_dates(symbol, min_days=0, tradier_client=tradier_client)
        
        if not expirations:
            return None
        
        # 返回最近的到期日
        return expirations[0]["date"]
        
    except Exception:
        return None


def filter_expirations_by_days(
    expirations: List[Dict], 
    min_days: int = 0, 
    max_days: int = 365
) -> List[Dict]:
    """
    按到期天数过滤到期日列表。
    
    Args:
        expirations: 到期日信息列表
        min_days: 最小天数（包含）
        max_days: 最大天数（包含）
    
    Returns:
        过滤后的到期日列表
    """
    filtered = []
    
    for exp in expirations:
        days = exp.get("days_to_expiration", 0)
        
        if min_days <= days <= max_days:
            filtered.append(exp)
    
    return filtered


def get_weekly_expirations(symbol: str, weeks: int = 4, tradier_client: Optional[TradierClient] = None) -> List[Dict[str, Any]]:
    """
    获取未来几周的周期权到期日。
    
    Args:
        symbol: 股票代码
        weeks: 获取未来几周的到期日
        tradier_client: Tradier 客户端实例
    
    Returns:
        周期权到期日列表
    """
    max_days = weeks * 7 + 3  # 多加3天缓冲
    
    try:
        expirations = get_option_expiration_dates(
            symbol=symbol,
            min_days=0,
            max_days=max_days,
            tradier_client=tradier_client
        )
        
        # 筛选周期权（通常是周五到期）
        weekly_exps = []
        for exp in expirations:
            exp_date = datetime.strptime(exp["date"], "%Y-%m-%d").date()
            
            # 检查是否为周期权（通常在周五，weekday() 返回 4）
            if exp_date.weekday() == 4:  # 周五
                exp_type = exp.get("expiration_type", "").lower()
                if "weekly" in exp_type or exp["days_to_expiration"] <= max_days:
                    weekly_exps.append(exp)
        
        return weekly_exps[:weeks] if weekly_exps else expirations[:weeks]
        
    except Exception as e:
        raise Exception(f"获取 {symbol} 周期权到期日失败: {str(e)}")


def get_monthly_expirations(symbol: str, months: int = 6, tradier_client: Optional[TradierClient] = None) -> List[Dict[str, Any]]:
    """
    获取未来几个月的月期权到期日。
    
    Args:
        symbol: 股票代码 
        months: 获取未来几个月的到期日
        tradier_client: Tradier 客户端实例
    
    Returns:
        月期权到期日列表
    """
    max_days = months * 31  # 粗略计算最大天数
    
    try:
        expirations = get_option_expiration_dates(
            symbol=symbol,
            min_days=7,  # 至少一周后
            max_days=max_days,
            tradier_client=tradier_client
        )
        
        # 筛选月期权（通常是第三个周五）
        monthly_exps = []
        seen_months = set()
        
        for exp in expirations:
            exp_date = datetime.strptime(exp["date"], "%Y-%m-%d").date()
            month_key = f"{exp_date.year}-{exp_date.month:02d}"
            
            # 避免同一个月的重复
            if month_key in seen_months:
                continue
                
            exp_type = exp.get("expiration_type", "").lower()
            if ("standard" in exp_type or "monthly" in exp_type) and exp_date.weekday() == 4:
                # 检查是否为第三个周五
                first_day = exp_date.replace(day=1)
                third_friday = _get_third_friday(first_day)
                
                if exp_date == third_friday:
                    monthly_exps.append(exp)
                    seen_months.add(month_key)
        
        return monthly_exps[:months]
        
    except Exception as e:
        raise Exception(f"获取 {symbol} 月期权到期日失败: {str(e)}")


def _get_third_friday(first_day: date) -> date:
    """
    计算给定月份的第三个周五。
    
    Args:
        first_day: 月份的第一天
    
    Returns:
        该月第三个周五的日期
    """
    # 找到第一个周五
    days_to_friday = (4 - first_day.weekday()) % 7  # 4是周五
    first_friday = first_day + timedelta(days=days_to_friday)
    
    # 第三个周五是第一个周五后14天
    third_friday = first_friday + timedelta(days=14)
    
    return third_friday


def summarize_expirations(expirations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    总结到期日信息。
    
    Args:
        expirations: 到期日列表
    
    Returns:
        到期日统计摘要
    """
    if not expirations:
        return {
            "total_count": 0,
            "date_range": None,
            "types_distribution": {},
            "avg_days_to_expiration": 0,
            "total_strikes": 0
        }
    
    # 统计基本信息
    total_count = len(expirations)
    earliest_date = expirations[0]["date"]
    latest_date = expirations[-1]["date"]
    
    # 统计到期类型分布
    types_dist = {}
    total_strikes = 0
    total_days = 0
    
    for exp in expirations:
        exp_type = exp.get("expiration_type", "unknown")
        types_dist[exp_type] = types_dist.get(exp_type, 0) + 1
        
        total_strikes += exp.get("strikes_count", 0)
        total_days += exp.get("days_to_expiration", 0)
    
    avg_days = total_days / total_count if total_count > 0 else 0
    
    return {
        "total_count": total_count,
        "date_range": {
            "earliest": earliest_date,
            "latest": latest_date
        },
        "types_distribution": types_dist,
        "avg_days_to_expiration": round(avg_days, 1),
        "total_strikes": total_strikes,
        "avg_strikes_per_expiration": round(total_strikes / total_count, 1) if total_count > 0 else 0
    }