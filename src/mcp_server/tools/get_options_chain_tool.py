"""
期权链 MCP 工具实现

提供期权链数据获取、分析和导出的 MCP 工具接口。
按照 PRD v5 要求实现智能筛选（20个 ITM + ATM + 20个 OTM）和 CSV 导出功能。
"""

import os
import asyncio
from typing import Dict, Any, Optional

from ..config.settings import settings
from ...provider.tradier.client import TradierClient
from ...option.options_chain import (
    get_options_chain_data,
    export_options_to_csv,
    filter_and_limit_options,
)


async def options_chain_tool(
    symbol: str,
    expiration: str,
    option_type: str = "both",
    include_greeks: bool = True
) -> Dict[str, Any]:
    """
    获取期权链数据并返回分析结果的 MCP 工具。
    
    这是主要的 MCP 工具函数，为 Claude Code 提供期权链数据分析功能。
    返回 10个 ITM + ATM + 10个 OTM 期权（节省 Context 空间），并自动导出 CSV 文件。
    
    Args:
        symbol: 股票代码 (必需) - 例如 "AAPL", "TSLA", "NVDA"
        expiration: 到期日 YYYY-MM-DD (必需) - 例如 "2024-01-19"  
        option_type: "call", "put", 或 "both" (默认 "both")
        include_greeks: 是否包含希腊字母 (默认 True)
    
    Returns:
        期权链分析结果字典
        {
            "csv_file_path": "/path/to/saved/file.csv",
            "summary": {
                "symbol": "AAPL",
                "expiration": "2024-01-19",
                "underlying_price": 150.00,
                "total_options": 200,
                "calls_count": 100,
                "puts_count": 100
            },
            "itm_options": [...],      # 10个 ITM 期权
            "atm_options": [...],      # ATM 期权 (如有)
            "otm_options": [...],      # 10个 OTM 期权
            "greeks_summary": {
                "avg_delta": 0.5,
                "avg_gamma": 0.02,
                "avg_theta": -0.1,
                "avg_vega": 0.3
            }
        }
    """
    try:
        # 验证输入参数
        _validate_inputs(symbol, expiration, option_type)
        
        # 初始化 Tradier 客户端
        tradier_client = TradierClient()
        
        # 获取完整的期权链数据
        options_data = await get_options_chain_data(
            symbol=symbol,
            expiration=expiration,
            option_type=option_type,
            include_greeks=include_greeks,
            tradier_client=tradier_client
        )
        
        # 应用智能筛选：10个 ITM + ATM + 10个 OTM (节省 Context 空间)
        filtered_classification = filter_and_limit_options(
            options_data["classification"],
            itm_limit=10,
            otm_limit=10
        )
        
        # 导出 CSV 文件
        csv_file_path = export_options_to_csv(
            options_data=options_data,
            symbol=symbol,
            option_type=option_type,
            expiration=expiration,
            output_dir="./data"
        )
        
        # 构建用户友好的响应格式
        response = {
            "csv_file_path": csv_file_path,
            "summary": options_data["summary"],
            "itm_options": _format_options_for_display(filtered_classification["itm"]),
            "atm_options": _format_options_for_display(filtered_classification["atm"]),
            "otm_options": _format_options_for_display(filtered_classification["otm"]),
            "greeks_summary": options_data.get("greeks_summary", {}),
            "metadata": {
                **options_data.get("metadata", {}),
                "filtered_counts": filtered_classification["counts"],
                "csv_exported": True,
                "csv_records_count": len(options_data["options_data"]["all_options"])
            }
        }
        
        # 添加中文说明
        response["说明"] = {
            "工具功能": "获取期权链数据并进行 ITM/ATM/OTM 智能分类",
            "数据来源": "Tradier API 实时数据",
            "筛选规则": "返回最具流动性的 10个价内期权 + 所有平值期权 + 10个价外期权（节省Context）",
            "CSV文件": "已自动保存到 ./data 目录，包含完整期权数据和希腊字母",
            "使用建议": "可通过 CSV 文件进行进一步的量化分析和策略回测"
        }
        
        return response
        
    except Exception as e:
        error_response = {
            "error": True,
            "message": f"获取 {symbol} 期权链数据失败",
            "details": str(e),
            "symbol": symbol,
            "expiration": expiration,
            "option_type": option_type,
            "建议": [
                "请检查股票代码是否正确",
                "请确认到期日格式为 YYYY-MM-DD",
                "请确认该股票在指定日期有可用的期权",
                "请检查 Tradier API 访问令牌是否有效"
            ]
        }
        return error_response


def _validate_inputs(symbol: str, expiration: str, option_type: str) -> None:
    """
    验证输入参数的有效性。
    
    Args:
        symbol: 股票代码
        expiration: 到期日
        option_type: 期权类型
    
    Raises:
        ValueError: 输入参数无效时抛出
    """
    if not symbol or not isinstance(symbol, str):
        raise ValueError("股票代码 (symbol) 必须为非空字符串")
    
    if not expiration or not isinstance(expiration, str):
        raise ValueError("到期日 (expiration) 必须为非空字符串")
    
    # 验证到期日格式 YYYY-MM-DD
    try:
        from datetime import datetime
        datetime.strptime(expiration, "%Y-%m-%d")
    except ValueError:
        raise ValueError("到期日格式必须为 YYYY-MM-DD，例如 '2024-01-19'")
    
    # 验证期权类型
    valid_types = ["call", "put", "both"]
    if option_type.lower() not in valid_types:
        raise ValueError(f"期权类型必须为 {valid_types} 之一")


def _format_options_for_display(options: list, max_display: int = 50) -> list:
    """
    格式化期权数据以便于显示和分析。
    
    Args:
        options: 期权合约列表
        max_display: 最大显示数量
    
    Returns:
        格式化后的期权数据列表
    """
    if not options:
        return []
    
    formatted_options = []
    
    for i, option in enumerate(options[:max_display]):
        # 基本信息
        formatted_option = {
            "序号": i + 1,
            "合约代码": option.symbol,
            "描述": option.description,
            "执行价格": option.strike,
            "期权类型": "看涨" if option.option_type == "call" else "看跌",
            "买价": option.bid,
            "卖价": option.ask,
            "中间价": option.mid_price,
            "最新价": option.last,
            "开盘价": option.open,
            "最高价": option.high,
            "最低价": option.low,
            "收盘价": option.close,
            "前收盘价": option.prevclose,
            "涨跌额": option.change,
            "涨跌幅": f"{option.change_percentage:.2f}%" if option.change_percentage else None,
            "成交量": option.volume or 0,
            "平均成交量": option.average_volume,
            "最新成交量": option.last_volume,
            "未平仓量": option.open_interest or 0,
            "买盘量": option.bidsize,
            "卖盘量": option.asksize,
            "52周最高": option.week_52_high,
            "52周最低": option.week_52_low,
            "合约规模": option.contract_size or 100,
        }
        
        # 计算指标
        if hasattr(option, 'intrinsic_value') and option.intrinsic_value is not None:
            formatted_option["内在价值"] = option.intrinsic_value
        if hasattr(option, 'time_value') and option.time_value is not None:
            formatted_option["时间价值"] = option.time_value
        if hasattr(option, 'moneyness') and option.moneyness is not None:
            formatted_option["价值性比率"] = option.moneyness
        if hasattr(option, 'days_to_expiration') and option.days_to_expiration is not None:
            formatted_option["到期天数"] = option.days_to_expiration
        if hasattr(option, 'in_the_money') and option.in_the_money is not None:
            formatted_option["是否价内"] = "是" if option.in_the_money else "否"
        
        # 希腊字母
        if option.greeks:
            greeks_info = {}
            if option.greeks.get("delta") is not None:
                greeks_info["Delta"] = option.greeks["delta"]
            if option.greeks.get("gamma") is not None:
                greeks_info["Gamma"] = option.greeks["gamma"]
            if option.greeks.get("theta") is not None:
                greeks_info["Theta"] = option.greeks["theta"]
            if option.greeks.get("vega") is not None:
                greeks_info["Vega"] = option.greeks["vega"]
            if option.greeks.get("mid_iv") is not None:
                greeks_info["隐含波动率"] = option.greeks["mid_iv"]
            
            if greeks_info:
                formatted_option["希腊字母"] = greeks_info
        
        formatted_options.append(formatted_option)
    
    return formatted_options


def _calculate_option_summary_stats(options: list) -> Dict[str, Any]:
    """
    计算期权的统计摘要。
    
    Args:
        options: 期权合约列表
    
    Returns:
        统计摘要字典
    """
    if not options:
        return {"数量": 0}
    
    total_volume = sum((opt.volume or 0) for opt in options)
    total_oi = sum((opt.open_interest or 0) for opt in options)
    
    # 计算价格范围
    strikes = [opt.strike for opt in options if opt.strike is not None]
    min_strike = min(strikes) if strikes else None
    max_strike = max(strikes) if strikes else None
    
    # 计算平均隐含波动率
    ivs = []
    for opt in options:
        if opt.greeks and opt.greeks.get("mid_iv"):
            ivs.append(opt.greeks["mid_iv"])
    
    avg_iv = sum(ivs) / len(ivs) if ivs else None
    
    return {
        "数量": len(options),
        "总成交量": total_volume,
        "总未平仓量": total_oi,
        "执行价格范围": {
            "最低": min_strike,
            "最高": max_strike
        } if min_strike and max_strike else None,
        "平均隐含波动率": round(avg_iv, 4) if avg_iv else None
    }


def get_available_expirations_for_symbol(symbol: str) -> Dict[str, Any]:
    """
    获取指定股票的可用期权到期日（辅助函数）。
    这个函数可以帮助用户选择合适的到期日。
    
    Args:
        symbol: 股票代码
    
    Returns:
        可用到期日信息
    """
    try:
        from ...option.option_expiration_dates import get_option_expiration_dates
        
        tradier_client = TradierClient()
        expirations = get_option_expiration_dates(
            symbol=symbol,
            min_days=1,  # 至少1天后到期
            max_days=365,  # 最多1年内
            tradier_client=tradier_client
        )
        
        return {
            "symbol": symbol,
            "available_expirations": expirations[:10],  # 显示前10个
            "total_count": len(expirations),
            "suggestion": "建议选择流动性较好的近月合约进行分析"
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"获取 {symbol} 可用到期日失败: {str(e)}"
        }


def get_option_strikes_for_expiration(symbol: str, expiration: str) -> Dict[str, Any]:
    """
    获取指定到期日的可用执行价格（辅助函数）。
    
    Args:
        symbol: 股票代码
        expiration: 到期日
    
    Returns:
        可用执行价格信息
    """
    try:
        from ...option.option_strikes import get_option_strikes
        
        tradier_client = TradierClient()
        strikes_data = get_option_strikes(
            symbol=symbol,
            expiration=expiration,
            strike_range_pct=0.2,  # ±20% 范围
            tradier_client=tradier_client
        )
        
        return {
            "symbol": symbol,
            "expiration": expiration,
            **strikes_data
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"获取 {symbol} 在 {expiration} 的执行价格失败: {str(e)}"
        }