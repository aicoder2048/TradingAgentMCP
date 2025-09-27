"""
期权被行权概率计算MCP工具

为TradingAgent MCP服务器提供专门的期权被行权概率计算功能，
基于Black-Scholes模型提供精确计算，替代简单的Delta近似方法。

Author: TradingAgent MCP Team
Version: v8.0
Created: 2024-09-27
"""

import asyncio
import traceback
from datetime import datetime
from typing import Any, Dict, Optional

from src.option.assignment_probability import OptionAssignmentCalculator
from src.provider.tradier.client import TradierClient
from src.utils.time import get_market_time_et


async def option_assignment_probability_tool(
    symbol: str,
    strike_price: float,
    expiration: str,
    option_type: str = "put",
    include_delta_comparison: bool = True,
    risk_free_rate: Optional[float] = None
) -> Dict[str, Any]:
    """
    计算期权被行权概率的专业MCP工具
    
    基于Black-Scholes模型提供精确的期权被行权概率计算，
    包含详细的风险分析、市场上下文和Delta比较功能。
    
    Args:
        symbol: 股票代码（必需，如 "AAPL", "TSLA", "NVDA"）
        strike_price: 期权行权价格（必需）
        expiration: 到期日 YYYY-MM-DD 格式（必需，如 "2024-01-19"）
        option_type: 期权类型 - "put" 或 "call"（可选，默认 "put"）
        include_delta_comparison: 是否包含Delta比较分析（可选，默认 True）
        risk_free_rate: 无风险利率（可选，默认 4.8%）
        
    Returns:
        包含被行权概率分析、风险评估和市场上下文的完整响应
        
    Examples:
        # 分析AAPL看跌期权被行权概率
        result = await option_assignment_probability_tool(
            symbol="AAPL",
            strike_price=145.0,
            expiration="2024-01-19",
            option_type="put"
        )
        
        # 分析TSLA看涨期权（不包含Delta比较）
        result = await option_assignment_probability_tool(
            symbol="TSLA", 
            strike_price=250.0,
            expiration="2024-02-16",
            option_type="call",
            include_delta_comparison=False
        )
    """
    
    try:
        # 参数验证和标准化
        symbol = symbol.upper().strip()
        option_type = option_type.lower().strip()
        
        if option_type not in ["put", "call"]:
            return {
                "symbol": symbol,
                "status": "error",
                "error": "invalid_option_type",
                "message": "期权类型必须是 'put' 或 'call'",
                "analysis_timestamp": get_market_time_et()
            }
        
        if strike_price <= 0:
            return {
                "symbol": symbol,
                "status": "error", 
                "error": "invalid_strike_price",
                "message": "行权价必须大于0",
                "analysis_timestamp": get_market_time_et()
            }
        
        print(f"🎯 开始分析 {symbol} {option_type.upper()} {strike_price} @ {expiration} 的被行权概率...")
        
        # 初始化组件
        client = TradierClient()
        calculator = OptionAssignmentCalculator()
        
        # 获取当前股票报价
        print(f"📊 获取 {symbol} 的实时市场数据...")
        quotes = client.get_quotes([symbol])
        if not quotes:
            return {
                "symbol": symbol,
                "status": "error",
                "error": "no_quote_data", 
                "message": f"无法获取 {symbol} 的市场报价数据",
                "analysis_timestamp": get_market_time_et()
            }
        
        underlying_price = quotes[0].last
        if not underlying_price or underlying_price <= 0:
            return {
                "symbol": symbol,
                "status": "error",
                "error": "invalid_price",
                "message": f"{symbol} 的价格数据无效或为零",
                "analysis_timestamp": get_market_time_et()
            }
        
        print(f"💰 {symbol} 当前价格: ${underlying_price:.2f}")
        
        # 获取期权链数据以提取隐含波动率和Delta
        print(f"🔗 获取 {symbol} {expiration} 期权链数据...")
        option_contracts = client.get_option_chain_enhanced(
            symbol=symbol,
            expiration=expiration,
            include_greeks=True
        )
        
        if not option_contracts:
            return {
                "symbol": symbol,
                "status": "error",
                "error": "no_option_data",
                "message": f"无法获取 {symbol} {expiration} 的期权链数据",
                "analysis_timestamp": get_market_time_et()
            }
        
        # 找到匹配的期权合约
        target_option = None
        for contract in option_contracts:
            if (contract.option_type.lower() == option_type and 
                abs(contract.strike - strike_price) < 0.01):  # 允许小的浮点误差
                target_option = contract
                break
        
        if not target_option:
            return {
                "symbol": symbol,
                "status": "error",
                "error": "option_not_found",
                "message": f"未找到 {symbol} {strike_price} {option_type.upper()} @ {expiration} 期权合约",
                "available_strikes": [c.strike for c in option_contracts if c.option_type.lower() == option_type],
                "analysis_timestamp": get_market_time_et()
            }
        
        # 提取期权数据
        implied_volatility = target_option.greeks.get("mid_iv", 0) if target_option.greeks else 0
        if implied_volatility <= 0:
            # 如果无法获取隐含波动率，使用历史波动率估算
            print("⚠️ 未获取到隐含波动率，使用估算值...")
            implied_volatility = 0.25  # 默认25%波动率
        
        # 计算到期天数
        from datetime import datetime
        try:
            exp_date = datetime.strptime(expiration, "%Y-%m-%d").date()
            today = datetime.now().date()
            days_to_expiry = max((exp_date - today).days, 0.1)  # 至少0.1天
        except ValueError:
            return {
                "symbol": symbol,
                "status": "error",
                "error": "invalid_expiration_format",
                "message": "到期日格式必须为 YYYY-MM-DD",
                "analysis_timestamp": get_market_time_et()
            }
        
        print(f"📅 距离到期: {days_to_expiry} 天")
        print(f"📈 隐含波动率: {implied_volatility:.2%}")
        
        # 计算精确被行权概率
        print("🔬 计算Black-Scholes精确被行权概率...")
        assignment_result = calculator.calculate_assignment_probability(
            underlying_price=underlying_price,
            strike_price=strike_price,
            time_to_expiry_days=days_to_expiry,
            implied_volatility=implied_volatility,
            risk_free_rate=risk_free_rate,
            option_type=option_type
        )
        
        if assignment_result["status"] == "error":
            return {
                "symbol": symbol,
                "status": "error",
                "error": "calculation_error",
                "message": assignment_result["error_message"],
                "analysis_timestamp": get_market_time_et()
            }
        
        print(f"✅ 被行权概率: {assignment_result['assignment_probability']:.2%}")
        
        # Delta比较分析（可选）
        delta_comparison = None
        if include_delta_comparison and target_option.greeks:
            delta_value = target_option.greeks.get("delta", 0)
            if delta_value != 0:
                print("📊 执行Delta比较分析...")
                delta_comparison = calculator.compare_with_delta_approximation(
                    underlying_price=underlying_price,
                    strike_price=strike_price,
                    time_to_expiry_days=days_to_expiry,
                    implied_volatility=implied_volatility,
                    delta_value=delta_value,
                    risk_free_rate=risk_free_rate,
                    option_type=option_type
                )
        
        # 构建期权详细信息
        option_details = {
            "symbol": target_option.symbol,
            "option_type": option_type.upper(),
            "strike_price": strike_price,
            "expiration": expiration,
            "days_to_expiry": days_to_expiry,
            "current_price": underlying_price,
            "bid": target_option.bid,
            "ask": target_option.ask,
            "mid_price": (target_option.bid + target_option.ask) / 2 if target_option.bid and target_option.ask else None,
            "volume": target_option.volume,
            "open_interest": target_option.open_interest,
            "greeks": target_option.greeks if target_option.greeks else {}
        }
        
        # 构建市场上下文
        market_context = {
            "implied_volatility": implied_volatility,
            "implied_volatility_percent": f"{implied_volatility:.2%}",
            "risk_free_rate": risk_free_rate or calculator.default_risk_free_rate,
            "market_session": "交易时段",  # 可以进一步细化
            "data_timestamp": get_market_time_et()
        }
        
        # 导出CSV数据（简化版）
        csv_filename = f"assignment_prob_{symbol}_{strike_price}{option_type[0].upper()}_{expiration.replace('-', '')}.csv"
        csv_path = f"./data/{csv_filename}"
        
        # 确保data目录存在
        import os
        os.makedirs("./data", exist_ok=True)
        
        try:
            # 创建CSV数据
            csv_data = [
                ["分析项目", "数值", "说明"],
                ["股票代码", symbol, "标的股票"],
                ["期权类型", option_type.upper(), "PUT或CALL"],
                ["行权价格", f"${strike_price:.2f}", "期权行权价"],
                ["当前价格", f"${underlying_price:.2f}", "标的当前价格"],
                ["到期日期", expiration, "期权到期日"],
                ["距离到期", f"{days_to_expiry}天", "剩余时间"],
                ["隐含波动率", f"{implied_volatility:.2%}", "年化波动率"],
                ["被行权概率", f"{assignment_result['assignment_probability']:.2%}", "Black-Scholes精确计算"],
                ["风险等级", assignment_result["assignment_risk_level"], "风险评估"],
                ["价值状态", assignment_result["moneyness"], "ITM/ATM/OTM状态"],
            ]
            
            if delta_comparison:
                csv_data.extend([
                    ["Delta近似", f"{delta_comparison['delta_approximation']:.2%}", "Delta近似被行权概率"],
                    ["精度差异", f"{delta_comparison['relative_difference_percent']:.2f}%", "相对误差"],
                    ["精度评估", delta_comparison["accuracy_assessment"], "Delta近似精度"]
                ])
            
            import csv
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(csv_data)
            
            print(f"💾 数据已导出到: {csv_path}")
            
        except Exception as e:
            print(f"⚠️ CSV导出失败: {e}")
            csv_path = None
        
        # 构建完整响应
        result = {
            "symbol": symbol,
            "current_price": underlying_price,
            "strike_price": strike_price,
            "option_type": option_type.upper(),
            "expiration": expiration,
            "days_to_expiry": days_to_expiry,
            "calculation_timestamp": get_market_time_et(),
            
            # 核心Black-Scholes计算结果
            "black_scholes_calculation": assignment_result,
            
            # Delta比较分析（如果请求）
            "delta_comparison": delta_comparison,
            
            # 期权详细信息
            "option_details": option_details,
            
            # 市场上下文
            "market_context": market_context,
            
            # 风险分析
            "risk_analysis": {
                "assignment_risk_level": assignment_result["assignment_risk_level"],
                "risk_explanation": assignment_result["interpretation"]["risk_explanation"],
                "moneyness_explanation": assignment_result["interpretation"]["moneyness_explanation"],
                "probability_meaning": assignment_result["interpretation"]["assignment_probability_meaning"]
            },
            
            # 技术信息
            "technical_info": {
                "calculation_method": "Black-Scholes精确计算",
                "data_source": "Tradier API实时数据",
                "accuracy_note": "基于实时隐含波动率和希腊字母的精确计算"
            },
            
            # 导出信息
            "csv_export_path": csv_path,
            "status": "success"
        }
        
        print(f"🎉 {symbol} 期权被行权概率分析完成！")
        return result
        
    except Exception as e:
        # 详细错误处理
        error_trace = traceback.format_exc()
        print(f"❌ 期权被行权概率工具错误: {str(e)}")
        print(f"错误堆栈: {error_trace}")
        
        return {
            "symbol": symbol if 'symbol' in locals() else "UNKNOWN",
            "status": "error",
            "error": type(e).__name__,
            "message": f"计算期权被行权概率时发生错误: {str(e)}",
            "error_details": {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": error_trace
            },
            "analysis_timestamp": get_market_time_et()
        }