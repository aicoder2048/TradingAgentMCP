# Stock Key Info MCP Server Tool

## Purpose

Create a MCP Server Tool for TradingAgentMCP MCP Server. This tool will take in a stock symbol and return the key information for the stock.

## Example of Returned Key Information for Tesla

```Text
⏺ ## TSLA (特斯拉) - 关键信息

  **基础信息**
  - 股票代码: TSLA
  - 收盘价: $442.790
  - 收盘时间: 09/24 16:00:00 (美东)

  **价格变动**
  - 涨跌额: +$16.940
  - 涨跌幅: +3.98%
  - 最高价: $444.210
  - 最低价: $429.030
  - 今开: $429.830
  - 昨收: $425.850

  **交易数据**
  - 成交额: 408.53亿
  - 成交量: 9313.36万股
  - 换手率: 3.35%

  **估值指标**
  - 市盈率TTM: 263.57
  - 市盈率(静): 217.05
  - 市净率: 19.04
  - 总市值: 1.47万亿
  - 总股本: 33.25亿
  - 流通值: 1.23万亿
  - 流通股: 27.78亿

  **技术指标**
  - 52周最高: $488.540
  - 52周最低: $212.110
  - 历史最高: $488.540
  - 历史最低: $0.999
  - Beta系数: 2.334
  - 振幅: 3.57%
  - 平均价: $438.650
  - 每手: 1股

  **盘前交易**
  - 盘前价格: $440.680
  - 盘前变动: -$2.110 (-0.48%)
  - 盘前时间: 06:36 (美东)
```

## Provider

- We use Tradier and Tradier API to obtain real, non-mock, and real-time, non-mock, data.
- The Tradier API requires an access token, which could be obtained from .env

## Refeence Implementation
- Let's create Traider Client at src/tradier_client.py, pls refer to its reference implementation at /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/tradier_client.md
- Double check the reference implementation for correctness and logics. You may refer tradier api docs at /Users/szou/Python/Playground/TradingAgentMCP/ai_docs/tradier_api_docs.md.
- There may be functions in tradier reference implementation not used for this v2 prd, but we could still implement them for forseeable future use or future versions of PRD.

write the enhanced prd to specs/prd_v2_ai_enhanced.md
