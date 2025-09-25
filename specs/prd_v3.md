# Earnings Calendar MCP Server Tool

## Purpose

Create a Earnings Calendar MCP Server Tool for TradingAgentMCP MCP Server. This tool will take in a stock symbol and return the earnings calendar information for that stock.

## Provider

- We use Tradier and Tradier API to obtain real, non-mock, and real-time, non-mock, data.
- The Tradier API requires an access token, which could be obtained from .env

## Refeence Implementation
- Let's create earning calendar function at src/market/earnings_calendar.py, pls refer to its reference implementation at /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/earnings_date.md
- Double check the reference implementation for correctness and logics. You may refer tradier api docs at /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/tradier_api_docs.md.
- There may be functions in tradier reference implementation not used for this v3 prd, but we could still implement them for forseeable future use or future versions of PRD.

write the enhanced prd to specs/prd_v3_ai_enhanced.md
