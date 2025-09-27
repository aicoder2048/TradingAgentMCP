# Options Chains MCP Server Tool

## Purpose

1. Create Options Chains MCP Server Tool to get the options chains given the stock symbol, expiration date, option_type, greeks=true.
2. Create a function to retreive Options Expiration Dates given the stock symbol.
3. Create a function to retreive Option Strikes given the stock symbol and expiration date.

## Instruction

- We create Options Chains MCP Server Tool and the options chains data retrieved is to be saved into a csv file into ./data dir, with name of <stock_symbol>_<option_type>_<expiration_date>_<timestamp>.csv. Note, the greeks are by default included
- Options Chains MCP Server Tool will return the full path to the saved csv file, as well as 20 OTM and 20 ITM options, as well as ATM option as well if any.
- We create the function to get options expiration dates in src/option/option_expiration_dates.py, and we don't yet want to make it a mcp server tool other than than an only local function.
- We create the function to get option strikes in src/option/option_strikes.py, and we don't yet want to make it a mcp server tool other than than an only local function.


## Reference Implementation

- Let's create a function to retrieve stock history data at src/option/options_chain.py, pls refer to its reference implementation at /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/options_chains.md
- Double check the reference implementation for correctness and logics. You may refer tradier api docs at /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/tradier_api_docs.md.
- There may be functions in tradier reference implementation not used for this v5 prd, but we could still implement them for forseeable future use or future versions of PRD.

write the enhanced prd to specs/prd_v5_ai_enhanced.md
