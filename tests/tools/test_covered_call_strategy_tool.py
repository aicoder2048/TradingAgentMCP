"""Tests for covered call strategy MCP tool."""

import pytest
from unittest.mock import patch, AsyncMock, Mock
from datetime import datetime, date
from src.mcp_server.tools.covered_call_strategy_tool import (
    covered_call_strategy_tool,
    validate_cc_parameters,
    get_strategy_examples,
    format_strategy_summary
)
from src.provider.tradier.client import OptionContract, TradierQuote


class TestCoveredCallStrategyTool:
    """Test suite for covered_call_strategy_tool MCP tool."""

    @pytest.mark.asyncio
    async def test_insufficient_shares_validation(self):
        """Test validation when user has insufficient shares."""
        result = await covered_call_strategy_tool(
            symbol="AAPL",
            shares_owned=50  # Less than 100
        )
        
        assert result["status"] == "insufficient_shares"
        assert "至少100股" in result["error"]
        assert result["shares_owned"] == 50
        assert result["shares_needed"] == 100

    @pytest.mark.asyncio
    async def test_invalid_strategy_type(self):
        """Test invalid strategy type handling."""
        result = await covered_call_strategy_tool(
            symbol="AAPL",
            purpose_type="invalid_type",
            shares_owned=100
        )
        
        assert result["status"] == "invalid_parameters"
        assert "策略类型必须是" in result["error"]

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.covered_call_strategy_tool.TradierClient')
    async def test_market_data_error(self, mock_client_class):
        """Test market data retrieval error."""
        # Setup mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_quotes.return_value = []  # No quotes returned
        
        result = await covered_call_strategy_tool(
            symbol="INVALID",
            shares_owned=100
        )
        
        assert result["status"] == "market_data_error"
        assert "无法获取" in result["error"]

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.covered_call_strategy_tool.TradierClient')
    @patch('src.mcp_server.tools.covered_call_strategy_tool.ExpirationSelector')
    @patch('src.mcp_server.tools.covered_call_strategy_tool.CoveredCallAnalyzer')
    async def test_successful_income_strategy(self, mock_analyzer_class, mock_expiration_class, mock_client_class):
        """Test successful income strategy execution."""
        # Setup mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock quote data
        mock_quote = TradierQuote(
            symbol="AAPL",
            last=150.0,
            change=1.5,
            change_percentage=1.0,
            volume=1000000,
            last_volume=100
        )
        mock_client.get_quotes.return_value = [mock_quote]
        mock_client.calculate_resistance_levels.return_value = {
            "resistance_20d": 155.0,
            "resistance_60d": 160.0
        }
        
        # Setup mock expiration selector
        mock_expiration = Mock()
        mock_expiration_class.return_value = mock_expiration
        mock_expiration.get_optimal_expiration = AsyncMock(return_value=(
            "2024-01-19",
            {"days_to_expiry": 7, "option_type": "weekly", "selection_reason": "optimal"}
        ))
        
        # Setup mock analyzer
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.delta_ranges = {"income": {"min": 0.10, "max": 0.30}}
        mock_analyzer.min_open_interest = 50
        mock_analyzer.min_volume = 10
        mock_analyzer.max_bid_ask_spread_pct = 0.15
        
        # Mock optimal strikes
        mock_optimal_strikes = [
            {
                "symbol": "AAPL240119C00155000",
                "strike": 155.0,
                "delta": 0.25,
                "premium": 2.50,
                "upside_capture": 3.33,
                "annualized_return": 15.2,
                "assignment_probability": 25.0,
                "composite_score": 85.5
            }
        ]
        mock_analyzer.find_optimal_strikes = AsyncMock(return_value=mock_optimal_strikes)
        
        # Mock recommendation engine and other components
        with patch('src.mcp_server.tools.covered_call_strategy_tool.CoveredCallRecommendationEngine') as mock_rec_engine_class, \
             patch('src.mcp_server.tools.covered_call_strategy_tool.CoveredCallOrderFormatter') as mock_formatter_class, \
             patch('src.mcp_server.tools.covered_call_strategy_tool.export_cc_analysis_to_csv') as mock_export, \
             patch('src.mcp_server.tools.covered_call_strategy_tool.get_cc_market_context') as mock_context, \
             patch('src.mcp_server.tools.covered_call_strategy_tool.generate_cc_execution_notes') as mock_notes:
            
            # Setup recommendation engine
            mock_rec_engine = Mock()
            mock_rec_engine_class.return_value = mock_rec_engine
            mock_recommendations = {
                "conservative": {
                    "profile": "conservative",
                    "option_details": mock_optimal_strikes[0],
                    "pnl_analysis": {
                        "premium_income": 1250.0,
                        "max_profit_if_called": 1750.0,
                        "annualized_return": 15.2
                    },
                    "risk_metrics": {
                        "assignment_probability": 25.0,
                        "delta": 0.25
                    },
                    "recommendation_reasoning": "Conservative income strategy with low assignment risk"
                }
            }
            mock_rec_engine.generate_three_alternatives.return_value = mock_recommendations
            
            # Setup order formatter
            mock_formatter = Mock()
            mock_formatter_class.return_value = mock_formatter
            mock_formatter.format_order_block.return_value = "Mock Order Block"
            
            # Setup other mocks
            mock_export.return_value = "./data/cc_AAPL_test.csv"
            mock_context.return_value = {"implied_volatility": 0.25}
            mock_notes.return_value = "Mock execution notes"
            
            result = await covered_call_strategy_tool(
                symbol="AAPL",
                purpose_type="income",
                shares_owned=500
            )
            
            # Verify successful response
            assert result["status"] == "success"
            assert result["symbol"] == "AAPL"
            assert result["current_price"] == 150.0
            assert result["position_validation"]["shares_owned"] == 500
            assert result["position_validation"]["contracts_available"] == 5
            assert "conservative" in result["recommendations"]
            assert result["csv_export_path"] == "./data/cc_AAPL_test.csv"

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.covered_call_strategy_tool.TradierClient')
    @patch('src.mcp_server.tools.covered_call_strategy_tool.ExpirationSelector')
    @patch('src.mcp_server.tools.covered_call_strategy_tool.CoveredCallAnalyzer')
    async def test_no_suitable_options(self, mock_analyzer_class, mock_expiration_class, mock_client_class):
        """Test scenario when no suitable options are found."""
        # Setup mocks similar to successful test but with empty optimal strikes
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_quote = TradierQuote(
            symbol="AAPL",
            last=150.0,
            change=1.5,
            change_percentage=1.0,
            volume=1000000,
            last_volume=100
        )
        mock_client.get_quotes.return_value = [mock_quote]
        mock_client.calculate_resistance_levels.return_value = {}
        
        mock_expiration = Mock()
        mock_expiration_class.return_value = mock_expiration
        mock_expiration.get_optimal_expiration = AsyncMock(return_value=(
            "2024-01-19",
            {"days_to_expiry": 7, "option_type": "weekly"}
        ))
        
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.delta_ranges = {"income": {"min": 0.10, "max": 0.30}}
        mock_analyzer.find_optimal_strikes = AsyncMock(return_value=[])  # No options found
        
        result = await covered_call_strategy_tool(
            symbol="AAPL",
            purpose_type="income",
            shares_owned=100
        )
        
        assert result["status"] == "no_suitable_options"
        assert "未找到符合" in result["message"]
        assert result["criteria"]["purpose_type"] == "income"

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.covered_call_strategy_tool.TradierClient')
    @patch('src.mcp_server.tools.covered_call_strategy_tool.ExpirationSelector')
    async def test_no_expiration_available(self, mock_expiration_class, mock_client_class):
        """Test scenario when no suitable expiration date is available."""
        # Setup mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_quote = TradierQuote(
            symbol="AAPL",
            last=150.0,
            change=1.5,
            change_percentage=1.0,
            volume=1000000,
            last_volume=100
        )
        mock_client.get_quotes.return_value = [mock_quote]
        
        # Setup expiration selector to return None
        mock_expiration = Mock()
        mock_expiration_class.return_value = mock_expiration
        mock_expiration.get_optimal_expiration = AsyncMock(return_value=None)
        
        result = await covered_call_strategy_tool(
            symbol="AAPL",
            shares_owned=100
        )
        
        assert result["status"] == "no_expiration_available"
        assert "无法找到适合" in result["error"]

    @pytest.mark.asyncio
    async def test_exit_strategy_parameters(self):
        """Test exit strategy with specific parameters."""
        with patch('src.mcp_server.tools.covered_call_strategy_tool.TradierClient') as mock_client_class, \
             patch('src.mcp_server.tools.covered_call_strategy_tool.ExpirationSelector') as mock_expiration_class, \
             patch('src.mcp_server.tools.covered_call_strategy_tool.CoveredCallAnalyzer') as mock_analyzer_class:
            
            # Setup basic mocks
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_quote = TradierQuote(symbol="TSLA", last=250.0, change=5.0, change_percentage=2.0, volume=500000, last_volume=100)
            mock_client.get_quotes.return_value = [mock_quote]
            mock_client.calculate_resistance_levels.return_value = {"resistance_1": 260.0}
            
            mock_expiration = Mock()
            mock_expiration_class.return_value = mock_expiration
            mock_expiration.get_optimal_expiration = AsyncMock(return_value=("2024-02-16", {"days_to_expiry": 30, "option_type": "monthly"}))
            
            mock_analyzer = Mock()
            mock_analyzer_class.return_value = mock_analyzer
            mock_analyzer.delta_ranges = {"exit": {"min": 0.30, "max": 0.70}}
            
            # Test that analyzer is initialized with exit strategy
            result = await covered_call_strategy_tool(
                symbol="TSLA",
                purpose_type="exit",
                duration="1m",
                shares_owned=200,
                avg_cost=220.0,
                min_premium=3.0
            )
            
            # Verify analyzer was called with correct parameters
            mock_analyzer_class.assert_called_with(
                symbol="TSLA",
                purpose_type="exit",
                duration="1m",
                shares_owned=200,
                avg_cost=220.0,
                tradier_client=mock_client
            )


class TestCoveredCallParameterValidation:
    """Test suite for covered call parameter validation."""

    def test_validate_cc_parameters_valid(self):
        """Test parameter validation with valid inputs."""
        result = validate_cc_parameters(
            symbol="AAPL",
            purpose_type="income",
            duration="1w",
            shares_owned=500,
            avg_cost=150.0,
            min_premium=2.0
        )
        
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_cc_parameters_insufficient_shares(self):
        """Test parameter validation with insufficient shares."""
        result = validate_cc_parameters(
            symbol="AAPL",
            purpose_type="income",
            duration="1w",
            shares_owned=50
        )
        
        assert result["is_valid"] is False
        assert any("至少100股" in error for error in result["errors"])

    def test_validate_cc_parameters_invalid_strategy_type(self):
        """Test parameter validation with invalid strategy type."""
        result = validate_cc_parameters(
            symbol="AAPL",
            purpose_type="invalid",
            duration="1w",
            shares_owned=100
        )
        
        assert result["is_valid"] is False
        assert any("策略类型必须是" in error for error in result["errors"])

    def test_validate_cc_parameters_empty_symbol(self):
        """Test parameter validation with empty symbol."""
        result = validate_cc_parameters(
            symbol="",
            purpose_type="income",
            duration="1w",
            shares_owned=100
        )
        
        assert result["is_valid"] is False
        assert any("股票代码不能为空" in error for error in result["errors"])

    def test_validate_cc_parameters_negative_costs(self):
        """Test parameter validation with negative values."""
        result = validate_cc_parameters(
            symbol="AAPL",
            purpose_type="income",
            duration="1w",
            shares_owned=100,
            avg_cost=-1.0,
            min_premium=-1.0
        )
        
        assert result["is_valid"] is False
        assert any("平均成本必须为正数" in error for error in result["errors"])
        assert any("最低权利金必须为正数" in error for error in result["errors"])


class TestCoveredCallUtilities:
    """Test suite for covered call utility functions."""

    def test_get_strategy_examples(self):
        """Test strategy examples retrieval."""
        examples = get_strategy_examples()
        
        assert "income_weekly" in examples
        assert "exit_monthly" in examples
        assert "large_position" in examples
        
        # Verify structure
        income_example = examples["income_weekly"]
        assert "description" in income_example
        assert "parameters" in income_example
        assert "expected_outcome" in income_example
        assert income_example["parameters"]["purpose_type"] == "income"

    def test_format_strategy_summary_success(self):
        """Test strategy summary formatting for successful result."""
        mock_result = {
            "status": "success",
            "symbol": "AAPL",
            "current_price": 150.25,
            "position_validation": {
                "shares_owned": 500,
                "contracts_available": 5
            },
            "recommendations": {
                "conservative": {
                    "option_details": {"strike": 155.0},
                    "pnl_analysis": {"annualized_return": 15.2}
                },
                "balanced": {
                    "option_details": {"strike": 152.5},
                    "pnl_analysis": {"annualized_return": 18.5}
                }
            },
            "csv_export_path": "./data/cc_AAPL_test.csv"
        }
        
        summary = format_strategy_summary(mock_result)
        
        assert "AAPL Covered Call策略分析" in summary
        assert "$150.25" in summary
        assert "500股" in summary
        assert "5个合约" in summary
        assert "Conservative" in summary
        assert "Balanced" in summary
        assert "cc_AAPL_test.csv" in summary

    def test_format_strategy_summary_failure(self):
        """Test strategy summary formatting for failed result."""
        mock_result = {
            "status": "insufficient_shares",
            "error": "需要至少100股"
        }
        
        summary = format_strategy_summary(mock_result)
        
        assert "❌ 分析失败" in summary
        assert "需要至少100股" in summary


class TestCoveredCallIntegration:
    """Integration test suite for covered call strategy tool."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_workflow_mock_integration(self):
        """Test full workflow with realistic mock data."""
        # This test would use more realistic mock data to test the full integration
        # but without hitting external APIs
        
        with patch('src.mcp_server.tools.covered_call_strategy_tool.TradierClient') as mock_client_class:
            # Setup comprehensive mock client
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock realistic market data
            mock_quote = TradierQuote(
                symbol="AAPL",
                last=175.50,
                change=2.30,
                change_percentage=1.33,
                volume=45000000,
                last_volume=100
            )
            mock_client.get_quotes.return_value = [mock_quote]
            
            # Mock realistic resistance levels
            mock_client.calculate_resistance_levels.return_value = {
                "resistance_20d": 180.0,
                "resistance_60d": 185.0,
                "sma_50_resistance": 178.0,
                "psychological_resistance": 180.0
            }
            
            # Mock option chain data
            mock_option_data = [
                OptionContract(
                    symbol="AAPL240119C00180000",
                    description="AAPL Jan 19 2024 $180.00 Call",
                    expiration_date="2024-01-19",
                    strike=180.0,
                    option_type="call",
                    bid=3.50,
                    ask=3.70,
                    open_interest=1500,
                    volume=250,
                    greeks={"delta": 0.25, "theta": -0.05, "mid_iv": 0.28}
                )
            ]
            mock_client.get_call_options_by_delta_range.return_value = mock_option_data
            
            # Setup other required mocks
            with patch('src.mcp_server.tools.covered_call_strategy_tool.ExpirationSelector') as mock_exp, \
                 patch('src.mcp_server.tools.covered_call_strategy_tool.export_cc_analysis_to_csv') as mock_export, \
                 patch('src.mcp_server.tools.covered_call_strategy_tool.get_cc_market_context') as mock_context:
                
                mock_exp_instance = Mock()
                mock_exp.return_value = mock_exp_instance
                mock_exp_instance.get_optimal_expiration = AsyncMock(return_value=(
                    "2024-01-19",
                    {"days_to_expiry": 14, "option_type": "weekly"}
                ))
                
                mock_export.return_value = "./data/cc_AAPL_integration_test.csv"
                mock_context.return_value = {
                    "implied_volatility": 0.28,
                    "momentum_score": "bullish",
                    "volatility_regime": "normal"
                }
                
                # Execute the tool
                result = await covered_call_strategy_tool(
                    symbol="AAPL",
                    purpose_type="income",
                    duration="2w",
                    shares_owned=1000,
                    avg_cost=170.0,
                    min_premium=2.0,
                    include_order_blocks=True
                )
                
                # Comprehensive verification
                assert result["status"] == "success"
                assert result["symbol"] == "AAPL"
                assert result["current_price"] == 175.50
                assert result["position_validation"]["shares_owned"] == 1000
                assert result["position_validation"]["contracts_available"] == 10
                assert result["strategy_parameters"]["purpose_type"] == "income"
                assert result["strategy_parameters"]["min_premium"] == 2.0
                assert result["selected_expiration"]["date"] == "2024-01-19"
                assert "disclaimer" in result
                
                # Verify CSV export was called
                mock_export.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])