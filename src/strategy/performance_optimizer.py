"""
Performance Optimization Module for Covered Call Strategy

Provides optimization utilities for large option chains analysis,
caching mechanisms, and performance monitoring.
"""

import time
import asyncio
from typing import Dict, Any, List, Optional, Callable
from functools import wraps, lru_cache
from datetime import datetime, timedelta
import json
import hashlib
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    operation_name: str
    start_time: float
    end_time: float
    duration: float
    options_analyzed: int
    cache_hits: int
    cache_misses: int
    memory_usage_mb: Optional[float] = None
    
    @property
    def options_per_second(self) -> float:
        """Calculate options analyzed per second"""
        return self.options_analyzed / self.duration if self.duration > 0 else 0


class PerformanceMonitor:
    """Performance monitoring and optimization utilities"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self._cache = {}
        self._cache_stats = {"hits": 0, "misses": 0}
        
    def timing_decorator(self, operation_name: str):
        """Decorator to measure execution time"""
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    end_time = time.time()
                    
                    # Extract metrics from result if available
                    options_count = 0
                    if isinstance(result, list):
                        options_count = len(result)
                    elif isinstance(result, dict) and 'analyzed_options' in result:
                        options_count = len(result['analyzed_options'])
                    
                    metrics = PerformanceMetrics(
                        operation_name=operation_name,
                        start_time=start_time,
                        end_time=end_time,
                        duration=end_time - start_time,
                        options_analyzed=options_count,
                        cache_hits=self._cache_stats["hits"],
                        cache_misses=self._cache_stats["misses"]
                    )
                    
                    self.metrics.append(metrics)
                    logger.info(f"{operation_name} completed in {metrics.duration:.2f}s, {options_count} options analyzed")
                    
                    return result
                except Exception as e:
                    end_time = time.time()
                    logger.error(f"{operation_name} failed after {end_time - start_time:.2f}s: {str(e)}")
                    raise
                    
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    end_time = time.time()
                    
                    options_count = len(result) if isinstance(result, list) else 0
                    
                    metrics = PerformanceMetrics(
                        operation_name=operation_name,
                        start_time=start_time,
                        end_time=end_time,
                        duration=end_time - start_time,
                        options_analyzed=options_count,
                        cache_hits=self._cache_stats["hits"],
                        cache_misses=self._cache_stats["misses"]
                    )
                    
                    self.metrics.append(metrics)
                    return result
                except Exception as e:
                    end_time = time.time()
                    logger.error(f"{operation_name} failed after {end_time - start_time:.2f}s: {str(e)}")
                    raise
                    
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    def get_cache_key(self, symbol: str, expiration: str, **kwargs) -> str:
        """Generate cache key for market data"""
        key_data = {
            "symbol": symbol,
            "expiration": expiration,
            **kwargs
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def cache_get(self, key: str) -> Optional[Any]:
        """Get data from cache with TTL check"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            # Check if cache entry is still valid (5 minutes TTL)
            if time.time() - timestamp < 300:
                self._cache_stats["hits"] += 1
                return data
            else:
                del self._cache[key]
        
        self._cache_stats["misses"] += 1
        return None
    
    def cache_set(self, key: str, data: Any) -> None:
        """Store data in cache with timestamp"""
        self._cache[key] = (data, time.time())
        
        # Cleanup old cache entries if cache gets too large
        if len(self._cache) > 1000:
            cutoff_time = time.time() - 300
            keys_to_remove = [
                k for k, (_, timestamp) in self._cache.items() 
                if timestamp < cutoff_time
            ]
            for k in keys_to_remove:
                del self._cache[k]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics"""
        if not self.metrics:
            return {"status": "no_metrics_available"}
        
        total_options = sum(m.options_analyzed for m in self.metrics)
        total_time = sum(m.duration for m in self.metrics)
        avg_duration = total_time / len(self.metrics)
        
        return {
            "total_operations": len(self.metrics),
            "total_options_analyzed": total_options,
            "total_execution_time": total_time,
            "average_operation_time": avg_duration,
            "options_per_second": total_options / total_time if total_time > 0 else 0,
            "cache_hit_rate": self._cache_stats["hits"] / (self._cache_stats["hits"] + self._cache_stats["misses"]) if (self._cache_stats["hits"] + self._cache_stats["misses"]) > 0 else 0,
            "cache_entries": len(self._cache)
        }


class OptimizedOptionAnalyzer:
    """Optimized option chain analyzer for large datasets"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.monitor = PerformanceMonitor()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    @PerformanceMonitor().timing_decorator("batch_option_analysis")
    async def analyze_option_batch(
        self,
        options: List[Any],
        analyzer_func: Callable,
        batch_size: int = 100
    ) -> List[Any]:
        """
        Process options in batches for better performance
        
        Args:
            options: List of option contracts to analyze
            analyzer_func: Function to analyze each option
            batch_size: Number of options to process in each batch
            
        Returns:
            List of analyzed option results
        """
        if len(options) <= batch_size:
            return [await analyzer_func(opt) for opt in options if opt]
        
        # Process in batches to avoid memory issues
        results = []
        for i in range(0, len(options), batch_size):
            batch = options[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[analyzer_func(opt) for opt in batch if opt],
                return_exceptions=True
            )
            
            # Filter out exceptions and None results
            valid_results = [
                result for result in batch_results 
                if result is not None and not isinstance(result, Exception)
            ]
            results.extend(valid_results)
            
            # Log progress for large datasets
            if len(options) > 500:
                progress = min(i + batch_size, len(options))
                logger.info(f"Processed {progress}/{len(options)} options ({progress/len(options)*100:.1f}%)")
        
        return results
    
    def parallel_calculate_metrics(
        self,
        options: List[Any],
        metric_functions: List[Callable]
    ) -> List[Dict[str, Any]]:
        """
        Calculate multiple metrics in parallel for better performance
        
        Args:
            options: List of option contracts
            metric_functions: List of functions to calculate metrics
            
        Returns:
            List of dictionaries containing calculated metrics
        """
        def calculate_all_metrics(option):
            metrics = {}
            for func in metric_functions:
                try:
                    result = func(option)
                    if isinstance(result, dict):
                        metrics.update(result)
                    else:
                        metrics[func.__name__] = result
                except Exception as e:
                    logger.warning(f"Metric calculation failed for {func.__name__}: {e}")
                    metrics[func.__name__] = None
            return metrics
        
        # Use thread pool for CPU-intensive calculations
        futures = [
            self.executor.submit(calculate_all_metrics, option) 
            for option in options
        ]
        
        results = []
        for future in futures:
            try:
                result = future.result(timeout=30)  # 30 second timeout
                results.append(result)
            except Exception as e:
                logger.error(f"Parallel metric calculation failed: {e}")
                results.append({})
        
        return results


class ErrorRecoveryManager:
    """Enhanced error handling and recovery mechanisms"""
    
    def __init__(self):
        self.error_counts = {}
        self.fallback_strategies = {}
        
    def register_fallback(self, error_type: str, fallback_func: Callable):
        """Register fallback function for specific error types"""
        self.fallback_strategies[error_type] = fallback_func
    
    async def execute_with_fallback(
        self,
        primary_func: Callable,
        fallback_key: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with fallback mechanisms
        
        Args:
            primary_func: Primary function to execute
            fallback_key: Key for fallback strategy
            *args, **kwargs: Arguments for the function
            
        Returns:
            Result from primary function or fallback
        """
        try:
            return await primary_func(*args, **kwargs)
        except Exception as e:
            error_type = type(e).__name__
            self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
            
            logger.warning(f"Primary function failed ({error_type}): {e}")
            
            # Try fallback if available
            if fallback_key in self.fallback_strategies:
                try:
                    logger.info(f"Attempting fallback strategy for {fallback_key}")
                    return await self.fallback_strategies[fallback_key](*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"Fallback strategy also failed: {fallback_error}")
                    raise fallback_error
            else:
                # No fallback available, re-raise original error
                raise e
    
    def get_error_statistics(self) -> Dict[str, int]:
        """Get error occurrence statistics"""
        return self.error_counts.copy()


class TimeoutManager:
    """Timeout management for API calls and long operations"""
    
    @staticmethod
    async def with_timeout(
        coro,
        timeout_seconds: float = 30.0,
        operation_name: str = "operation"
    ):
        """
        Execute coroutine with timeout
        
        Args:
            coro: Coroutine to execute
            timeout_seconds: Timeout in seconds
            operation_name: Name for logging
            
        Returns:
            Result of coroutine
            
        Raises:
            asyncio.TimeoutError: If operation times out
        """
        try:
            return await asyncio.wait_for(coro, timeout=timeout_seconds)
        except asyncio.TimeoutError:
            logger.error(f"{operation_name} timed out after {timeout_seconds} seconds")
            raise asyncio.TimeoutError(f"{operation_name} operation timed out")


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


@lru_cache(maxsize=128)
def calculate_technical_indicators_cached(
    prices: tuple,
    indicator_type: str
) -> Dict[str, float]:
    """
    Cached calculation of technical indicators
    
    Args:
        prices: Tuple of prices (for immutability and caching)
        indicator_type: Type of indicator to calculate
        
    Returns:
        Dictionary of calculated indicators
    """
    import numpy as np
    
    prices_array = np.array(prices)
    
    if indicator_type == "sma":
        return {
            "sma_20": np.mean(prices_array[-20:]) if len(prices_array) >= 20 else None,
            "sma_50": np.mean(prices_array[-50:]) if len(prices_array) >= 50 else None
        }
    elif indicator_type == "resistance":
        return {
            "resistance_20d": np.max(prices_array[-20:]) if len(prices_array) >= 20 else None,
            "resistance_60d": np.max(prices_array) if len(prices_array) > 0 else None
        }
    else:
        return {}


def optimize_large_position_analysis(shares_owned: int) -> Dict[str, Any]:
    """
    Optimize analysis parameters for large positions
    
    Args:
        shares_owned: Number of shares owned
        
    Returns:
        Optimized parameters for analysis
    """
    contracts_available = shares_owned // 100
    
    if contracts_available >= 50:
        # Very large position - use aggressive optimization
        return {
            "batch_size": 50,
            "parallel_workers": 8,
            "cache_ttl": 600,  # 10 minutes
            "analysis_depth": "basic",
            "recommendation": "Consider splitting analysis across multiple sessions"
        }
    elif contracts_available >= 20:
        # Large position - moderate optimization
        return {
            "batch_size": 25,
            "parallel_workers": 4,
            "cache_ttl": 300,  # 5 minutes
            "analysis_depth": "standard",
            "recommendation": "Analysis optimized for large position"
        }
    else:
        # Standard position - full analysis
        return {
            "batch_size": 10,
            "parallel_workers": 2,
            "cache_ttl": 60,   # 1 minute
            "analysis_depth": "comprehensive",
            "recommendation": "Full analysis recommended"
        }


class MemoryOptimizer:
    """Memory optimization utilities for large datasets"""
    
    @staticmethod
    def optimize_option_data(options: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Optimize option data by removing unnecessary fields and compacting data
        
        Args:
            options: List of option data dictionaries
            
        Returns:
            Optimized option data
        """
        essential_fields = {
            'symbol', 'strike', 'delta', 'premium', 'bid', 'ask',
            'open_interest', 'volume', 'implied_volatility', 'theta',
            'upside_capture', 'annualized_return', 'assignment_probability',
            'composite_score'
        }
        
        optimized = []
        for option in options:
            if option:
                # Keep only essential fields
                optimized_option = {
                    key: value for key, value in option.items()
                    if key in essential_fields and value is not None
                }
                
                # Round numerical values to reduce memory
                for key, value in optimized_option.items():
                    if isinstance(value, float):
                        optimized_option[key] = round(value, 4)
                
                optimized.append(optimized_option)
        
        return optimized
    
    @staticmethod
    def get_memory_usage_mb() -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0  # psutil not available


# Initialize components
optimizer = OptimizedOptionAnalyzer()
error_manager = ErrorRecoveryManager()
timeout_manager = TimeoutManager()
memory_optimizer = MemoryOptimizer()