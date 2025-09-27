# PRD v7 - Covered Call Strategy MCP Server Tool Implementation Plan

## Executive Summary

This document outlines the comprehensive implementation plan for the Covered Call Strategy MCP Server Tool, an advanced options trading analysis system designed to automate the selection and recommendation of covered call options. The tool integrates seamlessly with the existing TradingAgentMCP infrastructure, leveraging real-time Tradier API data to provide institutional-grade covered call strategy recommendations for income generation and strategic position management.

## Problem Statement & Objectives

### Core Problem
Options traders and stock investors need sophisticated tools to implement covered call strategies effectively, balancing income generation with upside participation. Current manual analysis is time-consuming and prone to missing optimal opportunities. The tool must analyze multiple factors including:

- Delta/probability of assignment across different strikes
- Premium income vs. opportunity cost of capped upside
- Duration optimization based on theta decay and stock appreciation
- Market volatility and technical resistance levels
- Risk-adjusted returns and exit strategies

### Strategic Objectives

1. **Automated Strategy Construction**: Develop an MCP tool that automatically analyzes options chains to identify optimal covered call opportunities based on user-defined criteria
2. **Risk-Based Classification**: Implement dual-purpose strategy types:
   - **Income Strategy** (10-30% delta): Focus on premium collection while maintaining most upside potential
   - **Exit Strategy** (30-70% delta): Accept higher assignment probability to exit position at target price + premium
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
│   Covered Call Strategy Tool                │
├─────────────────────────────────────────────┤
│ Core Components:                            │
│ • covered_call_strategy_tool()             │
│ • analyze_cc_opportunities()               │
│ • calculate_optimal_strikes()              │
│ • generate_strategy_recommendations()      │
├─────────────────────────────────────────────┤
│ Analysis Engine:                            │
│ • Delta-based strike selection             │
│ • Premium yield optimization               │
│ • Upside capture analysis                  │
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
├── strategy/                                  # EXTENDED: Strategy module
│   ├── __init__.py
│   ├── covered_call.py                       # NEW: Core covered call strategy logic
│   ├── strategy_analyzer.py                 # EXTENDED: Strategy analysis engine
│   └── risk_calculator.py                   # EXTENDED: Risk metrics calculation
├── option/                                   # Existing module (reused)
│   ├── option_expiration_selector.py        # REUSED: Duration-based expiry selection
│   └── greeks_enhanced.py                   # REUSED: Enhanced Greeks calculations
├── mcp_server/
│   └── tools/
│       └── covered_call_strategy_tool.py    # NEW: MCP tool implementation
└── provider/tradier/
    └── client.py                            # EXTENDED: Add CC-specific methods
```

## Detailed Implementation Plan

### Phase 1: Core Infrastructure & Data Layer

#### 1.1 Extend Tradier Client
**File**: `src/provider/tradier/client.py`

```python
def get_call_options_by_delta_range(
    self,
    symbol: str,
    expiration: str,
    delta_min: float,
    delta_max: float
) -> List[OptionContract]:
    """
    Get call options within specified delta range.
    Optimized for covered call strategy selection.
    """

def get_stock_position_info(
    self,
    symbol: str
) -> Dict[str, Any]:
    """
    Get current stock position information for covered call validation.
    Returns shares owned, avg cost, market value.
    """

def calculate_resistance_levels(
    self,
    symbol: str,
    lookback_days: int = 60
) -> Dict[str, float]:
    """
    Calculate technical resistance levels for strike selection.
    """
```

#### 1.2 Create Covered Call Strategy Engine
**File**: `src/strategy/covered_call.py`

```python
class CoveredCallAnalyzer:
    """Core analyzer for covered call opportunities."""
    
    def __init__(
        self,
        symbol: str,
        purpose_type: str,  # "income" or "exit"
        duration: str,
        shares_owned: int,
        avg_cost: Optional[float] = None,
        tradier_client: TradierClient = None
    ):
        self.symbol = symbol
        self.purpose_type = purpose_type
        self.duration = duration
        self.shares_owned = shares_owned
        self.avg_cost = avg_cost
        self.client = tradier_client or TradierClient()
        
        # Delta ranges based on purpose (positive for calls)
        self.delta_ranges = {
            "income": {"min": 0.10, "max": 0.30},    # Lower delta = less likely assignment
            "exit": {"min": 0.30, "max": 0.70}       # Higher delta = more likely assignment
        }
    
    async def find_optimal_strikes(
        self,
        expiration: str,
        underlying_price: float,
        min_premium: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Find optimal call strike prices based on delta requirements.
        Returns sorted list of opportunities.
        """
        
    async def calculate_strategy_metrics(
        self,
        option_contract: OptionContract,
        underlying_price: float
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive metrics for a covered call position:
        - Annualized return (premium + any appreciation to strike)
        - Upside capture to strike
        - Downside protection (premium only)
        - Opportunity cost analysis
        - Expected value calculations
        """
        
    def classify_risk_profile(
        self,
        options: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Classify options into conservative, balanced, aggressive.
        Based on delta, upside capture, and premium yield.
        """
        
    def validate_position_requirements(self) -> Dict[str, Any]:
        """
        Validate that user has sufficient shares for covered call strategy.
        Returns position status and recommendations.
        """
```

### Phase 2: Strategy Selection Logic

#### 2.1 Expiration Date Selection (Reuse Existing)
**File**: `src/option/option_expiration_selector.py`

The existing `ExpirationSelector` class can be reused with the same duration mappings:

```python
DURATION_MAPPINGS = {
    "1w": {"min_days": 5, "max_days": 9, "preferred": "weekly"},
    "2w": {"min_days": 10, "max_days": 18, "preferred": "weekly"},
    "1m": {"min_days": 25, "max_days": 35, "preferred": "monthly"},
    "3m": {"min_days": 80, "max_days": 100, "preferred": "monthly"},
    "6m": {"min_days": 170, "max_days": 190, "preferred": "monthly"},
    "1y": {"min_days": 350, "max_days": 380, "preferred": "leaps"}
}
```

#### 2.2 Delta-Based Strike Selection Algorithm
**File**: `src/strategy/strategy_analyzer.py` (Extended)

```python
class DeltaBasedCallStrikeSelector:
    """Advanced call strike selection using delta and technical analysis."""
    
    async def analyze_call_option_chain(
        self,
        option_chain: List[OptionContract],
        target_delta_range: Tuple[float, float],
        underlying_price: float,
        resistance_levels: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Implements covered call specific analysis:
        1. Filter by delta range (positive for calls)
        2. Calculate premium yield vs. upside opportunity cost
        3. Assess technical resistance proximity
        4. Score based on risk-reward profile
        5. Rank opportunities
        """
        
        analyzed_options = []
        
        for option in option_chain:
            if not self._is_within_delta_range(option, target_delta_range):
                continue
                
            # Only analyze call options above current price
            if option.strike <= underlying_price:
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
                "upside_capture": ((option.strike - underlying_price) / underlying_price) * 100,
                "total_return_if_called": self._calculate_total_return_if_called(
                    option, underlying_price
                ),
                "annualized_return": self._calculate_annualized_return(option, underlying_price),
                "assignment_probability": option.greeks.get("delta", 0) * 100,
                "liquidity_score": self._calculate_liquidity_score(option),
                "technical_score": self._calculate_technical_score(
                    option.strike, resistance_levels
                ),
                "opportunity_cost": self._calculate_opportunity_cost(option, underlying_price)
            }
            
            analyzed_options.append(metrics)
        
        # Sort by composite score (premium yield + upside capture - opportunity cost)
        return sorted(
            analyzed_options,
            key=lambda x: (
                x["total_return_if_called"] * x["liquidity_score"] * x["technical_score"]
            ),
            reverse=True
        )
        
    def _calculate_total_return_if_called(
        self,
        option: OptionContract,
        underlying_price: float
    ) -> float:
        """Calculate total return if option is assigned (premium + appreciation)."""
        premium_return = (option.premium / underlying_price) * 100
        appreciation_return = ((option.strike - underlying_price) / underlying_price) * 100
        return premium_return + appreciation_return
        
    def _calculate_technical_score(
        self,
        strike: float,
        resistance_levels: Dict[str, float]
    ) -> float:
        """Score strike based on proximity to technical resistance."""
        scores = []
        for level_name, level_price in resistance_levels.items():
            if level_price and strike <= level_price * 1.02:  # Within 2% of resistance
                scores.append(0.9)  # High score for strikes near resistance
            elif level_price and strike <= level_price * 1.05:  # Within 5% of resistance
                scores.append(0.7)
            else:
                scores.append(0.5)  # Lower score for strikes far from resistance
        
        return max(scores) if scores else 0.5
```

### Phase 3: Recommendation Engine

#### 3.1 Strategy Recommendation Generator
**File**: `src/strategy/covered_call.py`

```python
class CoveredCallRecommendationEngine:
    """Generate professional covered call strategy recommendations."""
    
    def generate_three_alternatives(
        self,
        analyzed_options: List[Dict[str, Any]],
        underlying_price: float,
        purpose_type: str,
        shares_owned: int
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate conservative, balanced, and aggressive alternatives.
        """
        
        recommendations = {}
        
        # Conservative: Lower delta, more upside preservation
        conservative = self._select_conservative_option(analyzed_options, purpose_type)
        
        # Balanced: Optimal premium-to-upside ratio
        balanced = self._select_balanced_option(analyzed_options, purpose_type)
        
        # Aggressive: Higher delta, maximum premium, higher assignment risk
        aggressive = self._select_aggressive_option(analyzed_options, purpose_type)
        
        for name, option in [
            ("conservative", conservative),
            ("balanced", balanced),
            ("aggressive", aggressive)
        ]:
            if option:
                recommendations[name] = self._build_recommendation(
                    option, underlying_price, shares_owned, name
                )
        
        return recommendations
    
    def _build_recommendation(
        self,
        option: Dict[str, Any],
        underlying_price: float,
        shares_owned: int,
        profile: str
    ) -> Dict[str, Any]:
        """Build comprehensive recommendation with P&L analysis."""
        
        strike = option["strike"]
        premium = option["premium"]
        contracts = shares_owned // 100  # Number of contracts can be written
        
        return {
            "profile": profile,
            "option_details": option,
            "position_info": {
                "shares_owned": shares_owned,
                "contracts_to_write": contracts,
                "shares_covered": contracts * 100
            },
            "pnl_analysis": {
                "premium_income": premium * contracts * 100,
                "max_profit_scenario": f"Stock called away at ${strike}",
                "max_profit": (premium + max(0, strike - underlying_price)) * contracts * 100,
                "breakeven_price": underlying_price - premium,
                "downside_protection": premium * 100 / underlying_price,  # Percentage
                "upside_capture": option["upside_capture"],
                "total_return_if_called": option["total_return_if_called"],
                "annualized_return": option["annualized_return"],
                "opportunity_cost": option["opportunity_cost"]
            },
            "risk_metrics": {
                "assignment_probability": option["assignment_probability"],
                "delta": option["delta"],
                "theta_per_day": option["theta"] * contracts * 100,
                "implied_volatility": option["implied_volatility"],
                "liquidity_score": option["liquidity_score"],
                "upside_at_risk": (underlying_price * (1 + option["upside_capture"]/100) - strike) * shares_owned if option["upside_capture"] > 0 else 0
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
        """Generate detailed reasoning for the recommendation."""
        
        if purpose_type == "income":
            if profile == "conservative":
                return f"Low {option['delta']:.2f} delta provides steady income with minimal assignment risk. Retains {option['upside_capture']:.1f}% upside potential to strike."
            elif profile == "balanced":
                return f"Balanced {option['delta']:.2f} delta offers good premium ({option['premium']:.2f}) while capturing {option['upside_capture']:.1f}% upside if called."
            else:  # aggressive
                return f"Higher {option['delta']:.2f} delta maximizes premium income but caps upside at {option['upside_capture']:.1f}% above current price."
        else:  # exit strategy
            if profile == "conservative":
                return f"Conservative exit at {option['upside_capture']:.1f}% above current price with {option['premium']:.2f} premium buffer."
            elif profile == "balanced":
                return f"Balanced exit strategy targeting {option['upside_capture']:.1f}% appreciation plus {option['premium']:.2f} premium income."
            else:  # aggressive
                return f"Aggressive exit with {option['assignment_probability']:.1f}% assignment probability for maximum premium collection."
```

#### 3.2 Professional Order Formatting
**File**: `src/strategy/covered_call.py`

```python
class CoveredCallOrderFormatter:
    """Format covered call orders following institutional trading conventions."""
    
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
        position = recommendation["position_info"]
        
        order_block = f"""
╔══════════════════════════════════════════════════════════╗
║                    COVERED CALL ORDER                    ║
╠══════════════════════════════════════════════════════════╣
║ Symbol:        {option['symbol']:43} ║
║ Action:        SELL TO OPEN                              ║
║ Quantity:      {position['contracts_to_write']} CONTRACT(S) ({position['shares_covered']} SHARES COVERED) ║
║ Order Type:    LIMIT                                     ║
║ Strike:        ${option['strike']:<6.2f}                             ║
║ Expiration:    {self._format_expiration(option['expiration']):43} ║
║ Limit Price:   ${option['premium']:<6.2f} (MID)                      ║
╠══════════════════════════════════════════════════════════╣
║                      P&L ANALYSIS                        ║
╠══════════════════════════════════════════════════════════╣
║ Premium Income: ${pnl['premium_income']:<8.2f}                         ║
║ Max Profit:    ${pnl['max_profit']:<8.2f} (if called away)             ║
║ Upside Capture: {pnl['upside_capture']:<6.2f}% to strike                    ║
║ Downside Prot: {pnl['downside_protection']:<6.2f}% (premium only)            ║
║ Annual Return: {pnl['annualized_return']:<6.2f}%                           ║
╠══════════════════════════════════════════════════════════╣
║                    RISK METRICS                          ║
╠══════════════════════════════════════════════════════════╣
║ Delta:         {option['delta']:<8.4f}                              ║
║ Assign Prob:   {option['assignment_probability']:<6.1f}%                            ║
║ Impl Vol:      {option['implied_volatility']:<6.2%}                        ║
║ Theta/Day:     ${option['theta'] * position['contracts_to_write'] * 100:<7.2f}                           ║
║ Upside at Risk: ${recommendation['risk_metrics']['upside_at_risk']:<7.2f}                          ║
╚══════════════════════════════════════════════════════════╝

EXECUTION NOTES:
• Ensure {position['shares_owned']} shares are held long before selling calls
• Place limit order at mid-price or better
• Monitor for fills during high liquidity periods (9:30-10:30 AM, 3:00-4:00 PM ET)
• Consider rolling up and out if stock approaches strike with time remaining
• Set GTC (Good Till Cancelled) with daily review
• ASSIGNMENT RISK: Be prepared to sell shares at ${option['strike']:.2f} if assigned
"""
        return order_block
```

### Phase 4: MCP Tool Implementation

#### 4.1 Main MCP Tool Function
**File**: `src/mcp_server/tools/covered_call_strategy_tool.py`

```python
from typing import Dict, Any, Optional
from ..config.settings import settings
from ...provider.tradier.client import TradierClient
from ...strategy.covered_call import (
    CoveredCallAnalyzer,
    CoveredCallRecommendationEngine,
    CoveredCallOrderFormatter
)
from ...option.option_expiration_selector import ExpirationSelector

async def covered_call_strategy_tool(
    symbol: str,
    purpose_type: str = "income",
    duration: str = "1w",
    shares_owned: int = 100,
    avg_cost: Optional[float] = None,
    min_premium: Optional[float] = None,
    include_order_blocks: bool = True
) -> Dict[str, Any]:
    """
    Covered Call Strategy MCP Tool
    
    Analyzes options chains to recommend optimal covered call strategies
    for income generation or strategic position exits.
    
    Args:
        symbol: Stock ticker symbol (e.g., "AAPL", "TSLA")
        purpose_type: Strategy purpose - "income" (10-30% delta) or "exit" (30-70% delta)
        duration: Time horizon - "1w", "2w", "1m", "3m", "6m", "1y"
        shares_owned: Number of shares owned (must be >= 100)
        avg_cost: Average cost basis per share (optional, for tax analysis)
        min_premium: Minimum premium threshold (optional)
        include_order_blocks: Generate professional order formatting
    
    Returns:
        Comprehensive strategy analysis with three alternatives:
        {
            "symbol": "AAPL",
            "current_price": 150.25,
            "analysis_timestamp": "2024-01-15 14:30:00 ET",
            "strategy_parameters": {...},
            "position_validation": {
                "shares_owned": 500,
                "contracts_available": 5,
                "position_value": 75125.00
            },
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
                "resistance_levels": {...}
            },
            "csv_export_path": "./data/cc_AAPL_20240115_143000.csv",
            "execution_notes": "..."
        }
    """
    
    try:
        # Validate position requirements
        if shares_owned < 100:
            return {
                "error": "Insufficient shares for covered call strategy. Minimum 100 shares required.",
                "status": "failed",
                "shares_owned": shares_owned,
                "shares_needed": 100
            }
        
        # Initialize components
        client = TradierClient()
        analyzer = CoveredCallAnalyzer(
            symbol=symbol,
            purpose_type=purpose_type,
            duration=duration,
            shares_owned=shares_owned,
            avg_cost=avg_cost,
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
        
        # Validate position value
        position_value = underlying_price * shares_owned
        contracts_available = shares_owned // 100
        
        # Select optimal expiration
        expiration_selector = ExpirationSelector(client)
        expiration, exp_metadata = await expiration_selector.get_optimal_expiration(
            symbol=symbol,
            duration=duration
        )
        
        # Get resistance levels for technical analysis
        resistance_levels = client.calculate_resistance_levels(symbol)
        
        # Analyze options chain
        optimal_strikes = await analyzer.find_optimal_strikes(
            expiration=expiration,
            underlying_price=underlying_price,
            min_premium=min_premium
        )
        
        if not optimal_strikes:
            return {
                "symbol": symbol,
                "status": "no_suitable_options",
                "message": f"No call options found matching {purpose_type} criteria for {duration} duration",
                "current_price": underlying_price,
                "checked_expiration": expiration,
                "shares_owned": shares_owned
            }
        
        # Generate recommendations
        recommendation_engine = CoveredCallRecommendationEngine()
        recommendations = recommendation_engine.generate_three_alternatives(
            analyzed_options=optimal_strikes,
            underlying_price=underlying_price,
            purpose_type=purpose_type,
            shares_owned=shares_owned
        )
        
        # Generate order blocks if requested
        order_blocks = {}
        if include_order_blocks:
            formatter = CoveredCallOrderFormatter()
            for profile, rec in recommendations.items():
                order_blocks[profile] = formatter.format_order_block(rec)
        
        # Export to CSV
        csv_path = await export_cc_analysis_to_csv(
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
                "min_premium": min_premium
            },
            "position_validation": {
                "shares_owned": shares_owned,
                "contracts_available": contracts_available,
                "position_value": position_value,
                "avg_cost": avg_cost
            },
            "selected_expiration": {
                "date": expiration,
                "days_to_expiry": exp_metadata["days_to_expiry"],
                "type": exp_metadata["option_type"]  # weekly/monthly
            },
            "recommendations": recommendations,
            "order_blocks": order_blocks if include_order_blocks else None,
            "market_context": await get_cc_market_context(symbol, client, resistance_levels),
            "csv_export_path": csv_path,
            "execution_notes": generate_cc_execution_notes(recommendations, purpose_type, shares_owned),
            "status": "success"
        }
        
        return result
        
    except Exception as e:
        return {
            "symbol": symbol,
            "status": "error",
            "error": str(e),
            "message": "Failed to generate covered call strategy recommendations",
            "shares_owned": shares_owned
        }
```

#### 4.2 Supporting Functions
**File**: `src/strategy/covered_call.py`

```python
async def export_cc_analysis_to_csv(
    symbol: str,
    recommendations: Dict[str, Dict[str, Any]],
    analyzed_options: List[Dict[str, Any]]
) -> str:
    """Export covered call analysis to CSV file."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"cc_{symbol}_{timestamp}.csv"
    filepath = os.path.join("./data", filename)
    
    with open(filepath, 'w', newline='') as csvfile:
        fieldnames = [
            'profile', 'symbol', 'strike', 'expiration', 'delta', 
            'premium', 'upside_capture', 'total_return_if_called',
            'assignment_probability', 'downside_protection', 'contracts',
            'premium_income', 'recommendation'
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
    """Get market context for better covered call decisions."""
    
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
    
    # Calculate momentum indicators
    current_price = closes[-1]
    sma_20 = sum(closes[-20:]) / 20
    sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else None
    
    momentum_score = "bullish" if current_price > sma_20 else "bearish"
    if sma_50 and current_price > sma_50:
        momentum_score = "strong_bullish"
    elif sma_50 and current_price < sma_50:
        momentum_score = "strong_bearish"
    
    return {
        "implied_volatility": current_iv,
        "historical_volatility": historical_volatility,
        "iv_rank": iv_rank,
        "iv_premium": current_iv - historical_volatility,
        "resistance_levels": resistance_levels,
        "momentum_score": momentum_score,
        "technical_levels": {
            "sma_20": sma_20,
            "sma_50": sma_50,
            "support_1": min(closes[-20:]),  # 20-day low
            "resistance_1": max(closes[-20:])  # 20-day high
        },
        "volatility_regime": "high" if iv_rank > 50 else "low"
    }

def generate_cc_execution_notes(
    recommendations: Dict[str, Dict[str, Any]],
    purpose_type: str,
    shares_owned: int
) -> str:
    """Generate execution notes based on recommendations."""
    
    notes = []
    contracts_available = shares_owned // 100
    
    notes.append(f"• Position validation: {shares_owned} shares owned, {contracts_available} contracts available")
    
    if purpose_type == "income":
        notes.append("• Income strategy - aim to keep shares and collect premium")
        notes.append("• Consider rolling calls up and out if stock approaches strike")
        notes.append("• Monitor delta; consider closing if delta exceeds 0.50")
        notes.append("• Tax consideration: Assignment creates taxable event")
    else:  # exit strategy
        notes.append("• Exit strategy - prepared for assignment at target price")
        notes.append("• This caps upside but provides premium income buffer")
        notes.append("• Consider stock fundamentals before accepting assignment")
        notes.append("• Tax consideration: Calculate gain/loss vs cost basis")
    
    # Add volatility-specific notes
    balanced = recommendations.get("balanced", {})
    if balanced and balanced.get("risk_metrics", {}).get("implied_volatility", 0) > 0.40:
        notes.append("• High IV environment - favorable for selling premium")
        notes.append("• Consider shorter duration to capture IV crush")
    
    # Position-specific notes
    if contracts_available > 5:
        notes.append("• Large position - consider laddering across multiple expirations")
        notes.append("• Consider writing partial position to maintain upside exposure")
    
    notes.append("• Execute during regular market hours for best liquidity")
    notes.append("• Use limit orders; avoid market orders on options")
    notes.append("• Monitor earnings announcements that may affect volatility")
    
    return "\n".join(notes)
```

### Phase 5: Integration & Testing

#### 5.1 Server Registration
**File**: `src/mcp_server/server.py`

```python
# Add to imports
from .tools.covered_call_strategy_tool import covered_call_strategy_tool

# Add new tool registration
@mcp.tool()
async def covered_call_strategy_tool_mcp(
    symbol: str,
    purpose_type: str = "income",
    duration: str = "1w", 
    shares_owned: int = 100,
    avg_cost: float = None,
    min_premium: float = None,
    include_order_blocks: bool = True
) -> Dict[str, Any]:
    """
    Covered Call Strategy Analysis Tool
    
    Analyzes options chains to recommend optimal covered call strategies
    for income generation and strategic position management.
    
    Args:
        symbol: Stock ticker symbol (e.g., "AAPL", "TSLA", "NVDA")
        purpose_type: Strategy purpose - "income" (收入导向) or "exit" (减仓)
        duration: Time horizon - "1w", "2w", "1m", "3m", "6m", "1y"
        shares_owned: Number of shares owned (minimum 100)
        avg_cost: Average cost basis per share (optional)
        min_premium: Minimum premium threshold (optional)
        include_order_blocks: Generate professional order blocks
        
    Returns:
        Comprehensive covered call analysis with three risk-adjusted alternatives
    """
    return await covered_call_strategy_tool(
        symbol=symbol,
        purpose_type=purpose_type,
        duration=duration,
        shares_owned=shares_owned,
        avg_cost=avg_cost,
        min_premium=min_premium,
        include_order_blocks=include_order_blocks
    )
```

#### 5.2 Testing Strategy
**File**: `tests/tools/test_covered_call_strategy_tool.py`

```python
import pytest
from unittest.mock import Mock, patch
from src.mcp_server.tools.covered_call_strategy_tool import covered_call_strategy_tool

@pytest.mark.asyncio
class TestCoveredCallStrategyTool:
    
    async def test_insufficient_shares_validation(self):
        """Test validation when user has insufficient shares."""
        result = await covered_call_strategy_tool(
            symbol="AAPL",
            shares_owned=50  # Less than 100
        )
        
        assert result["status"] == "failed"
        assert "Insufficient shares" in result["error"]
        assert result["shares_needed"] == 100
    
    async def test_successful_income_strategy(self):
        """Test successful income strategy execution."""
        with patch('src.strategy.covered_call.TradierClient') as mock_client:
            # Mock setup for successful analysis
            mock_client.return_value.get_quotes.return_value = [
                Mock(last=150.0)
            ]
            
            result = await covered_call_strategy_tool(
                symbol="AAPL",
                purpose_type="income",
                shares_owned=500
            )
            
            assert result["status"] == "success"
            assert result["position_validation"]["contracts_available"] == 5
```

## Testing & Validation Strategy

### Unit Testing
- **Strategy Logic**: Test delta filtering, P&L calculations, and recommendation generation
- **Risk Calculations**: Validate Greeks, assignment probabilities, and opportunity cost analysis
- **Position Validation**: Test share requirements and contract calculations
- **Technical Analysis**: Test resistance level calculations and strike selection

### Integration Testing
- **API Integration**: Test Tradier API calls for call options chains
- **MCP Integration**: Test tool registration and parameter handling
- **CSV Export**: Validate data export format and completeness
- **Error Handling**: Test various failure scenarios

### Performance Testing
- **Response Time**: Tool should respond within 3-5 seconds for typical requests
- **Memory Usage**: Efficient handling of large option chains
- **API Rate Limits**: Respect Tradier API limits

## Success Criteria

### Functional Requirements
1. ✅ **Strategy Analysis**: Generate three risk-adjusted covered call recommendations
2. ✅ **Position Integration**: Validate share ownership and calculate optimal contract quantity
3. ✅ **Professional Output**: JP Morgan-style order blocks and comprehensive analysis
4. ✅ **Risk Management**: Accurate assignment probability and opportunity cost analysis
5. ✅ **Data Export**: CSV export for further analysis

### Technical Requirements
1. ✅ **MCP Integration**: Seamless integration with existing server infrastructure
2. ✅ **Performance**: Sub-5 second response times
3. ✅ **Error Handling**: Graceful handling of edge cases and API failures
4. ✅ **Code Quality**: >90% test coverage and type safety
5. ✅ **Documentation**: Comprehensive inline documentation and examples

### Business Requirements
1. ✅ **User Experience**: Intuitive parameter interface and clear recommendations
2. ✅ **Risk Transparency**: Clear disclosure of risks and opportunity costs
3. ✅ **Professional Standards**: Institutional-quality analysis and formatting
4. ✅ **Flexibility**: Support for both income and exit strategies
5. ✅ **Scalability**: Handle large positions (1000+ shares) efficiently

## Risk Assessment & Mitigation

### Technical Risks
- **API Dependency**: Mitigate with comprehensive error handling and fallback logic
- **Data Quality**: Validate option chain data and handle missing Greeks
- **Performance**: Optimize algorithms for large option chains

### Financial Risks  
- **Assignment Risk**: Clearly communicate assignment probabilities and implications
- **Opportunity Cost**: Transparently show upside potential being sacrificed
- **Tax Implications**: Provide warnings about taxable events upon assignment

### User Experience Risks
- **Complexity**: Provide clear explanations and progressive disclosure
- **Misuse**: Include comprehensive warnings and position validation
- **Over-reliance**: Emphasize tool is for analysis, not investment advice

## Implementation Timeline

### Week 1: Foundation
- [ ] Extend Tradier client with call option methods
- [ ] Create CoveredCallAnalyzer core class
- [ ] Implement basic delta-based filtering

### Week 2: Strategy Engine
- [ ] Build recommendation engine with three-tier system
- [ ] Implement P&L and risk calculations
- [ ] Add technical analysis integration

### Week 3: MCP Integration
- [ ] Create MCP tool interface
- [ ] Add professional order formatting
- [ ] Implement CSV export functionality

### Week 4: Testing & Polish
- [ ] Comprehensive testing suite
- [ ] Performance optimization
- [ ] Documentation and examples

## Future Enhancements

### Advanced Features
1. **Multi-Strike Strategies**: Ladder multiple calls across different strikes
2. **Rolling Analysis**: Automated roll-up and roll-out recommendations
3. **Tax Optimization**: Integration with cost basis and tax-loss harvesting
4. **Earnings Integration**: Adjust strategies around earnings announcements
5. **Portfolio Integration**: Multi-symbol covered call optimization

### Technical Improvements
1. **Machine Learning**: Predictive modeling for optimal strike selection
2. **Real-time Monitoring**: Live position tracking and adjustment alerts
3. **Backtesting**: Historical performance analysis of strategies
4. **Risk Budgeting**: Portfolio-level risk allocation across positions
5. **Social Features**: Strategy sharing and community insights

---

This comprehensive implementation plan provides the framework for building a professional-grade covered call strategy MCP tool that integrates seamlessly with the existing TradingAgentMCP infrastructure while providing institutional-quality analysis and recommendations.