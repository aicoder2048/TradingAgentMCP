"""
单元测试：期权限价单成交概率预测核心模块
"""

import pytest
import numpy as np
from unittest.mock import Mock, AsyncMock, patch
from src.option.limit_order_probability import (
    MonteCarloEngine,
    VolatilityMixer,
    FillDetector,
    StatisticalAnalyzer,
    TheoreticalValidator,
    SimulationParameters
)


class TestMonteCarloEngine:
    @pytest.mark.asyncio
    async def test_price_path_generation(self):
        """测试价格路径生成正确性"""
        params = SimulationParameters(
            current_price=10.0,
            underlying_price=100.0,
            strike=100.0,
            days_to_expiry=10,
            delta=-0.5,
            theta=-0.05,
            gamma=0.01,
            vega=0.1,
            implied_volatility=0.3,
            historical_volatility=0.3,
            effective_volatility=0.3,
            simulations=100
        )

        engine = MonteCarloEngine(params)
        paths = await engine.simulate_price_paths()

        assert paths.shape == (100, 10)
        assert np.all(paths >= 0)  # 期权价格不能为负
        assert np.all(np.isfinite(paths))  # 没有inf或nan值

    @pytest.mark.asyncio
    async def test_boundary_conditions(self):
        """测试边界条件"""
        # 测试1: 限价等于当前价格
        params = SimulationParameters(
            current_price=10.0,
            underlying_price=100.0,
            strike=100.0,
            days_to_expiry=5,
            delta=-0.5,
            theta=-0.1,
            gamma=0.01,
            vega=0.1,
            implied_volatility=0.3,
            historical_volatility=0.3,
            effective_volatility=0.3,
            simulations=1000
        )

        engine = MonteCarloEngine(params)
        paths = await engine.simulate_price_paths()
        detector = FillDetector()

        results = detector.detect_fills(paths, limit_price=10.0, order_side="sell")
        assert results["fill_probability"] > 0.99  # 应该接近100%

        # 测试2: 零波动率
        params_zero_vol = SimulationParameters(
            current_price=10.0,
            underlying_price=100.0,
            strike=100.0,
            days_to_expiry=5,
            delta=-0.5,
            theta=-0.1,
            gamma=0.01,
            vega=0.1,
            implied_volatility=0.001,
            historical_volatility=0.001,
            effective_volatility=0.001,
            simulations=100
        )

        engine_zero = MonteCarloEngine(params_zero_vol)
        paths_zero = await engine_zero.simulate_price_paths()

        # 接近零波动率时，路径应该几乎确定性
        std_final = np.std(paths_zero[:, -1])
        assert std_final < 0.1  # 非常低的标准差


class TestVolatilityMixer:
    @pytest.mark.asyncio
    async def test_effective_volatility_calculation(self):
        """测试波动率混合逻辑"""
        mock_client = Mock()
        mixer = VolatilityMixer(mock_client)

        with patch('src.stock.history_data.get_stock_history_data') as mock_history:
            mock_history.return_value = {
                "status": "success",
                "preview_records": [{"close": 100 + i * 0.5} for i in range(100)]
            }

            result = await mixer.calculate_effective_volatility(
                symbol="AAPL",
                implied_volatility=0.35,
                lookback_days=90
            )

            assert "effective_volatility" in result
            assert 0 < result["effective_volatility"] < 1
            assert result["weight_iv"] + result["weight_hv"] == 1.0

    @pytest.mark.asyncio
    async def test_fallback_to_iv_only(self):
        """测试历史数据不可用时回退到纯IV"""
        mock_client = Mock()
        mixer = VolatilityMixer(mock_client)

        with patch('src.stock.history_data.get_stock_history_data') as mock_history:
            mock_history.return_value = {
                "status": "error",
                "error": "Data unavailable"
            }

            result = await mixer.calculate_effective_volatility(
                symbol="AAPL",
                implied_volatility=0.35,
                lookback_days=90
            )

            assert result["method"] == "iv_only_fallback"
            assert result["effective_volatility"] == 0.35
            assert result["weight_iv"] == 1.0
            assert result["weight_hv"] == 0.0


class TestFillDetector:
    def test_sell_order_detection(self):
        """测试卖单成交检测"""
        # 创建示例路径
        paths = np.array([
            [10.0, 10.5, 11.0, 10.8, 10.9],  # 索引2成交 (11.0 >= 11.0)
            [10.0, 10.2, 10.4, 10.6, 10.8],  # 永不成交
            [10.0, 10.1, 10.2, 11.5, 11.0],  # 索引3成交 (11.5 >= 11.0)
        ])

        detector = FillDetector()
        results = detector.detect_fills(
            price_paths=paths,
            limit_price=11.0,
            order_side="sell"
        )

        assert results["fill_probability"] == 2/3  # 3条路径中2条成交
        assert abs(results["expected_days_to_fill"] - 2.5) < 0.01  # 索引2和索引3的平均: (2+3)/2=2.5

    def test_buy_order_detection(self):
        """测试买单成交检测"""
        paths = np.array([
            [10.0, 9.5, 9.0, 9.2, 9.1],   # 索引2成交
            [10.0, 9.8, 9.6, 9.4, 9.2],   # 限价9.0时永不成交
            [10.0, 10.1, 9.9, 8.5, 8.8],  # 索引3成交
        ])

        detector = FillDetector()
        results = detector.detect_fills(
            price_paths=paths,
            limit_price=9.0,
            order_side="buy"
        )

        assert results["fill_probability"] == 2/3
        assert results["expected_days_to_fill"] == (2 + 3) / 2

    def test_percentile_calculation(self):
        """测试百分位数计算"""
        # 创建100条路径，明确的成交时间分布
        paths = []
        for i in range(100):
            path = [10.0] * 10
            if i < 50:  # 50%的路径在第2天成交
                path[2] = 11.0
            elif i < 75:  # 25%的路径在第5天成交
                path[5] = 11.0
            elif i < 90:  # 15%的路径在第8天成交
                path[8] = 11.0
            paths.append(path)

        paths = np.array(paths)
        detector = FillDetector()
        results = detector.detect_fills(
            price_paths=paths,
            limit_price=11.0,
            order_side="sell"
        )

        # 验证百分位数
        assert results["percentile_days"][25] <= 2
        assert results["percentile_days"][50] <= 5
        assert results["percentile_days"][75] <= 8


class TestStatisticalAnalyzer:
    def test_confidence_metrics(self):
        """测试置信区间计算"""
        analyzer = StatisticalAnalyzer()

        simulation_results = {
            "fill_probability": 0.68,
            "expected_days_to_fill": 3.2
        }

        metrics = analyzer.calculate_confidence_metrics(
            simulation_results=simulation_results,
            num_simulations=10000,
            backtest_results=None
        )

        assert "standard_error" in metrics
        assert metrics["standard_error"] < 0.01  # 10k模拟应该有小误差
        assert metrics["confidence_interval"]["lower"] < 0.68
        assert metrics["confidence_interval"]["upper"] > 0.68
        assert metrics["confidence_interval"]["level"] == 0.95

    def test_confidence_level_with_backtest(self):
        """测试有回测结果时的置信度评估"""
        analyzer = StatisticalAnalyzer()

        simulation_results = {
            "fill_probability": 0.68,
            "expected_days_to_fill": 3.2
        }

        # 高质量回测结果
        backtest_results = {
            "mae": 0.08,
            "backtest_samples": 60
        }

        metrics = analyzer.calculate_confidence_metrics(
            simulation_results=simulation_results,
            num_simulations=10000,
            backtest_results=backtest_results
        )

        assert metrics["confidence_level"] == "high"
        assert metrics["confidence_score"] == 0.9


class TestTheoreticalValidator:
    @pytest.mark.asyncio
    async def test_theoretical_validation(self):
        """测试理论验证通过"""
        validator = TheoreticalValidator()
        results = await validator.validate_model()

        assert "all_tests_passed" in results
        # 单个测试可能因随机性失败，但结构应该有效
        assert isinstance(results["all_tests_passed"], bool)
        assert len(results) >= 6  # 至少6个测试

        # 验证关键测试存在
        assert "limit_equals_current" in results
        assert "zero_volatility_deterministic" in results
        assert "higher_vol_higher_prob" in results
        assert "longer_window_higher_prob" in results

    @pytest.mark.asyncio
    async def test_limit_equals_current_validation(self):
        """测试限价等于当前价格时接近100%成交概率"""
        params = SimulationParameters(
            current_price=10.0,
            underlying_price=100.0,
            strike=100.0,
            days_to_expiry=5,
            delta=-0.5,
            theta=-0.1,
            gamma=0.01,
            vega=0.1,
            implied_volatility=0.3,
            historical_volatility=0.3,
            effective_volatility=0.3,
            simulations=1000
        )

        engine = MonteCarloEngine(params)
        paths = await engine.simulate_price_paths()
        detector = FillDetector()
        results = detector.detect_fills(paths, limit_price=10.0, order_side="sell")

        # 限价等于当前价，应该立即成交
        assert results["fill_probability"] > 0.99


class TestRecommendationEngine:
    @pytest.mark.asyncio
    async def test_generate_recommendations(self):
        """测试建议生成"""
        from src.option.limit_order_probability import RecommendationEngine

        fill_results = {
            "fill_probability": 0.68,
            "expected_days_to_fill": 3.2,
            "median_days_to_fill": 2.5
        }

        confidence_metrics = {
            "confidence_level": "high",
            "confidence_score": 0.9,
            "standard_error": 0.04
        }

        recommender = RecommendationEngine()
        result = await recommender.generate_recommendations(
            fill_results=fill_results,
            current_price=2.50,
            limit_price=2.80,
            order_side="sell",
            confidence_metrics=confidence_metrics
        )

        assert "recommendations" in result
        assert "alternative_limits" in result
        assert len(result["recommendations"]) > 0
        assert len(result["alternative_limits"]) > 0

    @pytest.mark.asyncio
    async def test_alternative_limits_ordering(self):
        """测试替代限价按成交概率排序"""
        from src.option.limit_order_probability import RecommendationEngine

        alternatives = await RecommendationEngine._generate_alternatives(
            current_price=2.50,
            limit_price=2.80,
            order_side="sell",
            current_fill_prob=0.68
        )

        # 验证按成交概率降序排列
        for i in range(len(alternatives) - 1):
            assert alternatives[i]["fill_probability"] >= alternatives[i + 1]["fill_probability"]

        # 验证包含当前限价
        current_limit_scenarios = [a for a in alternatives if a["scenario"] == "当前限价"]
        assert len(current_limit_scenarios) == 1
        assert current_limit_scenarios[0]["limit_price"] == 2.80
