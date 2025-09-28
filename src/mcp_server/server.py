from fastmcp import FastMCP
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Union
from .tools.hello_tool import hello
from .tools.get_market_time_tool import get_market_time_status
from .tools.stock_key_info_tool import get_stock_key_info
from .tools.get_earnings_calendar_tool import get_earnings_calendar_tool
from .tools.get_stock_history_tool import get_stock_history_tool
from .tools.get_options_chain_tool import options_chain_tool
from .tools.cash_secured_put_strategy_tool import cash_secured_put_strategy_tool
from .tools.covered_call_strategy_tool import covered_call_strategy_tool
from .tools.option_assignment_probability_tool import option_assignment_probability_tool
from .tools.option_expirations_tool import (
    get_option_expirations_tool,
    get_next_expiration_tool,
    get_weekly_expirations_tool,
    get_monthly_expirations_tool,
    filter_expirations_by_days_tool
)
from .prompts.hello_prompt import call_hello_multiple
from .prompts.income_generation_csp_prompt import income_generation_csp_engine
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

    @mcp.tool()
    async def get_option_expirations_tool_mcp(
        symbol: str,
        min_days: int = None,
        max_days: int = None
    ) -> Dict[str, Any]:
        """
        获取期权到期日列表，支持按天数过滤。
        
        这是获取期权到期日的核心工具，可以替代手动计算到期日期。
        特别适合在调用 options_chain_tool 之前确定正确的到期日。
        
        Args:
            symbol: 股票代码 (例如: "AAPL", "TSLA", "NVDA")
            min_days: 最小到期天数过滤 (可选)
            max_days: 最大到期天数过滤 (可选)
        
        Returns:
            包含到期日信息列表和统计摘要的字典
        """
        return await get_option_expirations_tool(symbol, min_days, max_days)

    @mcp.tool()
    async def get_next_expiration_tool_mcp(symbol: str) -> Dict[str, Any]:
        """
        获取下一个最近的期权到期日。
        
        快速获取最近可用的期权到期日，适合需要立即执行策略的场景。
        
        Args:
            symbol: 股票代码 (例如: "AAPL", "TSLA", "NVDA")
        
        Returns:
            包含下一个到期日信息的字典
        """
        return await get_next_expiration_tool(symbol)

    @mcp.tool()
    async def get_weekly_expirations_tool_mcp(
        symbol: str,
        weeks: int = 4
    ) -> Dict[str, Any]:
        """
        获取未来几周的周期权到期日。
        
        专门用于短期策略，如7-28天的现金担保PUT或备兑看涨策略。
        周期权通常流动性较好，适合频繁交易。
        
        Args:
            symbol: 股票代码 (例如: "AAPL", "TSLA", "NVDA")
            weeks: 获取未来几周的到期日 (默认: 4)
        
        Returns:
            包含周期权到期日列表的字典
        """
        return await get_weekly_expirations_tool(symbol, weeks)

    @mcp.tool()
    async def get_monthly_expirations_tool_mcp(
        symbol: str,
        months: int = 6
    ) -> Dict[str, Any]:
        """
        获取未来几个月的月期权到期日。
        
        适用于中长期策略，月期权通常流动性最佳，执行价格选择较多。
        
        Args:
            symbol: 股票代码 (例如: "AAPL", "TSLA", "NVDA")
            months: 获取未来几个月的到期日 (默认: 6)
        
        Returns:
            包含月期权到期日列表的字典
        """
        return await get_monthly_expirations_tool(symbol, months)

    @mcp.tool()
    async def filter_expirations_by_days_tool_mcp(
        symbol: str,
        min_days: int = 7,
        max_days: int = 28
    ) -> Dict[str, Any]:
        """
        获取指定天数范围内的期权到期日。
        
        针对收入生成策略优化的工具，默认7-28天窗口非常适合
        高频收入策略。这个工具可以替代手动计算到期日的方式。
        
        Args:
            symbol: 股票代码 (例如: "AAPL", "TSLA", "NVDA")
            min_days: 最小天数 (默认: 7)
            max_days: 最大天数 (默认: 28)
        
        Returns:
            包含过滤后期权到期日和策略建议的字典
        """
        return await filter_expirations_by_days_tool(symbol, min_days, max_days)

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

    @mcp.prompt()
    async def income_generation_csp_engine_prompt(
        tickers: str,  # 简化：只接受字符串，内部处理所有格式
        cash_usd: Union[float, int, str],  # 修复: 支持多种数值类型
        min_days: int = 7,
        max_days: int = 28,
        target_apy_pct: Union[float, int] = 50,  # 修复: 支持整数和浮点数
        min_winrate_pct: Union[float, int] = 70,  # 修复: 支持整数和浮点数
        confidence_pct: Union[float, int] = 90,   # 修复: 支持整数和浮点数
    ) -> str:
        """
        Generate income-focused Cash-Secured Put strategy execution prompt.

        Creates a comprehensive execution plan for high-yield, low-assignment-risk 
        options strategies optimized for premium collection rather than stock acquisition.
        Targets ≥50% annualized returns with Delta range 0.10-0.30.

        Args:
            tickers: Target symbols - supports multiple formats:
                - JSON string: "[\"TSLA\", \"GOOG\", \"META\"]" or "['TSLA','GOOG','META']"
                - Space separated: "TSLA GOOG META"
                - Comma separated: "TSLA,GOOG,META"
                - Single ticker: "TSLA"
                (default: [\"SPY\", \"QQQ\", \"AAPL\", \"MSFT\", \"NVDA\"])
            cash_usd: Available capital for strategies (accepts int, float, or string)
            min_days: Minimum days to expiration (default: 7)
            max_days: Maximum days to expiration (default: 28)
            target_apy_pct: Target annualized percentage yield (default: 50%)
            min_winrate_pct: Minimum target win rate (default: 70%)
            confidence_pct: Statistical confidence level (default: 90%)

        Returns:
            Comprehensive execution prompt string with tool call sequences,
            screening criteria, and professional risk management protocols
        """
        # DEBUG: 记录MCP入口参数
        try:
            from .utils.debug_logger import debug_mcp_entry
            debug_mcp_entry(
                tickers,
                cash_usd=cash_usd,
                min_days=min_days,
                max_days=max_days,
                target_apy_pct=target_apy_pct,
                min_winrate_pct=min_winrate_pct,
                confidence_pct=confidence_pct
            )
        except ImportError:
            # 如果debug模块不存在，静默失败
            pass
        except Exception as e:
            print(f"DEBUG logging failed: {e}")
        
        # 修复: 统一转换所有数值参数为正确类型
        try:
            cash_usd = float(cash_usd)
            target_apy_pct = float(target_apy_pct)
            min_winrate_pct = float(min_winrate_pct)
            confidence_pct = float(confidence_pct)
        except (ValueError, TypeError) as e:
            raise ValueError(f"参数类型转换失败: {e}")
        
        return await income_generation_csp_engine(
            tickers=tickers,  # 现在直接传递字符串
            cash_usd=cash_usd,
            min_days=min_days,
            max_days=max_days,
            target_apy_pct=target_apy_pct,
            min_winrate_pct=min_winrate_pct,
            confidence_pct=confidence_pct
        )

    return mcp
