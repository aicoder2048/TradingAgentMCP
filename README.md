# TradingAgent MCP

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.0+-green.svg)](https://github.com/fastmcp/fastmcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个生产就绪的交易代理 MCP 服务器，基于 FastMCP 框架构建。提供股票市场数据、交易时段状态和综合股票信息的实时访问功能，与 Claude Code 和其他 MCP 客户端无缝集成。

## 🌟 核心功能

- **📊 实时市场数据**: 通过 Tradier API 提供实时股票信息和市场时间
- **🕐 交易时段跟踪**: 准确获取美股市场开盘状态和交易时段信息
- **📈 综合股票分析**: 详细的股票关键信息，包括价格、成交量、估值指标和技术指标
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
│       │   └── get_stock_history_tool.py # 历史数据工具 🆕
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
│   │   └── test_get_stock_history_tool.py # 历史数据工具测试 🆕
│   └── prompts/
│       └── test_hello_prompt.py
├── specs/
│   ├── prd_v0_ai_enhanced.md  # Product requirements document
│   ├── prd_v3_ai_enhanced.md  # 财报日历 PRD 🆕
│   └── prd_v4_ai_enhanced.md  # 历史数据 PRD 🆕
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

- **hello**: 简单的问候工具（演示用）
  - 输入: `name` (字符串)
  - 返回: 结构化的问候响应

### 提示

- **call_hello_multiple**: 演示提示功能
  - 生成多次调用 hello 工具的指令
  - 参数: `name` (字符串), `times` (整数)

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

# 分析多个股票  
同时获取 AAPL、NVDA、MSFT 的股票数据、财报时间和历史趋势进行投资分析
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

### 可扩展功能

1. **期权数据**: 期权链、隐含波动率、希腊字母
2. **技术分析**: 更多技术指标、图表模式识别
3. **基本面分析**: 财务报表、估值模型
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