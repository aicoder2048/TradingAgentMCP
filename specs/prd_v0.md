做一个最简单的mcp server, 包括:

- 一个简单的 mcp server tool: hello(name)
- 一个简单的 mcp server prompt: call hello(name) x times. The prompt string returned will allow claude code (which is mcp client) to call mcp server tool: hello (name) x times.
- We specifically use claude code to connect and run this mcp server.

有了这个mcp server 框架以后, 我们再添加更多的有意义的mcp server tools and mcp server prompts as needed.

reference the following docs as reference:
- quick-data-mcp mcp server tech reprot: /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/cc_genui_quick_data_mcp_tech_guide_20250922_114012.html
- docs for fastmcp: /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/fastmcp.md
- claude code doc for mcp: /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/claude_opus_mcp_breakdown.md
- uv doc for package management and python projects execution: /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/uv_running_python.md


write the enhanced prd to specs/prd_v1.md.
