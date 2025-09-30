# 快速提示词参考

复制即用的Claude Code提示词模板。

---

## 🎯 最常用的5个提示词

### 1️⃣ 周度收入 - CSP
```
使用cash_secured_put_strategy_tool_mcp分析AAPL的周度收入策略：
- 股票：AAPL
- 目的：income
- 周期：1w
- 资金：$50,000
```

### 2️⃣ 月度折价建仓 - CSP
```
使用cash_secured_put_strategy_tool_mcp分析NVDA的折价建仓：
- 股票：NVDA
- 目的：discount
- 周期：1m
- 资金：$100,000
```

### 3️⃣ 持仓收入增强 - CC
```
使用covered_call_strategy_tool_mcp分析我的AAPL持仓：
- 股票：AAPL
- 持仓：500股
- 成本：$145.50
- 目的：income
- 周期：1w
```

### 4️⃣ 战略减仓 - CC
```
使用covered_call_strategy_tool_mcp分析MSFT减仓：
- 股票：MSFT
- 持仓：300股
- 成本：$320
- 目的：exit
- 周期：1m
```

### 5️⃣ 多股票对比
```
使用cash_secured_put_strategy_tool_mcp分别分析AAPL、MSFT、SPY的1w收入策略（各$50,000），然后对比推荐最适合保守投资者的。
```

---

## 📋 通用模板

### CSP模板
```
使用cash_secured_put_strategy_tool_mcp分析[股票]：
- 股票：[AAPL/TSLA/NVDA...]
- 目的：[income/discount]
- 周期：[1w/2w/1m/3m/6m]
- 资金：$[金额]
```

### CC模板
```
使用covered_call_strategy_tool_mcp分析[股票]：
- 股票：[AAPL/MSFT...]
- 持仓：[数量]股
- 成本：$[价格]
- 目的：[income/exit]
- 周期：[1w/2w/1m/3m]
```

---

## 🔥 进阶用法

### Wheel策略
```
帮我设计AAPL的Wheel策略：
1. 先用cash_secured_put_strategy_tool_mcp分析discount策略（2w, $50k）
2. 如被分配，再用covered_call_strategy_tool_mcp分析income策略（2w）
说明完整流程和预期收益。
```

### 风险对冲
```
我持有500股NVDA，同时想加仓。请：
1. 用covered_call_strategy_tool_mcp分析现有持仓（income, 1w）
2. 用cash_secured_put_strategy_tool_mcp分析加仓策略（discount, 1w, $70k）
分析这个组合的风险收益。
```

### 收益率优化
```
$100,000资金，用cash_secured_put_strategy_tool_mcp分析AAPL的1w、2w、1m三种周期，对比年化收益率，推荐最优配置。
```

---

## ⚡ 填空式提示词

**只需修改【】内容即可使用**

### CSP收入策略
```
使用cash_secured_put_strategy_tool_mcp分析【AAPL】的收入策略，周期【1w】，资金【$50,000】，目的是避免被分配，重点看年化收益率和胜率。
```

### CSP折价策略
```
使用cash_secured_put_strategy_tool_mcp分析【NVDA】的折价建仓，周期【1m】，资金【$100,000】，我愿意被分配，请说明有效买入成本。
```

### CC收入增强
```
使用covered_call_strategy_tool_mcp，我持有【500】股【AAPL】（成本【$145】），周期【1w】，不想被call走，请推荐保守策略。
```

### CC减仓退出
```
使用covered_call_strategy_tool_mcp，我持有【300】股【MSFT】（成本【$320】），周期【1m】，愿意被call走，请说明有效卖出价。
```

---

## 🎯 按需求选择

### 我想要...

| 需求 | 使用的提示词 |
|------|-------------|
| 每周赚权利金 | 提示词 1️⃣ (周度收入CSP) |
| 低价买入股票 | 提示词 2️⃣ (月度折价CSP) |
| 持股增加收入 | 提示词 3️⃣ (持仓收入CC) |
| 高价卖出股票 | 提示词 4️⃣ (战略减仓CC) |
| 对比多只股票 | 提示词 5️⃣ (多股票对比) |
| 完整策略计划 | Wheel策略 |
| 同时买入卖出 | 风险对冲 |

---

## 💡 使用技巧

1. **直接复制粘贴** - 所有提示词都可以直接在Claude Code中使用
2. **修改参数** - 改股票代码、金额、周期等
3. **添加要求** - 可以在提示词后追加"请重点分析..."等要求
4. **组合使用** - 可以在一个提示词中请求多个分析
5. **后续提问** - 根据结果提出"如果被分配怎么办"等问题

---

## 📊 参数速查

### Duration (周期)
- `1w` = 1周 (5-10天)
- `2w` = 2周 (10-17天)
- `1m` = 1月 (21-35天)
- `3m` = 3月 (50-75天)
- `6m` = 6月 (135-165天)

### Purpose (目的)
- CSP: `income` (收入) / `discount` (折价)
- CC: `income` (保留) / `exit` (减仓)

### Risk Level (风险)
- `conservative` - 保守 (胜率高)
- `balanced` - 平衡 (推荐)
- `aggressive` - 激进 (收益高)

---

## 🚀 快速开始

1. **选择一个提示词** - 从最常用的5个中选
2. **复制到Claude Code** - 完整复制
3. **修改参数** - 改成你的股票和金额
4. **发送** - Claude自动调用MCP工具
5. **查看结果** - 获得专业分析

---

**现在就试试**: 复制提示词 1️⃣，改成你想分析的股票，粘贴到Claude Code！