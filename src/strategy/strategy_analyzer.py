"""
策略分析器模块

提供期权链分析、执行价选择和策略评估的核心算法，包括：
- 基于Delta的执行价选择
- 期权链循环分析
- 流动性和风险评分
- 策略优化算法
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..provider.tradier.client import OptionContract


@dataclass
class AnalysisMetrics:
    """分析指标数据类"""
    symbol: str
    strike: float
    delta: float
    premium: float
    bid_ask_spread: float
    open_interest: int
    volume: int
    implied_volatility: float
    theta: float
    premium_yield: float
    annualized_return: float
    assignment_probability: float
    liquidity_score: float
    risk_score: float
    composite_score: float


class DeltaBasedStrikeSelector:
    """基于Delta的执行价选择器"""
    
    def __init__(
        self,
        min_open_interest: int = 50,
        min_volume: int = 10,
        max_spread_pct: float = 0.15,
        liquidity_weight: float = 0.3,
        return_weight: float = 0.5,
        risk_weight: float = 0.2
    ):
        self.min_open_interest = min_open_interest
        self.min_volume = min_volume
        self.max_spread_pct = max_spread_pct
        self.liquidity_weight = liquidity_weight
        self.return_weight = return_weight
        self.risk_weight = risk_weight
    
    async def analyze_option_chain_loop(
        self,
        option_chain: List[OptionContract],
        target_delta_range: Tuple[float, float],
        underlying_price: float,
        strategy_type: str = "income"
    ) -> List[AnalysisMetrics]:
        """
        实现期权链分析循环逻辑
        
        Args:
            option_chain: 期权链数据
            target_delta_range: 目标Delta范围 (min, max)
            underlying_price: 标的价格
            strategy_type: 策略类型 ("income" 或 "discount")
            
        Returns:
            分析后的期权指标列表，按综合评分排序
        """
        analyzed_options = []
        delta_min, delta_max = target_delta_range
        
        for option in option_chain:
            # 1. Delta范围过滤
            if not self._is_within_delta_range(option, delta_min, delta_max):
                continue
            
            # 2. 基础流动性检查
            if not self._meets_liquidity_requirements(option):
                continue
            
            # 3. 计算全面指标
            metrics = self._calculate_comprehensive_metrics(
                option, underlying_price, strategy_type
            )
            
            if metrics:
                analyzed_options.append(metrics)
        
        # 4. 按综合评分排序
        return sorted(
            analyzed_options,
            key=lambda x: x.composite_score,
            reverse=True
        )
    
    def _is_within_delta_range(
        self,
        option: OptionContract,
        delta_min: float,
        delta_max: float
    ) -> bool:
        """检查期权是否在目标Delta范围内"""
        if not option.greeks:
            return False
        
        delta = option.greeks.get("delta", 0)
        return delta_min <= delta <= delta_max
    
    def _meets_liquidity_requirements(self, option: OptionContract) -> bool:
        """检查期权是否满足流动性要求"""
        # 检查开放利益和成交量
        oi = option.open_interest or 0
        volume = option.volume or 0
        
        if oi < self.min_open_interest or volume < self.min_volume:
            return False
        
        # 检查买卖价差
        bid = option.bid or 0
        ask = option.ask or 0
        
        if bid <= 0 or ask <= 0:
            return False
        
        mid_price = (bid + ask) / 2
        spread_pct = (ask - bid) / mid_price
        
        return spread_pct <= self.max_spread_pct
    
    def _calculate_comprehensive_metrics(
        self,
        option: OptionContract,
        underlying_price: float,
        strategy_type: str
    ) -> Optional[AnalysisMetrics]:
        """计算期权的综合指标"""
        
        try:
            # 基础数据
            strike = option.strike
            bid = option.bid or 0
            ask = option.ask or 0
            mid_price = (bid + ask) / 2
            bid_ask_spread = ask - bid
            
            # 希腊字母
            greeks = option.greeks or {}
            delta = greeks.get("delta", 0)
            theta = greeks.get("theta", 0)
            implied_vol = greeks.get("mid_iv", 0)
            
            # 计算到期时间
            exp_date = datetime.strptime(option.expiration_date, "%Y-%m-%d").date()
            today = datetime.now().date()
            days_to_expiry = max((exp_date - today).days, 1)
            
            # 收益指标
            premium_yield = self._calculate_premium_yield(mid_price, underlying_price)
            annualized_return = self._calculate_annualized_return(
                mid_price, strike, days_to_expiry
            )
            
            # 风险指标
            assignment_probability = abs(delta) * 100
            liquidity_score = self._calculate_liquidity_score(option)
            risk_score = self._calculate_risk_score(option, underlying_price)
            
            # 综合评分
            composite_score = self._calculate_composite_score(
                annualized_return, liquidity_score, assignment_probability, strategy_type
            )
            
            return AnalysisMetrics(
                symbol=option.symbol,
                strike=strike,
                delta=delta,
                premium=mid_price,
                bid_ask_spread=bid_ask_spread,
                open_interest=option.open_interest or 0,
                volume=option.volume or 0,
                implied_volatility=implied_vol,
                theta=theta,
                premium_yield=premium_yield,
                annualized_return=annualized_return,
                assignment_probability=assignment_probability,
                liquidity_score=liquidity_score,
                risk_score=risk_score,
                composite_score=composite_score
            )
            
        except Exception as e:
            print(f"Error calculating metrics for {option.symbol}: {e}")
            return None
    
    def _calculate_premium_yield(self, premium: float, underlying_price: float) -> float:
        """计算权利金收益率"""
        return (premium / underlying_price) * 100
    
    def _calculate_annualized_return(
        self,
        premium: float,
        strike: float,
        days_to_expiry: int
    ) -> float:
        """计算年化收益率"""
        if strike <= 0 or days_to_expiry <= 0:
            return 0
        
        return (premium / strike) * (365 / days_to_expiry) * 100
    
    def _calculate_liquidity_score(self, option: OptionContract) -> float:
        """
        计算流动性评分 (0-100)
        基于开放利益、成交量和买卖价差
        """
        oi = option.open_interest or 0
        volume = option.volume or 0
        bid = option.bid or 0
        ask = option.ask or 0
        
        if bid <= 0 or ask <= 0:
            return 0
        
        mid_price = (bid + ask) / 2
        spread_pct = (ask - bid) / mid_price
        
        # 开放利益评分 (0-40分)
        oi_score = min(oi / 1000, 1) * 40
        
        # 成交量评分 (0-30分)
        volume_score = min(volume / 100, 1) * 30
        
        # 价差评分 (0-30分) - 价差越小评分越高
        spread_score = max(0, (0.1 - spread_pct) / 0.1) * 30
        
        return oi_score + volume_score + spread_score
    
    def _calculate_risk_score(self, option: OptionContract, underlying_price: float) -> float:
        """
        计算风险评分 (0-100，100为最高风险)
        基于Delta、价内程度和时间衰减
        """
        greeks = option.greeks or {}
        delta = abs(greeks.get("delta", 0))
        theta = abs(greeks.get("theta", 0))
        strike = option.strike
        
        # Delta风险 (0-40分)
        delta_risk = delta * 40
        
        # 价内程度风险 (0-40分)
        if underlying_price > 0:
            moneyness = abs(underlying_price - strike) / underlying_price
            moneyness_risk = min(moneyness * 100, 40)
        else:
            moneyness_risk = 40
        
        # 时间衰减风险 (0-20分) - Theta越大风险越高
        theta_risk = min(theta * 1000, 20)
        
        return delta_risk + moneyness_risk + theta_risk
    
    def _calculate_composite_score(
        self,
        annualized_return: float,
        liquidity_score: float,
        assignment_prob: float,
        strategy_type: str
    ) -> float:
        """
        计算综合评分
        根据策略类型调整权重
        """
        # 标准化各项评分到0-100
        return_score = min(annualized_return, 100)  # 年化收益最高100%
        liquid_score = liquidity_score  # 已经是0-100
        
        if strategy_type == "income":
            # 收入策略：低分配概率更重要
            assignment_score = max(0, 100 - assignment_prob * 2)  # 分配概率越低评分越高
            composite = (
                return_score * 0.4 +
                liquid_score * 0.3 +
                assignment_score * 0.3
            )
        else:  # discount
            # 折价策略：可接受更高分配概率
            assignment_score = min(assignment_prob, 100)  # 适度的分配概率是好的
            composite = (
                return_score * 0.5 +
                liquid_score * 0.4 +
                assignment_score * 0.1
            )
        
        return composite


class OptionChainAnalyzer:
    """期权链分析器"""
    
    def __init__(self):
        self.strike_selector = DeltaBasedStrikeSelector()
    
    async def filter_and_analyze_chain(
        self,
        option_chain: List[OptionContract],
        underlying_price: float,
        analysis_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        过滤和分析期权链
        
        Args:
            option_chain: 期权链数据
            underlying_price: 标的价格
            analysis_params: 分析参数
                - delta_range: Delta范围
                - strategy_type: 策略类型
                - capital_limit: 资金限制
                - min_liquidity: 最小流动性要求
                
        Returns:
            分析结果字典
        """
        delta_range = analysis_params.get("delta_range", (-0.30, -0.10))
        strategy_type = analysis_params.get("strategy_type", "income")
        capital_limit = analysis_params.get("capital_limit")
        
        # 过滤看跌期权
        put_options = [
            opt for opt in option_chain
            if opt.option_type == "put"
        ]
        
        # 分析期权链
        analyzed_options = await self.strike_selector.analyze_option_chain_loop(
            put_options, delta_range, underlying_price, strategy_type
        )
        
        # 应用资金限制
        if capital_limit:
            analyzed_options = [
                opt for opt in analyzed_options
                if opt.strike * 100 <= capital_limit
            ]
        
        # 生成统计摘要
        summary = self._generate_analysis_summary(analyzed_options, underlying_price)
        
        return {
            "analyzed_options": analyzed_options,
            "summary": summary,
            "total_candidates": len(analyzed_options),
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def _generate_analysis_summary(
        self,
        analyzed_options: List[AnalysisMetrics],
        underlying_price: float
    ) -> Dict[str, Any]:
        """生成分析摘要"""
        
        if not analyzed_options:
            return {
                "status": "no_options",
                "message": "未找到符合条件的期权"
            }
        
        # 统计指标
        returns = [opt.annualized_return for opt in analyzed_options]
        deltas = [opt.delta for opt in analyzed_options]
        liquidity_scores = [opt.liquidity_score for opt in analyzed_options]
        
        return {
            "status": "success",
            "total_options": len(analyzed_options),
            "return_stats": {
                "min": min(returns),
                "max": max(returns),
                "avg": sum(returns) / len(returns),
                "median": sorted(returns)[len(returns) // 2]
            },
            "delta_stats": {
                "min": min(deltas),
                "max": max(deltas),
                "avg": sum(deltas) / len(deltas)
            },
            "liquidity_stats": {
                "avg_score": sum(liquidity_scores) / len(liquidity_scores),
                "min_score": min(liquidity_scores),
                "max_score": max(liquidity_scores)
            },
            "best_option": {
                "symbol": analyzed_options[0].symbol,
                "strike": analyzed_options[0].strike,
                "score": analyzed_options[0].composite_score
            } if analyzed_options else None
        }


def analyze_option_chain_loop(
    option_chain: List[OptionContract],
    target_delta_range: Tuple[float, float],
    underlying_price: float,
    strategy_type: str = "income"
) -> List[Dict[str, Any]]:
    """
    期权链分析循环的便捷函数
    
    Args:
        option_chain: 期权链数据
        target_delta_range: 目标Delta范围
        underlying_price: 标的价格
        strategy_type: 策略类型
        
    Returns:
        分析结果列表
    """
    selector = DeltaBasedStrikeSelector()
    
    # 异步调用需要在同步函数中处理
    import asyncio
    
    async def _analyze():
        return await selector.analyze_option_chain_loop(
            option_chain, target_delta_range, underlying_price, strategy_type
        )
    
    try:
        # 获取或创建事件循环
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果循环正在运行，创建新的任务
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _analyze())
                metrics = future.result()
        else:
            metrics = loop.run_until_complete(_analyze())
    except RuntimeError:
        # 如果没有事件循环，创建新的
        metrics = asyncio.run(_analyze())
    
    # 转换为字典格式
    return [
        {
            "symbol": m.symbol,
            "strike": m.strike,
            "delta": m.delta,
            "premium": m.premium,
            "annualized_return": m.annualized_return,
            "assignment_probability": m.assignment_probability,
            "liquidity_score": m.liquidity_score,
            "risk_score": m.risk_score,
            "composite_score": m.composite_score
        }
        for m in metrics
    ]