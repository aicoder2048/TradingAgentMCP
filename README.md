# TradingAgent MCP

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.0+-green.svg)](https://github.com/fastmcp/fastmcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个生产就绪的交易代理 MCP 服务器，基于 FastMCP 框架构建。提供股票市场数据、交易时段状态和综合股票信息的实时访问功能，与 Claude Code 和其他 MCP 客户端无缝集成。

## 🌟 核心功能

- **📊 实时市场数据**: 通过 Tradier API 提供实时股票信息和市场时间
- **🕐 交易时段跟踪**: 准确获取美股市场开盘状态和交易时段信息
- **📈 综合股票分析**: 详细的股票关键信息，包括价格、成交量、估值指标和技术指标
- **🎯 现金保障看跌策略**: 专业级期权策略分析，支持收入和折扣购买双重目的 🆕
- **📞 Covered Call策略**: 持股投资者的专业covered call期权策略分析和风险管理 🆕
- **🧠 智能期权筛选**: 基于Delta的期权选择、风险评估和专业订单格式化 🆕
- **⚖️ 三级风险建议**: 保守、平衡、激进三种风险级别的投资建议 🆕
- **💵 收入生成CSP引擎**: 专业收入导向现金担保看跌策略提示生成器，目标≥50%年化收益 🆕
- **🏗️ 股票建仓CSP引擎**: 专业股票获取导向现金担保看跌策略提示生成器，欢迎分配建仓 🆕
- **🔄 期权仓位再平衡引擎**: 实时风险监控、智能决策分析和防御性Roll策略执行 🆕
- **🔧 环境配置**: 基于环境变量的灵活配置，支持沙盒和生产环境
- **🧩 模块化架构**: 工具、提示和配置的清晰分离
- **🧪 测试就绪**: 内置 pytest 测试框架
- **📝 类型安全**: 完整的类型提示和 Pydantic 模型支持
- **🔌 Claude Code 优化**: 为 Claude Code 集成预配置
- **📦 UV 包管理**: 使用 UV 进行现代 Python 包管理

## 📋 系统要求

- Python 3.13 或更高版本
- [UV 包管理器](https://github.com/astral-sh/uv)
- Claude Code（用于 MCP 客户端集成）
- [Tradier 开发者账户](https://developer.tradier.com/)（用于市场数据 API 访问）

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone <repository-url>
cd TradingAgentMCP
```

### 2. 环境配置

```bash
# 复制环境配置文件
cp .env.sample .env

# 编辑 .env 文件，设置你的配置
# 需要设置 TRADIER_ACCESS_TOKEN 和其他变量
```

**重要**: 在 `.env` 文件中配置你的 Tradier API 访问令牌：

```env
# 从 https://developer.tradier.com/ 获取你的令牌
TRADIER_ACCESS_TOKEN=your-tradier-access-token-here
TRADIER_ENVIRONMENT=sandbox  # 或 'production' 用于实盘
MCP_SERVER_NAME=TradingAgentMCP
```

### 3. 安装依赖

```bash
# 创建虚拟环境并安装依赖
uv sync --python 3.13
```

### 4. 配置 Claude Code 集成

```bash
# 复制 MCP 配置文件
cp .mcp.json.sample .mcp.json

# 编辑 .mcp.json，更新项目路径
# 更新服务器名称和项目路径
```

### 5. 运行服务器

```bash
# 使用 UV 直接运行
uv run python main.py

# 或先激活环境
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python main.py
```

## 📁 Project Structure

```
.
├── main.py                    # Server entry point
├── .env                       # Environment variables (create from .env.sample)
├── .env.sample               # Environment variables template
├── .mcp.json                 # Claude Code configuration (create from sample)
├── .mcp.json.sample          # Claude Code configuration template
├── pyproject.toml            # Project dependencies and metadata
├── uv.lock                   # Locked dependencies
├── src/
│   ├── market/               # 市场数据处理模块
│   │   ├── __init__.py
│   │   ├── config.py        # 市场配置
│   │   ├── earnings_calendar.py # 财报日历功能 🆕
│   │   ├── holidays.py      # 市场假期处理
│   │   ├── hours.py         # 交易时段管理
│   │   └── data/
│   │       └── mkt_holidays_2025_2026.json # 市场假期数据
│   ├── provider/            # 数据提供商集成
│   │   └── tradier/
│   │       ├── __init__.py
│   │       └── client.py    # Tradier API 客户端
│   ├── stock/               # 股票信息处理
│   │   ├── __init__.py
│   │   ├── info.py         # 股票信息处理器  
│   │   └── history_data.py # 历史数据和技术分析 🆕
│   ├── option/              # 期权分析模块 🆕
│   │   ├── __init__.py
│   │   ├── option_expiration_selector.py # 智能期权到期日选择 🆕
│   │   ├── greeks_enhanced.py # 增强希腊字母计算 🆕
│   │   ├── options_chain.py  # 期权链处理
│   │   ├── option_strikes.py # 期权行权价管理
│   │   └── option_expiration_dates.py # 期权到期日处理
│   ├── strategy/            # 交易策略模块 🆕
│   │   ├── __init__.py
│   │   ├── cash_secured_put.py # 现金保障看跌策略分析器 🆕
│   │   ├── covered_call.py # Covered Call策略分析器 🆕
│   │   ├── strategy_analyzer.py # Delta基础行权价选择器 🆕
│   │   ├── risk_calculator.py # 期权风险计算器 🆕
│   │   ├── error_handling.py # 增强错误处理模块 🆕
│   │   └── performance_optimizer.py # 性能优化模块 🆕
│   ├── utils/               # 通用工具
│   │   ├── __init__.py
│   │   └── time.py         # 时间处理工具
│   └── mcp_server/          # MCP 服务器核心
│       ├── __init__.py
│       ├── server.py        # 主服务器实现
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py  # 配置管理
│       ├── models/
│       │   ├── __init__.py
│       │   └── schemas.py   # Pydantic 数据模型
│       ├── tools/           # MCP 工具实现
│       │   ├── __init__.py
│       │   ├── hello_tool.py # 示例工具实现
│       │   ├── get_market_time_tool.py # 市场时间工具
│       │   ├── stock_key_info_tool.py  # 股票信息工具
│       │   ├── get_earnings_calendar_tool.py # 财报日历工具 🆕
│       │   ├── get_stock_history_tool.py # 历史数据工具 🆕
│       │   ├── cash_secured_put_strategy_tool.py # 现金保障看跌策略工具 🆕
│       │   └── covered_call_strategy_tool.py # Covered Call策略工具 🆕
│       └── prompts/
│           ├── __init__.py
│           └── hello_prompt.py # 示例提示实现
├── data/                      # CSV 数据存储目录 🆕
│   └── .gitkeep               # Git 目录占位文件
├── tests/
│   ├── __init__.py
│   ├── stock/
│   │   ├── test_info.py       # 股票信息测试
│   │   └── test_history_data.py # 历史数据测试 🆕
│   ├── tools/
│   │   ├── test_hello_tool.py
│   │   ├── test_get_market_time_tool.py
│   │   ├── test_stock_info_tool.py 
│   │   ├── test_get_earnings_calendar_tool.py
│   │   ├── test_get_stock_history_tool.py # 历史数据工具测试 🆕
│   │   └── test_covered_call_strategy_tool.py # Covered Call策略工具测试 🆕
│   └── prompts/
│       └── test_hello_prompt.py
├── specs/
│   ├── prd_v0_ai_enhanced.md  # Product requirements document
│   ├── prd_v3_ai_enhanced.md  # 财报日历 PRD 🆕
│   ├── prd_v4_ai_enhanced.md  # 历史数据 PRD 🆕
│   ├── prd_v6_ai_enhanced.md  # 现金保障看跌策略 PRD 🆕
│   └── prd_v7_ai_enhanced.md  # Covered Call策略 PRD 🆕
└── ai_docs/                    # Reference documentation
```

## ⚙️ Configuration

### 环境变量

在 `.env` 文件中配置服务器环境变量：

```env
# 服务器配置
MCP_SERVER_NAME=TradingAgentMCP  # MCP 服务器名称
MCP_VERSION=1.0.0                # 服务器版本

# Tradier API 配置
TRADIER_ACCESS_TOKEN=your-token-here  # Tradier API 访问令牌
TRADIER_ENVIRONMENT=sandbox           # sandbox 或 production

# 日志配置
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR, CRITICAL
DEBUG=false                      # 启用调试模式

# 功能配置
MAX_PROMPT_CALLS=10             # 最大提示调用次数
ENABLE_METRICS=false            # 启用指标收集
```

### Claude Code 集成

在 `.mcp.json` 中配置 Claude Code 连接到你的服务器：

```json
{
  "mcpServers": {
    "TradingAgentMCP": {
      "command": "uv",
      "args": ["run", "python", "/path/to/TradingAgentMCP/main.py"],
      "env": {
        "LOG_LEVEL": "DEBUG",
        "PYTHONPATH": "/path/to/TradingAgentMCP"
      }
    }
  }
}
```

## 🛠️ 开发指南

### 添加新工具

1. 在 `src/mcp_server/tools/` 中创建新文件
2. 实现异步工具函数
3. 在 `tools/__init__.py` 中导出
4. 在 `server.py` 中使用 `@mcp.tool()` 装饰器注册

示例:
```python
# src/mcp_server/tools/my_trading_tool.py
async def my_trading_tool(symbol: str) -> dict:
    """你的工具描述。"""
    return {"result": f"处理股票: {symbol}"}
```

### 添加新提示

1. 在 `src/mcp_server/prompts/` 中创建新文件
2. 实现异步提示函数
3. 在 `prompts/__init__.py` 中导出
4. 在 `server.py` 中使用 `@mcp.prompt()` 装饰器注册

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行覆盖率测试
uv run pytest --cov=src/mcp_server

# 运行特定测试文件
uv run pytest tests/tools/test_hello_tool.py
```

## 🔍 可用工具和提示

### 交易工具

- **get_market_time_tool**: 获取美股市场时间和交易状态
  - 无需输入参数
  - 返回: 包含东部时间、市场状态、交易日信息的综合数据

- **stock_info_tool**: 获取股票综合关键信息
  - 输入: `symbol` (股票代码，如 "TSLA", "AAPL", "NVDA")
  - 返回: 详细的股票信息，包括价格数据、交易量、估值指标和技术指标

- **earnings_calendar_tool**: 获取股票财报日历信息 🆕
  - 输入: `symbol` (股票代码，如 "TSLA", "AAPL", "NVDA")
  - 返回: 包含历史和未来财报事件、下次财报日期的综合日历信息
  - 特色: 智能过滤（仅显示12个月内的财报相关事件）

- **stock_history_tool**: 获取股票历史数据和技术分析 🆕
  - 输入: 
    - `symbol` (必需: 股票代码，如 "AAPL", "TSLA", "NVDA")
    - `start_date` (可选: 开始日期 YYYY-MM-DD)
    - `end_date` (可选: 结束日期 YYYY-MM-DD) 
    - `date_range` (可选: 相对范围如 "30d", "3m", "1y")
    - `interval` (可选: "daily", "weekly", "monthly", 默认 "daily")
    - `include_indicators` (可选: 是否包含技术指标, 默认 true)
  - 返回: 历史 OHLCV 数据、技术指标、CSV 文件路径、统计摘要
  - 特色: 
    - 支持灵活日期范围 (绝对/相对/混合模式)
    - 全套技术指标 (SMA, EMA, RSI, MACD, ATR, 布林带等)
    - 自动保存 CSV 文件到 `./data` 目录
    - 上下文优化 (仅返回摘要 + 前30条记录)

- **cash_secured_put_strategy_tool_mcp**: 现金保障看跌期权策略分析工具 🆕
  - 输入:
    - `symbol` (必需: 股票代码，如 "AAPL", "TSLA", "NVDA")
    - `purpose_type` (可选: "income" 收入导向 或 "discount" 折扣购买, 默认 "income")
    - `duration` (可选: "1w", "2w", "1m", "3m", "6m", "1y", 默认 "1w")
    - `capital_limit` (可选: 最大可用资金金额)
    - `include_order_blocks` (可选: 是否包含专业订单块, 默认 true)
    - `min_premium` (可选: 最低权利金要求)
    - `max_delta` (可选: 最大Delta限制)
  - 返回: 
    - 三级风险建议 (保守、平衡、激进)
    - JP Morgan风格的专业订单块
    - 完整的风险分析和P&L场景
    - CSV数据导出
  - 特色:
    - 基于Delta的智能期权筛选 (收入: 10-30%, 折扣: 30-70%)
    - 智能期权到期日选择 (优先周期权/月期权)
    - 专业级风险评估和分配概率计算
    - 机构级订单格式化 (类似JP Morgan交易台风格)

- **covered_call_strategy_tool_mcp**: Covered Call期权策略分析工具 🆕
  - 输入:
    - `symbol` (必需: 股票代码，如 "AAPL", "TSLA", "NVDA")
    - `purpose_type` (可选: "income" 收入导向 或 "exit" 减仓导向, 默认 "income")
    - `duration` (可选: "1w", "2w", "1m", "3m", "6m", "1y", 默认 "1w")
    - `shares_owned` (必需: 持有股票数量，至少100股, 默认 100)
    - `avg_cost` (可选: 每股平均成本基础，用于税务分析)
    - `min_premium` (可选: 最低权利金门槛)
    - `include_order_blocks` (可选: 是否包含专业订单块, 默认 true)
  - 返回:
    - 三级风险建议 (保守、平衡、激进)
    - 专业订单格式化和执行说明
    - 完整的P&L分析和风险评估
    - 持仓验证和合约计算
    - CSV数据导出和市场环境分析
  - 特色:
    - 基于Delta的call期权筛选 (收入: 10-30%, 减仓: 30-70%)
    - 智能技术阻力位分析影响执行价选择
    - 上涨捕获vs机会成本优化分析
    - 分配概率和downside保护计算
    - 机构级JP Morgan风格订单块

- **option_limit_order_probability_tool_mcp**: 期权限价单成交概率预测工具 🆕
  - 输入:
    - `symbol` (必需: 股票代码，如 "AAPL", "TSLA", "NVDA")
    - `strike_price` (必需: 期权执行价格)
    - `expiration` (必需: 到期日期 YYYY-MM-DD 格式)
    - `option_type` (必需: 期权类型 "put" 或 "call")
    - `current_price` (必需: 当前期权市场价格)
    - `limit_price` (必需: 目标限价)
    - `order_side` (必需: 订单方向 "buy" 或 "sell")
    - `analysis_window` (可选: 分析窗口天数)
  - 返回:
    - 成交概率 (0-100%)
    - **当日成交概率 (0-100%)** 🆕
    - 预期成交时间 (天数)
    - 置信度指标和统计验证
    - 每日成交概率分布
    - 替代限价建议
    - 完整的风险分析
  - 特色:
    - 蒙特卡洛模拟 (10,000+ paths)
    - 动态波动率混合 (IV + HV)
    - Greeks敏感度分析
    - 理论和实证双重验证
    - 智能替代限价推荐
    - 统计置信度评估

- **hello**: 简单的问候工具（演示用）
  - 输入: `name` (字符串)
  - 返回: 结构化的问候响应

### 提示

- **call_hello_multiple**: 演示提示功能
  - 生成多次调用 hello 工具的指令
  - 参数: `name` (字符串), `times` (整数)

- **income_generation_csp_engine**: 收入生成现金担保看跌策略引擎 🆕
  - 生成高收益、低分配风险的期权策略执行计划
  - 参数: 
    - `tickers` (股票列表): 目标股票代码 (例如: ["AAPL", "TSLA"])
    - `cash_usd` (浮点数): 可用资金
    - `min_days` (整数): 最小到期天数 (默认: 7)
    - `max_days` (整数): 最大到期天数 (默认: 28)
    - `target_apy_pct` (浮点数): 目标年化收益率 (默认: 50%)
    - `min_winrate_pct` (浮点数): 最小胜率要求 (默认: 70%)
    - `confidence_pct` (浮点数): 统计置信度 (默认: 90%)
  - 返回: 综合的收入导向策略执行提示，包含工具调用序列、筛选标准和风险管理协议

- **stock_acquisition_csp_engine**: 股票建仓现金担保看跌策略引擎 🆕
  - 生成以折扣价建立股票头寸的期权策略执行计划，欢迎股票分配
  - 参数:
    - `tickers` (股票列表): 目标股票代码 (例如: ["AAPL", "MSFT"])
    - `cash_usd` (浮点数): 可用资金
    - `target_allocation_probability` (浮点数): 目标分配概率 (默认: 65.0%)
    - `max_single_position_pct` (浮点数): 单股票最大仓位 (默认: 25.0%)
    - `min_days` (整数): 最小到期天数 (默认: 21)
    - `max_days` (整数): 最大到期天数 (默认: 60)
    - `target_annual_return_pct` (浮点数): 目标年化收益率 (默认: 25.0%)
    - `preferred_sectors` (字符串): 偏好行业 (默认: "Technology,Healthcare,Consumer Discretionary")
  - 返回: 综合的股票建仓策略执行提示，包含基本面分析、期权筛选、组合配置和分配后管理

- **option_position_rebalancer_engine**: 期权仓位再平衡与风险管理引擎 🆕
  - 为现有期权仓位提供实时风险监控、智能决策分析和防御性策略执行
  - 参数:
    - `option_symbol` (必需): OCC标准期权合约符号 (例如: "MU251017P00167500", "TSLA250919P00390000")
    - `position_size` (必需): 仓位大小 (负数表示做空，正数表示做多)
    - `entry_price` (必需): 入场价格 (期权单价 per share)
    - `position_type` (可选): 仓位类型 - "short_put", "short_call", "long_put", "long_call" (默认: "short_put")
    - `entry_date` (可选): 入场日期 YYYY-MM-DD 格式
    - `risk_tolerance` (可选): 风险容忍度 - "conservative", "moderate", "aggressive" (默认: "moderate")
    - `defensive_roll_trigger_pct` (可选): 防御性滚动触发阈值百分比 (默认: 15.0)
    - `profit_target_pct` (可选): 获利目标百分比 (默认: 70.0)
    - `max_additional_capital` (可选): 最大额外资金投入 (默认: 0)
  - 返回:
    - 实时P&L和Greeks风险敞口分析
    - Hold/Close/Roll的量化评分和决策支持
    - 防御性策略 (Calendar/Diagonal/Triple Strike Resize Roll)
    - Bloomberg/IEX标准订单格式
  - 特色:
    - 自动解析OCC期权符号 (股票代码、到期日、行权价、期权类型)
    - 实时被行权概率计算和风险监控
    - 基于市场条件的智能策略评估
    - 三级风险容忍度的差异化建议

## 🔍 工具 vs 提示：核心区别与使用场景

理解**工具（Tool）**和**提示（Prompt）**的区别，可以帮助你选择正确的方式完成任务。

### 本质区别

| 维度 | MCP Server Tool | MCP Server Prompt |
|------|----------------|-------------------|
| **类比** | 🔧 单个工具（锤子） | 📋 施工图纸（告诉AI怎么用工具） |
| **输入** | 参数（symbol, duration等） | 参数 + AI上下文 |
| **输出** | 结构化数据（JSON） | 超长Prompt字符串 |
| **执行者** | Python代码直接执行 | AI（Claude）读取并执行 |
| **复杂度** | 单一任务 | 多步骤工作流 |
| **调用方式** | 任何工具/脚本 | AI助手（Claude Code） |
| **典型用例** | 快速获取单个结果 | 完整分析和决策支持 |

### CSP工具与Prompt的具体区别

#### 📊 `cash_secured_put_strategy_tool_mcp` (Tool)

**核心能力**：
- ✅ 在**一个到期日**下，分析不同的执行价（Strike）
- ✅ 自动选择最优到期日（通过内部ExpirationSelector）
- ✅ 返回三个风险级别的推荐（conservative/balanced/aggressive）
- ✅ 可被任何程序调用（脚本、自动化工作流等）

**工作流程**：
```
用户输入: symbol="AAPL", purpose_type="income", duration="1w"
    ↓
内部ExpirationSelector筛选所有1周内的到期日
    ↓
选择最优的一个到期日（例如：2025-10-18）
    ↓
只分析这个到期日的期权链
    ↓
返回：conservative/balanced/aggressive 三个推荐
      （都是2025-10-18到期的不同执行价）
```

**限制**：
- ❌ 不比较多个到期日的策略
- ❌ 不支持多股票组合分配
- ❌ 不展示到期日筛选的详细评分过程
- ❌ 返回结果中只有一个到期日

**典型使用场景**：
```python
# 场景：自动化脚本，每天分析AAPL的周度CSP策略
result = cash_secured_put_strategy_tool_mcp(
    symbol="AAPL",
    purpose_type="income",
    duration="1w",
    capital_limit=50000
)

# 提取推荐
conservative = result["recommendations"]["conservative"]
print(f"执行价: ${conservative['option_details']['strike']}")
print(f"到期日: {result['selected_expiration']['date']}")  # 只有一个
print(f"年化收益: {conservative['pnl_analysis']['annualized_return']}%")
```

---

#### 📋 `income_generation_csp_engine` 和 `stock_acquisition_csp_engine` (Prompts)

**核心能力**：
- ✅ 完整的AI工作流编排（7-8个步骤）
- ✅ 先调用`optimal_expiration_selector_tool_mcp`智能筛选到期日（返回评分详情）
- ✅ 支持多个股票的投资组合分配
- ✅ 包含市场分析、基本面分析、技术面分析
- ✅ 生成完整的HTML报告和执行建议

**工作流程**：
```
用户输入: tickers=["AAPL","MSFT"], cash_usd=50000, target_apy_pct=50
    ↓
第1步: 验证市场时间 (get_market_time_tool)
    ↓
第2步: 分析AAPL和MSFT的基本面、技术面 (stock_info_tool, stock_history_tool)
    ↓
第3步: 智能到期日优化选择 (optimal_expiration_selector_tool_mcp)
         - 获取所有候选到期日
         - 展示评分详情（Theta效率、Gamma风险、流动性）
         - 选择最优到期日
    ↓
第4步: 对每个股票调用CSP Tool (cash_secured_put_strategy_tool_mcp)
         - AAPL使用优化选择的到期日
         - MSFT使用优化选择的到期日
    ↓
第5步: 期权链深度分析 (options_chain_tool_mcp)
    ↓
第6步: 被行权概率计算 (option_assignment_probability_tool_mcp)
    ↓
第7步: 投资组合优化 (portfolio_optimization_tool_mcp)
         - 基于夏普比率分配权重
         - AAPL: 60% ($30,000)
         - MSFT: 40% ($20,000)
    ↓
返回：完整分析报告 + HTML文件 + 执行建议
```

**优势**：
- ✅ 展示到期日优化的完整过程（评分、排名、选择理由）
- ✅ 多股票智能配置（基于风险收益优化）
- ✅ AI提供决策建议和执行指导
- ✅ 完整的风险管理和监控计划

**限制**：
- ❌ 需要AI执行（不能在脚本中直接调用）
- ❌ 执行时间较长（调用多个工具）

**典型使用场景**：
```
用户在Claude Code中提问:
"我有5万美金，想通过卖PUT获得年化50%收益，帮我分析AAPL和MSFT"

Claude调用Prompt后执行:
1. ✅ 验证市场时间
2. ✅ 分析AAPL/MSFT基本面和技术面
3. ✅ 智能选择最优到期日（展示评分过程）
4. ✅ 生成两个股票的CSP策略
5. ✅ 计算被行权概率
6. ✅ 优化投资组合配置
7. ✅ 生成HTML报告

Claude输出:
"根据分析，建议分配：
- AAPL: 60% ($30,000) - 保守策略 - 年化52%
- MSFT: 40% ($20,000) - 平衡策略 - 年化48%
综合年化收益预期: 50.4%

详细分析已保存到report.html"
```

---

#### 🎯 两个CSP Prompt的区别

| 维度 | income_generation_csp | stock_acquisition_csp |
|------|---------------------|----------------------|
| **目标** | 收取权利金，**不想**被分配股票 | 以折扣价买入，**欢迎**被分配 |
| **Delta范围** | 0.10-0.30（保守） | 0.30-0.50（激进） |
| **到期日偏好** | 7-21天（快速周转） | 30-60天（耐心等待） |
| **Tool参数** | `purpose_type="income"` | `purpose_type="discount"` |
| **评估重点** | 年化收益率、避免分配 | 分配概率、折扣幅度 |
| **投资组合** | 多样化（降低风险） | 集中化（建仓优质股票） |
| **关键词** | 都调用同一个Tool | 但传递不同参数和分析逻辑 |

---

### 使用场景决策树

```
你的需求是什么？
    ↓
   /  \
  /    \
快速    完整
结果    分析
 ↓      ↓

直接   使用
调用   Prompt
Tool    ↓
 ↓
        AI编排
JSON    多工具
结果     ↓

        完整
        报告
        +建议
```

#### 选择Tool的情况：
- ✅ 我知道具体参数（symbol, duration等）
- ✅ 我只要策略推荐结果（单个到期日）
- ✅ 我会自己分析和决策
- ✅ 我要在程序中调用（自动化）
- ✅ 我需要快速结果

#### 选择Prompt的情况：
- ✅ 我需要完整的分析流程
- ✅ 我需要AI帮我选股、选到期日
- ✅ 我需要投资组合优化建议
- ✅ 我需要风险评估和执行建议
- ✅ 我需要人类可读的报告
- ✅ 我想看到期日优化的评分过程
- ✅ 我要分析多个股票并智能分配资金

---

### 代码示例对比

#### 示例1：直接用Tool（程序化）

```python
# 快速获取AAPL的CSP推荐
import asyncio

async def quick_analysis():
    result = await cash_secured_put_strategy_tool_mcp(
        symbol="AAPL",
        purpose_type="income",
        duration="1w",
        capital_limit=50000
    )

    # 只关注结果
    conservative = result["recommendations"]["conservative"]
    print(f"推荐执行价: ${conservative['option_details']['strike']}")
    print(f"到期日: {result['selected_expiration']['date']}")  # 单一日期
    print(f"年化收益: {conservative['pnl_analysis']['annualized_return']}%")

    # 特点：快速、直接、单一到期日
```

#### 示例2：通过Prompt（AI辅助决策）

```
用户在Claude Code中提问：
"我有5万美金，想通过CSP策略实现年化50%收益，
 该投资哪些股票？怎么分配？"

选择Prompt：income_generation_csp_engine

Claude执行完整流程：
1. ✅ 市场时间验证
2. ✅ 多股票基本面分析
3. ✅ 智能到期日优化（展示评分排名）
4. ✅ 对每个股票生成CSP策略
5. ✅ 被行权概率计算
6. ✅ 投资组合配置（基于夏普比率）
7. ✅ 生成HTML报告

Claude输出：
"根据分析，建议分配：
- AAPL: 60% - 年化52%
- MSFT: 40% - 年化48%

到期日优化详情：
- 2025-10-18评分85分（选中）
  - Theta效率：92分
  - 流动性：88分
  - Gamma风险：78分
- 2025-10-25评分78分
  - Theta效率：85分
  ...

详细报告已保存"
```

---

### 关键要点总结

1. **Tool是单个函数** - 做一件具体的事
   - CSP Tool = 给定到期日范围 → 选择最优一个 → 分析 → 返回推荐

2. **Prompt是AI工作流编排器** - 组合多个Tool完成复杂任务
   - CSP Prompts = 市场分析 + 选股 + 到期日优化 + 策略生成 + 组合配置

3. **到期日处理的区别**：
   - Tool：内部选择**一个**最优到期日，不展示过程
   - Prompt：先调用`optimal_expiration_selector`展示**所有候选**的评分排名，再用最优的调用Tool

4. **多股票支持的区别**：
   - Tool：每次只分析一个股票
   - Prompt：分析多个股票 + 智能分配投资组合权重

5. **两层设计的好处**：
   - Tool可以被任何地方复用（脚本、自动化、其他Prompt）
   - Prompt可以灵活编排业务逻辑
   - 关注点分离，易于维护

---

## 🎯 与 Claude Code 配合使用

1. **启动服务器**: 服务器将根据 `.mcp.json` 中的配置运行
2. **检查连接**: 在 Claude Code 中使用 `/mcp` 命令验证连接
3. **使用工具**: 通过 Claude Code 直接调用交易工具
4. **使用提示**: 访问提示进行引导式交互

### 示例用法

```
# 获取市场状态
使用 get_market_time_tool 获取当前美股市场状态

# 查看股票信息  
使用 stock_info_tool 查看 TSLA 的详细信息

# 查看财报日历
使用 earnings_calendar_tool 获取 AAPL 的财报日历和下次财报日期

# 获取股票历史数据和技术分析 🆕
使用 stock_history_tool 获取 TSLA 过去3个月的日线数据和技术指标
使用 stock_history_tool 获取 AAPL 指定日期范围的数据 (start_date="2023-01-01", end_date="2023-12-31")
使用 stock_history_tool 获取 NVDA 过去1年的周线数据 (date_range="1y", interval="weekly")

# 现金保障看跌期权策略分析 🆕
使用 cash_secured_put_strategy_tool_mcp 分析 AAPL 的收入导向策略 (purpose_type="income", duration="1w")
使用 cash_secured_put_strategy_tool_mcp 分析 TSLA 的折扣购买策略 (purpose_type="discount", duration="1m", capital_limit=50000)
使用 cash_secured_put_strategy_tool_mcp 获取 NVDA 的保守策略建议 (duration="2w", max_delta=-0.20, min_premium=2.0)

# Covered Call期权策略分析 🆕
使用 covered_call_strategy_tool_mcp 分析 AAPL 持仓的收入导向策略 (shares_owned=500, purpose_type="income", duration="1w")
使用 covered_call_strategy_tool_mcp 分析 TSLA 的减仓策略 (shares_owned=200, purpose_type="exit", duration="1m", avg_cost=220.0)
使用 covered_call_strategy_tool_mcp 获取 NVDA 大仓位策略建议 (shares_owned=1000, duration="2w", min_premium=3.0)

# 期权限价单成交概率预测 🆕
使用 option_limit_order_probability_tool_mcp 预测 AAPL 看跌期权卖单成交概率
  (symbol="AAPL", strike_price=145.0, expiration="2025-11-07", option_type="put",
   current_price=2.50, limit_price=2.80, order_side="sell")
使用 option_limit_order_probability_tool_mcp 预测 TSLA 看涨期权买单成交概率
  (symbol="TSLA", strike_price=250.0, expiration="2025-11-21", option_type="call",
   current_price=12.00, limit_price=10.50, order_side="buy")
使用 option_limit_order_probability_tool_mcp 分析 NVDA 限价单策略并获得替代建议
  (symbol="NVDA", strike_price=140.0, expiration="2025-12-19", option_type="put",
   current_price=3.20, limit_price=3.60, order_side="sell", analysis_window=14)

# 专注当日成交概率 🆕
使用 option_limit_order_probability_tool_mcp 获取 AAPL 当日成交概率（避免Greeks静态化误差）
  (symbol="AAPL", strike_price=145.0, expiration="2025-11-07", option_type="put",
   current_price=2.50, limit_price=2.80, order_side="sell", analysis_window=1)
  → 查看输出中的 first_day_fill_probability 字段

# 分析多个股票
同时获取 AAPL、NVDA、MSFT 的股票数据、财报时间、历史趋势和期权策略进行综合投资分析

# 综合期权策略分析 🆕  
结合 cash_secured_put 和 covered_call 策略，为现金和持股投资者提供完整的期权策略组合建议

# 收入生成CSP策略引擎提示 🆕
使用 income_generation_csp_engine 提示生成 AAPL 收入导向策略 (tickers=["AAPL"], cash_usd=50000, target_apy_pct=50)
使用 income_generation_csp_engine 提示生成多股票保守策略 (tickers=["SPY","QQQ"], cash_usd=25000, target_apy_pct=40, min_winrate_pct=80)
使用 income_generation_csp_engine 提示生成激进收入策略 (tickers=["TSLA","NVDA"], cash_usd=100000, target_apy_pct=60, min_winrate_pct=65)

# 股票建仓CSP策略引擎提示 🆕
使用 stock_acquisition_csp_engine 提示生成 AAPL 保守建仓策略 (tickers=["AAPL"], cash_usd=50000, target_allocation_probability=60.0, max_single_position_pct=20.0)
使用 stock_acquisition_csp_engine 提示生成多股票平衡建仓策略 (tickers=["AAPL","MSFT","GOOGL"], cash_usd=100000, target_allocation_probability=65.0, target_annual_return_pct=25.0)
使用 stock_acquisition_csp_engine 提示生成激进建仓策略 (tickers=["TSLA","NVDA"], cash_usd=200000, target_allocation_probability=75.0, max_single_position_pct=35.0)

# 期权仓位再平衡引擎提示 🆕
使用 option_position_rebalancer_engine 分析现有MU看跌期权仓位 (option_symbol="MU251017P00167500", position_size=-4, entry_price=2.03)
使用 option_position_rebalancer_engine 评估TSLA看涨期权持仓 (option_symbol="TSLA251017C00250000", position_size=-20, entry_price=12.00, risk_tolerance="conservative")
使用 option_position_rebalancer_engine 管理GOOG看跌期权策略 (option_symbol="GOOG251017P00150000", position_size=-10, entry_price=15.50, max_additional_capital=50000)
```

## 🚦 Development Workflow

1. **Planning Phase**
   - Use `specs/prd_v0_ai_enhanced.md` as template
   - Define your tools and prompts requirements

2. **Implementation**
   - Follow the modular structure
   - Implement tools in `src/mcp_server/tools/`
   - Implement prompts in `src/mcp_server/prompts/`

3. **Testing**
   - Write tests for all new features
   - Maintain test coverage above 80%

4. **Documentation**
   - Update this README with new features
   - Document tool and prompt signatures

## 📈 交易功能扩展

TradingAgent MCP 提供了一个强大的框架，可以轻松扩展更多交易相关功能。

### 当前功能

- **实时市场数据**: 通过 Tradier API 获取实时股票信息
- **市场时间跟踪**: 准确的美股交易时段状态
- **股票综合分析**: 价格、成交量、估值和技术指标
- **财报日历分析**: 智能财报事件跟踪和日期预测
- **历史数据分析**: 全套技术指标和趋势分析
- **现金保障看跌策略**: 专业级期权策略分析和风险评估 🆕

### 当前期权功能 🆕

1. **期权链分析**: ITM/ATM/OTM 智能分类和流动性评估
2. **希腊字母计算**: Delta、Gamma、Theta、Vega 和隐含波动率
3. **期权到期日选择**: 智能周期权/月期权选择算法
4. **现金保障看跌策略**: 收入导向和折扣购买双重策略
5. **Covered Call策略**: 持股投资者的收入和减仓策略双重目的 🆕
6. **技术分析集成**: 阻力位分析影响期权执行价选择 🆕
7. **风险管理**: 三级风险建议和专业订单格式化

### 可扩展功能

1. **更多期权策略**: 铁鹰式、日历价差、跨式套利等
2. **组合期权策略**: 多腿期权组合分析和优化
3. **波动率分析**: 隐含波动率曲面和波动率套利
4. **组合管理**: 投资组合跟踪、风险分析
5. **交易执行**: 下单、订单管理（需要相应授权）

### 产品需求文档 (PRDs)

`specs/` 目录包含项目的迭代开发 PRD：

- **人工版本**: `prd_v0.md` - 初始人工编写的需求
- **AI 增强版本**: `prd_v0_ai_enhanced.md` - AI 增强的详细规格

#### 版本管理
- 逐步推进版本：v1、v2、v3 等
- 每个版本代表：
  - 新功能添加
  - 主要架构变更  
  - 关键错误修复

### Claude Code 命令

位于 `.claude/commands/`：

#### 上下文启动命令
- **`prime.md`**: Claude 的通用上下文启动
- **`prime_cc.md`**: Claude Code 专用上下文启动

#### 规划命令
- **`quick-plan.md`**: 将人工 PRD 转换为详细技术规格

### 扩展指南

1. **从 PRD 开始**: 在 `specs/prd_v1.md` 中编写需求
2. **生成 AI 增强版本**: 使用 `/quick-plan` 创建详细规格
3. **实现功能**: 按照既定模式添加工具和提示
4. **记录进度**: 为每个主要版本更新 PRD

## 📚 相关文档

- [FastMCP 文档](https://github.com/fastmcp/fastmcp)
- [MCP 协议规范](https://modelcontextprotocol.io)
- [Claude Code MCP 指南](https://docs.anthropic.com/claude/docs/mcp)
- [Tradier 开发者文档](https://developer.tradier.com/)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 致谢

- 基于 [FastMCP](https://github.com/fastmcp/fastmcp) 框架构建
- 为 [Claude Code](https://claude.ai) 集成而设计
- 使用 [UV](https://github.com/astral-sh/uv) 进行包管理
- 市场数据由 [Tradier](https://tradier.com) 提供

## 📮 支持

如有问题、疑问或建议，请在 GitHub 上提交 issue。

---

*TradingAgent MCP - 为交易分析和市场数据访问而构建的专业 MCP 服务器。*