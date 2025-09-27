"""
Enhanced Error Handling Module for Covered Call Strategy

Provides comprehensive error types, validation utilities, and recovery mechanisms.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better classification"""
    VALIDATION = "validation"
    MARKET_DATA = "market_data"
    API_ERROR = "api_error"
    CALCULATION = "calculation"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    TIMEOUT = "timeout"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class StrategyError:
    """Structured error information"""
    code: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    details: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    recovery_actions: Optional[List[str]] = None


class CoveredCallErrorHandler:
    """Comprehensive error handling for covered call strategies"""
    
    # Error code definitions
    ERROR_CODES = {
        "CC001": StrategyError(
            code="CC001",
            message="持股数量不足，无法实施covered call策略",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.HIGH,
            suggestions=[
                "购买足够的股票以达到100股的倍数",
                "考虑使用现金保障看跌策略作为替代",
                "等待积累更多股份后再实施策略"
            ],
            recovery_actions=[
                "检查当前持股数量",
                "计算需要额外购买的股票数量",
                "评估购买成本与策略收益"
            ]
        ),
        
        "CC002": StrategyError(
            code="CC002", 
            message="无法获取市场数据，请检查股票代码或网络连接",
            category=ErrorCategory.MARKET_DATA,
            severity=ErrorSeverity.CRITICAL,
            suggestions=[
                "验证股票代码拼写是否正确",
                "检查网络连接状态",
                "确认市场是否开放",
                "稍后重试"
            ],
            recovery_actions=[
                "使用备用数据源",
                "检查API限制",
                "验证认证令牌"
            ]
        ),
        
        "CC003": StrategyError(
            code="CC003",
            message="无法找到符合条件的期权，请调整策略参数",
            category=ErrorCategory.INSUFFICIENT_DATA,
            severity=ErrorSeverity.MEDIUM,
            suggestions=[
                "调整期权到期日期",
                "降低最低权利金要求",
                "扩大Delta范围",
                "选择不同的策略类型"
            ],
            recovery_actions=[
                "分析当前期权链",
                "检查流动性要求",
                "考虑更长期限的期权"
            ]
        ),
        
        "CC004": StrategyError(
            code="CC004",
            message="期权链数据分析超时，请稍后重试",
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            suggestions=[
                "稍后重试分析",
                "选择更短的期限",
                "减少分析的期权数量"
            ],
            recovery_actions=[
                "使用缓存数据",
                "简化分析参数",
                "分批处理期权数据"
            ]
        ),
        
        "CC005": StrategyError(
            code="CC005",
            message="API请求频率限制，请稍后重试",
            category=ErrorCategory.API_ERROR,
            severity=ErrorSeverity.MEDIUM,
            suggestions=[
                "等待几分钟后重试",
                "检查API使用配额",
                "考虑升级API计划"
            ],
            recovery_actions=[
                "实施请求速率限制",
                "使用缓存数据",
                "优化API调用频率"
            ]
        ),
        
        "CC006": StrategyError(
            code="CC006",
            message="策略参数配置无效",
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            suggestions=[
                "检查所有必需参数",
                "验证参数值范围",
                "使用默认推荐值"
            ],
            recovery_actions=[
                "重置为默认配置",
                "逐一验证参数",
                "查阅参数文档"
            ]
        ),
        
        "CC007": StrategyError(
            code="CC007",
            message="期权希腊字母计算失败",
            category=ErrorCategory.CALCULATION,
            severity=ErrorSeverity.MEDIUM,
            suggestions=[
                "使用简化分析模式",
                "检查市场数据完整性",
                "稍后重试"
            ],
            recovery_actions=[
                "使用历史平均值",
                "跳过复杂指标计算",
                "提供基础分析"
            ]
        ),
        
        "CC008": StrategyError(
            code="CC008",
            message="网络连接超时或不稳定",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            suggestions=[
                "检查网络连接",
                "重试操作",
                "使用备用网络"
            ],
            recovery_actions=[
                "使用离线模式",
                "启用重试机制",
                "缓存数据本地使用"
            ]
        )
    }
    
    def __init__(self):
        self.error_history: List[StrategyError] = []
        self.recovery_attempts = {}
    
    def handle_error(
        self,
        error_code: str,
        context: Optional[Dict[str, Any]] = None,
        custom_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle error with comprehensive information and suggestions
        
        Args:
            error_code: Error code from ERROR_CODES
            context: Additional context information
            custom_details: Custom error details
            
        Returns:
            Structured error response
        """
        if error_code not in self.ERROR_CODES:
            return self._handle_unknown_error(error_code, context, custom_details)
        
        error = self.ERROR_CODES[error_code]
        
        # Add to error history
        self.error_history.append(error)
        
        # Track recovery attempts
        self.recovery_attempts[error_code] = self.recovery_attempts.get(error_code, 0) + 1
        
        # Build comprehensive error response
        error_response = {
            "status": "error",
            "error_code": error.code,
            "error_message": error.message,
            "category": error.category.value,
            "severity": error.severity.value,
            "timestamp": self._get_timestamp(),
            "suggestions": error.suggestions or [],
            "recovery_actions": error.recovery_actions or [],
            "context": context or {},
            "details": {
                **(error.details or {}),
                **(custom_details or {}),
                "recovery_attempts": self.recovery_attempts[error_code]
            }
        }
        
        # Add escalation path for repeated errors
        if self.recovery_attempts[error_code] > 3:
            error_response["escalation"] = {
                "message": "多次尝试失败，建议寻求技术支持",
                "support_actions": [
                    "联系技术支持团队",
                    "提供错误日志和上下文",
                    "考虑使用备用策略"
                ]
            }
        
        logger.error(f"Handled error {error_code}: {error.message}")
        return error_response
    
    def _handle_unknown_error(
        self,
        error_code: str,
        context: Optional[Dict[str, Any]],
        custom_details: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle unknown error codes"""
        return {
            "status": "error",
            "error_code": "CC999",
            "error_message": f"未知错误代码: {error_code}",
            "category": ErrorCategory.CONFIGURATION.value,
            "severity": ErrorSeverity.HIGH.value,
            "timestamp": self._get_timestamp(),
            "suggestions": [
                "检查错误代码是否正确",
                "查阅错误代码文档",
                "联系技术支持"
            ],
            "context": context or {},
            "details": custom_details or {}
        }
    
    def validate_strategy_parameters(
        self,
        symbol: str,
        purpose_type: str,
        duration: str,
        shares_owned: int,
        avg_cost: Optional[float] = None,
        min_premium: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive parameter validation with specific error codes
        
        Returns:
            Validation result with specific error codes if validation fails
        """
        errors = []
        
        # Stock symbol validation
        if not symbol or not symbol.strip():
            errors.append(self.handle_error("CC006", 
                context={"parameter": "symbol", "value": symbol},
                custom_details={"validation_rule": "symbol_required"}
            ))
        elif len(symbol.strip()) > 5:
            errors.append(self.handle_error("CC006",
                context={"parameter": "symbol", "value": symbol},
                custom_details={"validation_rule": "symbol_length", "max_length": 5}
            ))
        
        # Shares validation
        if shares_owned < 100:
            errors.append(self.handle_error("CC001",
                context={
                    "shares_owned": shares_owned,
                    "shares_needed": 100,
                    "shortfall": 100 - shares_owned
                }
            ))
        
        # Strategy type validation
        valid_purposes = ["income", "exit"]
        if purpose_type not in valid_purposes:
            errors.append(self.handle_error("CC006",
                context={
                    "parameter": "purpose_type",
                    "value": purpose_type,
                    "valid_values": valid_purposes
                }
            ))
        
        # Duration validation
        valid_durations = ["1w", "2w", "1m", "3m", "6m", "1y"]
        if duration not in valid_durations:
            errors.append(self.handle_error("CC006",
                context={
                    "parameter": "duration", 
                    "value": duration,
                    "valid_values": valid_durations
                }
            ))
        
        # Cost validations
        if avg_cost is not None and avg_cost <= 0:
            errors.append(self.handle_error("CC006",
                context={
                    "parameter": "avg_cost",
                    "value": avg_cost,
                    "validation_rule": "positive_number"
                }
            ))
        
        if min_premium is not None and min_premium <= 0:
            errors.append(self.handle_error("CC006",
                context={
                    "parameter": "min_premium",
                    "value": min_premium,
                    "validation_rule": "positive_number"
                }
            ))
        
        if errors:
            return {
                "is_valid": False,
                "errors": errors,
                "error_count": len(errors)
            }
        
        return {
            "is_valid": True,
            "errors": [],
            "validation_summary": "All parameters are valid"
        }
    
    def classify_exception(self, exception: Exception) -> str:
        """
        Classify exceptions into error codes
        
        Args:
            exception: The exception to classify
            
        Returns:
            Appropriate error code
        """
        exception_type = type(exception).__name__
        exception_message = str(exception).lower()
        
        # Network and timeout errors
        if "timeout" in exception_message or exception_type in ["TimeoutError", "ConnectTimeout"]:
            return "CC004"
        
        # API and HTTP errors
        if "api" in exception_message or exception_type in ["HTTPError", "RequestException"]:
            if "rate limit" in exception_message or "429" in exception_message:
                return "CC005"
            else:
                return "CC002"
        
        # Network connectivity
        if exception_type in ["ConnectionError", "NetworkError"]:
            return "CC008"
        
        # Calculation errors
        if exception_type in ["ValueError", "TypeError", "ZeroDivisionError"]:
            return "CC007"
        
        # Default to configuration error for unknown exceptions
        return "CC006"
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error occurrence statistics"""
        if not self.error_history:
            return {"status": "no_errors_recorded"}
        
        # Count errors by category and severity
        category_counts = {}
        severity_counts = {}
        
        for error in self.error_history:
            category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "errors_by_category": category_counts,
            "errors_by_severity": severity_counts,
            "recovery_attempts": self.recovery_attempts.copy(),
            "most_common_error": max(self.recovery_attempts.items(), key=lambda x: x[1])[0] if self.recovery_attempts else None
        }
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class RecoveryStrategies:
    """Recovery strategies for different error scenarios"""
    
    @staticmethod
    async def fallback_market_data(symbol: str) -> Optional[Dict[str, Any]]:
        """Fallback strategy for market data retrieval"""
        try:
            # Implementation would use cached data or alternative data source
            logger.info(f"Attempting fallback market data retrieval for {symbol}")
            return {
                "source": "fallback",
                "symbol": symbol,
                "estimated_price": None,
                "message": "使用备用数据源或缓存数据"
            }
        except Exception as e:
            logger.error(f"Fallback market data strategy failed: {e}")
            return None
    
    @staticmethod
    async def simplified_analysis(options: List[Any]) -> List[Dict[str, Any]]:
        """Simplified analysis when full analysis fails"""
        try:
            # Basic analysis without complex calculations
            simplified_results = []
            for option in options[:10]:  # Limit to first 10 options
                if hasattr(option, 'strike') and hasattr(option, 'bid') and hasattr(option, 'ask'):
                    simplified_results.append({
                        "symbol": getattr(option, 'symbol', 'Unknown'),
                        "strike": option.strike,
                        "premium": (option.bid + option.ask) / 2 if option.bid and option.ask else 0,
                        "analysis_type": "simplified"
                    })
            return simplified_results
        except Exception as e:
            logger.error(f"Simplified analysis strategy failed: {e}")
            return []


# Global error handler instance
error_handler = CoveredCallErrorHandler()