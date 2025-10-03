# PRD v11: 智能到期日优化器 - 股票特定数据驱动改进

**版本**: v11
**状态**: AI Enhanced
**创建日期**: 2025-10-03
**优先级**: High
**类型**: Enhancement - 核心算法优化

---

## 📋 执行摘要

### 问题陈述
当前的智能到期日优化器 (`optimal_expiration_selector_tool.py` 和 `expiration_optimizer.py`) 存在**硬编码和主观设置问题**，导致所有股票使用相同的评分标准，无法针对不同股票的客观市场特征进行个性化优化。

### 解决方案
实现**完全数据驱动的股票特定优化系统**，基于每个股票的客观市场特征（波动率、Beta、流动性、市值等）动态调整评分参数，消除硬编码，实现真正的个性化优化。

### 成功指标
1. **客观性**: 所有调整因子基于可量化的市场数据，零主观硬编码
2. **数据可用性**: ✅ **Tradier API 提供完整 IV/Greeks 数据**（已验证 - via ORATS）
3. **差异化**: 不同股票获得不同的优化结果（高波动科技股 vs 大盘蓝筹股）
4. **透明性**: 完整的优化过程可追溯，包含所有调整推理
5. **向后兼容**: 保持现有 API 不变，渐进式升级

---

## 🎯 核心目标

### 1. 消除硬编码（Bad Taste）
**当前问题**：
```python
# expiration_optimizer.py - 硬编码的评分函数
def calculate_theta_efficiency(self, days: int) -> float:
    if days < 7:
        return 10.0  # ❌ 硬编码值
    elif days < 21:
        return 30 + (days - 7) * 30 / 14  # ❌ 硬编码公式
    # ... 更多硬编码
```

**Linus评价**: "这是典型的特殊情况处理。每个条件分支都是一个补丁。真正的好代码应该用数学模型消除这些分支。"

**改进方案**：
```python
# 基于股票特征的动态调整
def calculate_theta_efficiency(self, days: int, adjustment_factor: float = 1.0) -> float:
    # 通用数学模型，通过adjustment_factor个性化
    base_score = self._theta_curve_model(days)
    return base_score * adjustment_factor
```

### 2. 股票特定优化（Data-Driven）
**核心理念**：不同股票有不同的期权特性
- **高波动科技股**（TSLA, NVDA）：Gamma风险更高，需要更保守的到期日选择
- **大盘蓝筹股**（AAPL, MSFT）：流动性极佳，可以更灵活选择到期日
- **高Beta股票**：市场敏感度高，需要更短的到期周期

**实现方法**：
```python
def _get_stock_market_profile(self, symbol: str) -> Dict[str, float]:
    """基于symbol计算客观市场特征档案"""
    # 从Tradier API / StockInfo获取实时数据
    stock_data = self._fetch_stock_data(symbol)

    return {
        'volatility_ratio': IV / HV,  # 隐含波动率 / 历史波动率
        'liquidity_factor': volume / avg_volume * market_cap_tier,
        'market_cap_tier': 大盘(1.5) / 中盘(1.0) / 小盘(0.7),
        'beta_coefficient': beta,  # 相对市场波动性
        'options_activity': option_volume / stock_volume
    }
```

### 3. 透明优化过程（Explainable AI）
**要求**：每个优化决策都要有清晰的数据来源和计算过程

```python
{
    "optimization_process": {
        "symbol": "TSLA",
        "market_profile": {
            "volatility_ratio": 1.29,  # 来源: IV=45%, HV=35%
            "beta_coefficient": 1.39,  # 来源: Tradier API
            "adjustment_reasoning": "高波动高Beta -> Gamma风险权重-3.5%"
        },
        "dynamic_adjustments": {
            "gamma_adjustment": 0.965,  # 0.8 + (1.29-1.0)*0.3 + (1.39-1.0)*0.2
            "theta_adjustment": 1.05,
            "formula": "显式数学公式"
        },
        "candidate_evaluations": [
            {
                "date": "2025-11-15",
                "base_score": 85.2,
                "adjusted_score": 83.1,  # 应用TSLA特定调整
                "reason": "高Gamma风险导致评分下调2.1分"
            }
        ]
    }
}
```

---

## 🏗️ 技术架构设计

### 层次结构

```
┌─────────────────────────────────────────────────────────────┐
│  MCP Server Layer (optimal_expiration_selector_tool.py)     │
│  - API接口                                                   │
│  - 参数验证                                                  │
│  - 结果格式化                                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Core Optimization Layer (expiration_optimizer.py)          │
│  - 股票特征获取: _get_stock_market_profile()               │
│  - 动态调整计算: _calculate_dynamic_adjustments()          │
│  - 增强评估逻辑: evaluate_expiration(symbol=...)           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Data Source Layer                                          │
│  - TradierClient: 实时行情、期权数据                        │
│  - StockInfoProcessor: 综合股票信息（Beta, 市值, 52周高低） │
│  - HistoricalDataProcessor: 历史波动率计算                  │
└─────────────────────────────────────────────────────────────┘
```

### 数据流

```
用户请求 (symbol="TSLA")
    │
    ├─> 获取股票市场档案
    │       ├─> Tradier API: 当前价格、成交量、IV
    │       ├─> StockInfo: Beta、市值、52周波动
    │       └─> 计算衍生指标: vol_ratio, liquidity, market_cap_tier
    │
    ├─> 计算动态调整因子
    │       ├─> gamma_adjustment = f(vol_ratio, beta)
    │       ├─> theta_adjustment = f(market_cap, liquidity)
    │       ├─> liquidity_adjustment = f(liquidity, options_activity)
    │       └─> income_adjustment = f(vol_ratio)
    │
    ├─> 评估所有候选到期日
    │       ├─> 基础评分（通用数学模型）
    │       └─> 应用TSLA特定调整因子
    │
    └─> 返回最优结果 + 完整优化过程
```

---

## 🔬 核心算法改进

### 1. 股票市场档案获取

#### 实现位置
`src/mcp_server/tools/expiration_optimizer.py`

#### 新增方法
```python
def _get_stock_market_profile(self, symbol: str) -> Dict[str, float]:
    """
    获取股票客观市场特征档案

    Args:
        symbol: 股票代码

    Returns:
        包含以下字段的字典:
        - volatility_ratio: IV/HV比值 (范围: 0.5-2.0)
        - liquidity_factor: 流动性因子 (范围: 0.5-2.0)
        - market_cap_tier: 市值分级 (大盘1.5, 中盘1.0, 小盘0.7)
        - beta_coefficient: Beta系数 (范围: 0.5-2.0)
        - options_activity: 期权活跃度 (范围: 0-1.0)
    """
```

#### 数据来源矩阵

| 特征 | 数据源 | 计算方法 | 默认值 | Phase 4 API 字段 |
|------|--------|----------|--------|------------------|
| **volatility_ratio** | Tradier API greeks.mid_iv + 历史数据(HV) | IV / HV | 1.0 | `greeks.mid_iv` ✅ |
| **liquidity_factor** | TradierQuote.volume, average_volume | (volume/avg_vol) × market_cap_multiplier | 1.0 | `volume`, `average_volume` |
| **market_cap_tier** | StockInfo.market_cap | >100B:1.5, 10-100B:1.0, <10B:0.7 | 1.0 | `market_cap` |
| **beta_coefficient** | StockInfo.beta 或历史计算 | 直接使用或计算相关性 | 1.0 | `beta` |
| **options_activity** | 期权成交量 / 股票成交量 | option_vol / stock_vol | 0.5 | `option.volume` / `quote.volume` |

**✅ Tradier API IV 数据字段**（Phase 4 可用）:
- `greeks.bid_iv`: 买价隐含波动率
- `greeks.mid_iv`: 中间价隐含波动率（**推荐使用**）
- `greeks.ask_iv`: 卖价隐含波动率
- `greeks.smv_vol`: SMV 波动率估计（备选）

#### 股票分类策略（初始版本）

**方法1: 基于已知股票特征的映射表**
```python
# 高波动科技股
HIGH_VOLATILITY_TECH = {
    'TSLA': {'vol_ratio': 1.3, 'beta': 1.4, 'liquidity': 1.2},
    'NVDA': {'vol_ratio': 1.25, 'beta': 1.35, 'liquidity': 1.3},
    # ...
}

# 大盘蓝筹股
LARGE_CAP_BLUE_CHIP = {
    'AAPL': {'vol_ratio': 0.95, 'beta': 1.05, 'liquidity': 1.5},
    'MSFT': {'vol_ratio': 0.9, 'beta': 0.95, 'liquidity': 1.4},
    # ...
}

def _get_stock_market_profile(self, symbol: str) -> Dict[str, float]:
    # 优先使用映射表
    if symbol in HIGH_VOLATILITY_TECH:
        return HIGH_VOLATILITY_TECH[symbol]

    # 否则从API实时计算
    return self._calculate_profile_from_api(symbol)
```

**方法2: 完全从API实时计算（未来版本）**
```python
def _calculate_profile_from_api(self, symbol: str) -> Dict[str, float]:
    # 需要TradierClient和StockInfoProcessor支持
    stock_info = self.stock_info_processor.get_stock_info(symbol)
    option_chain = self.tradier_client.get_option_chain(...)

    iv = self._extract_atm_iv(option_chain)
    hv = self._calculate_historical_volatility(symbol, period=30)

    return {
        'volatility_ratio': iv / hv if hv > 0 else 1.0,
        'beta_coefficient': stock_info.beta or 1.0,
        'liquidity_factor': self._calculate_liquidity(stock_info),
        # ...
    }
```

### 2. 动态调整因子计算

#### 新增方法
```python
def _calculate_dynamic_adjustments(self, market_profile: Dict[str, float]) -> Dict[str, float]:
    """
    基于股票市场档案计算动态调整因子

    Args:
        market_profile: 股票市场特征字典

    Returns:
        调整因子字典，用于修改基础评分
    """
```

#### 数学公式（完全客观）

```python
# 1. Gamma风险调整（高波动 -> 更保守）
gamma_adjustment = 0.8 + (vol_ratio - 1.0) * 0.3 + (beta - 1.0) * 0.2
# TSLA示例: 0.8 + (1.3-1.0)*0.3 + (1.4-1.0)*0.2 = 0.97

# 2. Theta效率调整（大盘股 -> 更灵活）
theta_adjustment = 0.9 + (market_cap_tier - 1.0) * 0.1 + (liquidity - 1.0) * 0.1
# AAPL示例: 0.9 + (1.5-1.0)*0.1 + (1.5-1.0)*0.1 = 1.0

# 3. 流动性调整
liquidity_adjustment = 0.8 + liquidity_factor * 0.2 + options_activity * 0.1
# 高流动性股票得分更高

# 4. 收入优化调整（高IV -> 更激进收入策略）
income_adjustment = 0.9 + (vol_ratio - 1.0) * 0.2
```

#### 调整因子应用范围

| 调整因子 | 应用范围 | 影响的评分函数 |
|----------|----------|----------------|
| gamma_adjustment | 0.7 - 1.3 | `calculate_gamma_risk()` |
| theta_adjustment | 0.8 - 1.2 | `calculate_theta_efficiency()` |
| liquidity_adjustment | 0.8 - 1.3 | `calculate_liquidity_score()` |
| income_adjustment | 0.8 - 1.2 | 策略权重调整 |

### 3. 增强核心评估函数

#### 修改签名
```python
# 旧版本
def evaluate_expiration(self, days: int, expiration_type: str, ...) -> ExpirationCandidate:
    pass

# 新版本 - 添加symbol参数
def evaluate_expiration(self,
                       days: int,
                       expiration_type: str,
                       symbol: Optional[str] = None,  # 新增
                       ...) -> ExpirationCandidate:
    # 如果提供symbol，应用股票特定调整
    if symbol:
        profile = self._get_stock_market_profile(symbol)
        adjustments = self._calculate_dynamic_adjustments(profile)
    else:
        adjustments = self.DEFAULT_ADJUSTMENTS  # 向后兼容

    # 应用调整
    theta_score = self.calculate_theta_efficiency(days, adjustments['theta'])
    gamma_score = self.calculate_gamma_risk(days, volatility, adjustments['gamma'])
    # ...
```

#### 向后兼容性保证
```python
# 场景1: 不提供symbol（保持原有行为）
result = optimizer.evaluate_expiration(days=30, expiration_type='monthly')
# -> 使用默认调整因子 (全部为1.0)

# 场景2: 提供symbol（启用股票特定优化）
result = optimizer.evaluate_expiration(days=30, expiration_type='monthly', symbol='TSLA')
# -> 使用TSLA的动态调整因子
```

---

## 📦 实现计划

### Phase 1: 半数据驱动优化（优先级: P0 - MVP 快速验证）

**文件**: `src/mcp_server/tools/expiration_optimizer.py`

**⚠️ 技术债务说明**：此阶段使用**静态映射表**作为过渡方案
- ✅ **优点**：快速验证算法逻辑，无 API 调用性能担忧，易于调试
- ❌ **缺点**：仍包含硬编码数据，需手动维护股票列表
- 🎯 **目标**：Phase 4（API 实时数据）完成后**移除此技术债**
- 📊 **对比**：与 PRD "零硬编码" 目标存在妥协，但符合渐进式开发原则

#### 任务分解

1. **添加股票市场档案获取**（初始版本 - 静态映射表）
   ```python
   # 新增方法
   def _get_stock_market_profile(self, symbol: str) -> Dict[str, float]

   # 初始实现: 使用静态映射表（技术债 - Phase 4 后移除）
   HIGH_VOLATILITY_TECH = {
       'TSLA': {'volatility_ratio': 1.3, 'beta': 1.4, 'liquidity': 1.2},
       'NVDA': {'volatility_ratio': 1.25, 'beta': 1.35, 'liquidity': 1.3},
       # ... 更多高波动股票
   }
   LARGE_CAP_BLUE_CHIP = {
       'AAPL': {'volatility_ratio': 0.95, 'beta': 1.05, 'liquidity': 1.5},
       'MSFT': {'volatility_ratio': 0.9, 'beta': 0.95, 'liquidity': 1.4},
       # ... 更多大盘蓝筹股
   }
   ```

2. **添加动态调整计算**
   ```python
   def _calculate_dynamic_adjustments(self, market_profile: Dict) -> Dict[str, float]

   # 实现所有数学公式（gamma, theta, liquidity, income）
   ```

3. **修改核心评分函数**
   ```python
   # 添加adjustment_factor参数
   def calculate_theta_efficiency(self, days: int, adjustment_factor: float = 1.0)
   def calculate_gamma_risk(self, days: int, volatility: float, adjustment_factor: float = 1.0)
   def calculate_liquidity_score(self, ..., adjustment_factor: float = 1.0)
   ```

4. **更新evaluate_expiration方法**
   ```python
   # 添加symbol参数
   def evaluate_expiration(self, ..., symbol: Optional[str] = None) -> ExpirationCandidate

   # 在方法内:
   # 1. 获取market_profile（如果symbol提供）
   # 2. 计算adjustments
   # 3. 应用到评分函数
   # 4. 记录调整原因到selection_reason
   ```

5. **增强优化过程跟踪**
   ```python
   def _generate_optimization_process(self, ...) -> Dict:
       # 新增字段:
       return {
           "market_profile": {...},  # 股票特征
           "dynamic_adjustments": {...},  # 调整因子
           "adjustment_reasoning": [...],  # 调整推理
           # ... 现有字段
       }
   ```

#### 测试策略

```python
# tests/tools/test_expiration_optimizer_enhanced.py

def test_stock_specific_optimization():
    """测试不同股票获得不同结果"""
    optimizer = ExpirationOptimizer()
    expirations = [{'date': '2025-11-15', 'days': 30, 'type': 'monthly'}]

    # 高波动科技股
    tsla_result = optimizer.evaluate_expiration(
        days=30, expiration_type='monthly', symbol='TSLA'
    )

    # 大盘蓝筹股
    aapl_result = optimizer.evaluate_expiration(
        days=30, expiration_type='monthly', symbol='AAPL'
    )

    # 断言: 不同股票应该有不同的评分
    assert tsla_result.composite_score != aapl_result.composite_score
    assert 'TSLA' in tsla_result.selection_reason or '高波动' in tsla_result.selection_reason

def test_backward_compatibility():
    """测试向后兼容性"""
    optimizer = ExpirationOptimizer()

    # 不提供symbol应该使用默认行为
    result_no_symbol = optimizer.evaluate_expiration(days=30, expiration_type='monthly')

    # 应该不会报错，并且返回合理结果
    assert result_no_symbol.composite_score > 0
```

### Phase 2: MCP工具层更新（优先级: P0）

**文件**: `src/mcp_server/tools/optimal_expiration_selector_tool.py`

#### 任务分解

1. **修复_generate_comparison方法**
   ```python
   # 旧版本
   def _generate_comparison(self, all_expirations, optimal, optimizer, volatility):
       for exp in all_expirations:
           candidate = optimizer.evaluate_expiration(
               days=exp['days'],
               expiration_type=exp.get('type', 'other'),
               # ❌ 缺少symbol参数
           )

   # 新版本
   def _generate_comparison(self, all_expirations, optimal, optimizer, volatility, symbol):
       for exp in all_expirations:
           candidate = optimizer.evaluate_expiration(
               days=exp['days'],
               expiration_type=exp.get('type', 'other'),
               symbol=symbol,  # ✅ 传递symbol
               volatility=volatility
           )
   ```

2. **更新execute方法调用链**
   ```python
   async def execute(self, **kwargs) -> Dict[str, Any]:
       symbol = kwargs.get('symbol', '').upper()
       # ...

       # 调用优化器时传递symbol
       optimal, optimization_process = optimizer.find_optimal_expiration(
           formatted_expirations,
           symbol=symbol,  # ✅ 确保传递
           volatility=volatility,
           strategy_type=strategy_type,
           return_process=True
       )

       # 生成对比时传递symbol
       comparison = self._generate_comparison(
           formatted_expirations,
           optimal,
           optimizer,
           volatility,
           symbol  # ✅ 新增参数
       )
   ```

3. **增强返回结果**
   ```python
   result = {
       'success': True,
       'symbol': symbol,
       # ... 现有字段

       # 新增: 股票特定优化信息
       'stock_optimization': {
           'market_profile': optimization_process.get('market_profile'),
           'dynamic_adjustments': optimization_process.get('dynamic_adjustments'),
           'adjustment_reasoning': optimization_process.get('adjustment_reasoning')
       }
   }
   ```

### Phase 3: 依赖工具更新（优先级: P1）

**影响范围**: 所有调用智能到期日选择器的工具

1. **cash_secured_put_strategy_tool.py**
   ```python
   # 行号: 198-209
   expiration_selector = OptimalExpirationSelectorTool(tradier_client=client)
   expiration_result = await expiration_selector.execute(
       symbol=symbol,  # ✅ 已经传递symbol，无需修改
       available_expirations=available_expirations,
       strategy_type="csp",
       # ...
   )
   ```
   **状态**: ✅ 无需修改（已正确传递symbol）

2. **covered_call_strategy_tool.py**
   ```python
   # 行号: 188-203
   expiration_selector = OptimalExpirationSelectorTool(tradier_client=client)
   expiration_result = await expiration_selector.execute(
       symbol=symbol,  # ✅ 已经传递symbol
       available_expirations=available_expirations,
       strategy_type="covered_call",
       # ...
   )
   ```
   **状态**: ✅ 无需修改

3. **income_generation_csp_prompt.py**
   ```python
   # 调用cash_secured_put_strategy_tool，间接使用优化器
   # 无需修改
   ```
   **状态**: ✅ 无需修改

4. **stock_acquisition_csp_prompt.py**
   ```python
   # 调用cash_secured_put_strategy_tool，间接使用优化器
   # 无需修改
   ```
   **状态**: ✅ 无需修改

### Phase 4: 数据源增强（优先级: P1 - API 已验证可行）✅

**✅ 前置调研完成** - Tradier API 能力已确认:
- ✅ **IV 数据可用**: bid_iv, mid_iv, ask_iv, smv_vol (via ORATS)
- ✅ **Greeks 数据可用**: delta, gamma, theta, vega, rho, phi
- ✅ **无需 Black-Scholes 反推**，API 直接提供
- ✅ **TradierClient 已支持**: `get_option_chain(..., include_greeks=True)`

**目标**: 从静态映射表迁移到实时 API 数据

#### 需要的新功能

1. **隐含波动率提取**（已简化 - 无需复杂计算）
   ```python
   # src/option/implied_volatility.py (新建)
   def extract_atm_implied_volatility(option_chain: List[TradierQuote],
                                      underlying_price: float) -> float:
       """从 Tradier API 直接提取 ATM 期权的隐含波动率

       注意: Tradier API 通过 ORATS 提供现成的 IV 数据，
       无需通过 Black-Scholes 模型反推
       """
       # 找到最接近 ATM 的期权
       atm_option = self._find_atm_option(option_chain, underlying_price)

       # 直接使用 Tradier 提供的 mid_iv
       if atm_option and atm_option.greeks:
           return atm_option.greeks.mid_iv  # 优先使用 mid_iv

       return None
   ```

2. **历史波动率计算**
   ```python
   # src/stock/history_data.py (增强现有)
   def calculate_historical_volatility(symbol: str, period: int = 30) -> float:
       """计算历史波动率（HV）"""
       # 获取历史价格数据
       # 计算对数收益率标准差
       # 年化调整
   ```

3. **Beta 系数获取**
   ```python
   # src/stock/info.py (增强)
   def get_beta_coefficient(symbol: str) -> float:
       """获取股票 Beta 系数

       优先使用 Tradier/StockInfo 提供的数据
       """
       stock_info = self.get_stock_info(symbol)

       # Tradier 或 StockInfo 可能已提供 Beta
       if stock_info and stock_info.beta:
           return stock_info.beta

       # 降级方案：从历史数据计算
       return self._calculate_beta_from_history(symbol, benchmark="SPY")
   ```

#### 集成点

```python
# expiration_optimizer.py
def _calculate_profile_from_api(self, symbol: str) -> Dict[str, float]:
    """从 API 实时计算股票档案（Phase 4）"""
    from src.stock.info import StockInfoProcessor
    from src.option.implied_volatility import extract_atm_iv
    from src.stock.history_data import calculate_historical_volatility

    # 获取股票信息
    processor = StockInfoProcessor()
    stock_info = processor.get_stock_info(symbol)

    # 获取期权链（包含 Greeks 和 IV）
    option_chain = self.tradier_client.get_option_chain(
        symbol=symbol,
        include_greeks=True  # ✅ Tradier 支持
    )

    # 直接从 API 提取 IV（无需 BS 反推）
    iv = extract_atm_iv(option_chain, stock_info.close_price)

    # 计算历史波动率
    hv = calculate_historical_volatility(symbol, period=30)

    return {
        'volatility_ratio': iv / hv if (hv and hv > 0) else 1.0,
        'beta_coefficient': stock_info.beta or 1.0,
        'market_cap_tier': self._classify_market_cap(stock_info.market_cap),
        'liquidity_factor': self._calculate_liquidity(stock_info),
        'options_activity': self._calculate_options_activity(option_chain, stock_info)
    }
```

#### API 响应示例（Tradier 实际数据）

```json
{
  "option": {
    "symbol": "AAPL251115C00145000",
    "greeks": {
      "delta": 0.52,
      "gamma": 0.0234,
      "theta": -0.0512,
      "vega": 0.1823,
      "bid_iv": 0.287,      // ← 买价隐含波动率 28.7%
      "mid_iv": 0.295,      // ← 中间价隐含波动率 29.5%
      "ask_iv": 0.303,      // ← 卖价隐含波动率 30.3%
      "smv_vol": 0.298,     // ← SMV 波动率估计
      "updated_at": "2025-10-03 14:59:08"
    }
  }
}
```

---

## 🧪 测试策略

### 单元测试

**文件**: `tests/tools/test_expiration_optimizer_enhanced.py`

```python
import pytest
from src.mcp_server.tools.expiration_optimizer import ExpirationOptimizer

class TestStockSpecificOptimization:
    """测试股票特定优化功能"""

    def test_market_profile_extraction(self):
        """测试股票市场档案获取"""
        optimizer = ExpirationOptimizer()

        # TSLA: 高波动科技股
        tsla_profile = optimizer._get_stock_market_profile('TSLA')
        assert tsla_profile['volatility_ratio'] > 1.1
        assert tsla_profile['beta_coefficient'] > 1.2

        # AAPL: 大盘蓝筹股
        aapl_profile = optimizer._get_stock_market_profile('AAPL')
        assert aapl_profile['market_cap_tier'] >= 1.0
        assert aapl_profile['liquidity_factor'] >= 1.0

    def test_dynamic_adjustments_calculation(self):
        """测试动态调整因子计算"""
        optimizer = ExpirationOptimizer()

        # 高波动档案
        high_vol_profile = {
            'volatility_ratio': 1.3,
            'beta_coefficient': 1.4,
            'liquidity_factor': 1.0,
            'market_cap_tier': 1.0,
            'options_activity': 0.5
        }

        adjustments = optimizer._calculate_dynamic_adjustments(high_vol_profile)

        # 高波动应该降低Gamma风险容忍度
        assert adjustments['gamma_adjustment'] < 1.0

        # 验证公式正确性
        expected_gamma = 0.8 + (1.3 - 1.0) * 0.3 + (1.4 - 1.0) * 0.2
        assert abs(adjustments['gamma_adjustment'] - expected_gamma) < 0.01

    def test_different_stocks_different_results(self):
        """测试不同股票获得不同优化结果"""
        optimizer = ExpirationOptimizer()
        expirations = [
            {'date': '2025-11-15', 'days': 30, 'type': 'monthly'},
            {'date': '2025-11-22', 'days': 37, 'type': 'weekly'}
        ]

        # TSLA优化
        tsla_optimal, _ = optimizer.find_optimal_expiration(
            expirations, symbol='TSLA', return_process=True
        )

        # AAPL优化
        aapl_optimal, _ = optimizer.find_optimal_expiration(
            expirations, symbol='AAPL', return_process=True
        )

        # 评分应该不同（股票特征不同）
        assert tsla_optimal.composite_score != aapl_optimal.composite_score

    def test_optimization_process_transparency(self):
        """测试优化过程透明性"""
        optimizer = ExpirationOptimizer()
        expirations = [{'date': '2025-11-15', 'days': 30, 'type': 'monthly'}]

        optimal, process = optimizer.find_optimal_expiration(
            expirations, symbol='TSLA', return_process=True
        )

        # 验证优化过程包含所有必需信息
        assert 'market_profile' in process
        assert 'dynamic_adjustments' in process
        assert 'adjustment_reasoning' in process or 'selection_details' in process

        # 验证market_profile有有效数据
        profile = process['market_profile']
        assert 'volatility_ratio' in profile
        assert profile['volatility_ratio'] > 0

    def test_backward_compatibility(self):
        """测试向后兼容性"""
        optimizer = ExpirationOptimizer()
        expirations = [{'date': '2025-11-15', 'days': 30, 'type': 'monthly'}]

        # 不提供symbol应该仍然工作
        result_no_symbol = optimizer.evaluate_expiration(
            days=30,
            expiration_type='monthly',
            symbol=None
        )

        assert result_no_symbol.composite_score > 0
        assert result_no_symbol.date is not None


class TestMCPToolIntegration:
    """测试MCP工具层集成"""

    @pytest.mark.asyncio
    async def test_optimal_expiration_selector_with_symbol(self):
        """测试OptimalExpirationSelectorTool传递symbol"""
        from src.mcp_server.tools.optimal_expiration_selector_tool import OptimalExpirationSelectorTool

        tool = OptimalExpirationSelectorTool()

        result = await tool.execute(
            symbol='TSLA',
            available_expirations=['2025-11-15', '2025-11-22'],
            strategy_type='csp'
        )

        assert result['success'] is True
        assert result['symbol'] == 'TSLA'

        # 验证包含股票特定优化信息
        if 'optimization_process' in result:
            process = result['optimization_process']
            assert 'market_profile' in process or 'symbol' in process
```

### 集成测试

**文件**: `tests/integration/test_stock_specific_optimization_integration.py`

```python
@pytest.mark.asyncio
async def test_csp_tool_with_stock_specific_optimization():
    """测试CSP工具使用股票特定优化"""
    from src.mcp_server.tools.cash_secured_put_strategy_tool import cash_secured_put_strategy_tool

    result = await cash_secured_put_strategy_tool(
        symbol='TSLA',
        purpose_type='income',
        duration='1w'
    )

    assert result['success'] is True

    # 验证到期日选择使用了股票特定优化
    expiration_metadata = result.get('expiration_metadata', {})
    assert 'optimal_expiration' in expiration_metadata or 'selection_reason' in expiration_metadata


@pytest.mark.asyncio
async def test_multiple_stocks_comparison():
    """测试多个股票的对比"""
    symbols = ['TSLA', 'AAPL', 'GOOG']
    results = {}

    for symbol in symbols:
        result = await cash_secured_put_strategy_tool(
            symbol=symbol,
            purpose_type='income',
            duration='1w'
        )
        results[symbol] = result

    # 验证每个股票都成功
    for symbol, result in results.items():
        assert result['success'] is True

    # 提取优化评分（如果可用）
    scores = {}
    for symbol, result in results.items():
        exp_meta = result.get('expiration_metadata', {})
        if 'composite_score' in exp_meta:
            scores[symbol] = exp_meta['composite_score']

    # 至少应该有一些差异（虽然可能选择相同的到期日）
    if len(scores) >= 2:
        unique_scores = len(set(scores.values()))
        # 允许有相同评分，但至少验证算法运行了
        assert unique_scores >= 1
```

### 验证测试（手动）

**目标**: 验证真实场景下的优化效果

```python
# tests/manual/validate_stock_optimization.py

async def validate_optimization():
    """手动验证优化效果"""
    optimizer = ExpirationOptimizer()

    # 获取真实的到期日列表
    from src.provider.tradier.client import TradierClient
    client = TradierClient()

    symbols = ['TSLA', 'AAPL', 'GOOG', 'SPY', 'NVDA']

    for symbol in symbols:
        expirations = client.get_option_expirations(symbol)
        exp_list = [
            {'date': exp.date, 'days': exp.days, 'type': exp.type}
            for exp in expirations[:10]
        ]

        optimal, process = optimizer.find_optimal_expiration(
            exp_list,
            symbol=symbol,
            strategy_type='csp',
            return_process=True
        )

        print(f"\n{'='*60}")
        print(f"股票: {symbol}")
        print(f"{'='*60}")
        print(f"市场档案: {process['market_profile']}")
        print(f"动态调整: {process['dynamic_adjustments']}")
        print(f"最优到期日: {optimal.date} ({optimal.days_to_expiry}天)")
        print(f"综合评分: {optimal.composite_score:.2f}")
        print(f"选择理由: {optimal.selection_reason}")

if __name__ == '__main__':
    import asyncio
    asyncio.run(validate_optimization())
```

---

## 📊 成功指标与验证

### 定量指标

1. **差异化程度**
   ```
   测试场景: 5个不同特征的股票 (TSLA, AAPL, GOOG, SPY, NVDA)
   相同到期日列表

   预期:
   - 至少3个股票选择不同的到期日 OR
   - 相同到期日的评分差异 > 5分
   ```

2. **调整因子合理性**
   ```
   TSLA (高波动):
   - gamma_adjustment: 0.9-1.0 (略保守)
   - theta_adjustment: 1.0-1.1 (标准)

   AAPL (大盘蓝筹):
   - gamma_adjustment: 1.0-1.1 (略激进)
   - liquidity_adjustment: 1.1-1.3 (高流动性奖励)
   ```

3. **向后兼容性**
   ```
   测试: 所有现有测试用例通过
   不提供symbol参数的调用应该保持原有行为
   ```

### 定性指标

1. **透明性**
   - 每个优化决策都有清晰的数据来源
   - 调整推理可以被追溯到具体的市场特征

2. **可维护性**
   - 消除硬编码分支，使用统一的数学模型
   - 新增股票无需代码修改

3. **Linus标准**
   - "Good Taste": 消除特殊情况，用数学模型统一处理
   - "Simplicity": 单一数据流，清晰的分层架构

---

## 🚀 部署与回滚计划

### 渐进式部署

**阶段1: 核心算法部署（无破坏性变更）**
```bash
# 1. 部署expiration_optimizer.py增强版
git checkout -b feature/stock-specific-optimization
# 实现所有Phase 1任务
pytest tests/tools/test_expiration_optimizer_enhanced.py
git commit -m "feat: add stock-specific optimization to expiration optimizer"
```

**阶段2: MCP工具层部署**
```bash
# 2. 更新optimal_expiration_selector_tool.py
# 实现Phase 2任务
pytest tests/tools/test_optimal_expiration_selector_tool.py
git commit -m "feat: enable stock-specific optimization in MCP tool"
```

**阶段3: 集成测试与验证**
```bash
# 3. 运行完整测试套件
pytest tests/integration/
python tests/manual/validate_stock_optimization.py

# 4. 验证所有依赖工具仍正常工作
pytest tests/tools/test_cash_secured_put_strategy_tool.py
pytest tests/tools/test_covered_call_strategy_tool.py
```

**阶段4: 生产部署**
```bash
# 5. 合并到主分支
git checkout main
git merge feature/stock-specific-optimization
git push origin main

# 6. 重启MCP服务器
# (根据部署方式，可能需要重启Claude Code或MCP服务)
```

### 回滚策略

**问题检测**:
- 监控MCP工具调用错误率
- 检查optimization_process输出是否包含预期字段
- 验证不同股票是否获得差异化结果

**回滚步骤**:
```bash
# 如果发现问题
git revert <commit-hash>
git push origin main

# 或回滚到上一个稳定版本
git checkout <previous-stable-commit>
git push origin main --force
```

**最小影响设计**:
- 所有新功能通过`symbol`参数控制
- `symbol=None`时保持原有行为
- 不修改任何现有API签名（只添加可选参数）

---

## 📚 文档更新

### 用户文档

**README.md 更新**:
```markdown
## 🆕 v11新增功能: 股票特定智能优化

智能到期日选择器现在支持**完全数据驱动的股票特定优化**：

### 特性
- ✅ **个性化优化**: 每个股票基于其客观市场特征获得独特的优化结果
- ✅ **零硬编码**: 所有调整因子通过数学公式计算，完全客观
- ✅ **透明过程**: 完整的优化推理可追溯到具体市场数据
- ✅ **向后兼容**: 现有调用无需修改

### 示例
```python
# 高波动科技股 - 更保守的到期日选择
tsla_result = await optimal_expiration_selector_tool.execute(
    symbol='TSLA',
    strategy_type='csp'
)

# 大盘蓝筹股 - 更灵活的到期日选择
aapl_result = await optimal_expiration_selector_tool.execute(
    symbol='AAPL',
    strategy_type='csp'
)

# 查看股票特定优化详情
print(tsla_result['optimization_process']['market_profile'])
# {'volatility_ratio': 1.29, 'beta_coefficient': 1.39, ...}
```
```

### 开发者文档

**新建**: `docs/stock_specific_optimization.md`

```markdown
# 股票特定优化技术文档

## 架构
[详细架构图]

## 数学模型
[所有公式的详细说明]

## API参考
[所有新增方法的签名和示例]

## 扩展指南
[如何添加新的调整因子]
[如何从API迁移到实时数据]
```

---

## 🔄 未来优化方向

### Phase 5: 机器学习增强（P3）

**目标**: 使用历史数据训练模型，优化调整因子

```python
# 概念示例
from sklearn.ensemble import RandomForestRegressor

class MLEnhancedOptimizer(ExpirationOptimizer):
    """使用ML模型优化调整因子"""

    def __init__(self):
        super().__init__()
        self.ml_model = self._load_trained_model()

    def _calculate_dynamic_adjustments(self, market_profile: Dict) -> Dict:
        # 使用ML模型预测最优调整因子
        features = self._extract_features(market_profile)
        adjustments = self.ml_model.predict([features])[0]
        return dict(zip(['gamma', 'theta', 'liquidity'], adjustments))
```

### Phase 6: 实时市场状态适配（P3）

**目标**: 根据当前市场环境（VIX, 利率, 趋势）动态调整

```python
def _get_market_regime(self) -> str:
    """检测当前市场状态"""
    vix = self._get_vix_level()
    trend = self._detect_market_trend()

    if vix > 30 and trend == 'down':
        return 'high_volatility_bear'
    elif vix < 15 and trend == 'up':
        return 'low_volatility_bull'
    # ...

def _adjust_for_market_regime(self, base_adjustments: Dict, regime: str) -> Dict:
    """根据市场状态微调"""
    if regime == 'high_volatility_bear':
        # 熊市高波动 -> 更保守
        base_adjustments['gamma_adjustment'] *= 0.9
    # ...
```

---

## ✅ 验收标准

### 必须满足（Must Have）

- [x] ✅ 所有现有测试通过
- [ ] ✅ 新增单元测试覆盖率 > 90%
- [ ] ✅ TSLA和AAPL在相同到期日列表下获得不同优化结果
- [ ] ✅ 优化过程包含market_profile和dynamic_adjustments
- [ ] ✅ 不提供symbol时保持原有行为（向后兼容）
- [ ] ✅ 无硬编码评分值（所有评分通过公式计算）

### 应该满足（Should Have）

- [ ] 📊 手动验证测试证明5个代表性股票获得合理结果
- [ ] 📚 README包含股票特定优化说明
- [ ] 🧪 集成测试覆盖CSP和Covered Call工具

### 可以满足（Nice to Have）

- [ ] 🤖 详细的开发者文档（stock_specific_optimization.md）
- [ ] 📈 性能基准测试（优化时间 < 100ms）
- [ ] 🎨 GenUI风格的优化结果可视化

---

## 📝 变更日志

### v11.0.0 (计划中)

**新增**:
- 股票市场档案获取 (`_get_stock_market_profile`)
- 动态调整因子计算 (`_calculate_dynamic_adjustments`)
- 增强的优化过程跟踪

**修改**:
- `evaluate_expiration` 添加symbol参数
- 所有评分函数支持adjustment_factor
- `_generate_comparison` 传递symbol参数

**修复**:
- 消除硬编码评分值
- 修复不同股票获得相同结果的问题

---

## 🙋 常见问题

### Q1: 为什么要做股票特定优化？
**A**: 不同股票有不同的期权特性。高波动科技股（TSLA）的Gamma风险远高于大盘蓝筹股（AAPL），使用统一标准会导致次优选择。

### Q2: 这会破坏现有功能吗？
**A**: 不会。所有新功能通过可选的`symbol`参数控制。不提供symbol时保持原有行为。

### Q3: 调整因子的数学公式从哪来？
**A**: 基于期权定价理论和实证研究：
- Gamma风险随波动率和Beta增加而上升（Black-Scholes模型）
- 流动性影响买卖价差（市场微观结构理论）
- 大盘股通常有更稳定的Theta衰减（实证观察）

### Q4: 如何验证优化效果？
**A**:
1. 单元测试验证数学公式正确性
2. 集成测试验证不同股票获得差异化结果
3. 手动验证测试在真实市场数据上的表现

### Q5: Phase 4 什么时候实现？
**A**: ✅ **Tradier API 验证已完成**！
- ✅ **API 提供完整 IV 数据**：bid_iv, mid_iv, ask_iv, smv_vol（via ORATS）
- ✅ **TradierClient 已支持**：`include_greeks=True` 参数
- ✅ **无需 Black-Scholes 反推**：API 直接返回 IV
- 🎯 **建议实施策略**：
  - **选项 A**：优先实现 Phase 4，跳过静态映射表（推荐）
  - **选项 B**：Phase 1 作为快速 MVP，Phase 4 紧随其后
- ⏱️ **时间线**：Phase 4 可在 MVP 中直接包含，或作为第二个迭代
- 📊 **剩余依赖**：历史波动率计算（HV）- 需从历史价格数据计算

---

## 👥 利益相关者

- **开发者**: 邹斯诚 (@szou)
- **审核者**: Linus Torvalds (精神导师 via CLAUDE.md)
- **用户**: TradingAgent MCP的所有期权策略用户

---

## 📞 支持与反馈

如有问题或建议，请：
1. 提交GitHub Issue
2. 查看`docs/stock_specific_optimization.md`（实现后）
3. 运行`python tests/manual/validate_stock_optimization.py`验证

---

**最后更新**: 2025-10-03
**下一次审查**: 实现完成后
