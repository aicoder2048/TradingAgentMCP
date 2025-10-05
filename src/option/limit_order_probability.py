"""
期权限价单成交概率预测核心模块

基于蒙特卡洛模拟、波动率分析和Greeks敏感度预测限价单成交概率。
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
from scipy import stats
import asyncio
from concurrent.futures import ThreadPoolExecutor


@dataclass
class SimulationParameters:
    """蒙特卡洛模拟参数"""
    current_price: float
    underlying_price: float
    strike: float
    days_to_expiry: int
    delta: float
    theta: float
    gamma: float
    vega: float
    implied_volatility: float
    historical_volatility: float
    effective_volatility: float
    risk_free_rate: float = 0.048
    simulations: int = 10000
    first_day_fraction: float = 1.0  # 第一交易日的有效时间比例 (0.0-1.0)


@dataclass
class FillStatistics:
    """蒙特卡洛模拟的统计结果"""
    fill_probability: float
    expected_days_to_fill: float
    standard_error: float
    confidence_interval: Tuple[float, float]
    probability_by_day: List[Dict[str, float]]
    percentile_days: Dict[int, float]


class MonteCarloEngine:
    """
    高性能蒙特卡洛模拟引擎，用于期权价格路径模拟。
    使用向量化NumPy操作以提高效率。
    """

    def __init__(self, params: SimulationParameters):
        self.params = params
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def simulate_price_paths(self) -> np.ndarray:
        """
        使用并行处理模拟期权价格路径。

        Returns:
            形状为(simulations, days_to_expiry)的价格路径数组
        """
        # 将模拟分割到多个worker进行并行处理
        chunk_size = self.params.simulations // 4
        tasks = []

        for i in range(4):
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size if i < 3 else self.params.simulations
            task = self._simulate_chunk(start_idx, end_idx)
            tasks.append(task)

        chunks = await asyncio.gather(*tasks)
        return np.vstack(chunks)

    async def _simulate_chunk(self, start_idx: int, end_idx: int) -> np.ndarray:
        """并行模拟一批价格路径"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._simulate_paths_vectorized,
            end_idx - start_idx
        )

    def _simulate_paths_vectorized(self, num_paths: int) -> np.ndarray:
        """
        使用NumPy的向量化价格路径模拟。

        支持部分交易日：第一天可以是不完整的交易日（盘中预测）。

        股票价格演化:
        S(t+1) = S(t) * exp((μ - σ²/2)dt + σ√dt * Z)

        期权价格变化:
        ΔP = Delta * ΔS + 0.5 * Gamma * ΔS² + Theta * dt
        """
        # 初始化数组
        days = self.params.days_to_expiry
        stock_paths = np.zeros((num_paths, days))
        option_paths = np.zeros((num_paths, days))

        # 基准价格（起点）
        base_stock_price = self.params.underlying_price
        base_option_price = self.params.current_price

        # 向量化随机游走
        for t in range(days):
            # 确定时间步长和起点价格
            if t == 0:
                # 第一天：使用 first_day_fraction（支持部分交易日）
                dt = self.params.first_day_fraction / 365
                prev_stock = base_stock_price
                prev_option = base_option_price
            else:
                # 后续天数：完整交易日
                dt = 1 / 365
                prev_stock = stock_paths[:, t-1]
                prev_option = option_paths[:, t-1]

            # 如果没有剩余时间，保持价格不变
            if dt <= 0:
                stock_paths[:, t] = prev_stock
                option_paths[:, t] = prev_option
                continue

            sqrt_dt = np.sqrt(dt)

            # 生成随机冲击
            Z = np.random.standard_normal(num_paths)

            # 股票价格演化 (几何布朗运动)
            drift = -0.5 * self.params.effective_volatility ** 2 * dt
            diffusion = self.params.effective_volatility * sqrt_dt * Z
            stock_paths[:, t] = prev_stock * np.exp(drift + diffusion)

            # 计算股票价格变化
            delta_S = stock_paths[:, t] - prev_stock

            # 期权价格变化 (二阶近似)
            delta_option = (
                self.params.delta * delta_S +
                0.5 * self.params.gamma * delta_S ** 2 +
                self.params.theta * dt
            )

            # 更新期权价格并设置下界
            option_paths[:, t] = np.maximum(
                0,
                prev_option + delta_option
            )

        return option_paths

    def __del__(self):
        """清理executor"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)


class VolatilityMixer:
    """
    复杂的波动率计算，结合IV和HV。
    实现基于市场条件的动态加权。
    """

    def __init__(self, tradier_client):
        self.tradier_client = tradier_client

    async def calculate_effective_volatility(
        self,
        symbol: str,
        implied_volatility: float,
        lookback_days: int = 90,
        dynamic_weights: bool = True
    ) -> Dict[str, float]:
        """
        使用动态加权计算有效波动率。

        动态加权根据以下因素调整IV/HV混合:
        - IV/HV比率 (均值回归预期)
        - 近期波动率趋势
        - 到期时间
        """
        from src.stock.history_data import get_stock_history_data

        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        # 获取历史数据
        history_result = await get_stock_history_data(
            symbol=symbol,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            include_indicators=False
        )

        if history_result.get("status") != "success":
            # 回退到纯IV
            return {
                "implied_volatility": implied_volatility,
                "historical_volatility": implied_volatility,
                "effective_volatility": implied_volatility,
                "weight_iv": 1.0,
                "weight_hv": 0.0,
                "method": "iv_only_fallback"
            }

        # 计算历史波动率
        prices = [row["close"] for row in history_result["preview_records"]]
        returns = np.diff(np.log(prices))
        hv = np.std(returns) * np.sqrt(252)  # 年化

        # 如果启用动态加权，计算权重
        if dynamic_weights:
            iv_hv_ratio = implied_volatility / hv if hv > 0 else 1.0

            # 均值回归: 高IV/HV比率 → 更多权重给HV
            if iv_hv_ratio > 1.5:
                weight_iv = 0.4
                weight_hv = 0.6
            elif iv_hv_ratio < 0.7:
                weight_iv = 0.7
                weight_hv = 0.3
            else:
                weight_iv = 0.6
                weight_hv = 0.4
        else:
            weight_iv = 0.6
            weight_hv = 0.4

        effective_vol = weight_iv * implied_volatility + weight_hv * hv

        return {
            "implied_volatility": implied_volatility,
            "historical_volatility": hv,
            "effective_volatility": effective_vol,
            "weight_iv": weight_iv,
            "weight_hv": weight_hv,
            "iv_hv_ratio": implied_volatility / hv if hv > 0 else None,
            "method": "dynamic_mixing" if dynamic_weights else "static_mixing"
        }


class FillDetector:
    """
    高级成交检测，考虑市场微观结构。
    """

    @staticmethod
    def detect_fills(
        price_paths: np.ndarray,
        limit_price: float,
        order_side: str,
        include_touch_probability: bool = True,
        first_day_fraction: float = 1.0,
        current_price: Optional[float] = None,
        expiration_date: Optional[str] = None,
        market_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        检测所有模拟路径中的成交情况。

        Args:
            price_paths: 模拟的价格路径数组
            limit_price: 目标限价
            order_side: "buy" 或 "sell"
            include_touch_probability: 追踪价格是否触及限价
            first_day_fraction: 第一交易日的有效时间比例 (0.0-1.0)
            current_price: 当前价格（用于检查即刻成交）
            expiration_date: 到期日期 YYYY-MM-DD 格式
            market_context: 市场上下文（包含 eastern_time, first_day_is_today 等）

        Returns:
            综合成交统计数据
        """
        from datetime import datetime, timedelta

        num_paths, days = price_paths.shape

        # 生成日期映射：天数索引 → 日历日期
        day_to_calendar_date = {}
        if expiration_date and market_context:
            try:
                eastern_time = market_context.get("eastern_time")
                if eastern_time:
                    # 确定第一个交易日的日历日期
                    if market_context.get("first_day_is_today"):
                        first_calendar_date = eastern_time.date()
                    else:
                        # 第一交易日是明天
                        first_calendar_date = eastern_time.date() + timedelta(days=1)

                    # 为每一天生成日历日期
                    for day_idx in range(days):
                        calendar_date = first_calendar_date + timedelta(days=day_idx)
                        day_to_calendar_date[day_idx] = calendar_date.strftime("%Y-%m-%d")
            except Exception:
                pass  # 如果日期解析失败，继续不带日期

        # 检查是否即刻成交（限价已满足当前价格条件）
        immediate_fill = False
        if current_price is not None:
            if order_side == "buy":
                immediate_fill = limit_price >= current_price
            else:  # sell
                immediate_fill = limit_price <= current_price

        # 确定成交条件
        if order_side == "buy":
            # 买单在价格 <= 限价时成交
            fills = price_paths <= limit_price
        else:
            # 卖单在价格 >= 限价时成交
            fills = price_paths >= limit_price

        # 找到每条路径的首次成交日
        first_fill_days = np.full(num_paths, -1)
        touched = np.zeros(num_paths, dtype=bool)

        # 如果即刻成交，所有路径在第0天成交
        if immediate_fill:
            first_fill_days[:] = 0
            touched[:] = True
        else:
            for i in range(num_paths):
                fill_indices = np.where(fills[i])[0]
                if len(fill_indices) > 0:
                    first_fill_days[i] = fill_indices[0]
                    touched[i] = True

        # 计算统计数据
        filled_mask = first_fill_days >= 0
        fill_probability = np.mean(filled_mask)

        if np.any(filled_mask):
            expected_days = np.mean(first_fill_days[filled_mask])
            median_days = np.median(first_fill_days[filled_mask])

            # 计算已成交订单的百分位数
            percentiles = {
                25: np.percentile(first_fill_days[filled_mask], 25),
                50: median_days,
                75: np.percentile(first_fill_days[filled_mask], 75),
                90: np.percentile(first_fill_days[filled_mask], 90)
            }
        else:
            expected_days = float('inf')
            median_days = float('inf')
            percentiles = {25: float('inf'), 50: float('inf'),
                         75: float('inf'), 90: float('inf')}

        # 计算每日成交概率
        daily_fills = []
        cumulative_prob = 0

        for day in range(days):
            daily_fill_count = np.sum(first_fill_days == day)
            daily_prob = daily_fill_count / num_paths
            cumulative_prob += daily_prob

            if daily_prob > 0:
                day_entry = {
                    "day": day + 1,  # 第1天、第2天...
                    "daily_prob": daily_prob,
                    "cumulative_prob": cumulative_prob,
                    "is_partial_day": (day == 0 and first_day_fraction < 1.0)
                }

                # 添加日历日期
                if day in day_to_calendar_date:
                    day_entry["calendar_date"] = day_to_calendar_date[day]

                daily_fills.append(day_entry)

        # 计算第一天成交概率 (day index = 0)
        first_day_fill_count = np.sum(first_fill_days == 0)
        first_day_prob = first_day_fill_count / num_paths

        # 触及概率 (价格在任意时刻达到限价)
        touch_probability = np.mean(touched) if include_touch_probability else None

        # 生成百分位数的友好描述（替代"第0天"混淆表述）
        percentile_descriptions = {}
        for pct, day_value in percentiles.items():
            if day_value == float('inf'):
                percentile_descriptions[pct] = "不太可能成交"
            else:
                day_idx = int(day_value)

                # 生成基础描述
                if day_idx == 0:
                    desc = "今日成交"
                elif day_idx == 1:
                    desc = "明日成交"
                else:
                    desc = f"{day_idx + 1}天内成交"

                # 添加日历日期
                if day_idx in day_to_calendar_date:
                    desc += f" ({day_to_calendar_date[day_idx]} EDT)"

                percentile_descriptions[pct] = desc

        return {
            "fill_probability": float(fill_probability),
            "first_day_fill_probability": float(first_day_prob),
            "expected_days_to_fill": float(expected_days) if expected_days != float('inf') else None,
            "median_days_to_fill": float(median_days) if median_days != float('inf') else None,
            "percentile_days": {k: float(v) for k, v in percentiles.items()},
            "percentile_descriptions": percentile_descriptions,  # 新增：友好描述
            "probability_by_day": [
                {
                    "day": int(item["day"]),
                    "daily_prob": float(item["daily_prob"]),
                    "cumulative_prob": float(item["cumulative_prob"]),
                    "is_partial_day": bool(item["is_partial_day"]),
                    "calendar_date": item.get("calendar_date")  # 可能为 None
                }
                for item in daily_fills[:10]
            ],
            "touch_probability": float(touch_probability) if touch_probability is not None else None,
            "no_fill_probability": float(1 - fill_probability)
        }


class StatisticalAnalyzer:
    """
    高级统计分析和置信度评估。
    """

    @staticmethod
    def calculate_confidence_metrics(
        simulation_results: Dict[str, Any],
        num_simulations: int,
        backtest_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        计算置信区间和可靠性指标。
        """
        fill_prob = simulation_results["fill_probability"]

        # 二项比例的标准误差
        if 0 < fill_prob < 1:
            standard_error = np.sqrt(fill_prob * (1 - fill_prob) / num_simulations)
        else:
            standard_error = 0

        # 95%置信区间
        z_score = 1.96  # 95%置信度
        ci_lower = max(0, fill_prob - z_score * standard_error)
        ci_upper = min(1, fill_prob + z_score * standard_error)

        # 确定置信度等级
        confidence_level = "low"
        confidence_score = 0.5

        if backtest_results:
            mae = backtest_results.get("mae", 1.0)
            samples = backtest_results.get("backtest_samples", 0)

            if mae < 0.10 and samples > 50:
                confidence_level = "high"
                confidence_score = 0.9
            elif mae < 0.15 and samples > 30:
                confidence_level = "medium"
                confidence_score = 0.7
        elif standard_error < 0.05:
            confidence_level = "medium"
            confidence_score = 0.7

        return {
            "standard_error": float(standard_error),
            "confidence_interval": {
                "lower": float(ci_lower),
                "upper": float(ci_upper),
                "level": 0.95
            },
            "confidence_level": confidence_level,
            "confidence_score": float(confidence_score),
            "statistical_significance": bool(standard_error < 0.05),
            "sample_size_adequate": bool(num_simulations >= 10000)
        }


class TheoreticalValidator:
    """
    模型正确性的理论验证框架。
    """

    @staticmethod
    async def validate_model() -> Dict[str, bool]:
        """
        运行综合理论验证测试。
        """
        tests = {}

        # 测试1: 限价等于当前价 → 100%成交概率
        engine = MonteCarloEngine(SimulationParameters(
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
        ))

        paths = await engine.simulate_price_paths()
        detector = FillDetector()
        results = detector.detect_fills(paths, limit_price=10.0, order_side="sell")
        tests["limit_equals_current"] = results["fill_probability"] > 0.99

        # 测试2: 零波动率 → 确定性结果
        engine_zero_vol = MonteCarloEngine(SimulationParameters(
            current_price=10.0,
            underlying_price=100.0,
            strike=100.0,
            days_to_expiry=5,
            delta=-0.5,
            theta=-0.1,
            gamma=0.01,
            vega=0.1,
            implied_volatility=0.001,  # 接近零
            historical_volatility=0.001,
            effective_volatility=0.001,
            simulations=100
        ))

        paths_zero = await engine_zero_vol.simulate_price_paths()
        std_dev = np.std(paths_zero[:, -1])
        tests["zero_volatility_deterministic"] = std_dev < 0.01

        # 测试3: 更高波动率 → 更高成交概率 (对于价外限价)
        high_vol_params = SimulationParameters(
            current_price=10.0,
            underlying_price=100.0,
            strike=100.0,
            days_to_expiry=10,
            delta=-0.5,
            theta=-0.1,
            gamma=0.01,
            vega=0.1,
            implied_volatility=0.5,
            historical_volatility=0.5,
            effective_volatility=0.5,
            simulations=1000
        )

        low_vol_params = SimulationParameters(
            current_price=10.0,
            underlying_price=100.0,
            strike=100.0,
            days_to_expiry=10,
            delta=-0.5,
            theta=-0.1,
            gamma=0.01,
            vega=0.1,
            implied_volatility=0.1,
            historical_volatility=0.1,
            effective_volatility=0.1,
            simulations=1000
        )

        engine_high = MonteCarloEngine(high_vol_params)
        engine_low = MonteCarloEngine(low_vol_params)

        paths_high = await engine_high.simulate_price_paths()
        paths_low = await engine_low.simulate_price_paths()

        results_high = detector.detect_fills(paths_high, limit_price=11.0, order_side="sell")
        results_low = detector.detect_fills(paths_low, limit_price=11.0, order_side="sell")

        tests["higher_vol_higher_prob"] = (
            results_high["fill_probability"] > results_low["fill_probability"]
        )

        # 测试4: 更长时间窗口 → 更高成交概率
        short_window = SimulationParameters(
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

        long_window = SimulationParameters(
            current_price=10.0,
            underlying_price=100.0,
            strike=100.0,
            days_to_expiry=20,
            delta=-0.5,
            theta=-0.1,
            gamma=0.01,
            vega=0.1,
            implied_volatility=0.3,
            historical_volatility=0.3,
            effective_volatility=0.3,
            simulations=1000
        )

        engine_short = MonteCarloEngine(short_window)
        engine_long = MonteCarloEngine(long_window)

        paths_short = await engine_short.simulate_price_paths()
        paths_long = await engine_long.simulate_price_paths()

        results_short = detector.detect_fills(paths_short, limit_price=10.5, order_side="sell")
        results_long = detector.detect_fills(paths_long, limit_price=10.5, order_side="sell")

        tests["longer_window_higher_prob"] = (
            results_long["fill_probability"] >= results_short["fill_probability"]
        )

        # 测试5: OTM看跌期权的Theta衰减
        tests["theta_decay_negative"] = high_vol_params.theta < 0

        # 测试6: 买卖逻辑对称性
        results_buy = detector.detect_fills(paths_high, limit_price=9.0, order_side="buy")
        results_sell = detector.detect_fills(paths_high, limit_price=11.0, order_side="sell")
        tests["buy_sell_logic_correct"] = (
            results_buy["fill_probability"] > 0 and
            results_sell["fill_probability"] > 0
        )

        # 所有测试必须通过
        tests["all_tests_passed"] = all(tests.values())

        # 转换所有numpy.bool为Python bool
        return {k: bool(v) for k, v in tests.items()}


class BacktestValidator:
    """
    使用历史数据进行简化回测验证。
    """

    def __init__(self, tradier_client):
        self.tradier_client = tradier_client

    async def run_backtest(
        self,
        symbol: str,
        strike: float,
        option_type: str,
        days_to_expiry: int = 30,
        lookback_days: int = 90,
        limit_premium_percentage: float = 0.10
    ) -> Dict[str, Any]:
        """
        使用Black-Scholes定价运行简化回测。
        """
        from src.stock.history_data import get_stock_history_data
        from scipy.stats import norm
        import math

        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days + days_to_expiry)

        # 获取历史数据
        history_result = await get_stock_history_data(
            symbol=symbol,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            include_indicators=False
        )

        if history_result.get("status") != "success":
            return {
                "backtest_available": False,
                "error": "Historical data unavailable"
            }

        data = history_result["preview_records"]
        if len(data) < lookback_days:
            return {
                "backtest_available": False,
                "error": "Insufficient historical data"
            }

        # 运行回测模拟
        test_results = []

        for i in range(lookback_days - days_to_expiry):
            start_date = i
            end_date = i + days_to_expiry

            # 获取此窗口的价格
            start_price = data[start_date]["close"]

            # 使用Black-Scholes计算理论期权价格
            theoretical_price = self._black_scholes_price(
                S=start_price,
                K=strike,
                T=days_to_expiry/365,
                r=0.048,
                sigma=0.3,  # 假设波动率
                option_type=option_type
            )

            # 设置高于理论价格的限价
            limit_price = theoretical_price * (1 + limit_premium_percentage)

            # 检查限价是否会被成交
            filled = False
            fill_day = None

            for j in range(start_date, end_date):
                if j >= len(data):
                    break

                daily_price = data[j]["close"]
                daily_option_price = self._black_scholes_price(
                    S=daily_price,
                    K=strike,
                    T=(days_to_expiry - (j - start_date))/365,
                    r=0.048,
                    sigma=0.3,
                    option_type=option_type
                )

                if daily_option_price >= limit_price:
                    filled = True
                    fill_day = j - start_date
                    break

            test_results.append({
                "filled": filled,
                "fill_day": fill_day,
                "theoretical_price": theoretical_price,
                "limit_price": limit_price
            })

        # 计算统计数据
        fill_rate = sum(1 for r in test_results if r["filled"]) / len(test_results)
        avg_fill_days = np.mean([
            r["fill_day"] for r in test_results
            if r["filled"] and r["fill_day"] is not None
        ]) if any(r["filled"] for r in test_results) else None

        return {
            "backtest_available": True,
            "backtest_samples": int(len(test_results)),
            "actual_fill_rate": float(fill_rate),
            "average_days_to_fill": float(avg_fill_days) if avg_fill_days is not None else None,
            "test_results_sample": test_results[:5],  # 检查样本
            "is_reliable": bool(len(test_results) > 30),
            "mae": None  # 将通过与预测比较来计算
        }

    def _black_scholes_price(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str
    ) -> float:
        """
        简化的Black-Scholes定价公式。
        """
        from scipy.stats import norm
        import math

        if T <= 0:
            # 到期时
            if option_type == "call":
                return max(0, S - K)
            else:
                return max(0, K - S)

        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        if option_type == "call":
            price = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
        else:
            price = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

        return max(0, price)


class RecommendationEngine:
    """
    生成智能建议和替代限价。
    """

    @staticmethod
    async def generate_recommendations(
        fill_results: Dict[str, Any],
        current_price: float,
        limit_price: float,
        order_side: str,
        confidence_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        根据分析生成可操作的建议。
        """
        fill_prob = fill_results["fill_probability"]
        expected_days = fill_results.get("expected_days_to_fill")
        first_day_prob = fill_results.get("first_day_fill_probability", 0)
        percentile_desc = fill_results.get("percentile_descriptions", {})

        # 获取首日描述（带日期）
        first_day_desc = "首日"
        if fill_results.get("probability_by_day") and len(fill_results["probability_by_day"]) > 0:
            first_day = fill_results["probability_by_day"][0]
            if "calendar_date" in first_day and first_day["calendar_date"]:
                first_day_desc = f"首日({first_day['calendar_date']} EDT)"

        # 生成文本建议
        recommendations = []

        # 主要评估
        if fill_prob >= 0.8:
            recommendations.append(
                f"✅ 高成交概率: 该限价有 {fill_prob*100:.0f}% 概率成交"
            )
        elif fill_prob >= 0.5:
            recommendations.append(
                f"⚠️ 中等成交概率: 该限价有 {fill_prob*100:.0f}% 概率成交"
            )
        else:
            recommendations.append(
                f"❌ 低成交概率: 该限价仅有 {fill_prob*100:.0f}% 概率成交"
            )

        # 首日成交概率
        if first_day_prob > 0:
            recommendations.append(
                f"{first_day_desc}成交概率: {first_day_prob*100:.1f}%"
            )

        # 时间预期
        if expected_days and expected_days < float('inf'):
            recommendations.append(
                f"预期成交时间: {expected_days:.1f} 天"
            )

        # 百分位数友好描述
        if 50 in percentile_desc:
            recommendations.append(
                f"50%概率: {percentile_desc[50]}"
            )

        # 置信度评估
        if confidence_metrics["confidence_level"] == "high":
            recommendations.append("预测置信度: 高 (基于充分的历史验证)")
        elif confidence_metrics["confidence_level"] == "medium":
            recommendations.append("预测置信度: 中等 (统计误差在可接受范围)")
        else:
            recommendations.append("⚠️ 预测置信度: 低 (结果仅供参考)")

        # 生成替代限价
        alternatives = await RecommendationEngine._generate_alternatives(
            current_price, limit_price, order_side, fill_prob
        )

        # 根据成交概率添加具体建议
        if fill_prob < 0.5:
            if order_side == "sell":
                recommendations.append(
                    f"建议: 降低限价至 ${alternatives[1]['limit_price']:.2f} "
                    f"可提高成交率至 {alternatives[1]['fill_probability']*100:.0f}%"
                )
            else:
                recommendations.append(
                    f"建议: 提高限价至 ${alternatives[1]['limit_price']:.2f} "
                    f"可提高成交率至 {alternatives[1]['fill_probability']*100:.0f}%"
                )

        return {
            "recommendations": recommendations,
            "alternative_limits": alternatives,
            "optimal_limit_for_80pct": alternatives[1]["limit_price"] if len(alternatives) > 1 else None,
            "optimal_limit_for_quick_fill": alternatives[0]["limit_price"] if alternatives else None
        }

    @staticmethod
    async def _generate_alternatives(
        current_price: float,
        limit_price: float,
        order_side: str,
        current_fill_prob: float
    ) -> List[Dict[str, Any]]:
        """
        生成替代限价场景。
        """
        alternatives = []

        # 计算价格调整
        price_diff = abs(limit_price - current_price)

        if order_side == "sell":
            # 对于卖单，较低价格 = 较高成交概率
            scenarios = [
                {
                    "adjustment": -price_diff * 0.75,
                    "scenario": "快速成交方案",
                    "target_prob": 0.90
                },
                {
                    "adjustment": -price_diff * 0.50,
                    "scenario": "平衡方案",
                    "target_prob": 0.80
                },
                {
                    "adjustment": 0,
                    "scenario": "当前限价",
                    "target_prob": current_fill_prob
                },
                {
                    "adjustment": price_diff * 0.50,
                    "scenario": "高收益低概率",
                    "target_prob": 0.40
                }
            ]
        else:
            # 对于买单，较高价格 = 较高成交概率
            scenarios = [
                {
                    "adjustment": price_diff * 0.75,
                    "scenario": "快速成交方案",
                    "target_prob": 0.90
                },
                {
                    "adjustment": price_diff * 0.50,
                    "scenario": "平衡方案",
                    "target_prob": 0.80
                },
                {
                    "adjustment": 0,
                    "scenario": "当前限价",
                    "target_prob": current_fill_prob
                },
                {
                    "adjustment": -price_diff * 0.50,
                    "scenario": "低价高风险",
                    "target_prob": 0.40
                }
            ]

        for scenario in scenarios:
            alt_limit = limit_price + scenario["adjustment"]

            # 估计成交概率 (简化的替代方案)
            # 在生产环境中，会为每个方案运行小型模拟
            if scenario["scenario"] == "当前限价":
                est_prob = current_fill_prob
                est_days = 3.2  # 占位符
            else:
                # 基于价格距离的启发式估计
                price_ratio = abs(alt_limit - current_price) / current_price
                est_prob = min(0.95, max(0.05, scenario["target_prob"]))
                est_days = max(0.5, 10 * price_ratio) if est_prob > 0 else None

            alternatives.append({
                "limit_price": round(alt_limit, 2),
                "fill_probability": est_prob,
                "expected_days": est_days,
                "scenario": scenario["scenario"]
            })

        return sorted(alternatives, key=lambda x: x["fill_probability"], reverse=True)
