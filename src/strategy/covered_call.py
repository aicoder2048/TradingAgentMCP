"""
Covered Call Strategy Analysis Module

Provides comprehensive analysis for covered call options strategies,
including income generation and position exit strategies.
"""

import os
import csv
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

from ..provider.tradier.client import TradierClient, OptionContract
from ..option.option_expiration_selector import ExpirationSelector


@dataclass
class CoveredCallRecommendation:
    """Covered call strategy recommendation data structure"""
    profile: str  # conservative, balanced, aggressive
    option_details: Dict[str, Any]
    position_info: Dict[str, Any]
    pnl_analysis: Dict[str, Any]
    risk_metrics: Dict[str, Any]
    recommendation_reasoning: str


class CoveredCallAnalyzer:
    """
    Covered Call策略分析器
    
    为持有股票的投资者提供专业的covered call期权策略分析，
    支持收入导向和减仓两种策略类型。
    """
    
    def __init__(
        self,
        symbol: str,
        purpose_type: str,  # "income" or "exit"
        duration: str,      # "1w", "2w", "1m", "3m", "6m", "1y"
        shares_owned: int,
        avg_cost: Optional[float] = None,
        tradier_client: Optional[TradierClient] = None
    ):
        self.symbol = symbol.upper()
        self.purpose_type = purpose_type.lower()
        self.duration = duration.lower()
        self.shares_owned = shares_owned
        self.avg_cost = avg_cost
        self.client = tradier_client or TradierClient()
        
        # Delta范围基于策略目的 (正值，因为是call期权)
        self.delta_ranges = {
            "income": {"min": 0.10, "max": 0.30},    # 收入策略：低分配概率，保留更多上涨空间
            "exit": {"min": 0.30, "max": 0.70}       # 减仓策略：接受更高分配概率，目标价位减仓
        }
        
        # 最小流动性要求
        self.min_open_interest = 50
        self.min_volume = 10
        self.max_bid_ask_spread_pct = 0.15  # 15%
        
        # 可写合约数量
        self.contracts_available = shares_owned // 100
        
        if self.contracts_available == 0:
            raise ValueError(f"持股数量不足，需要至少100股才能实施covered call策略。当前持股: {shares_owned}")
    
    async def find_optimal_strikes(
        self,
        expiration: str,
        underlying_price: float,
        min_premium: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        基于Delta要求找到最优call执行价格
        
        Args:
            expiration: 到期日 (YYYY-MM-DD)
            underlying_price: 标的股票当前价格
            min_premium: 最低权利金要求 (可选)
            
        Returns:
            排序后的call期权机会列表
        """
        try:
            # 获取call期权链数据
            delta_range = self.delta_ranges[self.purpose_type]
            call_options = self.client.get_call_options_by_delta_range(
                symbol=self.symbol,
                expiration=expiration,
                delta_min=delta_range["min"],
                delta_max=delta_range["max"]
            )
            
            if not call_options:
                return []
            
            analyzed_options = []
            
            for option in call_options:
                # 基本验证
                if not self._is_valid_option(option):
                    continue
                    
                # 确保是价外期权（strike > current price）
                if option.strike <= underlying_price:
                    continue
                
                # 最低权利金检查
                if min_premium:
                    mid_price = (option.bid + option.ask) / 2
                    if mid_price < min_premium:
                        continue
                
                # 计算策略指标
                metrics = await self.calculate_strategy_metrics(option, underlying_price)
                if metrics:
                    analyzed_options.append(metrics)
            
            # 按综合评分排序
            return sorted(
                analyzed_options,
                key=lambda x: x["composite_score"],
                reverse=True
            )
            
        except Exception as e:
            print(f"Error finding optimal strikes: {e}")
            return []
    
    async def calculate_strategy_metrics(
        self,
        option: OptionContract,
        underlying_price: float
    ) -> Optional[Dict[str, Any]]:
        """
        计算covered call仓位的综合指标
        
        Args:
            option: call期权合约数据
            underlying_price: 标的价格
            
        Returns:
            包含所有策略指标的字典
        """
        try:
            # 基础数据
            strike = option.strike
            bid = option.bid or 0
            ask = option.ask or 0
            
            if bid <= 0 or ask <= 0:
                return None
                
            mid_price = (bid + ask) / 2
            bid_ask_spread = ask - bid
            
            # 希腊字母
            greeks = option.greeks or {}
            delta = greeks.get("delta", 0)
            theta = greeks.get("theta", 0)
            implied_vol = greeks.get("mid_iv", 0.25)  # 默认25%
            
            # 计算到期天数
            exp_date = datetime.strptime(option.expiration_date, "%Y-%m-%d").date()
            today = datetime.now().date()
            days_to_expiry = max((exp_date - today).days, 1)
            time_to_expiry = days_to_expiry / 365.0
            
            # Covered Call特有指标
            upside_capture = ((strike - underlying_price) / underlying_price) * 100
            premium_income = mid_price * self.contracts_available * 100
            shares_covered = self.contracts_available * 100
            
            # P&L分析 - 基于当前股价的机会成本
            max_profit_if_called = (
                (strike - underlying_price) * shares_covered +  # 股票升值收益
                premium_income                                   # 权利金收入
            )
            
            # 如果有成本基础，额外计算基于历史成本的收益（用于参考）
            if self.avg_cost is not None:
                historical_gain = (strike - self.avg_cost) * shares_covered + premium_income
                historical_return = (historical_gain / (self.avg_cost * shares_covered)) * 100
                historical_annualized = historical_return * (365 / days_to_expiry)
            else:
                historical_gain = None
                historical_return = None  
                historical_annualized = None
                
            # 策略收益率基于当前市价
            current_market_value = underlying_price * shares_covered
            total_return_if_called = (max_profit_if_called / current_market_value) * 100
            annualized_return = total_return_if_called * (365 / days_to_expiry)
            
            # 保本点计算 (股价下跌多少权利金能覆盖)
            downside_protection = (mid_price / underlying_price) * 100
            breakeven_price = underlying_price - mid_price
            
            # 机会成本分析 (如果股价超过strike的损失)
            opportunity_cost_per_share = max(0, underlying_price * 0.05 - (strike - underlying_price))  # 假设5%上涨
            total_opportunity_cost = opportunity_cost_per_share * shares_covered
            
            # 使用精确的Black-Scholes被行权概率计算
            from src.option.assignment_probability import OptionAssignmentCalculator
            
            assignment_calculator = OptionAssignmentCalculator()
            
            # 计算精确被行权概率（call期权）
            assignment_result = assignment_calculator.calculate_assignment_probability(
                underlying_price=underlying_price,
                strike_price=strike,
                time_to_expiry_days=days_to_expiry,
                implied_volatility=implied_vol,
                option_type="call"
            )
            
            if assignment_result["status"] == "success":
                # 使用精确计算结果
                assignment_probability = assignment_result["assignment_probability"] * 100  # 转换为百分比
                assignment_risk_level = assignment_result["assignment_risk_level"]
                
                # 保留Delta近似值用于比较
                delta_approximation = delta * 100
                
                # 计算精度提升
                precision_improvement = {
                    "exact_probability": assignment_probability,
                    "delta_approximation": delta_approximation,
                    "improvement_available": True,
                    "calculation_method": "Black-Scholes精确计算"
                }
            else:
                # 回退到Delta近似（向后兼容）
                assignment_probability = delta * 100
                assignment_risk_level = "中等" if 20 <= assignment_probability <= 40 else ("低" if assignment_probability < 20 else "高")
                
                precision_improvement = {
                    "exact_probability": None,
                    "delta_approximation": assignment_probability,
                    "improvement_available": False,
                    "calculation_method": "Delta近似（回退）",
                    "error_reason": assignment_result.get("error_message", "计算失败")
                }
            
            # 其他风险指标
            liquidity_score = self._calculate_liquidity_score(option)
            risk_score = self._calculate_risk_score(option, underlying_price)
            
            # 综合评分
            composite_score = self._calculate_composite_score(
                annualized_return, liquidity_score, assignment_probability,
                upside_capture, self.purpose_type
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
                "premium_income": premium_income,
                "shares_covered": shares_covered,
                "contracts_to_write": self.contracts_available,
                "max_profit_if_called": max_profit_if_called,
                "total_return_if_called": total_return_if_called,
                "annualized_return": annualized_return,
                "downside_protection": downside_protection,
                "breakeven_price": breakeven_price,
                "opportunity_cost": total_opportunity_cost,
                
                # 历史成本相关计算（如果有的话）
                "historical_gain": historical_gain,
                "historical_return": historical_return,
                "historical_annualized": historical_annualized,
                
                # 风险指标（增强版）
                "assignment_probability": assignment_probability,
                "assignment_risk_level": assignment_risk_level,
                "liquidity_score": liquidity_score,
                "risk_score": risk_score,
                "composite_score": composite_score,
                
                # 精度提升信息（新增）
                "precision_improvement": precision_improvement,
                
                # 元数据
                "calculation_timestamp": datetime.now().isoformat(),
                "enhanced_calculation": True  # 标识使用了增强计算
            }
            
        except Exception as e:
            print(f"Error calculating strategy metrics: {e}")
            return None
    
    def _is_valid_option(self, option: OptionContract) -> bool:
        """验证call期权是否满足基本要求"""
        return (
            option.strike is not None and
            option.bid is not None and
            option.ask is not None and
            option.bid > 0 and
            option.ask > 0 and
            (option.open_interest or 0) >= self.min_open_interest and
            (option.volume or 0) >= self.min_volume and
            (option.ask - option.bid) / ((option.ask + option.bid) / 2) <= self.max_bid_ask_spread_pct
        )
    
    def _calculate_liquidity_score(self, option: OptionContract) -> float:
        """计算流动性评分 (0-100)"""
        oi = option.open_interest or 0
        volume = option.volume or 0
        bid = option.bid or 0
        ask = option.ask or 0
        
        if bid <= 0 or ask <= 0:
            return 0
            
        mid_price = (bid + ask) / 2
        spread_pct = (ask - bid) / mid_price
        
        # 基于开放利益、成交量和价差的评分
        oi_score = min(oi / 1000, 1) * 40          # 最高40分
        volume_score = min(volume / 100, 1) * 30   # 最高30分  
        spread_score = max(0, (0.1 - spread_pct) / 0.1) * 30  # 最高30分
        
        return oi_score + volume_score + spread_score
    
    def _calculate_risk_score(self, option: OptionContract, underlying_price: float) -> float:
        """计算风险评分 (0-100，100为最高风险)"""
        delta = option.greeks.get("delta", 0) if option.greeks else 0
        strike = option.strike
        
        # 价外程度 (越价外风险越低)
        moneyness = (strike - underlying_price) / underlying_price
        moneyness_risk = max(0, 50 - (moneyness * 100))  # 价外程度转换为风险分数
        
        # Delta风险 (delta越高，分配概率越高)
        delta_risk = delta * 50
        
        return min(moneyness_risk + delta_risk, 100)
    
    def _calculate_composite_score(
        self,
        annualized_return: float,
        liquidity_score: float,
        assignment_prob: float,
        upside_capture: float,
        purpose_type: str
    ) -> float:
        """计算综合评分"""
        return_score = annualized_return
        
        if purpose_type == "income":
            # 收入策略：重视年化收益和低分配概率，保留上涨空间
            return (
                return_score * 0.4 +
                liquidity_score * 0.25 +
                max(0, 50 - assignment_prob) * 0.25 +  # 低分配概率加分
                min(upside_capture, 20) * 0.1          # 适当上涨空间加分
            )
        else:  # exit
            # 减仓策略：可接受更高分配概率，重视总收益
            return (
                return_score * 0.5 +
                liquidity_score * 0.3 +
                min(assignment_prob, 70) * 0.1 +       # 合理分配概率略加分
                upside_capture * 0.1                   # 到strike的收益
            )


class CoveredCallRecommendationEngine:
    """Covered Call策略推荐引擎"""
    
    def generate_three_alternatives(
        self,
        analyzed_options: List[Dict[str, Any]],
        underlying_price: float,
        purpose_type: str,
        shares_owned: int
    ) -> Dict[str, Dict[str, Any]]:
        """
        生成保守、平衡、激进三种策略建议
        
        Args:
            analyzed_options: 已分析的期权列表
            underlying_price: 当前股价
            purpose_type: 策略类型
            shares_owned: 持股数量
            
        Returns:
            三种风险级别的策略建议
        """
        if not analyzed_options:
            return {}
            
        recommendations = {}
        
        # 保守策略：选择delta最低的期权 (分配概率最低)
        conservative = self._select_conservative_option(analyzed_options, purpose_type)
        
        # 平衡策略：选择综合评分最高的期权
        balanced = self._select_balanced_option(analyzed_options, purpose_type)
        
        # 激进策略：选择年化收益最高的期权 (通常delta较高)
        aggressive = self._select_aggressive_option(analyzed_options, purpose_type)
        
        for name, option in [
            ("conservative", conservative),
            ("balanced", balanced), 
            ("aggressive", aggressive)
        ]:
            if option:
                recommendations[name] = self._build_recommendation(
                    option, underlying_price, shares_owned, name, purpose_type
                )
        
        return recommendations
    
    def _select_conservative_option(
        self,
        options: List[Dict[str, Any]],
        purpose_type: str
    ) -> Optional[Dict[str, Any]]:
        """选择保守期权：最低delta"""
        if not options:
            return None
            
        return min(options, key=lambda x: x["delta"])
    
    def _select_balanced_option(
        self,
        options: List[Dict[str, Any]],
        purpose_type: str
    ) -> Optional[Dict[str, Any]]:
        """选择平衡期权：最高综合评分"""
        if not options:
            return None
            
        return max(options, key=lambda x: x["composite_score"])
    
    def _select_aggressive_option(
        self,
        options: List[Dict[str, Any]],
        purpose_type: str
    ) -> Optional[Dict[str, Any]]:
        """选择激进期权：最高年化收益"""
        if not options:
            return None
            
        return max(options, key=lambda x: x["annualized_return"])
    
    def _build_recommendation(
        self,
        option: Dict[str, Any],
        underlying_price: float,
        shares_owned: int,
        profile: str,
        purpose_type: str
    ) -> Dict[str, Any]:
        """构建完整的策略建议"""
        
        contracts = shares_owned // 100
        
        return {
            "profile": profile,
            "option_details": option,
            "position_info": {
                "shares_owned": shares_owned,
                "contracts_to_write": contracts,
                "shares_covered": contracts * 100
            },
            "pnl_analysis": {
                "premium_income": option["premium_income"],
                "max_profit_if_called": option["max_profit_if_called"],
                "total_return_if_called": option["total_return_if_called"],
                "annualized_return": option["annualized_return"],
                "upside_capture": option["upside_capture"],
                "downside_protection": option["downside_protection"],
                "breakeven_price": option["breakeven_price"],
                "opportunity_cost": option["opportunity_cost"]
            },
            "risk_metrics": {
                "assignment_probability": option["assignment_probability"],
                "delta": option["delta"],
                "theta_per_day": option["theta"] * contracts * 100,
                "implied_volatility": option["implied_volatility"],
                "liquidity_score": option["liquidity_score"],
                "upside_at_risk": max(0, (underlying_price * 1.10 - option["strike"]) * option["shares_covered"])
            },
            "recommendation_reasoning": self._generate_reasoning(option, profile, underlying_price, purpose_type)
        }
    
    def _generate_reasoning(
        self,
        option: Dict[str, Any],
        profile: str,
        underlying_price: float,
        purpose_type: str
    ) -> str:
        """生成策略建议的详细说明"""
        
        delta = option["delta"]
        upside_capture = option["upside_capture"]
        premium = option["premium"]
        assignment_prob = option["assignment_probability"]
        
        if purpose_type == "income":
            if profile == "conservative":
                return f"保守收入策略：{delta:.2f} delta提供稳定权利金收入，分配概率仅{assignment_prob:.1f}%，保留{upside_capture:.1f}%的上涨潜力。"
            elif profile == "balanced":
                return f"平衡收入策略：{delta:.2f} delta在收益({premium:.2f})与风险间取得良好平衡，上涨{upside_capture:.1f}%时获得最佳收益。"
            else:  # aggressive
                return f"激进收入策略：{delta:.2f} delta最大化权利金收入，虽分配概率达{assignment_prob:.1f}%，但年化收益丰厚。"
        else:  # exit
            if profile == "conservative":
                return f"保守减仓策略：在{upside_capture:.1f}%上涨时减仓，{premium:.2f}权利金提供额外收益缓冲。"
            elif profile == "balanced":
                return f"平衡减仓策略：目标{upside_capture:.1f}%升值减仓，{assignment_prob:.1f}%分配概率适中，含{premium:.2f}权利金收入。"
            else:  # aggressive
                return f"激进减仓策略：{assignment_prob:.1f}%高分配概率确保减仓执行，最大化权利金收入。"


class CoveredCallOrderFormatter:
    """Covered Call专业订单格式化器"""
    
    def format_order_block(
        self,
        recommendation: Dict[str, Any],
        account_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成JP Morgan风格的专业订单块
        
        Args:
            recommendation: 策略建议数据
            account_info: 账户信息 (可选)
            
        Returns:
            格式化的专业订单块
        """
        option = recommendation["option_details"]
        pnl = recommendation["pnl_analysis"]
        position = recommendation["position_info"]
        risk = recommendation["risk_metrics"]
        
        # 格式化到期日
        exp_date = datetime.strptime(option["expiration"], "%Y-%m-%d").strftime("%b %d, %Y")
        
        order_block = f"""
╔══════════════════════════════════════════════════════════╗
║                   COVERED CALL ORDER                    ║
╠══════════════════════════════════════════════════════════╣
║ Symbol:        {option['symbol']:<43} ║
║ Action:        SELL TO OPEN                              ║
║ Quantity:      {position['contracts_to_write']} CONTRACT(S) ({position['shares_covered']} SHARES COVERED) ║
║ Order Type:    LIMIT                                     ║
║ Strike:        ${option['strike']:<6.2f}                             ║
║ Expiration:    {exp_date:<43} ║
║ Limit Price:   ${option['premium']:<6.2f} (MID)                      ║
╠══════════════════════════════════════════════════════════╣
║                      P&L ANALYSIS                        ║
╠══════════════════════════════════════════════════════════╣
║ Premium Income: ${pnl['premium_income']:<8.2f}                         ║
║ Max Profit:    ${pnl['max_profit_if_called']:<8.2f} (if called away)             ║
║ Upside Capture: {pnl['upside_capture']:<6.2f}% to strike                    ║
║ Downside Prot: {pnl['downside_protection']:<6.2f}% (premium only)            ║
║ Annual Return: {pnl['annualized_return']:<6.2f}%                           ║
║ Breakeven:     ${pnl['breakeven_price']:<8.2f}                           ║
╠══════════════════════════════════════════════════════════╣
║                    RISK METRICS                          ║
╠══════════════════════════════════════════════════════════╣
║ Delta:         {option['delta']:<8.4f}                              ║
║ Assign Prob:   {risk['assignment_probability']:<6.1f}%                            ║
║ Impl Vol:      {risk['implied_volatility']:<6.2%}                        ║
║ Theta/Day:     ${risk['theta_per_day']:<7.2f}                           ║
║ Upside at Risk: ${risk['upside_at_risk']:<7.2f}                          ║
╚══════════════════════════════════════════════════════════╝

EXECUTION NOTES:
• Ensure {position['shares_owned']} shares are held long before selling calls
• Place limit order at mid-price or better  
• Monitor for fills during high liquidity periods (9:30-10:30 AM, 3:00-4:00 PM ET)
• Consider rolling up and out if stock approaches strike with time remaining
• Set GTC (Good Till Cancelled) with daily review
• ASSIGNMENT RISK: Be prepared to sell shares at ${option['strike']:.2f} if assigned

STRATEGY REASONING:
{recommendation['recommendation_reasoning']}
"""
        return order_block


# Supporting Functions
async def export_cc_analysis_to_csv(
    symbol: str,
    recommendations: Dict[str, Dict[str, Any]],
    analyzed_options: List[Dict[str, Any]]
) -> str:
    """导出covered call分析结果到CSV文件"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"cc_{symbol}_{timestamp}.csv"
    filepath = os.path.join("./data", filename)
    
    # 确保data目录存在
    os.makedirs("./data", exist_ok=True)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'profile', 'symbol', 'strike', 'expiration', 'delta', 
            'premium', 'upside_capture', 'total_return_if_called',
            'assignment_probability', 'downside_protection', 'contracts',
            'premium_income', 'recommendation'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # 写入推荐结果
        for profile, rec in recommendations.items():
            writer.writerow({
                'profile': profile,
                'symbol': rec['option_details']['symbol'],
                'strike': rec['option_details']['strike'],
                'expiration': rec['option_details']['expiration'],
                'delta': rec['option_details']['delta'],
                'premium': rec['option_details']['premium'],
                'upside_capture': rec['pnl_analysis']['upside_capture'],
                'total_return_if_called': rec['pnl_analysis']['total_return_if_called'],
                'assignment_probability': rec['risk_metrics']['assignment_probability'],
                'downside_protection': rec['pnl_analysis']['downside_protection'],
                'contracts': rec['position_info']['contracts_to_write'],
                'premium_income': rec['pnl_analysis']['premium_income'],
                'recommendation': rec['recommendation_reasoning']
            })
    
    return filepath


async def get_cc_market_context(
    symbol: str,
    client: TradierClient,
    resistance_levels: Dict[str, float]
) -> Dict[str, Any]:
    """获取covered call决策的市场环境分析"""
    
    try:
        # 获取历史数据进行波动率分析
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        historical = client.get_historical_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval="daily"
        )
        
        if not historical:
            return {"error": "无法获取历史数据"}
        
        # 计算波动率指标
        closes = [float(bar.close) for bar in historical]
        returns = [
            (closes[i] - closes[i-1]) / closes[i-1] 
            for i in range(1, len(closes))
        ]
        
        historical_volatility = np.std(returns) * np.sqrt(252)  # 年化
        
        # 获取当前隐含波动率
        current_iv = await client.get_atm_implied_volatility(symbol)
        
        # 计算动量指标
        current_price = closes[-1]
        sma_20 = sum(closes[-20:]) / 20
        sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else None
        
        momentum_score = "neutral"
        if current_price > sma_20:
            momentum_score = "bullish"
        elif current_price < sma_20:
            momentum_score = "bearish"
            
        if sma_50:
            if current_price > sma_50 and current_price > sma_20:
                momentum_score = "strong_bullish"
            elif current_price < sma_50 and current_price < sma_20:
                momentum_score = "strong_bearish"
        
        return {
            "implied_volatility": current_iv,
            "historical_volatility": historical_volatility,
            "iv_premium": current_iv - historical_volatility,
            "resistance_levels": resistance_levels,
            "momentum_score": momentum_score,
            "technical_levels": {
                "sma_20": sma_20,
                "sma_50": sma_50,
                "support_1": min(closes[-20:]),  # 20日低点
                "resistance_1": max(closes[-20:])  # 20日高点
            },
            "volatility_regime": "high" if current_iv > historical_volatility * 1.2 else "normal"
        }
        
    except Exception as e:
        return {"error": f"获取市场环境数据失败: {str(e)}"}


def generate_cc_execution_notes(
    recommendations: Dict[str, Dict[str, Any]],
    purpose_type: str,
    shares_owned: int
) -> str:
    """生成执行说明"""
    
    notes = []
    contracts_available = shares_owned // 100
    
    notes.append(f"• 持仓验证: {shares_owned}股持有，{contracts_available}份合约可写")
    
    if purpose_type == "income":
        notes.append("• 收入策略 - 目标保留股票并收取权利金")
        notes.append("• 若股价接近执行价，考虑向上向外展期")
        notes.append("• 监控delta；若超过0.50考虑平仓")
        notes.append("• 税务考虑：分配时产生应税事件")
    else:  # exit
        notes.append("• 减仓策略 - 准备在目标价位被分配")
        notes.append("• 此策略限制上涨空间但提供权利金收入缓冲")
        notes.append("• 分配前考虑股票基本面")
        notes.append("• 税务考虑：计算相对成本基础的盈亏")
    
    # 添加波动率相关建议
    balanced = recommendations.get("balanced", {})
    if balanced and balanced.get("risk_metrics", {}).get("implied_volatility", 0) > 0.40:
        notes.append("• 高IV环境 - 有利于卖出权利金")
        notes.append("• 考虑较短期限以捕获IV下降")
    
    # 持仓相关建议
    if contracts_available > 5:
        notes.append("• 大仓位 - 考虑跨多个到期日分批操作")
        notes.append("• 考虑部分写入以保持上涨敞口")
    
    notes.append("• 正常交易时间执行以获得最佳流动性")
    notes.append("• 使用限价单；避免期权市价单")
    notes.append("• 关注可能影响波动率的财报公告")
    
    return "\n".join(notes)