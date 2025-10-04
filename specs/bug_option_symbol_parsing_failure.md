# Bug: Option Position Rebalancer Prompt - Option Symbol Parsing Failure

## Bug Description
When invoking the `option_position_rebalancer_engine_prompt` MCP Server Prompt from Claude Code, the first parameter (option symbol) fails to parse correctly. The user provides a compact option symbol like `"MU251017P00167500"` along with additional position parameters, but the current prompt implementation expects the user to provide STRUCTURED input with separate fields (symbol, strike, expiration, etc.).

**症状 (Symptoms)**:
- 用户输入: `"MU251017P00167500" 4 2.03`
- 期望: 自动解析出 symbol="MU", expiration="2025-10-17", strike=167.50, position_type="short_put"
- 实际输出:
  - **标的股票**: (空或错误)
  - **行权价格**: $0.00
  - **到期日期**: 20"M-U2-51 (乱码)

**Expected vs Actual Behavior**:
- **Expected**: 提示应该接受简洁的OCC期权符号作为第一个参数,自动解析出所有必要字段
- **Actual**: 提示需要用户提供复杂的结构化输入,违反了用户体验原则

## Problem Statement
核心问题是**数据结构设计错误**:

1. **MCP Server Prompt参数设计问题**: 当前prompt要求用户提供 `option_symbol` 作为字符串,但实际上期权符号是为券商设计的唯一标识符,不是人类友好的输入格式
2. **用户界面不友好**: Claude Code用户希望用简洁的命令行方式调用,例如 `/TradingAgentMCP:option_position_rebalancer_engine_prompt "MU251017P00167500" 4 2.03`,但当前设计强迫用户提供复杂的JSON结构
3. **解析逻辑存在但未被利用**: 代码中已经存在 `_extract_*_from_option_symbol()` 函数,但这些函数的解析结果没有正确传递给prompt生成逻辑

## Solution Statement
采用**两层输入模式 (Two-Tier Input Mode)**:

### 模式1: 简洁模式 (Compact Mode) - 新增
允许用户提供:
- `option_symbol`: OCC标准期权符号 (例如: "MU251017P00167500")
- `position_size`: 仓位大小 (例如: 4 表示4个合约)
- `entry_price`: 入场价格 (例如: 2.03)
- 其他可选参数使用默认值

系统**自动解析** option_symbol 提取:
- underlying_symbol
- strike_price
- expiration_date
- option_type (put/call)
- 自动推断 position_type (基于position_size正负)

### 模式2: 结构化模式 (Structured Mode) - 保留向后兼容
允许高级用户显式提供所有字段:
```python
{
    "symbol": "MU",
    "strike": 167.50,
    "expiration": "2025-10-17",
    "option_type": "put",
    "position_type": "short",
    "quantity": 4,
    "entry_price": 2.03,
    "entry_date": "2025-09-15"
}
```

## Steps to Reproduce
1. 在Claude Code中打开TradingAgentMCP项目
2. 执行MCP Server Prompt命令:
   ```
   /TradingAgentMCP:option_position_rebalancer_engine_prompt "MU251017P00167500" 4 2.03
   ```
3. 观察输出显示:
   - 标的股票字段为空或错误
   - 行权价格显示为 $0.00
   - 到期日期显示为乱码 "20M-U2-51"

## Root Cause Analysis

### 技术层面 (Technical Layer)
1. **MCP Server Prompt定义问题** (src/mcp_server/server.py):
   - 当前prompt定义只接受简单的字符串参数
   - 没有提供清晰的参数映射说明

2. **解析函数问题** (src/mcp_server/prompts/option_position_rebalancer_prompt.py:188-233):
   - `_extract_underlying_from_option_symbol()`: 逻辑正确
   - `_extract_strike_from_option_symbol()`: 逻辑正确
   - `_extract_expiration_from_option_symbol()`: 逻辑正确
   - **但这些函数的输出没有被正确使用!**

3. **Prompt生成逻辑问题** (option_position_rebalancer_prompt.py:82-86):
   ```python
   # 当前代码 - 解析结果计算出来了
   underlying_symbol = _extract_underlying_from_option_symbol(option_symbol)
   strike_price = _extract_strike_from_option_symbol(option_symbol)
   expiration_date = _extract_expiration_from_option_symbol(option_symbol)
   option_type = "put" if "P" in option_symbol else "call"

   # 但是生成的prompt文本中硬编码使用了原始输入而非解析结果!
   # 见 _generate_rebalancer_prompt() 函数第286-294行
   ```

### 设计哲学层面 (Design Philosophy - Linus's Perspective)
> "Don't parse what you can compute. Don't compute what you can store."

当前设计违反了这个原则:
- **问题**: 将期权符号(一个为机器设计的标识符)当作"输入参数",然后尝试从中解析数据
- **正确做法**: 用户应该提供**人类可读的结构化数据**,或者系统应该**智能解析机器标识符**

但是,考虑到用户体验:
- 期权交易者习惯使用OCC符号 (例如从券商平台复制)
- 强制用户手动拆分字段会降低效率
- **因此**: 我们应该支持OCC符号作为输入,但系统必须正确解析并使用解析结果

## Relevant Files
Use these files to fix the bug:

### 核心文件 (Core Files)
- **src/mcp_server/prompts/option_position_rebalancer_prompt.py** (主要修复目标)
  - 包含期权符号解析逻辑 (_extract_*_from_option_symbol)
  - 包含prompt生成逻辑 (_generate_rebalancer_prompt)
  - **问题**: 解析结果没有被正确传递和使用

- **src/mcp_server/server.py** (次要修复目标)
  - 注册MCP Server Prompt的地方
  - 需要确保prompt定义清晰明确参数含义

### 测试文件 (Test Files)
- **tests/test_option_position_rebalancer_prompt.py**
  - 已有测试用例验证解析逻辑
  - 需要新增测试用例验证end-to-end场景

### 参考文件 (Reference Files)
- **specs/prd_12.md** - PRD文档,说明feature需求
- **ai_docs/option_position_rebalancer.md** - 参考实现文档

### 新文件 (New Files)
无需创建新文件。

## Step by Step Tasks

### 步骤1: 验证和增强期权符号解析逻辑
- 审查 `_extract_underlying_from_option_symbol()` 函数:
  - 验证对多字符ticker的支持 (例如: GOOG, GOOGL, SPXW)
  - 处理边界情况
- 审查 `_extract_strike_from_option_symbol()` 函数:
  - 验证小数价格解析正确性 (例如: 167.50)
  - 添加错误处理
- 审查 `_extract_expiration_from_option_symbol()` 函数:
  - 验证日期格式转换正确性 (251017 -> 2025-10-17)
  - 添加日期验证
- 为所有解析函数添加详细的docstring和类型提示
- 添加单元测试覆盖边界情况

### 步骤2: 增强参数验证逻辑
- 修改 `_validate_rebalancer_parameters()` 函数:
  - 验证解析出的underlying_symbol是否有效
  - 验证解析出的strike_price是否在合理范围 (0-10000)
  - 验证解析出的expiration_date是否为未来日期
  - 验证option_type (put/call) 是否与符号中的P/C匹配
- 增强错误消息,提供更详细的调试信息
- 添加警告机制,当解析结果可疑时提示用户

### 步骤3: 修复Prompt生成逻辑
- 修改 `_generate_rebalancer_prompt()` 函数:
  - **关键修复**: 确保使用解析后的变量而非原始option_symbol
  - 第286-294行应该使用传入的 `underlying_symbol`, `strike_price`, `expiration_date` 参数
  - 验证所有模板变量正确绑定
- 添加调试输出模式,显示解析结果供用户验证
- 确保生成的prompt中所有占位符都被正确替换

### 步骤4: 优化用户体验
- 在生成的prompt顶部添加"解析验证"部分:
  ```
  ## 🔍 参数解析验证

  **原始输入**: MU251017P00167500
  **解析结果**:
  - 标的股票: MU
  - 行权价格: $167.50
  - 到期日期: 2025-10-17
  - 期权类型: PUT

  请确认以上解析结果正确。如有误,请使用结构化输入模式。
  ```
- 提供清晰的错误消息,指导用户如何修正输入

### 步骤5: 增加端到端测试
- 创建新测试函数 `test_end_to_end_option_symbol_parsing()`:
  - 模拟Claude Code调用场景
  - 提供OCC符号 + position_size + entry_price
  - 验证生成的prompt包含正确的解析结果
- 测试边界情况:
  - 多字符ticker (GOOG, SPXW)
  - 小数行权价 (167.50, 50.25)
  - 不同到期日格式
  - PUT vs CALL
- 验证生成的prompt质量:
  - 所有必需字段已填充
  - 无占位符残留
  - 数值格式正确

### 步骤6: 更新文档和示例
- 更新 `get_rebalancer_examples()` 函数:
  - 添加"简洁模式"示例
  - 保留"结构化模式"示例向后兼容
- 更新docstring说明两种输入模式
- 在PRD文档中更新使用说明

### 步骤7: 运行完整验证
- 执行 `Validation Commands` 中的所有命令
- 确保所有测试通过
- 手动测试Claude Code集成
- 验证错误处理和警告机制

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

### 单元测试
```bash
# 运行解析函数单元测试
cd tests && uv run pytest test_option_position_rebalancer_prompt.py::test_option_symbol_parsing -v

# 运行参数验证测试
cd tests && uv run pytest test_option_position_rebalancer_prompt.py::test_parameter_validation -v

# 运行完整测试套件
cd tests && uv run pytest test_option_position_rebalancer_prompt.py -v
```

### 端到端测试
```bash
# 运行独立测试脚本
cd /Users/szou/Python/Playground/TradingAgentMCP && uv run python tests/test_option_position_rebalancer_prompt.py
```

### 回归测试
```bash
# 运行所有MCP Server测试,确保没有破坏其他功能
cd tests && uv run pytest -v

# 验证MCP Server可以正常启动
uv run python main.py --validate
```

### 手动验证 (Manual Verification)
1. 启动MCP Server
2. 在Claude Code中执行:
   ```
   /TradingAgentMCP:option_position_rebalancer_engine_prompt "MU251017P00167500" 4 2.03
   ```
3. 验证输出包含:
   - ✅ 标的股票: MU
   - ✅ 行权价格: $167.50
   - ✅ 到期日期: 2025-10-17
   - ✅ 期权类型: put
   - ✅ 无乱码或空值

### 边界情况测试 (Edge Cases)
```bash
# 测试多字符ticker
/TradingAgentMCP:option_position_rebalancer_engine_prompt "GOOG251017P00150000" -10 15.50

# 测试小数行权价
/TradingAgentMCP:option_position_rebalancer_engine_prompt "AAPL251017C00220500" 5 3.25

# 测试CALL期权
/TradingAgentMCP:option_position_rebalancer_engine_prompt "TSLA251017C00250000" -20 12.00
```

## Notes

### Linus风格的技术分析

**🟢 Good Taste方面**:
- 解析函数本身设计简洁,单一职责
- 函数命名清晰,意图明确

**🔴 Bad Taste方面**:
- **数据流断裂**: 计算了解析结果但没有使用 → 经典的"计算了但没存储"反模式
- **特殊情况处理不足**: 没有处理解析失败的边界情况
- **用户界面设计糟糕**: 强迫用户提供机器友好的符号,然后又不信任它

### 修复原则

1. **Fail Fast**: 解析失败时立即报错,不要生成垃圾输出
2. **Trust But Verify**: 解析后展示结果给用户确认
3. **Simplicity**: 不要引入复杂的抽象,直接修复数据流
4. **Backward Compatibility**: 保留现有接口,添加新模式

### 依赖库
无需添加新库,使用Python标准库即可。

### 性能考虑
解析逻辑非常简单(字符串操作),性能影响可忽略不计。

### 安全考虑
- 输入验证: 防止注入攻击
- 长度限制: option_symbol不应超过30字符
- 格式验证: 严格验证OCC符号格式

### 未来改进
- 支持非标准期权符号格式 (不同券商可能有变体)
- 提供符号格式验证工具
- 集成期权符号标准化服务
