"""
Tests for Stock Acquisition CSP Engine MCP Server Prompt

测试股票建仓现金担保看跌期权策略提示的各种功能：
- 参数验证
- 基础提示生成
- 股票代码解析
- 边界条件处理
- 输出格式正确性
- 与收入生成引擎的差异化
"""

import pytest
from unittest.mock import patch
from src.mcp_server.prompts.stock_acquisition_csp_prompt import (
    stock_acquisition_csp_engine,
    _validate_stock_acquisition_parameters,
    _generate_stock_acquisition_prompt,
    _get_duration_from_days,
    _parse_tickers_input,
    get_stock_acquisition_examples,
    get_usage_guidelines
)


class TestParameterValidation:
    """测试参数验证功能"""
    
    def test_valid_parameters(self):
        """测试有效参数验证"""
        result = _validate_stock_acquisition_parameters(
            tickers=["AAPL", "TSLA"],
            cash_usd=50000.0,
            target_allocation_probability=65.0,
            max_single_position_pct=25.0,
            min_days=21,
            max_days=60,
            target_annual_return_pct=25.0,
            preferred_sectors="Technology,Healthcare"
        )
        
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
    
    def test_empty_ticker_list(self):
        """测试空股票列表（应该被允许，使用默认值）"""
        result = _validate_stock_acquisition_parameters(
            tickers=[],
            cash_usd=50000.0,
            target_allocation_probability=65.0,
            max_single_position_pct=25.0,
            min_days=21,
            max_days=60,
            target_annual_return_pct=25.0,
            preferred_sectors=None
        )
        
        # 空列表应该被允许（会使用默认股票）
        assert result["is_valid"] is True
    
    def test_invalid_cash_amount(self):
        """测试无效的资金金额"""
        result = _validate_stock_acquisition_parameters(
            tickers=["AAPL"],
            cash_usd=-1000.0,  # 负数资金
            target_allocation_probability=65.0,
            max_single_position_pct=25.0,
            min_days=21,
            max_days=60,
            target_annual_return_pct=25.0,
            preferred_sectors=None
        )
        
        assert result["is_valid"] is False
        assert any("资金金额必须大于0" in error for error in result["errors"])
    
    def test_invalid_allocation_probability(self):
        """测试无效的分配概率"""
        result = _validate_stock_acquisition_parameters(
            tickers=["AAPL"],
            cash_usd=50000.0,
            target_allocation_probability=150.0,  # 超过100%
            max_single_position_pct=25.0,
            min_days=21,
            max_days=60,
            target_annual_return_pct=25.0,
            preferred_sectors=None
        )
        
        assert result["is_valid"] is False
        assert any("目标分配概率必须在0-100%" in error for error in result["errors"])
    
    def test_invalid_position_percentage(self):
        """测试无效的单仓位百分比"""
        result = _validate_stock_acquisition_parameters(
            tickers=["AAPL"],
            cash_usd=50000.0,
            target_allocation_probability=65.0,
            max_single_position_pct=150.0,  # 超过100%
            min_days=21,
            max_days=60,
            target_annual_return_pct=25.0,
            preferred_sectors=None
        )
        
        assert result["is_valid"] is False
        assert any("单股票仓位百分比必须在0-100%" in error for error in result["errors"])
    
    def test_invalid_days_range(self):
        """测试无效的天数范围"""
        result = _validate_stock_acquisition_parameters(
            tickers=["AAPL"],
            cash_usd=50000.0,
            target_allocation_probability=65.0,
            max_single_position_pct=25.0,
            min_days=60,  # min > max
            max_days=30,
            target_annual_return_pct=25.0,
            preferred_sectors=None
        )
        
        assert result["is_valid"] is False
        assert any("最小天数必须小于最大天数" in error for error in result["errors"])
    
    def test_warning_conditions(self):
        """测试警告条件"""
        result = _validate_stock_acquisition_parameters(
            tickers=["AAPL"] * 12,  # 过多股票
            cash_usd=5000.0,  # 资金较少
            target_allocation_probability=20.0,  # 分配概率较低
            max_single_position_pct=60.0,  # 单仓位过高
            min_days=5,  # 天数较短
            max_days=400,  # 天数过长
            target_annual_return_pct=60.0,  # 收益率过高
            preferred_sectors=None
        )
        
        assert result["is_valid"] is True  # 有警告但仍有效
        assert len(result["warnings"]) > 0


class TestTickersParsing:
    """测试股票代码解析功能"""
    
    def test_parse_json_string(self):
        """测试JSON字符串格式解析"""
        result = _parse_tickers_input('["AAPL", "MSFT", "GOOGL"]')
        assert result == ["AAPL", "MSFT", "GOOGL"]
    
    def test_parse_comma_separated(self):
        """测试逗号分隔格式解析"""
        result = _parse_tickers_input("AAPL,MSFT,GOOGL")
        assert result == ["AAPL", "MSFT", "GOOGL"]
    
    def test_parse_space_separated(self):
        """测试空格分隔格式解析"""
        result = _parse_tickers_input("AAPL MSFT GOOGL")
        assert result == ["AAPL", "MSFT", "GOOGL"]
    
    def test_parse_single_ticker(self):
        """测试单个股票代码解析"""
        result = _parse_tickers_input("AAPL")
        assert result == ["AAPL"]
    
    def test_parse_list_input(self):
        """测试列表输入直接返回"""
        result = _parse_tickers_input(["AAPL", "MSFT"])
        assert result == ["AAPL", "MSFT"]
    
    def test_parse_empty_string(self):
        """测试空字符串解析"""
        result = _parse_tickers_input("")
        assert result == []
    
    def test_parse_with_whitespace(self):
        """测试带空格的解析"""
        result = _parse_tickers_input(" AAPL , MSFT , GOOGL ")
        assert result == ["AAPL", "MSFT", "GOOGL"]


class TestDurationMapping:
    """测试天数到duration的映射"""
    
    def test_duration_mapping_1w(self):
        """测试1周映射"""
        assert _get_duration_from_days(5, 9) == "1w"
    
    def test_duration_mapping_2w(self):
        """测试2周映射"""
        assert _get_duration_from_days(10, 18) == "2w"
    
    def test_duration_mapping_1m(self):
        """测试1月映射"""
        assert _get_duration_from_days(21, 35) == "1m"
    
    def test_duration_mapping_3m(self):
        """测试3月映射"""
        assert _get_duration_from_days(60, 100) == "3m"
    
    def test_duration_mapping_6m(self):
        """测试6月映射"""
        assert _get_duration_from_days(150, 190) == "6m"
    
    def test_duration_mapping_1y(self):
        """测试1年映射"""
        assert _get_duration_from_days(300, 400) == "1y"


class TestPromptGeneration:
    """测试提示生成功能"""
    
    @pytest.mark.asyncio
    async def test_basic_prompt_generation(self):
        """测试基本提示生成"""
        result = await stock_acquisition_csp_engine(
            tickers="AAPL",
            cash_usd=50000.0,
            target_allocation_probability=65.0,
            min_days=21,
            max_days=60
        )
        
        # 验证核心内容存在
        assert "股票建仓现金担保PUT引擎" in result
        assert 'purpose_type="discount"' in result
        assert "分配概率≥65.0%" in result or "目标分配概率65.0%" in result
        assert "21~60" in result or "21-60" in result
        assert "50000" in result or "50,000" in result
    
    @pytest.mark.asyncio 
    async def test_multiple_tickers(self):
        """测试多股票提示生成"""
        result = await stock_acquisition_csp_engine(
            tickers="AAPL,MSFT,GOOGL",
            cash_usd=100000.0,
            target_allocation_probability=70.0
        )
        
        assert "AAPL" in result
        assert "MSFT" in result or "AAPL, MSFT, GOOGL" in result
        assert "分配概率≥70.0%" in result or "目标分配概率70.0%" in result
    
    @pytest.mark.asyncio
    async def test_default_parameters(self):
        """测试默认参数"""
        result = await stock_acquisition_csp_engine(
            tickers="TSLA",
            cash_usd=75000.0
        )
        
        # 验证默认值
        assert "分配概率≥65.0%" in result or "目标分配概率65.0%" in result
        assert "单股票≤25.0%" in result or "max_single_position_pct=25.0" in result
        assert "21~60" in result or "21-60" in result
        assert "年化补偿≥25.0%" in result or "target_annual_return_pct=25.0" in result
    
    @pytest.mark.asyncio
    async def test_preferred_sectors(self):
        """测试偏好行业参数"""
        result = await stock_acquisition_csp_engine(
            tickers="AAPL",
            cash_usd=50000.0,
            preferred_sectors="Technology,Healthcare,Finance"
        )
        
        assert "Technology,Healthcare,Finance" in result
    
    @pytest.mark.asyncio
    async def test_empty_tickers_uses_defaults(self):
        """测试空股票列表使用默认值"""
        result = await stock_acquisition_csp_engine(
            tickers="",
            cash_usd=50000.0
        )
        
        # 应该包含默认股票
        assert any(ticker in result for ticker in ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"])


class TestParameterValidationErrors:
    """测试参数验证错误处理"""
    
    @pytest.mark.asyncio
    async def test_invalid_parameters_raise_error(self):
        """测试无效参数抛出错误"""
        with pytest.raises(ValueError) as exc_info:
            await stock_acquisition_csp_engine(
                tickers="AAPL",
                cash_usd=-1000.0,  # 无效资金
                target_allocation_probability=150.0  # 无效概率
            )
        
        assert "参数验证失败" in str(exc_info.value)


class TestOutputFormat:
    """测试输出格式"""
    
    @pytest.mark.asyncio
    async def test_contains_required_sections(self):
        """测试包含必需的部分"""
        result = await stock_acquisition_csp_engine(
            tickers="AAPL",
            cash_usd=50000.0
        )
        
        # 验证关键部分存在
        required_sections = [
            "策略目标与约束参数",
            "关键执行原则", 
            "强制执行序列",
            "股票建仓专用筛选标准",
            "专业输出规格要求",
            "建仓执行管理触发器"
        ]
        
        for section in required_sections:
            assert section in result
    
    @pytest.mark.asyncio
    async def test_contains_tool_calls(self):
        """测试包含工具调用"""
        result = await stock_acquisition_csp_engine(
            tickers="AAPL",
            cash_usd=50000.0
        )
        
        # 验证关键工具调用存在
        required_tools = [
            "get_market_time_tool()",
            "stock_info_tool(",
            "cash_secured_put_strategy_tool_mcp(",
            "options_chain_tool_mcp(",
            "option_assignment_probability_tool_mcp(",
            "portfolio_optimization_tool_mcp_tool("
        ]
        
        for tool in required_tools:
            assert tool in result
    
    @pytest.mark.asyncio
    async def test_stock_acquisition_focus(self):
        """测试股票建仓重点"""
        result = await stock_acquisition_csp_engine(
            tickers="AAPL",
            cash_usd=50000.0
        )
        
        # 验证股票建仓特色
        acquisition_keywords = [
            "欢迎股票分配",
            "股票获取",
            "建仓",
            "折扣价",
            "耐心建仓",
            "0.30~0.50"
        ]
        
        for keyword in acquisition_keywords:
            assert keyword in result


class TestExamplesAndGuidelines:
    """测试示例和指导功能"""
    
    def test_get_examples(self):
        """测试获取示例"""
        examples = get_stock_acquisition_examples()
        
        assert isinstance(examples, dict)
        assert "conservative_acquisition" in examples
        assert "balanced_acquisition" in examples
        assert "aggressive_acquisition" in examples
        
        # 验证示例结构
        conservative = examples["conservative_acquisition"]
        assert "description" in conservative
        assert "example_call" in conservative
        assert "expected_outcome" in conservative
        assert "use_case" in conservative
    
    def test_get_usage_guidelines(self):
        """测试获取使用指导"""
        guidelines = get_usage_guidelines()
        
        assert isinstance(guidelines, list)
        assert len(guidelines) > 0
        
        # 验证包含股票建仓相关指导
        guidelines_text = " ".join(guidelines)
        assert "建仓" in guidelines_text
        assert "Delta" in guidelines_text


class TestDifferentiationFromIncomeEngine:
    """测试与收入生成引擎的差异化"""
    
    @pytest.mark.asyncio
    async def test_different_default_parameters(self):
        """测试不同的默认参数"""
        result = await stock_acquisition_csp_engine(
            tickers="AAPL",
            cash_usd=50000.0
        )
        
        # 股票建仓引擎的特有参数
        assert "分配概率≥65.0%" in result or "目标分配概率65.0%" in result
        assert "单股票≤25.0%" in result or "max_single_position_pct=25.0" in result
        assert "21~60" in result  # 更长的时间范围
        
        # 不应该有收入引擎的特征
        assert "避免分配" not in result
        assert "min_winrate_pct" not in result
    
    @pytest.mark.asyncio
    async def test_discount_purpose_type(self):
        """测试使用discount目的类型"""
        result = await stock_acquisition_csp_engine(
            tickers="AAPL",
            cash_usd=50000.0
        )
        
        # 必须使用discount模式
        assert 'purpose_type="discount"' in result
        # 不应该有income模式
        assert 'purpose_type="income"' not in result
    
    @pytest.mark.asyncio
    async def test_assignment_welcome_attitude(self):
        """测试欢迎分配的态度"""
        result = await stock_acquisition_csp_engine(
            tickers="AAPL",
            cash_usd=50000.0
        )
        
        # 应该体现欢迎分配的态度
        welcome_phrases = [
            "欢迎股票分配",
            "欢迎分配",
            "期望分配",
            "获得股票"
        ]
        
        assert any(phrase in result for phrase in welcome_phrases)