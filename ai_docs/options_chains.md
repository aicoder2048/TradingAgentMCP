# Reference Implementation of Options Chains

```python
"""
Option Chain Data Retrieval Module
Provides tools to get option chain data for puts and calls
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.historical.stock import StockHistoricalDataClient, StockLatestTradeRequest
from alpaca.data.requests import OptionLatestQuoteRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import AssetStatus, ContractType
from alpaca.trading.requests import GetOptionContractsRequest

from ..providers.tradier_client import TradierClient


async def get_option_chain_data(
    symbol: str,
    min_expiration_days: int,
    max_expiration_days: int,
    strike_range: float,
    provider: str,
    trade_client: Optional[TradingClient],
    option_client: Optional[OptionHistoricalDataClient],
    stock_client: Optional[StockHistoricalDataClient],
    tradier_client: Optional[TradierClient],
) -> str:
    """
    Get option chain data for puts and calls with various expiration dates and strikes

    Args:
        symbol: Underlying stock symbol
        min_expiration_days: Minimum days to expiration
        max_expiration_days: Maximum days to expiration
        strike_range: Strike range as percentage (e.g., 0.05 for 5%)
        provider: Market data provider ('ALPACA' or 'TRADIER')
        trade_client: Alpaca trading client (when using ALPACA)
        option_client: Alpaca option data client (when using ALPACA)
        stock_client: Alpaca stock data client (when using ALPACA)
        tradier_client: Tradier client (when using TRADIER)

    Returns:
        Formatted string with option chain data
    """
    try:
        if provider == "ALPACA":
            return await _get_option_chain_alpaca(
                symbol,
                min_expiration_days,
                max_expiration_days,
                strike_range,
                trade_client,
                option_client,
                stock_client,
            )
        elif provider == "TRADIER":
            return _get_option_chain_tradier(
                symbol, min_expiration_days, max_expiration_days, strike_range, tradier_client
            )
        else:
            return f"Unsupported provider: {provider}"

    except Exception as e:
        return f"Error retrieving option chain for {symbol}: {str(e)}"


async def _get_option_chain_alpaca(
    symbol: str,
    min_expiration_days: int,
    max_expiration_days: int,
    strike_range: float,
    trade_client: TradingClient,
    option_client: OptionHistoricalDataClient,
    stock_client: StockHistoricalDataClient,
) -> str:
    """Get option chain using Alpaca API"""
    timezone = ZoneInfo("America/New_York")
    today = datetime.now(timezone).date()

    # Get current underlying price
    latest_trade_request = StockLatestTradeRequest(symbol_or_symbols=symbol)
    latest_trade_response = stock_client.get_stock_latest_trade(latest_trade_request)
    underlying_price = float(latest_trade_response[symbol].price)

    # Calculate strike price range
    min_strike = underlying_price * (1 - strike_range)
    max_strike = underlying_price * (1 + strike_range)

    # Calculate expiration date range
    min_expiration = today + timedelta(days=min_expiration_days)
    max_expiration = today + timedelta(days=max_expiration_days)

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

    # Get call options
    call_request = GetOptionContractsRequest(
        underlying_symbols=[symbol],
        strike_price_gte=str(min_strike),
        strike_price_lte=str(max_strike),
        status=AssetStatus.ACTIVE,
        expiration_date_gte=min_expiration,
        expiration_date_lte=max_expiration,
        root_symbol=symbol,
        type=ContractType.CALL,
    )

    call_options = trade_client.get_option_contracts(call_request).option_contracts

    # Process put options
    puts_data = []
    for option in put_options:
        try:
            option_data = await process_option_data(option, option_client, underlying_price)
            if option_data:
                puts_data.append(option_data)
        except Exception:
            continue  # Skip options that fail to process

    # Process call options
    calls_data = []
    for option in call_options:
        try:
            option_data = await process_option_data(option, option_client, underlying_price)
            if option_data:
                calls_data.append(option_data)
        except Exception:
            continue  # Skip options that fail to process

    # Sort options by expiration date and strike
    puts_data.sort(key=lambda x: (x["expiration_date"], x["strike_price"]))
    calls_data.sort(key=lambda x: (x["expiration_date"], x["strike_price"]))

    # Create summary
    option_chain_summary = {
        "provider": "ALPACA",
        "symbol": symbol,
        "underlying_price": round(underlying_price, 2),
        "strike_range": {"min": round(min_strike, 2), "max": round(max_strike, 2)},
        "expiration_range": {"min": min_expiration.strftime("%Y-%m-%d"), "max": max_expiration.strftime("%Y-%m-%d")},
        "puts": {"count": len(puts_data), "options": puts_data[:10]},  # Limit to first 10 for readability
        "calls": {"count": len(calls_data), "options": calls_data[:10]},  # Limit to first 10 for readability
    }

    return json.dumps(option_chain_summary, indent=2)


async def process_option_data(
    option, option_client: OptionHistoricalDataClient, underlying_price: float
) -> Dict[str, Any]:
    """
    Process individual option data including quotes and calculated metrics

    Args:
        option: Option contract data
        option_client: Alpaca option data client
        underlying_price: Current underlying stock price

    Returns:
        Dictionary with processed option data
    """
    try:
        # Get latest quote
        option_quote_request = OptionLatestQuoteRequest(symbol_or_symbols=option.symbol)
        option_quote_response = option_client.get_option_latest_quote(option_quote_request)
        option_quote = option_quote_response[option.symbol]

        # Calculate mid price
        bid_price = float(option_quote.bid_price) if option_quote.bid_price else 0
        ask_price = float(option_quote.ask_price) if option_quote.ask_price else 0
        mid_price = (bid_price + ask_price) / 2 if bid_price > 0 and ask_price > 0 else 0

        # Calculate intrinsic and time value
        strike_price = float(option.strike_price)
        if option.type == ContractType.PUT:
            intrinsic_value = max(0, strike_price - underlying_price)
        else:  # CALL
            intrinsic_value = max(0, underlying_price - strike_price)

        time_value = max(0, mid_price - intrinsic_value)

        # Calculate moneyness
        if option.type == ContractType.PUT:
            moneyness = strike_price / underlying_price
        else:  # CALL
            moneyness = underlying_price / strike_price

        # Determine if in-the-money
        if option.type == ContractType.PUT:
            in_the_money = underlying_price < strike_price
        else:  # CALL
            in_the_money = underlying_price > strike_price

        # Calculate days to expiration
        expiration_date = datetime.strptime(str(option.expiration_date), "%Y-%m-%d").date()
        today = datetime.now(ZoneInfo("America/New_York")).date()
        days_to_expiration = (expiration_date - today).days

        return {
            "symbol": option.symbol,
            "strike_price": strike_price,
            "expiration_date": option.expiration_date.strftime("%Y-%m-%d"),
            "days_to_expiration": days_to_expiration,
            "type": option.type.value,
            "bid_price": round(bid_price, 2),
            "ask_price": round(ask_price, 2),
            "mid_price": round(mid_price, 2),
            "bid_size": int(option_quote.bid_size) if option_quote.bid_size else 0,
            "ask_size": int(option_quote.ask_size) if option_quote.ask_size else 0,
            "open_interest": int(option.open_interest) if option.open_interest else 0,
            "intrinsic_value": round(intrinsic_value, 2),
            "time_value": round(time_value, 2),
            "moneyness": round(moneyness, 4),
            "in_the_money": in_the_money,
            "size": int(option.size) if option.size else 100,
        }

    except Exception:
        return None


def _get_option_chain_tradier(
    symbol: str, min_expiration_days: int, max_expiration_days: int, strike_range: float, tradier_client: TradierClient
) -> str:
    """Get option chain using Tradier API"""
    timezone = ZoneInfo("America/New_York")
    today = datetime.now(timezone).date()

    # Get current underlying price
    quotes = tradier_client.get_quotes([symbol])
    if not quotes:
        return f"Unable to get underlying price for {symbol}"

    underlying_price = quotes[0].last
    if underlying_price is None:
        return f"No price data available for {symbol}"

    # Calculate strike price range
    min_strike = underlying_price * (1 - strike_range)
    max_strike = underlying_price * (1 + strike_range)

    # Calculate expiration date range
    min_expiration = today + timedelta(days=min_expiration_days)
    max_expiration = today + timedelta(days=max_expiration_days)

    # Get available expiration dates
    expirations = tradier_client.get_option_expirations(symbol)
    valid_expirations = []
    for exp_str in expirations:
        exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
        if min_expiration <= exp_date <= max_expiration:
            valid_expirations.append(exp_str)

    if not valid_expirations:
        return f"No options found within expiration range for {symbol}"

    # Get option chains for each expiration
    all_puts = []
    all_calls = []

    for expiration in valid_expirations:
        try:
            options = tradier_client.get_option_chain(symbol, expiration, include_greeks=True)

            for option in options:
                if option.strike is None or option.strike < min_strike or option.strike > max_strike:
                    continue

                option_data = process_tradier_option_data(option, underlying_price)
                if option_data:
                    if option.option_type == "put":
                        all_puts.append(option_data)
                    elif option.option_type == "call":
                        all_calls.append(option_data)
        except Exception:
            continue  # Skip expirations that fail

    # Sort options by expiration date and strike
    all_puts.sort(key=lambda x: (x["expiration_date"], x["strike_price"]))
    all_calls.sort(key=lambda x: (x["expiration_date"], x["strike_price"]))

    # Create summary
    option_chain_summary = {
        "provider": "TRADIER",
        "symbol": symbol,
        "underlying_price": round(underlying_price, 2),
        "strike_range": {"min": round(min_strike, 2), "max": round(max_strike, 2)},
        "expiration_range": {"min": min_expiration.strftime("%Y-%m-%d"), "max": max_expiration.strftime("%Y-%m-%d")},
        "puts": {"count": len(all_puts), "options": all_puts[:10]},  # Limit to first 10 for readability
        "calls": {"count": len(all_calls), "options": all_calls[:10]},  # Limit to first 10 for readability
    }

    return json.dumps(option_chain_summary, indent=2)


def process_tradier_option_data(option, underlying_price: float) -> Dict[str, Any]:
    """Process individual Tradier option data"""
    try:
        strike_price = option.strike
        if strike_price is None:
            return None

        # Calculate bid/ask/mid prices
        bid_price = option.bid if option.bid is not None else 0
        ask_price = option.ask if option.ask is not None else 0
        mid_price = (bid_price + ask_price) / 2 if bid_price > 0 and ask_price > 0 else 0

        # Calculate intrinsic and time value
        if option.option_type == "put":
            intrinsic_value = max(0, strike_price - underlying_price)
        else:  # call
            intrinsic_value = max(0, underlying_price - strike_price)

        time_value = max(0, mid_price - intrinsic_value)

        # Calculate moneyness
        if option.option_type == "put":
            moneyness = strike_price / underlying_price
        else:  # call
            moneyness = underlying_price / strike_price

        # Determine if in-the-money
        if option.option_type == "put":
            in_the_money = underlying_price < strike_price
        else:  # call
            in_the_money = underlying_price > strike_price

        # Calculate days to expiration
        expiration_date = datetime.strptime(option.expiration_date, "%Y-%m-%d").date()
        today = datetime.now(ZoneInfo("America/New_York")).date()
        days_to_expiration = (expiration_date - today).days

        # Extract Greeks if available
        greeks_data = {}
        if option.greeks:
            greeks_data = {
                "delta": option.greeks.get("delta"),
                "gamma": option.greeks.get("gamma"),
                "theta": option.greeks.get("theta"),
                "vega": option.greeks.get("vega"),
                "rho": option.greeks.get("rho"),
                "implied_volatility": option.greeks.get("mid_iv"),
            }

        result = {
            "symbol": option.symbol,
            "strike_price": strike_price,
            "expiration_date": option.expiration_date,
            "days_to_expiration": days_to_expiration,
            "type": option.option_type,
            "bid_price": round(bid_price, 2),
            "ask_price": round(ask_price, 2),
            "mid_price": round(mid_price, 2),
            "open_interest": option.open_interest if option.open_interest is not None else 0,
            "intrinsic_value": round(intrinsic_value, 2),
            "time_value": round(time_value, 2),
            "moneyness": round(moneyness, 4),
            "in_the_money": in_the_money,
            "volume": option.volume if option.volume is not None else 0,
        }

        if greeks_data:
            result["greeks"] = greeks_data

        return result

    except Exception:
        return None

```
