from fastmcp import FastMCP
from contextlib import asynccontextmanager
from typing import Dict, Any
from .tools.hello_tool import hello
from .tools.get_market_time_tool import get_market_time_status
from .tools.stock_key_info_tool import get_stock_key_info
from .tools.get_earnings_calendar_tool import get_earnings_calendar_tool
from .tools.get_stock_history_tool import get_stock_history_tool
from .tools.get_options_chain_tool import options_chain_tool
from .tools.cash_secured_put_strategy_tool import cash_secured_put_strategy_tool
from .tools.covered_call_strategy_tool import covered_call_strategy_tool
from .tools.option_assignment_probability_tool import option_assignment_probability_tool
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

    @mcp.tool()
    async def cash_secured_put_strategy_tool_mcp(
        symbol: str,
        purpose_type: str = "income",
        duration: str = "1w",
        capital_limit: float = None,
        include_order_blocks: bool = True,
        min_premium: float = None,
        max_delta: float = None
    ) -> Dict[str, Any]:
        """
        现金保障看跌期权策略分析工具。
        
        分析期权链并生成基于Delta的现金保障看跌策略建议，支持收入和折扣购买双重目的。
        提供三种风险级别的专业建议和JP Morgan风格的交易订单块。
        
        Args:
            symbol: 股票代码 (必需) - 例如 "AAPL", "TSLA", "NVDA"
            purpose_type: 策略目的 - "income" (收入导向) 或 "discount" (折扣购买) (默认 "income")
            duration: 时间周期 - "1w", "2w", "1m", "3m", "6m", "1y" (默认 "1w")
            capital_limit: 资金限制 (可选) - 最大可用资金金额
            include_order_blocks: 是否包含专业订单块 (默认 True)
            min_premium: 最低权利金要求 (可选)
            max_delta: 最大Delta限制 (可选)
            
        Returns:
            包含策略分析、建议和订单块的完整结果
        """
        return await cash_secured_put_strategy_tool(
            symbol=symbol,
            purpose_type=purpose_type,
            duration=duration,
            capital_limit=capital_limit,
            include_order_blocks=include_order_blocks,
            min_premium=min_premium,
            max_delta=max_delta
        )

    @mcp.tool()
    async def covered_call_strategy_tool_mcp(
        symbol: str,
        purpose_type: str = "income",
        duration: str = "1w",
        shares_owned: int = 100,
        avg_cost: float = None,
        min_premium: float = None,
        include_order_blocks: bool = True
    ) -> Dict[str, Any]:
        """
        Covered Call策略分析工具。
        
        为持有股票的投资者提供专业的covered call期权策略分析，
        生成收入导向和减仓导向的策略建议，包含风险评估和专业订单格式。
        
        Args:
            symbol: 股票代码 (必需) - 例如 "AAPL", "TSLA", "NVDA"
            purpose_type: 策略目的 - "income" (收入导向) 或 "exit" (减仓导向) (默认 "income")
            duration: 时间周期 - "1w", "2w", "1m", "3m", "6m", "1y" (默认 "1w")
            shares_owned: 持有股票数量 (必需，至少100股) (默认 100)
            avg_cost: 每股平均成本基础 (可选，用于税务分析)
            min_premium: 最低权利金门槛 (可选)
            include_order_blocks: 是否包含专业订单块 (默认 True)
            
        Returns:
            包含策略分析、三级风险建议和专业订单格式的完整结果
        """
        return await covered_call_strategy_tool(
            symbol=symbol,
            purpose_type=purpose_type,
            duration=duration,
            shares_owned=shares_owned,
            avg_cost=avg_cost,
            min_premium=min_premium,
            include_order_blocks=include_order_blocks
        )

    @mcp.tool()
    async def option_assignment_probability_tool_mcp(
        symbol: str,
        strike_price: float,
        expiration: str,
        option_type: str = "put",
        include_delta_comparison: bool = True,
        risk_free_rate: float = None
    ) -> Dict[str, Any]:
        """
        期权被行权概率计算专业工具。
        
        基于Black-Scholes模型提供精确的期权被行权概率计算，
        替代简单的Delta近似方法，提供详细的风险分析和市场上下文。
        
        Args:
            symbol: 股票代码 (必需) - 例如 "AAPL", "TSLA", "NVDA"
            strike_price: 期权行权价格 (必需) - 例如 145.0
            expiration: 到期日 YYYY-MM-DD 格式 (必需) - 例如 "2024-01-19"
            option_type: 期权类型 - "put" 或 "call" (默认 "put")
            include_delta_comparison: 是否包含Delta比较分析 (默认 True)
            risk_free_rate: 无风险利率 (可选，默认 4.8%)
            
        Returns:
            包含精确被行权概率、风险分析、Delta比较和市场上下文的完整分析
        """
        return await option_assignment_probability_tool(
            symbol=symbol,
            strike_price=strike_price,
            expiration=expiration,
            option_type=option_type,
            include_delta_comparison=include_delta_comparison,
            risk_free_rate=risk_free_rate
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
