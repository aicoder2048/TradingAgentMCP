---
description: PRD for Income Generation CSP Engine MCP Server Prompt
---

# Income Generation CSP Engine MCP Server Prompt

Create an Income Generation CSP Engine MCP Server Prompt that can be used to:
- Collect option premium as PRIMARY income source
- Generate high annualized returns (≥50%) from CSP strategies
- AVOID stock assignment - premium collection is the goal
- Quick turnover strategies (7-28 days typical)
- Focus on out-of-the-money puts with low Delta (0.10-0.30)


## Implementation Instruction

- Pls refer to its reference implementation at /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/income_generation_csp_engine.md
- Double check the reference implementation for correctness and logics. You may refer tradier api docs at /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/tradier_api_docs.md.
- You may refer hello MCP Server Prompt at /Users/szou/Python/Playground/TradingAgentMCP/src/mcp_server/prompts/hello_prompt.py for implementing a MCP Server Prompt.
- We don't have to implement TaskProgressTracker feature
- Note that we have implemented cash secured sell put mcp server tool. When set process_type to "income", we are hoping for using this strategy for income generation. Since the reference implementation doesn't have this knowledge, we shall use discretion when refering to refernce implementation and consider our cash secured sell put mcp server tool.
- There maybe utilies refered or used by the refernce implementation, and we could retain them when needed

## output

write the enhanced prd to specs/prd_v9_ai_enhanced.md
