---
description: PRD for Stock Acquisition CSP Engine MCP Server Prompt
---

# Stock Acquisition CSP Engine MCP Server Prompt

Create a stock acquisition CSP Engine MCP Server Prompt that can be used to:
- BUILD STOCK POSITIONS as the PRIMARY goal
- ACQUIRE quality shares at DISCOUNT prices through assignment
- WELCOME stock assignment - ownership is desired outcome
- Long-term equity accumulation (21-60+ days typical)
- Focus on in-the-money/at-the-money puts with higher Delta (0.30-0.50)
- Lower annualized returns (15-35%) but effective stock acquisition

## Implementation Instruction

- Pls refer to its reference implementation at /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/stock_acquisition_csp_engine.md
- Double check the reference implementation for correctness and logics. You may refer tradier api docs at /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/tradier_api_docs.md.
- You may refer and MIRROR income generation csp engine MCP Server Prompt at /Users/szou/Python/Playground/TradingAgentMCP/src/mcp_server/prompts/income_generation_csp_prompt.py for implementing a MCP Server Prompt.
- We don't have to implement TaskProgressTracker feature
- Note that we have implemented cash secured sell put mcp server tool. When set process_type to "income", we are hoping for using this strategy for buying the stock with discount. Since the reference implementation doesn't have this knowledge, we shall use discretion when refering to refernce implementation and consider our cash secured sell put mcp server tool.
- There maybe utilies refered or used by the refernce implementation, and we could retain them when needed

## output

write the enhanced prd to specs/prd_v10_ai_enhanced.md
