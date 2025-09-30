"""
Tests for Income Generation CSP Engine MCP Server Prompt

测试收入生成现金担保看跌期权策略提示的各种功能：
- 参数验证
- 基础提示生成
- 边界条件处理
- 输出格式正确性
"""

import pytest
from unittest.mock import patch
from src.mcp_server.prompts.income_generation_csp_prompt import (
    income_generation_csp_engine,
    _validate_parameters,
    _generate_structured_prompt,
    get_income_csp_examples,
    get_usage_guidelines
)


class TestParameterValidation:
    """测试参数验证功能"""
    
    def test_valid_parameters(self):
        """测试有效参数验证"""
        result = _validate_parameters(
            tickers=["AAPL", "TSLA"],
            cash_usd=50000.0,
            target_apy_pct=50.0,
            min_winrate_pct=70.0,
            confidence_pct=90.0
        )

        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
    
    def test_empty_ticker_list(self):
        """测试空股票列表（应该被允许，使用默认值）"""
        result = _validate_parameters(
            tickers=[],
            cash_usd=50000.0,
            target_apy_pct=50.0,
            min_winrate_pct=70.0,
            confidence_pct=90.0
        )

        assert result["is_valid"] is True
    
    def test_invalid_cash_amount(self):
        """测试无效现金金额"""
        result = _validate_parameters(
            tickers=["AAPL"],
            cash_usd=-1000.0,
            target_apy_pct=50.0,
            min_winrate_pct=70.0,
            confidence_pct=90.0
        )

        assert result["is_valid"] is False
        assert "资金金额必须大于0" in result["errors"]

    def test_invalid_percentage_params(self):
        """测试无效百分比参数"""
        result = _validate_parameters(
            tickers=["AAPL"],
            cash_usd=50000.0,
            target_apy_pct=150.0,  # 超过100%
            min_winrate_pct=70.0,
            confidence_pct=90.0
        )

        assert result["is_valid"] is False
        assert any("目标年化收益率必须在0-100%之间" in error for error in result["errors"])
    
    def test_too_many_tickers(self):
        """测试过多股票代码"""
        long_ticker_list = [f"STOCK{i}" for i in range(15)]
        result = _validate_parameters(
            tickers=long_ticker_list,
            cash_usd=50000.0,
            target_apy_pct=50.0,
            min_winrate_pct=70.0,
            confidence_pct=90.0
        )

        assert result["is_valid"] is True
        assert "股票列表超过10个，将截取前10个" in result["warnings"]

    def test_small_cash_amount_warning(self):
        """测试小额现金警告"""
        result = _validate_parameters(
            tickers=["AAPL"],
            cash_usd=500.0,  # 小于1000
            target_apy_pct=50.0,
            min_winrate_pct=70.0,
            confidence_pct=90.0
        )

        assert result["is_valid"] is True
        assert "资金金额较小，可能无法找到合适的期权" in result["warnings"]


class TestPromptGeneration:
    """测试提示生成功能"""
    
    @pytest.mark.asyncio
    async def test_basic_prompt_generation(self):
        """测试基础提示生成"""
        prompt = await income_generation_csp_engine(
            tickers="AAPL",
            cash_usd=50000.0,
            target_apy_pct=50.0,
            min_winrate_pct=70.0,
            confidence_pct=90.0
        )

        # 验证提示包含关键部分
        assert "收入生成现金担保PUT策略引擎" in prompt
        assert "AAPL" in prompt
        assert "$50,000" in prompt
        assert "年化≥50.0%" in prompt
        assert "胜率≥70.0%" in prompt

        # 验证包含关键工具调用
        assert "get_market_time_tool()" in prompt
        assert "stock_info_tool" in prompt
        assert "cash_secured_put_strategy_tool_mcp" in prompt or "optimal_expiration_selector_tool_mcp" in prompt
        assert "options_chain_tool_mcp" in prompt
        assert "option_assignment_probability_tool_mcp" in prompt

        # 验证收入导向设置
        assert 'purpose_type="income"' in prompt
        assert "Delta" in prompt
    
    @pytest.mark.asyncio
    async def test_prompt_with_default_tickers(self):
        """测试使用默认股票列表的提示生成"""
        prompt = await income_generation_csp_engine(
            tickers="",
            cash_usd=100000.0
        )

        # 应该包含默认股票
        assert "SPY" in prompt
        assert "QQQ" in prompt
        assert "AAPL" in prompt
        assert "MSFT" in prompt
        assert "NVDA" in prompt

    @pytest.mark.asyncio
    async def test_prompt_with_many_tickers(self):
        """测试超过10个股票的情况"""
        many_tickers_str = " ".join([f"STOCK{i}" for i in range(15)])
        prompt = await income_generation_csp_engine(
            tickers=many_tickers_str,
            cash_usd=50000.0
        )

        # 应该只包含前10个
        ticker_count = 0
        for i in range(15):
            if f"STOCK{i}" in prompt:
                ticker_count += 1

        assert ticker_count <= 10

    @pytest.mark.asyncio
    async def test_invalid_parameters_raise_error(self):
        """测试无效参数抛出异常"""
        with pytest.raises(ValueError, match="参数验证失败"):
            await income_generation_csp_engine(
                tickers="AAPL",
                cash_usd=-1000.0  # 无效金额
            )
    
    def test_structured_prompt_content(self):
        """测试结构化提示内容"""
        prompt = _generate_structured_prompt(
            tickers=["AAPL", "TSLA"],
            tickers_str="AAPL, TSLA",
            primary_ticker="AAPL",
            cash_usd=50000.0,
            target_apy_pct=50.0,
            min_winrate_pct=70.0,
            confidence_pct=90.0
        )

        # 验证核心组件
        assert "策略目标" in prompt or "约束参数" in prompt
        assert "执行" in prompt
        assert "收入" in prompt or "优化" in prompt
        assert "输出" in prompt or "规格" in prompt

        # 验证风险控制特性
        assert "Delta" in prompt
        assert "分配" in prompt or "概率" in prompt


class TestHelperFunctions:
    """测试辅助函数"""
    
    def test_get_income_csp_examples(self):
        """测试获取策略示例"""
        examples = get_income_csp_examples()
        
        assert "conservative_income" in examples
        assert "balanced_income" in examples
        assert "aggressive_income" in examples
        
        # 验证保守策略示例
        conservative = examples["conservative_income"]
        assert conservative["example_call"]["target_apy_pct"] == 40
        assert conservative["example_call"]["min_winrate_pct"] == 80
    
    def test_get_usage_guidelines(self):
        """测试获取使用指导"""
        guidelines = get_usage_guidelines()
        
        assert isinstance(guidelines, list)
        assert len(guidelines) > 0
        
        # 验证包含关键指导原则
        guideline_text = " ".join(guidelines)
        assert "收入优先" in guideline_text
        assert "Delta控制" in guideline_text
        assert "快速周转" in guideline_text
        assert "高收益筛选" in guideline_text


class TestErrorHandling:
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_invalid_ticker_format(self):
        """测试无效股票代码格式 - 空字符串会使用默认股票列表"""
        # 空字符串不会抛出错误，而是使用默认股票列表
        prompt = await income_generation_csp_engine(
            tickers="",
            cash_usd=50000.0
        )
        assert "SPY" in prompt  # 应该包含默认股票

    @pytest.mark.asyncio
    async def test_zero_cash_amount(self):
        """测试零现金金额"""
        with pytest.raises(ValueError):
            await income_generation_csp_engine(
                tickers="AAPL",
                cash_usd=0.0
            )


class TestIntegrationScenarios:
    """测试集成场景"""

    @pytest.mark.asyncio
    async def test_conservative_income_scenario(self):
        """测试保守收入场景"""
        prompt = await income_generation_csp_engine(
            tickers="SPY QQQ",
            cash_usd=25000.0,
            target_apy_pct=40.0,
            min_winrate_pct=80.0,
            confidence_pct=95.0
        )

        assert "SPY" in prompt
        assert "QQQ" in prompt
        assert "$25,000" in prompt
        assert "年化≥40.0%" in prompt
        assert "胜率≥80.0%" in prompt
        assert "置信度≥95.0%" in prompt

    @pytest.mark.asyncio
    async def test_aggressive_income_scenario(self):
        """测试激进收入场景"""
        prompt = await income_generation_csp_engine(
            tickers="TSLA NVDA AMD",
            cash_usd=100000.0,
            target_apy_pct=60.0,
            min_winrate_pct=65.0,
            confidence_pct=85.0
        )

        assert "TSLA" in prompt
        assert "NVDA" in prompt
        assert "AMD" in prompt
        assert "$100,000" in prompt
        assert "年化≥60.0%" in prompt
        assert "胜率≥65.0%" in prompt
        assert "置信度≥85.0%" in prompt

    @pytest.mark.asyncio
    async def test_balanced_income_scenario(self):
        """测试平衡收入场景"""
        prompt = await income_generation_csp_engine(
            tickers="AAPL MSFT",
            cash_usd=50000.0,
            target_apy_pct=50.0,
            min_winrate_pct=70.0,
            confidence_pct=90.0
        )

        assert "AAPL" in prompt
        assert "MSFT" in prompt
        assert "$50,000" in prompt
        assert "年化≥50.0%" in prompt
        assert "胜率≥70.0%" in prompt
        assert "置信度≥90.0%" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])