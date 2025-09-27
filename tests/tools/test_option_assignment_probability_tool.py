"""
期权被行权概率MCP工具测试

测试option_assignment_probability_tool的MCP工具功能，
包括参数验证、API集成和响应格式验证。

Author: TradingAgent MCP Team
Version: v8.0
Created: 2024-09-27
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from src.mcp_server.tools.option_assignment_probability_tool import option_assignment_probability_tool


@pytest.fixture
def mock_tradier_client():
    """创建模拟的Tradier客户端"""
    mock_client = MagicMock()
    
    # 模拟股票报价
    mock_quote = MagicMock()
    mock_quote.last = 150.0
    mock_client.get_quotes.return_value = [mock_quote]
    
    # 模拟期权合约
    mock_option = MagicMock()
    mock_option.option_type = "put"
    mock_option.strike = 145.0
    mock_option.bid = 2.0
    mock_option.ask = 2.2
    mock_option.volume = 100
    mock_option.open_interest = 500
    mock_option.symbol = "AAPL241019P00145000"
    mock_option.greeks = {
        "delta": -0.25,
        "mid_iv": 0.22
    }
    
    mock_client.get_option_chain_enhanced.return_value = [mock_option]
    
    return mock_client


@pytest.fixture
def mock_calculator():
    """创建模拟的概率计算器"""
    mock_calc = MagicMock()
    
    # 模拟精确概率计算结果
    mock_calc.calculate_assignment_probability.return_value = {
        "status": "success",
        "assignment_probability": 0.28,
        "assignment_probability_percent": "28.00%",
        "expire_otm_probability": 0.72,
        "expire_otm_probability_percent": "72.00%",
        "assignment_risk_level": "中等",
        "moneyness": "虚值",
        "moneyness_ratio": 1.0345,
        "risk_assessment": "低",
        "interpretation": {
            "assignment_probability_meaning": "到期时期权处于实值被行权的概率为 28.00%",
            "risk_explanation": "基于当前参数，该期权的被行权风险评级为：中等",
            "moneyness_explanation": "当前期权状态为：虚值（股价/行权价比率：1.0345）"
        }
    }
    
    # 模拟Delta比较结果
    mock_calc.compare_with_delta_approximation.return_value = {
        "status": "success",
        "exact_assignment_probability": 0.28,
        "delta_approximation": 0.25,
        "absolute_difference": 0.03,
        "relative_difference_percent": 10.7,
        "accuracy_assessment": "中等精度",
        "recommendation": "建议使用精确计算"
    }
    
    return mock_calc


class TestOptionAssignmentProbabilityTool:
    """测试期权被行权概率MCP工具"""
    
    @pytest.mark.asyncio
    async def test_successful_put_calculation(self, mock_tradier_client, mock_calculator):
        """测试成功的看跌期权概率计算"""
        
        with patch('src.mcp_server.tools.option_assignment_probability_tool.TradierClient', return_value=mock_tradier_client), \
             patch('src.mcp_server.tools.option_assignment_probability_tool.OptionAssignmentCalculator', return_value=mock_calculator), \
             patch('src.mcp_server.tools.option_assignment_probability_tool.get_market_time_et', return_value="2024-09-27 14:30:00 ET"):
            
            result = await option_assignment_probability_tool(
                symbol="AAPL",
                strike_price=145.0,
                expiration="2024-10-19",
                option_type="put",
                include_delta_comparison=True
            )
        
        # 验证基本结构
        assert result["status"] == "success"
        assert result["symbol"] == "AAPL"
        assert result["current_price"] == 150.0
        assert result["strike_price"] == 145.0
        assert result["option_type"] == "PUT"
        assert result["expiration"] == "2024-10-19"
        
        # 验证核心计算结果
        assert "black_scholes_calculation" in result
        bs_calc = result["black_scholes_calculation"]
        assert bs_calc["assignment_probability"] == 0.28
        assert bs_calc["assignment_risk_level"] == "中等"
        
        # 验证Delta比较
        assert "delta_comparison" in result
        delta_comp = result["delta_comparison"]
        assert delta_comp["exact_assignment_probability"] == 0.28
        assert delta_comp["delta_approximation"] == 0.25
        
        # 验证响应完整性
        assert "option_details" in result
        assert "market_context" in result
        assert "risk_analysis" in result
        assert "technical_info" in result
    
    @pytest.mark.asyncio
    async def test_call_option_calculation(self, mock_tradier_client, mock_calculator):
        """测试看涨期权概率计算"""
        
        # 调整模拟数据为看涨期权
        mock_option = mock_tradier_client.get_option_chain_enhanced.return_value[0]
        mock_option.option_type = "call"
        mock_option.strike = 155.0
        mock_option.greeks["delta"] = 0.30
        
        with patch('src.mcp_server.tools.option_assignment_probability_tool.TradierClient', return_value=mock_tradier_client), \
             patch('src.mcp_server.tools.option_assignment_probability_tool.OptionAssignmentCalculator', return_value=mock_calculator), \
             patch('src.mcp_server.tools.option_assignment_probability_tool.get_market_time_et', return_value="2024-09-27 14:30:00 ET"):
            
            result = await option_assignment_probability_tool(
                symbol="AAPL",
                strike_price=155.0,
                expiration="2024-10-19",
                option_type="call"
            )
        
        assert result["status"] == "success"
        assert result["option_type"] == "CALL"
        assert result["strike_price"] == 155.0
    
    @pytest.mark.asyncio
    async def test_without_delta_comparison(self, mock_tradier_client, mock_calculator):
        """测试不包含Delta比较的情况"""
        
        with patch('src.mcp_server.tools.option_assignment_probability_tool.TradierClient', return_value=mock_tradier_client), \
             patch('src.mcp_server.tools.option_assignment_probability_tool.OptionAssignmentCalculator', return_value=mock_calculator), \
             patch('src.mcp_server.tools.option_assignment_probability_tool.get_market_time_et', return_value="2024-09-27 14:30:00 ET"):
            
            result = await option_assignment_probability_tool(
                symbol="AAPL",
                strike_price=145.0,
                expiration="2024-10-19",
                option_type="put",
                include_delta_comparison=False
            )
        
        assert result["status"] == "success"
        assert result["delta_comparison"] is None
    
    @pytest.mark.asyncio
    async def test_invalid_option_type(self):
        """测试无效期权类型的处理"""
        
        result = await option_assignment_probability_tool(
            symbol="AAPL",
            strike_price=145.0,
            expiration="2024-10-19",
            option_type="invalid"
        )
        
        assert result["status"] == "error"
        assert result["error"] == "invalid_option_type"
        assert "期权类型必须是 'put' 或 'call'" in result["message"]
    
    @pytest.mark.asyncio
    async def test_invalid_strike_price(self):
        """测试无效行权价的处理"""
        
        result = await option_assignment_probability_tool(
            symbol="AAPL",
            strike_price=-145.0,
            expiration="2024-10-19",
            option_type="put"
        )
        
        assert result["status"] == "error"
        assert result["error"] == "invalid_strike_price"
        assert "行权价必须大于0" in result["message"]
    
    @pytest.mark.asyncio
    async def test_no_quote_data(self, mock_calculator):
        """测试无股票报价数据的情况"""
        
        mock_client = MagicMock()
        mock_client.get_quotes.return_value = []  # 空的报价数据
        
        with patch('src.mcp_server.tools.option_assignment_probability_tool.TradierClient', return_value=mock_client), \
             patch('src.mcp_server.tools.option_assignment_probability_tool.OptionAssignmentCalculator', return_value=mock_calculator), \
             patch('src.mcp_server.tools.option_assignment_probability_tool.get_market_time_et', return_value="2024-09-27 14:30:00 ET"):
            
            result = await option_assignment_probability_tool(
                symbol="AAPL",
                strike_price=145.0,
                expiration="2024-10-19",
                option_type="put"
            )
        
        assert result["status"] == "error"
        assert result["error"] == "no_quote_data"
        assert "无法获取" in result["message"]
    
    @pytest.mark.asyncio
    async def test_no_option_data(self, mock_calculator):
        """测试无期权数据的情况"""
        
        mock_client = MagicMock()
        mock_quote = MagicMock()
        mock_quote.last = 150.0
        mock_client.get_quotes.return_value = [mock_quote]
        mock_client.get_option_chain_enhanced.return_value = []  # 空的期权数据
        
        with patch('src.mcp_server.tools.option_assignment_probability_tool.TradierClient', return_value=mock_client), \
             patch('src.mcp_server.tools.option_assignment_probability_tool.OptionAssignmentCalculator', return_value=mock_calculator), \
             patch('src.mcp_server.tools.option_assignment_probability_tool.get_market_time_et', return_value="2024-09-27 14:30:00 ET"):
            
            result = await option_assignment_probability_tool(
                symbol="AAPL",
                strike_price=145.0,
                expiration="2024-10-19",
                option_type="put"
            )
        
        assert result["status"] == "error"
        assert result["error"] == "no_option_data"
        assert "无法获取" in result["message"]
    
    @pytest.mark.asyncio
    async def test_option_not_found(self, mock_calculator):
        """测试找不到匹配期权合约的情况"""
        
        mock_client = MagicMock()
        mock_quote = MagicMock()
        mock_quote.last = 150.0
        mock_client.get_quotes.return_value = [mock_quote]
        
        # 创建不匹配的期权合约
        mock_option = MagicMock()
        mock_option.option_type = "put"
        mock_option.strike = 140.0  # 不匹配的行权价
        mock_client.get_option_chain_enhanced.return_value = [mock_option]
        
        with patch('src.mcp_server.tools.option_assignment_probability_tool.TradierClient', return_value=mock_client), \
             patch('src.mcp_server.tools.option_assignment_probability_tool.OptionAssignmentCalculator', return_value=mock_calculator), \
             patch('src.mcp_server.tools.option_assignment_probability_tool.get_market_time_et', return_value="2024-09-27 14:30:00 ET"):
            
            result = await option_assignment_probability_tool(
                symbol="AAPL",
                strike_price=145.0,
                expiration="2024-10-19",
                option_type="put"
            )
        
        assert result["status"] == "error"
        assert result["error"] == "option_not_found"
        assert "未找到" in result["message"]
        assert "available_strikes" in result
    
    @pytest.mark.asyncio
    async def test_invalid_expiration_format(self, mock_tradier_client, mock_calculator):
        """测试无效到期日格式的处理"""
        
        with patch('src.mcp_server.tools.option_assignment_probability_tool.TradierClient', return_value=mock_tradier_client), \
             patch('src.mcp_server.tools.option_assignment_probability_tool.OptionAssignmentCalculator', return_value=mock_calculator), \
             patch('src.mcp_server.tools.option_assignment_probability_tool.get_market_time_et', return_value="2024-09-27 14:30:00 ET"):
            
            result = await option_assignment_probability_tool(
                symbol="AAPL",
                strike_price=145.0,
                expiration="invalid-date",
                option_type="put"
            )
        
        assert result["status"] == "error"
        assert result["error"] == "invalid_expiration_format"
        assert "到期日格式必须为 YYYY-MM-DD" in result["message"]
    
    @pytest.mark.asyncio
    async def test_calculation_error(self, mock_tradier_client):
        """测试计算过程中的错误处理"""
        
        # 创建会产生错误的计算器
        mock_calc = MagicMock()
        mock_calc.calculate_assignment_probability.return_value = {
            "status": "error",
            "error_message": "计算参数错误"
        }
        
        with patch('src.mcp_server.tools.option_assignment_probability_tool.TradierClient', return_value=mock_tradier_client), \
             patch('src.mcp_server.tools.option_assignment_probability_tool.OptionAssignmentCalculator', return_value=mock_calc), \
             patch('src.mcp_server.tools.option_assignment_probability_tool.get_market_time_et', return_value="2024-09-27 14:30:00 ET"):
            
            result = await option_assignment_probability_tool(
                symbol="AAPL",
                strike_price=145.0,
                expiration="2024-10-19",
                option_type="put"
            )
        
        assert result["status"] == "error"
        assert result["error"] == "calculation_error"
        assert "计算参数错误" in result["message"]
    
    @pytest.mark.asyncio  
    async def test_csv_export_functionality(self, mock_tradier_client, mock_calculator):
        """测试CSV导出功能"""
        
        with patch('src.mcp_server.tools.option_assignment_probability_tool.TradierClient', return_value=mock_tradier_client), \
             patch('src.mcp_server.tools.option_assignment_probability_tool.OptionAssignmentCalculator', return_value=mock_calculator), \
             patch('src.mcp_server.tools.option_assignment_probability_tool.get_market_time_et', return_value="2024-09-27 14:30:00 ET"), \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open') as mock_open:
            
            result = await option_assignment_probability_tool(
                symbol="AAPL",
                strike_price=145.0,
                expiration="2024-10-19",
                option_type="put"
            )
        
        assert result["status"] == "success"
        assert "csv_export_path" in result
        
        # 验证CSV导出路径格式
        expected_filename = "assignment_prob_AAPL_145.0P_20241019.csv"
        expected_path = f"./data/{expected_filename}"
        assert result["csv_export_path"] == expected_path
        
        # 验证目录创建被调用
        mock_makedirs.assert_called_with("./data", exist_ok=True)