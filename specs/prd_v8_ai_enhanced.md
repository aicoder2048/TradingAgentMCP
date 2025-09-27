# PRD v8: 期权被行权概率MCP服务器工具 - AI增强版

## 📋 产品概述

### 产品名称
期权被行权概率计算MCP服务器工具 (Option Assignment Probability MCP Server Tool)

### 版本信息
- **版本**: v8.0
- **类型**: AI 增强 PRD 
- **创建日期**: 2024-09-27
- **状态**: 实施规划阶段

### 项目背景
当前TradingAgent MCP服务器中的期权策略工具（现金保障看跌和Covered Call）使用Delta值近似计算被行权概率，这种方法在某些市场条件下精度不足。本PRD旨在实现基于Black-Scholes模型的精确被行权概率计算，提升策略分析的准确性和可靠性。

## 🎯 产品目标

### 主要目标
1. **替换Delta近似**: 将现有策略工具中的`assignment_probability = abs(delta) * 100`替换为Black-Scholes精确计算
2. **新增独立工具**: 创建专门的被行权概率计算MCP工具
3. **向后兼容**: 确保现有API接口和功能不受影响
4. **性能优化**: 提供批量计算和比较分析功能

### 成功指标
- 被行权概率计算精度提升 > 15%
- 现有策略工具成功集成新算法
- 新MCP工具通过所有测试用例
- API响应时间 < 2秒

## 🏗️ 技术架构设计

### 核心模块架构

```
src/
├── option/
│   ├── assignment_probability.py      # 新增：被行权概率计算器
│   ├── greeks_enhanced.py            # 现有：复用BlackScholesCalculator
│   └── options_chain.py              # 现有：期权链处理
├── mcp_server/
│   ├── tools/
│   │   ├── option_assignment_probability_tool.py  # 新增：MCP工具
│   │   ├── cash_secured_put_strategy_tool.py      # 更新：集成新算法
│   │   └── covered_call_strategy_tool.py          # 更新：集成新算法
└── strategy/
    ├── cash_secured_put.py            # 更新：使用新概率计算
    └── covered_call.py                # 更新：使用新概率计算
```

### 数据流设计

```
Tradier API → Option Data → Assignment Probability Calculator → Strategy Tools
                                                               ↓
                                                       Enhanced Recommendations
```

## 📊 功能规格说明

### 1. 核心被行权概率计算器 (`src/option/assignment_probability.py`)

#### 1.1 主要功能类

```python
class OptionAssignmentCalculator:
    """期权被行权概率精确计算器"""
    
    def calculate_assignment_probability(
        self,
        underlying_price: float,
        strike_price: float,
        time_to_expiry_days: float,
        implied_volatility: float,
        risk_free_rate: float = 0.048,
        option_type: str = "put"
    ) -> Dict[str, Any]
    
    def compare_with_delta_approximation(
        self,
        underlying_price: float,
        strike_price: float,
        time_to_expiry_days: float,
        implied_volatility: float,
        delta_value: float,
        risk_free_rate: float = 0.048,
        option_type: str = "put"
    ) -> Dict[str, Any]
    
    def batch_calculate_portfolio_risk(
        self,
        positions: List[Dict[str, Any]]
    ) -> Dict[str, Any]
```

#### 1.2 算法规格

**Black-Scholes被行权概率公式**:
- **看跌期权**: `P(S_T < K) = N(-d2)`
- **看涨期权**: `P(S_T > K) = N(d2)`

其中:
```
d2 = d1 - σ√T
d1 = [ln(S/K) + (r + σ²/2)T] / (σ√T)
```

**参数定义**:
- S: 标的资产当前价格
- K: 期权行权价格  
- T: 距离到期时间（年）
- σ: 隐含波动率（年化）
- r: 无风险利率
- N(): 标准正态累积分布函数

### 2. 新增MCP工具 (`src/mcp_server/tools/option_assignment_probability_tool.py`)

#### 2.1 工具接口设计

```python
@mcp.tool()
async def option_assignment_probability_tool(
    symbol: str,
    strike_price: float,
    expiration: str,
    option_type: str = "put",
    include_delta_comparison: bool = True
) -> Dict[str, Any]
```

#### 2.2 返回数据结构

```json
{
    "symbol": "AAPL",
    "current_price": 150.25,
    "strike_price": 145.00,
    "option_type": "PUT",
    "expiration": "2024-01-19",
    "days_to_expiry": 4,
    "calculation_timestamp": "2024-01-15 14:30:00 ET",
    "black_scholes_calculation": {
        "assignment_probability": 0.2847,
        "assignment_probability_percent": "28.47%",
        "expire_otm_probability": 0.7153,
        "expire_otm_probability_percent": "71.53%",
        "risk_level": "中等",
        "moneyness": "虚值",
        "moneyness_ratio": 1.0362,
        "d1": 0.8234,
        "d2": 0.7892,
        "calculation_method": "Black-Scholes精确计算"
    },
    "delta_comparison": {
        "delta_approximation": 0.32,
        "delta_approximation_percent": "32.00%",
        "absolute_difference": 0.0353,
        "relative_difference_percent": 12.4,
        "accuracy_assessment": "中等精度",
        "recommendation": "建议使用精确计算"
    },
    "risk_analysis": {
        "assignment_risk_level": "中等",
        "risk_explanation": "基于当前参数，该期权的被行权风险评级为：中等",
        "moneyness_explanation": "当前期权状态为：虚值（股价/行权价比率：1.0362）"
    },
    "market_context": {
        "implied_volatility": 0.23,
        "implied_volatility_percent": "23.00%", 
        "risk_free_rate": 0.048,
        "time_value_remaining": 0.0110
    },
    "csv_export_path": "./data/assignment_prob_AAPL_145P_20240115.csv",
    "status": "success"
}
```

### 3. 现有工具集成更新

#### 3.1 Cash Secured Put策略工具更新

**当前代码** (`src/strategy/cash_secured_put.py:line 181`):
```python
# 原有Delta近似
assignment_probability = abs(delta) * 100
```

**更新后代码**:
```python
# 使用精确Black-Scholes计算
from src.option.assignment_probability import OptionAssignmentCalculator

assignment_calc = OptionAssignmentCalculator()
assignment_result = assignment_calc.calculate_assignment_probability(
    underlying_price=underlying_price,
    strike_price=strike,
    time_to_expiry_days=days_to_expiry,
    implied_volatility=implied_vol,
    option_type="put"
)
assignment_probability = assignment_result["assignment_probability"] * 100
```

#### 3.2 Covered Call策略工具更新

**当前代码** (`src/strategy/covered_call.py`):
```python
# 原有Delta近似
assignment_probability = delta * 100  # Delta近似为分配概率
```

**更新后代码**:
```python
# 使用精确Black-Scholes计算
assignment_result = assignment_calc.calculate_assignment_probability(
    underlying_price=underlying_price,
    strike_price=strike,
    time_to_expiry_days=days_to_expiry,
    implied_volatility=implied_vol,
    option_type="call"
)
assignment_probability = assignment_result["assignment_probability"] * 100
```

## 🔧 实施计划

### 阶段1: 核心计算器开发 (2-3天)

#### 任务1.1: 创建被行权概率计算模块
- **文件**: `src/option/assignment_probability.py`
- **依赖**: 复用`src/option/greeks_enhanced.py`中的`BlackScholesCalculator`
- **功能**: 
  - 实现`OptionAssignmentCalculator`类
  - 集成参考实现的算法逻辑
  - 添加风险等级评估
  - 支持单次和批量计算

#### 任务1.2: 单元测试开发
- **文件**: `tests/option/test_assignment_probability.py`
- **覆盖**: 
  - 边界条件测试
  - 精度验证测试
  - 与Delta近似的比较测试
  - 批量计算性能测试

### 阶段2: MCP工具实现 (1-2天)

#### 任务2.1: 创建MCP工具
- **文件**: `src/mcp_server/tools/option_assignment_probability_tool.py`
- **功能**:
  - 实现独立的被行权概率计算MCP工具
  - 支持单个期权和批量分析
  - 包含Delta比较分析
  - CSV数据导出功能

#### 任务2.2: 服务器注册
- **文件**: `src/mcp_server/server.py`
- **更新**: 注册新的MCP工具到FastMCP服务器

### 阶段3: 现有工具集成 (2-3天)

#### 任务3.1: 更新现金保障看跌策略
- **文件**: `src/strategy/cash_secured_put.py`
- **更新**: `CashSecuredPutAnalyzer.calculate_strategy_metrics()`方法
- **向后兼容**: 保持现有API接口不变

#### 任务3.2: 更新Covered Call策略
- **文件**: `src/strategy/covered_call.py`
- **更新**: 相应的策略计算方法
- **测试**: 确保推荐结果的一致性

### 阶段4: 测试与优化 (1-2天)

#### 任务4.1: 集成测试
- **测试**: 端到端MCP工具调用
- **验证**: 策略工具输出正确性
- **性能**: API响应时间优化

#### 任务4.2: 文档更新
- **README**: 更新工具说明
- **API文档**: 添加新工具规格
- **示例**: 提供使用示例

## 📈 API接口规格

### 新增MCP工具

```python
# 工具名称: option_assignment_probability_tool
# 描述: 计算期权被行权概率的专业工具

@mcp.tool()
async def option_assignment_probability_tool(
    symbol: str,                           # 必需: 股票代码
    strike_price: float,                   # 必需: 期权行权价格
    expiration: str,                       # 必需: 到期日 YYYY-MM-DD
    option_type: str = "put",             # 可选: "put" 或 "call"
    include_delta_comparison: bool = True, # 可选: 是否包含Delta比较
    risk_free_rate: float = 0.048         # 可选: 无风险利率
) -> Dict[str, Any]
```

### 现有工具增强

**现金保障看跌策略工具**增强输出:
```json
{
    "recommendations": {
        "conservative": {
            "risk_metrics": {
                "assignment_probability": 0.1847,      // 精确Black-Scholes计算
                "assignment_probability_method": "Black-Scholes",
                "delta_approximation": 0.21,           // 保留Delta近似用于比较
                "probability_accuracy_improvement": "13.2%"
            }
        }
    }
}
```

## 🧪 测试策略

### 单元测试

#### 核心算法测试
```python
class TestOptionAssignmentCalculator:
    def test_put_assignment_probability_calculation(self):
        """测试看跌期权被行权概率计算"""
        
    def test_call_assignment_probability_calculation(self):
        """测试看涨期权被行权概率计算"""
        
    def test_delta_comparison_accuracy(self):
        """测试与Delta近似的精度比较"""
        
    def test_edge_cases(self):
        """测试边界条件"""
        
    def test_batch_calculation_performance(self):
        """测试批量计算性能"""
```

#### MCP工具测试
```python
class TestOptionAssignmentProbabilityTool:
    def test_mcp_tool_response_format(self):
        """测试MCP工具响应格式"""
        
    def test_tradier_api_integration(self):
        """测试Tradier API集成"""
        
    def test_csv_export_functionality(self):
        """测试CSV导出功能"""
```

### 集成测试

#### 策略工具集成测试
```python
class TestStrategyToolsIntegration:
    def test_csp_strategy_with_new_probability(self):
        """测试CSP策略使用新概率计算"""
        
    def test_covered_call_strategy_integration(self):
        """测试Covered Call策略集成"""
        
    def test_recommendation_consistency(self):
        """测试推荐结果一致性"""
```

### 性能测试

#### 基准测试目标
- 单次概率计算: < 50ms
- 批量100个期权计算: < 2s
- MCP工具端到端响应: < 2s
- 内存使用: < 100MB

## 🔍 质量保证

### 代码质量标准
- **测试覆盖率**: > 90%
- **类型提示**: 100%覆盖
- **文档字符串**: 所有公共方法
- **错误处理**: 全面的异常捕获和日志记录

### 数据验证
- **输入验证**: 所有参数范围检查
- **输出验证**: 概率值在[0,1]范围内
- **边界情况**: 到期日、零波动率等特殊情况

### 向后兼容性
- **API接口**: 现有工具接口保持不变
- **响应格式**: 新增字段，不删除现有字段
- **性能**: 不降低现有工具性能

## 📊 预期收益

### 定量收益
- **计算精度提升**: 15-30%（基于Black-Scholes vs Delta比较）
- **风险评估准确性**: 提升20%以上
- **用户决策支持**: 更可靠的概率数据

### 定性收益
- **专业性增强**: 使用机构级计算方法
- **竞争优势**: 相比简单Delta近似的优势
- **用户信任**: 提供算法透明度和比较分析

## 🚀 部署计划

### 开发环境部署
1. **创建特性分支**: `feature/assignment-probability-v8`
2. **开发环境测试**: 完成所有单元测试和集成测试
3. **代码审查**: 团队代码审查和优化

### 生产环境部署
1. **渐进式发布**: 首先在内部环境验证
2. **A/B测试**: 对比新旧算法结果
3. **监控部署**: 性能和错误监控
4. **文档发布**: 更新用户文档和API规格

## 📋 验收标准

### 功能验收
- [ ] 新增`OptionAssignmentCalculator`类通过所有单元测试
- [ ] 新增MCP工具`option_assignment_probability_tool`正常工作
- [ ] 现有CSP和Covered Call策略工具成功集成新算法
- [ ] 所有API接口保持向后兼容
- [ ] CSV导出功能正常工作

### 性能验收
- [ ] 单次概率计算响应时间 < 50ms
- [ ] MCP工具端到端响应时间 < 2s
- [ ] 内存使用合理（< 100MB）
- [ ] 没有性能回归

### 质量验收
- [ ] 代码测试覆盖率 > 90%
- [ ] 所有边界条件正确处理
- [ ] 错误处理和日志记录完善
- [ ] 文档完整且准确

## 📝 风险评估与缓解

### 技术风险
**风险**: Black-Scholes模型在极端市场条件下的适用性
**缓解**: 提供Delta比较和警告机制，保留原有算法作为备选

**风险**: 性能影响
**缓解**: 实施性能基准测试，优化计算算法

### 集成风险
**风险**: 现有工具集成复杂性
**缓解**: 逐步集成，充分测试，保持向后兼容

**风险**: Tradier API数据质量
**缓解**: 数据验证和错误处理机制

## 🔮 未来扩展计划

### v8.1 增强功能
- **多资产支持**: 期货期权、外汇期权
- **高级模型**: Binomial、Monte Carlo模拟
- **实时监控**: 投资组合被行权风险实时监控

### v9.0 路线图
- **机器学习集成**: 基于历史数据的概率预测模型
- **风险管理**: 动态对冲建议
- **可视化工具**: 概率分布图表和热力图

---

## 📞 联系信息

**产品负责人**: TradingAgent MCP团队  
**技术负责人**: 期权策略开发组  
**创建时间**: 2024-09-27  
**文档版本**: v8.0-ai-enhanced  

---

*本PRD文档为AI增强版，包含详细的技术实施指导和全面的质量保证计划。*