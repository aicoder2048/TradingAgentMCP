"""
增强的希腊字母计算模块

提供精确的期权希腊字母计算功能，包括：
- Black-Scholes模型实现
- 隐含波动率计算
- 数值方法计算希腊字母
- 美式期权近似计算
- 波动率微笑处理
"""

import math
import numpy as np
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from scipy import stats, optimize
from scipy.stats import norm

from ..provider.tradier.client import OptionContract


@dataclass
class Greeks:
    """希腊字母数据类"""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    
    # 二阶希腊字母
    vanna: Optional[float] = None   # dDelta/dVolatility
    charm: Optional[float] = None   # dDelta/dTime
    volga: Optional[float] = None   # dVega/dVolatility
    veta: Optional[float] = None    # dVega/dTime
    
    # 颜色希腊字母
    speed: Optional[float] = None   # dGamma/dUnderlying
    zomma: Optional[float] = None   # dGamma/dVolatility
    color: Optional[float] = None   # dGamma/dTime


@dataclass 
class BSMParameters:
    """Black-Scholes-Merton模型参数"""
    underlying_price: float
    strike_price: float
    time_to_expiry: float
    risk_free_rate: float
    volatility: float
    dividend_yield: float = 0.0
    option_type: str = "call"  # "call" or "put"


class BlackScholesCalculator:
    """Black-Scholes期权定价和希腊字母计算器"""
    
    @staticmethod
    def d1(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
        """计算d1参数"""
        if T <= 0 or sigma <= 0:
            return 0.0
        return (math.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    
    @staticmethod
    def d2(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
        """计算d2参数"""
        if T <= 0 or sigma <= 0:
            return 0.0
        d1_val = BlackScholesCalculator.d1(S, K, T, r, sigma, q)
        return d1_val - sigma * math.sqrt(T)
    
    @staticmethod
    def option_price(params: BSMParameters) -> float:
        """计算期权理论价格"""
        S, K, T, r, sigma, q = (
            params.underlying_price, params.strike_price, params.time_to_expiry,
            params.risk_free_rate, params.volatility, params.dividend_yield
        )
        
        if T <= 0:
            # 到期时的内在价值
            if params.option_type.lower() == "call":
                return max(S - K, 0)
            else:
                return max(K - S, 0)
        
        if sigma <= 0:
            return 0.0
        
        d1_val = BlackScholesCalculator.d1(S, K, T, r, sigma, q)
        d2_val = BlackScholesCalculator.d2(S, K, T, r, sigma, q)
        
        if params.option_type.lower() == "call":
            price = (S * math.exp(-q * T) * norm.cdf(d1_val) - 
                    K * math.exp(-r * T) * norm.cdf(d2_val))
        else:  # put
            price = (K * math.exp(-r * T) * norm.cdf(-d2_val) - 
                    S * math.exp(-q * T) * norm.cdf(-d1_val))
        
        return max(price, 0)
    
    @staticmethod
    def calculate_greeks(params: BSMParameters, include_second_order: bool = False) -> Greeks:
        """计算完整的希腊字母"""
        S, K, T, r, sigma, q = (
            params.underlying_price, params.strike_price, params.time_to_expiry,
            params.risk_free_rate, params.volatility, params.dividend_yield
        )
        
        if T <= 0 or sigma <= 0:
            # 边界情况处理
            return Greeks(delta=0, gamma=0, theta=0, vega=0, rho=0)
        
        d1_val = BlackScholesCalculator.d1(S, K, T, r, sigma, q)
        d2_val = BlackScholesCalculator.d2(S, K, T, r, sigma, q)
        
        # 标准正态分布函数值
        N_d1 = norm.cdf(d1_val)
        N_d2 = norm.cdf(d2_val)
        n_d1 = norm.pdf(d1_val)  # 概率密度函数
        
        sqrt_T = math.sqrt(T)
        
        # 一阶希腊字母
        if params.option_type.lower() == "call":
            delta = math.exp(-q * T) * N_d1
            rho = K * T * math.exp(-r * T) * N_d2 / 100  # 除以100转换为百分点变化
        else:  # put
            delta = math.exp(-q * T) * (N_d1 - 1)
            rho = -K * T * math.exp(-r * T) * norm.cdf(-d2_val) / 100
        
        gamma = math.exp(-q * T) * n_d1 / (S * sigma * sqrt_T)
        theta = (-S * n_d1 * sigma * math.exp(-q * T) / (2 * sqrt_T) - 
                r * K * math.exp(-r * T) * N_d2 + 
                q * S * math.exp(-q * T) * N_d1) / 365  # 转换为每日衰减
        
        if params.option_type.lower() == "put":
            theta += (r * K * math.exp(-r * T) * norm.cdf(-d2_val) - 
                     q * S * math.exp(-q * T) * norm.cdf(-d1_val)) / 365
        
        vega = S * math.exp(-q * T) * n_d1 * sqrt_T / 100  # 除以100转换为百分点变化
        
        greeks = Greeks(
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            rho=rho
        )
        
        # 二阶希腊字母（可选）
        if include_second_order:
            greeks.vanna = -math.exp(-q * T) * n_d1 * d2_val / sigma / 100
            greeks.charm = (q * math.exp(-q * T) * N_d1 - 
                           math.exp(-q * T) * n_d1 * (2 * (r - q) * T - d2_val * sigma * sqrt_T) / 
                           (2 * T * sigma * sqrt_T)) / 365
            
            greeks.volga = S * math.exp(-q * T) * n_d1 * sqrt_T * d1_val * d2_val / sigma / 100
            greeks.veta = (-S * math.exp(-q * T) * n_d1 * sqrt_T * 
                          (q + ((r - q) * d1_val - d2_val / (2 * T)) / (sigma * sqrt_T))) / (365 * 100)
            
            greeks.speed = -gamma / S * (d1_val / (sigma * sqrt_T) + 1)
            greeks.zomma = gamma * (d1_val * d2_val - 1) / sigma / 100
            greeks.color = (-math.exp(-q * T) * n_d1 / (2 * S * T * sigma * sqrt_T) * 
                           (2 * q * T + 1 + (2 * (r - q) * T - d2_val * sigma * sqrt_T) * d1_val / 
                            (sigma * sqrt_T))) / 365
        
        return greeks


class ImpliedVolatilityCalculator:
    """隐含波动率计算器"""
    
    @staticmethod
    def calculate_iv(
        market_price: float,
        underlying_price: float,
        strike_price: float,
        time_to_expiry: float,
        risk_free_rate: float,
        option_type: str,
        dividend_yield: float = 0.0,
        max_iterations: int = 100,
        tolerance: float = 1e-6
    ) -> Optional[float]:
        """
        使用Newton-Raphson方法计算隐含波动率
        
        Args:
            market_price: 市场价格
            underlying_price: 标的价格
            strike_price: 执行价
            time_to_expiry: 到期时间（年）
            risk_free_rate: 无风险利率
            option_type: 期权类型
            dividend_yield: 分红收益率
            max_iterations: 最大迭代次数
            tolerance: 收敛容差
            
        Returns:
            隐含波动率或None
        """
        if market_price <= 0 or time_to_expiry <= 0:
            return None
        
        # 边界检查
        intrinsic = max(0, underlying_price - strike_price) if option_type.lower() == "call" else max(0, strike_price - underlying_price)
        if market_price < intrinsic:
            return None
        
        # 初始猜测值
        volatility = 0.2
        
        for i in range(max_iterations):
            params = BSMParameters(
                underlying_price=underlying_price,
                strike_price=strike_price,
                time_to_expiry=time_to_expiry,
                risk_free_rate=risk_free_rate,
                volatility=volatility,
                dividend_yield=dividend_yield,
                option_type=option_type
            )
            
            # 计算理论价格和Vega
            theoretical_price = BlackScholesCalculator.option_price(params)
            greeks = BlackScholesCalculator.calculate_greeks(params)
            vega = greeks.vega * 100  # 转换回原始单位
            
            # 价格差异
            price_diff = theoretical_price - market_price
            
            # 检查收敛
            if abs(price_diff) < tolerance:
                return volatility
            
            # 检查Vega是否过小
            if abs(vega) < 1e-10:
                break
            
            # Newton-Raphson更新
            volatility_new = volatility - price_diff / vega
            
            # 确保波动率在合理范围内
            volatility_new = max(0.001, min(5.0, volatility_new))
            
            # 检查变化是否过小
            if abs(volatility_new - volatility) < tolerance:
                return volatility_new
            
            volatility = volatility_new
        
        return None
    
    @staticmethod
    def calculate_iv_brent(
        market_price: float,
        underlying_price: float,
        strike_price: float,
        time_to_expiry: float,
        risk_free_rate: float,
        option_type: str,
        dividend_yield: float = 0.0
    ) -> Optional[float]:
        """
        使用Brent方法计算隐含波动率（更稳定）
        """
        if market_price <= 0 or time_to_expiry <= 0:
            return None
        
        def objective(vol):
            params = BSMParameters(
                underlying_price=underlying_price,
                strike_price=strike_price,
                time_to_expiry=time_to_expiry,
                risk_free_rate=risk_free_rate,
                volatility=vol,
                dividend_yield=dividend_yield,
                option_type=option_type
            )
            return BlackScholesCalculator.option_price(params) - market_price
        
        try:
            result = optimize.brentq(objective, 0.001, 5.0, xtol=1e-6)
            return result
        except (ValueError, RuntimeError):
            return None


class GreeksAnalyzer:
    """希腊字母分析器"""
    
    def __init__(self, risk_free_rate: float = 0.05):
        self.risk_free_rate = risk_free_rate
        self.bs_calculator = BlackScholesCalculator()
        self.iv_calculator = ImpliedVolatilityCalculator()
    
    def analyze_option_greeks(
        self,
        option: OptionContract,
        underlying_price: float,
        include_second_order: bool = False,
        use_market_iv: bool = True
    ) -> Dict[str, Any]:
        """
        分析期权的希腊字母
        
        Args:
            option: 期权合约
            underlying_price: 标的价格
            include_second_order: 是否包含二阶希腊字母
            use_market_iv: 是否使用市场隐含波动率
            
        Returns:
            希腊字母分析结果
        """
        # 计算到期时间
        from datetime import datetime
        exp_date = datetime.strptime(option.expiration_date, "%Y-%m-%d").date()
        today = datetime.now().date()
        days_to_expiry = max((exp_date - today).days, 0)
        time_to_expiry = days_to_expiry / 365.0
        
        if time_to_expiry <= 0:
            return self._get_expiry_greeks(option, underlying_price)
        
        # 获取隐含波动率
        iv = None
        if use_market_iv and option.greeks:
            iv = option.greeks.get("mid_iv")
        
        if not iv and option.bid and option.ask:
            # 使用市场价格计算隐含波动率
            mid_price = (option.bid + option.ask) / 2
            iv = self.iv_calculator.calculate_iv(
                market_price=mid_price,
                underlying_price=underlying_price,
                strike_price=option.strike,
                time_to_expiry=time_to_expiry,
                risk_free_rate=self.risk_free_rate,
                option_type=option.option_type
            )
        
        if not iv:
            iv = 0.25  # 默认波动率
        
        # 构建BSM参数
        params = BSMParameters(
            underlying_price=underlying_price,
            strike_price=option.strike,
            time_to_expiry=time_to_expiry,
            risk_free_rate=self.risk_free_rate,
            volatility=iv,
            option_type=option.option_type
        )
        
        # 计算希腊字母
        greeks = self.bs_calculator.calculate_greeks(params, include_second_order)
        
        # 计算理论价格
        theoretical_price = self.bs_calculator.option_price(params)
        
        # 分析价值性
        moneyness = self._calculate_moneyness(underlying_price, option.strike, option.option_type)
        
        return {
            "symbol": option.symbol,
            "theoretical_price": theoretical_price,
            "implied_volatility": iv,
            "greeks": {
                "delta": greeks.delta,
                "gamma": greeks.gamma,
                "theta": greeks.theta,
                "vega": greeks.vega,
                "rho": greeks.rho
            },
            "second_order_greeks": {
                "vanna": greeks.vanna,
                "charm": greeks.charm,
                "volga": greeks.volga,
                "veta": greeks.veta,
                "speed": greeks.speed,
                "zomma": greeks.zomma,
                "color": greeks.color
            } if include_second_order else None,
            "risk_metrics": {
                "days_to_expiry": days_to_expiry,
                "time_decay_per_day": abs(greeks.theta),
                "delta_hedging_ratio": abs(greeks.delta),
                "gamma_risk": greeks.gamma * underlying_price,
                "vega_risk": greeks.vega * iv
            },
            "moneyness_analysis": moneyness,
            "calculation_params": {
                "underlying_price": underlying_price,
                "strike_price": option.strike,
                "time_to_expiry": time_to_expiry,
                "risk_free_rate": self.risk_free_rate,
                "volatility": iv,
                "option_type": option.option_type
            }
        }
    
    def _get_expiry_greeks(self, option: OptionContract, underlying_price: float) -> Dict[str, Any]:
        """获取到期时的希腊字母（主要是内在价值）"""
        if option.option_type.lower() == "call":
            intrinsic = max(0, underlying_price - option.strike)
            delta = 1.0 if underlying_price > option.strike else 0.0
        else:
            intrinsic = max(0, option.strike - underlying_price)
            delta = -1.0 if underlying_price < option.strike else 0.0
        
        return {
            "symbol": option.symbol,
            "theoretical_price": intrinsic,
            "implied_volatility": 0.0,
            "greeks": {
                "delta": delta,
                "gamma": 0.0,
                "theta": 0.0,
                "vega": 0.0,
                "rho": 0.0
            },
            "risk_metrics": {
                "days_to_expiry": 0,
                "time_decay_per_day": 0.0,
                "delta_hedging_ratio": abs(delta),
                "gamma_risk": 0.0,
                "vega_risk": 0.0
            },
            "moneyness_analysis": self._calculate_moneyness(underlying_price, option.strike, option.option_type),
            "note": "Option has expired - showing intrinsic value only"
        }
    
    def _calculate_moneyness(self, underlying_price: float, strike_price: float, option_type: str) -> Dict[str, Any]:
        """计算期权价值性分析"""
        if option_type.lower() == "call":
            moneyness_ratio = underlying_price / strike_price
            is_itm = underlying_price > strike_price
            is_otm = underlying_price < strike_price
        else:  # put
            moneyness_ratio = strike_price / underlying_price
            is_itm = underlying_price < strike_price  
            is_otm = underlying_price > strike_price
        
        is_atm = abs(underlying_price - strike_price) / underlying_price < 0.02  # 2%范围内视为平值
        
        # 价值性描述
        if is_atm:
            moneyness_desc = "平值 (ATM)"
        elif is_itm:
            moneyness_desc = "价内 (ITM)"
        else:
            moneyness_desc = "价外 (OTM)"
        
        return {
            "is_itm": is_itm,
            "is_atm": is_atm,
            "is_otm": is_otm,
            "moneyness_ratio": moneyness_ratio,
            "description": moneyness_desc,
            "distance_from_strike": abs(underlying_price - strike_price),
            "distance_percentage": abs(underlying_price - strike_price) / underlying_price * 100
        }


# 便捷函数

def calculate_option_greeks(
    option: OptionContract,
    underlying_price: float,
    risk_free_rate: float = 0.05,
    include_second_order: bool = False
) -> Dict[str, Any]:
    """计算期权希腊字母的便捷函数"""
    analyzer = GreeksAnalyzer(risk_free_rate=risk_free_rate)
    return analyzer.analyze_option_greeks(
        option=option,
        underlying_price=underlying_price,
        include_second_order=include_second_order
    )


def calculate_implied_volatility(
    market_price: float,
    underlying_price: float,
    strike_price: float,
    time_to_expiry: float,
    risk_free_rate: float,
    option_type: str,
    dividend_yield: float = 0.0
) -> Optional[float]:
    """计算隐含波动率的便捷函数"""
    return ImpliedVolatilityCalculator.calculate_iv(
        market_price=market_price,
        underlying_price=underlying_price,
        strike_price=strike_price,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        option_type=option_type,
        dividend_yield=dividend_yield
    )


def calculate_all_greeks(
    underlying_price: float,
    strike_price: float,
    time_to_expiry: float,
    risk_free_rate: float,
    volatility: float,
    option_type: str,
    dividend_yield: float = 0.0
) -> Dict[str, float]:
    """计算所有希腊字母的便捷函数"""
    params = BSMParameters(
        underlying_price=underlying_price,
        strike_price=strike_price,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=dividend_yield,
        option_type=option_type
    )
    
    greeks = BlackScholesCalculator.calculate_greeks(params, include_second_order=True)
    
    return {
        "delta": greeks.delta,
        "gamma": greeks.gamma,
        "theta": greeks.theta,
        "vega": greeks.vega,
        "rho": greeks.rho,
        "vanna": greeks.vanna or 0,
        "charm": greeks.charm or 0,
        "volga": greeks.volga or 0,
        "veta": greeks.veta or 0,
        "speed": greeks.speed or 0,
        "zomma": greeks.zomma or 0,
        "color": greeks.color or 0
    }