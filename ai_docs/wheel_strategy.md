# Refefence Implementation for Wheel Strategy
The implementation includes both (1) cash-secured sell put strategy and (2) sell covered call strategy.

```python
"""
Wheel Strategy Construction Module
Provides tools to construct cash-secured put and covered call legs for the wheel strategy
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import OptionLatestQuoteRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import AssetStatus, ContractType
from alpaca.trading.requests import GetOptionContractsRequest

from ..providers.tradier_client import TradierClient
from .greeks import calculate_all_greeks, calculate_implied_volatility


async def construct_wheel_strategy(
    symbol: str,
    buying_power_limit: float,
    risk_free_rate: float,
    oi_threshold: int,
    delta_range_min: float,
    delta_range_max: float,
    provider: str,
    trade_client: Optional[TradingClient],
    option_client: Optional[OptionHistoricalDataClient],
    stock_client: Optional[StockHistoricalDataClient],
    tradier_client: Optional[TradierClient],
) -> str:
    """
    Construct cash-secured put and covered call legs for the wheel strategy

    Args:
        symbol: Underlying stock symbol
        buying_power_limit: Maximum buying power to use
        risk_free_rate: Risk-free rate for calculations
        oi_threshold: Minimum open interest threshold
        delta_range_min: Minimum delta for puts (e.g., -0.42)
        delta_range_max: Maximum delta for puts (e.g., -0.18)
        provider: Market data provider ('ALPACA' or 'TRADIER')
        trade_client: Alpaca trading client (when using ALPACA)
        option_client: Alpaca option data client (when using ALPACA)
        stock_client: Alpaca stock data client (when using ALPACA)
        tradier_client: Tradier client (when using TRADIER)

    Returns:
        Formatted string with wheel strategy recommendations
    """
    try:
        if provider == "ALPACA":
            return await _construct_wheel_strategy_alpaca(
                symbol,
                buying_power_limit,
                risk_free_rate,
                oi_threshold,
                delta_range_min,
                delta_range_max,
                trade_client,
                option_client,
                stock_client,
            )
        elif provider == "TRADIER":
            return await _construct_wheel_strategy_tradier(
                symbol,
                buying_power_limit,
                risk_free_rate,
                oi_threshold,
                delta_range_min,
                delta_range_max,
                tradier_client,
            )
        else:
            return f"Unsupported provider: {provider}"

    except Exception as e:
        return f"Error constructing wheel strategy for {symbol}: {str(e)}"


async def _construct_wheel_strategy_alpaca(
    symbol: str,
    buying_power_limit: float,
    risk_free_rate: float,
    oi_threshold: int,
    delta_range_min: float,
    delta_range_max: float,
    trade_client: TradingClient,
    option_client: OptionHistoricalDataClient,
    stock_client: StockHistoricalDataClient,
) -> str:
    """Construct wheel strategy using Alpaca API"""
    # For now, return a placeholder implementation
    return json.dumps(
        {
            "provider": "ALPACA",
            "symbol": symbol,
            "message": "Wheel strategy construction for Alpaca - implementation in progress",
            "parameters": {
                "buying_power_limit": buying_power_limit,
                "risk_free_rate": risk_free_rate,
                "oi_threshold": oi_threshold,
                "delta_range_min": delta_range_min,
                "delta_range_max": delta_range_max,
            },
        },
        indent=2,
    )


async def _construct_wheel_strategy_tradier(
    symbol: str,
    buying_power_limit: float,
    risk_free_rate: float,
    oi_threshold: int,
    delta_range_min: float,
    delta_range_max: float,
    tradier_client: TradierClient,
) -> str:
    """Construct wheel strategy using Tradier API"""
    try:
        # Get current underlying price
        quotes = tradier_client.get_quotes([symbol])
        if not quotes:
            return json.dumps(
                {"provider": "TRADIER", "symbol": symbol, "error": f"Unable to get underlying price for {symbol}"},
                indent=2,
            )

        underlying_price = quotes[0].last
        if underlying_price is None:
            return json.dumps(
                {"provider": "TRADIER", "symbol": symbol, "error": f"No price data available for {symbol}"}, indent=2
            )

        # Find cash-secured put options
        put_recommendation = await find_cash_secured_put_tradier(
            symbol,
            underlying_price,
            buying_power_limit,
            risk_free_rate,
            oi_threshold,
            delta_range_min,
            delta_range_max,
            tradier_client,
        )

        # Check for existing position to determine covered call availability
        call_recommendation = await find_covered_call_tradier(
            symbol, underlying_price, risk_free_rate, oi_threshold, tradier_client
        )

        # Generate strategy summary
        strategy_summary = generate_tradier_strategy_summary(
            put_recommendation, call_recommendation, underlying_price, buying_power_limit
        )

        # Create comprehensive response
        result = {
            "provider": "TRADIER",
            "symbol": symbol,
            "underlying_price": round(underlying_price, 2),
            "strategy_type": "wheel_strategy",
            "parameters": {
                "buying_power_limit": buying_power_limit,
                "risk_free_rate": risk_free_rate,
                "oi_threshold": oi_threshold,
                "delta_range_min": delta_range_min,
                "delta_range_max": delta_range_max,
            },
            "cash_secured_puts": put_recommendation,
            "covered_calls": call_recommendation,
            "strategy_summary": strategy_summary,
            "generated_at": datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M:%S %Z"),
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps(
            {"provider": "TRADIER", "symbol": symbol, "error": f"Error constructing wheel strategy: {str(e)}"}, indent=2
        )


async def find_cash_secured_put_tradier(
    symbol: str,
    underlying_price: float,
    buying_power_limit: float,
    risk_free_rate: float,
    oi_threshold: int,
    delta_range_min: float,
    delta_range_max: float,
    tradier_client: TradierClient,
) -> Dict[str, Any]:
    """Find suitable cash-secured put option using Tradier API"""
    try:
        timezone = ZoneInfo("America/New_York")
        today = datetime.now(timezone).date()

        # Set expiration date range (7 to 35 days)
        min_expiration = today + timedelta(days=7)
        max_expiration = today + timedelta(days=35)

        # Calculate strike price range (5% around current price)
        strike_range = 0.05
        min_strike = underlying_price * (1 - strike_range)
        max_strike = underlying_price * (1 + strike_range)

        # Get available expiration dates
        expirations = tradier_client.get_option_expirations(symbol)
        valid_expirations = []
        for exp_str in expirations:
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
            if min_expiration <= exp_date <= max_expiration:
                valid_expirations.append(exp_str)

        if not valid_expirations:
            return {"status": "no_options", "message": "No options found within expiration range"}

        suitable_puts = []

        # Get option chains for each valid expiration
        for expiration in valid_expirations:
            try:
                options = tradier_client.get_option_chain(symbol, expiration, include_greeks=True)

                for option in options:
                    if (
                        option.option_type != "put"
                        or option.strike is None
                        or option.strike < min_strike
                        or option.strike > max_strike
                    ):
                        continue

                    # Check open interest threshold
                    if option.open_interest is None or option.open_interest < oi_threshold:
                        continue

                    # Calculate bid/ask/mid prices
                    bid_price = option.bid if option.bid is not None else 0
                    ask_price = option.ask if option.ask is not None else 0

                    if bid_price <= 0 or ask_price <= 0:
                        continue

                    mid_price = (bid_price + ask_price) / 2
                    strike_price = option.strike

                    # Check buying power requirement (100 shares per contract)
                    required_buying_power = strike_price * 100
                    if required_buying_power > buying_power_limit:
                        continue

                    # Calculate days to expiration
                    exp_date = datetime.strptime(option.expiration_date, "%Y-%m-%d").date()
                    days_to_expiry = (exp_date - today).days
                    time_to_expiry = max(days_to_expiry / 365.0, 1 / 365.0)

                    # Get delta from Greeks or calculate it
                    delta = None
                    implied_vol = None

                    if option.greeks and option.greeks.get("delta"):
                        delta = option.greeks["delta"]
                        implied_vol = option.greeks.get("mid_iv", 0.2)  # Default IV if not available
                    else:
                        # Calculate implied volatility and delta
                        implied_vol = calculate_implied_volatility(
                            mid_price, underlying_price, strike_price, time_to_expiry, risk_free_rate, "put"
                        )
                        if implied_vol:
                            greeks = calculate_all_greeks(
                                underlying_price, strike_price, time_to_expiry, risk_free_rate, implied_vol, "put"
                            )
                            delta = greeks["delta"]

                    if delta is None:
                        continue

                    # Check if delta is in target range (-0.42 to -0.18)
                    if delta_range_min <= delta <= delta_range_max:
                        suitable_puts.append(
                            {
                                "symbol": option.symbol,
                                "strike_price": strike_price,
                                "expiration_date": option.expiration_date,
                                "days_to_expiry": days_to_expiry,
                                "bid_price": round(bid_price, 2),
                                "ask_price": round(ask_price, 2),
                                "mid_price": round(mid_price, 2),
                                "open_interest": option.open_interest,
                                "required_buying_power": round(required_buying_power, 2),
                                "premium_income": round(mid_price * 100, 2),
                                "delta": round(delta, 4),
                                "implied_volatility": round(implied_vol, 4) if implied_vol else None,
                                "annualized_return": round(
                                    (mid_price / strike_price) * (365 / days_to_expiry) * 100, 2
                                ),
                                "probability_assignment": round(abs(delta) * 100, 1),
                            }
                        )
            except Exception:
                continue  # Skip expirations that fail

        if suitable_puts:
            # Sort by annualized return (descending) then by delta (closest to -0.3)
            suitable_puts.sort(key=lambda x: (-x["annualized_return"], abs(x["delta"] + 0.3)))

            return {
                "status": "found",
                "count": len(suitable_puts),
                "recommended": suitable_puts[0],
                "alternatives": suitable_puts[1:5],  # Top 5 alternatives
            }
        else:
            return {
                "status": "no_suitable",
                "message": f"No put options found with delta between {delta_range_min} and {delta_range_max}",
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


async def find_covered_call_tradier(
    symbol: str, underlying_price: float, risk_free_rate: float, oi_threshold: int, tradier_client: TradierClient
) -> Dict[str, Any]:
    """Find suitable covered call option using Tradier API"""
    try:
        timezone = ZoneInfo("America/New_York")
        today = datetime.now(timezone).date()

        # Set expiration date range (7 to 35 days)
        min_expiration = today + timedelta(days=7)
        max_expiration = today + timedelta(days=35)

        # Calculate upper Bollinger Band for strike selection
        try:
            upper_bollinger = await calculate_upper_bollinger_band_tradier(symbol, tradier_client)
        except Exception:
            # Fallback to 110% of current price if Bollinger calculation fails
            upper_bollinger = underlying_price * 1.1

        # Set call strike range (above current price and preferably above Bollinger Band)
        call_min_strike = max(underlying_price * 1.02, underlying_price)  # At least 2% above current price
        call_max_strike = underlying_price * 1.15  # Up to 15% above current price

        # Get available expiration dates
        expirations = tradier_client.get_option_expirations(symbol)
        valid_expirations = []
        for exp_str in expirations:
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
            if min_expiration <= exp_date <= max_expiration:
                valid_expirations.append(exp_str)

        if not valid_expirations:
            return {"status": "no_options", "message": "No options found within expiration range"}

        suitable_calls = []

        # Get option chains for each valid expiration
        for expiration in valid_expirations:
            try:
                options = tradier_client.get_option_chain(symbol, expiration, include_greeks=True)

                for option in options:
                    if (
                        option.option_type != "call"
                        or option.strike is None
                        or option.strike < call_min_strike
                        or option.strike > call_max_strike
                    ):
                        continue

                    # Check open interest threshold
                    if option.open_interest is None or option.open_interest < oi_threshold:
                        continue

                    # Calculate bid/ask/mid prices
                    bid_price = option.bid if option.bid is not None else 0
                    ask_price = option.ask if option.ask is not None else 0

                    if bid_price <= 0 or ask_price <= 0:
                        continue

                    mid_price = (bid_price + ask_price) / 2
                    strike_price = option.strike

                    # Calculate days to expiration
                    exp_date = datetime.strptime(option.expiration_date, "%Y-%m-%d").date()
                    days_to_expiry = (exp_date - today).days
                    time_to_expiry = max(days_to_expiry / 365.0, 1 / 365.0)

                    # Get delta from Greeks or calculate it
                    delta = None
                    implied_vol = None

                    if option.greeks and option.greeks.get("delta"):
                        delta = option.greeks["delta"]
                        implied_vol = option.greeks.get("mid_iv", 0.2)
                    else:
                        # Calculate implied volatility and delta
                        implied_vol = calculate_implied_volatility(
                            mid_price, underlying_price, strike_price, time_to_expiry, risk_free_rate, "call"
                        )
                        if implied_vol:
                            greeks = calculate_all_greeks(
                                underlying_price, strike_price, time_to_expiry, risk_free_rate, implied_vol, "call"
                            )
                            delta = greeks["delta"]

                    if delta is None:
                        continue

                    # Look for calls with delta between 0.18 and 0.42, preferably above Bollinger Band
                    if 0.18 <= delta <= 0.42:
                        suitable_calls.append(
                            {
                                "symbol": option.symbol,
                                "strike_price": strike_price,
                                "expiration_date": option.expiration_date,
                                "days_to_expiry": days_to_expiry,
                                "bid_price": round(bid_price, 2),
                                "ask_price": round(ask_price, 2),
                                "mid_price": round(mid_price, 2),
                                "open_interest": option.open_interest,
                                "premium_income": round(mid_price * 100, 2),
                                "delta": round(delta, 4),
                                "implied_volatility": round(implied_vol, 4) if implied_vol else None,
                                "max_profit": round((strike_price - underlying_price + mid_price) * 100, 2),
                                "annualized_return": round(
                                    (mid_price / underlying_price) * (365 / days_to_expiry) * 100, 2
                                ),
                                "probability_assignment": round(delta * 100, 1),
                                "above_bollinger": strike_price > upper_bollinger,
                            }
                        )
            except Exception:
                continue  # Skip expirations that fail

        if suitable_calls:
            # Sort by: 1) above Bollinger Band preference, 2) annualized return (descending)
            suitable_calls.sort(key=lambda x: (-x["above_bollinger"], -x["annualized_return"]))

            return {
                "status": "found",
                "count": len(suitable_calls),
                "recommended": suitable_calls[0],
                "alternatives": suitable_calls[1:5],  # Top 5 alternatives
                "upper_bollinger_band": round(upper_bollinger, 2),
            }
        else:
            return {"status": "no_suitable", "message": "No call options found with delta between 0.18 and 0.42"}

    except Exception as e:
        return {"status": "error", "message": str(e)}


async def calculate_upper_bollinger_band_tradier(symbol: str, tradier_client: TradierClient) -> float:
    """Calculate 20-day upper Bollinger Band using Tradier historical data"""
    try:
        # Get 60 days of historical data to ensure we have enough for 20-day calculation
        timezone = ZoneInfo("America/New_York")
        today = datetime.now(timezone).date()
        start_date = (today - timedelta(days=60)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")

        historical_data = tradier_client.get_historical_data(
            symbol=symbol, start_date=start_date, end_date=end_date, interval="daily"
        )

        if not historical_data or len(historical_data) < 20:
            # Fallback: return current price * 1.1 as estimate
            quotes = tradier_client.get_quotes([symbol])
            current_price = quotes[0].last if quotes else 100.0
            return current_price * 1.1

        # Calculate 20-day SMA and standard deviation
        closes = [float(data.close) for data in historical_data[-20:]]
        sma_20 = sum(closes) / len(closes)

        # Calculate standard deviation
        variance = sum([(close - sma_20) ** 2 for close in closes]) / len(closes)
        std_20 = variance**0.5

        # Upper Bollinger Band = SMA + (2 * Standard Deviation)
        upper_band = sma_20 + (2 * std_20)

        return upper_band

    except Exception:
        # Return conservative estimate if calculation fails
        quotes = tradier_client.get_quotes([symbol])
        current_price = quotes[0].last if quotes else 100.0
        return current_price * 1.1


def generate_tradier_strategy_summary(
    put_rec: Dict, call_rec: Dict, underlying_price: float, buying_power_limit: float
) -> Dict[str, Any]:
    """Generate overall wheel strategy summary for Tradier"""
    summary = {
        "wheel_status": "incomplete",
        "recommended_actions": [],
        "total_income_potential": 0,
        "risk_assessment": "moderate",
        "buying_power_usage": 0,
    }

    if put_rec.get("status") == "found":
        put_data = put_rec["recommended"]
        summary["recommended_actions"].append(
            {
                "action": "sell_cash_secured_put",
                "description": f"Sell {put_data['symbol']} for ${put_data['premium_income']} premium",
                "strike_price": put_data["strike_price"],
                "expiration_date": put_data["expiration_date"],
                "delta": put_data["delta"],
                "probability_assignment": put_data["probability_assignment"],
                "required_buying_power": put_data["required_buying_power"],
                "annualized_return": put_data["annualized_return"],
            }
        )
        summary["total_income_potential"] += put_data["premium_income"]
        summary["buying_power_usage"] += put_data["required_buying_power"]
    elif put_rec.get("status") == "no_suitable":
        summary["recommended_actions"].append(
            {
                "action": "wait_for_put_opportunity",
                "description": put_rec.get("message", "No suitable put options found"),
            }
        )

    if call_rec.get("status") == "found":
        call_data = call_rec["recommended"]
        summary["recommended_actions"].append(
            {
                "action": "sell_covered_call",
                "description": f"Sell {call_data['symbol']} for ${call_data['premium_income']} premium",
                "strike_price": call_data["strike_price"],
                "expiration_date": call_data["expiration_date"],
                "delta": call_data["delta"],
                "max_profit": call_data["max_profit"],
                "probability_assignment": call_data["probability_assignment"],
                "annualized_return": call_data["annualized_return"],
            }
        )
        summary["total_income_potential"] += call_data["premium_income"]
        summary["wheel_status"] = "complete" if put_rec.get("status") == "found" else "call_only"
    elif call_rec.get("status") == "insufficient_shares":
        summary["recommended_actions"].append(
            {"action": "acquire_shares_first", "description": "Need to own at least 100 shares to sell covered calls"}
        )
    elif call_rec.get("status") == "no_suitable":
        summary["recommended_actions"].append(
            {
                "action": "wait_for_call_opportunity",
                "description": call_rec.get("message", "No suitable call options found"),
            }
        )

    if not summary["recommended_actions"]:
        summary["recommended_actions"].append(
            {"action": "wait", "description": "No suitable options found matching wheel strategy criteria"}
        )
        summary["wheel_status"] = "waiting"

    # Calculate buying power utilization
    if buying_power_limit > 0:
        summary["buying_power_utilization"] = round((summary["buying_power_usage"] / buying_power_limit) * 100, 1)

    return summary


async def find_cash_secured_put(
    symbol: str,
    underlying_price: float,
    min_strike: float,
    max_strike: float,
    min_expiration,
    max_expiration,
    buying_power_limit: float,
    risk_free_rate: float,
    oi_threshold: int,
    delta_range_min: float,
    delta_range_max: float,
    trade_client: TradingClient,
    option_client: OptionHistoricalDataClient,
) -> Dict[str, Any]:
    """Find suitable cash-secured put option"""
    try:
        # Get put options
        put_request = GetOptionContractsRequest(
            underlying_symbols=[symbol],
            strike_price_gte=str(min_strike),
            strike_price_lte=str(max_strike),
            status=AssetStatus.ACTIVE,
            expiration_date_gte=min_expiration,
            expiration_date_lte=max_expiration,
            root_symbol=symbol,
            type=ContractType.PUT,
        )

        put_options = trade_client.get_option_contracts(put_request).option_contracts

        if not put_options:
            return {"status": "no_options", "message": "No put options found in the specified range"}

        suitable_puts = []

        for option in put_options:
            try:
                # Check open interest
                if not option.open_interest or float(option.open_interest) < oi_threshold:
                    continue

                # Get latest quote
                option_quote_request = OptionLatestQuoteRequest(symbol_or_symbols=option.symbol)
                option_quote_response = option_client.get_option_latest_quote(option_quote_request)
                option_quote = option_quote_response[option.symbol]

                bid_price = float(option_quote.bid_price) if option_quote.bid_price else 0
                ask_price = float(option_quote.ask_price) if option_quote.ask_price else 0

                if bid_price <= 0 or ask_price <= 0:
                    continue

                mid_price = (bid_price + ask_price) / 2
                strike_price = float(option.strike_price)
                option_size = float(option.size) if option.size else 100

                # Check buying power requirement
                required_buying_power = strike_price * option_size
                if required_buying_power > buying_power_limit:
                    continue

                # Calculate Greeks
                days_to_expiry = (option.expiration_date - datetime.now(ZoneInfo("America/New_York")).date()).days
                time_to_expiry = max(days_to_expiry / 365.0, 1 / 365.0)

                # Calculate implied volatility and delta
                implied_vol = calculate_implied_volatility(
                    mid_price, underlying_price, strike_price, time_to_expiry, risk_free_rate, "put"
                )

                if implied_vol is None:
                    continue

                greeks = calculate_all_greeks(
                    underlying_price, strike_price, time_to_expiry, risk_free_rate, implied_vol, "put"
                )

                delta = greeks["delta"]

                # Check if delta is in target range
                if delta_range_min <= delta <= delta_range_max:
                    suitable_puts.append(
                        {
                            "symbol": option.symbol,
                            "strike_price": strike_price,
                            "expiration_date": option.expiration_date.strftime("%Y-%m-%d"),
                            "days_to_expiry": days_to_expiry,
                            "bid_price": round(bid_price, 2),
                            "ask_price": round(ask_price, 2),
                            "mid_price": round(mid_price, 2),
                            "open_interest": int(option.open_interest),
                            "required_buying_power": round(required_buying_power, 2),
                            "premium_income": round(mid_price * option_size, 2),
                            "delta": round(delta, 4),
                            "implied_volatility": round(implied_vol, 4),
                            "theta": round(greeks["theta"], 4),
                            "vega": round(greeks["vega"], 4),
                            "annualized_return": round((mid_price / strike_price) * (365 / days_to_expiry) * 100, 2),
                            "probability_assignment": round(abs(delta) * 100, 1),
                        }
                    )

            except Exception:
                continue  # Skip problematic options

        if suitable_puts:
            # Sort by annualized return (descending) then by delta (closest to -0.3)
            suitable_puts.sort(key=lambda x: (-x["annualized_return"], abs(x["delta"] + 0.3)))

            return {
                "status": "found",
                "count": len(suitable_puts),
                "recommended": suitable_puts[0],
                "alternatives": suitable_puts[1:5],  # Top 5 alternatives
            }
        else:
            return {
                "status": "no_suitable",
                "message": f"No put options found with delta between {delta_range_min} and {delta_range_max}",
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


async def find_covered_call(
    symbol: str,
    underlying_price: float,
    min_strike: float,
    max_strike: float,
    min_expiration,
    max_expiration,
    risk_free_rate: float,
    oi_threshold: int,
    trade_client: TradingClient,
    option_client: OptionHistoricalDataClient,
    stock_client: StockHistoricalDataClient,
) -> Dict[str, Any]:
    """Find suitable covered call option (if we own shares)"""
    try:
        # Check if we have positions in the stock
        try:
            positions = trade_client.get_all_positions()
            stock_position = next((pos for pos in positions if pos.symbol == symbol), None)

            if not stock_position or int(stock_position.qty_available) < 100:
                return {
                    "status": "insufficient_shares",
                    "message": f"Need at least 100 shares of {symbol} to sell covered calls",
                    "current_position": int(stock_position.qty_available) if stock_position else 0,
                }
        except Exception:
            return {"status": "no_position", "message": f"No position found in {symbol}"}

        # Calculate upper Bollinger Band for strike selection
        upper_bollinger = await calculate_upper_bollinger_band(symbol, stock_client)

        # Adjust strike range to be above current price
        call_min_strike = max(underlying_price * 1.02, min_strike)  # At least 2% above current price
        call_max_strike = min(upper_bollinger * 1.05, max_strike)  # Up to 5% above Bollinger Band

        # Get call options
        call_request = GetOptionContractsRequest(
            underlying_symbols=[symbol],
            strike_price_gte=str(call_min_strike),
            strike_price_lte=str(call_max_strike),
            status=AssetStatus.ACTIVE,
            expiration_date_gte=min_expiration,
            expiration_date_lte=max_expiration,
            root_symbol=symbol,
            type=ContractType.CALL,
        )

        call_options = trade_client.get_option_contracts(call_request).option_contracts

        if not call_options:
            return {"status": "no_options", "message": "No call options found in the specified range"}

        suitable_calls = []

        for option in call_options:
            try:
                # Check open interest
                if not option.open_interest or float(option.open_interest) < oi_threshold:
                    continue

                # Get latest quote
                option_quote_request = OptionLatestQuoteRequest(symbol_or_symbols=option.symbol)
                option_quote_response = option_client.get_option_latest_quote(option_quote_request)
                option_quote = option_quote_response[option.symbol]

                bid_price = float(option_quote.bid_price) if option_quote.bid_price else 0
                ask_price = float(option_quote.ask_price) if option_quote.ask_price else 0

                if bid_price <= 0 or ask_price <= 0:
                    continue

                mid_price = (bid_price + ask_price) / 2
                strike_price = float(option.strike_price)
                option_size = float(option.size) if option.size else 100

                # Calculate Greeks
                days_to_expiry = (option.expiration_date - datetime.now(ZoneInfo("America/New_York")).date()).days
                time_to_expiry = max(days_to_expiry / 365.0, 1 / 365.0)

                # Calculate implied volatility and delta
                implied_vol = calculate_implied_volatility(
                    mid_price, underlying_price, strike_price, time_to_expiry, risk_free_rate, "call"
                )

                if implied_vol is None:
                    continue

                greeks = calculate_all_greeks(
                    underlying_price, strike_price, time_to_expiry, risk_free_rate, implied_vol, "call"
                )

                delta = greeks["delta"]

                # Look for calls with delta between 0.18 and 0.42
                if 0.18 <= delta <= 0.42 and strike_price > upper_bollinger:
                    suitable_calls.append(
                        {
                            "symbol": option.symbol,
                            "strike_price": strike_price,
                            "expiration_date": option.expiration_date.strftime("%Y-%m-%d"),
                            "days_to_expiry": days_to_expiry,
                            "bid_price": round(bid_price, 2),
                            "ask_price": round(ask_price, 2),
                            "mid_price": round(mid_price, 2),
                            "open_interest": int(option.open_interest),
                            "premium_income": round(mid_price * option_size, 2),
                            "delta": round(delta, 4),
                            "implied_volatility": round(implied_vol, 4),
                            "theta": round(greeks["theta"], 4),
                            "vega": round(greeks["vega"], 4),
                            "max_profit": round((strike_price - underlying_price + mid_price) * option_size, 2),
                            "annualized_return": round(
                                (mid_price / underlying_price) * (365 / days_to_expiry) * 100, 2
                            ),
                            "probability_assignment": round(delta * 100, 1),
                        }
                    )

            except Exception:
                continue  # Skip problematic options

        if suitable_calls:
            # Sort by annualized return (descending)
            suitable_calls.sort(key=lambda x: -x["annualized_return"])

            return {
                "status": "found",
                "count": len(suitable_calls),
                "recommended": suitable_calls[0],
                "alternatives": suitable_calls[1:5],  # Top 5 alternatives
                "upper_bollinger_band": round(upper_bollinger, 2),
            }
        else:
            return {
                "status": "no_suitable",
                "message": "No call options found with delta between 0.18 and 0.42 above Bollinger Band",
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


async def calculate_upper_bollinger_band(symbol: str, stock_client: StockHistoricalDataClient) -> float:
    """Calculate 20-day upper Bollinger Band"""
    try:
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

        timezone = ZoneInfo("America/New_York")
        now = datetime.now(timezone)

        bars_request = StockBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=TimeFrame(amount=1, unit=TimeFrameUnit.Day),
            start=now - timedelta(days=60),
            end=now,
        )

        bars_response = stock_client.get_stock_bars(bars_request)
        df = bars_response.df

        if len(df) < 20:
            # If insufficient data, return current price * 1.1 as estimate
            from alpaca.data.historical.stock import StockLatestTradeRequest

            latest_trade_request = StockLatestTradeRequest(symbol_or_symbols=symbol)
            latest_trade_response = stock_client.get_stock_latest_trade(latest_trade_request)
            return float(latest_trade_response[symbol].price) * 1.1

        # Calculate 20-day SMA and standard deviation
        df = df.reset_index()
        sma_20 = df["close"].tail(20).mean()
        std_20 = df["close"].tail(20).std()

        # Upper Bollinger Band = SMA + (2 * Standard Deviation)
        upper_band = sma_20 + (2 * std_20)

        return upper_band

    except Exception:
        # Return conservative estimate if calculation fails
        from alpaca.data.historical.stock import StockLatestTradeRequest

        latest_trade_request = StockLatestTradeRequest(symbol_or_symbols=symbol)
        latest_trade_response = stock_client.get_stock_latest_trade(latest_trade_request)
        return float(latest_trade_response[symbol].price) * 1.1


def generate_strategy_summary(put_rec: Dict, call_rec: Dict, underlying_price: float) -> Dict[str, Any]:
    """Generate overall strategy summary"""
    summary = {
        "wheel_status": "incomplete",
        "recommended_actions": [],
        "income_potential": 0,
        "risk_assessment": "moderate",
    }

    if put_rec.get("status") == "found":
        summary["recommended_actions"].append(
            {
                "action": "sell_cash_secured_put",
                "description": f"Sell {put_rec['recommended']['symbol']} for ${put_rec['recommended']['premium_income']} premium",
                "probability_assignment": put_rec["recommended"]["probability_assignment"],
            }
        )
        summary["income_potential"] += put_rec["recommended"]["premium_income"]

    if call_rec.get("status") == "found":
        summary["recommended_actions"].append(
            {
                "action": "sell_covered_call",
                "description": f"Sell {call_rec['recommended']['symbol']} for ${call_rec['recommended']['premium_income']} premium",
                "max_profit": call_rec["recommended"]["max_profit"],
            }
        )
        summary["income_potential"] += call_rec["recommended"]["premium_income"]
        summary["wheel_status"] = "complete"

    if not summary["recommended_actions"]:
        summary["recommended_actions"].append(
            {"action": "wait", "description": "No suitable options found matching strategy criteria"}
        )
        summary["wheel_status"] = "waiting"

    return summary

```
