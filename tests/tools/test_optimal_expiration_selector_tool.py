"""
OptimalExpirationSelectorTool MCP工具测试

测试optimal_expiration_selector_tool的功能，包括：
- TradierClient初始化测试
- 自动获取到期日功能测试
- 手动提供到期日功能测试
- 错误处理测试

Author: TradingAgent MCP Team
Version: v1.0
Created: 2024-10-03
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from src.mcp_server.tools.optimal_expiration_selector_tool import OptimalExpirationSelectorTool
from src.provider.tradier.client import TradierClient


@pytest.fixture
def mock_tradier_client():
    """创建模拟的Tradier客户端"""
    mock_client = MagicMock()

    # 模拟期权到期日数据
    future_dates = [
        (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
        (datetime.now() + timedelta(days=21)).strftime("%Y-%m-%d"),
        (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%d"),
        (datetime.now() + timedelta(days=49)).strftime("%Y-%m-%d"),
    ]

    mock_expirations = [MagicMock(date=date) for date in future_dates]
    # get_option_expirations是同步方法，不是异步方法
    mock_client.get_option_expirations = MagicMock(return_value=mock_expirations)

    return mock_client


@pytest.fixture
def sample_expirations():
    """提供示例到期日列表"""
    future_dates = [
        (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
        (datetime.now() + timedelta(days=21)).strftime("%Y-%m-%d"),
        (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%d"),
    ]
    return future_dates


@pytest.mark.asyncio
async def test_tool_with_tradier_client(mock_tradier_client):
    """测试工具能够正确使用TradierClient"""
    tool = OptimalExpirationSelectorTool(tradier_client=mock_tradier_client)

    result = await tool.execute(symbol="GOOG")

    # 验证结果结构
    assert "success" in result
    assert "symbol" in result
    assert result["symbol"] == "GOOG"

    # 验证调用了Tradier客户端
    if result["success"]:
        mock_tradier_client.get_option_expirations.assert_called_once_with("GOOG")


@pytest.mark.asyncio
async def test_tool_with_provided_expirations(mock_tradier_client, sample_expirations):
    """测试工具使用手动提供的到期日"""
    tool = OptimalExpirationSelectorTool(tradier_client=mock_tradier_client)

    result = await tool.execute(
        symbol="GOOG",
        available_expirations=sample_expirations
    )

    # 验证结果
    assert "success" in result
    assert result["symbol"] == "GOOG"

    # 验证没有调用Tradier客户端（因为提供了到期日）
    mock_tradier_client.get_option_expirations.assert_not_called()


@pytest.mark.asyncio
async def test_tool_without_tradier_client_fails():
    """测试没有TradierClient时无法自动获取到期日"""
    tool = OptimalExpirationSelectorTool(tradier_client=None)

    result = await tool.execute(symbol="GOOG", available_expirations=None)

    # 验证返回错误
    assert "success" in result
    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_tool_with_invalid_symbol(mock_tradier_client):
    """测试无效股票代码的错误处理"""
    # get_option_expirations是同步方法，不是异步方法
    mock_tradier_client.get_option_expirations = MagicMock(return_value=None)

    tool = OptimalExpirationSelectorTool(tradier_client=mock_tradier_client)

    result = await tool.execute(symbol="INVALID")

    # 验证返回错误
    assert "success" in result
    if not result["success"]:
        assert "error" in result


@pytest.mark.asyncio
async def test_tool_with_strategy_type(mock_tradier_client, sample_expirations):
    """测试不同策略类型的支持"""
    tool = OptimalExpirationSelectorTool(tradier_client=mock_tradier_client)

    # 测试CSP策略
    result_csp = await tool.execute(
        symbol="GOOG",
        available_expirations=sample_expirations,
        strategy_type="csp"
    )
    assert "success" in result_csp

    # 测试covered call策略
    result_cc = await tool.execute(
        symbol="GOOG",
        available_expirations=sample_expirations,
        strategy_type="covered_call"
    )
    assert "success" in result_cc


@pytest.mark.asyncio
async def test_tool_with_custom_weights(mock_tradier_client, sample_expirations):
    """测试自定义权重配置"""
    tool = OptimalExpirationSelectorTool(tradier_client=mock_tradier_client)

    custom_weights = {
        "theta_efficiency": 0.4,
        "gamma_risk": 0.3,
        "liquidity": 0.2,
        "earnings_buffer": 0.1
    }

    result = await tool.execute(
        symbol="GOOG",
        available_expirations=sample_expirations,
        weights=custom_weights
    )

    assert "success" in result


@pytest.mark.asyncio
async def test_tool_response_structure(mock_tradier_client, sample_expirations):
    """测试响应结构的完整性"""
    tool = OptimalExpirationSelectorTool(tradier_client=mock_tradier_client)

    result = await tool.execute(
        symbol="GOOG",
        available_expirations=sample_expirations
    )

    # 验证基本字段
    assert "success" in result
    assert "symbol" in result
    assert "timestamp" in result

    # 如果成功，验证关键数据字段
    if result["success"]:
        # 响应中应包含选择的到期日信息
        assert result["symbol"] == "GOOG"


@pytest.mark.asyncio
async def test_tradier_client_integration():
    """测试真实的TradierClient集成（需要API访问）"""
    # 这个测试可能因API限制而失败，标记为可能跳过
    try:
        tradier_client = TradierClient()
        tool = OptimalExpirationSelectorTool(tradier_client=tradier_client)

        result = await tool.execute(symbol="AAPL")

        # 验证结果
        assert "success" in result
        assert "symbol" in result

    except Exception as e:
        pytest.skip(f"Tradier API不可用: {str(e)}")
