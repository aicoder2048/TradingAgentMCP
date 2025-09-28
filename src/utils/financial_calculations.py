"""
Financial calculation utilities for portfolio optimization.
Provides Sharpe ratio, risk metrics, and portfolio allocation calculations.
"""

from typing import Dict, List, Optional, Tuple
import math
from dataclasses import dataclass
from .math_validators import MathValidator


@dataclass
class StrategyMetrics:
    """Container for strategy performance metrics."""
    symbol: str
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_capital_required: float
    assignment_probability: float
    weight: Optional[float] = None


class FinancialCalculator:
    """Financial calculations for portfolio optimization."""
    
    # Default risk-free rate (US 10-year Treasury)
    DEFAULT_RISK_FREE_RATE = 0.048  # 4.8%
    
    @classmethod
    def calculate_sharpe_ratio(
        cls,
        annualized_return: float,
        volatility: float,
        risk_free_rate: Optional[float] = None
    ) -> float:
        """
        Calculate Sharpe ratio for risk-adjusted returns.
        
        Sharpe Ratio = (Return - Risk-Free Rate) / Volatility
        
        Args:
            annualized_return: Annual return as decimal (e.g., 0.35 for 35%)
            volatility: Standard deviation of returns
            risk_free_rate: Risk-free rate as decimal (default: 4.8%)
            
        Returns:
            Sharpe ratio value
        """
        if risk_free_rate is None:
            risk_free_rate = cls.DEFAULT_RISK_FREE_RATE
        
        # Handle edge cases
        if volatility <= 0:
            return 0.0
        
        excess_return = annualized_return - risk_free_rate
        sharpe = MathValidator.safe_divide(excess_return, volatility)
        
        return sharpe
    
    @classmethod
    def estimate_volatility_from_iv(
        cls,
        implied_volatility: float,
        time_to_expiry_days: int
    ) -> float:
        """
        Estimate annualized volatility from option implied volatility.
        
        Args:
            implied_volatility: IV from options (as decimal)
            time_to_expiry_days: Days to option expiration
            
        Returns:
            Estimated annualized volatility
        """
        # IV is already annualized, but we can adjust for the specific period
        # For short-term options, realized vol is often lower than IV
        adjustment_factor = 0.85  # Empirical adjustment
        
        # Adjust for time decay
        time_factor = math.sqrt(time_to_expiry_days / 365)
        
        # Estimated volatility
        estimated_vol = implied_volatility * adjustment_factor * time_factor
        
        return max(estimated_vol, 0.01)  # Minimum 1% volatility
    
    @classmethod
    def calculate_portfolio_sharpe_weights(
        cls,
        strategies: List[StrategyMetrics],
        risk_free_rate: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calculate portfolio weights based on Sharpe ratios.
        
        Method: Weight proportional to Sharpe ratio (higher Sharpe = higher weight)
        
        Args:
            strategies: List of strategy metrics
            risk_free_rate: Risk-free rate for Sharpe calculation
            
        Returns:
            Dictionary of symbol to weight allocation (0-1 scale)
        """
        if not strategies:
            return {}
        
        # Calculate Sharpe ratios if not already calculated
        for strategy in strategies:
            if strategy.sharpe_ratio == 0:
                strategy.sharpe_ratio = cls.calculate_sharpe_ratio(
                    strategy.annualized_return,
                    strategy.volatility,
                    risk_free_rate
                )
        
        # Filter out negative Sharpe ratios (below risk-free rate)
        positive_sharpe_strategies = [s for s in strategies if s.sharpe_ratio > 0]
        
        if not positive_sharpe_strategies:
            # If all Sharpe ratios are negative, equal weight
            equal_weight = 1.0 / len(strategies)
            return {s.symbol: equal_weight for s in strategies}
        
        # Calculate weights proportional to Sharpe ratio
        total_sharpe = sum(s.sharpe_ratio for s in positive_sharpe_strategies)
        
        weights = {}
        remaining_weight = 1.0
        
        for strategy in positive_sharpe_strategies:
            weight = MathValidator.safe_divide(strategy.sharpe_ratio, total_sharpe)
            weights[strategy.symbol] = weight
            remaining_weight -= weight
        
        # Allocate any remaining weight to zero-Sharpe strategies
        zero_sharpe_strategies = [s for s in strategies if s not in positive_sharpe_strategies]
        if zero_sharpe_strategies and abs(remaining_weight) > 0.001:
            per_strategy_weight = remaining_weight / len(zero_sharpe_strategies)
            for strategy in zero_sharpe_strategies:
                weights[strategy.symbol] = per_strategy_weight
        
        return weights
    
    @classmethod
    def calculate_kelly_criterion(
        cls,
        win_probability: float,
        win_return: float,
        loss_return: float
    ) -> float:
        """
        Calculate Kelly criterion for optimal position sizing.
        
        Kelly % = (p * b - q) / b
        where:
            p = probability of win
            q = probability of loss (1 - p)
            b = ratio of win to loss
        
        Args:
            win_probability: Probability of winning (0-1)
            win_return: Return if win (as decimal)
            loss_return: Loss if lose (as decimal, typically negative)
            
        Returns:
            Kelly percentage (fraction of capital to bet)
        """
        if loss_return >= 0 or win_return <= 0:
            return 0.0
        
        p = win_probability
        q = 1 - win_probability
        b = abs(win_return / loss_return)
        
        kelly = (p * b - q) / b
        
        # Apply Kelly fraction cap (never bet more than 25%)
        return min(max(kelly, 0), 0.25)
    
    @classmethod
    def calculate_risk_parity_weights(
        cls,
        volatilities: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate risk parity weights (inverse volatility weighting).
        
        Each asset contributes equally to portfolio risk.
        
        Args:
            volatilities: Dictionary of symbol to volatility
            
        Returns:
            Dictionary of symbol to weight allocation
        """
        if not volatilities:
            return {}
        
        # Calculate inverse volatilities
        inverse_vols = {}
        for symbol, vol in volatilities.items():
            if vol > 0:
                inverse_vols[symbol] = 1.0 / vol
            else:
                inverse_vols[symbol] = 0.0
        
        # Normalize to sum to 1
        total_inverse = sum(inverse_vols.values())
        
        if total_inverse == 0:
            # Equal weight if all volatilities are zero
            equal_weight = 1.0 / len(volatilities)
            return {s: equal_weight for s in volatilities}
        
        weights = {}
        for symbol, inverse_vol in inverse_vols.items():
            weights[symbol] = inverse_vol / total_inverse
        
        return weights
    
    @classmethod
    def calculate_portfolio_metrics(
        cls,
        strategies: List[StrategyMetrics],
        weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate portfolio-level metrics from individual strategies.
        
        Args:
            strategies: List of strategy metrics
            weights: Dictionary of symbol to weight
            
        Returns:
            Portfolio-level metrics
        """
        if not strategies or not weights:
            return {
                'portfolio_return': 0.0,
                'portfolio_volatility': 0.0,
                'portfolio_sharpe': 0.0,
                'total_capital': 0.0
            }
        
        # Calculate weighted returns
        portfolio_return = sum(
            weights.get(s.symbol, 0) * s.annualized_return 
            for s in strategies
        )
        
        # Simplified portfolio volatility (assuming no correlation)
        # In reality, should use correlation matrix
        portfolio_variance = sum(
            (weights.get(s.symbol, 0) ** 2) * (s.volatility ** 2)
            for s in strategies
        )
        portfolio_volatility = math.sqrt(portfolio_variance)
        
        # Portfolio Sharpe ratio
        portfolio_sharpe = cls.calculate_sharpe_ratio(
            portfolio_return,
            portfolio_volatility
        )
        
        # Total capital required
        total_capital = sum(
            weights.get(s.symbol, 0) * s.max_capital_required
            for s in strategies
        )
        
        return {
            'portfolio_return': portfolio_return,
            'portfolio_volatility': portfolio_volatility,
            'portfolio_sharpe': portfolio_sharpe,
            'total_capital': total_capital,
            'effective_return': portfolio_return * 100,  # As percentage
            'risk_adjusted_return': portfolio_sharpe * portfolio_volatility
        }
    
    @classmethod
    def format_allocation_explanation(
        cls,
        strategies: List[StrategyMetrics],
        weights: Dict[str, float],
        method: str = "sharpe"
    ) -> str:
        """
        Generate detailed explanation of allocation methodology.
        
        Args:
            strategies: List of strategy metrics
            weights: Calculated weights
            method: Allocation method used
            
        Returns:
            Formatted explanation string
        """
        explanation = f"## 投资组合配置方法论 - {method.upper()}加权\n\n"
        
        if method.lower() == "sharpe":
            explanation += "### 夏普比率加权配置说明\n\n"
            explanation += "夏普比率 = (年化收益率 - 无风险利率) / 波动率\n"
            explanation += f"无风险利率 = {cls.DEFAULT_RISK_FREE_RATE * 100:.2f}%\n\n"
            
            explanation += "### 各标的夏普比率计算:\n"
            for s in strategies:
                explanation += f"\n**{s.symbol}**:\n"
                explanation += f"  - 年化收益: {s.annualized_return * 100:.2f}%\n"
                explanation += f"  - 波动率: {s.volatility * 100:.2f}%\n"
                explanation += f"  - 夏普比率: {s.sharpe_ratio:.3f}\n"
                explanation += f"  - 配置权重: {weights.get(s.symbol, 0) * 100:.2f}%\n"
            
            explanation += "\n### 权重计算方法:\n"
            explanation += "权重 = 个股夏普比率 / 总夏普比率之和\n"
            explanation += "此方法使风险调整后收益较高的标的获得更大权重。\n"
            
        elif method.lower() == "risk_parity":
            explanation += "### 风险平价配置说明\n\n"
            explanation += "每个标的对组合的风险贡献相等。\n"
            explanation += "权重 = (1/波动率) / Σ(1/波动率)\n\n"
            
            for s in strategies:
                explanation += f"\n**{s.symbol}**: 波动率 {s.volatility * 100:.2f}% → 权重 {weights.get(s.symbol, 0) * 100:.2f}%\n"
        
        return explanation
    
    @classmethod
    def validate_capital_allocation(
        cls,
        total_capital: float,
        allocations: Dict[str, float],
        min_contracts: Dict[str, int] = None
    ) -> Tuple[bool, str]:
        """
        Validate if capital allocation is feasible.
        
        Args:
            total_capital: Total available capital
            allocations: Symbol to dollar amount allocations
            min_contracts: Minimum contracts required per symbol
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not allocations:
            return False, "没有分配方案"
        
        total_allocated = sum(allocations.values())
        
        if total_allocated > total_capital:
            return False, f"所需资金 ${total_allocated:,.0f} 超过可用资金 ${total_capital:,.0f}"
        
        if min_contracts:
            for symbol, min_count in min_contracts.items():
                if symbol in allocations and min_count > 0:
                    contract_value = allocations[symbol] / min_count
                    if contract_value < 100:  # Assuming minimum $100 per contract
                        return False, f"{symbol} 合约价值过低"
        
        return True, "资金分配有效"