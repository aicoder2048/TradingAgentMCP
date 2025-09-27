"""
现金担保看跌期权策略分析模块

提供现金担保看跌期权策略的完整分析功能，包括：
- 策略分析器：基于目的和时间的期权选择
- 推荐引擎：生成三级风险建议
- 订单格式化：专业级交易台格式
- 数据导出：CSV格式分析报告
"""

import os
import csv
import json
import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_HALF_UP

from ..provider.tradier.client import TradierClient, OptionContract
from ..utils.time import get_market_time_et


@dataclass
class CSPRecommendation:
    """现金担保看跌期权推荐数据类"""
    profile: str
    option_symbol: str
    strike: float
    expiration: str
    delta: float
    premium: float
    bid: float
    ask: float
    open_interest: int
    volume: int
    implied_volatility: float
    theta: float
    max_profit: float
    breakeven_price: float
    required_capital: float
    return_on_capital: float
    annualized_return: float
    assignment_probability: float
    liquidity_score: float
    risk_score: float
    reasoning: str


class CashSecuredPutAnalyzer:
    """现金担保看跌期权策略分析器"""
    
    def __init__(
        self,
        symbol: str,
        purpose_type: str,  # "income" or "discount"
        duration: str,      # "1w", "2w", "1m", "3m", "6m", "1y"
        tradier_client: Optional[TradierClient] = None
    ):
        self.symbol = symbol.upper()
        self.purpose_type = purpose_type.lower()
        self.duration = duration.lower()
        self.client = tradier_client or TradierClient()
        
        # Delta范围基于策略目的
        self.delta_ranges = {
            "income": {"min": -0.30, "max": -0.10},      # 收入策略：低分配概率
            "discount": {"min": -0.70, "max": -0.30}     # 折价策略：接受更高分配风险
        }
        
        # 最小流动性要求
        self.min_open_interest = 50
        self.min_volume = 10
        self.max_bid_ask_spread_pct = 0.15  # 15%
        
    async def find_optimal_strikes(
        self,
        expiration: str,
        underlying_price: float,
        capital_limit: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        基于Delta要求找到最优执行价格
        
        Args:
            expiration: 到期日 (YYYY-MM-DD)
            underlying_price: 标的股票当前价格
            capital_limit: 资金限制 (可选)
            
        Returns:
            排序后的期权机会列表
        """
        try:
            # 获取期权链数据
            option_contracts = self.client.get_option_chain_enhanced(
                symbol=self.symbol,
                expiration=expiration,
                include_greeks=True
            )
            
            if not option_contracts:
                return []
            
            # 过滤看跌期权
            put_options = [
                opt for opt in option_contracts 
                if opt.option_type == "put"
            ]
            
            analyzed_options = []
            delta_range = self.delta_ranges[self.purpose_type]
            
            for option in put_options:
                # 基本验证
                if not self._is_valid_option(option):
                    continue
                    
                # Delta范围检查
                delta = option.greeks.get("delta", 0) if option.greeks else 0
                if not (delta_range["min"] <= delta <= delta_range["max"]):
                    continue
                
                # 资金限制检查
                required_capital = option.strike * 100
                if capital_limit and required_capital > capital_limit:
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
        计算CSP仓位的综合指标
        
        Args:
            option: 期权合约数据
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
            implied_vol = greeks.get("mid_iv", 0)
            
            # 计算到期天数
            exp_date = datetime.strptime(option.expiration_date, "%Y-%m-%d").date()
            today = datetime.now().date()
            days_to_expiry = max((exp_date - today).days, 1)
            time_to_expiry = days_to_expiry / 365.0
            
            # P&L指标
            max_profit = mid_price * 100
            breakeven_price = strike - mid_price
            required_capital = strike * 100
            return_on_capital = (mid_price / strike) * 100
            annualized_return = return_on_capital * (365 / days_to_expiry)
            
            # 风险指标
            assignment_probability = abs(delta) * 100
            liquidity_score = self._calculate_liquidity_score(option)
            risk_score = self._calculate_risk_score(option, underlying_price)
            
            # 综合评分
            composite_score = self._calculate_composite_score(
                annualized_return, liquidity_score, assignment_probability,
                self.purpose_type
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
                "max_profit": max_profit,
                "breakeven_price": breakeven_price,
                "required_capital": required_capital,
                "return_on_capital": return_on_capital,
                "annualized_return": annualized_return,
                "assignment_probability": assignment_probability,
                "liquidity_score": liquidity_score,
                "risk_score": risk_score,
                "composite_score": composite_score
            }
            
        except Exception as e:
            print(f"Error calculating strategy metrics: {e}")
            return None
    
    def _is_valid_option(self, option: OptionContract) -> bool:
        """验证期权是否满足基本要求"""
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
        delta = abs(option.greeks.get("delta", 0)) if option.greeks else 0
        strike = option.strike
        
        # 价内程度
        moneyness = (underlying_price - strike) / underlying_price
        moneyness_risk = min(abs(moneyness) * 100, 50)
        
        # Delta风险
        delta_risk = delta * 50
        
        return moneyness_risk + delta_risk
    
    def _calculate_composite_score(
        self,
        annualized_return: float,
        liquidity_score: float,
        assignment_prob: float,
        purpose_type: str
    ) -> float:
        """计算综合评分"""
        if purpose_type == "income":
            # 收入策略：重视年化收益和低分配概率
            return (
                annualized_return * 0.4 +
                liquidity_score * 0.3 +
                max(0, 50 - assignment_prob) * 0.3
            )
        else:  # discount
            # 折价策略：可接受更高分配概率
            return (
                annualized_return * 0.5 +
                liquidity_score * 0.4 +
                min(assignment_prob, 50) * 0.1
            )


class StrategyRecommendationEngine:
    """策略推荐引擎"""
    
    def generate_three_alternatives(
        self,
        analyzed_options: List[Dict[str, Any]],
        underlying_price: float,
        purpose_type: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        生成三种风险级别的策略建议
        
        Args:
            analyzed_options: 已分析的期权列表
            underlying_price: 当前股价
            purpose_type: 策略目的
            
        Returns:
            包含conservative、balanced、aggressive三种建议的字典
        """
        if not analyzed_options:
            return {}
        
        recommendations = {}
        
        # Conservative: 最低风险，较低收益
        conservative = self._select_conservative_option(analyzed_options, purpose_type)
        if conservative:
            recommendations["conservative"] = self._build_recommendation(
                conservative, underlying_price, "conservative"
            )
        
        # Balanced: 平衡风险收益
        balanced = self._select_balanced_option(analyzed_options, purpose_type)
        if balanced:
            recommendations["balanced"] = self._build_recommendation(
                balanced, underlying_price, "balanced"
            )
        
        # Aggressive: 较高风险，较高收益
        aggressive = self._select_aggressive_option(analyzed_options, purpose_type)
        if aggressive:
            recommendations["aggressive"] = self._build_recommendation(
                aggressive, underlying_price, "aggressive"
            )
        
        return recommendations
    
    def _select_conservative_option(
        self,
        options: List[Dict[str, Any]],
        purpose_type: str
    ) -> Optional[Dict[str, Any]]:
        """选择保守型期权"""
        if purpose_type == "income":
            # 收入策略：选择最低Delta（最低分配概率）
            conservative_options = [
                opt for opt in options
                if opt["assignment_probability"] <= 20
            ]
            return min(conservative_options, key=lambda x: x["assignment_probability"]) if conservative_options else None
        else:
            # 折价策略：选择适中Delta但有良好流动性
            conservative_options = [
                opt for opt in options
                if 30 <= opt["assignment_probability"] <= 40
            ]
            return max(conservative_options, key=lambda x: x["liquidity_score"]) if conservative_options else None
    
    def _select_balanced_option(
        self,
        options: List[Dict[str, Any]],
        purpose_type: str
    ) -> Optional[Dict[str, Any]]:
        """选择平衡型期权"""
        # 选择综合评分最高的期权
        return max(options, key=lambda x: x["composite_score"]) if options else None
    
    def _select_aggressive_option(
        self,
        options: List[Dict[str, Any]],
        purpose_type: str
    ) -> Optional[Dict[str, Any]]:
        """选择激进型期权"""
        if purpose_type == "income":
            # 收入策略：选择年化收益最高的
            return max(options, key=lambda x: x["annualized_return"]) if options else None
        else:
            # 折价策略：选择最高Delta（最高分配概率）
            aggressive_options = [
                opt for opt in options
                if opt["assignment_probability"] >= 50
            ]
            return max(aggressive_options, key=lambda x: x["assignment_probability"]) if aggressive_options else options[0] if options else None
    
    def _build_recommendation(
        self,
        option: Dict[str, Any],
        underlying_price: float,
        profile: str
    ) -> Dict[str, Any]:
        """构建完整的推荐报告"""
        
        strike = option["strike"]
        premium = option["premium"]
        
        return {
            "profile": profile,
            "option_details": option,
            "pnl_analysis": {
                "max_profit": option["max_profit"],
                "max_profit_scenario": "期权到期无价值",
                "breakeven_price": option["breakeven_price"],
                "max_loss_theoretical": (strike - premium) * 100,
                "max_loss_scenario": "股票跌至0美元",
                "profit_at_current_price": premium * 100 if underlying_price > strike else 0,
                "required_capital": option["required_capital"],
                "return_on_capital": option["return_on_capital"],
                "annualized_return": option["annualized_return"]
            },
            "risk_metrics": {
                "assignment_probability": option["assignment_probability"],
                "delta": option["delta"],
                "theta_per_day": abs(option["theta"]) * 100,
                "implied_volatility": option["implied_volatility"],
                "liquidity_score": option["liquidity_score"],
                "risk_score": option["risk_score"]
            },
            "recommendation_reasoning": self._generate_reasoning(option, profile, underlying_price)
        }
    
    def _generate_reasoning(
        self,
        option: Dict[str, Any],
        profile: str,
        underlying_price: float
    ) -> str:
        """生成推荐理由"""
        
        profile_desc = {
            "conservative": "保守型",
            "balanced": "平衡型", 
            "aggressive": "激进型"
        }
        
        strike = option["strike"]
        delta = option["delta"]
        annual_return = option["annualized_return"]
        assign_prob = option["assignment_probability"]
        
        distance_pct = ((underlying_price - strike) / underlying_price) * 100
        
        reasoning = f"{profile_desc[profile]}策略推荐: "
        
        if profile == "conservative":
            reasoning += f"执行价${strike:.2f}距离当前价格{distance_pct:.1f}%，Delta为{delta:.3f}，分配概率仅{assign_prob:.1f}%，适合稳健收入策略。"
        elif profile == "balanced":
            reasoning += f"执行价${strike:.2f}提供{annual_return:.1f}%年化收益，Delta {delta:.3f}平衡了收入与分配风险，综合评分最优。"
        else:  # aggressive
            reasoning += f"执行价${strike:.2f}年化收益达{annual_return:.1f}%，虽然分配概率{assign_prob:.1f}%较高，但适合追求高收益的策略。"
        
        return reasoning


class ProfessionalOrderFormatter:
    """专业订单格式化器"""
    
    def format_order_block(
        self,
        recommendation: Dict[str, Any],
        account_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成JP Morgan风格的专业订单格式
        
        Args:
            recommendation: 推荐策略数据
            account_info: 账户信息 (可选)
            
        Returns:
            格式化的订单字符串
        """
        option = recommendation["option_details"]
        pnl = recommendation["pnl_analysis"]
        risk = recommendation["risk_metrics"]
        
        # 格式化到期日
        exp_date = datetime.strptime(option["expiration"], "%Y-%m-%d")
        exp_formatted = exp_date.strftime("%b %d, %Y")
        
        order_block = f"""
╔══════════════════════════════════════════════════════════╗
║                 CASH SECURED PUT ORDER                   ║
╠══════════════════════════════════════════════════════════╣
║ Symbol:        {option['symbol']:<43} ║
║ Action:        SELL TO OPEN                              ║
║ Quantity:      1 CONTRACT (100 SHARES)                   ║
║ Order Type:    LIMIT                                     ║
║ Strike:        ${option['strike']:<6.2f}                             ║
║ Expiration:    {exp_formatted:<43} ║
║ Limit Price:   ${option['premium']:<6.2f} (MID: ${option['bid']:.2f}-${option['ask']:.2f})              ║
╠══════════════════════════════════════════════════════════╣
║                      P&L ANALYSIS                        ║
╠══════════════════════════════════════════════════════════╣
║ Max Profit:    ${pnl['max_profit']:<8.2f}                          ║
║ Breakeven:     ${pnl['breakeven_price']:<8.2f}                          ║
║ Capital Req:   ${pnl['required_capital']:<8,.2f}                        ║
║ Return:        {pnl['return_on_capital']:<6.2f}% ({pnl['annualized_return']:.1f}% APR)       ║
╠══════════════════════════════════════════════════════════╣
║                    RISK METRICS                          ║
╠══════════════════════════════════════════════════════════╣
║ Delta:         {risk['delta']:<8.4f}                              ║
║ Assign Prob:   {risk['assignment_probability']:<6.1f}%                            ║
║ Impl Vol:      {risk['implied_volatility']:<6.2%}                        ║
║ Theta/Day:     ${risk['theta_per_day']:<7.2f}                           ║
║ Liquidity:     {risk['liquidity_score']:<6.1f}/100                       ║
╚══════════════════════════════════════════════════════════╝

EXECUTION NOTES:
• Place limit order at mid-price or better
• Monitor fills during high liquidity periods (9:30-10:30 AM, 3:00-4:00 PM ET)
• Consider splitting orders >10 contracts across multiple strikes  
• Set GTC (Good Till Cancelled) with daily review
• Ensure adequate buying power: ${pnl['required_capital']:,.2f}

RISK DISCLAIMER:
• Cash secured puts require 100% cash collateral
• Assignment can occur at any time before expiration
• Monitor delta changes and market conditions daily
"""
        return order_block


# 辅助函数

async def export_csp_analysis_to_csv(
    symbol: str,
    recommendations: Dict[str, Dict[str, Any]],
    analyzed_options: List[Dict[str, Any]]
) -> str:
    """导出CSP分析到CSV文件"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"csp_{symbol}_{timestamp}.csv"
    
    # 确保data目录存在
    data_dir = "./data"
    os.makedirs(data_dir, exist_ok=True)
    filepath = os.path.join(data_dir, filename)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'profile', 'symbol', 'strike', 'expiration', 'delta', 
            'premium', 'bid', 'ask', 'annualized_return', 'assignment_probability',
            'breakeven', 'max_profit', 'required_capital', 'liquidity_score',
            'risk_score', 'recommendation_reasoning'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # 写入推荐数据
        for profile, rec in recommendations.items():
            opt = rec['option_details']
            pnl = rec['pnl_analysis']
            risk = rec['risk_metrics']
            
            writer.writerow({
                'profile': profile,
                'symbol': opt['symbol'],
                'strike': opt['strike'],
                'expiration': opt['expiration'],
                'delta': opt['delta'],
                'premium': opt['premium'],
                'bid': opt['bid'],
                'ask': opt['ask'],
                'annualized_return': pnl['annualized_return'],
                'assignment_probability': risk['assignment_probability'],
                'breakeven': pnl['breakeven_price'],
                'max_profit': pnl['max_profit'],
                'required_capital': pnl['required_capital'],
                'liquidity_score': risk['liquidity_score'],
                'risk_score': risk['risk_score'],
                'recommendation_reasoning': rec['recommendation_reasoning']
            })
    
    return filepath


async def get_market_context(
    symbol: str,
    client: TradierClient
) -> Dict[str, Any]:
    """获取市场上下文信息"""
    
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
        
        if not historical or len(historical) < 10:
            return {"error": "Insufficient historical data"}
        
        # 计算波动率指标
        closes = [float(bar.close) for bar in historical]
        returns = [
            (closes[i] - closes[i-1]) / closes[i-1] 
            for i in range(1, len(closes))
        ]
        
        historical_volatility = np.std(returns) * np.sqrt(252)  # 年化波动率
        
        # 识别关键技术位
        technical_levels = {
            "support_1": min(closes[-20:]) if len(closes) >= 20 else min(closes),
            "resistance_1": max(closes[-20:]) if len(closes) >= 20 else max(closes),
            "sma_20": sum(closes[-20:]) / 20 if len(closes) >= 20 else sum(closes) / len(closes),
            "sma_50": sum(closes[-50:]) / 50 if len(closes) >= 50 else None
        }
        
        return {
            "historical_volatility": historical_volatility,
            "technical_levels": technical_levels,
            "data_points": len(closes),
            "volatility_regime": "high" if historical_volatility > 0.30 else "normal" if historical_volatility > 0.15 else "low"
        }
        
    except Exception as e:
        print(f"Error getting market context: {e}")
        return {"error": str(e)}


def generate_execution_notes(
    recommendations: Dict[str, Dict[str, Any]],
    purpose_type: str
) -> str:
    """生成执行说明"""
    
    notes = []
    
    if purpose_type == "income":
        notes.append("• 收入策略重点：专注权利金收取，避免被分配")
        notes.append("• 如股价接近执行价，考虑展期操作")
        notes.append("• 监控Delta变化；如超过-0.40建议平仓")
    else:  # discount
        notes.append("• 折价策略重点：准备被分配，确保资金充足")
        notes.append("• 这是以折价买入股票的入场策略")
        notes.append("• 参考技术支撑位选择执行价")
    
    # 添加波动率相关说明
    if recommendations:
        sample_rec = next(iter(recommendations.values()))
        iv = sample_rec.get("risk_metrics", {}).get("implied_volatility", 0)
        
        if iv > 0.40:
            notes.append("• 高隐含波动率环境，有利于卖出权利金")
            notes.append("• 考虑较短期限以捕获波动率回落")
        elif iv < 0.20:
            notes.append("• 低隐含波动率环境，权利金收入有限")
            notes.append("• 可考虑等待波动率上升后再操作")
    
    notes.extend([
        "• 建议在正常交易时段执行，流动性更好",
        "• 使用限价单，避免期权市价单",
        "• 大单可考虑分批执行或多执行价分散"
    ])
    
    return "\n".join(notes)