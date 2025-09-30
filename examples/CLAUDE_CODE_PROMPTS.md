# Claude Code MCP Tools 提示词模板

直接复制以下提示词到Claude Code中使用，Claude会自动调用相应的MCP工具。

---

## 📋 Cash Secured Put (CSP) 策略提示词

### 案例1: 周度收入策略

```
请使用cash_secured_put_strategy_tool_mcp分析AAPL的周度收入策略：
- 股票：AAPL
- 目的：income（收入导向，避免被分配）
- 周期：1w（1周）
- 资金限制：$500,000

请展示三个风险级别（conservative, balanced, aggressive）的推荐，并重点分析年化收益率和胜率。
```

---

### 案例2: 月度折价建仓

```
我想通过卖PUT以折价买入NVDA股票，请使用cash_secured_put_strategy_tool_mcp分析：
- 股票：NVDA
- 目的：discount（折价建仓，欢迎被分配）
- 周期：1m（1个月）
- 资金限制：$100,000
- 最低权利金要求：$5.00

请重点说明每个建议的有效买入成本和折价幅度。
```

---

### 案例3: 2周激进收入策略

```
请分析TSLA的激进收入策略（cash_secured_put_strategy_tool_mcp）：
- 股票：TSLA
- 目的：income
- 周期：2w
- 资金：$75,000
- Delta限制：不超过-0.35

我想看到aggressive级别的建议，重点关注年化收益率和分配风险。
```

---

### 案例4: 长期价值建仓（3个月）

```
我看好GOOGL长期前景，想耐心等待折价买入机会。请用cash_secured_put_strategy_tool_mcp分析：
- 股票：GOOGL
- 策略：discount（长期建仓）
- 周期：3m（3个月）
- 资金：$150,000
- 最低权利金：$10

请分析balanced策略，说明时间价值衰减特征和合理的分配概率。
```

---

### 案例5: 多只股票对比分析

```
请使用cash_secured_put_strategy_tool_mcp分别分析以下三只股票的1周收入策略，然后对比哪个最适合保守型投资者：

1. AAPL - income, 1w, 资金$50,000
2. MSFT - income, 1w, 资金$50,000
3. SPY - income, 1w, 资金$50,000

请对比它们的：
- 年化收益率
- 胜率
- Delta值
- 流动性

并给出推荐理由。
```

---

## 📋 Covered Call (CC) 策略提示词

### 案例6: 周度收入增强

```
我持有500股AAPL（平均成本$145.50），想通过卖出covered call增加收入。请用covered_call_strategy_tool_mcp分析：
- 股票：AAPL
- 持仓：500股
- 平均成本：$145.50
- 目的：income（不想被call走）
- 周期：1w

请展示三个风险级别的推荐，说明每种策略被call走的概率。
```

---

### 案例7: 战略减仓退出

```
我持有300股MSFT（成本$320/股），现在想部分获利了结，但希望以更高价格卖出。请使用covered_call_strategy_tool_mcp：
- 股票：MSFT
- 持仓：300股
- 成本：$320
- 目的：exit（愿意被call走）
- 周期：1m（1个月）

请重点说明有效卖出价格和相比成本的总收益。
```

---

### 案例8: 大仓位分批操作

```
我持有1000股TSLA（成本$250/股），想分批卖出covered call。请用covered_call_strategy_tool_mcp分析：
- 股票：TSLA
- 持仓：1000股
- 成本：$250
- 目的：income
- 周期：2w

请建议如何分批操作（比如先卖500股对应的5张合约，保留500股灵活性）。
```

---

## 🎯 组合策略提示词

### 案例9: Wheel策略设计

```
我想在AAPL上运行Wheel策略。请帮我设计：

第一步：使用cash_secured_put_strategy_tool_mcp分析
- 股票：AAPL
- 目的：discount（准备接受分配）
- 周期：2w
- 资金：$50,000

第二步：如果被分配获得股票后，使用covered_call_strategy_tool_mcp分析
- 股票：AAPL
- 持仓：假设被分配300股
- 目的：income
- 周期：2w

请说明完整的Wheel策略流程和预期收益。
```

---

### 案例10: 风险对冲组合

```
我持有500股NVDA，同时想通过CSP建仓买入更多。请分别分析：

1. 对现有持仓卖covered call（covered_call_strategy_tool_mcp）：
   - 持仓：500股
   - 目的：income
   - 周期：1w

2. 同时卖PUT准备加仓（cash_secured_put_strategy_tool_mcp）：
   - 资金：$70,000
   - 目的：discount
   - 周期：1w

请分析这个组合策略的风险和收益特征。
```

---

## 📊 深度分析提示词

### 案例11: 完整期权链分析

```
请对AAPL进行完整的现金担保PUT策略分析：

1. 使用cash_secured_put_strategy_tool_mcp分析1周期权：
   - 目的：income
   - 周期：1w
   - 资金：$50,000

2. 同时分析1个月期权：
   - 目的：discount
   - 周期：1m
   - 资金：$50,000

然后对比：
- 哪个周期的年化收益率更高？
- 哪个周期更适合当前的波动率环境？
- 时间价值衰减曲线有何不同？
```

---

### 案例12: 收益率优化分析

```
我有$100,000资金，想通过CSP策略最大化月度收益。请使用cash_secured_put_strategy_tool_mcp分别分析：

1. AAPL - income, 1w
2. AAPL - income, 2w
3. AAPL - income, 1m

计算每种策略的：
- 月度收益金额
- 月度收益率
- 风险调整后收益
- 资金使用效率

推荐最优组合（比如部分资金1w周期滚动，部分资金1m周期稳定）。
```

---

## 💡 特殊场景提示词

### 案例13: 财报前策略调整

```
TSLA即将发布财报，我想调整期权策略规避风险。请：

1. 使用earnings_calendar_tool查看TSLA的财报日期

2. 然后用cash_secured_put_strategy_tool_mcp分析：
   - 目的：income
   - 周期：选择避开财报日期的到期日
   - 资金：$75,000

请说明如何利用到期日选择来规避财报波动。
```

---

### 案例14: 高波动环境策略

```
当前市场波动率较高，我想利用这个机会。请用cash_secured_put_strategy_tool_mcp分析：

1. 高波动股票TSLA：
   - 目的：income
   - 周期：1w
   - 资金：$75,000

2. 低波动股票SPY：
   - 目的：income
   - 周期：1w
   - 资金：$50,000

对比高波动和低波动股票的期权策略差异，以及适用场景。
```

---

### 案例15: Delta中性组合

```
我想构建一个Delta中性的期权组合。请：

1. 用cash_secured_put_strategy_tool_mcp分析AAPL的CSP：
   - 目的：income
   - 周期：1m
   - Delta要求：约-0.30

2. 用covered_call_strategy_tool_mcp分析持有的AAPL的CC：
   - 持仓：500股
   - 目的：income
   - 周期：1m
   - Delta要求：约+0.30

说明如何通过同时持有股票、卖PUT和卖CALL来实现Delta中性。
```

---

## 🔄 动态调整提示词

### 案例16: 滚动调整策略

```
我上周卖出的AAPL PUT期权（行权价$145）现在权利金已跌至50%。请：

1. 分析是否应该平仓获利（当前权利金情况）

2. 如果平仓，用cash_secured_put_strategy_tool_mcp分析新的1周策略：
   - 目的：income
   - 周期：1w
   - 资金：从平仓释放的资金

3. 对比继续持有vs滚动调整的收益差异
```

---

### 案例17: 行权价调整分析

```
我持有的MSFT covered call（行权价$400）即将到期，但股价涨到了$405。请：

1. 分析被call走的概率和影响

2. 如果被call走，用cash_secured_put_strategy_tool_mcp分析如何重新建仓：
   - 目的：discount（想买回来）
   - 周期：1w
   - 资金：从卖出获得的资金

3. 说明完整的调整流程和预期成本
```

---

## 📈 实战场景整合

### 案例18: 完整交易计划

```
我是新手投资者，有$50,000资金，想从AAPL开始学习期权交易。请制定完整计划：

第一阶段 - 学习CSP（1-2个月）：
使用cash_secured_put_strategy_tool_mcp分析AAPL的conservative策略：
- 目的：income
- 周期：1w
- 资金：$25,000（只用一半资金）

第二阶段 - 如果被分配：
使用covered_call_strategy_tool_mcp分析：
- 目的：income
- 周期：1w

第三阶段 - Wheel策略循环

请详细说明每个阶段的操作步骤、风险点和预期收益。
```

---

### 案例19: 市场环境适配

```
请根据当前市场环境（使用get_market_time_tool获取），分析最适合的期权策略：

1. 如果当前是盘中交易时段：
   用cash_secured_put_strategy_tool_mcp实时分析AAPL的1w策略

2. 如果当前是盘后：
   说明应该等待下个交易日的策略

3. 考虑周五到期的期权时间衰减加速特性

给出具体的入场时机建议。
```

---

### 案例20: 投资组合优化

```
我有以下持仓和资金，请优化整体期权策略：

现有持仓：
- AAPL 500股（成本$145）
- MSFT 300股（成本$320）

可用资金：
- $100,000

请使用MCP工具分析：

1. AAPL持仓的covered_call策略（covered_call_strategy_tool_mcp）
2. MSFT持仓的covered_call策略（covered_call_strategy_tool_mcp）
3. 用现金建仓GOOGL的CSP策略（cash_secured_put_strategy_tool_mcp）

优化目标：
- 总体年化收益率最大化
- 风险分散（不同股票、不同到期日）
- 资金使用效率最优

请给出具体的配置建议和预期收益。
```

---

## 🎓 使用技巧

### 提示词编写要点

1. **明确指定MCP工具名称**
   - `cash_secured_put_strategy_tool_mcp` - CSP策略
   - `covered_call_strategy_tool_mcp` - CC策略
   - 其他辅助工具如 `get_market_time_tool`, `earnings_calendar_tool` 等

2. **提供完整参数**
   - 股票代码（symbol）
   - 策略目的（purpose_type: income/discount或exit）
   - 时间周期（duration: 1w, 2w, 1m等）
   - 资金或持仓信息

3. **说明分析重点**
   - 关注哪个风险级别（conservative/balanced/aggressive）
   - 重点关注哪些指标（年化收益率、胜率、Delta等）
   - 需要对比分析的维度

4. **请求具体输出**
   - 是否需要解释推荐理由
   - 是否需要风险提示
   - 是否需要执行建议

---

## 📝 提示词模板

### 通用CSP模板

```
请使用cash_secured_put_strategy_tool_mcp分析[股票代码]的现金担保PUT策略：
- 股票：[SYMBOL]
- 目的：[income/discount]
- 周期：[1w/2w/1m/3m/6m/1y]
- 资金限制：$[金额]
- [可选]最低权利金：$[金额]
- [可选]Delta限制：[值]

请展示[conservative/balanced/aggressive/all]级别的推荐，重点分析[关注点]。
```

### 通用CC模板

```
请使用covered_call_strategy_tool_mcp分析[股票代码]的备兑看涨期权策略：
- 股票：[SYMBOL]
- 持仓：[数量]股
- 平均成本：$[成本]
- 目的：[income/exit]
- 周期：[1w/2w/1m/3m/6m]
- [可选]最低权利金：$[金额]

请展示[conservative/balanced/aggressive/all]级别的推荐，重点分析[关注点]。
```

---

## ⚠️ 重要提示

1. **Claude会自动识别并调用MCP工具**
   - 不需要写代码
   - 不需要导入模块
   - 只需要用自然语言描述需求

2. **参数灵活性**
   - 可以用中文描述参数（Claude会转换）
   - 可以省略可选参数
   - 可以添加额外的分析要求

3. **组合使用**
   - 可以在一个提示词中请求多个工具
   - 可以请求对比分析
   - 可以请求深度解读

4. **实时数据**
   - MCP工具会使用实时市场数据
   - 分析结果基于当前价格和期权链
   - 建议在交易时段使用以获得最准确数据

---

## 🚀 快速开始

**第1步**: 复制任意一个案例提示词

**第2步**: 粘贴到Claude Code对话框

**第3步**: 根据需要修改股票代码、参数

**第4步**: 发送，等待Claude调用MCP工具并返回分析

**第5步**: 根据分析结果提出后续问题或调整参数

---

**开始使用**: 从案例1或案例6开始，体验MCP工具的强大功能！
