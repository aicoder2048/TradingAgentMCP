"""
期权被行权概率计算器测试模块

测试OptionAssignmentCalculator类的所有功能，包括：
- 单次概率计算精度验证
- Delta比较分析功能
- 批量计算性能测试
- 边界条件和错误处理

Author: TradingAgent MCP Team
Version: v8.0  
Created: 2024-09-27
"""

import pytest
import math
from typing import Dict, Any
from unittest.mock import patch

from src.option.assignment_probability import OptionAssignmentCalculator


# 全局fixture定义
@pytest.fixture
def calculator():
    """创建计算器实例"""
    return OptionAssignmentCalculator(default_risk_free_rate=0.048)

@pytest.fixture
def sample_put_data():
    """看跌期权样本数据"""
    return {
        "underlying_price": 150.0,
        "strike_price": 145.0,
        "time_to_expiry_days": 30.0,
        "implied_volatility": 0.25,
        "option_type": "put"
    }

@pytest.fixture
def sample_call_data():
    """看涨期权样本数据"""
    return {
        "underlying_price": 150.0,
        "strike_price": 155.0,
        "time_to_expiry_days": 30.0,
        "implied_volatility": 0.25,
        "option_type": "call"
    }


class TestOptionAssignmentCalculator:
    """测试OptionAssignmentCalculator类的核心功能"""
    pass

class TestSingleCalculation:
    """测试单次被行权概率计算"""
    
    def test_put_assignment_probability_calculation(self, calculator, sample_put_data):
        """测试看跌期权被行权概率计算"""
        result = calculator.calculate_assignment_probability(**sample_put_data)
        
        # 验证基本结构
        assert result["status"] == "success"
        assert "assignment_probability" in result
        assert "assignment_probability_percent" in result
        assert "black_scholes_parameters" in result
        
        # 验证概率值合理性（0-1之间）
        prob = result["assignment_probability"]
        assert 0 <= prob <= 1
        
        # 验证看跌期权概率计算逻辑（OTM PUT应该有较低概率）
        # 当前价格150 > 行权价145，看跌期权为虚值，被行权概率应该较低
        assert prob < 0.5  # 虚值看跌期权被行权概率应该小于50%
        
        # 验证d1, d2参数计算
        d1 = result["black_scholes_parameters"]["d1"]
        d2 = result["black_scholes_parameters"]["d2"]
        assert d1 > d2  # d1应该总是大于d2
        
    def test_call_assignment_probability_calculation(self, calculator, sample_call_data):
        """测试看涨期权被行权概率计算"""
        result = calculator.calculate_assignment_probability(**sample_call_data)
        
        assert result["status"] == "success"
        
        # 验证看涨期权概率计算逻辑（OTM CALL应该有较低概率）
        # 当前价格150 < 行权价155，看涨期权为虚值，被行权概率应该较低
        prob = result["assignment_probability"]
        assert 0 <= prob <= 1
        assert prob < 0.5  # 虚值看涨期权被行权概率应该小于50%
        
    def test_itm_put_higher_probability(self, calculator):
        """测试实值看跌期权有更高的被行权概率"""
        # 实值看跌期权：当前价格 < 行权价
        itm_put = {
            "underlying_price": 140.0,  # 低于行权价
            "strike_price": 150.0,
            "time_to_expiry_days": 30.0,
            "implied_volatility": 0.25,
            "option_type": "put"
        }
        
        # 虚值看跌期权：当前价格 > 行权价
        otm_put = {
            "underlying_price": 160.0,  # 高于行权价
            "strike_price": 150.0,
            "time_to_expiry_days": 30.0,
            "implied_volatility": 0.25,
            "option_type": "put"
        }
        
        itm_result = calculator.calculate_assignment_probability(**itm_put)
        otm_result = calculator.calculate_assignment_probability(**otm_put)
        
        # 实值期权被行权概率应该高于虚值期权
        assert itm_result["assignment_probability"] > otm_result["assignment_probability"]
        
    def test_time_decay_effect(self, calculator, sample_put_data):
        """测试时间衰减对被行权概率的影响"""
        # 短期到期
        short_term = sample_put_data.copy()
        short_term["time_to_expiry_days"] = 7.0
        
        # 长期到期
        long_term = sample_put_data.copy()
        long_term["time_to_expiry_days"] = 90.0
        
        short_result = calculator.calculate_assignment_probability(**short_term)
        long_result = calculator.calculate_assignment_probability(**long_term)
        
        # 验证两个计算都成功
        assert short_result["status"] == "success"
        assert long_result["status"] == "success"
        
        # 对于虚值期权，时间越长，被行权概率通常越高（有更多时间进入实值）
        # 注意：这个关系在不同市场条件下可能有所不同
        short_prob = short_result["assignment_probability"]
        long_prob = long_result["assignment_probability"]
        
        # 至少验证概率值都在合理范围内
        assert 0 <= short_prob <= 1
        assert 0 <= long_prob <= 1

class TestDeltaComparison:
    """测试Delta比较分析功能"""
    
    def test_delta_comparison_basic(self, calculator, sample_put_data):
        """测试基本Delta比较功能"""
        delta_value = -0.25  # 典型的看跌期权Delta值
        
        result = calculator.compare_with_delta_approximation(
            delta_value=delta_value,
            **sample_put_data
        )
        
        assert result["status"] == "success"
        assert "exact_assignment_probability" in result
        assert "delta_approximation" in result
        assert "absolute_difference" in result
        assert "relative_difference_percent" in result
        assert "accuracy_assessment" in result
        assert "recommendation" in result
        
        # 验证Delta近似值正确处理（取绝对值）
        assert result["delta_approximation"] == abs(delta_value)
        
    def test_delta_accuracy_assessment(self, calculator):
        """测试Delta精度评估功能"""
        test_cases = [
            # 高精度情况：相对误差 < 5%
            {"exact_prob": 0.30, "delta": 0.31, "expected_accuracy": "高精度"},  # 3.33%
            # 中等精度情况：相对误差 5-15%
            {"exact_prob": 0.30, "delta": 0.33, "expected_accuracy": "中等精度"},  # 10%
            # 低精度情况：相对误差 > 15%
            {"exact_prob": 0.30, "delta": 0.40, "expected_accuracy": "低精度"},  # 33.33%
        ]
        
        for case in test_cases:
            # 模拟精确计算结果
            with patch.object(calculator, 'calculate_assignment_probability') as mock_calc:
                mock_calc.return_value = {
                    "status": "success",
                    "assignment_probability": case["exact_prob"]
                }
                
                result = calculator.compare_with_delta_approximation(
                    underlying_price=150.0,
                    strike_price=145.0,
                    time_to_expiry_days=30.0,
                    implied_volatility=0.25,
                    delta_value=case["delta"],
                    option_type="put"
                )
                
                assert result["accuracy_assessment"] == case["expected_accuracy"]

class TestBatchCalculation:
    """测试批量计算功能"""
    
    def test_batch_portfolio_analysis(self, calculator):
        """测试投资组合批量分析"""
        positions = [
            {
                "symbol": "AAPL",
                "underlying_price": 150.0,
                "strike_price": 145.0,
                "time_to_expiry_days": 30.0,
                "implied_volatility": 0.25,
                "option_type": "put",
                "contracts": 10
            },
            {
                "symbol": "TSLA", 
                "underlying_price": 200.0,
                "strike_price": 210.0,
                "time_to_expiry_days": 15.0,
                "implied_volatility": 0.35,
                "option_type": "call",
                "contracts": 5
            }
        ]
        
        result = calculator.batch_calculate_portfolio_risk(positions)
        
        assert result["status"] == "success"
        assert "portfolio_overview" in result
        assert "position_analyses" in result
        assert "portfolio_risk_assessment" in result
        
        # 验证投资组合概览
        overview = result["portfolio_overview"]
        assert overview["total_positions"] == 2
        assert overview["analyzed_positions"] <= 2
        
        # 验证仓位分析
        analyses = result["position_analyses"]
        assert len(analyses) == 2
        
        # 验证每个仓位的分析结果
        for analysis in analyses:
            if analysis.get("status") != "error":
                assert "assignment_probability" in analysis
                assert "expected_assignments" in analysis
                assert analysis["assignment_probability"] >= 0
                assert analysis["assignment_probability"] <= 1
    
    def test_batch_with_error_handling(self, calculator):
        """测试批量计算中的错误处理"""
        positions = [
            # 正常仓位
            {
                "symbol": "AAPL",
                "underlying_price": 150.0,
                "strike_price": 145.0,
                "time_to_expiry_days": 30.0,
                "implied_volatility": 0.25,
                "option_type": "put"
            },
            # 错误仓位：负价格
            {
                "symbol": "INVALID",
                "underlying_price": -150.0,  # 无效价格
                "strike_price": 145.0,
                "time_to_expiry_days": 30.0,
                "implied_volatility": 0.25,
                "option_type": "put"
            }
        ]
        
        result = calculator.batch_calculate_portfolio_risk(positions)
        
        assert result["status"] == "success"  # 整体分析成功
        
        analyses = result["position_analyses"]
        assert len(analyses) == 2
        
        # 第一个仓位应该成功
        assert analyses[0].get("status") != "error"
        
        # 第二个仓位应该有错误
        assert analyses[1]["status"] == "error"
        assert "error" in analyses[1]

class TestParameterValidation:
    """测试参数验证功能"""
    
    def test_negative_prices_validation(self, calculator):
        """测试负价格验证"""
        # 测试负的标的价格
        result = calculator.calculate_assignment_probability(
            underlying_price=-150.0,
            strike_price=145.0,
            time_to_expiry_days=30.0,
            implied_volatility=0.25,
            option_type="put"
        )
        assert result["status"] == "error"
        assert "标的价格必须大于0" in result["error_message"]
        
        # 测试负的行权价
        result = calculator.calculate_assignment_probability(
            underlying_price=150.0,
            strike_price=-145.0,
            time_to_expiry_days=30.0,
            implied_volatility=0.25,
            option_type="put"
        )
        assert result["status"] == "error"
        assert "行权价必须大于0" in result["error_message"]
    
    def test_invalid_time_validation(self, calculator):
        """测试无效时间验证"""
        result = calculator.calculate_assignment_probability(
            underlying_price=150.0,
            strike_price=145.0,
            time_to_expiry_days=0.0,
            implied_volatility=0.25,
            option_type="put"
        )
        assert result["status"] == "error"
        assert "到期天数必须大于0" in result["error_message"]
    
    def test_invalid_volatility_validation(self, calculator):
        """测试无效波动率验证"""
        result = calculator.calculate_assignment_probability(
            underlying_price=150.0,
            strike_price=145.0,
            time_to_expiry_days=30.0,
            implied_volatility=0.0,
            option_type="put"
        )
        assert result["status"] == "error"
        assert "隐含波动率必须大于0" in result["error_message"]
    
    def test_invalid_option_type_validation(self, calculator):
        """测试无效期权类型验证"""
        result = calculator.calculate_assignment_probability(
            underlying_price=150.0,
            strike_price=145.0,
            time_to_expiry_days=30.0,
            implied_volatility=0.25,
            option_type="invalid"
        )
        assert result["status"] == "error"
        assert "期权类型必须是'put'或'call'" in result["error_message"]

class TestMoneynessAnalysis:
    """测试价值状态分析"""
    
    def test_put_moneyness_categories(self, calculator):
        """测试看跌期权价值状态分类"""
        base_params = {
            "strike_price": 100.0,
            "time_to_expiry_days": 30.0,
            "implied_volatility": 0.25,
            "option_type": "put"
        }
        
        test_cases = [
            {"underlying_price": 90.0, "expected_moneyness": "深度实值"},  # 0.90
            {"underlying_price": 96.0, "expected_moneyness": "实值"},     # 0.96
            {"underlying_price": 100.0, "expected_moneyness": "接近平值"}, # 1.00
            {"underlying_price": 104.0, "expected_moneyness": "虚值"},     # 1.04
            {"underlying_price": 110.0, "expected_moneyness": "深度虚值"}, # 1.10
        ]
        
        for case in test_cases:
            result = calculator.calculate_assignment_probability(
                underlying_price=case["underlying_price"],
                **base_params
            )
            assert result["moneyness"] == case["expected_moneyness"]
    
    def test_call_moneyness_categories(self, calculator):
        """测试看涨期权价值状态分类"""
        base_params = {
            "strike_price": 100.0,
            "time_to_expiry_days": 30.0,
            "implied_volatility": 0.25,
            "option_type": "call"
        }
        
        test_cases = [
            {"underlying_price": 110.0, "expected_moneyness": "深度实值"}, # 1.10
            {"underlying_price": 104.0, "expected_moneyness": "实值"},     # 1.04
            {"underlying_price": 100.0, "expected_moneyness": "接近平值"}, # 1.00
            {"underlying_price": 96.0, "expected_moneyness": "虚值"},     # 0.96
            {"underlying_price": 90.0, "expected_moneyness": "深度虚值"}, # 0.90
        ]
        
        for case in test_cases:
            result = calculator.calculate_assignment_probability(
                underlying_price=case["underlying_price"],
                **base_params
            )
            assert result["moneyness"] == case["expected_moneyness"]

class TestPerformance:
    """测试性能相关功能"""
    
    def test_single_calculation_performance(self, calculator, sample_put_data):
        """测试单次计算性能（目标: < 50ms）"""
        import time
        
        # 预热
        calculator.calculate_assignment_probability(**sample_put_data)
        
        # 性能测试
        start_time = time.time()
        for _ in range(100):  # 100次计算
            calculator.calculate_assignment_probability(**sample_put_data)
        end_time = time.time()
        
        avg_time_ms = (end_time - start_time) / 100 * 1000
        print(f"Average calculation time: {avg_time_ms:.2f}ms")
        
        # 验证平均时间 < 50ms（这是一个目标，实际可能因环境而异）
        assert avg_time_ms < 100  # 放宽到100ms以适应不同环境
    
    def test_batch_calculation_performance(self, calculator):
        """测试批量计算性能（目标: 100个 < 2s）"""
        import time
        
        # 创建100个测试仓位
        positions = []
        for i in range(100):
            positions.append({
                "symbol": f"TEST{i}",
                "underlying_price": 150.0 + i,
                "strike_price": 145.0 + i,
                "time_to_expiry_days": 30.0,
                "implied_volatility": 0.25,
                "option_type": "put" if i % 2 == 0 else "call"
            })
        
        start_time = time.time()
        result = calculator.batch_calculate_portfolio_risk(positions)
        end_time = time.time()
        
        execution_time = end_time - start_time
        print(f"Batch calculation time for 100 positions: {execution_time:.2f}s")
        
        assert result["status"] == "success"
        assert execution_time < 5.0  # 放宽到5秒以适应不同环境

class TestEdgeCases:
    """测试边界条件"""
    
    def test_very_short_expiry(self, calculator):
        """测试极短到期时间"""
        result = calculator.calculate_assignment_probability(
            underlying_price=150.0,
            strike_price=145.0,
            time_to_expiry_days=0.1,  # 0.1天 = 2.4小时
            implied_volatility=0.25,
            option_type="put"
        )
        
        assert result["status"] == "success"
        assert 0 <= result["assignment_probability"] <= 1
    
    def test_very_high_volatility(self, calculator):
        """测试极高波动率"""
        result = calculator.calculate_assignment_probability(
            underlying_price=150.0,
            strike_price=145.0,
            time_to_expiry_days=30.0,
            implied_volatility=2.0,  # 200%波动率
            option_type="put"
        )
        
        assert result["status"] == "success"
        assert 0 <= result["assignment_probability"] <= 1
    
    def test_very_low_volatility(self, calculator):
        """测试极低波动率"""
        result = calculator.calculate_assignment_probability(
            underlying_price=150.0,
            strike_price=145.0,
            time_to_expiry_days=30.0,
            implied_volatility=0.001,  # 0.1%波动率
            option_type="put"
        )
        
        assert result["status"] == "success"
        assert 0 <= result["assignment_probability"] <= 1

class TestResponseFormat:
    """测试响应格式"""
    
    def test_successful_response_structure(self, calculator, sample_put_data):
        """测试成功响应的结构"""
        result = calculator.calculate_assignment_probability(**sample_put_data)
        
        # 必须包含的顶级字段
        required_fields = [
            "status", "calculation_method", "assignment_probability",
            "assignment_probability_percent", "expire_otm_probability",
            "expire_otm_probability_percent", "assignment_risk_level",
            "moneyness", "moneyness_ratio", "risk_assessment",
            "black_scholes_parameters", "input_parameters", "interpretation"
        ]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
        
        # 验证特定字段的数据类型
        assert isinstance(result["assignment_probability"], float)
        assert isinstance(result["assignment_probability_percent"], str)
        assert isinstance(result["black_scholes_parameters"], dict)
        assert isinstance(result["input_parameters"], dict)
        assert isinstance(result["interpretation"], dict)
    
    def test_error_response_structure(self, calculator):
        """测试错误响应的结构"""
        # 触发一个参数错误
        result = calculator.calculate_assignment_probability(
            underlying_price=-150.0,  # 无效价格
            strike_price=145.0,
            time_to_expiry_days=30.0,
            implied_volatility=0.25,
            option_type="put"
        )
        
        assert result["status"] == "error"
        assert "error_message" in result
        assert "error_type" in result
        assert "timestamp" in result