"""MCP tool for stock key information retrieval."""

from typing import Dict, Any
from datetime import datetime, timezone
from src.stock.info import StockInfoProcessor


async def get_stock_key_info(symbol: str) -> Dict[str, Any]:
    """
    Get comprehensive key information for a stock symbol.
    
    This MCP tool retrieves detailed stock information including:
    - Basic price and trading data from real-time market feeds
    - Valuation metrics (PE ratios, market cap, etc.)
    - Technical indicators (52-week range, beta, amplitude)
    - Pre-market data when available
    - Market context and timing information
    
    The information is formatted in both human-readable Chinese format
    and structured data for programmatic use.
    
    Args:
        symbol: Stock ticker symbol (e.g., "TSLA", "AAPL", "NVDA")
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating if request succeeded
        - symbol: The requested stock symbol (normalized to uppercase)
        - formatted_info: Human-readable Chinese formatted stock information
        - raw_data: Structured data object for programmatic use
        - timestamp: UTC timestamp of the response
        - error: Error message (only present if failed)
        
    Examples:
        >>> result = await get_stock_key_info("TSLA")
        >>> print(result["formatted_info"])
        ## TSLA (特斯拉) - 关键信息
        
        **基础信息**
        - 股票代码: TSLA
        - 收盘价: $442.790
        - 收盘时间: 09/25 16:00:00 (美东收盘)
        ...
        
        >>> print(result["raw_data"]["price_data"]["close_price"])
        442.79
    """
    try:
        # Initialize the stock information processor
        processor = StockInfoProcessor()
        
        # Get comprehensive stock information
        stock_info = await processor.get_stock_info(symbol.upper())
        
        # Format information for human readability
        formatted_info = processor.format_stock_info(stock_info)
        
        # Get structured data for programmatic use
        raw_data = processor.get_raw_data_dict(stock_info)
        
        # Generate response timestamp
        response_timestamp = datetime.now(timezone.utc).isoformat()
        
        return {
            "success": True,
            "symbol": stock_info.symbol,
            "formatted_info": formatted_info,
            "raw_data": raw_data,
            "timestamp": response_timestamp
        }
        
    except Exception as e:
        # Handle any errors gracefully
        error_timestamp = datetime.now(timezone.utc).isoformat()
        
        return {
            "success": False,
            "symbol": symbol.upper(),
            "error": str(e),
            "timestamp": error_timestamp,
            "formatted_info": f"❌ 无法获取 {symbol.upper()} 的股票信息\n\n错误: {str(e)}",
            "raw_data": None
        }