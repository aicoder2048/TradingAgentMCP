"""
期权链核心处理模块

提供期权链数据获取、分析、分类和导出功能。
包括 ITM/ATM/OTM 分类算法、希腊字母处理和 CSV 导出。
"""

import os
import csv
import json
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import asdict
import math

from ..provider.tradier.client import TradierClient, OptionContract
from ..utils.time import get_market_time_et


async def get_options_chain_data(
    symbol: str,
    expiration: str, 
    option_type: str = "both",
    include_greeks: bool = True,
    tradier_client: Optional[TradierClient] = None
) -> Dict[str, Any]:
    """
    获取并处理期权链数据的主函数。
    
    Args:
        symbol: 股票代码 (e.g., "AAPL", "TSLA")
        expiration: 到期日 (YYYY-MM-DD format)
        option_type: 期权类型 ("call", "put", "both")
        include_greeks: 是否包含希腊字母 (默认 True)
        tradier_client: Tradier 客户端实例
    
    Returns:
        包含期权数据、分类信息和统计的字典
        {
            "summary": {...},
            "options_data": {...},
            "classification": {...},
            "greeks_summary": {...}
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
        
        # 获取期权链数据
        option_contracts = tradier_client.get_option_chain_enhanced(
            symbol=symbol, 
            expiration=expiration, 
            include_greeks=include_greeks
        )
        
        if not option_contracts:
            raise ValueError(f"未找到 {symbol} 在 {expiration} 的期权数据")
        
        # 过滤期权类型
        if option_type.lower() == "call":
            option_contracts = [opt for opt in option_contracts if opt.option_type == "call"]
        elif option_type.lower() == "put":
            option_contracts = [opt for opt in option_contracts if opt.option_type == "put"]
        # option_type == "both" 时不进行过滤
        
        # 计算期权指标
        enhanced_contracts = []
        for contract in option_contracts:
            enhanced_contract = calculate_option_metrics(contract, underlying_price)
            enhanced_contracts.append(enhanced_contract)
        
        # 按价值性分类期权
        classification = classify_options_by_moneyness(enhanced_contracts, underlying_price)
        
        # 计算希腊字母摘要
        greeks_summary = _calculate_greeks_summary(enhanced_contracts) if include_greeks else {}
        
        # 生成统计摘要
        summary = _generate_summary(
            symbol=symbol,
            expiration=expiration, 
            underlying_price=underlying_price,
            option_type=option_type,
            total_options=len(enhanced_contracts),
            classification=classification
        )
        
        return {
            "summary": summary,
            "options_data": {
                "all_options": enhanced_contracts,
                "calls": [opt for opt in enhanced_contracts if opt.option_type == "call"],
                "puts": [opt for opt in enhanced_contracts if opt.option_type == "put"]
            },
            "classification": classification,
            "greeks_summary": greeks_summary,
            "metadata": {
                "data_timestamp": datetime.now().isoformat(),
                "market_time": get_market_time_et(),
                "data_source": "Tradier API"
            }
        }
        
    except Exception as e:
        raise Exception(f"获取 {symbol} 期权链数据失败: {str(e)}")


def classify_options_by_moneyness(
    options: List[OptionContract], 
    underlying_price: float,
    atm_threshold: float = 0.01  # ±1% 为 ATM
) -> Dict[str, List[OptionContract]]:
    """
    按价值性分类期权 (ITM/ATM/OTM)。
    
    Args:
        options: OptionContract 对象列表
        underlying_price: 当前股价
        atm_threshold: ATM 判定阈值（百分比）
    
    Returns:
        分类结果字典
        {
            "itm": [...],    # In-The-Money options  
            "atm": [...],    # At-The-Money options
            "otm": [...]     # Out-Of-The-Money options
        }
    """
    itm_options = []
    atm_options = []
    otm_options = []
    
    for option in options:
        if option.strike is None:
            continue
            
        moneyness_type = classify_option_moneyness(
            option.strike, underlying_price, option.option_type, atm_threshold
        )
        
        if moneyness_type == "ITM":
            itm_options.append(option)
        elif moneyness_type == "ATM":
            atm_options.append(option)
        else:  # OTM
            otm_options.append(option)
    
    # 按执行价格排序
    itm_options.sort(key=lambda x: x.strike)
    atm_options.sort(key=lambda x: x.strike)
    otm_options.sort(key=lambda x: x.strike)
    
    return {
        "itm": itm_options,
        "atm": atm_options, 
        "otm": otm_options,
        "counts": {
            "itm": len(itm_options),
            "atm": len(atm_options),
            "otm": len(otm_options)
        }
    }


def classify_option_moneyness(
    strike: float, 
    underlying_price: float, 
    option_type: str,
    atm_threshold: float = 0.01
) -> str:
    """
    判断单个期权的价值性分类。
    
    Args:
        strike: 执行价格
        underlying_price: 当前股价
        option_type: 期权类型 ("call" 或 "put")
        atm_threshold: ATM 判定阈值（百分比）
    
    Returns:
        "ITM", "ATM", 或 "OTM"
    """
    price_diff_pct = abs(strike - underlying_price) / underlying_price
    
    # 首先检查是否为 ATM
    if price_diff_pct <= atm_threshold:
        return "ATM"
    
    # 根据期权类型判定 ITM/OTM
    if option_type.lower() == "call":
        return "ITM" if strike < underlying_price else "OTM"
    else:  # put
        return "ITM" if strike > underlying_price else "OTM"


def calculate_option_metrics(contract: OptionContract, underlying_price: float) -> OptionContract:
    """
    计算期权的各项指标。
    
    Args:
        contract: 原始期权合约
        underlying_price: 当前股价
    
    Returns:
        增强后的期权合约（包含计算指标）
    """
    # 创建合约副本
    enhanced = OptionContract(
        symbol=contract.symbol,
        strike=contract.strike,
        expiration_date=contract.expiration_date,
        option_type=contract.option_type,
        bid=contract.bid,
        ask=contract.ask,
        last=contract.last,
        volume=contract.volume,
        open_interest=contract.open_interest,
        underlying=contract.underlying,
        change=contract.change,
        change_percentage=contract.change_percentage,
        greeks=contract.greeks
    )
    
    # 计算中间价格
    if enhanced.bid is not None and enhanced.ask is not None and enhanced.bid > 0 and enhanced.ask > 0:
        enhanced.mid_price = round((enhanced.bid + enhanced.ask) / 2, 3)
    
    # 计算内在价值
    if enhanced.strike is not None:
        if enhanced.option_type == "call":
            enhanced.intrinsic_value = max(0, underlying_price - enhanced.strike)
        else:  # put
            enhanced.intrinsic_value = max(0, enhanced.strike - underlying_price)
        enhanced.intrinsic_value = round(enhanced.intrinsic_value, 3)
    
    # 计算时间价值
    if enhanced.mid_price is not None and enhanced.intrinsic_value is not None:
        enhanced.time_value = max(0, enhanced.mid_price - enhanced.intrinsic_value)
        enhanced.time_value = round(enhanced.time_value, 3)
    
    # 计算价值性比率
    if enhanced.strike is not None:
        if enhanced.option_type == "call":
            enhanced.moneyness = round(underlying_price / enhanced.strike, 4)
        else:  # put
            enhanced.moneyness = round(enhanced.strike / underlying_price, 4)
    
    # 计算到期天数
    if enhanced.expiration_date:
        try:
            exp_date = datetime.strptime(enhanced.expiration_date, "%Y-%m-%d").date()
            today = date.today()
            enhanced.days_to_expiration = (exp_date - today).days
        except ValueError:
            enhanced.days_to_expiration = None
    
    # 判断是否为价内期权
    if enhanced.strike is not None:
        if enhanced.option_type == "call":
            enhanced.in_the_money = underlying_price > enhanced.strike
        else:  # put
            enhanced.in_the_money = underlying_price < enhanced.strike
    
    return enhanced


def export_options_to_csv(
    options_data: Dict[str, Any],
    symbol: str,
    option_type: str, 
    expiration: str,
    output_dir: str = "./data"
) -> str:
    """
    导出期权数据到 CSV 文件。
    
    Args:
        options_data: 期权数据字典
        symbol: 股票代码
        option_type: 期权类型
        expiration: 到期日
        output_dir: 输出目录
    
    Returns:
        CSV 文件的完整路径
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成文件名：<symbol>_<option_type>_<expiration>_<timestamp>.csv
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{symbol}_{option_type}_{expiration}_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)
    
    try:
        # 获取所有期权数据
        all_options = options_data.get("options_data", {}).get("all_options", [])
        
        if not all_options:
            raise ValueError("没有期权数据可导出")
        
        # CSV 字段定义
        fieldnames = [
            "symbol", "description", "strike_price", "expiration_date", "option_type", "underlying",
            "bid", "ask", "mid_price", "last", "open", "high", "low", "close", "prevclose",
            "volume", "average_volume", "last_volume", "open_interest",
            "change", "change_percentage", "bidsize", "asksize",
            "week_52_high", "week_52_low", "contract_size", "root_symbol",
            "trade_date", "bid_date", "ask_date",
            "intrinsic_value", "time_value", "moneyness", 
            "days_to_expiration", "in_the_money"
        ]
        
        # 添加希腊字母字段（如果存在）
        sample_option = all_options[0]
        if sample_option.greeks:
            greek_fields = ["delta", "gamma", "theta", "vega", "rho", 
                          "implied_volatility", "bid_iv", "mid_iv", "ask_iv"]
            fieldnames.extend(greek_fields)
        
        # 写入 CSV 文件
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for option in all_options:
                row = {
                    "symbol": option.symbol,
                    "description": option.description,
                    "strike_price": option.strike,
                    "expiration_date": option.expiration_date,
                    "option_type": option.option_type,
                    "underlying": option.underlying,
                    "bid": option.bid,
                    "ask": option.ask,
                    "mid_price": option.mid_price,
                    "last": option.last,
                    "open": option.open,
                    "high": option.high,
                    "low": option.low,
                    "close": option.close,
                    "prevclose": option.prevclose,
                    "volume": option.volume,
                    "average_volume": option.average_volume,
                    "last_volume": option.last_volume,
                    "open_interest": option.open_interest,
                    "change": option.change,
                    "change_percentage": option.change_percentage,
                    "bidsize": option.bidsize,
                    "asksize": option.asksize,
                    "week_52_high": option.week_52_high,
                    "week_52_low": option.week_52_low,
                    "contract_size": option.contract_size,
                    "root_symbol": option.root_symbol,
                    "trade_date": option.trade_date,
                    "bid_date": option.bid_date,
                    "ask_date": option.ask_date,
                    "intrinsic_value": option.intrinsic_value,
                    "time_value": option.time_value,
                    "moneyness": option.moneyness,
                    "days_to_expiration": option.days_to_expiration,
                    "in_the_money": option.in_the_money
                }
                
                # 添加希腊字母数据
                if option.greeks:
                    row.update({
                        "delta": option.greeks.get("delta"),
                        "gamma": option.greeks.get("gamma"),
                        "theta": option.greeks.get("theta"),
                        "vega": option.greeks.get("vega"),
                        "rho": option.greeks.get("rho"),
                        "implied_volatility": option.greeks.get("mid_iv"),
                        "bid_iv": option.greeks.get("bid_iv"),
                        "mid_iv": option.greeks.get("mid_iv"),
                        "ask_iv": option.greeks.get("ask_iv")
                    })
                
                writer.writerow(row)
        
        return os.path.abspath(filepath)
        
    except Exception as e:
        raise Exception(f"导出 CSV 文件失败: {str(e)}")


def filter_and_limit_options(
    classification: Dict[str, List[OptionContract]],
    itm_limit: int = 10,
    otm_limit: int = 10
) -> Dict[str, List[OptionContract]]:
    """
    筛选和限制期权数量，默认返回 10个 ITM + ATM + 10个 OTM（节省Context）。
    
    Args:
        classification: 分类后的期权数据
        itm_limit: ITM 期权限制数量（默认10）
        otm_limit: OTM 期权限制数量（默认10）
    
    Returns:
        筛选后的期权分类
    """
    itm_options = classification.get("itm", [])
    atm_options = classification.get("atm", [])
    otm_options = classification.get("otm", [])
    
    # ITM 期权：选择最接近 ATM 的期权，优先考虑流动性
    # 对于 Call: 选择执行价格最高的（最接近股价）
    # 对于 Put: 选择执行价格最低的（最接近股价）
    itm_calls = [opt for opt in itm_options if opt.option_type == "call"]
    itm_puts = [opt for opt in itm_options if opt.option_type == "put"]
    
    # 按流动性和接近度排序，然后分配限制数量
    itm_calls.sort(key=lambda x: (x.strike, _calculate_liquidity_score(x)), reverse=True)
    itm_puts.sort(key=lambda x: (-x.strike, _calculate_liquidity_score(x)), reverse=True)
    
    # 智能分配：如果某类型期权较少，另一类型可以多选一些
    total_itm_available = len(itm_calls) + len(itm_puts)
    if total_itm_available <= itm_limit:
        selected_itm_calls = itm_calls
        selected_itm_puts = itm_puts
    else:
        # 平均分配，但允许一方多选
        calls_limit = min(len(itm_calls), itm_limit // 2)
        puts_limit = min(len(itm_puts), itm_limit - calls_limit)
        # 如果puts不够，calls可以多选
        if puts_limit < itm_limit // 2:
            calls_limit = min(len(itm_calls), itm_limit - puts_limit)
        
        selected_itm_calls = itm_calls[:calls_limit]
        selected_itm_puts = itm_puts[:puts_limit]
    
    # OTM 期权：按流动性（成交量和未平仓合约）排序
    otm_calls = [opt for opt in otm_options if opt.option_type == "call"]
    otm_puts = [opt for opt in otm_options if opt.option_type == "put"]
    
    # 按流动性评分排序
    otm_calls.sort(key=lambda x: _calculate_liquidity_score(x), reverse=True)
    otm_puts.sort(key=lambda x: _calculate_liquidity_score(x), reverse=True)
    
    # 智能分配 OTM 期权
    total_otm_available = len(otm_calls) + len(otm_puts)
    if total_otm_available <= otm_limit:
        selected_otm_calls = otm_calls
        selected_otm_puts = otm_puts
    else:
        # 平均分配，但允许一方多选
        calls_limit = min(len(otm_calls), otm_limit // 2)
        puts_limit = min(len(otm_puts), otm_limit - calls_limit)
        # 如果puts不够，calls可以多选
        if puts_limit < otm_limit // 2:
            calls_limit = min(len(otm_calls), otm_limit - puts_limit)
        
        selected_otm_calls = otm_calls[:calls_limit]
        selected_otm_puts = otm_puts[:puts_limit]
    
    return {
        "itm": selected_itm_calls + selected_itm_puts,
        "atm": atm_options,  # 返回所有 ATM 期权
        "otm": selected_otm_calls + selected_otm_puts,
        "counts": {
            "itm": len(selected_itm_calls + selected_itm_puts),
            "atm": len(atm_options),
            "otm": len(selected_otm_calls + selected_otm_puts)
        }
    }


def _calculate_liquidity_score(option: OptionContract) -> float:
    """
    计算期权的流动性评分。
    
    Args:
        option: 期权合约
    
    Returns:
        流动性评分（越高越好）
    """
    volume = option.volume or 0
    open_interest = option.open_interest or 0
    
    # 流动性评分 = 成交量权重 * 成交量 + 未平仓合约权重 * 未平仓合约
    volume_weight = 0.6
    oi_weight = 0.4
    
    return volume_weight * volume + oi_weight * open_interest


def _calculate_greeks_summary(options: List[OptionContract]) -> Dict[str, Any]:
    """
    计算希腊字母统计摘要。
    
    Args:
        options: 期权合约列表
    
    Returns:
        希腊字母统计摘要
    """
    options_with_greeks = [opt for opt in options if opt.greeks]
    
    if not options_with_greeks:
        return {"message": "无希腊字母数据"}
    
    # 收集所有希腊字母数据
    deltas = []
    gammas = []
    thetas = []
    vegas = []
    rhos = []
    ivs = []
    
    for option in options_with_greeks:
        greeks = option.greeks
        if greeks.get("delta") is not None:
            deltas.append(greeks["delta"])
        if greeks.get("gamma") is not None:
            gammas.append(greeks["gamma"])
        if greeks.get("theta") is not None:
            thetas.append(greeks["theta"])
        if greeks.get("vega") is not None:
            vegas.append(greeks["vega"])
        if greeks.get("rho") is not None:
            rhos.append(greeks["rho"])
        if greeks.get("mid_iv") is not None:
            ivs.append(greeks["mid_iv"])
    
    def safe_avg(values):
        return round(sum(values) / len(values), 4) if values else 0
    
    return {
        "sample_size": len(options_with_greeks),
        "averages": {
            "delta": safe_avg(deltas),
            "gamma": safe_avg(gammas), 
            "theta": safe_avg(thetas),
            "vega": safe_avg(vegas),
            "rho": safe_avg(rhos),
            "implied_volatility": safe_avg(ivs)
        },
        "ranges": {
            "delta": {"min": min(deltas), "max": max(deltas)} if deltas else {},
            "gamma": {"min": min(gammas), "max": max(gammas)} if gammas else {},
            "theta": {"min": min(thetas), "max": max(thetas)} if thetas else {},
            "vega": {"min": min(vegas), "max": max(vegas)} if vegas else {},
            "implied_volatility": {"min": min(ivs), "max": max(ivs)} if ivs else {}
        }
    }


def _generate_summary(
    symbol: str,
    expiration: str,
    underlying_price: float,
    option_type: str,
    total_options: int,
    classification: Dict[str, Any]
) -> Dict[str, Any]:
    """
    生成期权链摘要信息。
    
    Args:
        symbol: 股票代码
        expiration: 到期日
        underlying_price: 当前股价
        option_type: 期权类型
        total_options: 期权总数
        classification: 分类统计
    
    Returns:
        摘要信息字典
    """
    counts = classification.get("counts", {})
    calls_count = len([opt for opt in classification.get("itm", []) + 
                      classification.get("atm", []) + 
                      classification.get("otm", []) 
                      if opt.option_type == "call"])
    puts_count = total_options - calls_count
    
    return {
        "symbol": symbol,
        "expiration": expiration,
        "underlying_price": round(underlying_price, 2),
        "option_type_requested": option_type,
        "total_options": total_options,
        "calls_count": calls_count,
        "puts_count": puts_count,
        "moneyness_distribution": counts,
        "data_completeness": {
            "has_pricing": total_options > 0,
            "has_volume": True,  # 假设都有成交量数据
            "has_greeks": True   # 假设都有希腊字母数据
        }
    }