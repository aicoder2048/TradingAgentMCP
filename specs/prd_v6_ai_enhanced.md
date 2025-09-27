# PRD v6 - Cash Secured Put Strategy MCP Server Tool Implementation Plan

## Executive Summary

This document outlines the comprehensive implementation plan for the Cash Secured Put (CSP) Strategy MCP Server Tool, an advanced options trading analysis system designed to automate the selection and recommendation of cash secured put options. The tool integrates seamlessly with the existing TradingAgentMCP infrastructure, leveraging real-time Tradier API data to provide institutional-grade options strategy recommendations.

## Problem Statement & Objectives

### Core Problem
Options traders need sophisticated tools to implement the cash secured put strategy effectively, balancing income generation with risk management. Current manual analysis is time-consuming and prone to missing optimal opportunities. The tool must analyze multiple factors including:

- Delta/probability of assignment across different strikes
- Premium income vs. capital requirements
- Duration optimization based on theta decay
- Market volatility and technical indicators
- Risk-adjusted returns

### Strategic Objectives

1. **Automated Strategy Construction**: Develop an MCP tool that automatically analyzes options chains to identify optimal CSP opportunities based on user-defined criteria
2. **Risk-Based Classification**: Implement dual-purpose strategy types:
   - **Income Strategy** (10-30% delta): Focus on premium collection with lower assignment probability
   - **Discount Strategy** (30-70% delta): Accept higher assignment risk for acquiring stocks at discount
3. **Duration Flexibility**: Support multiple time horizons from weekly to yearly expirations
4. **Professional Analytics**: Provide institutional-quality P&L analysis, Greeks, and order formatting
5. **Intelligent Recommendations**: Generate three risk-adjusted alternatives (conservative, balanced, aggressive)

## Technical Architecture

### System Architecture
```
┌─────────────────────────────────────────────┐
│           Claude Code Client                │
└─────────────────────────────────────────────┘
                    ↓ MCP Protocol
┌─────────────────────────────────────────────┐
│         MCP Server (FastMCP)                │
├─────────────────────────────────────────────┤
│   Cash Secured Put Strategy Tool            │
├─────────────────────────────────────────────┤
│ Core Components:                            │
│ • cash_secured_put_strategy_tool()         │
│ • analyze_csp_opportunities()              │
│ • calculate_optimal_strikes()              │
│ • generate_strategy_recommendations()      │
├─────────────────────────────────────────────┤
│ Analysis Engine:                            │
│ • Delta-based strike selection             │
│ • Premium yield optimization               │
│ • Risk assessment algorithms               │
│ • P&L scenario modeling                    │
├─────────────────────────────────────────────┤
│ Data Layer:                                │
│ • Real-time options chains                 │
│ • Greeks calculation                       │
│ • Historical volatility analysis           │
│ • CSV export functionality                 │
└─────────────────────────────────────────────┘
                    ↓ REST API
┌─────────────────────────────────────────────┐
│            Tradier API                      │
│   • /v1/markets/options/chains              │
│   • /v1/markets/options/expirations         │
│   • /v1/markets/quotes                      │
│   • /v1/markets/history                     │
└─────────────────────────────────────────────┘
```

### Module Structure
```
src/
├── strategy/                                  # NEW: Strategy module
│   ├── __init__.py
│   ├── cash_secured_put.py                  # Core CSP strategy logic
│   ├── strategy_analyzer.py                 # Strategy analysis engine
│   └── risk_calculator.py                   # Risk metrics calculation
├── option/                                   # Existing module (extended)
│   ├── option_expiration_selector.py        # NEW: Duration-based expiry selection
│   └── greeks_enhanced.py                   # NEW: Enhanced Greeks calculations
├── mcp_server/
│   └── tools/
│       └── cash_secured_put_strategy_tool.py # MCP tool implementation
└── provider/tradier/
    └── client.py                            # Extended with CSP-specific methods
```

## Detailed Implementation Plan

### Phase 1: Core Infrastructure & Data Layer

#### 1.1 Extend Tradier Client
**File**: `src/provider/tradier/client.py`

```python
def get_options_by_delta_range(
    self,
    symbol: str,
    expiration: str,
    option_type: str,
    delta_min: float,
    delta_max: float
) -> List[OptionContract]:
    """
    Get options within specified delta range.
    Optimized for CSP strategy selection.
    """

def get_next_expiration_by_duration(
    self,
    symbol: str,
    duration: str  # "1w", "2w", "1m", "3m", "6m", "1y"
) -> str:
    """
    Get the next appropriate expiration date based on duration.
    Handles weekly/monthly options and trading day calculations.
    """

def calculate_implied_volatility_surface(
    self,
    symbol: str,
    expiration_dates: List[str]
) -> Dict[str, Dict[float, float]]:
    """
    Build IV surface for volatility analysis.
    """
```

#### 1.2 Create Strategy Analysis Engine
**File**: `src/strategy/cash_secured_put.py`

```python
class CashSecuredPutAnalyzer:
    """Core analyzer for CSP opportunities."""
    
    def __init__(
        self,
        symbol: str,
        purpose_type: str,  # "income" or "discount"
        duration: str,
        tradier_client: TradierClient
    ):
        self.symbol = symbol
        self.purpose_type = purpose_type
        self.duration = duration
        self.client = tradier_client
        
        # Delta ranges based on purpose
        self.delta_ranges = {
            "income": {"min": -0.30, "max": -0.10},
            "discount": {"min": -0.70, "max": -0.30}
        }
    
    async def find_optimal_strikes(
        self,
        expiration: str,
        underlying_price: float,
        capital_limit: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Find optimal strike prices based on delta requirements.
        Returns sorted list of opportunities.
        """
        
    async def calculate_strategy_metrics(
        self,
        option_contract: OptionContract,
        underlying_price: float
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive metrics for a CSP position:
        - Annualized return on capital
        - Break-even price
        - Maximum loss scenarios
        - Probability of profit
        - Expected value
        """
        
    def classify_risk_profile(
        self,
        options: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Classify options into conservative, balanced, aggressive.
        Based on delta, premium yield, and days to expiry.
        """
```

### Phase 2: Strategy Selection Logic

#### 2.1 Expiration Date Selection
**File**: `src/option/option_expiration_selector.py`

```python
class ExpirationSelector:
    """Intelligent expiration date selection based on duration preferences."""
    
    DURATION_MAPPINGS = {
        "1w": {"min_days": 5, "max_days": 9, "preferred": "weekly"},
        "2w": {"min_days": 10, "max_days": 18, "preferred": "weekly"},
        "1m": {"min_days": 25, "max_days": 35, "preferred": "monthly"},
        "3m": {"min_days": 80, "max_days": 100, "preferred": "monthly"},
        "6m": {"min_days": 170, "max_days": 190, "preferred": "monthly"},
        "1y": {"min_days": 350, "max_days": 380, "preferred": "leaps"}
    }
    
    async def get_optimal_expiration(
        self,
        symbol: str,
        duration: str,
        prefer_high_liquidity: bool = True
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Select optimal expiration date considering:
        - Duration requirements
        - Liquidity (open interest/volume)
        - Weekly vs monthly preference
        - Special events (earnings, dividends)
        """
```

#### 2.2 Delta-Based Strike Selection Algorithm
**File**: `src/strategy/strategy_analyzer.py`

```python
class DeltaBasedStrikeSelector:
    """Advanced strike selection using delta and market structure."""
    
    async def analyze_option_chain_loop(
        self,
        option_chain: List[OptionContract],
        target_delta_range: Tuple[float, float],
        underlying_price: float
    ) -> List[Dict[str, Any]]:
        """
        Implements the <analyze-option-loop> logic:
        1. Filter by delta range
        2. Calculate premium yield
        3. Assess liquidity (bid-ask spread, open interest)
        4. Score based on risk-reward profile
        5. Rank opportunities
        """
        
        analyzed_options = []
        
        for option in option_chain:
            if not self._is_within_delta_range(option, target_delta_range):
                continue
                
            metrics = {
                "symbol": option.symbol,
                "strike": option.strike,
                "delta": option.greeks.get("delta"),
                "premium": (option.bid + option.ask) / 2,
                "bid_ask_spread": option.ask - option.bid,
                "open_interest": option.open_interest,
                "volume": option.volume,
                "implied_volatility": option.greeks.get("mid_iv"),
                "theta": option.greeks.get("theta"),
                "premium_yield": self._calculate_premium_yield(option, underlying_price),
                "annualized_return": self._calculate_annualized_return(option, underlying_price),
                "assignment_probability": abs(option.greeks.get("delta", 0)) * 100,
                "liquidity_score": self._calculate_liquidity_score(option),
                "risk_score": self._calculate_risk_score(option, underlying_price)
            }
            
            analyzed_options.append(metrics)
        
        # Sort by composite score
        return sorted(
            analyzed_options,
            key=lambda x: x["annualized_return"] * x["liquidity_score"],
            reverse=True
        )
```

### Phase 3: Recommendation Engine

#### 3.1 Strategy Recommendation Generator
**File**: `src/strategy/cash_secured_put.py`

```python
class StrategyRecommendationEngine:
    """Generate professional strategy recommendations."""
    
    def generate_three_alternatives(
        self,
        analyzed_options: List[Dict[str, Any]],
        underlying_price: float,
        purpose_type: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate conservative, balanced, and aggressive alternatives.
        """
        
        recommendations = {}
        
        # Conservative: Lower delta, higher probability of keeping premium
        conservative = self._select_conservative_option(analyzed_options, purpose_type)
        
        # Balanced: Optimal risk-reward ratio
        balanced = self._select_balanced_option(analyzed_options, purpose_type)
        
        # Aggressive: Higher delta, better premium, higher assignment risk
        aggressive = self._select_aggressive_option(analyzed_options, purpose_type)
        
        for name, option in [
            ("conservative", conservative),
            ("balanced", balanced),
            ("aggressive", aggressive)
        ]:
            if option:
                recommendations[name] = self._build_recommendation(
                    option, underlying_price, name
                )
        
        return recommendations
    
    def _build_recommendation(
        self,
        option: Dict[str, Any],
        underlying_price: float,
        profile: str
    ) -> Dict[str, Any]:
        """Build comprehensive recommendation with P&L analysis."""
        
        strike = option["strike"]
        premium = option["premium"]
        
        return {
            "profile": profile,
            "option_details": option,
            "pnl_analysis": {
                "max_profit": premium * 100,
                "max_profit_scenario": "Option expires worthless",
                "breakeven_price": strike - premium,
                "max_loss": (strike - premium) * 100,
                "max_loss_scenario": f"Stock falls to $0",
                "profit_at_current": premium * 100 if underlying_price > strike else None,
                "required_capital": strike * 100,
                "return_on_capital": (premium / strike) * 100,
                "annualized_return": option["annualized_return"]
            },
            "risk_metrics": {
                "assignment_probability": option["assignment_probability"],
                "delta": option["delta"],
                "theta_per_day": option["theta"] * 100,
                "implied_volatility": option["implied_volatility"],
                "liquidity_score": option["liquidity_score"]
            },
            "recommendation_reasoning": self._generate_reasoning(option, profile, underlying_price)
        }
```

#### 3.2 Professional Order Formatting
**File**: `src/strategy/cash_secured_put.py`

```python
class ProfessionalOrderFormatter:
    """Format orders following institutional trading conventions."""
    
    def format_order_block(
        self,
        recommendation: Dict[str, Any],
        account_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate professional order block in JP Morgan style format.
        """
        
        option = recommendation["option_details"]
        pnl = recommendation["pnl_analysis"]
        
        order_block = f"""
╔══════════════════════════════════════════════════════════╗
║                  CASH SECURED PUT ORDER                   ║
╠══════════════════════════════════════════════════════════╣
║ Symbol:        {option['symbol']:43} ║
║ Action:        SELL TO OPEN                              ║
║ Quantity:      1 CONTRACT (100 SHARES)                   ║
║ Order Type:    LIMIT                                     ║
║ Strike:        ${option['strike']:<6.2f}                             ║
║ Expiration:    {self._format_expiration(option['expiration']):43} ║
║ Limit Price:   ${option['premium']:<6.2f} (MID)                      ║
╠══════════════════════════════════════════════════════════╣
║                      P&L ANALYSIS                        ║
╠══════════════════════════════════════════════════════════╣
║ Max Profit:    ${pnl['max_profit']:<8.2f}                          ║
║ Breakeven:     ${pnl['breakeven_price']:<8.2f}                          ║
║ Capital Req:   ${pnl['required_capital']:<8.2f}                          ║
║ Return:        {pnl['return_on_capital']:<6.2%} ({pnl['annualized_return']:.2f}% APR)        ║
╠══════════════════════════════════════════════════════════╣
║                    RISK METRICS                          ║
╠══════════════════════════════════════════════════════════╣
║ Delta:         {option['delta']:<8.4f}                              ║
║ Assign Prob:   {option['assignment_probability']:<6.1f}%                            ║
║ Impl Vol:      {option['implied_volatility']:<6.2%}                        ║
║ Theta/Day:     ${abs(option['theta']) * 100:<7.2f}                           ║
╚══════════════════════════════════════════════════════════╝

EXECUTION NOTES:
• Place limit order at mid-price or better
• Monitor for fills during high liquidity periods (9:30-10:30 AM, 3:00-4:00 PM ET)
• Consider splitting large orders across multiple strikes if size > 10 contracts
• Set GTC (Good Till Cancelled) with daily review
"""
        return order_block
```

### Phase 4: MCP Tool Implementation

#### 4.1 Main MCP Tool Function
**File**: `src/mcp_server/tools/cash_secured_put_strategy_tool.py`

```python
from typing import Dict, Any, Optional
from ..config.settings import settings
from ...provider.tradier.client import TradierClient
from ...strategy.cash_secured_put import (
    CashSecuredPutAnalyzer,
    StrategyRecommendationEngine,
    ProfessionalOrderFormatter
)

async def cash_secured_put_strategy_tool(
    symbol: str,
    purpose_type: str = "income",
    duration: str = "1w",
    capital_limit: Optional[float] = None,
    include_order_blocks: bool = True
) -> Dict[str, Any]:
    """
    Cash Secured Put Strategy MCP Tool
    
    Analyzes options chains to recommend optimal cash secured put strategies
    based on purpose (income vs discount) and time horizon.
    
    Args:
        symbol: Stock ticker symbol (e.g., "AAPL", "TSLA")
        purpose_type: Strategy purpose - "income" (10-30% delta) or "discount" (30-70% delta)
        duration: Time horizon - "1w", "2w", "1m", "3m", "6m", "1y"
        capital_limit: Maximum capital to allocate (optional)
        include_order_blocks: Generate professional order formatting
    
    Returns:
        Comprehensive strategy analysis with three alternatives:
        {
            "symbol": "AAPL",
            "current_price": 150.25,
            "analysis_timestamp": "2024-01-15 14:30:00 ET",
            "strategy_parameters": {...},
            "selected_expiration": {
                "date": "2024-01-19",
                "days_to_expiry": 4,
                "type": "weekly"
            },
            "recommendations": {
                "conservative": {...},
                "balanced": {...},
                "aggressive": {...}
            },
            "market_context": {
                "implied_volatility": 0.25,
                "iv_rank": 45,
                "technical_levels": {...}
            },
            "csv_export_path": "./data/csp_AAPL_20240115_143000.csv",
            "execution_notes": "..."
        }
    """
    
    try:
        # Initialize components
        client = TradierClient()
        analyzer = CashSecuredPutAnalyzer(
            symbol=symbol,
            purpose_type=purpose_type,
            duration=duration,
            tradier_client=client
        )
        
        # Get current market data
        quotes = client.get_quotes([symbol])
        if not quotes:
            return {
                "error": f"Unable to fetch quote for {symbol}",
                "status": "failed"
            }
        
        underlying_price = quotes[0].last
        
        # Select optimal expiration
        expiration_selector = ExpirationSelector(client)
        expiration, exp_metadata = await expiration_selector.get_optimal_expiration(
            symbol=symbol,
            duration=duration
        )
        
        # Analyze options chain
        optimal_strikes = await analyzer.find_optimal_strikes(
            expiration=expiration,
            underlying_price=underlying_price,
            capital_limit=capital_limit
        )
        
        if not optimal_strikes:
            return {
                "symbol": symbol,
                "status": "no_suitable_options",
                "message": f"No options found matching {purpose_type} criteria for {duration} duration",
                "current_price": underlying_price,
                "checked_expiration": expiration
            }
        
        # Generate recommendations
        recommendation_engine = StrategyRecommendationEngine()
        recommendations = recommendation_engine.generate_three_alternatives(
            analyzed_options=optimal_strikes,
            underlying_price=underlying_price,
            purpose_type=purpose_type
        )
        
        # Generate order blocks if requested
        order_blocks = {}
        if include_order_blocks:
            formatter = ProfessionalOrderFormatter()
            for profile, rec in recommendations.items():
                order_blocks[profile] = formatter.format_order_block(rec)
        
        # Export to CSV
        csv_path = await export_csp_analysis_to_csv(
            symbol=symbol,
            recommendations=recommendations,
            analyzed_options=optimal_strikes
        )
        
        # Build response
        result = {
            "symbol": symbol,
            "current_price": underlying_price,
            "analysis_timestamp": get_market_time_et(),
            "strategy_parameters": {
                "purpose_type": purpose_type,
                "duration": duration,
                "delta_range": analyzer.delta_ranges[purpose_type],
                "capital_limit": capital_limit
            },
            "selected_expiration": {
                "date": expiration,
                "days_to_expiry": exp_metadata["days_to_expiry"],
                "type": exp_metadata["option_type"]  # weekly/monthly
            },
            "recommendations": recommendations,
            "order_blocks": order_blocks if include_order_blocks else None,
            "market_context": await get_market_context(symbol, client),
            "csv_export_path": csv_path,
            "execution_notes": generate_execution_notes(recommendations, purpose_type),
            "status": "success"
        }
        
        return result
        
    except Exception as e:
        return {
            "symbol": symbol,
            "status": "error",
            "error": str(e),
            "message": "Failed to generate CSP strategy recommendations"
        }
```

#### 4.2 Supporting Functions
**File**: `src/strategy/cash_secured_put.py`

```python
async def export_csp_analysis_to_csv(
    symbol: str,
    recommendations: Dict[str, Dict[str, Any]],
    analyzed_options: List[Dict[str, Any]]
) -> str:
    """Export CSP analysis to CSV file."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"csp_{symbol}_{timestamp}.csv"
    filepath = os.path.join("./data", filename)
    
    with open(filepath, 'w', newline='') as csvfile:
        fieldnames = [
            'profile', 'symbol', 'strike', 'expiration', 'delta', 
            'premium', 'annualized_return', 'assignment_probability',
            'breakeven', 'max_profit', 'required_capital', 'recommendation'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write recommendations
        for profile, rec in recommendations.items():
            writer.writerow({
                'profile': profile,
                'symbol': rec['option_details']['symbol'],
                'strike': rec['option_details']['strike'],
                'expiration': rec['option_details']['expiration'],
                'delta': rec['option_details']['delta'],
                'premium': rec['option_details']['premium'],
                'annualized_return': rec['pnl_analysis']['annualized_return'],
                'assignment_probability': rec['risk_metrics']['assignment_probability'],
                'breakeven': rec['pnl_analysis']['breakeven_price'],
                'max_profit': rec['pnl_analysis']['max_profit'],
                'required_capital': rec['pnl_analysis']['required_capital'],
                'recommendation': rec['recommendation_reasoning']
            })
    
    return filepath

async def get_market_context(
    symbol: str,
    client: TradierClient
) -> Dict[str, Any]:
    """Get market context for better strategy decisions."""
    
    # Get historical data for volatility analysis
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    historical = client.get_historical_data(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        interval="daily"
    )
    
    # Calculate volatility metrics
    closes = [float(bar.close) for bar in historical]
    returns = [
        (closes[i] - closes[i-1]) / closes[i-1] 
        for i in range(1, len(closes))
    ]
    
    historical_volatility = np.std(returns) * np.sqrt(252)  # Annualized
    
    # Get current IV from ATM options
    current_iv = await get_atm_implied_volatility(symbol, client)
    
    # Calculate IV rank (percentile over last year)
    iv_rank = calculate_iv_rank(current_iv, symbol, client)
    
    # Identify key technical levels
    technical_levels = {
        "support_1": min(closes[-20:]),  # 20-day low
        "resistance_1": max(closes[-20:]),  # 20-day high
        "sma_20": sum(closes[-20:]) / 20,
        "sma_50": sum(closes[-50:]) / 50 if len(closes) >= 50 else None
    }
    
    return {
        "implied_volatility": current_iv,
        "historical_volatility": historical_volatility,
        "iv_rank": iv_rank,
        "iv_premium": current_iv - historical_volatility,
        "technical_levels": technical_levels,
        "volatility_regime": "high" if iv_rank > 50 else "low"
    }

def generate_execution_notes(
    recommendations: Dict[str, Dict[str, Any]],
    purpose_type: str
) -> str:
    """Generate execution notes based on recommendations."""
    
    notes = []
    
    if purpose_type == "income":
        notes.append("• Focus on premium collection - avoid assignment")
        notes.append("• Consider rolling if stock approaches strike")
        notes.append("• Monitor delta changes; close if delta exceeds -0.40")
    else:  # discount
        notes.append("• Prepared for assignment - ensure capital available")
        notes.append("• This is an entry strategy for long stock position")
        notes.append("• Consider technical support levels for strike selection")
    
    # Add volatility-specific notes
    balanced = recommendations.get("balanced", {})
    if balanced and balanced.get("risk_metrics", {}).get("implied_volatility", 0) > 0.40:
        notes.append("• High IV environment - favorable for selling premium")
        notes.append("• Consider shorter duration to capture IV crush")
    
    notes.append("• Best execution during regular market hours")
    notes.append("• Use limit orders; avoid market orders on options")
    
    return "\n".join(notes)
```

### Phase 5: Integration & Testing

#### 5.1 Server Registration
**File**: `src/mcp_server/server.py`

```python
# Add to imports
from .tools.cash_secured_put_strategy_tool import cash_secured_put_strategy_tool

# Register tool in create_server()
@mcp.tool()
async def cash_secured_sell_put_tool(
    symbol: str,
    purpose_type: str = "income",
    duration: str = "1w",
    capital_limit: Optional[float] = None,
    include_order_blocks: bool = True
) -> Dict[str, Any]:
    """
    获取现金担保卖出看跌期权策略建议。
    
    Analyzes options chains to recommend optimal cash secured put strategies
    for income generation or stock acquisition at discount.
    
    Args:
        symbol: 股票代码 (e.g., "AAPL", "TSLA", "NVDA")
        purpose_type: 策略目的 - "income" (收入) 或 "discount" (折价买入)
        duration: 时间跨度 - "1w", "2w", "1m", "3m", "6m", "1y"
        capital_limit: 最大资金限制 (可选)
        include_order_blocks: 是否生成专业订单格式
        
    Returns:
        包含三个风险级别建议的综合策略分析
    """
    return await cash_secured_put_strategy_tool(
        symbol=symbol,
        purpose_type=purpose_type,
        duration=duration,
        capital_limit=capital_limit,
        include_order_blocks=include_order_blocks
    )
```

#### 5.2 Test Suite
**File**: `tests/tools/test_cash_secured_put_tool.py`

```python
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.mcp_server.tools.cash_secured_put_strategy_tool import (
    cash_secured_put_strategy_tool
)

@pytest.mark.asyncio
async def test_csp_income_strategy():
    """Test CSP tool with income strategy parameters."""
    
    with patch('src.provider.tradier.client.TradierClient') as mock_client:
        # Setup mock responses
        mock_client.return_value.get_quotes.return_value = [
            Mock(last=150.00, symbol="AAPL")
        ]
        
        mock_client.return_value.get_option_expirations.return_value = [
            "2024-01-19", "2024-01-26", "2024-02-16"
        ]
        
        # Mock option chain with various deltas
        mock_options = [
            Mock(
                symbol="AAPL240119P145",
                strike=145.00,
                option_type="put",
                bid=1.20,
                ask=1.30,
                open_interest=500,
                volume=100,
                greeks={"delta": -0.20, "theta": -0.05, "mid_iv": 0.25}
            ),
            Mock(
                symbol="AAPL240119P140",
                strike=140.00,
                option_type="put",
                bid=0.80,
                ask=0.90,
                open_interest=800,
                volume=200,
                greeks={"delta": -0.15, "theta": -0.04, "mid_iv": 0.24}
            )
        ]
        
        mock_client.return_value.get_option_chain_enhanced.return_value = mock_options
        
        # Execute tool
        result = await cash_secured_put_strategy_tool(
            symbol="AAPL",
            purpose_type="income",
            duration="1w"
        )
        
        # Assertions
        assert result["status"] == "success"
        assert result["symbol"] == "AAPL"
        assert "recommendations" in result
        assert "conservative" in result["recommendations"]
        assert "balanced" in result["recommendations"]
        assert "aggressive" in result["recommendations"]
        
        # Verify delta ranges for income strategy
        for rec in result["recommendations"].values():
            delta = rec["option_details"]["delta"]
            assert -0.30 <= delta <= -0.10

@pytest.mark.asyncio
async def test_csp_discount_strategy():
    """Test CSP tool with discount strategy parameters."""
    
    result = await cash_secured_put_strategy_tool(
        symbol="TSLA",
        purpose_type="discount",
        duration="1m",
        capital_limit=50000
    )
    
    # Verify higher delta for discount strategy
    if result["status"] == "success":
        for rec in result["recommendations"].values():
            delta = rec["option_details"]["delta"]
            assert -0.70 <= delta <= -0.30

@pytest.mark.asyncio
async def test_csp_no_suitable_options():
    """Test handling when no suitable options are found."""
    
    with patch('src.provider.tradier.client.TradierClient') as mock_client:
        mock_client.return_value.get_option_chain_enhanced.return_value = []
        
        result = await cash_secured_put_strategy_tool(
            symbol="XYZ",
            purpose_type="income",
            duration="1w"
        )
        
        assert result["status"] == "no_suitable_options"
        assert "message" in result

@pytest.mark.asyncio
async def test_duration_expiration_mapping():
    """Test correct expiration selection for different durations."""
    
    test_cases = [
        ("1w", 5, 9),
        ("2w", 10, 18),
        ("1m", 25, 35),
        ("3m", 80, 100),
        ("6m", 170, 190),
        ("1y", 350, 380)
    ]
    
    for duration, min_days, max_days in test_cases:
        # Test expiration selection logic
        selector = ExpirationSelector(Mock())
        result = await selector.get_optimal_expiration("AAPL", duration)
        
        # Verify days to expiry is within expected range
        assert min_days <= result[1]["days_to_expiry"] <= max_days
```

## Risk Management & Edge Cases

### Risk Considerations

1. **Assignment Risk Management**
   - Monitor delta changes in real-time
   - Alert when delta exceeds threshold
   - Provide rolling recommendations

2. **Liquidity Risk**
   - Filter options with minimum open interest (100 contracts)
   - Check bid-ask spreads (<10% of mid-price)
   - Prefer monthly expirations for better liquidity

3. **Capital Management**
   - Validate sufficient buying power
   - Calculate margin requirements
   - Track aggregate exposure across positions

### Edge Cases

1. **No Suitable Options**
   - Return clear message with reasons
   - Suggest alternative expirations or strikes
   - Provide market context explanation

2. **Extreme Market Conditions**
   - Detect high volatility regimes (VIX > 30)
   - Adjust recommendations accordingly
   - Add risk warnings to output

3. **API Failures**
   - Implement retry logic with exponential backoff
   - Cache recent data for resilience
   - Graceful degradation with partial data

## Success Metrics

### Functional Requirements
- [ ] Tool processes requests in <2 seconds
- [ ] Provides 3 distinct recommendations per request
- [ ] Correctly filters options by delta range
- [ ] Generates valid CSV exports
- [ ] Produces professional order blocks

### Quality Metrics
- [ ] Delta accuracy within ±0.02 of target range
- [ ] Annualized return calculations accurate to ±1%
- [ ] P&L scenarios cover all market conditions
- [ ] Recommendations align with stated purpose type

### User Experience
- [ ] Clear, actionable recommendations
- [ ] Professional formatting for institutional use
- [ ] Comprehensive risk disclosures
- [ ] Educational execution notes

## Testing Strategy

### Unit Tests
- Delta calculation accuracy
- Strike selection algorithm
- P&L scenario modeling
- Duration to expiration mapping

### Integration Tests
- Tradier API data flow
- MCP server integration
- CSV export functionality
- Error handling pathways

### End-to-End Tests
- Complete strategy generation flow
- Multiple symbols and durations
- Edge case handling
- Performance benchmarks

## Deployment Checklist

1. **Code Implementation**
   - [ ] Implement core CSP analyzer
   - [ ] Create strategy recommendation engine
   - [ ] Build professional formatter
   - [ ] Integrate MCP tool

2. **Testing**
   - [ ] Unit tests passing (>90% coverage)
   - [ ] Integration tests complete
   - [ ] Manual testing with real data
   - [ ] Performance benchmarks met

3. **Documentation**
   - [ ] Update README with new tool
   - [ ] Add usage examples
   - [ ] Document API parameters
   - [ ] Create troubleshooting guide

4. **Deployment**
   - [ ] Environment variables configured
   - [ ] Dependencies updated in pyproject.toml
   - [ ] Server registration complete
   - [ ] Claude Code integration tested

## Implementation Timeline

### Week 1: Core Infrastructure
- Days 1-2: Extend Tradier client, create strategy module structure
- Days 3-4: Implement CSP analyzer and delta-based selection
- Day 5: Build expiration selector and duration mapping

### Week 2: Strategy Logic & Recommendations
- Days 6-7: Develop recommendation engine with three profiles
- Days 8-9: Create professional order formatter
- Day 10: Implement P&L analysis and risk metrics

### Week 3: Integration & Testing
- Days 11-12: MCP tool implementation and server registration
- Days 13-14: Comprehensive testing suite
- Day 15: Documentation, deployment, and final validation

## Conclusion

The Cash Secured Put Strategy MCP Server Tool represents a sophisticated addition to the TradingAgentMCP ecosystem, providing institutional-grade options analysis capabilities through an intuitive interface. By leveraging real-time market data, advanced Greeks calculations, and intelligent strategy selection algorithms, this tool empowers traders to implement CSP strategies with confidence and precision.

The modular architecture ensures maintainability and extensibility, while the comprehensive testing strategy guarantees reliability in production environments. Professional order formatting and detailed P&L analysis meet the requirements of institutional trading desks, making this tool suitable for both retail and professional traders.

This implementation follows best practices established in the existing codebase while introducing innovative features that set new standards for options strategy automation in the MCP ecosystem.