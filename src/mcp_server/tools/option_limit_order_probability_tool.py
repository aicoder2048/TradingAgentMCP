"""
期权限价单成交概率预测MCP工具

预测期权限价单的成交概率、预期成交时间和置信度评估。
使用蒙特卡洛模拟、波动率分析和Greeks敏感度进行概率建模。
"""

import asyncio
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

from ..config.settings import settings
from ...provider.tradier.client import TradierClient
from ...option.limit_order_probability import (
    MonteCarloEngine,
    VolatilityMixer,
    FillDetector,
    StatisticalAnalyzer,
    TheoreticalValidator,
    BacktestValidator,
    RecommendationEngine,
    SimulationParameters
)
from ...option.options_chain import get_options_chain_data
from ...option.market_time_context import calculate_first_day_context, format_market_context_summary
from ...utils.time import get_market_time_et, get_timezone_time
from ...market.config import MARKET_CONFIG


async def option_limit_order_probability_tool(
    symbol: str,
    strike_price: float,
    expiration: str,
    option_type: str,
    current_price: float,
    limit_price: float,
    order_side: str,
    analysis_window: Optional[int] = None
) -> Dict[str, Any]:
    """
    期权限价单成交概率预测工具

    基于蒙特卡洛模拟预测限价单成交概率，帮助交易者评估限价策略的可行性。

    Args:
        symbol: 股票代码 (例如: "AAPL", "TSLA", "NVDA")
        strike_price: 执行价格
        expiration: 到期日期 YYYY-MM-DD 格式
        option_type: 期权类型 "put" 或 "call"
        current_price: 当前期权市场价格
        limit_price: 目标限价
        order_side: 订单方向 "buy" 或 "sell"
        analysis_window: 分析窗口天数 (可选，默认到期前全部天数)

    Returns:
        包含成交概率、预期时间、置信度和建议的综合分析结果

    Examples:
        # 预测卖出限价单成交概率
        >>> result = await option_limit_order_probability_tool(
        ...     symbol="AAPL",
        ...     strike_price=145.0,
        ...     expiration="2025-11-07",
        ...     option_type="put",
        ...     current_price=2.50,
        ...     limit_price=2.80,
        ...     order_side="sell"
        ... )
        >>> print(f"Fill Probability: {result['fill_probability']*100:.1f}%")
        Fill Probability: 68.0%
    """

    try:
        # Step 1: 参数验证
        if option_type.lower() not in ["put", "call"]:
            return {
                "error": "Invalid option_type. Must be 'put' or 'call'",
                "status": "error"
            }

        if order_side.lower() not in ["buy", "sell"]:
            return {
                "error": "Invalid order_side. Must be 'buy' or 'sell'",
                "status": "error"
            }

        # 验证限价与当前价格的逻辑
        if order_side == "sell" and limit_price <= current_price:
            return {
                "error": "For sell orders, limit price must be above current price",
                "status": "error"
            }

        if order_side == "buy" and limit_price >= current_price:
            return {
                "error": "For buy orders, limit price must be below current price",
                "status": "error"
            }

        # Step 2: 初始化Tradier客户端
        tradier_client = TradierClient()

        # Step 3: 获取当前市场数据和Greeks
        print(f"🔍 获取期权链数据: {symbol} {strike_price} {expiration}")

        options_result = await get_options_chain_data(
            symbol=symbol,
            expiration=expiration,
            option_type=option_type,
            tradier_client=tradier_client,
            include_greeks=True
        )

        # get_options_chain_data 返回的结构:
        # {
        #   "summary": {...},
        #   "options_data": {"all_options": [OptionContract, ...], "calls": [...], "puts": [...]},
        #   "classification": {...},
        #   "greeks_summary": {...}
        # }

        # 获取标的物价格
        underlying_price = options_result["summary"]["underlying_price"]

        # 根据期权类型选择正确的列表
        if option_type.lower() == "put":
            options_list = options_result["options_data"]["puts"]
        elif option_type.lower() == "call":
            options_list = options_result["options_data"]["calls"]
        else:
            options_list = options_result["options_data"]["all_options"]

        # 找到特定期权 (OptionContract对象)
        option_found = None
        for opt in options_list:
            if abs(opt.strike - strike_price) < 0.01:
                option_found = opt
                break

        if not option_found:
            return {
                "error": f"Option not found for strike {strike_price}",
                "status": "error"
            }

        # 提取Greeks和市场数据 (从OptionContract对象)
        greeks = option_found.greeks if option_found.greeks else {}
        delta = greeks.get("delta", -0.5 if option_type == "put" else 0.5)
        theta = greeks.get("theta", -0.05)
        gamma = greeks.get("gamma", 0.01)
        vega = greeks.get("vega", 0.1)
        implied_vol = greeks.get("mid_iv", 0.3)

        # 计算到期天数
        exp_date = datetime.strptime(expiration, "%Y-%m-%d")
        today = datetime.now()
        days_to_expiry = (exp_date - today).days

        if analysis_window:
            days_to_expiry = min(days_to_expiry, analysis_window)

        if days_to_expiry <= 0:
            return {
                "error": "Option has already expired or expires today",
                "status": "error"
            }

        # Step 3.5: 获取市场时间上下文
        eastern_time = get_timezone_time(MARKET_CONFIG["timezone"])
        market_ctx = calculate_first_day_context(eastern_time)
        market_ctx["eastern_time"] = eastern_time  # 添加到上下文中，供日历日期映射使用

        print(f"📅 市场时间上下文:")
        print(format_market_context_summary(market_ctx))

        # Step 4: 计算有效波动率
        print("📊 计算有效波动率...")
        vol_mixer = VolatilityMixer(tradier_client)
        vol_result = await vol_mixer.calculate_effective_volatility(
            symbol=symbol,
            implied_volatility=implied_vol,
            lookback_days=90,
            dynamic_weights=True
        )

        effective_vol = vol_result["effective_volatility"]

        # Step 5: 运行蒙特卡洛模拟
        print(f"🎲 运行蒙特卡洛模拟 (10,000 paths)...")

        sim_params = SimulationParameters(
            current_price=current_price,
            underlying_price=underlying_price,
            strike=strike_price,
            days_to_expiry=days_to_expiry,
            delta=delta,
            theta=theta,
            gamma=gamma,
            vega=vega,
            implied_volatility=implied_vol,
            historical_volatility=vol_result["historical_volatility"],
            effective_volatility=effective_vol,
            simulations=10000,
            first_day_fraction=market_ctx["first_day_fraction"]
        )

        monte_carlo = MonteCarloEngine(sim_params)
        price_paths = await monte_carlo.simulate_price_paths()

        # Step 6: 检测成交
        detector = FillDetector()
        fill_results = detector.detect_fills(
            price_paths=price_paths,
            limit_price=limit_price,
            order_side=order_side,
            include_touch_probability=True,
            first_day_fraction=market_ctx["first_day_fraction"],
            current_price=current_price,
            expiration_date=expiration,
            market_context=market_ctx
        )

        # Step 7: 计算置信度指标
        analyzer = StatisticalAnalyzer()

        # Step 8: 运行理论验证
        print("✅ 运行理论验证...")
        validator = TheoreticalValidator()
        validation_results = await validator.validate_model()

        # Step 9: 运行回测验证 (如果时间允许)
        backtest_results = None
        if days_to_expiry <= 60:  # 仅对短期期权进行回测
            print("📈 运行历史回测验证...")
            backtester = BacktestValidator(tradier_client)
            try:
                backtest_results = await asyncio.wait_for(
                    backtester.run_backtest(
                        symbol=symbol,
                        strike=strike_price,
                        option_type=option_type,
                        days_to_expiry=days_to_expiry,
                        lookback_days=90,
                        limit_premium_percentage=(limit_price - current_price) / current_price
                    ),
                    timeout=3.0  # 3秒超时
                )

                # 如果回测成功，计算MAE
                if backtest_results.get("backtest_available"):
                    actual_rate = backtest_results["actual_fill_rate"]
                    predicted_rate = fill_results["fill_probability"]
                    mae = abs(actual_rate - predicted_rate)
                    backtest_results["mae"] = mae
                    backtest_results["predicted_fill_rate"] = predicted_rate

            except asyncio.TimeoutError:
                print("⚠️ 回测超时，跳过")
                backtest_results = {"backtest_available": False, "error": "Timeout"}

        # 计算最终置信度指标
        confidence_metrics = analyzer.calculate_confidence_metrics(
            simulation_results=fill_results,
            num_simulations=10000,
            backtest_results=backtest_results
        )

        # Step 10: 生成建议
        print("💡 生成智能建议...")
        recommender = RecommendationEngine()
        recommendations_result = await recommender.generate_recommendations(
            fill_results=fill_results,
            current_price=current_price,
            limit_price=limit_price,
            order_side=order_side,
            confidence_metrics=confidence_metrics
        )

        # Step 11: 格式化最终响应
        et_time = get_market_time_et()

        return {
            "symbol": symbol,
            "option_details": {
                "strike": strike_price,
                "expiration": expiration,
                "type": option_type,
                "current_price": current_price,
                "limit_price": limit_price,
                "order_side": order_side,
                "underlying_price": underlying_price
            },
            "fill_probability": fill_results["fill_probability"],
            "first_day_fill_probability": fill_results["first_day_fill_probability"],
            "expected_days_to_fill": fill_results.get("expected_days_to_fill"),
            "median_days_to_fill": fill_results.get("median_days_to_fill"),
            "standard_error": confidence_metrics["standard_error"],
            "confidence_metrics": confidence_metrics,
            "probability_by_day": fill_results["probability_by_day"],
            "percentile_days": fill_results.get("percentile_days", {}),
            "percentile_descriptions": fill_results.get("percentile_descriptions", {}),  # 新增
            "touch_probability": fill_results.get("touch_probability"),
            "analysis_basis": {
                "implied_volatility": implied_vol,
                "historical_volatility": vol_result["historical_volatility"],
                "effective_volatility": effective_vol,
                "volatility_method": vol_result["method"],
                "iv_hv_ratio": vol_result.get("iv_hv_ratio"),
                "delta": delta,
                "theta": theta,
                "gamma": gamma,
                "vega": vega,
                "days_to_expiry": days_to_expiry,
                "analysis_window": analysis_window or days_to_expiry,
                "price_move_required": limit_price - current_price,
                "move_percentage": abs(limit_price - current_price) / current_price * 100
            },
            "validation": {
                "method": "monte_carlo",
                "simulations": 10000,
                "theoretical_validation": validation_results,
                "theoretical_validated": validation_results.get("all_tests_passed", False),
                "backtest_available": backtest_results is not None and backtest_results.get("backtest_available", False),
                "backtest_mae": backtest_results.get("mae") if backtest_results else None,
                "backtest_samples": backtest_results.get("backtest_samples") if backtest_results else None,
                "confidence_level": confidence_metrics["confidence_level"],
                "confidence_score": confidence_metrics["confidence_score"]
            },
            "recommendations": recommendations_result["recommendations"],
            "alternative_limits": recommendations_result["alternative_limits"],
            "optimal_limits": {
                "for_80pct_fill": recommendations_result.get("optimal_limit_for_80pct"),
                "for_quick_fill": recommendations_result.get("optimal_limit_for_quick_fill")
            },
            "analysis_timestamp": et_time.strftime("%Y-%m-%d %H:%M:%S ET"),
            "market_context": {
                "session": market_ctx["market_session"],
                "first_trading_day": "今天" if market_ctx["first_day_is_today"] else "明天",
                "first_day_fraction": market_ctx["first_day_fraction"],
                "explanation": market_ctx["explanation"],
                "remaining_hours": market_ctx.get("remaining_hours"),
                "total_trading_hours": market_ctx.get("total_trading_hours"),
                "trading_hours_display": market_ctx.get("trading_hours_display"),
                "current_iv_percentile": None,
                "recent_volatility_trend": "elevated" if vol_result.get("iv_hv_ratio", 1.0) > 1.2 else "normal"
            },
            "disclaimer": (
                "本分析基于统计模型和历史数据，不构成投资建议。"
                "实际成交受市场流动性、订单簿深度等多种因素影响。"
                "期权交易存在重大风险，可能导致全部本金损失。"
                "请谨慎决策，自行承担交易风险。"
            ),
            "status": "success"
        }

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"❌ 限价单概率分析错误: {str(e)}")
        print(f"详细错误:\n{error_trace}")

        return {
            "error": f"Analysis failed: {str(e)}",
            "error_type": type(e).__name__,
            "error_trace": error_trace if settings.debug_mode else None,
            "symbol": symbol,
            "status": "error"
        }
