# Stock History Data MCP Server Tool

## Purpose

Create a Stock History Data MCP Server Tool to retrieve stock history data given a ticker and a date range.

## Provider

- We use Tradier and Tradier API to obtain real, non-mock, and real-time, non-mock, data.
- The Tradier API requires an access token, which could be obtained from .env

## Instructions

- a date range could be defined by start_date and end_date, with date format of "YYYY-MM-DD", or past days/months with format like "30d" or "3m"
- the retrieved data will be stored as a csv file in the "./data" directory with proper name like "<symbol>_2022-01-01_2022-02-01_<timestamp>.csv"
- it will return the path to the saved csv file, as well as up to top 30 records.
- Note, in order to preserve the proper usage of context for llm, we don't want to dump all the data to the context (or output/stdout from the mcp server tool).

## Refeence Implementation

- Let's create a function to retrieve stock history data at src/stock/history_data.py, pls refer to its reference implementation at /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/stock_history_data.md.md
- Double check the reference implementation for correctness and logics. You may refer tradier api docs at /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/tradier_api_docs.md.
- There may be functions in tradier reference implementation not used for this v4 prd, but we could still implement them for forseeable future use or future versions of PRD.

write the enhanced prd to specs/prd_v4_ai_enhanced.md
