---
Description: Option Position Rebalancer - 期权仓位再平衡与风险管理引擎 MCP server prompt for Options Trading Toolkit.
---

## Use this MCP server prompt when the user wants to:
✅ MANAGE existing option positions actively
✅ EVALUATE current P&L and risk exposure
✅ DECIDE on hold/close/roll strategies based on market conditions
✅ IMPLEMENT defensive roll strategies to mitigate downside risk
✅ OPTIMIZE position management for changing market dynamics
✅ REBALANCE portfolio Greeks and time decay exposure


## Instructions:
- Don't have to implement TaskProgressTracker

## Relative Implementation:
- /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/option_position_rebalancer.md
- The following are functions and files used/referered by the reference implementation above:
  1. get_current_us_east_datetime_tool
  READ /Users/szou/Python/Playground/MCP4Claude/src/mcp_server_options/modules/functionality/datetime_utils.py
  函数: async def get_current_us_east_datetime()

  2. get_market_calendar_info_tool
  READ /Users/szou/Python/Playground/MCP4Claude/src/mcp_server_options/modules/functionality/datetime_utils.py
  函数: async def get_market_calendar_info(days_ahead: int = 7)

  3. get_asset_info_tool

  READ /Users/szou/Python/Playground/MCP4Claude/src/mcp_server_options/modules/functionality/asset_info.py
  函数: async def get_asset_info(symbol, provider, alpaca_clients, tradier_client)

  4. get_option_chain_tool

  READ /Users/szou/Python/Playground/MCP4Claude/src/mcp_server_options/modules/functionality/option_chain.py
  函数: async def get_option_chain_data(symbol, min_expiration_days, max_expiration_days, strike_range, provider,
  alpaca_clients, tradier_client)

  5. calculate_assignment_probability_tool

  READ /Users/szou/Python/Playground/MCP4Claude/src/mcp_server_options/modules/functionality/assignment_probability.py
  函数: async def calculate_assignment_probability(underlying_price, strike_price, time_to_expiry_days, implied_volatility,
  risk_free_rate, option_type)

  6. analyze_option_position_tool

  READ /Users/szou/Python/Playground/MCP4Claude/src/mcp_server_options/modules/functionality/option_position_analysis.py
  函数: async def analyze_option_position(option_symbol, entry_price, position_type, number_of_contracts, underlying_price,
  current_price, risk_tolerance, include_greeks_analysis, include_market_outlook, include_roll_strategies, provider,
  alpaca_clients, tradier_client)

  7. analyze_option_strategy_tool

  READ /Users/szou/Python/Playground/MCP4Claude/src/mcp_server_options/modules/functionality/analyze_option_strategy.py
  函数: async def analyze_option_strategy(strategy_type, underlying_symbol, underlying_price, implied_volatility, ...)

  8. recommend_option_strategies_tool

  READ /Users/szou/Python/Playground/MCP4Claude/src/mcp_server_options/modules/functionality/analyze_option_strategy.py
  函数: async def recommend_option_strategies(underlying_price, market_outlook, volatility_outlook, capital_available,
  risk_tolerance)

  9. analyze_roll_strategy_tool

  READ /Users/szou/Python/Playground/MCP4Claude/src/mcp_server_options/modules/functionality/analyze_roll_strategy.py
  函数: async def analyze_roll_strategy(option_symbol, strike_price, quantity, days_to_expiry, premium_received,
  current_option_price, underlying_price, implied_volatility, target_cashless, max_additional_capital, risk_tolerance,
  include_real_time_chain, provider, alpaca_clients, tradier_client)

  10. construct_calendar_spread_tool

  READ /Users/szou/Python/Playground/MCP4Claude/src/mcp_server_options/modules/functionality/calendar_spread.py
  函数: async def construct_calendar_spread(symbol, buying_power_limit, option_type, min_short_expiration_days,
  max_short_expiration_days, min_long_expiration_days, max_long_expiration_days, strike_range, ...)

## output

write the enhanced prd to specs/prd_v12_ai_enhanced.md
