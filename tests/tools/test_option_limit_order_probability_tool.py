"""
集成测试：期权限价单成交概率预测工具
"""

import pytest
from unittest.mock import Mock, patch
from dataclasses import dataclass
from typing import Optional, Dict
from src.mcp_server.tools.option_limit_order_probability_tool import (
    option_limit_order_probability_tool
)


@dataclass
class MockOptionContract:
    """Mock OptionContract for testing"""
    symbol: str
    strike: float
    expiration_date: str
    option_type: str
    bid: Optional[float] = None
    ask: Optional[float] = None
    last: Optional[float] = None
    greeks: Optional[Dict[str, float]] = None


def create_mock_options_result(strike: float, option_type: str, underlying_price: float, greeks: Dict[str, float]):
    """Helper function to create mock options chain data"""
    mock_option = MockOptionContract(
        symbol=f"TEST{strike:.0f}{option_type[0].upper()}",
        strike=strike,
        expiration_date="2025-11-07",
        option_type=option_type,
        greeks=greeks
    )

    options_list = [mock_option]
    return {
        "summary": {
            "underlying_price": underlying_price
        },
        "options_data": {
            "all_options": options_list,
            "calls": options_list if option_type == "call" else [],
            "puts": options_list if option_type == "put" else []
        },
        "classification": {},
        "greeks_summary": {}
    }


class TestOptionLimitOrderProbabilityTool:
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """测试完整工作流"""
        with patch('src.mcp_server.tools.option_limit_order_probability_tool.TradierClient'):
            with patch('src.mcp_server.tools.option_limit_order_probability_tool.get_options_chain_data') as mock_chain:
                mock_chain.return_value = create_mock_options_result(
                    strike=145.0,
                    option_type="put",
                    underlying_price=150.0,
                    greeks={
                        "delta": -0.42,
                        "theta": -0.08,
                        "gamma": 0.02,
                        "vega": 0.15,
                        "mid_iv": 0.35
                    }
                )

                with patch('src.stock.history_data.get_stock_history_data') as mock_history:
                    mock_history.return_value = {
                        "status": "success",
                        "preview_records": [{"close": 150 + i * 0.5} for i in range(100)]
                    }

                    result = await option_limit_order_probability_tool(
                        symbol="AAPL",
                        strike_price=145.0,
                        expiration="2025-11-07",
                        option_type="put",
                        current_price=2.50,
                        limit_price=2.80,
                        order_side="sell"
                    )

                    assert result["status"] == "success"
                    assert "fill_probability" in result
                    assert 0 <= result["fill_probability"] <= 1

                    # 验证first_day_fill_probability字段
                    assert "first_day_fill_probability" in result
                    assert 0 <= result["first_day_fill_probability"] <= 1
                    assert result["first_day_fill_probability"] <= result["fill_probability"]

    @pytest.mark.asyncio
    async def test_parameter_validation(self):
        """测试输入参数验证"""
        # 无效的期权类型
        result = await option_limit_order_probability_tool(
            symbol="AAPL",
            strike_price=145.0,
            expiration="2025-11-07",
            option_type="invalid",
            current_price=2.50,
            limit_price=2.80,
            order_side="sell"
        )
        assert result["status"] == "error"
        assert "Invalid option_type" in result["error"]

        # 无效的订单方向
        result = await option_limit_order_probability_tool(
            symbol="AAPL",
            strike_price=145.0,
            expiration="2025-11-07",
            option_type="put",
            current_price=2.50,
            limit_price=2.80,
            order_side="invalid"
        )
        assert result["status"] == "error"
        assert "Invalid order_side" in result["error"]

        # 卖单的无效限价（低于当前价）
        result = await option_limit_order_probability_tool(
            symbol="AAPL",
            strike_price=145.0,
            expiration="2025-11-07",
            option_type="put",
            current_price=2.50,
            limit_price=2.40,
            order_side="sell"
        )
        assert result["status"] == "error"
        assert "limit price must be above current price" in result["error"]

    @pytest.mark.asyncio
    async def test_sell_order_scenario(self):
        """测试卖单场景"""
        with patch('src.mcp_server.tools.option_limit_order_probability_tool.TradierClient'):
            with patch('src.mcp_server.tools.option_limit_order_probability_tool.get_options_chain_data') as mock_chain:
                mock_chain.return_value = create_mock_options_result(
                    strike=145.0,
                    option_type="put",
                    underlying_price=150.0,
                    greeks={
                        "delta": -0.42,
                        "theta": -0.08,
                        "gamma": 0.02,
                        "vega": 0.15,
                        "mid_iv": 0.35
                    }
                )

                with patch('src.stock.history_data.get_stock_history_data') as mock_history:
                    mock_history.return_value = {
                        "status": "success",
                        "preview_records": [{"close": 150 + i * 0.2} for i in range(100)]
                    }

                    result = await option_limit_order_probability_tool(
                        symbol="AAPL",
                        strike_price=145.0,
                        expiration="2025-11-07",
                        option_type="put",
                        current_price=2.50,
                        limit_price=2.80,
                        order_side="sell"
                    )

                    assert result["status"] == "success"
                    assert result["option_details"]["order_side"] == "sell"
                    assert "fill_probability" in result
                    assert "first_day_fill_probability" in result

    @pytest.mark.asyncio
    async def test_option_not_found_error(self):
        """测试期权未找到错误"""
        with patch('src.mcp_server.tools.option_limit_order_probability_tool.TradierClient'):
            with patch('src.mcp_server.tools.option_limit_order_probability_tool.get_options_chain_data') as mock_chain:
                mock_chain.return_value = create_mock_options_result(
                    strike=140.0,  # 不同的执行价
                    option_type="put",
                    underlying_price=150.0,
                    greeks={
                        "delta": -0.30,
                        "theta": -0.06,
                        "gamma": 0.01,
                        "vega": 0.12,
                        "mid_iv": 0.32
                    }
                )

                result = await option_limit_order_probability_tool(
                    symbol="AAPL",
                    strike_price=145.0,  # 请求的执行价不存在
                    expiration="2025-11-07",
                    option_type="put",
                    current_price=2.50,
                    limit_price=2.80,
                    order_side="sell"
                )

                assert result["status"] == "error"
                assert "Option not found" in result["error"]
