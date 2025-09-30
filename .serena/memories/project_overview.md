# TradingAgent MCP 项目概览

## 项目目的
TradingAgent MCP 是一个生产级的交易代理 MCP 服务器，基于 FastMCP 框架构建。主要提供：
- 实时股票市场数据和交易时段状态
- 综合股票信息分析
- 专业期权策略分析（现金担保看跌、备兑看涨策略）
- 智能期权到期日选择和风险评估
- 与 Claude Code 和其他 MCP 客户端的无缝集成

## 技术栈
- **Python 3.13+** - 主要编程语言
- **FastMCP 2.0+** - MCP 服务器框架
- **UV** - 现代 Python 包管理器
- **Pydantic** - 数据验证和模型
- **Pytest** - 测试框架
- **Tradier API** - 市场数据提供商
- **pandas & numpy** - 数据处理和技术指标计算

## 项目结构
```
src/
├── market/           # 市场数据处理
├── provider/tradier/ # Tradier API 集成
├── stock/           # 股票信息处理
├── option/          # 期权分析模块
├── strategy/        # 交易策略模块
└── mcp_server/      # MCP 服务器核心
    ├── tools/       # MCP 工具实现
    └── prompts/     # MCP 提示实现
```

## 核心功能模块
1. **市场数据模块**: 实时价格、交易时段、市场假期处理
2. **期权分析模块**: 期权链处理、希腊字母计算、智能到期日选择
3. **策略分析模块**: 现金担保PUT、备兑CALL策略分析
4. **风险管理模块**: 期权分配概率计算、风险评估