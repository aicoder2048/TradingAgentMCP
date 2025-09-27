---
description: option assignment probability mcp server tool
---

# option assignment probability mcp server tool

Create an option assignment probablity mcp server tool for calculate put and call option assignment probability.


## Instructions

- We use Tradier and Tradier API to obtain real, non-mock, and real-time, non-mock, data.
- The Tradier API requires an access token, which could be obtained from .env

## workflow
1. Review and refer reference implement at /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/calculate_assignment_probability.md
2. Double check the reference implementation for correctness and logics. You may refer tradier api docs at /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/tradier_api_docs.md.
3. There may be functions in tradier reference implementation not used for this v4 prd, but we could still implement them for forseeable future use or future versions of PRD.
4. Since we have explictly created this tool or function to calculate assignment probability, make sure the it is being actually used in other mcp server tool, such as sell put option and sell covered call option, because they previously just use delta to approximate assignment probability .

## Output
write the enhanced prd to specs/prd_v8_ai_enhanced.md
