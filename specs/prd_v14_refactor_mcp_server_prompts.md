# PRD v14: MCP Server Prompts重构计划

## 📋 概述

**目标**: 消除MCP Server Prompts中的代码重复，建立可扩展的公共工具模块，为未来Covered Call prompts做好架构准备。

**原则**:
- ✅ 提取公共代码到独立utils模块
- ✅ 保持各Prompt的独立性和专注性
- ✅ 零破坏外部API
- ✅ 为未来扩展预留架构空间

---

## 🔍 现状分析

### 现有Prompt文件

```
src/mcp_server/prompts/
├── income_generation_csp_prompt.py       (717行) ← 需要重构
├── stock_acquisition_csp_prompt.py       (773行) ← 需要重构
└── option_position_rebalancer_prompt.py  (983行) ← 保持独立
```

### 代码重复统计

| 函数名 | 重复次数 | 总行数 | 影响文件 |
|--------|---------|--------|----------|
| `_parse_tickers_input()` | 2 | 489行 × 2 = 978行 | income_csp, stock_acquisition_csp |
| `_get_duration_from_days()` | 2 | 21行 × 2 = 42行 | income_csp, stock_acquisition_csp |
| **总计** | - | **1020行重复代码** | - |

### 特殊情况

**option_position_rebalancer_prompt.py**:
- ✅ **无代码重复** - 它有独特的OCC期权符号解析函数
- ✅ **策略无关** - 同时支持CSP (`SHORT_PUT`) 和 Covered Call (`SHORT_CALL`)
- ✅ **保持独立** - 不需要重构

---

## 🎯 重构目标

### 短期目标 (Phase 1)
1. 创建`prompt_utils.py`公共工具模块
2. 重构现有2个CSP prompts，消除代码重复
3. 保持100%向后兼容

### 中期目标 (Phase 2 - 未来扩展)
4. 为即将添加的Covered Call prompts提供公共工具:
   - `income_generation_cc_prompt.py`
   - `stock_reduction_cc_prompt.py`
5. 提取更多可复用的Prompt片段（可选）

---

## 📐 架构设计

### Phase 1: 最小化重构方案 (本次实施)

```
src/mcp_server/prompts/
├── __init__.py
├── prompt_utils.py                           ← 【新建】公共工具模块
│   ├── parse_tickers_input()                 ← 489行通用ticker解析
│   └── get_duration_from_days()              ← 21行duration转换
│
├── income_generation_csp_prompt.py           ← 【重构】删除重复代码
├── stock_acquisition_csp_prompt.py           ← 【重构】删除重复代码
└── option_position_rebalancer_prompt.py      ← 【保持不变】
```

### Phase 2: 未来扩展架构 (预留设计)

```
src/mcp_server/prompts/
├── __init__.py
├── prompt_utils.py                           ← 基础工具（ticker解析等）
├── workflow_snippets.py                      ← 【未来】通用工作流片段
│   ├── generate_market_time_step()           ← 市场时间验证步骤
│   ├── generate_stock_analysis_step()        ← 股票分析步骤
│   └── generate_expiration_selection_step()  ← 到期日选择步骤
│
├── income_generation_csp_prompt.py
├── stock_acquisition_csp_prompt.py
├── income_generation_cc_prompt.py            ← 【未来添加】
├── stock_reduction_cc_prompt.py              ← 【未来添加】
└── option_position_rebalancer_prompt.py
```

---

## 🔨 详细实施计划

### Step 1: 创建公共工具模块

**文件**: `src/mcp_server/prompts/prompt_utils.py`

**内容**:
```python
"""
MCP Server Prompt公共工具模块

为各类期权策略Prompt提供通用的辅助函数。
"""

from typing import List, Union
import json
import ast


def parse_tickers_input(tickers_input: Union[List[str], str]) -> List[str]:
    """
    解析不同格式的tickers输入

    支持的格式:
    - Python列表: ['TSLA', 'GOOG', 'META']
    - JSON字符串: ["TSLA", "GOOG", "META"]
    - 空格分隔: "TSLA GOOG META"
    - 逗号分隔: "TSLA,GOOG,META"
    - 单个ticker: "TSLA"

    Args:
        tickers_input: 输入的tickers，可以是列表或字符串

    Returns:
        List[str]: 解析后的ticker列表

    Example:
        >>> parse_tickers_input('AAPL TSLA GOOG')
        ['AAPL', 'TSLA', 'GOOG']

        >>> parse_tickers_input('["AAPL", "TSLA"]')
        ['AAPL', 'TSLA']
    """
    # 【完整复制 income_generation_csp_prompt.py 中的实现】
    # Lines 489-698 (489行代码)
    pass


def get_duration_from_days(min_days: int, max_days: int) -> str:
    """
    根据天数范围转换为duration参数

    Args:
        min_days: 最小天数
        max_days: 最大天数

    Returns:
        str: duration参数值 ("1w", "2w", "1m", "3m", "6m", "1y")

    Example:
        >>> get_duration_from_days(7, 14)
        '1w'

        >>> get_duration_from_days(21, 35)
        '1m'
    """
    avg_days = (min_days + max_days) / 2

    if avg_days <= 9:
        return "1w"
    elif avg_days <= 18:
        return "2w"
    elif avg_days <= 35:
        return "1m"
    elif avg_days <= 100:
        return "3m"
    elif avg_days <= 190:
        return "6m"
    else:
        return "1y"
```

**预期行数**: ~210行（包含文档和debug逻辑）

---

### Step 2: 重构 `income_generation_csp_prompt.py`

**修改清单**:

1. **删除函数** (Lines 489-698):
   ```python
   # 删除整个 _parse_tickers_input() 函数定义
   ```

2. **删除函数** (Lines 414-434):
   ```python
   # 删除整个 _get_duration_from_days() 函数定义
   ```

3. **添加导入** (Line 18附近):
   ```python
   from .prompt_utils import parse_tickers_input, get_duration_from_days
   ```

4. **修改调用** (Line 62):
   ```python
   # 旧代码
   tickers_list = _parse_tickers_input(tickers)

   # 新代码
   tickers_list = parse_tickers_input(tickers)
   ```

**预期变化**:
- 文件行数: 717行 → ~397行 (减少320行，-44.6%)
- 外部API: **完全不变**
- 功能行为: **完全不变**

---

### Step 3: 重构 `stock_acquisition_csp_prompt.py`

**修改清单**:

1. **删除函数** (Lines 491-700):
   ```python
   # 删除整个 _parse_tickers_input() 函数定义
   ```

2. **删除函数** (Lines 467-487):
   ```python
   # 删除整个 _get_duration_from_days() 函数定义
   ```

3. **添加导入** (Line 18附近):
   ```python
   from .prompt_utils import parse_tickers_input, get_duration_from_days
   ```

4. **修改调用** (Line 64):
   ```python
   # 旧代码
   tickers_list = _parse_tickers_input(tickers)

   # 新代码
   tickers_list = parse_tickers_input(tickers)
   ```

**预期变化**:
- 文件行数: 773行 → ~453行 (减少320行，-41.4%)
- 外部API: **完全不变**
- 功能行为: **完全不变**

---

### Step 4: 更新 `prompts/__init__.py` (可选)

**目的**: 检查是否需要导出新的utils模块

**操作**:
```python
# 如果 __init__.py 导出了其他模块，可以考虑添加:
from .prompt_utils import parse_tickers_input, get_duration_from_days

# 但通常不需要，因为utils是内部使用
```

---

### Step 5: 验证测试

**语法检查**:
```bash
# Python语法验证
uv run python -m py_compile src/mcp_server/prompts/prompt_utils.py
uv run python -m py_compile src/mcp_server/prompts/income_generation_csp_prompt.py
uv run python -m py_compile src/mcp_server/prompts/stock_acquisition_csp_prompt.py
```

**导入测试**:
```bash
# 验证模块可以正常导入
uv run python -c "
from src.mcp_server.prompts.income_generation_csp_prompt import income_generation_csp_engine
print('✅ Income CSP Prompt OK')
"

uv run python -c "
from src.mcp_server.prompts.stock_acquisition_csp_prompt import stock_acquisition_csp_engine
print('✅ Stock Acquisition CSP Prompt OK')
"
```

**功能测试**:
```bash
# 测试parse_tickers_input函数
uv run python -c "
from src.mcp_server.prompts.prompt_utils import parse_tickers_input

# 测试各种格式
assert parse_tickers_input('AAPL TSLA GOOG') == ['AAPL', 'TSLA', 'GOOG']
assert parse_tickers_input('[\"AAPL\", \"TSLA\"]') == ['AAPL', 'TSLA']
assert parse_tickers_input('AAPL,TSLA,GOOG') == ['AAPL', 'TSLA', 'GOOG']
assert parse_tickers_input('AAPL') == ['AAPL']
assert parse_tickers_input(['AAPL', 'TSLA']) == ['AAPL', 'TSLA']

print('✅ parse_tickers_input 所有测试通过')
"

# 测试get_duration_from_days函数
uv run python -c "
from src.mcp_server.prompts.prompt_utils import get_duration_from_days

assert get_duration_from_days(7, 14) == '1w'
assert get_duration_from_days(14, 21) == '2w'
assert get_duration_from_days(21, 35) == '1m'
assert get_duration_from_days(60, 90) == '3m'

print('✅ get_duration_from_days 所有测试通过')
"
```

---

## 📊 重构效果预期

### 代码量优化

| 指标 | 重构前 | 重构后 | 改善 |
|------|--------|--------|------|
| **总代码行数** | 1490行 | ~860行 + 210行utils | -28.5% |
| **重复代码** | 1020行 | 0行 | **-100%** |
| **维护点** | 2个文件各维护1份 | 1个utils文件 | **-50%** |
| **income_csp文件大小** | 717行 | ~397行 | -44.6% |
| **stock_acquisition_csp文件大小** | 773行 | ~453行 | -41.4% |

### 质量提升

| 维度 | 重构前 | 重构后 |
|------|--------|--------|
| **代码复用性** | 低（代码复制） | 高（统一工具） |
| **维护成本** | 高（改2处） | 低（改1处） |
| **一致性** | 中（可能漂移） | 高（强制统一） |
| **测试覆盖** | 分散 | 集中 |
| **向后兼容** | N/A | ✅ 100% |

### 未来扩展能力

| 场景 | 重构前 | 重构后 |
|------|--------|--------|
| **添加CC prompts** | 再复制489行 | 直接import |
| **修复ticker解析bug** | 需改2处 | 只改1处 |
| **添加新ticker格式** | 需改2处 | 只改1处 |
| **代码审查难度** | 高 | 低 |

---

## ⚠️ 风险评估与缓解

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|---------|
| **导入路径错误** | 低 | 中 | Step 5语法检查 |
| **功能行为变化** | 极低 | 高 | 代码完全复制，无逻辑改动 |
| **Debug日志失效** | 低 | 低 | 保留所有debug_logger调用 |
| **破坏外部API** | 零 | 高 | 仅内部重构，对外API不变 |
| **测试失败** | 极低 | 中 | 功能完全一致 |

---

## 🎯 验收标准

### 功能验收
- [ ] `income_generation_csp_engine()` 功能完全正常
- [ ] `stock_acquisition_csp_engine()` 功能完全正常
- [ ] `parse_tickers_input()` 支持所有原有格式
- [ ] `get_duration_from_days()` 转换逻辑正确

### 代码质量
- [ ] 所有文件通过Python语法检查
- [ ] 无重复代码（通过人工review）
- [ ] 导入路径正确无误
- [ ] 代码风格一致

### 兼容性
- [ ] 外部调用代码无需修改
- [ ] MCP Server注册无需修改
- [ ] 现有测试全部通过（如有）
- [ ] 文档更新完整

---

## 📅 执行时间线

| 阶段 | 预计耗时 | 说明 |
|------|---------|------|
| **Step 1: 创建utils** | 3分钟 | 复制粘贴现有代码 |
| **Step 2: 重构income_csp** | 3分钟 | 删除+导入 |
| **Step 3: 重构stock_acquisition_csp** | 3分钟 | 删除+导入 |
| **Step 4: 更新__init__** | 1分钟 | 可选步骤 |
| **Step 5: 验证测试** | 5分钟 | 语法、导入、功能测试 |
| **总计** | **15分钟** | |

---

## 🔮 未来扩展规划 (Phase 2)

### 即将添加的Prompts

1. **income_generation_cc_prompt.py**
   - 目的: Covered Call收入生成策略
   - 复用: `parse_tickers_input()`, `get_duration_from_days()`
   - 差异: `purpose_type="income"`, Delta范围不同

2. **stock_reduction_cc_prompt.py**
   - 目的: Covered Call股票减持策略
   - 复用: `parse_tickers_input()`, `get_duration_from_days()`
   - 差异: `purpose_type="exit"`, Delta范围更激进

### 可选的工作流片段提取 (workflow_snippets.py)

如果发现Prompt生成中有大量重复的工作流步骤，可以进一步提取：

```python
# workflow_snippets.py (未来可选)

def generate_market_time_step() -> str:
    """生成通用的市场时间验证步骤"""
    return """### 第一步: 时间基准验证 (关键!)
```
get_market_time_tool()
```
**验证要求**: 确保返回有效市场时间...
"""

def generate_stock_analysis_step(ticker: str) -> str:
    """生成股票基础分析步骤"""
    return f"""### 第二步: 股票基础分析
```
stock_info_tool(symbol="{ticker}")
stock_history_tool(symbol="{ticker}", date_range="3m")
```
"""

def generate_expiration_selection_step(ticker: str, strategy_type: str) -> str:
    """生成智能到期日选择步骤"""
    return f"""### 第三步: 智能到期日优化选择
```
optimal_expiration_selector_tool_mcp(
    symbol="{ticker}",
    strategy_type="{strategy_type}"
)
```
"""
```

**评估标准**: 只有在至少3个Prompts共享相同片段时才提取。

---

## 📝 总结

### Linus评价

> "Good. You're eliminating the stupid copy-paste pattern without over-engineering. Keep each prompt doing one thing well, extract the common boring stuff, and don't break userspace. This is how you refactor properly."

### 核心原则遵守情况

| Linus原则 | 遵守情况 | 说明 |
|----------|---------|------|
| **Never break userspace** | ✅ | 外部API完全不变 |
| **Simplicity first** | ✅ | 只提取明确重复的代码 |
| **Good taste** | ✅ | 消除特殊情况（重复代码） |
| **Data structures matter** | ✅ | 保持原有数据流不变 |
| **Don't over-engineer** | ✅ | 不引入不必要的抽象 |

---

## 🚀 下一步行动

准备好后，按以下顺序执行：

1. ✅ 创建 `src/mcp_server/prompts/prompt_utils.py`
2. ✅ 重构 `income_generation_csp_prompt.py`
3. ✅ 重构 `stock_acquisition_csp_prompt.py`
4. ✅ 运行验证测试
5. ✅ 更新README.md（可选，说明工具复用）

**预计总耗时**: 15分钟

---

*最后更新: 2025-10-05*
*作者: Linus的工程哲学指导下的重构计划*
