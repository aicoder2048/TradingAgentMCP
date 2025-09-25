from fastmcp import FastMCP
from contextlib import asynccontextmanager
from typing import Dict, Any
from .tools.hello_tool import hello
from .tools.get_market_time_tool import get_market_time_status
from .tools.stock_key_info_tool import get_stock_key_info
from .tools.get_earnings_calendar_tool import get_earnings_calendar_tool
from .tools.get_stock_history_tool import get_stock_history_tool
from .tools.get_options_chain_tool import options_chain_tool
from .prompts.hello_prompt import call_hello_multiple
from .config.settings import settings

@asynccontextmanager
async def lifespan(server: FastMCP):
    """Server lifecycle management."""
    print(f"🚀 Starting {settings.server_name} server...")
    yield
    print(f"👋 Shutting down {settings.server_name} server...")

def create_server() -> FastMCP:
    """Create and configure the MCP server."""
    mcp = FastMCP(
        name=settings.server_name,
        version=settings.version,
        lifespan=lifespan
    )

    @mcp.tool()
    async def hello_tool(name: str) -> Dict[str, Any]:
        """
        Say hello to someone.

        Args:
            name: The name of the person to greet

        Returns:
            A greeting response with status and message
        """
        return await hello(name)

    @mcp.tool()
    async def get_market_time_tool() -> Dict[str, Any]:
        """
        Get current US market time and trading status.

        Returns comprehensive market timing information including Eastern time,
        market session status, and trading day information.

        Returns:
            Dictionary containing market time and status information
        """
        return await get_market_time_status()

    @mcp.tool()
    async def stock_info_tool(symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive key information for a stock symbol.
        
        Retrieves detailed stock information including price data, trading volume,
        valuation metrics, and technical indicators using real-time Tradier API data.
        The information is presented in both human-readable Chinese format and
        structured data format for programmatic use.
        
        Args:
            symbol: Stock ticker symbol (e.g., "TSLA", "AAPL", "NVDA")
            
        Returns:
            Comprehensive stock information with formatted display and raw data
        """
        return await get_stock_key_info(symbol)

    @mcp.tool()
    async def earnings_calendar_tool(symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive earnings calendar information for a stock symbol.
        
        Retrieves detailed earnings calendar data including upcoming and historical
        earnings events, announcement dates, and corporate calendar information
        using real-time Tradier API data. Essential for trading decisions and
        event-driven investment strategies.
        
        Args:
            symbol: Stock ticker symbol (e.g., "TSLA", "AAPL", "NVDA")
            
        Returns:
            Comprehensive earnings calendar information with events, dates, and metadata
        """
        return await get_earnings_calendar_tool(symbol)

    @mcp.tool()
    async def stock_history_tool(
        symbol: str,
        start_date: str = None,
        end_date: str = None, 
        date_range: str = None,
        interval: str = "daily",
        include_indicators: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive stock history data with technical indicators and CSV export.
        
        Retrieves historical stock price data and performs comprehensive technical analysis.
        Data is automatically saved to CSV files for further analysis while returning
        context-optimized summaries and preview records.
        
        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "TSLA", "NVDA")
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            date_range: Relative range like "30d", "3m", "1y" (optional)
            interval: Data interval - "daily", "weekly", "monthly" (default: "daily")
            include_indicators: Calculate technical indicators (default: True)
            
        Returns:
            Dictionary with historical data, technical analysis, CSV path, and summaries
        """
        return await get_stock_history_tool(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            date_range=date_range,
            interval=interval,
            include_indicators=include_indicators
        )

    @mcp.tool()
    async def options_chain_tool_mcp(
        symbol: str,
        expiration: str,
        option_type: str = "both",
        include_greeks: bool = True
    ) -> Dict[str, Any]:
        """
        获取期权链数据和分析。
        
        提供全面的期权链数据分析功能，包括 ITM/ATM/OTM 智能分类、
        希腊字母计算和 CSV 数据导出。返回最具流动性的
        10个价内期权 + 所有平值期权 + 10个价外期权（节省Context空间）。
        
        Args:
            symbol: 股票代码 (必需) - 例如 "AAPL", "TSLA", "NVDA"
            expiration: 到期日 YYYY-MM-DD (必需) - 例如 "2024-01-19"
            option_type: 期权类型 - "call", "put", 或 "both" (默认 "both")
            include_greeks: 是否包含希腊字母 (默认 True)
        
        Returns:
            包含期权数据、分类结果、CSV 文件路径和统计摘要的字典
        """
        return await options_chain_tool(
            symbol=symbol,
            expiration=expiration,
            option_type=option_type,
            include_greeks=include_greeks
        )

    @mcp.prompt()
    async def call_hello_multiple_prompt(name: str, times: int = 3) -> str:
        """
        Generate a prompt to call hello multiple times.

        Args:
            name: The name to use in the hello calls
            times: Number of times to call hello (default: 3)

        Returns:
            A formatted prompt string
        """
        return await call_hello_multiple(name, times)

    return mcp
