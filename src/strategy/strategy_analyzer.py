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


class DeltaBasedCallStrikeSelector:
    """
    基于Delta的Call期权执行价选择器
    专为covered call策略优化
    """
    
    def __init__(
        self,
        min_open_interest: int = 50,
        min_volume: int = 10,
        max_spread_pct: float = 0.15,
        liquidity_weight: float = 0.25,
        return_weight: float = 0.4,
        upside_weight: float = 0.2,
        risk_weight: float = 0.15
    ):
        self.min_open_interest = min_open_interest
        self.min_volume = min_volume
        self.max_spread_pct = max_spread_pct
        self.liquidity_weight = liquidity_weight
        self.return_weight = return_weight
        self.upside_weight = upside_weight
        self.risk_weight = risk_weight
    
    async def analyze_call_option_chain(
        self,
        option_chain: List[OptionContract],
        target_delta_range: Tuple[float, float],
        underlying_price: float,
        resistance_levels: Dict[str, float],
        strategy_type: str = "income"
    ) -> List[Dict[str, Any]]:
        """
        实现covered call特定的call期权链分析
        
        Args:
            option_chain: 期权链数据
            target_delta_range: 目标Delta范围 (min, max) - 正值
            underlying_price: 标的价格
            resistance_levels: 技术阻力位字典
            strategy_type: 策略类型 ("income" 或 "exit")
            
        Returns:
            分析后的call期权指标列表，按综合评分排序
        """
        analyzed_options = []
        delta_min, delta_max = target_delta_range
        
        for option in option_chain:
            # 1. 仅分析call期权
            if option.option_type != "call":
                continue
            
            # 2. 确保是价外期权 (strike > underlying_price)
            if option.strike <= underlying_price:
                continue
            
            # 3. Delta范围过滤 (call期权delta为正值)
            if not self._is_within_delta_range(option, delta_min, delta_max):
                continue
            
            # 4. 基础流动性检查
            if not self._meets_liquidity_requirements(option):
                continue
            
            # 5. 计算call期权特有指标
            metrics = self._calculate_call_option_metrics(
                option, underlying_price, resistance_levels, strategy_type
            )
            
            if metrics:
                analyzed_options.append(metrics)
        
        # 6. 按综合评分排序
        return sorted(
            analyzed_options,
            key=lambda x: x["composite_score"],
            reverse=True
        )
    
    def _is_within_delta_range(
        self,
        option: OptionContract,
        delta_min: float,
        delta_max: float
    ) -> bool:
        """检查call期权是否在目标Delta范围内"""
        if not option.greeks:
            return False
        
        delta = option.greeks.get("delta", 0)
        # Call期权delta应该为正值
        return delta_min <= delta <= delta_max and delta > 0
    
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
    
    def _calculate_call_option_metrics(
        self,
        option: OptionContract,
        underlying_price: float,
        resistance_levels: Dict[str, float],
        strategy_type: str
    ) -> Optional[Dict[str, Any]]:
        """计算call期权的covered call策略指标"""
        
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
            time_to_expiry = days_to_expiry / 365.0
            
            # Covered Call特有指标
            upside_capture = ((strike - underlying_price) / underlying_price) * 100
            premium_yield = (mid_price / underlying_price) * 100
            
            # 收益指标
            total_return_if_called = self._calculate_total_return_if_called(
                mid_price, strike, underlying_price
            )
            annualized_return = total_return_if_called * (365 / days_to_expiry)
            
            # 风险指标
            assignment_probability = delta * 100  # Delta近似为分配概率
            downside_protection = premium_yield  # 权利金提供的下跌保护
            
            # 机会成本分析
            opportunity_cost = self._calculate_opportunity_cost(
                strike, underlying_price, option
            )
            
            # 技术分析评分
            technical_score = self._calculate_technical_score(
                strike, resistance_levels
            )
            
            # 流动性评分
            liquidity_score = self._calculate_liquidity_score(option)
            
            # 风险评分
            risk_score = self._calculate_call_risk_score(option, underlying_price)
            
            # 综合评分
            composite_score = self._calculate_call_composite_score(
                annualized_return, liquidity_score, assignment_probability,
                upside_capture, technical_score, strategy_type
            )
            
            return {
                "symbol": option.symbol,
                "strike": strike,
                "expiration": option.expiration_date,
                "days_to_expiry": days_to_expiry,
                "delta": delta,
                "premium": mid_price,
                "bid": bid,
                "ask": ask,
                "bid_ask_spread": bid_ask_spread,
                "open_interest": option.open_interest or 0,
                "volume": option.volume or 0,
                "implied_volatility": implied_vol,
                "theta": theta,
                
                # Covered Call特有指标
                "upside_capture": upside_capture,
                "premium_yield": premium_yield,
                "total_return_if_called": total_return_if_called,
                "annualized_return": annualized_return,
                "assignment_probability": assignment_probability,
                "downside_protection": downside_protection,
                "opportunity_cost": opportunity_cost,
                
                # 评分指标
                "technical_score": technical_score,
                "liquidity_score": liquidity_score,
                "risk_score": risk_score,
                "composite_score": composite_score
            }
            
        except Exception as e:
            print(f"Error calculating call option metrics for {option.symbol}: {e}")
            return None
    
    def _calculate_total_return_if_called(
        self,
        premium: float,
        strike: float,
        underlying_price: float
    ) -> float:
        """计算如果期权被行权的总收益率"""
        # 总收益 = 权利金收益 + 股票升值收益
        premium_return = (premium / underlying_price) * 100
        appreciation_return = ((strike - underlying_price) / underlying_price) * 100
        return premium_return + appreciation_return
    
    def _calculate_opportunity_cost(
        self,
        strike: float,
        underlying_price: float,
        option: OptionContract
    ) -> float:
        """
        计算机会成本
        如果股票价格超过执行价，损失的潜在收益
        """
        # 假设股票可能上涨20%的情况下的机会成本
        potential_upside = underlying_price * 0.20
        current_upside_to_strike = strike - underlying_price
        
        if potential_upside > current_upside_to_strike:
            opportunity_cost_per_share = potential_upside - current_upside_to_strike
            return (opportunity_cost_per_share / underlying_price) * 100
        
        return 0  # 没有机会成本
    
    def _calculate_technical_score(
        self,
        strike: float,
        resistance_levels: Dict[str, float]
    ) -> float:
        """
        基于技术阻力位计算执行价评分
        执行价接近阻力位得分更高
        """
        if not resistance_levels:
            return 50  # 中性分数
        
        scores = []
        for level_name, level_price in resistance_levels.items():
            if level_price and level_price > 0:
                # 执行价在阻力位附近得分更高
                distance_pct = abs(strike - level_price) / level_price
                
                if distance_pct <= 0.02:  # 2%内
                    scores.append(90)
                elif distance_pct <= 0.05:  # 5%内
                    scores.append(75)
                elif distance_pct <= 0.10:  # 10%内
                    scores.append(60)
                else:
                    scores.append(40)
        
        return max(scores) if scores else 50
    
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
    
    def _calculate_call_risk_score(
        self,
        option: OptionContract,
        underlying_price: float
    ) -> float:
        """
        计算call期权风险评分 (0-100，100为最高风险)
        基于Delta、价外程度和时间衰减
        """
        greeks = option.greeks or {}
        delta = greeks.get("delta", 0)
        theta = abs(greeks.get("theta", 0))
        strike = option.strike
        
        # Delta风险 (0-40分) - delta越高分配概率越高
        delta_risk = delta * 40
        
        # 价外程度风险 (0-40分) - 越价外风险越低
        if underlying_price > 0:
            otm_degree = (strike - underlying_price) / underlying_price
            # 价外10%以上风险很低，价外2%以下风险很高
            if otm_degree >= 0.10:
                otm_risk = 10
            elif otm_degree >= 0.05:
                otm_risk = 20
            elif otm_degree >= 0.02:
                otm_risk = 30
            else:
                otm_risk = 40
        else:
            otm_risk = 40
        
        # 时间衰减风险 (0-20分) - 对于call卖方，theta是有利的
        theta_risk = max(0, 20 - min(theta * 1000, 20))
        
        return delta_risk + otm_risk + theta_risk
    
    def _calculate_call_composite_score(
        self,
        annualized_return: float,
        liquidity_score: float,
        assignment_prob: float,
        upside_capture: float,
        technical_score: float,
        strategy_type: str
    ) -> float:
        """
        计算call期权的综合评分
        根据策略类型调整权重
        """
        # 标准化各项评分到0-100
        return_score = min(annualized_return, 100)  # 年化收益最高100%
        liquid_score = liquidity_score  # 已经是0-100
        tech_score = technical_score  # 已经是0-100
        
        if strategy_type == "income":
            # 收入策略：重视收益和低分配概率，保留上涨空间
            assignment_score = max(0, 100 - assignment_prob * 2)  # 分配概率越低越好
            upside_score = min(upside_capture, 50)  # 适度上涨空间即可
            
            composite = (
                return_score * self.return_weight +
                liquid_score * self.liquidity_weight +
                assignment_score * self.risk_weight +
                upside_score * self.upside_weight +
                tech_score * 0.1
            )
        else:  # exit
            # 减仓策略：可接受更高分配概率，重视到执行价的收益
            assignment_score = min(assignment_prob, 70)  # 适度分配概率是好的
            upside_score = upside_capture  # 到执行价的完整收益
            
            composite = (
                return_score * self.return_weight +
                liquid_score * self.liquidity_weight +
                assignment_score * 0.1 +
                upside_score * self.upside_weight +
                tech_score * self.risk_weight
            )
        
        return min(composite, 100)


class TechnicalAnalysisIntegrator:
    """技术分析集成器，为期权策略提供技术分析支持"""
    
    @staticmethod
    def analyze_resistance_proximity(
        strike_prices: List[float],
        resistance_levels: Dict[str, float],
        tolerance_pct: float = 0.05
    ) -> Dict[float, Dict[str, Any]]:
        """
        分析执行价与阻力位的接近程度
        
        Args:
            strike_prices: 执行价列表
            resistance_levels: 阻力位字典
            tolerance_pct: 容忍度百分比 (5% = 0.05)
            
        Returns:
            每个执行价的阻力位分析结果
        """
        results = {}
        
        for strike in strike_prices:
            proximity_analysis = {
                "near_resistance": False,
                "closest_resistance": None,
                "distance_pct": float('inf'),
                "resistance_type": None,
                "score": 0
            }
            
            # 检查与各阻力位的距离
            for resistance_name, resistance_level in resistance_levels.items():
                if resistance_level and resistance_level > 0:
                    distance_pct = abs(strike - resistance_level) / resistance_level
                    
                    if distance_pct < proximity_analysis["distance_pct"]:
                        proximity_analysis.update({
                            "closest_resistance": resistance_level,
                            "distance_pct": distance_pct,
                            "resistance_type": resistance_name
                        })
                    
                    # 在容忍度范围内认为接近阻力位
                    if distance_pct <= tolerance_pct:
                        proximity_analysis["near_resistance"] = True
            
            # 计算技术分析评分
            if proximity_analysis["distance_pct"] <= 0.02:  # 2%内
                proximity_analysis["score"] = 90
            elif proximity_analysis["distance_pct"] <= 0.05:  # 5%内
                proximity_analysis["score"] = 75
            elif proximity_analysis["distance_pct"] <= 0.10:  # 10%内
                proximity_analysis["score"] = 60
            else:
                proximity_analysis["score"] = 40
            
            results[strike] = proximity_analysis
        
        return results
    
    @staticmethod
    def calculate_momentum_bias(
        current_price: float,
        sma_20: Optional[float],
        sma_50: Optional[float]
    ) -> Dict[str, Any]:
        """
        计算动量偏向，影响期权策略选择
        
        Returns:
            动量分析结果，包括偏向和强度
        """
        momentum_analysis = {
            "bias": "neutral",
            "strength": "weak",
            "score": 50,
            "recommendation": "balanced_strategy"
        }
        
        if not sma_20:
            return momentum_analysis
        
        # 基于20日均线的基础偏向
        if current_price > sma_20 * 1.02:  # 超出2%
            momentum_analysis["bias"] = "bullish"
            momentum_analysis["score"] = 65
        elif current_price < sma_20 * 0.98:  # 低于2%
            momentum_analysis["bias"] = "bearish"
            momentum_analysis["score"] = 35
        
        # 如果有50日均线，进一步细化
        if sma_50:
            if current_price > sma_50 and current_price > sma_20:
                momentum_analysis.update({
                    "bias": "strong_bullish",
                    "strength": "strong",
                    "score": 80,
                    "recommendation": "higher_strike_preference"
                })
            elif current_price < sma_50 and current_price < sma_20:
                momentum_analysis.update({
                    "bias": "strong_bearish",
                    "strength": "strong", 
                    "score": 20,
                    "recommendation": "lower_strike_preference"
                })
        
        return momentum_analysis
    
    @staticmethod
    def suggest_strike_adjustments(
        base_strikes: List[float],
        momentum_bias: Dict[str, Any],
        resistance_analysis: Dict[float, Dict[str, Any]]
    ) -> Dict[str, List[float]]:
        """
        基于技术分析建议执行价调整
        
        Returns:
            调整建议，包括preferred, alternative, avoid等分类
        """
        suggestions = {
            "preferred": [],
            "alternative": [],
            "avoid": []
        }
        
        momentum_score = momentum_bias.get("score", 50)
        
        for strike in base_strikes:
            resistance_info = resistance_analysis.get(strike, {})
            technical_score = resistance_info.get("score", 50)
            
            # 综合评分
            combined_score = (momentum_score + technical_score) / 2
            
            if combined_score >= 70:
                suggestions["preferred"].append(strike)
            elif combined_score >= 50:
                suggestions["alternative"].append(strike)
            else:
                suggestions["avoid"].append(strike)
        
        return suggestions


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