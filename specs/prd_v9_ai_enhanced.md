# PRD v9 AI Enhanced: Income Generation CSP Engine MCP Server Prompt

## Executive Summary

Create a specialized MCP Server Prompt for the TradingAgent MCP that focuses exclusively on income generation through Cash-Secured Put (CSP) strategies. This prompt will leverage the existing `cash_secured_put_strategy_tool_mcp` to generate high-yield, low-assignment-risk options strategies optimized for premium collection rather than stock acquisition.

## Product Overview

### Core Value Proposition

**Primary Goal**: Generate high annualized returns (≥50%) through systematic Cash-Secured Put premium collection while minimizing stock assignment risk.

**Target Users**: 
- Options traders focused on income generation
- Investors seeking consistent premium collection
- Risk-averse traders who want to avoid stock ownership
- Users seeking quick-turnover options strategies

### Key Differentiators

1. **Income-First Approach**: Exclusively targets premium collection over stock acquisition
2. **High-Yield Focus**: Targets ≥50% annualized returns through systematic analysis
3. **Assignment Avoidance**: Optimizes for low Delta (0.10-0.30) to minimize assignment risk
4. **Quick Turnover**: Focuses on 7-28 day strategies for rapid capital cycling
5. **MCP Integration**: Seamlessly integrates with existing TradingAgent MCP tools

## Functional Requirements

### FR1: Prompt Function Design

**Function Signature:**
```python
async def income_generation_csp_engine(
    tickers: list,
    cash_usd: float,
    min_days: int = 7,
    max_days: int = 28,
    target_apy_pct: float = 50,
    min_winrate_pct: float = 70,
    confidence_pct: float = 90,
) -> str:
```

**Parameters:**
- `tickers`: List of target symbols (default: ["SPY", "QQQ", "AAPL", "MSFT", "NVDA"])
- `cash_usd`: Available capital for strategies
- `min_days`: Minimum days to expiration (default: 7)
- `max_days`: Maximum days to expiration (default: 28)
- `target_apy_pct`: Target annualized percentage yield (default: 50%)
- `min_winrate_pct`: Minimum target win rate (default: 70%)
- `confidence_pct`: Statistical confidence level (default: 90%)

### FR2: Prompt Output Structure

The prompt must generate a comprehensive execution plan that includes:

1. **Market Time Validation**: Mandatory time baseline verification
2. **Symbol Analysis Pipeline**: Asset info, historical data, technical indicators
3. **Options Chain Analysis**: Focus on OTM puts with target Delta ranges
4. **Strategy Screening**: Income-optimized CSP selection criteria
5. **Risk Assessment**: Assignment probability and portfolio impact analysis
6. **Execution Guidance**: Professional order formatting and management rules

### FR3: Integration with Existing MCP Tools

**Primary Tool Integration:**
- `cash_secured_put_strategy_tool_mcp` with `purpose_type="income"`
- `get_market_time_tool` for time validation
- `stock_info_tool` for underlying analysis
- `stock_history_tool` for technical context
- `options_chain_tool_mcp` for comprehensive options data

**Tool Call Sequence:**
1. Market time validation
2. Multi-symbol asset analysis (parallel execution)
3. Income-focused CSP strategy generation
4. Risk analysis and position sizing
5. Professional order block generation

### FR4: Selection and Filtering Criteria

**Primary Screening (Income Focus):**
- Delta Range: 0.10 ≤ |Delta| ≤ 0.30 (prioritize 0.15-0.25)
- Liquidity: Bid-Ask spread ≤ 10% of premium, OI ≥ 500, Volume ≥ 50
- IV Environment: IV Rank ≥ 30th percentile
- Technical Support: Strike price 5-15% below key support levels
- Time to Expiration: 7-28 days (weekly options preferred)

**Secondary Optimization:**
- Annualized Return Priority: Target ≥50% APY
- Win Rate Estimation: Historical + Delta-based probability ≥70%
- Risk-Adjusted Returns: Sharpe ratio and Kelly criterion optimization
- Liquidity Scoring: Premium market depth and execution feasibility

## Technical Specifications

### TS1: Prompt Architecture

**File Location:** `/src/mcp_server/prompts/income_generation_csp_prompt.py`

**Function Structure:**
```python
async def income_generation_csp_engine(
    tickers: list,
    cash_usd: float,
    min_days: int = 7,
    max_days: int = 28,
    target_apy_pct: float = 50,
    min_winrate_pct: float = 70,
    confidence_pct: float = 90,
) -> str:
    """
    Generate income-focused Cash-Secured Put strategies prompt.
    
    Returns:
        Comprehensive execution prompt string
    """
```

### TS2: Generated Prompt Structure

**Prompt Components:**
1. **Header**: Strategy objectives and constraints
2. **Time Validation Protocol**: Mandatory market time verification
3. **Tool Execution Sequence**: Step-by-step MCP tool calls
4. **Screening Criteria**: Income-optimized filtering parameters
5. **Output Specifications**: Required analysis format
6. **Risk Management Rules**: Assignment avoidance protocols
7. **Execution Checklist**: Professional implementation guide

### TS3: Error Handling and Validation

**Input Validation:**
- Ticker list validation (max 10 symbols)
- Cash amount bounds checking ($1,000 - $1,000,000)
- Date range validation (min_days < max_days)
- Percentage parameter bounds (0-100%)

**Execution Safety:**
- Market hours validation
- API rate limiting considerations
- Fallback symbol handling
- Error recovery procedures

### TS4: Integration Points

**MCP Server Registration:**
```python
@mcp.prompt()
async def income_generation_csp_engine(
    tickers: list,
    cash_usd: float,
    min_days: int = 7,
    max_days: int = 28,
    target_apy_pct: float = 50,
    min_winrate_pct: float = 70,
    confidence_pct: float = 90,
) -> str:
```

**Dependencies:**
- FastMCP framework
- Existing TradingAgent MCP tools
- Tradier API client
- Market time utilities

## Non-Functional Requirements

### NFR1: Performance

- **Response Time**: Prompt generation < 1 second
- **Concurrent Users**: Support 10+ simultaneous prompt requests
- **Memory Usage**: < 100MB per prompt generation
- **API Efficiency**: Minimize redundant tool calls in generated prompts

### NFR2: Reliability

- **Availability**: 99.9% uptime aligned with MCP server
- **Error Rate**: < 0.1% prompt generation failures
- **Data Consistency**: Ensure market time synchronization
- **Graceful Degradation**: Handle partial tool failures

### NFR3: Usability

- **Prompt Clarity**: Generated prompts must be self-explanatory
- **Parameter Validation**: Clear error messages for invalid inputs
- **Documentation**: Comprehensive usage examples
- **Claude Code Integration**: Seamless prompt execution

### NFR4: Security and Compliance

- **API Security**: Secure Tradier API credential handling
- **Data Privacy**: No storage of sensitive financial data
- **Audit Trail**: Log prompt generation and execution
- **Disclaimer**: Clear risk warnings in all outputs

## User Experience Design

### UX1: Prompt Usage Flow

**Claude Code Integration:**
```
User: "Generate an income-focused CSP strategy for AAPL with $50,000 capital"
Claude: [Calls income_generation_csp_engine prompt]
Output: [Comprehensive execution plan with specific tool calls]
User: [Executes the generated plan step by step]
```

**Example Prompt Call:**
```python
# Call the prompt with specific parameters
prompt_result = await income_generation_csp_engine(
    tickers=["AAPL"],
    cash_usd=50000,
    min_days=7,
    max_days=21,
    target_apy_pct=50
)
```

### UX2: Generated Prompt Experience

**Structured Output Format:**
1. **Strategy Objectives**: Clear income-focused goals
2. **Time-Sensitive Validation**: Market time verification steps
3. **Sequential Tool Calls**: Numbered execution sequence
4. **Filtering Criteria**: Specific screening parameters
5. **Success Metrics**: Quantified performance targets
6. **Risk Controls**: Assignment avoidance protocols

**User Guidance:**
- Clear tool call syntax with parameters
- Expected output descriptions
- Error handling instructions
- Progress tracking guidance

## Implementation Plan

### Phase 1: Core Prompt Development (Week 1)

**Tasks:**
1. Create `income_generation_csp_prompt.py` file
2. Implement core prompt generation logic
3. Integrate with existing MCP tool ecosystem
4. Add comprehensive parameter validation
5. Create unit tests for prompt generation

**Deliverables:**
- Functional prompt generation function
- Input validation and error handling
- Basic integration tests
- Initial documentation

### Phase 2: Tool Integration and Optimization (Week 2)

**Tasks:**
1. Optimize tool call sequences for efficiency
2. Implement income-specific filtering logic
3. Add market context validation
4. Create execution templates and examples
5. Performance testing and optimization

**Deliverables:**
- Optimized prompt output
- Performance benchmarks
- Integration with cash_secured_put_strategy_tool
- Market time validation logic

### Phase 3: Testing and Documentation (Week 3)

**Tasks:**
1. Comprehensive testing across market conditions
2. User experience testing with Claude Code
3. Documentation and usage examples
4. Error handling and edge case coverage
5. Security and compliance validation

**Deliverables:**
- Complete test suite
- User documentation
- Claude Code integration guide
- Security audit results

### Phase 4: Production Deployment (Week 4)

**Tasks:**
1. Production environment setup
2. Monitoring and logging implementation
3. Performance monitoring
4. User training and support
5. Post-deployment validation

**Deliverables:**
- Production-ready deployment
- Monitoring dashboard
- User training materials
- Support documentation

## Testing Strategy

### Test Cases

**TC1: Basic Prompt Generation**
- Input: Valid ticker list, cash amount, standard parameters
- Expected: Well-formed prompt with tool call sequence
- Validation: Prompt structure, parameter passing, syntax correctness

**TC2: Income Focus Validation**
- Input: Income-specific parameters (Delta 0.10-0.30)
- Expected: Prompt emphasizes premium collection over assignment
- Validation: Tool parameters set to `purpose_type="income"`

**TC3: Edge Case Handling**
- Input: Invalid tickers, extreme parameters, market hours
- Expected: Graceful error handling and clear messages
- Validation: Error messages, fallback behaviors

**TC4: Integration Testing**
- Input: Full prompt execution through Claude Code
- Expected: Successful tool execution and results
- Validation: End-to-end workflow completion

**TC5: Performance Testing**
- Input: Multiple concurrent prompt generations
- Expected: Sub-second response times, stable performance
- Validation: Response time metrics, memory usage

### Acceptance Criteria

**AC1: Functional Requirements**
- [ ] Prompt generates valid tool call sequences
- [ ] Income-focused parameters correctly set
- [ ] Market time validation included
- [ ] Error handling for all edge cases
- [ ] Integration with existing MCP tools

**AC2: Performance Requirements**
- [ ] Prompt generation < 1 second
- [ ] Memory usage < 100MB per request
- [ ] Support 10+ concurrent users
- [ ] 99.9% availability

**AC3: User Experience Requirements**
- [ ] Clear, actionable prompt output
- [ ] Self-explanatory tool call syntax
- [ ] Comprehensive error messages
- [ ] Professional documentation

## Risk Assessment and Mitigation

### High-Risk Items

**R1: Market Data Dependency**
- Risk: Tradier API outages affecting prompt execution
- Mitigation: Graceful degradation, cached fallback data
- Monitoring: API health checks, error rate alerts

**R2: Tool Integration Complexity**
- Risk: Breaking changes in existing MCP tools
- Mitigation: Version pinning, compatibility testing
- Monitoring: Integration test automation

**R3: Financial Data Accuracy**
- Risk: Incorrect options data leading to poor strategies
- Mitigation: Multiple data validation layers, disclaimers
- Monitoring: Data quality checks, audit trails

### Medium-Risk Items

**R4: Performance Degradation**
- Risk: Slow prompt generation affecting user experience
- Mitigation: Caching, optimization, load balancing
- Monitoring: Performance metrics, user experience tracking

**R5: Parameter Validation Gaps**
- Risk: Invalid inputs causing runtime errors
- Mitigation: Comprehensive validation, input sanitization
- Monitoring: Error logging, validation failure tracking

## Success Metrics

### Key Performance Indicators (KPIs)

**KPI1: Prompt Quality**
- Metric: Successful prompt execution rate
- Target: >99% success rate
- Measurement: Tool execution completion tracking

**KPI2: User Adoption**
- Metric: Monthly active prompt users
- Target: 50+ users within 3 months
- Measurement: Claude Code usage analytics

**KPI3: Performance**
- Metric: Average prompt generation time
- Target: <1 second
- Measurement: Response time monitoring

**KPI4: Strategy Effectiveness**
- Metric: Generated strategies meeting target APY
- Target: >90% of strategies meet 50% APY target
- Measurement: Strategy analysis results tracking

### Success Criteria

**Short-term (1 month):**
- Functional prompt deployed and available
- Basic integration with Claude Code working
- 10+ successful user executions
- Documentation complete

**Medium-term (3 months):**
- 50+ active users
- <1 second average response time
- 99% uptime achieved
- User satisfaction >4.5/5

**Long-term (6 months):**
- 100+ active users
- Advanced features implemented
- Integration with additional tools
- Proven strategy effectiveness

## Resource Requirements

### Development Resources

**Human Resources:**
- 1 Senior Python Developer (4 weeks, 100%)
- 1 Options Trading Expert (2 weeks, 50%)
- 1 QA Engineer (2 weeks, 50%)
- 1 Technical Writer (1 week, 100%)

**Technical Resources:**
- Development environment access
- Tradier API testing credentials
- Claude Code development setup
- MCP server infrastructure

### Infrastructure Requirements

**Computing Resources:**
- CPU: Standard cloud compute instances
- Memory: 8GB minimum for development
- Storage: 10GB for logs and temporary data
- Network: Standard bandwidth requirements

**External Services:**
- Tradier API access (existing)
- Claude Code integration (existing)
- MCP server infrastructure (existing)

## Conclusion

The Income Generation CSP Engine MCP Server Prompt will provide TradingAgent MCP users with a powerful, specialized tool for generating high-yield, low-risk options income strategies. By leveraging existing MCP tools and focusing specifically on premium collection over stock acquisition, this prompt will fill a critical gap in the current options strategy toolkit.

The implementation follows established patterns from the existing codebase while introducing income-specific optimizations that align with the unique requirements of premium collection strategies. The comprehensive testing and validation approach ensures reliability and accuracy for financial decision-making.

Success will be measured through user adoption, prompt execution reliability, and the effectiveness of generated strategies in meeting target return objectives while minimizing assignment risk.

## Appendix

### A1: Reference Implementation Analysis

The reference implementation at `/ai_docs/income_generation_csp_engine.md` provides extensive detail on the desired functionality. Key insights:

1. **Progress Tracking**: Original includes TaskProgressTracker which we'll omit
2. **Tool Sequence**: Detailed tool call sequence with error handling
3. **Income Focus**: Specific emphasis on premium collection over assignment
4. **Market Validation**: Critical time-based validation requirements
5. **Professional Format**: JP Morgan-style order block formatting

### A2: Existing Tool Integration

The `cash_secured_put_strategy_tool_mcp` provides excellent foundation:

1. **Purpose Type Support**: Already supports "income" vs "discount" modes
2. **Delta Range Control**: Configurable Delta filtering for income focus
3. **Professional Output**: Order blocks and risk analysis included
4. **Market Context**: Comprehensive market analysis integration
5. **CSV Export**: Data export for further analysis

### A3: Prompt vs Tool Distinction

This PRD creates a **PROMPT** that generates execution plans, not a new **TOOL**:

- **Prompt**: Generates comprehensive execution instructions for users
- **Tool**: Performs specific analysis and returns data
- **Integration**: Prompt leverages existing tools for actual execution
- **Value**: Provides structured, income-focused analysis workflow

### A4: Market Time Criticality

Options analysis requires precise time handling:

- **Market Hours**: Validate trading session status
- **Expiration Dates**: Ensure options haven't expired
- **Settlement**: Account for settlement and exercise timelines
- **Time Decay**: Factor time remaining for premium analysis

This attention to timing is critical for accurate options analysis and strategy viability.