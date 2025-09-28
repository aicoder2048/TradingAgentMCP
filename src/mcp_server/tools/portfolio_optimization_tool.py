"""
Portfolio optimization MCP tool for scientific allocation strategies.
Implements Sharpe ratio-based and other optimization methods.
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from ...utils.financial_calculations import FinancialCalculator, StrategyMetrics
from ...utils.math_validators import MathValidator


async def portfolio_optimization_tool_mcp(
    strategies_data: List[Dict[str, Any]],
    total_capital: float,
    optimization_method: str = "sharpe",
    risk_free_rate: Optional[float] = None,
    constraints: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Portfolio optimization tool using various scientific methods.
    
    This tool implements multiple portfolio optimization strategies including:
    - Sharpe ratio optimization (default)
    - Risk parity allocation
    - Kelly criterion sizing
    - Equal weight allocation
    
    Args:
        strategies_data: List of strategy dictionaries with metrics
            Each should contain:
            - symbol: Stock ticker
            - annualized_return: Expected annual return (decimal)
            - premium_collected: Premium from option strategy
            - capital_required: Capital needed for strategy
            - assignment_probability: Probability of assignment
            - days_to_expiry: Days until option expiration
            - implied_volatility: Option IV (optional)
            
        total_capital: Total available capital for allocation
        
        optimization_method: Method to use for optimization
            - "sharpe": Sharpe ratio weighted (default)
            - "risk_parity": Risk parity allocation
            - "equal": Equal weight allocation
            - "kelly": Kelly criterion sizing
            
        risk_free_rate: Risk-free rate for Sharpe calculation (default: 4.8%)
        
        constraints: Optional constraints dictionary
            - min_allocation: Minimum allocation per position (default: 0.05)
            - max_allocation: Maximum allocation per position (default: 0.60)
            - min_positions: Minimum number of positions (default: 2)
            
    Returns:
        Dictionary containing:
        - allocations: Symbol to allocation percentage mapping
        - capital_allocations: Symbol to dollar amount mapping
        - metrics: Portfolio and individual strategy metrics
        - explanation: Detailed methodology explanation
        - validation: Validation results and warnings
    """
    
    try:
        # Parse and validate input strategies
        strategies = []
        for data in strategies_data:
            # Estimate volatility from IV or use default
            if 'implied_volatility' in data and data['implied_volatility'] > 0:
                volatility = FinancialCalculator.estimate_volatility_from_iv(
                    data['implied_volatility'],
                    data.get('days_to_expiry', 30)
                )
            else:
                # Use assignment probability as proxy for volatility
                assignment_prob = data.get('assignment_probability', 0.20)
                volatility = assignment_prob * 0.5  # Rough estimate
            
            strategy = StrategyMetrics(
                symbol=data['symbol'],
                annualized_return=data.get('annualized_return', 0),
                volatility=volatility,
                sharpe_ratio=0,  # Will be calculated
                max_capital_required=data.get('capital_required', 0),
                assignment_probability=data.get('assignment_probability', 0.20)
            )
            strategies.append(strategy)
        
        # Apply constraints
        if constraints is None:
            constraints = {
                'min_allocation': 0.00,  # 0% minimum (allow zero allocation)
                'max_allocation': 0.80,  # 80% maximum (allow concentration)
                'min_positions': 1        # At least 1 position
            }
        
        # Calculate optimization based on method
        if optimization_method.lower() == "sharpe":
            weights = FinancialCalculator.calculate_portfolio_sharpe_weights(
                strategies, 
                risk_free_rate
            )
            method_description = "夏普比率加权优化"
            
        elif optimization_method.lower() == "risk_parity":
            volatilities = {s.symbol: s.volatility for s in strategies}
            weights = FinancialCalculator.calculate_risk_parity_weights(volatilities)
            method_description = "风险平价配置"
            
        elif optimization_method.lower() == "kelly":
            # Kelly criterion for each strategy
            weights = {}
            for strategy in strategies:
                win_prob = 1 - strategy.assignment_probability
                win_return = strategy.annualized_return
                loss_return = -0.10  # Assume 10% loss if assigned
                
                kelly_pct = FinancialCalculator.calculate_kelly_criterion(
                    win_prob, win_return, loss_return
                )
                weights[strategy.symbol] = kelly_pct
            
            # Normalize Kelly percentages
            total_kelly = sum(weights.values())
            if total_kelly > 0:
                weights = {k: v/total_kelly for k, v in weights.items()}
            method_description = "凯利准则优化"
            
        else:  # Equal weight
            equal_weight = 1.0 / len(strategies)
            weights = {s.symbol: equal_weight for s in strategies}
            method_description = "等权重配置"
        
        # Apply constraints to weights
        adjusted_weights = apply_constraints(weights, constraints)
        
        # Calculate capital allocations
        capital_allocations = {
            symbol: weight * total_capital 
            for symbol, weight in adjusted_weights.items()
        }
        
        # Calculate portfolio metrics
        portfolio_metrics = FinancialCalculator.calculate_portfolio_metrics(
            strategies, adjusted_weights
        )
        
        # Generate detailed explanation
        explanation = FinancialCalculator.format_allocation_explanation(
            strategies, adjusted_weights, optimization_method
        )
        
        # Add performance comparison vs target
        target_return = 0.50  # 50% target
        comparison = MathValidator.compare(
            portfolio_metrics['effective_return'], 
            target_return * 100,
            'exceeds'
        )
        
        # Validation
        validation_result, validation_msg = FinancialCalculator.validate_capital_allocation(
            total_capital, capital_allocations
        )
        
        # Prepare individual strategy details
        strategy_details = []
        for strategy in strategies:
            strategy_details.append({
                'symbol': strategy.symbol,
                'weight': adjusted_weights.get(strategy.symbol, 0),
                'capital_allocated': capital_allocations.get(strategy.symbol, 0),
                'annualized_return': strategy.annualized_return,
                'volatility': strategy.volatility,
                'sharpe_ratio': strategy.sharpe_ratio,
                'assignment_probability': strategy.assignment_probability
            })
        
        result = {
            'success': True,
            'optimization_method': method_description,
            'allocations': {
                k: round(v * 100, 2) for k, v in adjusted_weights.items()
            },  # As percentages
            'capital_allocations': capital_allocations,
            'portfolio_metrics': {
                'expected_annual_return': round(portfolio_metrics['portfolio_return'] * 100, 2),
                'portfolio_volatility': round(portfolio_metrics['portfolio_volatility'] * 100, 2),
                'portfolio_sharpe_ratio': round(portfolio_metrics['portfolio_sharpe'], 3),
                'total_capital_required': round(portfolio_metrics['total_capital'], 2),
                'risk_adjusted_return': round(portfolio_metrics['risk_adjusted_return'] * 100, 2)
            },
            'strategy_details': strategy_details,
            'performance_vs_target': {
                'actual_return': round(portfolio_metrics['effective_return'], 2),
                'target_return': round(target_return * 100, 2),
                'exceeds_target': comparison['result'],
                'difference': round(comparison['difference'], 2),
                'description': comparison['chinese_description']
            },
            'explanation': explanation,
            'validation': {
                'is_valid': validation_result,
                'message': validation_msg,
                'constraints_applied': constraints
            },
            'timestamp': datetime.now().isoformat(),
            'risk_free_rate_used': risk_free_rate or FinancialCalculator.DEFAULT_RISK_FREE_RATE
        }
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'timestamp': datetime.now().isoformat()
        }


def apply_constraints(
    weights: Dict[str, float],
    constraints: Dict[str, Any]
) -> Dict[str, float]:
    """
    Apply portfolio constraints to weights.
    
    Args:
        weights: Original weights
        constraints: Constraint dictionary
        
    Returns:
        Adjusted weights satisfying constraints
    """
    min_alloc = constraints.get('min_allocation', 0.00)
    max_alloc = constraints.get('max_allocation', 0.80)
    min_positions = constraints.get('min_positions', 1)
    
    adjusted = weights.copy()
    
    # Apply min/max constraints
    for symbol in adjusted:
        # Only apply minimum if weight is already non-zero
        if adjusted[symbol] > 0:
            if adjusted[symbol] < min_alloc and min_alloc > 0:
                adjusted[symbol] = min_alloc
            elif adjusted[symbol] > max_alloc:
                adjusted[symbol] = max_alloc
    
    # Ensure minimum positions
    if len([w for w in adjusted.values() if w > 0]) < min_positions:
        # If not enough positions, equal weight the minimum
        sorted_symbols = sorted(adjusted.keys(), key=lambda x: adjusted[x], reverse=True)
        top_symbols = sorted_symbols[:min_positions]
        
        equal_weight = 1.0 / min_positions
        adjusted = {s: equal_weight if s in top_symbols else 0 for s in adjusted}
    
    # Renormalize to sum to 1
    total = sum(adjusted.values())
    if total > 0:
        adjusted = {k: v/total for k, v in adjusted.items()}
    
    return adjusted


# Export for MCP server registration
__all__ = ['portfolio_optimization_tool_mcp']