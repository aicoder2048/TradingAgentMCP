"""
日内波动率估计模块

基于历史OHLC数据估计日内价格波动范围，用于改进限价订单成交概率预测。
考虑日内高低点而非仅收盘价，更准确地评估限价订单的触及概率。
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass


@dataclass
class IntradayRangeEstimate:
    """日内范围估计结果"""
    avg_high_low_ratio: float  # 平均(high-low)/close比率
    avg_true_range: float      # 平均真实范围（ATR）
    intraday_volatility: float # 日内波动率
    high_percentile_95: float  # 95百分位高点偏差
    low_percentile_95: float   # 95百分位低点偏差
    sample_days: int           # 样本天数


class IntradayVolatilityEstimator:
    """
    日内波动率估计器

    基于历史OHLC数据估计未来的日内价格范围（高低点）。
    用于改进期权限价订单成交概率预测，考虑日内触及而非仅收盘价。
    """

    def __init__(self, tradier_client):
        """
        初始化估计器

        Args:
            tradier_client: TradierClient实例，用于获取历史数据
        """
        self.tradier_client = tradier_client
        self._cache = {}  # 缓存估计结果

    async def estimate_intraday_range(
        self,
        symbol: str,
        lookback_days: int = 90,
        use_cache: bool = True
    ) -> IntradayRangeEstimate:
        """
        基于历史数据估计日内价格范围的统计特征

        Args:
            symbol: 股票代码
            lookback_days: 回溯天数（默认90天）
            use_cache: 是否使用缓存

        Returns:
            IntradayRangeEstimate对象，包含日内范围统计指标
        """
        # 检查缓存
        cache_key = f"{symbol}_{lookback_days}"
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        # 获取历史OHLC数据
        from ..stock.history_data import get_stock_history_data

        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days + 30)  # 多取一些以应对节假日

        try:
            history_result = await get_stock_history_data(
                symbol=symbol,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                include_indicators=False,
                tradier_client=self.tradier_client
            )

            if history_result.get("status") != "success":
                # 回退到默认值
                return self._get_default_estimate()

            # 提取OHLC数据
            data = history_result["preview_records"]

            if len(data) < 20:  # 至少需要20天数据
                return self._get_default_estimate()

            # 计算各项指标
            high_low_ratios = []
            true_ranges = []
            high_deviations = []  # (high - close) / close
            low_deviations = []   # (close - low) / close

            for i, record in enumerate(data):
                high = record["high"]
                low = record["low"]
                close = record["close"]

                if close > 0:
                    # 高低点比率
                    hl_ratio = (high - low) / close
                    high_low_ratios.append(hl_ratio)

                    # 高点偏差和低点偏差
                    high_dev = (high - close) / close
                    low_dev = (close - low) / close
                    high_deviations.append(high_dev)
                    low_deviations.append(low_dev)

                    # 真实范围（ATR的基础）
                    if i > 0:
                        prev_close = data[i-1]["close"]
                        tr = max(
                            high - low,
                            abs(high - prev_close),
                            abs(low - prev_close)
                        )
                        true_ranges.append(tr)

            # 计算统计指标
            avg_hl_ratio = np.mean(high_low_ratios)
            avg_tr = np.mean(true_ranges) if true_ranges else avg_hl_ratio * data[-1]["close"]

            # 日内波动率（年化）
            # 使用Parkinson波动率估计：基于高低点的波动率估计
            parkinson_vol = self._calculate_parkinson_volatility(data)

            # 95百分位的高低点偏差
            high_p95 = np.percentile(high_deviations, 95)
            low_p95 = np.percentile(low_deviations, 95)

            estimate = IntradayRangeEstimate(
                avg_high_low_ratio=float(avg_hl_ratio),
                avg_true_range=float(avg_tr),
                intraday_volatility=float(parkinson_vol),
                high_percentile_95=float(high_p95),
                low_percentile_95=float(low_p95),
                sample_days=len(data)
            )

            # 缓存结果
            if use_cache:
                self._cache[cache_key] = estimate

            return estimate

        except Exception as e:
            print(f"⚠️ 日内波动率估计失败: {str(e)}")
            return self._get_default_estimate()

    def _calculate_parkinson_volatility(self, data: list) -> float:
        """
        计算Parkinson波动率（基于高低点的波动率估计）

        Parkinson公式：σ = sqrt(1/(4n*ln(2)) * Σ(ln(High/Low))²)

        Args:
            data: OHLC数据列表

        Returns:
            年化波动率
        """
        if len(data) < 2:
            return 0.3  # 默认30%

        log_hl_ratios = []
        for record in data:
            if record["high"] > 0 and record["low"] > 0:
                log_hl = np.log(record["high"] / record["low"])
                log_hl_ratios.append(log_hl ** 2)

        if not log_hl_ratios:
            return 0.3

        # Parkinson估计器
        n = len(log_hl_ratios)
        variance = np.sum(log_hl_ratios) / (4 * n * np.log(2))

        # 年化（假设252个交易日）
        annual_volatility = np.sqrt(variance * 252)

        # 限制在合理范围内
        return float(np.clip(annual_volatility, 0.1, 2.0))

    def _get_default_estimate(self) -> IntradayRangeEstimate:
        """
        返回默认估计值（当无法获取历史数据时）
        """
        return IntradayRangeEstimate(
            avg_high_low_ratio=0.025,  # 2.5%的日内范围
            avg_true_range=5.0,        # 假设$5的ATR
            intraday_volatility=0.30,  # 30%年化波动率
            high_percentile_95=0.015,  # 1.5%的高点偏差
            low_percentile_95=0.015,   # 1.5%的低点偏差
            sample_days=0
        )

    def estimate_option_intraday_range(
        self,
        option_close: float,
        stock_close: float,
        stock_high: float,
        stock_low: float,
        delta: float,
        gamma: float
    ) -> Dict[str, float]:
        """
        基于股票的日内范围估计期权的日内高低点

        使用Delta和Gamma近似：
        ΔOption ≈ Delta * ΔStock + 0.5 * Gamma * ΔStock²

        Args:
            option_close: 期权收盘价
            stock_close: 股票收盘价
            stock_high: 股票日内最高价
            stock_low: 股票日内最低价
            delta: 期权Delta
            gamma: 期权Gamma

        Returns:
            {'high': 期权估计最高价, 'low': 期权估计最低价}
        """
        # 计算股票的价格变化
        delta_stock_high = stock_high - stock_close
        delta_stock_low = stock_low - stock_close

        # 使用Delta + Gamma近似计算期权价格变化
        option_delta_high = (
            delta * delta_stock_high +
            0.5 * gamma * (delta_stock_high ** 2)
        )

        option_delta_low = (
            delta * delta_stock_low +
            0.5 * gamma * (delta_stock_low ** 2)
        )

        # 计算期权的估计高低点
        option_high = option_close + option_delta_high
        option_low = option_close + option_delta_low

        # 确保高低点逻辑正确（high > low）
        estimated_high = max(option_high, option_low)
        estimated_low = min(option_high, option_low)

        # 期权价格不能为负
        estimated_low = max(0, estimated_low)
        estimated_high = max(0, estimated_high)

        return {
            "high": float(estimated_high),
            "low": float(estimated_low)
        }

    async def simulate_intraday_paths(
        self,
        close_prices: np.ndarray,
        stock_close_prices: np.ndarray,
        delta: float,
        gamma: float,
        symbol: str,
        lookback_days: int = 90
    ) -> Dict[str, np.ndarray]:
        """
        为蒙特卡洛模拟的收盘价路径生成对应的日内高低点路径

        Args:
            close_prices: 期权收盘价路径数组 (num_paths, num_days)
            stock_close_prices: 股票收盘价路径数组 (num_paths, num_days)
            delta: 期权Delta
            gamma: 期权Gamma
            symbol: 股票代码
            lookback_days: 历史数据回溯天数

        Returns:
            {
                'close': 收盘价路径,
                'high': 日内最高价路径,
                'low': 日内最低价路径
            }
        """
        # 获取日内范围估计
        range_estimate = await self.estimate_intraday_range(
            symbol=symbol,
            lookback_days=lookback_days
        )

        num_paths, num_days = close_prices.shape

        high_paths = np.zeros_like(close_prices)
        low_paths = np.zeros_like(close_prices)

        # 为每个路径的每一天估计高低点
        for path_idx in range(num_paths):
            for day_idx in range(num_days):
                stock_close = stock_close_prices[path_idx, day_idx]
                option_close = close_prices[path_idx, day_idx]

                # 使用对数正态分布估计股票的日内高低点
                # 基于历史统计的百分位数
                stock_high = stock_close * (1 + range_estimate.high_percentile_95)
                stock_low = stock_close * (1 - range_estimate.low_percentile_95)

                # 映射到期权价格
                option_range = self.estimate_option_intraday_range(
                    option_close=option_close,
                    stock_close=stock_close,
                    stock_high=stock_high,
                    stock_low=stock_low,
                    delta=delta,
                    gamma=gamma
                )

                high_paths[path_idx, day_idx] = option_range["high"]
                low_paths[path_idx, day_idx] = option_range["low"]

        return {
            "close": close_prices,
            "high": high_paths,
            "low": low_paths
        }
