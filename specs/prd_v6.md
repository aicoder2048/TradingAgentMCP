---
description: Cash-secured sell put strategy MCP Server Tool
argument-hint: [symbol] [purpose type] [duration]
allowed-tools: all tools
---

# Cash Secured Sell Put Strategy

Create Cash Secured Sell Put Strategy MCP Server Tool to creae the requested cash secured sell put strategy for the given symbol, purpose type and duration

## Variables
SYMBOL: $1
PURPOSE_TYPE: $2, defautl to "income"
DURATION: $3, default to "1w", which typically means next Friday.

## Instructions
- We use Tradier and Tradier API to obtain real, non-mock, and real-time, non-mock, data.
- The Tradier API requires an access token, which could be obtained from .env
- `PURPOSE_TYPE` could be either "income" or "discount", where "income" means to use the option to generate premium as income (don't intend to be assigned with the underlying security), and "discount" means to use the option to generate premium as discount but as a tool to buy the underlying security at a discount (therefore, it's acceptable to be assigned with the underlying security).
- if `PURPOSE_TYPE` is "income", then we will construct the option by choosing the **STRIKE** price lower than the last closing price or current market price with Delta or likelyhood to be assigned btw 10-30%; if `PURPOSE_TYPE` is "discount", then we will construct the option by choosing the **STRIKE** price lower than but closer to the last closing price or current market price with Delta or likelyhood to be assigned btw 30-50%; Sometimes for "discount" purpose type, we may even let the **STRIKE** go beyond last closing price or current market price with much aggressive Delta or likelyhood to be assigned, in order to secure the opportunity to be able to buy the underlying security at a discount.
- `DURATION` could be either "1w", "2w", "1m", "3m", "6m", "1y" where "1w" means 1 week, "1m" means 1 month, "3m" means 3 months, "6m" means 6 months, "1y" means 1 year.
- We create the function to get cash-secured sell put option strategy in mcp server tool python file in this directory: src/mcp_server/tools. Refer to its reference implementation at /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/wheel_strategy.md
- Double check the reference implementation for correctness and logics. You may refer tradier api docs at /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/tradier_api_docs.md.

## Workflow
1. Get expiration dates according to `DURATION`. "1w" means the next incoming Friday beyond 1 week, and so for "2w" etc.
2. Analyze the options chains data to find the strike price with Delta or likelyhood to be assigned between 10-30% for "income" purpose type, and between 30-50%, and even aggressive 60-70% for "discount" purpose type in a <analyze-option-loop>
3. Find and suggest three alternatives of the options: balanced, conservative, and aggressive, with analytics and reasoning.

<analyze-option-loop>
    ...
</analyze-option-loop>

## Suggested Sell Put Option Strategies
- The MCP Server Tool offers professional suggestions for the options, including description.
- For each suggestion, provide extended explainations like P&L analysis and a reasoning for the choice.
- Provide a text block of the order in the format of trading desk convention at top-tier firms like JP Morgan.

## Write the enhanced prd to specs/prd_v6_ai_enhanced.md
