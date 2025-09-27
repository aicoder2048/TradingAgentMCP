"""
策略模块 - 交易策略分析和实施工具

该模块提供各种期权交易策略的分析和实施功能，包括：
- 现金担保看跌期权策略 (Cash Secured Put)
- 策略分析引擎
- 风险计算工具
"""

from .cash_secured_put import (
    CashSecuredPutAnalyzer,
    StrategyRecommendationEngine,
    ProfessionalOrderFormatter,
    export_csp_analysis_to_csv,
    get_market_context,
    generate_execution_notes
)

from .strategy_analyzer import (
    DeltaBasedStrikeSelector,
    analyze_option_chain_loop
)

from .risk_calculator import (
    calculate_option_risk_metrics,
    calculate_pnl_scenarios,
    assess_assignment_probability
)

__all__ = [
    # Cash Secured Put Strategy
    "CashSecuredPutAnalyzer",
    "StrategyRecommendationEngine", 
    "ProfessionalOrderFormatter",
    "export_csp_analysis_to_csv",
    "get_market_context",
    "generate_execution_notes",
    
    # Strategy Analysis
    "DeltaBasedStrikeSelector",
    "analyze_option_chain_loop",
    
    # Risk Calculation
    "calculate_option_risk_metrics",
    "calculate_pnl_scenarios", 
    "assess_assignment_probability"
]