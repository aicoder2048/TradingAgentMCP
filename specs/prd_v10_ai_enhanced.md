# PRD v10: Stock Acquisition CSP Engine MCP Server Prompt

## Executive Summary

本PRD规定了股票建仓现金担保看跌期权引擎MCP服务器提示的详细实现计划。该提示专门为**股票获取策略**设计，与现有的**收入生成策略**形成互补对比。核心目标是通过期权分配以折扣价建立优质股票头寸，而非专注于收取权利金。

### 战略差异对比

| 维度 | 收入生成CSP引擎 | 股票建仓CSP引擎 (本PRD) |
|------|-----------------|-------------------------|
| **主要目标** | 收取权利金，避免分配 | 获得股票，欢迎分配 |
| **Delta范围** | 0.10~0.30 (低概率) | 0.30~0.50 (高概率) |
| **年化目标** | ≥50%（激进收益） | 15~35%（合理补偿） |
| **持仓期限** | 7~28天（快周转） | 21~60天（耐心等待） |
| **股票选择** | 高IV，流动性优先 | 基本面优质，估值合理 |
| **分配态度** | 尽量避免 | 积极欢迎 |

---

## 1. Problem Statement

### 1.1 核心问题
现有的 `income_generation_csp_engine` 提示专注于权利金收取，采用低Delta策略避免股票分配。然而，许多投资者希望通过现金担保看跌期权以折扣价获得优质股票头寸，这需要截然不同的策略方法。

### 1.2 用户需求场景
- **长期价值投资者**: 希望以折扣价建立优质股票头寸
- **股票积累策略**: 愿意承担分配风险换取更低的有效购买价格
- **轮式期权策略**: 建仓-分配-covered call循环策略的起点
- **低估值机会**: 在市场回调时建立心仪股票头寸

### 1.3 现有解决方案的局限性
1. **income_generation_csp_engine**: 专注避免分配，不适合股票获取
2. **cash_secured_put_strategy_tool**: 支持"discount"模式但缺乏专用引导提示
3. **缺乏股票建仓专用工作流**: 没有面向分配欢迎的结构化策略引擎

---

## 2. Technical Objectives

### 2.1 功能目标
- 创建专门的股票建仓CSP引擎MCP提示
- 提供完整的股票获取导向工作流
- 整合现有工具但优化参数配置
- 生成专业的建仓执行计划

### 2.2 性能目标
- **分配概率**: 目标65%分配概率（vs收入策略的<30%）
- **年化补偿**: 15-35%合理等待成本（vs收入策略的≥50%）
- **持仓期限**: 21-60天耐心建仓（vs收入策略的7-28天）
- **股票质量**: 基本面健康+估值合理优先

### 2.3 集成目标
- 复用现有MCP工具生态
- 遵循现有提示架构模式
- 与收入生成引擎形成差异化互补
- 支持后续covered call策略连接

---

## 3. Architecture Design

### 3.1 核心架构模式

基于现有 `income_generation_csp_prompt.py` 的成功模式，采用以下架构：

```python
# 文件: src/mcp_server/prompts/stock_acquisition_csp_prompt.py

async def stock_acquisition_csp_engine(
    tickers: str,
    cash_usd: float,
    target_allocation_probability: float = 65.0,
    max_single_position_pct: float = 25.0,
    min_days: int = 21,
    max_days: int = 60,
    target_annual_return_pct: float = 25.0,
    preferred_sectors: Optional[str] = None,
) -> str:
    """
    股票建仓现金担保看跌期权策略引擎
    """
```

### 3.2 参数设计差异

| 参数 | 收入生成引擎 | 股票建仓引擎 | 差异说明 |
|------|-------------|-------------|----------|
| `min_days` | 7 | 21 | 更长期的建仓视角 |
| `max_days` | 28 | 60 | 允许更充分的价格调整 |
| `target_apy_pct` | 50 | 25 | 合理的等待成本补偿 |
| `min_winrate_pct` | 70 | 35 | 欢迎分配，"败率"即成功 |
| `新增: target_allocation_probability` | N/A | 65 | 期望分配概率 |
| `新增: max_single_position_pct` | N/A | 25 | 单股票仓位控制 |

### 3.3 工具调用策略

**关键差异**: 在调用 `cash_secured_put_strategy_tool_mcp` 时使用 `purpose_type="discount"`

```python
# 核心工具调用配置
cash_secured_put_strategy_tool_mcp(
    symbol=target_symbol,
    purpose_type="discount",  # 关键！股票获取模式
    duration=duration_mapping,
    capital_limit=position_limit,
    include_order_blocks=True,
    min_premium=None,  # 不限制最小权利金
    max_delta=-0.30   # 允许更高Delta
)
```

---

## 4. Implementation Plan

### 4.1 Phase 1: 核心提示引擎开发

#### 4.1.1 文件创建
```bash
# 目标文件
src/mcp_server/prompts/stock_acquisition_csp_prompt.py
```

#### 4.1.2 核心函数实现
```python
async def stock_acquisition_csp_engine(
    tickers: str,
    cash_usd: float,
    target_allocation_probability: float = 65.0,
    max_single_position_pct: float = 25.0,
    min_days: int = 21,
    max_days: int = 60,
    target_annual_return_pct: float = 25.0,
    preferred_sectors: Optional[str] = None,
) -> str:
    """股票建仓CSP策略引擎"""
    
    # 1. 参数解析和验证（复用income引擎模式）
    tickers_list = _parse_tickers_input(tickers)
    validation_result = _validate_stock_acquisition_parameters(...)
    
    # 2. 生成结构化提示
    prompt = _generate_stock_acquisition_prompt(...)
    
    return prompt
```

#### 4.1.3 辅助函数开发
```python
def _validate_stock_acquisition_parameters(...) -> Dict[str, Any]:
    """股票建仓参数验证"""
    
def _generate_stock_acquisition_prompt(...) -> str:
    """生成股票建仓结构化提示"""
    
def _get_duration_from_days(min_days: int, max_days: int) -> str:
    """天数范围转duration参数"""
    
def get_stock_acquisition_examples() -> Dict[str, Any]:
    """获取股票建仓策略使用示例"""
```

### 4.2 Phase 2: 提示内容架构

#### 4.2.1 主要工作流序列

```markdown
# 🏗️ 股票建仓现金担保PUT引擎

## ⚠️ 关键执行原则
**股票获取优先策略 - 欢迎股票分配**:
- 🎯 **核心目标**: 以折扣价获得优质股票，权利金为次要考虑
- 📊 **Delta范围**: 偏好 0.30~0.50 (目标分配概率65%)
- ⏰ **耐心建仓**: 21-60天期权，给股价充分调整时间
- 💰 **合理补偿**: 年化收益15-35%，作为等待成本补偿

## 🔄 强制执行序列

### 第一步: 时间基准验证
get_market_time_tool()

### 第二步: 股票基本面分析
stock_info_tool(symbol=primary_ticker)
stock_history_tool(symbol=primary_ticker, date_range="6m", interval="daily")

### 第三步: 股票建仓导向CSP策略
cash_secured_put_strategy_tool_mcp(
    symbol=primary_ticker,
    purpose_type="discount",  # 关键：股票获取模式
    duration=duration_mapping,
    capital_limit=position_limit,
    include_order_blocks=True,
    max_delta=-0.30  # 允许更高Delta获取分配
)

### 第四步: 期权链深度分析
options_chain_tool_mcp(...)

### 第五步: 分配概率验证
option_assignment_probability_tool_mcp(...)

### 第六步: 投资组合配置优化
portfolio_optimization_tool_mcp_tool(...)
```

#### 4.2.2 股票筛选标准

```markdown
## 🎯 股票建仓专用筛选标准

### 一级筛选：基本面健康度
- **财务健康**: ROE ≥ 15%，负债率 ≤ 40%，现金流为正
- **盈利稳定性**: 近5年连续盈利，增长率 ≥ 5%
- **市场地位**: 行业前5，市值 ≥ 500亿美元
- **分红历史**: 稳定分红记录（加分项）

### 二级筛选：估值合理性
- **PE估值**: 当前PE ≤ 5年平均PE × 1.2
- **PB估值**: PB ≤ 行业平均 × 1.5
- **PEG比率**: PEG ≤ 1.5

### 三级筛选：技术面确认
- **趋势位置**: 股价接近50日或200日均线支撑
- **RSI水平**: 30 ≤ RSI ≤ 65
- **成交量确认**: 近期成交量正常
- **支撑位强度**: 目标行权价接近关键技术支撑位

### 四级评分：建仓优先级
1. **分配概率** (40%权重): 目标Delta 0.35~0.45为满分
2. **价值折扣** (35%权重): 行权价相对当前价格的折扣幅度
3. **基本面质量** (25%权重): 财务健康度评分
```

### 4.3 Phase 3: MCP服务器集成

#### 4.3.1 服务器注册
```python
# 在 src/mcp_server/server.py 中注册新提示

@mcp.prompt()
async def stock_acquisition_csp_engine(
    tickers: str,
    cash_usd: float,
    target_allocation_probability: float = 65.0,
    max_single_position_pct: float = 25.0,
    min_days: int = 21,
    max_days: int = 60,
    target_annual_return_pct: float = 25.0,
    preferred_sectors: Optional[str] = None,
) -> types.PromptMessage:
    """
    股票建仓现金担保看跌期权策略引擎
    
    专门为股票获取而设计的CSP策略，通过期权分配以折扣价建立优质股票头寸。
    """
    
    try:
        from .prompts.stock_acquisition_csp_prompt import stock_acquisition_csp_engine as engine
        
        prompt_content = await engine(
            tickers=tickers,
            cash_usd=cash_usd,
            target_allocation_probability=target_allocation_probability,
            max_single_position_pct=max_single_position_pct,
            min_days=min_days,
            max_days=max_days,
            target_annual_return_pct=target_annual_return_pct,
            preferred_sectors=preferred_sectors
        )
        
        return types.PromptMessage(
            role="user",
            content=types.TextContent(
                type="text",
                text=prompt_content
            )
        )
        
    except Exception as e:
        error_msg = f"股票建仓CSP引擎错误: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        return types.PromptMessage(
            role="user", 
            content=types.TextContent(
                type="text",
                text=f"⚠️ {error_msg}\n\n请检查输入参数并重试。"
            )
        )
```

#### 4.3.2 导入更新
```python
# 在 src/mcp_server/prompts/__init__.py 中添加
from .stock_acquisition_csp_prompt import (
    stock_acquisition_csp_engine,
    get_stock_acquisition_examples
)
```

---

## 5. Testing Strategy

### 5.1 单元测试

#### 5.1.1 参数验证测试
```python
# tests/prompts/test_stock_acquisition_csp_prompt.py

import pytest
from src.mcp_server.prompts.stock_acquisition_csp_prompt import (
    stock_acquisition_csp_engine,
    _validate_stock_acquisition_parameters,
    _parse_tickers_input
)

class TestStockAcquisitionCSPPrompt:
    
    @pytest.mark.asyncio
    async def test_basic_prompt_generation(self):
        """测试基本提示生成"""
        result = await stock_acquisition_csp_engine(
            tickers="AAPL",
            cash_usd=50000.0,
            target_allocation_probability=65.0,
            min_days=21,
            max_days=60
        )
        
        assert "股票建仓现金担保PUT引擎" in result
        assert 'purpose_type="discount"' in result
        assert "target_allocation_probability=65.0" in result
    
    def test_parameter_validation(self):
        """测试参数验证"""
        # 测试有效参数
        valid_result = _validate_stock_acquisition_parameters(
            tickers=["AAPL", "MSFT"],
            cash_usd=50000.0,
            target_allocation_probability=65.0,
            max_single_position_pct=25.0,
            min_days=21,
            max_days=60,
            target_annual_return_pct=25.0
        )
        assert valid_result["is_valid"] == True
        
        # 测试无效参数
        invalid_result = _validate_stock_acquisition_parameters(
            tickers=[],
            cash_usd=-1000.0,  # 负数
            target_allocation_probability=150.0,  # 超过100%
            min_days=100,
            max_days=50  # min > max
        )
        assert invalid_result["is_valid"] == False
        assert len(invalid_result["errors"]) > 0
    
    def test_tickers_parsing(self):
        """测试股票代码解析"""
        # JSON格式
        result1 = _parse_tickers_input('["AAPL", "MSFT", "GOOGL"]')
        assert result1 == ["AAPL", "MSFT", "GOOGL"]
        
        # 逗号分隔
        result2 = _parse_tickers_input("AAPL,MSFT,GOOGL")
        assert result2 == ["AAPL", "MSFT", "GOOGL"]
        
        # 空格分隔
        result3 = _parse_tickers_input("AAPL MSFT GOOGL")
        assert result3 == ["AAPL", "MSFT", "GOOGL"]
        
        # 单个股票
        result4 = _parse_tickers_input("AAPL")
        assert result4 == ["AAPL"]
```

#### 5.1.2 工具集成测试
```python
    @pytest.mark.asyncio
    async def test_tool_integration_parameters(self):
        """测试工具集成参数正确性"""
        prompt = await stock_acquisition_csp_engine(
            tickers="AAPL",
            cash_usd=100000.0,
            target_allocation_probability=70.0,
            min_days=30,
            max_days=45
        )
        
        # 验证关键参数出现在提示中
        assert 'purpose_type="discount"' in prompt
        assert "target_allocation_probability=70.0" in prompt
        assert "30~45" in prompt or "30-45" in prompt
        assert "100000" in prompt or "100,000" in prompt
```

### 5.2 集成测试

#### 5.2.1 MCP服务器集成
```python
# tests/integration/test_stock_acquisition_integration.py

import pytest
from mcp import types
from src.mcp_server.server import mcp

class TestStockAcquisitionIntegration:
    
    @pytest.mark.asyncio
    async def test_mcp_prompt_registration(self):
        """测试MCP提示注册"""
        # 模拟MCP客户端调用
        result = await mcp.call_prompt(
            "stock_acquisition_csp_engine",
            arguments={
                "tickers": "AAPL",
                "cash_usd": 50000.0,
                "target_allocation_probability": 65.0
            }
        )
        
        assert isinstance(result, types.PromptMessage)
        assert result.role == "user"
        assert "股票建仓" in result.content.text
    
    @pytest.mark.asyncio 
    async def test_error_handling(self):
        """测试错误处理"""
        result = await mcp.call_prompt(
            "stock_acquisition_csp_engine",
            arguments={
                "tickers": "",  # 无效输入
                "cash_usd": -1000.0  # 负数
            }
        )
        
        assert "错误" in result.content.text or "Error" in result.content.text
```

### 5.3 功能测试用例

#### 5.3.1 典型使用场景
```python
class TestStockAcquisitionScenarios:
    
    @pytest.mark.asyncio
    async def test_conservative_stock_acquisition(self):
        """保守股票建仓策略"""
        prompt = await stock_acquisition_csp_engine(
            tickers="SPY,QQQ",
            cash_usd=25000.0,
            target_allocation_probability=60.0,
            max_single_position_pct=20.0,
            min_days=30,
            max_days=60,
            target_annual_return_pct=20.0
        )
        
        assert "SPY,QQQ" in prompt or "SPY, QQQ" in prompt
        assert "target_allocation_probability=60.0" in prompt
        assert "max_single_position_pct=20.0" in prompt
    
    @pytest.mark.asyncio
    async def test_aggressive_stock_acquisition(self):
        """激进股票建仓策略"""
        prompt = await stock_acquisition_csp_engine(
            tickers="TSLA,NVDA,AMD",
            cash_usd=100000.0,
            target_allocation_probability=75.0,
            max_single_position_pct=35.0,
            min_days=21,
            max_days=45,
            target_annual_return_pct=30.0
        )
        
        assert "TSLA" in prompt and "NVDA" in prompt
        assert "target_allocation_probability=75.0" in prompt
```

---

## 6. Validation Criteria

### 6.1 功能验证清单
- [ ] 提示生成功能正常
- [ ] 参数验证机制有效
- [ ] 股票代码解析支持多种格式
- [ ] MCP服务器注册成功
- [ ] 与现有工具集成无冲突
- [ ] 错误处理和异常情况覆盖

### 6.2 内容质量验证
- [ ] 提示内容逻辑清晰完整
- [ ] 工具调用序列正确
- [ ] 参数传递准确
- [ ] 与收入生成引擎差异化明确
- [ ] 股票建仓理念贯穿始终

### 6.3 集成验证
- [ ] Claude Code中可正常调用
- [ ] 与现有工具无参数冲突
- [ ] 错误信息友好易懂
- [ ] 性能表现acceptable

---

## 7. Success Metrics

### 7.1 技术指标
- **提示生成成功率**: ≥99%
- **参数验证准确率**: 100%
- **MCP集成稳定性**: 无崩溃错误
- **响应时间**: <2秒

### 7.2 用户体验指标
- **提示内容质量**: 逻辑清晰、易于理解
- **工具调用有效性**: 正确配置purpose_type="discount"
- **差异化明确性**: 与收入生成引擎区别明显
- **使用便利性**: 参数配置简单直观

### 7.3 业务价值指标
- **策略执行成功率**: 基于实际使用反馈
- **分配概率达成**: 实际分配比例接近目标65%
- **用户采用率**: 相对于收入生成引擎的使用比例
- **策略效果**: 长期收益表现评估

---

## 8. Risk Mitigation

### 8.1 技术风险
**风险**: 与现有收入生成引擎参数冲突
**缓解**: 采用不同的默认参数集，明确函数命名差异

**风险**: MCP集成错误
**缓解**: 充分的集成测试，渐进式部署

### 8.2 用户体验风险
**风险**: 用户混淆两种策略
**缓解**: 清晰的策略差异说明，不同的函数命名

**风险**: 参数配置复杂
**缓解**: 合理的默认值，详细的参数说明

### 8.3 业务风险
**风险**: 股票建仓策略效果不佳
**缓解**: 基于成熟理论和历史回测，提供风险警示

**风险**: 用户过度承担分配风险
**缓解**: 明确的风险声明，合理的仓位控制建议

---

## 9. Rollout Plan

### 9.1 Phase 1: 开发和测试 (Week 1-2)
- 实现核心提示引擎
- 完成单元测试
- 本地集成测试

### 9.2 Phase 2: 集成和验证 (Week 3)
- MCP服务器集成
- 集成测试验证
- 文档完善

### 9.3 Phase 3: 部署和监控 (Week 4)
- 生产环境部署
- 使用监控和反馈收集
- 迭代优化

---

## 10. Appendix

### 10.1 示例使用场景

#### 10.1.1 保守股票建仓
```python
# 适合稳健投资者的股票建仓策略
stock_acquisition_csp_engine(
    tickers="SPY,QQQ,AAPL",
    cash_usd=50000.0,
    target_allocation_probability=60.0,
    max_single_position_pct=20.0,
    min_days=30,
    max_days=60,
    target_annual_return_pct=20.0,
    preferred_sectors="Technology,Healthcare"
)
```

#### 10.1.2 激进股票建仓
```python
# 适合激进投资者的高概率分配策略
stock_acquisition_csp_engine(
    tickers="TSLA,NVDA,AMD",
    cash_usd=100000.0,
    target_allocation_probability=75.0,
    max_single_position_pct=35.0,
    min_days=21,
    max_days=45,
    target_annual_return_pct=30.0
)
```

### 10.2 核心技术依赖
- 现有 `cash_secured_put_strategy_tool_mcp` (purpose_type="discount")
- 现有 `options_chain_tool_mcp`
- 现有 `option_assignment_probability_tool_mcp`
- 现有 `portfolio_optimization_tool_mcp_tool`
- MCP框架和Claude Code集成

### 10.3 文档更新清单
- [ ] README.md 添加新提示说明
- [ ] API文档更新
- [ ] 使用示例补充
- [ ] 与收入生成引擎的对比说明

---

*本PRD版本: v10*  
*创建日期: 2024-09-28*  
*负责人: TradingAgent MCP开发团队*  
*审核状态: 待技术审核*