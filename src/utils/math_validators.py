"""
Mathematical validation and calculation utilities.
Provides safe mathematical operations and comparison logic validation.
"""

from typing import Dict, Optional, Union
import math


class MathValidator:
    """Mathematical logic validator for safe and accurate calculations."""
    
    @staticmethod
    def compare(
        actual: float, 
        target: float, 
        operation: str = 'exceeds'
    ) -> Dict[str, Union[float, bool, str, None]]:
        """
        Universal comparison function with detailed results.
        
        Args:
            actual: Actual value
            target: Target value
            operation: Comparison type ('exceeds', 'meets', 'below', 'equals')
            
        Returns:
            Dictionary with comparison results and metrics
        """
        operations = {
            'exceeds': actual > target,
            'meets': actual >= target,
            'below': actual < target,
            'equals': abs(actual - target) < 0.0001
        }
        
        # Generate descriptive text based on comparison
        if actual > target:
            relation = "超过"
            symbol = ">"
        elif actual < target:
            relation = "低于"
            symbol = "<"
        else:
            relation = "等于"
            symbol = "="
        
        return {
            'actual': actual,
            'target': target,
            'operation': operation,
            'result': operations.get(operation, False),
            'difference': actual - target,
            'ratio': MathValidator.safe_divide(actual, target),
            'percentage_diff': MathValidator.safe_divide(actual - target, target) * 100,
            'description': f"{actual:.2f}% {symbol} {target:.2f}%",
            'chinese_description': f"实际收益 {actual:.2f}% {relation}目标 {target:.2f}%"
        }
    
    @staticmethod
    def safe_divide(
        numerator: float, 
        denominator: float, 
        default: float = 0.0
    ) -> float:
        """
        Safe division to avoid division by zero errors.
        
        Args:
            numerator: The dividend
            denominator: The divisor
            default: Default value when denominator is zero
            
        Returns:
            Division result or default value
        """
        if denominator == 0 or math.isnan(denominator) or math.isinf(denominator):
            return default
        
        result = numerator / denominator
        
        # Handle infinity and NaN results
        if math.isnan(result) or math.isinf(result):
            return default
            
        return result
    
    @staticmethod
    def percentage(
        value: float, 
        total: float, 
        decimals: int = 2
    ) -> float:
        """
        Calculate percentage with safe division.
        
        Args:
            value: Part value
            total: Total value
            decimals: Number of decimal places
            
        Returns:
            Percentage value
        """
        raw_percentage = MathValidator.safe_divide(value, total) * 100
        return round(raw_percentage, decimals)
    
    @staticmethod
    def annualized_return(
        return_rate: float, 
        days: int
    ) -> float:
        """
        Calculate annualized return from period return.
        
        Args:
            return_rate: Period return rate (as decimal, e.g., 0.05 for 5%)
            days: Number of days in the period
            
        Returns:
            Annualized return rate
        """
        if days <= 0:
            return 0.0
        
        # Avoid negative returns that would cause math domain error
        if return_rate <= -1:
            return -1.0
        
        try:
            # Formula: (1 + period_return) ^ (365 / days) - 1
            annualized = math.pow(1 + return_rate, 365 / days) - 1
            
            # Sanity check for extreme values
            if math.isnan(annualized) or math.isinf(annualized):
                return 0.0
                
            return annualized
            
        except (ValueError, OverflowError):
            return 0.0
    
    @staticmethod
    def weighted_average(
        values: list, 
        weights: list
    ) -> Optional[float]:
        """
        Calculate weighted average.
        
        Args:
            values: List of values
            weights: List of weights (should sum to 1.0)
            
        Returns:
            Weighted average or None if invalid input
        """
        if not values or not weights or len(values) != len(weights):
            return None
        
        # Normalize weights if they don't sum to 1
        weight_sum = sum(weights)
        if weight_sum == 0:
            return None
            
        normalized_weights = [w / weight_sum for w in weights]
        
        return sum(v * w for v, w in zip(values, normalized_weights))
    
    @staticmethod
    def validate_percentage_allocation(
        allocations: Dict[str, float],
        tolerance: float = 0.01
    ) -> Dict[str, Union[bool, float, str]]:
        """
        Validate that percentage allocations sum to 100%.
        
        Args:
            allocations: Dictionary of name to percentage allocation
            tolerance: Acceptable deviation from 100%
            
        Returns:
            Validation results
        """
        total = sum(allocations.values())
        is_valid = abs(total - 100.0) <= tolerance
        
        return {
            'is_valid': is_valid,
            'total': total,
            'deviation': total - 100.0,
            'message': f"总分配: {total:.2f}% {'✓ 有效' if is_valid else '✗ 无效'}",
            'allocations': allocations
        }
    
    @staticmethod
    def format_percentage(
        value: float,
        decimals: int = 2,
        include_sign: bool = False
    ) -> str:
        """
        Format a decimal value as a percentage string.
        
        Args:
            value: Decimal value (e.g., 0.125 for 12.5%)
            decimals: Number of decimal places
            include_sign: Whether to include + sign for positive values
            
        Returns:
            Formatted percentage string
        """
        percentage = value * 100
        formatted = f"{percentage:.{decimals}f}%"
        
        if include_sign and percentage > 0:
            formatted = f"+{formatted}"
            
        return formatted
    
    @staticmethod
    def calculate_return_metrics(
        initial_value: float,
        final_value: float,
        days: int
    ) -> Dict[str, float]:
        """
        Calculate various return metrics.
        
        Args:
            initial_value: Starting value
            final_value: Ending value
            days: Investment period in days
            
        Returns:
            Dictionary of return metrics
        """
        if initial_value <= 0:
            return {
                'total_return': 0.0,
                'percentage_return': 0.0,
                'annualized_return': 0.0,
                'daily_return': 0.0
            }
        
        total_return = final_value - initial_value
        percentage_return = total_return / initial_value
        annualized = MathValidator.annualized_return(percentage_return, days)
        daily_return = percentage_return / days if days > 0 else 0
        
        return {
            'total_return': total_return,
            'percentage_return': percentage_return,
            'annualized_return': annualized,
            'daily_return': daily_return
        }