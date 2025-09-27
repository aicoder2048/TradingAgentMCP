"""Tests for cash secured put strategy MCP tool."""

import pytest
from unittest.mock import patch, AsyncMock, Mock
from datetime import datetime, date
from src.mcp_server.tools.cash_secured_put_strategy_tool import (
    cash_secured_put_strategy_tool,
    validate_csp_parameters,
    get_strategy_examples,
    format_strategy_summary
)
from src.provider.tradier.client import OptionContract, TradierQuote
from src.option.option_expiration_selector import ExpirationSelectionResult


class TestCashSecuredPutStrategyTool:
    """Test suite for cash_secured_put_strategy_tool MCP tool."""

    @pytest.mark.asyncio
    async def test_insufficient_capital_validation(self):
        """Test validation when user has insufficient capital."""
        result = await cash_secured_put_strategy_tool(
            symbol="AAPL",
            capital_limit=5000  # Insufficient for AAPL puts
        )
        
        assert result["status"] == "no_suitable_options"
        assert "未找到符合" in result["message"]
        assert result["details"]["capital_limit"] == 5000

    @pytest.mark.asyncio
    async def test_invalid_strategy_type(self):
        """Test invalid strategy type handling."""
        result = await cash_secured_put_strategy_tool(
            symbol="AAPL",
            purpose_type="invalid_type",
            capital_limit=50000
        )
        
        assert result["status"] == "error"
        assert "目的类型必须是" in result["message"]

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.cash_secured_put_strategy_tool.TradierClient')
    async def test_market_data_error(self, mock_client_class):
        """Test market data retrieval error."""
        # Setup mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_quotes.return_value = []  # No quotes returned
        
        result = await cash_secured_put_strategy_tool(
            symbol="INVALID",
            capital_limit=50000
        )
        
        assert result["status"] == "error"
        assert "无法获取" in result["message"]

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.cash_secured_put_strategy_tool.TradierClient')
    @patch('src.mcp_server.tools.cash_secured_put_strategy_tool.ExpirationSelector')
    @patch('src.mcp_server.tools.cash_secured_put_strategy_tool.CashSecuredPutAnalyzer')
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
        mock_expiration.get_optimal_expiration = AsyncMock(return_value=ExpirationSelectionResult(
            selected_date="2024-01-19",
            selection_reason="optimal weekly expiration",
            metadata={"actual_days": 7, "expiration_type": "weekly"},
            alternatives=[]
        ))
        
        # Setup mock analyzer
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.delta_ranges = {"income": {"min": -0.30, "max": -0.10}}
        mock_analyzer.min_open_interest = 50
        mock_analyzer.min_volume = 10
        mock_analyzer.max_bid_ask_spread_pct = 0.15
        
        # Mock optimal strikes
        mock_optimal_strikes = [
            {
                "symbol": "AAPL240119P00145000",
                "strike_price": 145.0,
                "delta": -0.25,
                "premium": 2.50,
                "assignment_probability": 0.16,  # Enhanced calculation
                "composite_score": 85.5,
                "required_capital": 14500.0
            }
        ]
        mock_analyzer.find_optimal_strikes = AsyncMock(return_value=mock_optimal_strikes)
        
        # Mock recommendation engine and other components
        with patch('src.mcp_server.tools.cash_secured_put_strategy_tool.StrategyRecommendationEngine') as mock_rec_engine_class, \
             patch('src.mcp_server.tools.cash_secured_put_strategy_tool.ProfessionalOrderFormatter') as mock_formatter_class, \
             patch('src.mcp_server.tools.cash_secured_put_strategy_tool.export_csp_analysis_to_csv') as mock_export, \
             patch('src.mcp_server.tools.cash_secured_put_strategy_tool.get_market_context') as mock_context, \
             patch('src.mcp_server.tools.cash_secured_put_strategy_tool.generate_execution_notes') as mock_notes:
            
            # Setup recommendation engine
            mock_rec_engine = Mock()
            mock_rec_engine_class.return_value = mock_rec_engine
            mock_recommendations = {
                "conservative": {
                    "profile": "conservative",
                    "option_details": mock_optimal_strikes[0],
                    "pnl_analysis": {
                        "premium_income": 250.0,
                        "max_profit": 250.0,
                        "annualized_return": 12.5,
                        "required_capital": 14500.0
                    },
                    "risk_metrics": {
                        "assignment_probability": 0.16,
                        "delta": -0.25
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
            mock_export.return_value = "./data/csp_AAPL_test.csv"
            mock_context.return_value = {"implied_volatility": 0.25}
            mock_notes.return_value = "Mock execution notes"
            
            result = await cash_secured_put_strategy_tool(
                symbol="AAPL",
                purpose_type="income",
                capital_limit=50000
            )
            
            # Verify successful response
            assert result["status"] == "success"
            assert result["symbol"] == "AAPL"
            assert result["current_price"] == 150.0
            assert result["strategy_parameters"]["capital_limit"] == 50000
            assert result["strategy_parameters"]["purpose_type"] == "income"
            assert "conservative" in result["recommendations"]
            assert result["csv_export_path"] == "./data/csp_AAPL_test.csv"

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.cash_secured_put_strategy_tool.TradierClient')
    @patch('src.mcp_server.tools.cash_secured_put_strategy_tool.ExpirationSelector')
    @patch('src.mcp_server.tools.cash_secured_put_strategy_tool.CashSecuredPutAnalyzer')
    async def test_discount_buying_strategy(self, mock_analyzer_class, mock_expiration_class, mock_client_class):
        """Test successful discount buying strategy execution."""
        # Similar setup but for discount strategy
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_quote = TradierQuote(
            symbol="TSLA",
            last=250.0,
            change=5.0,
            change_percentage=2.0,
            volume=500000,
            last_volume=100
        )
        mock_client.get_quotes.return_value = [mock_quote]
        mock_client.calculate_resistance_levels.return_value = {"resistance_1": 260.0}
        
        mock_expiration = Mock()
        mock_expiration_class.return_value = mock_expiration
        mock_expiration.get_optimal_expiration = AsyncMock(return_value=ExpirationSelectionResult(
            selected_date="2024-02-16",
            selection_reason="monthly expiration",
            metadata={"actual_days": 30, "expiration_type": "monthly"},
            alternatives=[]
        ))
        
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.delta_ranges = {"discount": {"min": -0.70, "max": -0.30}}
        
        # Configure find_optimal_strikes to return a proper list
        optimal_strikes_data = [{
            "symbol": "TSLA240216P00240000",
            "strike_price": 240.0,
            "delta": -0.45,
            "premium": 8.50,
            "assignment_probability": 0.35,
            "composite_score": 92.3,
            "required_capital": 24000.0
        }]
        mock_analyzer.find_optimal_strikes = AsyncMock(return_value=optimal_strikes_data)
        
        # Mock recommendation engine and other dependencies
        with patch('src.mcp_server.tools.cash_secured_put_strategy_tool.StrategyRecommendationEngine') as mock_rec_engine_class, \
             patch('src.mcp_server.tools.cash_secured_put_strategy_tool.ProfessionalOrderFormatter') as mock_formatter_class, \
             patch('src.mcp_server.tools.cash_secured_put_strategy_tool.export_csp_analysis_to_csv') as mock_export, \
             patch('src.mcp_server.tools.cash_secured_put_strategy_tool.get_market_context') as mock_context, \
             patch('src.mcp_server.tools.cash_secured_put_strategy_tool.generate_execution_notes') as mock_notes:
            
            # Setup recommendation engine
            mock_rec_engine = Mock()
            mock_rec_engine_class.return_value = mock_rec_engine
            mock_recommendations = {
                "conservative": {
                    "profile": "conservative",
                    "option_details": optimal_strikes_data[0],
                    "pnl_analysis": {
                        "premium_income": 850.0,
                        "max_profit": 850.0,
                        "annualized_return": 15.5,
                        "required_capital": 24000.0
                    },
                    "risk_metrics": {
                        "assignment_probability": 0.35,
                        "delta": -0.45
                    },
                    "recommendation_reasoning": "Discount buying strategy with moderate assignment risk"
                }
            }
            mock_rec_engine.generate_three_alternatives.return_value = mock_recommendations
            
            # Setup other mocks
            mock_formatter = Mock()
            mock_formatter_class.return_value = mock_formatter
            mock_formatter.format_order_block.return_value = "Mock Order Block"
            
            mock_export.return_value = "./data/csp_TSLA_discount.csv"
            mock_context.return_value = {"implied_volatility": 0.35}
            mock_notes.return_value = "Mock execution notes"
        
            # Test that analyzer is initialized with discount strategy
            result = await cash_secured_put_strategy_tool(
                symbol="TSLA",
                purpose_type="discount",
                duration="1m",
                capital_limit=30000,
                min_premium=5.0
            )
            
            # Verify successful execution
            assert result["status"] == "success"
            assert result["symbol"] == "TSLA"
            assert result["current_price"] == 250.0
            
            # Verify analyzer was called with correct parameters (capital_limit is passed to find_optimal_strikes, not constructor)
            mock_analyzer_class.assert_called_with(
                symbol="TSLA",
                purpose_type="discount",
                duration="1m",
                tradier_client=mock_client
            )

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.cash_secured_put_strategy_tool.TradierClient')
    @patch('src.mcp_server.tools.cash_secured_put_strategy_tool.ExpirationSelector')
    @patch('src.mcp_server.tools.cash_secured_put_strategy_tool.CashSecuredPutAnalyzer')
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
        mock_expiration.get_optimal_expiration = AsyncMock(return_value=ExpirationSelectionResult(
            selected_date="2024-01-19",
            selection_reason="weekly expiration",
            metadata={"actual_days": 7, "expiration_type": "weekly"},
            alternatives=[]
        ))
        
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.delta_ranges = {"income": {"min": -0.30, "max": -0.10}}
        mock_analyzer.find_optimal_strikes = AsyncMock(return_value=[])  # No options found
        
        result = await cash_secured_put_strategy_tool(
            symbol="AAPL",
            purpose_type="income",
            capital_limit=50000
        )
        
        assert result["status"] == "no_suitable_options"
        assert "未找到符合" in result["message"]
        assert result["details"]["purpose_type"] == "income"

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.cash_secured_put_strategy_tool.TradierClient')
    @patch('src.mcp_server.tools.cash_secured_put_strategy_tool.ExpirationSelector')
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
        
        result = await cash_secured_put_strategy_tool(
            symbol="AAPL",
            capital_limit=50000
        )
        
        assert result["status"] == "error"
        assert "error" in result

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.cash_secured_put_strategy_tool.TradierClient')
    async def test_analyzer_error_handling(self, mock_client_class):
        """Test analyzer initialization or processing errors."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_quote = TradierQuote(symbol="AAPL", last=150.0, change=1.5, change_percentage=1.0, volume=1000000, last_volume=100)
        mock_client.get_quotes.return_value = [mock_quote]
        
        # Mock analyzer to raise an exception
        with patch('src.mcp_server.tools.cash_secured_put_strategy_tool.CashSecuredPutAnalyzer') as mock_analyzer_class:
            mock_analyzer_class.side_effect = Exception("Analyzer initialization failed")
            
            result = await cash_secured_put_strategy_tool(
                symbol="AAPL",
                capital_limit=50000
            )
            
            assert result["status"] == "error"
            assert "error" in result
            assert "message" in result
            assert "Analyzer initialization failed" in result["message"]

    @pytest.mark.asyncio
    async def test_negative_capital_validation(self):
        """Test negative capital limit validation."""
        result = await cash_secured_put_strategy_tool(
            symbol="AAPL",
            capital_limit=-1000
        )
        
        # Negative capital limit should result in no suitable options being found
        assert result["status"] == "no_suitable_options"
        assert "未找到符合" in result["message"]

    @pytest.mark.asyncio
    async def test_empty_symbol_handling(self):
        """Test empty symbol handling."""
        result = await cash_secured_put_strategy_tool(
            symbol="",
            capital_limit=50000
        )
        
        assert result["status"] == "error"
        assert "error" in result


class TestCSPParameterValidation:
    """Test suite for CSP parameter validation."""

    @pytest.mark.asyncio
    async def test_validate_csp_parameters_valid(self):
        """Test parameter validation with valid inputs."""
        result = await validate_csp_parameters(
            symbol="AAPL",
            purpose_type="income",
            duration="1w",
            capital_limit=50000
        )
        
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_csp_parameters_insufficient_capital(self):
        """Test parameter validation with insufficient capital."""
        result = await validate_csp_parameters(
            symbol="AAPL",
            purpose_type="income",
            duration="1w",
            capital_limit=500  # Too low
        )
        
        assert result["is_valid"] is True  # Warnings don't make it invalid
        assert any("资金限制过小" in warning for warning in result["warnings"])

    @pytest.mark.asyncio
    async def test_validate_csp_parameters_invalid_strategy_type(self):
        """Test parameter validation with invalid strategy type."""
        result = await validate_csp_parameters(
            symbol="AAPL",
            purpose_type="invalid",
            duration="1w",
            capital_limit=50000
        )
        
        assert result["is_valid"] is False
        assert any("目的类型必须是" in error for error in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_csp_parameters_empty_symbol(self):
        """Test parameter validation with empty symbol."""
        result = await validate_csp_parameters(
            symbol="",
            purpose_type="income",
            duration="1w",
            capital_limit=50000
        )
        
        assert result["is_valid"] is False
        assert any("股票代码不能为空" in error for error in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_csp_parameters_negative_values(self):
        """Test parameter validation with negative values."""
        result = await validate_csp_parameters(
            symbol="AAPL",
            purpose_type="income",
            duration="1w",
            capital_limit=-1000
        )
        
        assert result["is_valid"] is False
        assert any("资金限制必须大于0" in error for error in result["errors"])


class TestCSPUtilities:
    """Test suite for CSP utility functions."""

    def test_get_strategy_examples(self):
        """Test strategy examples retrieval."""
        examples = get_strategy_examples()
        
        assert "income_strategies" in examples
        assert "discount_strategies" in examples
        assert "usage_tips" in examples
        
        # Verify structure - check that income strategies exist
        income_strategies = examples["income_strategies"]
        assert "conservative_weekly" in income_strategies
        
        # Verify individual strategy structure
        conservative_strategy = income_strategies["conservative_weekly"]
        assert "description" in conservative_strategy
        assert "purpose_type" in conservative_strategy
        assert "duration" in conservative_strategy
        assert conservative_strategy["purpose_type"] == "income"

    def test_format_strategy_summary_success(self):
        """Test strategy summary formatting for successful result."""
        mock_result = {
            "status": "success",
            "symbol": "AAPL",
            "current_price": 150.25,
            "strategy_parameters": {
                "capital_limit": 50000,
                "purpose_type": "income",
                "duration": "1w"
            },
            "recommendations": {
                "conservative": {
                    "option_details": {"strike": 145.0},
                    "pnl_analysis": {
                        "annualized_return": 12.5,
                        "required_capital": 14500.0
                    },
                    "risk_metrics": {
                        "assignment_probability": 16.0
                    }
                },
                "balanced": {
                    "option_details": {"strike": 147.5},
                    "pnl_analysis": {
                        "annualized_return": 15.2,
                        "required_capital": 14750.0
                    },
                    "risk_metrics": {
                        "assignment_probability": 20.0
                    }
                }
            },
            "csv_export_path": "./data/csp_AAPL_test.csv"
        }
        
        summary = format_strategy_summary(mock_result)
        
        assert "AAPL 现金担保看跌期权策略分析" in summary
        assert "$150.25" in summary
        assert "income" in summary
        assert "保守" in summary
        assert "平衡" in summary

    def test_format_strategy_summary_failure(self):
        """Test strategy summary formatting for failed result."""
        mock_result = {
            "status": "insufficient_capital",
            "message": "资金不足以执行此策略"
        }
        
        summary = format_strategy_summary(mock_result)
        
        assert "策略分析失败" in summary
        assert "资金不足以执行此策略" in summary


class TestCSPIntegration:
    """Integration test suite for CSP strategy tool."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_workflow_mock_integration(self):
        """Test full workflow with realistic mock data."""
        # This test would use more realistic mock data to test the full integration
        # but without hitting external APIs
        
        with patch('src.mcp_server.tools.cash_secured_put_strategy_tool.TradierClient') as mock_client_class:
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
            
            # Mock the analyzer to return proper strike data instead of option contracts
            # (since the function expects the analyzer to process and return analyzed strikes)
            
            # Setup other required mocks
            with patch('src.mcp_server.tools.cash_secured_put_strategy_tool.CashSecuredPutAnalyzer') as mock_analyzer_class, \
                 patch('src.mcp_server.tools.cash_secured_put_strategy_tool.ExpirationSelector') as mock_exp, \
                 patch('src.mcp_server.tools.cash_secured_put_strategy_tool.StrategyRecommendationEngine') as mock_rec_engine_class, \
                 patch('src.mcp_server.tools.cash_secured_put_strategy_tool.ProfessionalOrderFormatter') as mock_formatter_class, \
                 patch('src.mcp_server.tools.cash_secured_put_strategy_tool.export_csp_analysis_to_csv') as mock_export, \
                 patch('src.mcp_server.tools.cash_secured_put_strategy_tool.get_market_context') as mock_context, \
                 patch('src.mcp_server.tools.cash_secured_put_strategy_tool.generate_execution_notes') as mock_notes:
                
                # Configure analyzer mock
                mock_analyzer = Mock()
                mock_analyzer_class.return_value = mock_analyzer
                mock_analyzer.delta_ranges = {"income": {"min": -0.30, "max": -0.10}}
                
                # Mock realistic analyzed options data
                optimal_strikes_data = [{
                    "symbol": "AAPL240119P00170000",
                    "strike_price": 170.0,
                    "delta": -0.25,
                    "premium": 3.30,
                    "assignment_probability": 0.20,
                    "composite_score": 88.5,
                    "required_capital": 17000.0
                }]
                mock_analyzer.find_optimal_strikes = AsyncMock(return_value=optimal_strikes_data)
                
                # Configure expiration selector
                mock_exp_instance = Mock()
                mock_exp.return_value = mock_exp_instance
                mock_exp_instance.get_optimal_expiration = AsyncMock(return_value=ExpirationSelectionResult(
                    selected_date="2024-01-19",
                    selection_reason="weekly expiration",
                    metadata={"actual_days": 14, "expiration_type": "weekly"},
                    alternatives=[]
                ))
                
                # Configure recommendation engine
                mock_rec_engine = Mock()
                mock_rec_engine_class.return_value = mock_rec_engine
                mock_recommendations = {
                    "conservative": {
                        "profile": "conservative",
                        "option_details": optimal_strikes_data[0],
                        "pnl_analysis": {
                            "premium_income": 330.0,
                            "max_profit": 330.0,
                            "annualized_return": 14.1,
                            "required_capital": 17000.0
                        },
                        "risk_metrics": {
                            "assignment_probability": 0.20,
                            "delta": -0.25
                        },
                        "recommendation_reasoning": "Conservative income strategy"
                    }
                }
                mock_rec_engine.generate_three_alternatives.return_value = mock_recommendations
                
                # Configure order formatter
                mock_formatter = Mock()
                mock_formatter_class.return_value = mock_formatter
                mock_formatter.format_order_block.return_value = "Mock Professional Order Block"
                
                # Configure other utilities
                mock_export.return_value = "./data/csp_AAPL_integration_test.csv"
                mock_context.return_value = {
                    "implied_volatility": 0.28,
                    "momentum_score": "neutral",
                    "volatility_regime": "normal"
                }
                mock_notes.return_value = "Mock execution notes"
                
                # Execute the tool
                result = await cash_secured_put_strategy_tool(
                    symbol="AAPL",
                    purpose_type="income",
                    duration="2w",
                    capital_limit=75000,
                    min_premium=2.0,
                    include_order_blocks=True
                )
                
                # Comprehensive verification
                assert result["status"] == "success"
                assert result["symbol"] == "AAPL"
                assert result["current_price"] == 175.50
                assert result["strategy_parameters"]["capital_limit"] == 75000
                assert result["strategy_parameters"]["purpose_type"] == "income"
                assert result["strategy_parameters"]["min_premium"] == 2.0
                assert result["selected_expiration"]["date"] == "2024-01-19"
                assert "disclaimer" in result
                
                # Verify CSV export was called
                mock_export.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])