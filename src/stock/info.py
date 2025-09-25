"""Stock information processing and formatting."""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from src.provider.tradier.client import TradierClient, TradierQuote
from src.utils.time import get_timezone_time
from src.market.hours import get_market_status


@dataclass
class StockInfo:
    """Standardized stock information data structure."""
    
    # Basic information
    symbol: str
    company_name: str
    close_price: float
    close_time: str
    
    # Price movement
    change_amount: float
    change_percentage: float
    high_price: float
    low_price: float
    open_price: float
    prev_close: float
    
    # Trading data
    volume: int
    turnover_amount: Optional[float] = None
    turnover_rate: Optional[float] = None
    
    # Valuation metrics
    pe_ratio_ttm: Optional[float] = None
    pe_ratio_static: Optional[float] = None
    pb_ratio: Optional[float] = None
    market_cap: Optional[float] = None
    total_shares: Optional[float] = None
    float_market_cap: Optional[float] = None
    float_shares: Optional[float] = None
    
    # Technical indicators
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    historical_high: Optional[float] = None
    historical_low: Optional[float] = None
    beta: Optional[float] = None
    amplitude: Optional[float] = None
    average_price: Optional[float] = None
    lot_size: int = 1
    
    # Pre-market data
    premarket_price: Optional[float] = None
    premarket_change: Optional[float] = None
    premarket_change_percentage: Optional[float] = None
    premarket_time: Optional[str] = None
    
    # Additional context
    market_status: Optional[str] = None
    data_timestamp: Optional[str] = None


class StockInfoProcessor:
    """Stock information processor with business logic and formatting."""
    
    def __init__(self):
        """Initialize processor with Tradier client."""
        self.tradier_client = TradierClient()
    
    async def get_stock_info(self, symbol: str) -> StockInfo:
        """Get complete stock information for a symbol.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            StockInfo object with comprehensive data
            
        Raises:
            Exception: If unable to fetch stock data
        """
        try:
            # 1. Get basic quote data
            quotes = self.tradier_client.get_quotes([symbol.upper()])
            if not quotes:
                raise ValueError(f"No data found for symbol: {symbol}")
            
            quote = quotes[0]
            
            # 2. Get company information (optional, may fail)
            company_info = self.tradier_client.get_company_info(symbol.upper())
            
            # 3. Get financial ratios (optional, may fail)
            ratios = self.tradier_client.get_ratios(symbol.upper())
            
            # 4. Get 52-week high/low from quote data (preferred) or historical data (fallback)
            week_52_high = quote.week_52_high
            week_52_low = quote.week_52_low
            
            # Fallback to historical data if not available in quote
            if week_52_high is None or week_52_low is None:
                hist_high, hist_low = self._get_52_week_range(symbol.upper())
                week_52_high = week_52_high or hist_high
                week_52_low = week_52_low or hist_low
            
            # 5. Get current market status
            eastern_time = get_timezone_time("US/Eastern")
            market_status = get_market_status(eastern_time)
            
            # 6. Build standardized data structure
            stock_info = self._build_stock_info(quote, company_info, ratios, market_status, eastern_time, week_52_high, week_52_low)
            
            return stock_info
            
        except Exception as e:
            raise Exception(f"Failed to fetch stock info for {symbol}: {str(e)}")
    
    def _get_52_week_range(self, symbol: str) -> tuple[Optional[float], Optional[float]]:
        """Get 52-week high and low from historical data.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Tuple of (52_week_high, 52_week_low) or (None, None) if failed
        """
        try:
            # Calculate date range for 52 weeks (365 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            historical_data = self.tradier_client.get_historical_data(
                symbol,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            if not historical_data:
                return None, None
            
            # Extract highs and lows from historical data
            highs = [day.high for day in historical_data if day.high is not None]
            lows = [day.low for day in historical_data if day.low is not None]
            
            if not highs or not lows:
                return None, None
                
            return max(highs), min(lows)
            
        except Exception:
            # Silently fail - 52-week data is nice-to-have, not critical
            return None, None

    def _build_stock_info(
        self, 
        quote: TradierQuote, 
        company_info: Dict, 
        ratios: Dict,
        market_status: str,
        eastern_time: datetime,
        week_52_high: Optional[float] = None,
        week_52_low: Optional[float] = None
    ) -> StockInfo:
        """Build standardized stock info from API responses.
        
        Args:
            quote: Tradier quote data
            company_info: Company fundamental data
            ratios: Financial ratios data
            market_status: Current market status
            eastern_time: Current Eastern time
            
        Returns:
            StockInfo object
        """
        # Calculate amplitude
        amplitude = None
        if quote.high and quote.low and quote.prevclose and quote.prevclose != 0:
            amplitude = ((quote.high - quote.low) / quote.prevclose) * 100
        
        # Calculate average price
        average_price = None
        if quote.high and quote.low:
            average_price = (quote.high + quote.low) / 2
        
        # Extract company name and try to get additional info from company data
        company_name = quote.description or quote.symbol
        
        # Try to extract market cap from company info if available
        if company_info and "tables" in company_info:
            comp_tables = company_info["tables"]
            # Look for market cap in various possible locations
            pass  # company_info doesn't seem to have market cap either
        
        # Extract financial ratios from ratios data
        pe_ratio_ttm = None
        pe_ratio_static = None
        pb_ratio = None
        market_cap = None
        beta = None
        
        if ratios and "results" in ratios and len(ratios["results"]) > 0:
            # Ratios data structure is {'request': ..., 'results': [{'tables': {...}}]}
            first_result = ratios["results"][0]
            if "tables" in first_result:
                tables = first_result["tables"]
            
                # Note: valuation_ratios_restate table not available in current API response
                # We'll extract available financial metrics from operation_ratios_restate
                
                # Try to extract operation ratios and financial metrics
                if "operation_ratios_restate" in tables:
                    op_ratios = tables["operation_ratios_restate"]
                    if isinstance(op_ratios, list) and len(op_ratios) > 0:
                        # Try different period keys (most recent first)
                        recent_data = op_ratios[0]
                        for period_key in ["period_3m", "period_6m", "period_1y"]:
                            if period_key in recent_data:
                                period_data = recent_data[period_key]
                                # Extract available metrics (no PE/PB ratios available in this endpoint)
                                # Note: market_cap and beta not available in operation_ratios_restate
                                break
        
        # Determine price label based on market status
        price_time_label = self._get_price_time_label(market_status, eastern_time)
        
        # Build timestamp
        data_timestamp = datetime.now().isoformat()
        
        # Handle pre-market/after-hours data
        premarket_price = None
        premarket_change = None
        premarket_change_percentage = None
        premarket_time = None
        
        # In pre-market or after-hours, current price is the extended hours price
        # But also populate if we have different last vs prevclose (indicates movement)
        if quote.last and quote.prevclose and quote.last != quote.prevclose:
            if market_status in ["pre-market", "after-hours"]:
                premarket_price = quote.last
                premarket_change = quote.last - quote.prevclose
                premarket_change_percentage = (premarket_change / quote.prevclose) * 100
                premarket_time = eastern_time.strftime("%H:%M (美东)")
            # For regular market hours, if change is 0 but last != prevclose, use that data
            elif quote.change == 0 and quote.change_percentage == 0:
                # This might be delayed data, but still useful
                quote.change = quote.last - quote.prevclose
                quote.change_percentage = (quote.change / quote.prevclose) * 100
        
        # Calculate turnover amount if we have price and volume
        turnover_amount = None
        if quote.last and quote.volume:
            turnover_amount = quote.last * quote.volume
        
        # Use 52-week high/low from quote data (preferred) or historical data (fallback)
        
        return StockInfo(
            # Basic information
            symbol=quote.symbol,
            company_name=company_name,
            close_price=quote.last or 0.0,
            close_time=price_time_label,
            
            # Price movement
            change_amount=quote.change or 0.0,
            change_percentage=quote.change_percentage or 0.0,
            high_price=quote.high or quote.last or 0.0,  # Use last if high not available
            low_price=quote.low or quote.last or 0.0,   # Use last if low not available  
            open_price=quote.open or quote.prevclose or 0.0,  # Use prevclose if open not available
            prev_close=quote.prevclose or 0.0,
            
            # Trading data
            volume=quote.volume or 0,
            turnover_amount=turnover_amount,
            # Note: turnover_rate needs float shares to calculate
            
            # Valuation metrics (from ratios API)
            pe_ratio_ttm=pe_ratio_ttm,
            pe_ratio_static=pe_ratio_static,
            pb_ratio=pb_ratio,
            market_cap=market_cap,
            
            # Technical indicators
            week_52_high=week_52_high,
            week_52_low=week_52_low,
            amplitude=amplitude,
            average_price=average_price,
            beta=beta,
            lot_size=1,  # US stocks default to 1 share per lot
            
            # Pre-market/after-hours data
            premarket_price=premarket_price,
            premarket_change=premarket_change,
            premarket_change_percentage=premarket_change_percentage,
            premarket_time=premarket_time,
            
            # Context
            market_status=market_status,
            data_timestamp=data_timestamp
        )
    
    def _get_price_time_label(self, market_status: str, eastern_time: datetime) -> str:
        """Generate appropriate price time label based on market status.
        
        Args:
            market_status: Current market status
            eastern_time: Current Eastern time
            
        Returns:
            Formatted time label string
        """
        time_str = eastern_time.strftime("%m/%d %H:%M:%S")
        
        if market_status == "market":
            return f"{time_str} (美东实时)"
        elif market_status == "pre-market":
            return f"{time_str} (美东盘前)"
        elif market_status == "after-hours":
            return f"{time_str} (美东盘后)"
        else:
            return f"{time_str} (美东收盘)"
    
    def format_stock_info(self, stock_info: StockInfo) -> str:
        """Format stock information as user-friendly Chinese text.
        
        Args:
            stock_info: StockInfo object to format
            
        Returns:
            Formatted Chinese text string
        """
        # Company display name
        company_display = f"{stock_info.symbol} ({stock_info.company_name})"
        
        # Formatting helper functions
        def format_currency(value: Optional[float], prefix: str = "$") -> str:
            """Format currency value."""
            if value is None:
                return "N/A"
            return f"{prefix}{value:,.3f}"
        
        def format_percentage(value: Optional[float]) -> str:
            """Format percentage value."""
            if value is None:
                return "N/A"
            sign = "+" if value >= 0 else ""
            return f"{sign}{value:.2f}%"
        
        def format_large_number(value: Optional[float], suffix: str = "") -> str:
            """Format large numbers with Chinese units."""
            if value is None:
                return "N/A"
            
            abs_value = abs(value)
            if abs_value >= 1e12:
                return f"{value/1e12:.2f}万亿{suffix}"
            elif abs_value >= 1e8:
                return f"{value/1e8:.2f}亿{suffix}"
            elif abs_value >= 1e4:
                return f"{value/1e4:.2f}万{suffix}"
            else:
                return f"{value:,.0f}{suffix}"
        
        def format_change_with_sign(value: Optional[float]) -> str:
            """Format change amount with appropriate sign."""
            if value is None:
                return "N/A"
            if value >= 0:
                return f"+{format_currency(value)[1:]}"  # Remove $ and add +
            else:
                return format_currency(value)
        
        # Build the formatted output
        output = f"""## {company_display} - 关键信息

**基础信息**
- 股票代码: {stock_info.symbol}
- 收盘价: {format_currency(stock_info.close_price)}
- 收盘时间: {stock_info.close_time}

**价格变动**
- 涨跌额: {format_change_with_sign(stock_info.change_amount)}
- 涨跌幅: {format_percentage(stock_info.change_percentage)}
- 最高价: {format_currency(stock_info.high_price)}
- 最低价: {format_currency(stock_info.low_price)}
- 今开: {format_currency(stock_info.open_price)}
- 昨收: {format_currency(stock_info.prev_close)}

**交易数据**
- 成交量: {format_large_number(stock_info.volume, "股")}"""
        
        # Add turnover data if available
        if stock_info.turnover_amount:
            output += f"\n- 成交额: {format_large_number(stock_info.turnover_amount)}"
        if stock_info.turnover_rate:
            output += f"\n- 换手率: {stock_info.turnover_rate:.2f}%"
        
        # Add valuation metrics if available
        valuation_items = []
        if stock_info.pe_ratio_ttm:
            valuation_items.append(f"- 市盈率TTM: {stock_info.pe_ratio_ttm:.2f}")
        if stock_info.pe_ratio_static:
            valuation_items.append(f"- 市盈率(静): {stock_info.pe_ratio_static:.2f}")
        if stock_info.pb_ratio:
            valuation_items.append(f"- 市净率: {stock_info.pb_ratio:.2f}")
        if stock_info.market_cap:
            valuation_items.append(f"- 总市值: {format_large_number(stock_info.market_cap)}")
        if stock_info.total_shares:
            valuation_items.append(f"- 总股本: {format_large_number(stock_info.total_shares, '亿')}")
        if stock_info.float_market_cap:
            valuation_items.append(f"- 流通值: {format_large_number(stock_info.float_market_cap)}")
        if stock_info.float_shares:
            valuation_items.append(f"- 流通股: {format_large_number(stock_info.float_shares, '亿')}")
        
        if valuation_items:
            output += "\n\n**估值指标**\n" + "\n".join(valuation_items)
        
        # Add technical indicators
        output += "\n\n**技术指标**"
        if stock_info.week_52_high:
            output += f"\n- 52周最高: {format_currency(stock_info.week_52_high)}"
        if stock_info.week_52_low:
            output += f"\n- 52周最低: {format_currency(stock_info.week_52_low)}"
        if stock_info.historical_high:
            output += f"\n- 历史最高: {format_currency(stock_info.historical_high)}"
        if stock_info.historical_low:
            output += f"\n- 历史最低: {format_currency(stock_info.historical_low)}"
        if stock_info.beta:
            output += f"\n- Beta系数: {stock_info.beta:.3f}"
        if stock_info.amplitude:
            output += f"\n- 振幅: {stock_info.amplitude:.2f}%"
        if stock_info.average_price:
            output += f"\n- 平均价: {format_currency(stock_info.average_price)}"
        output += f"\n- 每手: {stock_info.lot_size}股"
        
        # Add pre-market data if available
        if stock_info.premarket_price:
            output += f"\n\n**盘前交易**"
            output += f"\n- 盘前价格: {format_currency(stock_info.premarket_price)}"
            if stock_info.premarket_change:
                premarket_change_str = format_change_with_sign(stock_info.premarket_change)
                premarket_pct_str = format_percentage(stock_info.premarket_change_percentage)
                output += f"\n- 盘前变动: {premarket_change_str} ({premarket_pct_str})"
            if stock_info.premarket_time:
                output += f"\n- 盘前时间: {stock_info.premarket_time}"
        
        return output
    
    def get_raw_data_dict(self, stock_info: StockInfo) -> Dict[str, Any]:
        """Convert StockInfo to structured dictionary for API responses.
        
        Args:
            stock_info: StockInfo object
            
        Returns:
            Dictionary with structured stock data
        """
        return {
            "symbol": stock_info.symbol,
            "company_name": stock_info.company_name,
            "price_data": {
                "close_price": stock_info.close_price,
                "change_amount": stock_info.change_amount,
                "change_percentage": stock_info.change_percentage,
                "high_price": stock_info.high_price,
                "low_price": stock_info.low_price,
                "open_price": stock_info.open_price,
                "prev_close": stock_info.prev_close
            },
            "trading_data": {
                "volume": stock_info.volume,
                "turnover_amount": stock_info.turnover_amount,
                "turnover_rate": stock_info.turnover_rate
            },
            "valuation_metrics": {
                "pe_ratio_ttm": stock_info.pe_ratio_ttm,
                "pe_ratio_static": stock_info.pe_ratio_static,
                "pb_ratio": stock_info.pb_ratio,
                "market_cap": stock_info.market_cap,
                "total_shares": stock_info.total_shares,
                "float_market_cap": stock_info.float_market_cap,
                "float_shares": stock_info.float_shares
            },
            "technical_indicators": {
                "week_52_high": stock_info.week_52_high,
                "week_52_low": stock_info.week_52_low,
                "historical_high": stock_info.historical_high,
                "historical_low": stock_info.historical_low,
                "beta": stock_info.beta,
                "amplitude": stock_info.amplitude,
                "average_price": stock_info.average_price,
                "lot_size": stock_info.lot_size
            },
            "premarket_data": {
                "premarket_price": stock_info.premarket_price,
                "premarket_change": stock_info.premarket_change,
                "premarket_change_percentage": stock_info.premarket_change_percentage,
                "premarket_time": stock_info.premarket_time
            },
            "context": {
                "market_status": stock_info.market_status,
                "close_time": stock_info.close_time,
                "data_timestamp": stock_info.data_timestamp
            }
        }