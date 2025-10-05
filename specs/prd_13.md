# PRD v13: 期权限价单成交概率预测工具

## 文档信息

- **版本**: v13
- **创建日期**: 2025-10-05
- **状态**: Planning
- **优先级**: High
- **类型**: New Feature

## 执行摘要

开发独立的期权限价单成交概率预测工具 (`option_limit_order_probability_tool`)，基于蒙特卡洛模拟、波动率分析和Greeks敏感度，预测期权限价单的成交概率、预期成交时间和置信度评估。该工具解决交易者在下限价单前"能否成交"的核心问题。

## Instructions
- 参考 cash_secured_put_strategy_tool 中的MCP Server Tool的开发规范

## 参考文件
- /Users/szou/Python/Playground/TradingAgentMCP/src/mcp_server/server.py
- /Users/szou/Python/Playground/TradingAgentMCP/src/mcp_server/tools/cash_secured_put_strategy_tool.py
- /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/claude_opus_mcp_breakdown.md
- /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/fastmcp.md

## 问题陈述

### 当前痛点

**核心问题**: 交易者在下期权限价单时，无法预知该限价是否能成交

**具体场景**:
```
当前期权价格: $2.50
交易者想法: "我想以 $2.80 卖出 PUT，这个限价能成交吗？"
现有系统: 无法回答 🤷
```

**与现有功能的区别**:
- ❌ **`min_premium`** - 这是市价筛选（当前价格 ≥ $2.00 就符合）
- ✅ **限价单预测** - 预测未来价格是否能达到 $2.80（概率性问题）

### 真实需求

交易者需要知道:
1. **成交概率** - 限价单有多大概率成交？
2. **成交时间** - 预计多久能成交？
3. **置信度** - 预测的可靠性如何？
4. **替代方案** - 如果概率太低，应该调整到什么价位？

## 解决方案概述

### 核心方法

**基于以下因素的概率模型**:
1. **历史股价趋势** - 标的股票的价格运动方向和速度
2. **波动率分析** - 隐含波动率(IV) + 历史波动率(HV)混合
3. **Greeks敏感度** - Delta对股价运动的响应、Theta时间衰减
4. **蒙特卡洛模拟** - 10,000次路径模拟统计成交概率

### 技术方案

```python
# 算法流程
1. 获取当前期权Greeks (IV, Delta, Theta)
2. 获取标的历史波动率 (HV)
3. 计算有效波动率 = 0.6 * IV + 0.4 * HV
4. 蒙特卡洛模拟:
   - 模拟股价每日随机游走
   - 根据Delta计算期权价格变化
   - 应用Theta时间衰减
   - 检查是否触达限价
5. 统计成交概率和预期时间
6. 理论验证 + 简化回测
```

## 功能需求

### FR-1: 核心工具接口

**工具名称**: `option_limit_order_probability_tool_mcp`

**输入参数**:
```python
{
    "symbol": str,              # 股票代码 (必需)
    "strike_price": float,      # 执行价格 (必需)
    "expiration": str,          # 到期日 YYYY-MM-DD (必需)
    "option_type": str,         # "put" 或 "call" (必需)
    "current_price": float,     # 当前期权价格 (必需)
    "limit_price": float,       # 目标限价 (必需)
    "order_side": str,          # "buy" 或 "sell" (必需)
    "analysis_window": int      # 分析窗口天数 (可选，默认到期前全部)
}
```

**输出结构**:
```python
{
    # 核心结果
    "fill_probability": 0.68,           # 成交概率 68%
    "expected_days_to_fill": 3.2,       # 预期 3.2 天成交
    "standard_error": 0.04,             # 标准误差 ±4%

    # 每日累计概率
    "probability_by_day": [
        {"day": 1, "cumulative_prob": 0.25, "daily_prob": 0.25},
        {"day": 2, "cumulative_prob": 0.45, "daily_prob": 0.20},
        {"day": 3, "cumulative_prob": 0.68, "daily_prob": 0.23},
        {"day": 5, "cumulative_prob": 0.82, "daily_prob": 0.14}
    ],

    # 分析基础数据
    "analysis_basis": {
        "implied_volatility": 0.35,      # 隐含波动率
        "historical_volatility": 0.32,   # 历史波动率 (3个月)
        "effective_volatility": 0.34,    # 有效波动率 (混合)
        "delta": -0.42,                  # Delta
        "theta_per_day": -0.08,          # 每日Theta衰减
        "days_to_expiry": 15,            # 距离到期天数
        "price_move_required": 0.30,     # 需要的价格变动 ($)
        "move_in_std": 0.45              # 以标准差衡量的变动
    },

    # 验证信息
    "validation": {
        "method": "monte_carlo",
        "simulations": 10000,
        "backtest_available": true,      # 是否有回测
        "backtest_mae": 0.12,            # 回测平均误差
        "confidence_level": "high",      # high/medium/low
        "theoretical_validated": true    # 理论验证通过
    },

    # 智能建议
    "recommendations": [
        "该限价有 68% 概率在 3.2 天内成交",
        "标准误差 ±4%，估计相对可靠",
        "如需更高成交率(80%+)，建议降低限价至 $2.65",
        "如追求快速成交(1天内)，建议降低限价至 $2.55"
    ],

    # 替代限价方案
    "alternative_limits": [
        {
            "limit_price": 2.55,
            "fill_probability": 0.85,
            "expected_days": 1.5,
            "scenario": "快速成交方案"
        },
        {
            "limit_price": 2.65,
            "fill_probability": 0.81,
            "expected_days": 2.1,
            "scenario": "平衡方案"
        },
        {
            "limit_price": 2.80,
            "fill_probability": 0.68,
            "expected_days": 3.2,
            "scenario": "当前限价"
        },
        {
            "limit_price": 3.00,
            "fill_probability": 0.42,
            "expected_days": 5.8,
            "scenario": "高收益低概率"
        }
    ],

    "status": "success"
}
```

### FR-2: 蒙特卡洛模拟引擎

**核心算法模块**: `src/option/limit_order_probability.py`

**主要功能**:

1. **期权价格模拟**
   ```python
   def simulate_option_price_path(
       current_price: float,
       underlying_price: float,
       strike: float,
       days_remaining: int,
       delta: float,
       theta: float,
       volatility: float,
       risk_free_rate: float = 0.048
   ) -> List[float]:
       """
       模拟单条期权价格路径

       每日更新逻辑:
       1. 股价随机游走: S_t+1 = S_t * exp(μ*dt + σ*sqrt(dt)*Z)
       2. Delta影响: ΔP_delta = Delta * (S_t+1 - S_t)
       3. Theta衰减: ΔP_theta = Theta * dt
       4. 新期权价格: P_t+1 = P_t + ΔP_delta + ΔP_theta
       """
   ```

2. **成交检测逻辑**
   ```python
   def check_limit_fill(
       price_path: List[float],
       limit_price: float,
       order_side: str
   ) -> Tuple[bool, Optional[int]]:
       """
       检查价格路径是否触达限价

       买单: 期权价格 <= 限价时成交
       卖单: 期权价格 >= 限价时成交

       Returns:
           (是否成交, 成交日期索引)
       """
   ```

3. **概率统计**
   ```python
   def calculate_fill_statistics(
       simulation_results: List[Tuple[bool, Optional[int]]],
       simulations: int = 10000
   ) -> Dict[str, Any]:
       """
       计算成交概率统计数据

       Returns:
           - fill_probability: 成交概率
           - expected_days: 期望成交天数
           - standard_error: 标准误差
           - probability_by_day: 每日累计概率分布
       """
   ```

### FR-3: 波动率混合计算

**波动率模块**: `src/option/limit_order_probability.py`

```python
def calculate_effective_volatility(
    symbol: str,
    implied_volatility: float,
    lookback_days: int = 90,
    iv_weight: float = 0.6,
    hv_weight: float = 0.4
) -> Dict[str, float]:
    """
    计算有效波动率

    方法:
    1. 从 stock_history_tool 获取历史数据
    2. 计算历史波动率 (HV)
    3. 混合: effective_vol = iv_weight * IV + hv_weight * HV

    Args:
        symbol: 股票代码
        implied_volatility: 隐含波动率
        lookback_days: 历史回溯天数
        iv_weight: IV权重 (默认60%)
        hv_weight: HV权重 (默认40%)

    Returns:
        {
            "implied_volatility": 0.35,
            "historical_volatility": 0.32,
            "effective_volatility": 0.34,
            "hv_lookback_days": 90
        }
    """
```

### FR-4: 理论验证框架

**验证模块**: `src/option/limit_order_probability.py`

```python
def theoretical_validation() -> Dict[str, bool]:
    """
    边界条件和理论验证

    测试用例:
    1. 限价 = 当前价 → 概率 = 100%, 天数 = 0
    2. 限价远高于当前价 → 概率 ≈ 0%
    3. 波动率 = 0 → 确定性结果 (0% 或 100%)
    4. 波动率 ↑ → 成交概率 ↑
    5. 时间窗口 ↑ → 成交概率 ↑
    6. Theta < 0 (PUT卖方) → 时间对卖方不利

    Returns:
        所有测试的通过状态
    """
```

### FR-5: 简化回测验证 (Phase 2)

**回测模块**: `src/option/limit_order_probability.py`

```python
def simple_backtest_validation(
    symbol: str,
    strike: float,
    days_to_expiry: int = 30,
    lookback_days: int = 90,
    limit_premium_pct: float = 0.10
) -> Dict[str, Any]:
    """
    基于历史股价的简化回测

    流程:
    1. 获取历史股价数据 (lookback_days)
    2. 对每个历史日期:
       a. 用 Black-Scholes 计算当日期权理论价格
       b. 设置限价 (理论价格 * (1 + limit_premium_pct))
       c. 模拟接下来 N 天，检查是否成交
       d. 记录实际成交结果
    3. 对比实际成交率 vs 模型预测成交率
    4. 计算 MAE (Mean Absolute Error)

    Returns:
        {
            "backtest_samples": 60,
            "actual_fill_rate": 0.65,
            "predicted_fill_rate": 0.68,
            "mae": 0.12,
            "is_reliable": true,  # MAE < 0.15
            "sample_results": [...]
        }
    """
```

### FR-6: MCP工具封装

**MCP工具**: `src/mcp_server/tools/option_limit_order_probability_tool.py`

```python
async def option_limit_order_probability_tool(
    symbol: str,
    strike_price: float,
    expiration: str,
    option_type: str,
    current_price: float,
    limit_price: float,
    order_side: str,
    analysis_window: Optional[int] = None
) -> Dict[str, Any]:
    """
    期权限价单成交概率预测工具

    执行流程:
    1. 参数验证
    2. 获取当前Greeks (调用现有工具)
    3. 获取历史波动率
    4. 计算有效波动率
    5. 执行蒙特卡洛模拟
    6. 运行理论验证
    7. 运行简化回测 (如果数据充足)
    8. 生成智能建议和替代方案
    9. 返回完整分析结果
    """
```

## 非功能需求

### NFR-1: 性能要求

- **响应时间**: < 5秒 (10,000次模拟)
- **并发支持**: 支持多个请求并行处理
- **资源占用**: 单次请求内存 < 100MB

### NFR-2: 准确性要求

- **理论验证**: 100% 边界条件测试通过
- **回测MAE**: < 15% (Mean Absolute Error)
- **置信度分级**:
  - High: MAE < 10%, 回测样本 > 50
  - Medium: MAE < 15%, 回测样本 > 30
  - Low: MAE ≥ 15% 或无回测数据

### NFR-3: 可维护性

- **代码模块化**: 核心算法、验证、工具封装分离
- **单元测试覆盖率**: > 80%
- **文档完整性**: 所有公开函数有详细docstring

### NFR-4: 用户体验

- **清晰的输出**: 概率用百分比表示，避免小数混淆
- **智能建议**: 提供可操作的替代限价方案
- **透明度**: 显示分析基础数据和验证状态
- **警告提示**: 当置信度低时明确告知用户

## 技术架构

### 模块结构

```
src/option/
├── limit_order_probability.py       # 核心算法模块 🆕
│   ├── simulate_option_price_path()
│   ├── monte_carlo_fill_probability()
│   ├── calculate_effective_volatility()
│   ├── theoretical_validation()
│   └── simple_backtest_validation()

src/mcp_server/tools/
├── option_limit_order_probability_tool.py  # MCP工具接口 🆕

tests/option/
├── test_limit_order_probability.py   # 单元测试 🆕

tests/tools/
├── test_option_limit_order_probability_tool.py  # 集成测试 🆕
```

### 依赖关系

**现有依赖**:
- `src/option/greeks_enhanced.py` - 获取Delta, Theta, IV
- `src/stock/history_data.py` - 获取历史数据计算HV
- `src/provider/tradier/client.py` - 市场数据
- `scipy.stats` - 统计分布计算
- `numpy` - 数值计算

**新增依赖**: 无

### 数据流

```
用户输入 (symbol, strike, limit_price, ...)
    ↓
[MCP Tool] 参数验证
    ↓
[Tradier API] 获取Greeks和当前价格
    ↓
[Stock History] 获取历史数据 → 计算HV
    ↓
[Volatility Mixer] IV + HV → 有效波动率
    ↓
[Monte Carlo Engine] 10,000次模拟
    ↓
[Statistics] 计算概率、期望天数、标准误差
    ↓
[Validation] 理论验证 + 简化回测
    ↓
[Recommendations] 生成智能建议和替代方案
    ↓
用户输出 (JSON结构化结果)
```

## 实施计划

### Phase 1: 核心算法开发 (4-6小时)

#### Step 1.1: 创建核心模块
- [ ] 创建 `src/option/limit_order_probability.py`
- [ ] 实现 `simulate_option_price_path()` 函数
- [ ] 实现 `monte_carlo_fill_probability()` 函数
- [ ] 实现 `calculate_fill_statistics()` 函数

#### Step 1.2: 波动率混合
- [ ] 实现 `calculate_effective_volatility()` 函数
- [ ] 集成 `stock_history_tool` 获取历史数据
- [ ] 实现历史波动率计算逻辑

#### Step 1.3: 理论验证
- [ ] 实现 `theoretical_validation()` 函数
- [ ] 编写边界条件测试用例
- [ ] 实现敏感性分析测试

#### Step 1.4: 单元测试
- [ ] 创建 `tests/option/test_limit_order_probability.py`
- [ ] 测试蒙特卡洛模拟准确性
- [ ] 测试波动率计算
- [ ] 测试边界条件
- [ ] 测试敏感性分析

### Phase 2: 简化回测验证 (3-4小时)

#### Step 2.1: 回测框架
- [ ] 实现 `simple_backtest_validation()` 函数
- [ ] 实现 Black-Scholes 期权定价
- [ ] 实现历史数据回溯逻辑

#### Step 2.2: 准确性评估
- [ ] 实现 MAE 计算
- [ ] 实现置信度评级逻辑
- [ ] 生成回测报告

#### Step 2.3: 回测测试
- [ ] 使用真实历史数据测试
- [ ] 验证回测准确性
- [ ] 调整模型参数优化MAE

### Phase 3: MCP工具封装 (2-3小时)

#### Step 3.1: 工具实现
- [ ] 创建 `src/mcp_server/tools/option_limit_order_probability_tool.py`
- [ ] 实现参数验证
- [ ] 集成核心算法模块
- [ ] 实现错误处理

#### Step 3.2: 智能建议
- [ ] 实现替代限价方案生成
- [ ] 实现智能建议文本生成
- [ ] 格式化输出结果

#### Step 3.3: 服务器注册
- [ ] 在 `server.py` 中注册工具
- [ ] 添加完整的docstring
- [ ] 更新工具列表

### Phase 4: 集成测试与文档 (2小时)

#### Step 4.1: 集成测试
- [ ] 创建 `tests/tools/test_option_limit_order_probability_tool.py`
- [ ] 测试完整工作流
- [ ] 测试错误场景
- [ ] 性能测试

#### Step 4.2: 文档更新
- [ ] 更新 `README.md` 添加工具说明
- [ ] 创建使用示例文档
- [ ] 添加API文档

#### Step 4.3: 验证
- [ ] 运行所有测试确保通过
- [ ] 性能验证 (响应时间 < 5秒)
- [ ] 端到端功能验证

## 测试策略

### 单元测试

**测试文件**: `tests/option/test_limit_order_probability.py`

```python
class TestMonteCarloSimulation:
    def test_boundary_limit_equals_current():
        """限价 = 当前价 → 概率 100%, 天数 0"""

    def test_boundary_limit_far_above():
        """限价远高于当前价 → 概率 ≈ 0%"""

    def test_volatility_impact():
        """波动率 ↑ → 成交概率 ↑"""

    def test_time_window_impact():
        """时间窗口 ↑ → 成交概率 ↑"""

    def test_delta_sensitivity():
        """Delta影响期权价格变动"""

    def test_theta_decay():
        """Theta时间衰减正确"""

class TestVolatilityMixing:
    def test_effective_volatility_calculation():
        """有效波动率 = 0.6*IV + 0.4*HV"""

    def test_historical_volatility_accuracy():
        """历史波动率计算准确"""

class TestBacktestValidation:
    def test_backtest_mae_calculation():
        """MAE计算正确"""

    def test_confidence_level_assignment():
        """置信度分级逻辑正确"""
```

### 集成测试

**测试文件**: `tests/tools/test_option_limit_order_probability_tool.py`

```python
class TestLimitOrderProbabilityTool:
    async def test_complete_workflow():
        """完整工作流测试"""
        result = await option_limit_order_probability_tool(
            symbol="AAPL",
            strike_price=145.0,
            expiration="2025-11-07",
            option_type="put",
            current_price=2.50,
            limit_price=2.80,
            order_side="sell"
        )
        assert result["status"] == "success"
        assert 0 <= result["fill_probability"] <= 1
        assert result["expected_days_to_fill"] >= 0

    async def test_parameter_validation():
        """参数验证测试"""

    async def test_error_handling():
        """错误处理测试"""

    async def test_performance():
        """性能测试: < 5秒"""
```

### 回测验证

**测试文件**: `tests/option/test_backtest_validation.py`

```python
class TestBacktestAccuracy:
    async def test_aapl_30day_backtest():
        """AAPL 30天期权回测"""
        result = simple_backtest_validation(
            symbol="AAPL",
            strike=145.0,
            days_to_expiry=30,
            lookback_days=90
        )
        assert result["mae"] < 0.15
        assert result["is_reliable"] == True

    async def test_high_volatility_stock():
        """高波动股票回测"""

    async def test_low_volatility_stock():
        """低波动股票回测"""
```

## 验证标准

### 功能验证

- [ ] 所有输入参数正确验证
- [ ] 蒙特卡洛模拟生成合理结果
- [ ] 波动率混合计算正确
- [ ] 理论验证100%通过
- [ ] 回测MAE < 15%
- [ ] 智能建议准确可用
- [ ] 替代方案合理有效

### 性能验证

- [ ] 10,000次模拟 < 5秒
- [ ] 内存占用 < 100MB
- [ ] 支持并发请求

### 准确性验证

- [ ] 边界条件测试100%通过
- [ ] 敏感性分析符合预期
- [ ] 回测验证MAE < 15%
- [ ] 不同股票表现稳定

## 验证命令

```bash
# Phase 1: 单元测试
uv run pytest tests/option/test_limit_order_probability.py -v

# Phase 2: 回测验证
uv run pytest tests/option/test_backtest_validation.py -v

# Phase 3: 集成测试
uv run pytest tests/tools/test_option_limit_order_probability_tool.py -v

# 完整测试套件
uv run pytest tests/ -v

# 性能测试
uv run pytest tests/tools/test_option_limit_order_probability_tool.py::test_performance -v

# 测试覆盖率
uv run pytest tests/option/ tests/tools/test_option_limit_order_probability_tool.py --cov=src/option/limit_order_probability --cov=src/mcp_server/tools/option_limit_order_probability_tool --cov-report=html
```

## 使用示例

### 示例1: 基本使用

```python
# 查询: AAPL PUT $145, 当前 $2.50, 想以 $2.80 卖出
result = await option_limit_order_probability_tool_mcp(
    symbol="AAPL",
    strike_price=145.0,
    expiration="2025-11-07",
    option_type="put",
    current_price=2.50,
    limit_price=2.80,
    order_side="sell"
)

print(f"成交概率: {result['fill_probability']*100:.1f}%")
print(f"预期成交天数: {result['expected_days_to_fill']:.1f}")
print(f"置信度: {result['validation']['confidence_level']}")
```

**预期输出**:
```
成交概率: 68.0%
预期成交天数: 3.2
置信度: high

建议:
- 该限价有 68% 概率在 3.2 天内成交
- 如需更高成交率(80%+)，建议降低限价至 $2.65
```

### 示例2: 买入限价单

```python
# TSLA CALL $250, 当前 $12.00, 想以 $10.50 买入
result = await option_limit_order_probability_tool_mcp(
    symbol="TSLA",
    strike_price=250.0,
    expiration="2025-11-21",
    option_type="call",
    current_price=12.00,
    limit_price=10.50,
    order_side="buy"
)

# 查看替代方案
for alt in result['alternative_limits']:
    print(f"限价 ${alt['limit_price']}: "
          f"{alt['fill_probability']*100:.0f}% 概率, "
          f"{alt['expected_days']:.1f} 天")
```

### 示例3: 与CSP策略结合

```python
# 先获取CSP推荐
csp_result = await cash_secured_put_strategy_tool_mcp(
    symbol="AAPL",
    purpose_type="income",
    duration="1w",
    capital_limit=50000
)

# 对推荐的执行价分析限价成交概率
conservative = csp_result['recommendations']['conservative']
strike = conservative['option_details']['strike_price']
premium = conservative['option_details']['premium']

# 想以高于市价10%卖出
target_limit = premium * 1.10

limit_analysis = await option_limit_order_probability_tool_mcp(
    symbol="AAPL",
    strike_price=strike,
    expiration=csp_result['selected_expiration']['date'],
    option_type="put",
    current_price=premium,
    limit_price=target_limit,
    order_side="sell"
)

print(f"CSP推荐: ${strike} PUT @ ${premium}")
print(f"限价 ${target_limit}: {limit_analysis['fill_probability']*100:.0f}% 成交概率")
```

## 成功标准

### 技术标准

- [ ] 所有单元测试通过 (覆盖率 > 80%)
- [ ] 所有集成测试通过
- [ ] 性能满足要求 (< 5秒)
- [ ] 理论验证100%通过
- [ ] 回测MAE < 15%

### 功能标准

- [ ] 准确预测限价单成交概率
- [ ] 提供合理的预期成交时间
- [ ] 智能建议实用有效
- [ ] 替代方案合理可行
- [ ] 置信度评估准确

### 用户体验标准

- [ ] 输出清晰易懂
- [ ] 建议可操作
- [ ] 警告提示及时
- [ ] 文档完整清晰

## 风险与限制

### 风险

1. **模型准确性风险**
   - 蒙特卡洛依赖波动率假设
   - 市场极端情况下预测可能失效
   - 缓解: 回测验证 + 置信度评级

2. **数据依赖风险**
   - 依赖Tradier API数据质量
   - 历史数据可能不足
   - 缓解: 数据验证 + 错误处理

3. **性能风险**
   - 10,000次模拟可能影响响应速度
   - 缓解: 性能优化 + 异步处理

### 限制

1. **模型假设**
   - 假设股价遵循几何布朗运动
   - 假设波动率相对稳定
   - 不考虑市场微观结构

2. **数据限制**
   - 无历史期权价格数据 (Phase 3暂不实施)
   - 依赖Black-Scholes理论定价
   - 回测基于模拟非实际数据

3. **适用范围**
   - 适用于流动性好的期权
   - 不适用于极端市场环境
   - 不保证实际成交

### 免责声明

输出中必须包含:
```
"disclaimer": "本分析基于统计模型和历史数据，不构成投资建议。
实际成交受市场流动性、订单簿深度等多种因素影响。期权交易存在重大风险，
可能导致全部本金损失。请谨慎决策，自行承担交易风险。"
```

## 未来扩展

### Phase 3: 完整历史回测 (未来)
- 获取历史期权价格数据
- 实际成交数据回测
- 提高模型准确性

### Phase 4: 机器学习增强 (未来)
- 使用ML模型预测成交概率
- 学习历史成交模式
- 自适应参数调整

### Phase 5: 实时订单簿分析 (未来)
- 集成Level 2数据
- 分析订单簿深度
- 更精确的成交预测

## 附录

### A. 数学公式

**蒙特卡洛股价模拟**:
```
S(t+1) = S(t) * exp((μ - σ²/2)*dt + σ*sqrt(dt)*Z)

其中:
S(t) = t时刻股价
μ = 预期收益率 (假设为0，中性模拟)
σ = 波动率
dt = 时间步长 (1/365)
Z ~ N(0,1) = 标准正态分布随机数
```

**期权价格变化**:
```
ΔP_option = Delta * ΔS + Theta * dt

其中:
ΔP_option = 期权价格变化
Delta = 期权Delta值
ΔS = 股价变化
Theta = 每日时间衰减
dt = 时间步长
```

**有效波动率**:
```
σ_effective = w_IV * σ_IV + w_HV * σ_HV

默认权重:
w_IV = 0.6 (隐含波动率权重)
w_HV = 0.4 (历史波动率权重)
```

**标准误差**:
```
SE = sqrt(p * (1-p) / n)

其中:
p = 成交概率
n = 模拟次数 (10,000)
```

### B. 参考资料

- Black-Scholes期权定价模型
- 蒙特卡洛方法在期权定价中的应用
- 期权Greeks及其在交易中的应用
- 波动率估计与预测方法

---

**版本历史**:
- v13.0 (2025-10-05): 初始版本，定义期权限价单成交概率预测工具

## Output
Write the enhanced PRD to specs/prd_13_ai_enhanced.md
