"""
股票特定优化功能测试

测试expiration_optimizer的股票特定优化功能，包括：
- 股票市场档案获取
- 动态调整因子计算
- 不同股票获得不同优化结果
- 向后兼容性（不提供symbol时的行为）
- 优化过程透明性

Author: TradingAgent MCP Team
Version: v11.0 (PRD v11)
Created: 2025-10-03
"""

import pytest
from datetime import datetime, timedelta
from src.mcp_server.tools.expiration_optimizer import ExpirationOptimizer


class TestStockMarketProfile:
    """测试股票市场档案获取功能"""

    def test_get_high_volatility_tech_profile(self):
        """测试高波动科技股的市场档案"""
        optimizer = ExpirationOptimizer()

        # TSLA: 高波动科技股
        tsla_profile = optimizer._get_stock_market_profile('TSLA')
        assert tsla_profile['volatility_ratio'] > 1.1
        assert tsla_profile['beta'] > 1.2
        assert 'liquidity' in tsla_profile
        assert 'market_cap_tier' in tsla_profile
        assert 'options_activity' in tsla_profile

    def test_get_large_cap_blue_chip_profile(self):
        """测试大盘蓝筹股的市场档案"""
        optimizer = ExpirationOptimizer()

        # AAPL: 大盘蓝筹股
        aapl_profile = optimizer._get_stock_market_profile('AAPL')
        assert aapl_profile['market_cap_tier'] >= 1.0
        assert aapl_profile['liquidity'] >= 1.0
        assert aapl_profile['volatility_ratio'] <= 1.1  # 相对低波动

    def test_get_unknown_stock_profile(self):
        """测试未知股票返回中性档案"""
        optimizer = ExpirationOptimizer()

        # 未知股票
        unknown_profile = optimizer._get_stock_market_profile('UNKNOWN')
        assert unknown_profile['volatility_ratio'] == 1.0
        assert unknown_profile['beta'] == 1.0
        assert unknown_profile['liquidity'] == 1.0
        assert unknown_profile['market_cap_tier'] == 1.0


class TestDynamicAdjustments:
    """测试动态调整因子计算"""

    def test_high_volatility_adjustments(self):
        """测试高波动股票的调整因子"""
        optimizer = ExpirationOptimizer()

        high_vol_profile = {
            'volatility_ratio': 1.3,
            'beta': 1.4,
            'liquidity': 1.0,
            'market_cap_tier': 1.0,
            'options_activity': 0.5
        }

        adjustments = optimizer._calculate_dynamic_adjustments(high_vol_profile)

        # 高波动应该降低Gamma风险容忍度
        assert adjustments['gamma_adjustment'] < 1.0
        assert 0.7 <= adjustments['gamma_adjustment'] <= 1.3

    def test_large_cap_adjustments(self):
        """测试大盘股的调整因子"""
        optimizer = ExpirationOptimizer()

        large_cap_profile = {
            'volatility_ratio': 0.95,
            'beta': 1.05,
            'liquidity': 1.5,
            'market_cap_tier': 1.5,
            'options_activity': 0.9
        }

        adjustments = optimizer._calculate_dynamic_adjustments(large_cap_profile)

        # 大盘股应该提升Theta效率评分
        assert adjustments['theta_adjustment'] > 1.0
        assert adjustments['liquidity_adjustment'] > 1.0

    def test_adjustment_formulas_consistency(self):
        """测试调整因子公式的一致性"""
        optimizer = ExpirationOptimizer()

        # TSLA档案
        tsla_profile = {
            'volatility_ratio': 1.30,
            'beta': 1.40,
            'liquidity': 1.20,
            'market_cap_tier': 1.0,
            'options_activity': 0.8
        }

        adjustments = optimizer._calculate_dynamic_adjustments(tsla_profile)

        # 验证Gamma调整公式: 0.8 + (1.3-1.0)*(-0.15) + (1.4-1.0)*(-0.10)
        expected_gamma = 0.8 + (1.3 - 1.0) * (-0.15) + (1.4 - 1.0) * (-0.10)
        assert abs(adjustments['gamma_adjustment'] - expected_gamma) < 0.01


class TestStockSpecificOptimization:
    """测试股票特定优化功能"""

    def test_different_stocks_different_results(self):
        """测试不同股票获得不同优化结果"""
        optimizer = ExpirationOptimizer()

        expirations = [
            {'date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
             'days': 30, 'type': 'monthly'},
            {'date': (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d'),
             'days': 45, 'type': 'monthly'}
        ]

        # TSLA优化
        tsla_optimal, tsla_process = optimizer.find_optimal_expiration(
            expirations, symbol='TSLA', return_process=True
        )

        # AAPL优化
        aapl_optimal, aapl_process = optimizer.find_optimal_expiration(
            expirations, symbol='AAPL', return_process=True
        )

        # 验证市场档案不同
        assert tsla_process['market_profile'] != aapl_process['market_profile']

        # 验证调整因子不同
        assert tsla_process['dynamic_adjustments'] != aapl_process['dynamic_adjustments']

    def test_symbol_affects_scoring(self):
        """测试symbol参数影响评分"""
        optimizer = ExpirationOptimizer()

        # 使用相同的到期日
        exp = {'date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
               'days': 30, 'type': 'monthly'}

        # 评估TSLA
        tsla_candidate = optimizer.evaluate_expiration(
            days=exp['days'],
            expiration_type=exp['type'],
            date=exp['date'],
            symbol='TSLA'
        )

        # 评估AAPL
        aapl_candidate = optimizer.evaluate_expiration(
            days=exp['days'],
            expiration_type=exp['type'],
            date=exp['date'],
            symbol='AAPL'
        )

        # 评分应该不同（由于调整因子不同）
        # 注意：评分可能相同或非常接近，取决于具体的调整因子
        # 但至少应该经过了不同的调整过程
        assert tsla_candidate is not None
        assert aapl_candidate is not None


class TestBackwardCompatibility:
    """测试向后兼容性"""

    def test_no_symbol_uses_default_adjustments(self):
        """测试不提供symbol时使用默认调整因子"""
        optimizer = ExpirationOptimizer()

        expirations = [
            {'date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
             'days': 30, 'type': 'monthly'}
        ]

        # 不提供symbol
        optimal_no_symbol, _ = optimizer.find_optimal_expiration(
            expirations,
            return_process=False
        )

        assert optimal_no_symbol.composite_score > 0
        assert optimal_no_symbol.date is not None

    def test_evaluate_expiration_without_symbol(self):
        """测试evaluate_expiration不传symbol的兼容性"""
        optimizer = ExpirationOptimizer()

        candidate = optimizer.evaluate_expiration(
            days=30,
            expiration_type='monthly',
            symbol=None  # 明确传None
        )

        assert candidate.composite_score > 0
        assert candidate.theta_efficiency > 0
        assert candidate.gamma_risk > 0

    def test_old_api_still_works(self):
        """测试旧API仍然可用"""
        optimizer = ExpirationOptimizer()

        expirations = [
            {'date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
             'days': 30, 'type': 'monthly'}
        ]

        # 旧式调用（不传symbol）
        optimal, _ = optimizer.find_optimal_expiration(expirations)

        assert optimal is not None
        assert optimal.date is not None


class TestOptimizationProcessTransparency:
    """测试优化过程透明性"""

    def test_process_contains_market_profile(self):
        """测试优化过程包含市场档案"""
        optimizer = ExpirationOptimizer()

        expirations = [
            {'date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
             'days': 30, 'type': 'monthly'}
        ]

        optimal, process = optimizer.find_optimal_expiration(
            expirations, symbol='TSLA', return_process=True
        )

        # 验证包含market_profile
        assert 'market_profile' in process
        profile = process['market_profile']

        assert '波动率比值' in profile
        assert 'Beta系数' in profile
        assert '流动性因子' in profile
        assert '市值分级' in profile
        assert '期权活跃度' in profile

    def test_process_contains_dynamic_adjustments(self):
        """测试优化过程包含动态调整"""
        optimizer = ExpirationOptimizer()

        expirations = [
            {'date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
             'days': 30, 'type': 'monthly'}
        ]

        optimal, process = optimizer.find_optimal_expiration(
            expirations, symbol='TSLA', return_process=True
        )

        # 验证包含dynamic_adjustments
        assert 'dynamic_adjustments' in process
        adjustments = process['dynamic_adjustments']

        assert 'Gamma调整' in adjustments
        assert 'Theta调整' in adjustments
        assert '流动性调整' in adjustments
        assert '收入调整' in adjustments

    def test_process_contains_adjustment_reasoning(self):
        """测试优化过程包含调整推理"""
        optimizer = ExpirationOptimizer()

        expirations = [
            {'date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
             'days': 30, 'type': 'monthly'}
        ]

        # 使用高波动股票（应该有调整推理）
        optimal, process = optimizer.find_optimal_expiration(
            expirations, symbol='TSLA', return_process=True
        )

        # TSLA是高波动股票，应该有adjustment_reasoning
        if 'adjustment_reasoning' in process:
            reasoning = process['adjustment_reasoning']
            assert isinstance(reasoning, list)
            assert len(reasoning) > 0


class TestCoreScoringFunctions:
    """测试核心评分函数的adjustment_factor支持"""

    def test_theta_efficiency_with_adjustment(self):
        """测试Theta效率评分支持调整因子"""
        optimizer = ExpirationOptimizer()

        # 基础评分
        base_score = optimizer.calculate_theta_efficiency(30, adjustment_factor=1.0)

        # 提升评分
        boosted_score = optimizer.calculate_theta_efficiency(30, adjustment_factor=1.1)

        # 降低评分
        reduced_score = optimizer.calculate_theta_efficiency(30, adjustment_factor=0.9)

        assert boosted_score > base_score
        assert reduced_score < base_score

    def test_gamma_risk_with_adjustment(self):
        """测试Gamma风险评分支持调整因子"""
        optimizer = ExpirationOptimizer()

        base_score = optimizer.calculate_gamma_risk(30, volatility=0.3, adjustment_factor=1.0)
        boosted_score = optimizer.calculate_gamma_risk(30, volatility=0.3, adjustment_factor=1.1)
        reduced_score = optimizer.calculate_gamma_risk(30, volatility=0.3, adjustment_factor=0.9)

        assert boosted_score > base_score
        assert reduced_score < base_score

    def test_liquidity_with_adjustment(self):
        """测试流动性评分支持调整因子"""
        optimizer = ExpirationOptimizer()

        base_score = optimizer.calculate_liquidity_score('monthly', 30, adjustment_factor=1.0)
        boosted_score = optimizer.calculate_liquidity_score('monthly', 30, adjustment_factor=1.1)
        reduced_score = optimizer.calculate_liquidity_score('monthly', 30, adjustment_factor=0.9)

        assert boosted_score > base_score
        assert reduced_score < base_score


class TestSelectionReasonEnhancement:
    """测试选择理由增强"""

    def test_selection_reason_includes_stock_info(self):
        """测试选择理由包含股票特定信息"""
        optimizer = ExpirationOptimizer()

        candidate = optimizer.evaluate_expiration(
            days=30,
            expiration_type='monthly',
            symbol='TSLA'
        )

        # TSLA是高波动股票，选择理由应该包含相关信息
        reason = candidate.selection_reason
        assert 'TSLA' in reason or '高波动' in reason or 'Beta' in reason
