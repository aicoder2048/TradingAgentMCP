我们要改进一下 智能到期日优化器这个MCP SERVER TOOL /Users/szou/Python/Playground/TradingAgentMCP/src/mcp_server/tools/optimal_expiration_selector_tool.py.

目前的版本实现有不少是硬编码和相对主观的设置. 请参考 /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/cc_genui_stock_specific_optimization_fix_20250929_030957_PST.html, 改进智能到期优化器的实现方法, 力求为每个股票, 基于其客观特征获得独特的优化结果, 系统数据驱动, 避免硬编码.

相关文件包括当不限于:
- /Users/szou/Python/Playground/TradingAgentMCP/src/mcp_server/server.py
- /Users/szou/Python/Playground/TradingAgentMCP/src/mcp_server/tools/optimal_expiration_selector_tool.py
- /Users/szou/Python/Playground/TradingAgentMCP/src/mcp_server/tools/expiration_optimizer.py
- /Users/szou/Python/Playground/TradingAgentMCP/src/mcp_server/tools/cash_secured_put_strategy_tool.py
- /Users/szou/Python/Playground/TradingAgentMCP/src/mcp_server/tools/covered_call_strategy_tool.py
- /Users/szou/Python/Playground/TradingAgentMCP/src/mcp_server/tools/option_expirations_tool.py
- /Users/szou/Python/Playground/TradingAgentMCP/src/mcp_server/prompts/income_generation_csp_prompt.py
- /Users/szou/Python/Playground/TradingAgentMCP/src/mcp_server/prompts/stock_acquisition_csp_prompt.py

Write an enhanced version of PRD to /Users/szou/Python/Playground/TradingAgentMCP/specs/prd_v11_ai_enhanced.md
