# Stock Key Info MCP Server Tool Implementation Plan

## 项目概述

### 目标
为 TradingAgentMCP MCP Server 实现一个股票关键信息查询工具，该工具能够接收股票代码并返回全面的股票信息，包括基础价格、交易数据、估值指标和技术指标。

### 核心需求
- **输入**: 股票代码 (如 TSLA, AAPL)
- **输出**: 格式化的股票关键信息，包括中文标签和详细数据
- **数据源**: Tradier API (实时、非模拟数据)
- **集成**: 作为 MCP Server Tool 集成到现有系统

## 技术架构

### 架构设计原则
遵循现有项目的分层架构：
- `src/provider/tradier/` - Tradier API 数据提供商层
- `src/stock/` - 股票数据处理业务逻辑层  
- `src/market/` - 市场基础设施层 (现有，提供市场时段等信息)
- `src/mcp_server/tools/` - MCP 工具封装层

### 依赖关系
```
mcp_server/tools/stock_info_tool.py 
    ↓
stock/info.py ←→ market/hours.py (market status info)
    ↓
provider/tradier/client.py 
    ↓
Tradier API
```

### 模块职责说明
- **src/market/** (现有): 市场运行机制 - 交易时段、节假日、市场状态
- **src/stock/**: 个股数据处理 - 股票信息获取、格式化、模型定义  
- **src/provider/**: 数据提供商接口 - 可扩展支持多个数据源

## 详细实现方案

### 第一阶段：基础设施搭建

#### 1.1 创建 Tradier 客户端
**文件**: `src/provider/tradier/client.py`

基于参考实现创建完整的 Tradier API 客户端：

```python
import os
import requests
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class TradierQuote:
    # 基础价格信息
    symbol: str
    last: Optional[float]          # 最新价
    bid: Optional[float]           # 买价
    ask: Optional[float]           # 卖价
    open: Optional[float]          # 开盘价
    high: Optional[float]          # 最高价
    low: Optional[float]           # 最低价
    prevclose: Optional[float]     # 昨收价
    change: Optional[float]        # 涨跌额
    change_percentage: Optional[float]  # 涨跌幅
    
    # 交易数据
    volume: Optional[int]          # 成交量
    
    # 其他属性
    description: Optional[str] = None

class TradierClient:
    def __init__(self, access_token: str = None):
        self.access_token = access_token or os.getenv("TRADIER_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("TRADIER_ACCESS_TOKEN environment variable is required")
        
        self.base_url = "https://api.tradier.com"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        })
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None) -> Dict:
        """统一的 API 请求处理"""
        # 实现请求逻辑，包括错误处理
    
    def get_quotes(self, symbols: List[str]) -> List[TradierQuote]:
        """获取股票报价信息"""
        # 调用 /v1/markets/quotes API
    
    def get_company_info(self, symbol: str) -> Dict:
        """获取公司基本信息"""
        # 调用 /beta/markets/fundamentals/company API
    
    def get_ratios(self, symbol: str) -> Dict:
        """获取财务比率数据"""
        # 调用 /beta/markets/fundamentals/ratios API
    
    def search_securities(self, query: str) -> List[Dict]:
        """搜索证券信息"""
        # 调用 /v1/markets/search API
```

#### 1.2 配置环境变量
**文件**: `.env` (更新)

添加 Tradier API 配置：
```env
# Tradier API Configuration
TRADIER_ACCESS_TOKEN=your_access_token_here
TRADIER_BASE_URL=https://api.tradier.com
```

### 第二阶段：股票信息处理层

#### 2.1 创建股票信息处理模块
**文件**: `src/stock/__init__.py`
```python
"""Stock information processing module."""
```

**文件**: `src/stock/info.py`

核心业务逻辑，负责数据转换和格式化：

```python
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
from src.provider.tradier.client import TradierClient, TradierQuote

@dataclass
class StockInfo:
    """标准化的股票信息数据结构"""
    # 基础信息
    symbol: str
    company_name: str
    close_price: float
    close_time: str
    
    # 价格变动
    change_amount: float
    change_percentage: float
    high_price: float
    low_price: float
    open_price: float
    prev_close: float
    
    # 交易数据
    volume: int
    turnover_amount: Optional[float] = None
    turnover_rate: Optional[float] = None
    
    # 估值指标
    pe_ratio_ttm: Optional[float] = None
    pe_ratio_static: Optional[float] = None
    pb_ratio: Optional[float] = None
    market_cap: Optional[float] = None
    total_shares: Optional[float] = None
    float_market_cap: Optional[float] = None
    float_shares: Optional[float] = None
    
    # 技术指标
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    historical_high: Optional[float] = None
    historical_low: Optional[float] = None
    beta: Optional[float] = None
    amplitude: Optional[float] = None
    average_price: Optional[float] = None
    lot_size: int = 1
    
    # 盘前数据
    premarket_price: Optional[float] = None
    premarket_change: Optional[float] = None
    premarket_change_percentage: Optional[float] = None
    premarket_time: Optional[str] = None

class StockInfoProcessor:
    """股票信息处理器"""
    
    def __init__(self):
        self.tradier_client = TradierClient()
    
    async def get_stock_info(self, symbol: str) -> StockInfo:
        """获取完整的股票信息"""
        try:
            # 1. 获取基础报价数据
            quotes = self.tradier_client.get_quotes([symbol.upper()])
            if not quotes:
                raise ValueError(f"No data found for symbol: {symbol}")
            
            quote = quotes[0]
            
            # 2. 获取公司信息 (可选)
            company_info = self.tradier_client.get_company_info(symbol.upper())
            
            # 3. 获取财务比率 (可选)
            ratios = self.tradier_client.get_ratios(symbol.upper())
            
            # 4. 构建标准化数据结构
            stock_info = self._build_stock_info(quote, company_info, ratios)
            
            return stock_info
            
        except Exception as e:
            raise Exception(f"Failed to fetch stock info for {symbol}: {str(e)}")
    
    def _build_stock_info(self, quote: TradierQuote, company_info: Dict, ratios: Dict) -> StockInfo:
        """构建标准化的股票信息数据结构"""
        # 计算振幅
        amplitude = None
        if quote.high and quote.low and quote.prevclose:
            amplitude = ((quote.high - quote.low) / quote.prevclose) * 100
        
        # 提取公司名称
        company_name = quote.description or quote.symbol
        
        # 构建时间信息 (假设为美东时间)
        from src.utils.time import get_timezone_time
        eastern_time = get_timezone_time("US/Eastern")
        close_time = eastern_time.strftime("%m/%d %H:%M:%S")
        
        return StockInfo(
            # 基础信息
            symbol=quote.symbol,
            company_name=company_name,
            close_price=quote.last or 0.0,
            close_time=close_time + " (美东)",
            
            # 价格变动
            change_amount=quote.change or 0.0,
            change_percentage=quote.change_percentage or 0.0,
            high_price=quote.high or 0.0,
            low_price=quote.low or 0.0,
            open_price=quote.open or 0.0,
            prev_close=quote.prevclose or 0.0,
            
            # 交易数据
            volume=quote.volume or 0,
            # turnover_amount 和 turnover_rate 需要额外计算
            
            # 技术指标
            amplitude=amplitude,
            lot_size=1  # 美股默认1股
        )
    
    def format_stock_info(self, stock_info: StockInfo) -> str:
        """格式化股票信息为用户友好的文本"""
        # 构建中文公司名称 (如果有的话，否则使用英文)
        company_display = f"{stock_info.symbol} ({stock_info.company_name})"
        
        # 格式化数值显示
        def format_currency(value: Optional[float], prefix: str = "$") -> str:
            if value is None:
                return "N/A"
            return f"{prefix}{value:,.3f}"
        
        def format_percentage(value: Optional[float]) -> str:
            if value is None:
                return "N/A"
            sign = "+" if value >= 0 else ""
            return f"{sign}{value:.2f}%"
        
        def format_number(value: Optional[float], suffix: str = "") -> str:
            if value is None:
                return "N/A"
            if value >= 1e12:
                return f"{value/1e12:.2f}万亿{suffix}"
            elif value >= 1e8:
                return f"{value/1e8:.2f}亿{suffix}"
            elif value >= 1e4:
                return f"{value/1e4:.2f}万{suffix}"
            return f"{value:,.0f}{suffix}"
        
        output = f"""## {company_display} - 关键信息

**基础信息**
- 股票代码: {stock_info.symbol}
- 收盘价: {format_currency(stock_info.close_price)}
- 收盘时间: {stock_info.close_time}

**价格变动**
- 涨跌额: {format_currency(stock_info.change_amount, "+" if stock_info.change_amount >= 0 else "")}
- 涨跌幅: {format_percentage(stock_info.change_percentage)}
- 最高价: {format_currency(stock_info.high_price)}
- 最低价: {format_currency(stock_info.low_price)}
- 今开: {format_currency(stock_info.open_price)}
- 昨收: {format_currency(stock_info.prev_close)}

**交易数据**
- 成交量: {format_number(stock_info.volume, "股")}"""

        # 添加可选的估值指标
        if any([stock_info.pe_ratio_ttm, stock_info.pb_ratio, stock_info.market_cap]):
            output += """

**估值指标**"""
            if stock_info.pe_ratio_ttm:
                output += f"\n- 市盈率TTM: {stock_info.pe_ratio_ttm:.2f}"
            if stock_info.pb_ratio:
                output += f"\n- 市净率: {stock_info.pb_ratio:.2f}"
            if stock_info.market_cap:
                output += f"\n- 总市值: {format_number(stock_info.market_cap)}"

        # 添加技术指标
        output += """

**技术指标**"""
        if stock_info.week_52_high:
            output += f"\n- 52周最高: {format_currency(stock_info.week_52_high)}"
        if stock_info.week_52_low:
            output += f"\n- 52周最低: {format_currency(stock_info.week_52_low)}"
        if stock_info.beta:
            output += f"\n- Beta系数: {stock_info.beta:.3f}"
        if stock_info.amplitude:
            output += f"\n- 振幅: {stock_info.amplitude:.2f}%"
        output += f"\n- 每手: {stock_info.lot_size}股"

        # 添加盘前数据 (如果有)
        if stock_info.premarket_price:
            output += f"""

**盘前交易**
- 盘前价格: {format_currency(stock_info.premarket_price)}
- 盘前变动: {format_currency(stock_info.premarket_change)} ({format_percentage(stock_info.premarket_change_percentage)})"""
            if stock_info.premarket_time:
                output += f"\n- 盘前时间: {stock_info.premarket_time}"

        return output
```

### 第三阶段：MCP 工具实现

#### 3.1 创建 MCP 工具
**文件**: `src/mcp_server/tools/stock_info_tool.py`

MCP 工具封装层：

```python
"""MCP tool for stock key information retrieval."""

from typing import Dict, Any
from src.stock.info import StockInfoProcessor

async def get_stock_key_info(symbol: str) -> Dict[str, Any]:
    """
    Get comprehensive key information for a stock symbol.
    
    This MCP tool retrieves detailed stock information including:
    - Basic price and trading data
    - Valuation metrics  
    - Technical indicators
    - Pre-market data (if available)
    
    Args:
        symbol: Stock ticker symbol (e.g., "TSLA", "AAPL")
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating if request succeeded
        - symbol: The requested stock symbol
        - formatted_info: Human-readable formatted stock information
        - raw_data: Structured data object for programmatic use
        - timestamp: UTC timestamp of the response
        - error: Error message (if failed)
    """
    try:
        processor = StockInfoProcessor()
        
        # 获取股票信息
        stock_info = await processor.get_stock_info(symbol.upper())
        
        # 格式化信息
        formatted_info = processor.format_stock_info(stock_info)
        
        from datetime import datetime, timezone
        
        return {
            "success": True,
            "symbol": stock_info.symbol,
            "formatted_info": formatted_info,
            "raw_data": {
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
                    "pb_ratio": stock_info.pb_ratio,
                    "market_cap": stock_info.market_cap
                },
                "technical_indicators": {
                    "week_52_high": stock_info.week_52_high,
                    "week_52_low": stock_info.week_52_low,
                    "beta": stock_info.beta,
                    "amplitude": stock_info.amplitude
                }
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "symbol": symbol.upper(),
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
```

#### 3.2 更新服务器注册
**文件**: `src/mcp_server/server.py` (更新)

在现有服务器中注册新工具：

```python
# 添加导入
from .tools.stock_info_tool import get_stock_key_info

# 在 create_server 函数中添加工具注册
@mcp.tool()
async def stock_info_tool(symbol: str) -> Dict[str, Any]:
    """
    Get comprehensive key information for a stock symbol.
    
    Retrieves detailed stock information including price data, trading volume,
    valuation metrics, and technical indicators using real-time Tradier API data.
    
    Args:
        symbol: Stock ticker symbol (e.g., "TSLA", "AAPL", "NVDA")
        
    Returns:
        Comprehensive stock information with formatted display and raw data
    """
    return await get_stock_key_info(symbol)
```

#### 3.3 更新工具导出
**文件**: `src/mcp_server/tools/__init__.py` (更新)

```python
"""MCP Server tools module."""

from .hello_tool import hello
from .get_market_time_tool import get_market_time_status
from .stock_info_tool import get_stock_key_info

__all__ = ["hello", "get_market_time_status", "get_stock_key_info"]
```

### 第四阶段：依赖和配置

#### 4.1 更新项目依赖
**文件**: `pyproject.toml` (更新)

添加新依赖：
```toml
dependencies = [
    "fastmcp>=2.0.0",
    "pydantic>=2.0.0",
    "requests>=2.28.0",  # 用于 Tradier API 调用
]
```

#### 4.2 创建 Provider 模块初始化
**文件**: `src/provider/__init__.py`
```python
"""Data provider modules."""
```

**文件**: `src/provider/tradier/__init__.py`
```python
"""Tradier API client module."""

from .client import TradierClient, TradierQuote

__all__ = ["TradierClient", "TradierQuote"]
```

### 第五阶段：测试实现

#### 5.1 单元测试
**文件**: `tests/provider/tradier/test_client.py`

```python
"""Tests for Tradier API client."""

import pytest
from unittest.mock import Mock, patch
from src.provider.tradier.client import TradierClient, TradierQuote

class TestTradierClient:
    
    @pytest.fixture
    def client(self):
        return TradierClient("test_token")
    
    @patch('src.provider.tradier.client.requests.Session.get')
    def test_get_quotes_success(self, mock_get, client):
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "quotes": {
                "quote": {
                    "symbol": "TSLA",
                    "last": 442.79,
                    "change": 16.94,
                    "change_percentage": 3.98,
                    # ... other fields
                }
            }
        }
        mock_get.return_value = mock_response
        
        quotes = client.get_quotes(["TSLA"])
        
        assert len(quotes) == 1
        assert quotes[0].symbol == "TSLA"
        assert quotes[0].last == 442.79
    
    def test_missing_access_token(self):
        with pytest.raises(ValueError, match="access token is required"):
            TradierClient(None)
```

**文件**: `tests/stock/test_info.py`

```python
"""Tests for stock information processing."""

import pytest
from unittest.mock import Mock, AsyncMock
from src.stock.info import StockInfoProcessor, StockInfo

class TestStockInfoProcessor:
    
    @pytest.fixture
    def processor(self):
        return StockInfoProcessor()
    
    @pytest.mark.asyncio
    async def test_get_stock_info_success(self, processor):
        # Mock the Tradier client
        with patch.object(processor, 'tradier_client') as mock_client:
            mock_quote = Mock()
            mock_quote.symbol = "TSLA"
            mock_quote.last = 442.79
            # ... set other attributes
            
            mock_client.get_quotes.return_value = [mock_quote]
            mock_client.get_company_info.return_value = {}
            mock_client.get_ratios.return_value = {}
            
            stock_info = await processor.get_stock_info("TSLA")
            
            assert stock_info.symbol == "TSLA"
            assert stock_info.close_price == 442.79
    
    def test_format_stock_info(self, processor):
        stock_info = StockInfo(
            symbol="TSLA",
            company_name="Tesla Inc",
            close_price=442.79,
            change_amount=16.94,
            change_percentage=3.98,
            # ... other required fields
        )
        
        formatted = processor.format_stock_info(stock_info)
        
        assert "TSLA (Tesla Inc)" in formatted
        assert "$442.790" in formatted
        assert "+3.98%" in formatted
```

**文件**: `tests/tools/test_stock_info_tool.py`

```python
"""Tests for stock info MCP tool."""

import pytest
from unittest.mock import patch, AsyncMock
from src.mcp_server.tools.stock_info_tool import get_stock_key_info

@pytest.mark.asyncio
async def test_get_stock_key_info_success():
    with patch('src.mcp_server.tools.stock_info_tool.StockInfoProcessor') as mock_processor_class:
        mock_processor = AsyncMock()
        mock_processor_class.return_value = mock_processor
        
        mock_stock_info = Mock()
        mock_stock_info.symbol = "TSLA"
        mock_processor.get_stock_info.return_value = mock_stock_info
        mock_processor.format_stock_info.return_value = "Formatted info"
        
        result = await get_stock_key_info("TSLA")
        
        assert result["success"] is True
        assert result["symbol"] == "TSLA"
        assert "formatted_info" in result
        assert "raw_data" in result

@pytest.mark.asyncio
async def test_get_stock_key_info_error():
    with patch('src.mcp_server.tools.stock_info_tool.StockInfoProcessor') as mock_processor_class:
        mock_processor = AsyncMock()
        mock_processor_class.return_value = mock_processor
        mock_processor.get_stock_info.side_effect = Exception("API Error")
        
        result = await get_stock_key_info("INVALID")
        
        assert result["success"] is False
        assert "error" in result
```

#### 5.2 集成测试
**文件**: `tests/integration/test_stock_info_integration.py`

```python
"""Integration tests for stock info functionality."""

import pytest
import os
from src.mcp_server.tools.stock_info_tool import get_stock_key_info

@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("TRADIER_ACCESS_TOKEN"), reason="Requires Tradier API token")
@pytest.mark.asyncio
async def test_real_stock_info_retrieval():
    """Test with real Tradier API (requires valid token)."""
    result = await get_stock_key_info("AAPL")
    
    assert result["success"] is True
    assert result["symbol"] == "AAPL"
    assert "Apple" in result["formatted_info"] or "AAPL" in result["formatted_info"]
    assert result["raw_data"]["price_data"]["close_price"] > 0
```

## 实施挑战与解决方案

### 挑战1：API 限制和错误处理
**问题**: Tradier API 可能有速率限制，且可能返回不完整数据

**解决方案**:
- 实现指数退避重试机制
- 对缺失数据提供默认值
- 完善的错误日志记录

```python
import time
import random

class TradierClient:
    def _make_request_with_retry(self, method: str, endpoint: str, params: Dict = None, max_retries: int = 3) -> Dict:
        for attempt in range(max_retries):
            try:
                return self._make_request(method, endpoint, params)
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                
                # 指数退避
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
```

### 挑战2：数据格式标准化
**问题**: 不同 API 端点返回的数据格式不一致

**解决方案**:
- 创建标准化的数据转换层
- 使用 dataclass 确保类型安全
- 提供数据验证和清洗功能

### 挑战3：中英文混合显示
**问题**: 需要提供中文标签但保持英文数据准确性

**解决方案**:
- 创建翻译映射表
- 保持原始英文数据在 raw_data 中
- 格式化输出仅用于显示

### 挑战4：实时数据的时效性
**问题**: 确保显示的时间信息准确

**解决方案**:
- 集成现有的市场时间工具
- 标明数据更新时间
- 区分盘前、盘中、盘后数据

## 成功标准

### 功能性标准
- ✅ 能够成功查询主流股票 (TSLA, AAPL, NVDA 等)
- ✅ 返回完整的格式化信息，包含所有必需字段
- ✅ 错误处理优雅，提供有用的错误信息
- ✅ 响应时间在合理范围内 (<5秒)

### 代码质量标准
- ✅ 测试覆盖率 >80%
- ✅ 类型提示完整
- ✅ 遵循项目代码风格
- ✅ 完整的文档字符串

### 集成标准
- ✅ 成功注册为 MCP 工具
- ✅ 在 Claude Code 中正常工作
- ✅ 与现有系统无冲突
- ✅ 配置管理统一

## 部署和维护

### 部署步骤
1. 确保 `.env` 文件配置正确的 `TRADIER_ACCESS_TOKEN`
2. 运行 `uv sync` 安装新依赖
3. 执行单元测试确保功能正常
4. 重启 MCP 服务器
5. 在 Claude Code 中测试工具

### 监控和维护
- 监控 Tradier API 响应时间和错误率
- 定期验证数据准确性
- 更新股票列表和公司信息
- 根据用户反馈优化显示格式

### 扩展计划
- 支持期权信息查询
- 添加技术分析指标
- 集成多个数据源
- 支持国际市场股票

## 时间估算

- **第一阶段** (Tradier 客户端): 2-3天
- **第二阶段** (股票信息处理): 3-4天  
- **第三阶段** (MCP 工具集成): 1-2天
- **第四阶段** (依赖配置): 1天
- **第五阶段** (测试实现): 2-3天

**总计**: 9-13天

## 总结

这个实现计划遵循了现有项目的架构原则，提供了完整的股票信息查询功能。通过分层设计，确保了代码的可维护性和可扩展性。详细的测试策略和错误处理保证了生产环境的稳定性。

计划中的每个组件都有明确的职责，使用真实的 Tradier API 数据，并提供了用户友好的中文格式化输出。整个实现将无缝集成到现有的 TradingAgentMCP 系统中。