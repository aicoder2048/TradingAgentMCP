"""
风险计算器模块

提供期权策略的风险评估和计算功能，包括：
- 期权风险指标计算
- P&L情景分析
- 分配概率评估
- 风险限额监控
- VaR和压力测试
"""

import numpy as np
import math
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from scipy import stats

from ..provider.tradier.client import OptionContract


@dataclass
class RiskMetrics:
    """风险指标数据类"""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    implied_volatility: float
    time_decay_per_day: float
    assignment_probability: float
    liquidity_risk: float
    concentration_risk: float
    var_1_day: float
    var_5_day: float


@dataclass
class PLScenario:
    """P&L情景数据类"""
    scenario_name: str
    underlying_price: float
    days_forward: int
    option_value: float
    pnl: float
    pnl_percentage: float
    probability: float


class OptionRiskCalculator:
    """期权风险计算器"""
    
    def __init__(self, risk_free_rate: float = 0.05):
        self.risk_free_rate = risk_free_rate
    
    def calculate_option_risk_metrics(
        self,
        option: OptionContract,
        underlying_price: float,
        portfolio_size: Optional[int] = 1
    ) -> RiskMetrics:
        """
        计算期权的综合风险指标
        
        Args:
            option: 期权合约数据
            underlying_price: 标的当前价格
            portfolio_size: 组合规模（合约数量）
            
        Returns:
            风险指标对象
        """
        greeks = option.greeks or {}
        
        # 基础希腊字母
        delta = greeks.get("delta", 0)
        gamma = greeks.get("gamma", 0)
        theta = greeks.get("theta", 0)
        vega = greeks.get("vega", 0)
        rho = greeks.get("rho", 0)
        iv = greeks.get("mid_iv", 0)
        
        # 计算每日时间衰减
        time_decay_per_day = abs(theta) * 100  # 每份合约每日衰减金额
        
        # 分配概率 (基于Delta)
        assignment_prob = abs(delta) * 100
        
        # 流动性风险评估
        liquidity_risk = self._calculate_liquidity_risk(option)
        
        # 集中度风险 (单一期权占组合比重)
        concentration_risk = min(portfolio_size / 10, 1) * 100  # 假设理想组合10个合约
        
        # VaR计算
        var_1_day = self._calculate_var(option, underlying_price, 1, 0.95)
        var_5_day = self._calculate_var(option, underlying_price, 5, 0.95)
        
        return RiskMetrics(
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            rho=rho,
            implied_volatility=iv,
            time_decay_per_day=time_decay_per_day,
            assignment_probability=assignment_prob,
            liquidity_risk=liquidity_risk,
            concentration_risk=concentration_risk,
            var_1_day=var_1_day,
            var_5_day=var_5_day
        )
    
    def calculate_pnl_scenarios(
        self,
        option: OptionContract,
        underlying_price: float,
        scenarios: Optional[List[Dict[str, Any]]] = None
    ) -> List[PLScenario]:
        """
        计算多种市场情景下的P&L
        
        Args:
            option: 期权合约
            underlying_price: 当前标的价格
            scenarios: 自定义情景列表，None则使用默认情景
            
        Returns:
            P&L情景列表
        """
        if scenarios is None:
            scenarios = self._get_default_scenarios(underlying_price)
        
        pnl_scenarios = []
        current_premium = (option.bid + option.ask) / 2 if option.bid and option.ask else 0
        
        for scenario in scenarios:
            name = scenario["name"]
            new_price = scenario["underlying_price"]
            days_forward = scenario.get("days_forward", 0)
            probability = scenario.get("probability", 0)
            
            # 计算新的期权价值
            new_option_value = self._calculate_option_value_at_price(
                option, new_price, days_forward
            )
            
            # P&L计算 (对于卖出期权，收入权利金，成本为期权价值变化)
            pnl = current_premium * 100 - new_option_value * 100  # 每份合约100股
            pnl_percentage = (pnl / (current_premium * 100)) * 100 if current_premium > 0 else 0
            
            pnl_scenarios.append(PLScenario(
                scenario_name=name,
                underlying_price=new_price,
                days_forward=days_forward,
                option_value=new_option_value,
                pnl=pnl,
                pnl_percentage=pnl_percentage,
                probability=probability
            ))
        
        return pnl_scenarios
    
    def assess_assignment_probability(
        self,
        option: OptionContract,
        underlying_price: float,
        volatility: Optional[float] = None
    ) -> Dict[str, float]:
        """
        评估期权分配概率
        
        Args:
            option: 期权合约
            underlying_price: 当前标的价格
            volatility: 波动率 (可选，默认使用IV)
            
        Returns:
            包含不同时间点分配概率的字典
        """
        strike = option.strike
        greeks = option.greeks or {}
        iv = volatility or greeks.get("mid_iv", 0.25)
        
        # 计算到期天数
        exp_date = datetime.strptime(option.expiration_date, "%Y-%m-%d").date()
        today = datetime.now().date()
        days_to_expiry = max((exp_date - today).days, 1)
        time_to_expiry = days_to_expiry / 365.0
        
        probabilities = {}
        
        # 当前分配概率 (基于Delta)
        current_delta = greeks.get("delta", 0)
        probabilities["current"] = abs(current_delta) * 100
        
        # 到期时分配概率 (使用Black-Scholes)
        if option.option_type == "put":
            # 看跌期权：股价低于执行价时被分配
            d1 = (math.log(underlying_price / strike) + 
                  (self.risk_free_rate + 0.5 * iv**2) * time_to_expiry) / (iv * math.sqrt(time_to_expiry))
            d2 = d1 - iv * math.sqrt(time_to_expiry)
            
            prob_itm = stats.norm.cdf(-d2) * 100  # N(-d2)为看跌期权价内概率
            probabilities["at_expiration"] = prob_itm
        else:
            # 看涨期权：股价高于执行价时被分配
            d1 = (math.log(underlying_price / strike) + 
                  (self.risk_free_rate + 0.5 * iv**2) * time_to_expiry) / (iv * math.sqrt(time_to_expiry))
            d2 = d1 - iv * math.sqrt(time_to_expiry)
            
            prob_itm = stats.norm.cdf(d2) * 100  # N(d2)为看涨期权价内概率
            probabilities["at_expiration"] = prob_itm
        
        # 不同时间点的概率
        time_points = [0.25, 0.5, 0.75]  # 25%, 50%, 75%的剩余时间
        for tp in time_points:
            remaining_time = time_to_expiry * tp
            if remaining_time > 0:
                prob = self._calculate_probability_at_time(
                    underlying_price, strike, remaining_time, iv, option.option_type
                )
                probabilities[f"at_{int(tp*100)}pct_time"] = prob
        
        return probabilities
    
    def _calculate_liquidity_risk(self, option: OptionContract) -> float:
        """
        计算流动性风险评分 (0-100，100为最高风险)
        """
        bid = option.bid or 0
        ask = option.ask or 0
        oi = option.open_interest or 0
        volume = option.volume or 0
        
        if bid <= 0 or ask <= 0:
            return 100  # 最高风险
        
        # 买卖价差风险
        mid_price = (bid + ask) / 2
        spread_pct = (ask - bid) / mid_price
        spread_risk = min(spread_pct * 1000, 50)  # 最高50分
        
        # 开放利益风险
        oi_risk = max(0, 25 - min(oi / 100, 25))  # 最高25分
        
        # 成交量风险
        volume_risk = max(0, 25 - min(volume / 50, 25))  # 最高25分
        
        return spread_risk + oi_risk + volume_risk
    
    def _calculate_var(
        self,
        option: OptionContract,
        underlying_price: float,
        days: int,
        confidence: float
    ) -> float:
        """
        计算期权的风险价值 (VaR)
        
        Args:
            option: 期权合约
            underlying_price: 当前标的价格
            days: 持有天数
            confidence: 置信水平 (如0.95表示95%)
            
        Returns:
            VaR值 (美元)
        """
        greeks = option.greeks or {}
        delta = greeks.get("delta", 0)
        gamma = greeks.get("gamma", 0)
        theta = greeks.get("theta", 0)
        vega = greeks.get("vega", 0)
        iv = greeks.get("mid_iv", 0.25)
        
        # 假设标的价格变化的日波动率
        daily_vol = iv / math.sqrt(252)
        
        # 计算置信水平对应的z值
        z_score = stats.norm.ppf(1 - confidence)
        
        # 价格变化
        price_change = underlying_price * daily_vol * math.sqrt(days) * z_score
        
        # 期权价值变化 (使用泰勒展开近似)
        option_value_change = (
            delta * price_change +
            0.5 * gamma * price_change**2 +
            theta * days +
            vega * 0.01  # 假设IV变化1%
        )
        
        # VaR为负的价值变化
        var = max(0, -option_value_change * 100)  # 转换为每份合约的美元金额
        
        return var
    
    def _get_default_scenarios(self, underlying_price: float) -> List[Dict[str, Any]]:
        """获取默认市场情景"""
        return [
            {
                "name": "现价不变",
                "underlying_price": underlying_price,
                "days_forward": 0,
                "probability": 0.20
            },
            {
                "name": "上涨5%",
                "underlying_price": underlying_price * 1.05,
                "days_forward": 10,
                "probability": 0.15
            },
            {
                "name": "上涨10%",
                "underlying_price": underlying_price * 1.10,
                "days_forward": 20,
                "probability": 0.10
            },
            {
                "name": "下跌5%",
                "underlying_price": underlying_price * 0.95,
                "days_forward": 10,
                "probability": 0.20
            },
            {
                "name": "下跌10%",
                "underlying_price": underlying_price * 0.90,
                "days_forward": 20,
                "probability": 0.15
            },
            {
                "name": "下跌15%",
                "underlying_price": underlying_price * 0.85,
                "days_forward": 30,
                "probability": 0.10
            },
            {
                "name": "到期时执行价",
                "underlying_price": None,  # 将在计算时设置为执行价
                "days_forward": None,  # 将设置为到期天数
                "probability": 0.10
            }
        ]
    
    def _calculate_option_value_at_price(
        self,
        option: OptionContract,
        new_price: float,
        days_forward: int
    ) -> float:
        """
        计算期权在新价格和时间下的理论价值
        这里使用简化的Black-Scholes模型
        """
        if new_price is None:
            new_price = option.strike
        
        greeks = option.greeks or {}
        iv = greeks.get("mid_iv", 0.25)
        
        # 计算剩余时间
        exp_date = datetime.strptime(option.expiration_date, "%Y-%m-%d").date()
        today = datetime.now().date()
        days_to_expiry = max((exp_date - today).days - days_forward, 0)
        
        if days_to_expiry <= 0:
            # 到期时的内在价值
            if option.option_type == "put":
                return max(option.strike - new_price, 0)
            else:
                return max(new_price - option.strike, 0)
        
        time_to_expiry = days_to_expiry / 365.0
        
        # 简化的Black-Scholes计算
        try:
            d1 = (math.log(new_price / option.strike) + 
                  (self.risk_free_rate + 0.5 * iv**2) * time_to_expiry) / (iv * math.sqrt(time_to_expiry))
            d2 = d1 - iv * math.sqrt(time_to_expiry)
            
            if option.option_type == "put":
                option_value = (option.strike * math.exp(-self.risk_free_rate * time_to_expiry) * 
                              stats.norm.cdf(-d2) - new_price * stats.norm.cdf(-d1))
            else:
                option_value = (new_price * stats.norm.cdf(d1) - 
                              option.strike * math.exp(-self.risk_free_rate * time_to_expiry) * 
                              stats.norm.cdf(d2))
            
            return max(option_value, 0)
            
        except (ValueError, ZeroDivisionError):
            # 如果计算失败，返回内在价值
            if option.option_type == "put":
                return max(option.strike - new_price, 0)
            else:
                return max(new_price - option.strike, 0)
    
    def _calculate_probability_at_time(
        self,
        current_price: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        option_type: str
    ) -> float:
        """计算指定时间点的价内概率"""
        
        if time_to_expiry <= 0:
            if option_type == "put":
                return 100 if current_price < strike else 0
            else:
                return 100 if current_price > strike else 0
        
        try:
            d2 = (math.log(current_price / strike) + 
                  (self.risk_free_rate - 0.5 * volatility**2) * time_to_expiry) / (volatility * math.sqrt(time_to_expiry))
            
            if option_type == "put":
                prob = stats.norm.cdf(-d2) * 100
            else:
                prob = stats.norm.cdf(d2) * 100
                
            return prob
            
        except (ValueError, ZeroDivisionError):
            return 50.0  # 默认50%概率


class PortfolioRiskManager:
    """组合风险管理器"""
    
    def __init__(self, max_single_position: float = 0.1, max_sector_exposure: float = 0.3):
        self.max_single_position = max_single_position  # 单一仓位最大比例
        self.max_sector_exposure = max_sector_exposure    # 单一行业最大敞口
        self.risk_calculator = OptionRiskCalculator()
    
    def assess_portfolio_risk(
        self,
        positions: List[Dict[str, Any]],
        total_capital: float
    ) -> Dict[str, Any]:
        """
        评估组合整体风险
        
        Args:
            positions: 仓位列表
            total_capital: 总资本
            
        Returns:
            组合风险评估报告
        """
        total_exposure = sum(pos.get("required_capital", 0) for pos in positions)
        
        # 计算各项风险指标
        concentration_risk = self._calculate_concentration_risk(positions, total_capital)
        liquidity_risk = self._calculate_portfolio_liquidity_risk(positions)
        correlation_risk = self._calculate_correlation_risk(positions)
        
        # 总体风险评分
        overall_risk_score = (concentration_risk + liquidity_risk + correlation_risk) / 3
        
        return {
            "total_positions": len(positions),
            "total_exposure": total_exposure,
            "capital_utilization": (total_exposure / total_capital) * 100,
            "concentration_risk": concentration_risk,
            "liquidity_risk": liquidity_risk,
            "correlation_risk": correlation_risk,
            "overall_risk_score": overall_risk_score,
            "risk_level": self._get_risk_level(overall_risk_score),
            "recommendations": self._generate_risk_recommendations(
                concentration_risk, liquidity_risk, correlation_risk
            )
        }
    
    def _calculate_concentration_risk(
        self,
        positions: List[Dict[str, Any]],
        total_capital: float
    ) -> float:
        """计算集中度风险"""
        if not positions:
            return 0
        
        position_sizes = [pos.get("required_capital", 0) / total_capital for pos in positions]
        
        # 检查单一仓位过大
        max_position = max(position_sizes) if position_sizes else 0
        concentration_penalty = max(0, (max_position - self.max_single_position) * 500)
        
        # 使用HHI指数评估集中度
        hhi = sum(size**2 for size in position_sizes)
        hhi_risk = min(hhi * 100, 100)
        
        return min(concentration_penalty + hhi_risk, 100)
    
    def _calculate_portfolio_liquidity_risk(self, positions: List[Dict[str, Any]]) -> float:
        """计算组合流动性风险"""
        if not positions:
            return 0
        
        liquidity_scores = [pos.get("liquidity_score", 50) for pos in positions]
        avg_liquidity = sum(liquidity_scores) / len(liquidity_scores)
        
        # 流动性风险与流动性评分成反比
        return max(0, 100 - avg_liquidity)
    
    def _calculate_correlation_risk(self, positions: List[Dict[str, Any]]) -> float:
        """计算相关性风险（简化版）"""
        if len(positions) <= 1:
            return 0
        
        # 按行业分组
        sectors = {}
        for pos in positions:
            sector = pos.get("sector", "Unknown")
            sectors[sector] = sectors.get(sector, 0) + pos.get("required_capital", 0)
        
        # 检查行业集中度
        total_capital = sum(sectors.values())
        if total_capital <= 0:
            return 0
        
        max_sector_exposure = max(sectors.values()) / total_capital
        correlation_risk = max(0, (max_sector_exposure - self.max_sector_exposure) * 200)
        
        return min(correlation_risk, 100)
    
    def _get_risk_level(self, risk_score: float) -> str:
        """根据风险评分确定风险等级"""
        if risk_score < 30:
            return "低风险"
        elif risk_score < 60:
            return "中等风险"
        elif risk_score < 80:
            return "高风险"
        else:
            return "极高风险"
    
    def _generate_risk_recommendations(
        self,
        concentration_risk: float,
        liquidity_risk: float,
        correlation_risk: float
    ) -> List[str]:
        """生成风险管理建议"""
        recommendations = []
        
        if concentration_risk > 50:
            recommendations.append("建议分散投资，减少单一仓位规模")
        
        if liquidity_risk > 50:
            recommendations.append("建议增加高流动性期权的比重")
        
        if correlation_risk > 50:
            recommendations.append("建议增加不同行业的配置，降低行业集中度")
        
        if not recommendations:
            recommendations.append("当前风险水平可接受，保持现有配置")
        
        return recommendations


# 便捷函数

def calculate_option_risk_metrics(
    option: OptionContract,
    underlying_price: float,
    portfolio_size: int = 1
) -> Dict[str, Any]:
    """计算期权风险指标的便捷函数"""
    calculator = OptionRiskCalculator()
    metrics = calculator.calculate_option_risk_metrics(option, underlying_price, portfolio_size)
    
    # 转换为字典格式
    return {
        "delta": metrics.delta,
        "gamma": metrics.gamma,
        "theta": metrics.theta,
        "vega": metrics.vega,
        "rho": metrics.rho,
        "implied_volatility": metrics.implied_volatility,
        "time_decay_per_day": metrics.time_decay_per_day,
        "assignment_probability": metrics.assignment_probability,
        "liquidity_risk": metrics.liquidity_risk,
        "concentration_risk": metrics.concentration_risk,
        "var_1_day": metrics.var_1_day,
        "var_5_day": metrics.var_5_day
    }


def calculate_pnl_scenarios(
    option: OptionContract,
    underlying_price: float,
    custom_scenarios: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """计算P&L情景的便捷函数"""
    calculator = OptionRiskCalculator()
    scenarios = calculator.calculate_pnl_scenarios(option, underlying_price, custom_scenarios)
    
    # 转换为字典格式
    return [
        {
            "scenario_name": s.scenario_name,
            "underlying_price": s.underlying_price,
            "days_forward": s.days_forward,
            "option_value": s.option_value,
            "pnl": s.pnl,
            "pnl_percentage": s.pnl_percentage,
            "probability": s.probability
        }
        for s in scenarios
    ]


def assess_assignment_probability(
    option: OptionContract,
    underlying_price: float,
    volatility: Optional[float] = None
) -> Dict[str, float]:
    """评估分配概率的便捷函数"""
    calculator = OptionRiskCalculator()
    return calculator.assess_assignment_probability(option, underlying_price, volatility)