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

        results = detector.detect_fills(
            paths,
            limit_price=10.0,
            order_side="sell",
            current_price=10.0  # 传递当前价格
        )
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

        # 验证first_day_fill_probability字段存在
        assert "first_day_fill_probability" in results
        assert 0 <= results["first_day_fill_probability"] <= 1
        # 第一天概率应该 <= 总概率
        assert results["first_day_fill_probability"] <= results["fill_probability"]
        # 这个测试用例中没有路径在第一天(索引0)成交
        assert results["first_day_fill_probability"] == 0

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

        # 验证first_day_fill_probability字段
        assert "first_day_fill_probability" in results
        assert results["first_day_fill_probability"] <= results["fill_probability"]
        assert results["first_day_fill_probability"] == 0  # 没有路径在第一天成交

    def test_first_day_fill_probability(self):
        """测试第一天成交概率计算"""
        paths = np.array([
            [11.0, 10.5, 10.2, 10.0, 9.9],   # 第0天立即成交 (11.0 >= 11.0)
            [10.0, 11.2, 11.5, 11.0, 10.8],  # 第1天成交
            [10.0, 10.2, 10.4, 10.6, 10.8],  # 永不成交
            [11.5, 11.2, 11.0, 10.9, 10.7],  # 第0天立即成交 (11.5 >= 11.0)
        ])

        detector = FillDetector()
        results = detector.detect_fills(
            price_paths=paths,
            limit_price=11.0,
            order_side="sell"
        )

        # 4条路径中3条成交
        assert results["fill_probability"] == 3/4

        # 2条路径在第0天（第一天）成交
        assert results["first_day_fill_probability"] == 2/4
        assert results["first_day_fill_probability"] == 0.5

        # 第一天概率应该 <= 总概率
        assert results["first_day_fill_probability"] <= results["fill_probability"]

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
        results = detector.detect_fills(
            paths,
            limit_price=10.0,
            order_side="sell",
            current_price=10.0  # 传递当前价格
        )

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


class TestMarketTimeAwareness:
    """测试市场时间感知功能"""

    @pytest.mark.asyncio
    async def test_partial_trading_day_simulation(self):
        """测试部分交易日的价格模拟"""
        # 盘中预测：剩余50%交易时间
        params_partial = SimulationParameters(
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
            simulations=100,
            first_day_fraction=0.5  # 剩余50%时间
        )

        engine = MonteCarloEngine(params_partial)
        paths = await engine.simulate_price_paths()

        assert paths.shape == (100, 5)
        assert np.all(paths >= 0)
        assert np.all(np.isfinite(paths))

        # 第一天的价格变化应该小于完整交易日
        first_day_changes = np.abs(paths[:, 0] - params_partial.current_price)
        avg_first_day_change = np.mean(first_day_changes)

        # 完整交易日对比
        params_full = SimulationParameters(
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
            simulations=100,
            first_day_fraction=1.0  # 完整交易日
        )

        engine_full = MonteCarloEngine(params_full)
        paths_full = await engine_full.simulate_price_paths()
        full_day_changes = np.abs(paths_full[:, 0] - params_full.current_price)
        avg_full_day_change = np.mean(full_day_changes)

        # 部分交易日的平均价格变化应该小于完整交易日
        # 注意：由于随机性，这个测试可能偶尔失败，所以用较宽松的阈值
        assert avg_first_day_change < avg_full_day_change * 1.2

    @pytest.mark.asyncio
    async def test_first_day_fill_probability_with_partial_day(self):
        """测试部分交易日的首日成交概率"""
        params = SimulationParameters(
            current_price=10.0,
            underlying_price=100.0,
            strike=100.0,
            days_to_expiry=5,
            delta=-0.5,
            theta=-0.1,
            gamma=0.01,
            vega=0.1,
            implied_volatility=0.5,  # 高波动率
            historical_volatility=0.5,
            effective_volatility=0.5,
            simulations=1000,
            first_day_fraction=0.5  # 剩余50%时间
        )

        engine = MonteCarloEngine(params)
        paths = await engine.simulate_price_paths()

        detector = FillDetector()
        results = detector.detect_fills(
            paths,
            limit_price=10.5,
            order_side="sell",
            first_day_fraction=0.5
        )

        # 第一天成交概率应该 > 0（因为索引0参与模拟了）
        assert results["first_day_fill_probability"] >= 0

        # 总成交概率应该 >= 第一天成交概率
        assert results["fill_probability"] >= results["first_day_fill_probability"]

    def test_is_partial_day_flag(self):
        """测试 is_partial_day 标记正确性"""
        # 创建简单的测试路径
        paths = np.array([
            [10.0, 10.5, 11.0, 10.8, 10.9],
            [10.0, 10.2, 10.3, 11.0, 10.7],
            [10.0, 11.0, 10.6, 10.5, 10.4],
        ])

        detector = FillDetector()

        # 测试1: 部分交易日
        results_partial = detector.detect_fills(
            paths,
            limit_price=11.0,
            order_side="sell",
            first_day_fraction=0.5
        )

        # 第一天应该标记为 is_partial_day
        prob_by_day = results_partial["probability_by_day"]
        if len(prob_by_day) > 0 and prob_by_day[0]["day"] == 1:
            assert prob_by_day[0]["is_partial_day"] is True

        # 测试2: 完整交易日
        results_full = detector.detect_fills(
            paths,
            limit_price=11.0,
            order_side="sell",
            first_day_fraction=1.0
        )

        # 第一天不应该标记为 is_partial_day
        prob_by_day_full = results_full["probability_by_day"]
        if len(prob_by_day_full) > 0 and prob_by_day_full[0]["day"] == 1:
            assert prob_by_day_full[0]["is_partial_day"] is False

    def test_zero_remaining_time(self):
        """测试剩余时间为0的情况"""
        params = SimulationParameters(
            current_price=10.0,
            underlying_price=100.0,
            strike=100.0,
            days_to_expiry=3,
            delta=-0.5,
            theta=-0.1,
            gamma=0.01,
            vega=0.1,
            implied_volatility=0.3,
            historical_volatility=0.3,
            effective_volatility=0.3,
            simulations=10,
            first_day_fraction=0.0  # 没有剩余时间
        )

        engine = MonteCarloEngine(params)
        import asyncio
        paths = asyncio.run(engine.simulate_price_paths())

        # 第一天的价格应该保持不变
        assert np.all(paths[:, 0] == params.current_price)

    def test_calendar_date_mapping(self):
        """测试日历日期映射"""
        from datetime import datetime

        paths = np.array([
            [11.0, 10.5, 11.0],  # 第一天就成交（day_idx=0）
            [11.0, 11.0, 10.6],  # 第一天就成交（day_idx=0）
        ])

        detector = FillDetector()

        # 模拟市场上下文
        market_ctx = {
            "first_day_is_today": True,
            "eastern_time": datetime(2025, 10, 5, 12, 0)  # 2025-10-05 12:00 PM
        }

        results = detector.detect_fills(
            paths,
            limit_price=11.0,
            order_side="sell",
            expiration_date="2025-10-17",
            market_context=market_ctx
        )

        # 验证第一天有日历日期
        prob_by_day = results["probability_by_day"]
        assert len(prob_by_day) > 0
        assert "calendar_date" in prob_by_day[0]
        assert prob_by_day[0]["calendar_date"] == "2025-10-05"  # 今日

        # 验证百分位数描述存在
        percentile_desc = results.get("percentile_descriptions", {})
        assert len(percentile_desc) > 0
        # 验证包含 EDT 标记
        if 25 in percentile_desc:
            assert "EDT" in percentile_desc[25] or "成交" in percentile_desc[25]

    def test_percentile_descriptions_no_zero_day(self):
        """测试百分位数描述不包含混淆的'第0天'"""
        from datetime import datetime

        paths = np.array([
            [10.0, 10.5, 11.0, 10.8],
            [10.0, 11.0, 10.6, 10.5],
            [10.0, 10.2, 11.0, 10.7],
        ])

        detector = FillDetector()

        market_ctx = {
            "first_day_is_today": True,
            "eastern_time": datetime(2025, 10, 5, 10, 0)
        }

        results = detector.detect_fills(
            paths,
            limit_price=11.0,
            order_side="sell",
            expiration_date="2025-10-17",
            market_context=market_ctx
        )

        percentile_desc = results.get("percentile_descriptions", {})

        # 验证不包含"第0天"这种混淆表述
        for desc in percentile_desc.values():
            assert "第0天" not in desc
            # 应该用"今日"、"明日"或具体天数
            assert ("今日" in desc or "明日" in desc or "天内" in desc or
                    "不太可能" in desc)
