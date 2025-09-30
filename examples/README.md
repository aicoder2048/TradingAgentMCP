# Claude Code MCP Tools 使用指南

在Claude Code中通过自然语言直接调用期权策略分析工具。

---

## 🎯 核心概念

本项目提供两个MCP Server工具：

1. **cash_secured_put_strategy_tool_mcp** - 现金担保看跌期权策略
   - 用途：卖PUT收取权利金 或 以折价买入股票

2. **covered_call_strategy_tool_mcp** - 备兑看涨期权策略
   - 用途：持仓增加收入 或 以更高价格卖出股票

**无需编程** - 直接用自然语言在Claude Code中调用！

---

## 📁 文件说明

### 🔥 [QUICK_PROMPTS.md](./QUICK_PROMPTS.md) - 快速参考
**最常用！** 包含：
- 5个最常用提示词（复制即用）
- 通用模板（填空即可）
- 进阶用法
- 参数速查表

**适合**:
- ✅ 快速查找需要的提示词
- ✅ 不想读长文档
- ✅ 立即开始使用

---

### 📚 [CLAUDE_CODE_PROMPTS.md](./CLAUDE_CODE_PROMPTS.md) - 完整案例集
详细的20个实战案例，包含：

**基础策略（案例1-5）**
- 周度收入策略
- 月度折价建仓
- 激进收入策略
- 长期价值投资
- 多股票对比

**Covered Call（案例6-8）**
- 持仓收入增强
- 战略减仓退出
- 大仓位分批操作

**组合策略（案例9-10）**
- Wheel策略设计
- 风险对冲组合

**深度分析（案例11-12）**
- 完整期权链分析
- 收益率优化

**特殊场景（案例13-15）**
- 财报前调整
- 高波动环境
- Delta中性组合

**动态调整（案例16-17）**
- 滚动调整策略
- 行权价调整

**实战整合（案例18-20）**
- 完整交易计划
- 市场环境适配
- 投资组合优化

**适合**:
- ✅ 深入学习各种场景
- ✅ 寻找特定用例
- ✅ 理解策略组合

---

## 🚀 快速开始（3步）

### 第1步：打开文件
打开 [QUICK_PROMPTS.md](./QUICK_PROMPTS.md)

### 第2步：选择提示词
选择最常用的5个中的任意一个，比如：

```
使用cash_secured_put_strategy_tool_mcp分析AAPL的周度收入策略：
- 股票：AAPL
- 目的：income
- 周期：1w
- 资金：$50,000
```

### 第3步：在Claude Code中使用
1. 复制提示词
2. 粘贴到Claude Code对话框
3. 修改股票代码和参数（可选）
4. 发送
5. Claude会自动调用MCP工具并返回分析结果

---

## 💡 使用示例

### 示例1：在Claude Code中问

**您的输入:**
```
使用cash_secured_put_strategy_tool_mcp分析TSLA的周度收入策略：
- 股票：TSLA
- 目的：income（避免被分配）
- 周期：1w
- 资金：$75,000
```

**Claude会自动:**
1. 调用 `cash_secured_put_strategy_tool_mcp`
2. 分析TSLA当前价格和期权链
3. 返回三个风险级别的推荐：
   - Conservative（保守）
   - Balanced（平衡）
   - Aggressive（激进）
4. 展示关键指标：
   - 行权价
   - Delta值
   - 权利金
   - 年化收益率
   - 胜率

---

### 示例2：组合策略

**您的输入:**
```
我持有500股AAPL（成本$145），想通过covered call增加收入。
使用covered_call_strategy_tool_mcp分析：
- 周期：1w
- 目的：income（不想被call走）

请推荐保守策略，并说明被call走的概率。
```

**Claude会:**
1. 调用工具分析当前市场
2. 推荐保守策略（高胜率，低被call概率）
3. 解释风险和收益
4. 给出执行建议

---

## 📊 两个工具的对比

| 特性 | Cash Secured Put | Covered Call |
|------|-----------------|--------------|
| **前提条件** | 有现金 | 持有股票（≥100股） |
| **主要目的** | 收权利金 / 折价买入 | 增加收入 / 高价卖出 |
| **适用场景** | 看好股票想买入 | 已持有想增收 |
| **风险** | 可能被分配股票 | 可能被call走 |
| **收益来源** | 权利金 | 权利金 |
| **资金需求** | 行权价×100×合约数 | 0（已有股票） |

---

## 🎓 学习路径

### Level 1: 基础入门 (5分钟)
1. 打开 [QUICK_PROMPTS.md](./QUICK_PROMPTS.md)
2. 使用提示词 1️⃣（周度收入CSP）
3. 在Claude Code中测试

### Level 2: 探索场景 (15分钟)
1. 打开 [CLAUDE_CODE_PROMPTS.md](./CLAUDE_CODE_PROMPTS.md)
2. 阅读案例1-8（基础策略）
3. 尝试2-3个不同的提示词

### Level 3: 高级应用 (30分钟)
1. 学习案例9-12（组合策略）
2. 尝试Wheel策略和收益率优化
3. 根据自己的需求修改提示词

### Level 4: 实战应用 (持续)
1. 根据市场环境选择策略
2. 使用案例13-20的特殊场景提示词
3. 构建自己的投资组合

---

## 📋 常见问题

### Q1: 我必须要懂编程吗？
**A:** 不需要！直接复制提示词到Claude Code即可。

### Q2: 参数可以改吗？
**A:** 可以随意修改股票代码、周期、金额等参数。

### Q3: 可以用中文描述吗？
**A:** 可以！Claude会理解中文并转换为正确的参数。

### Q4: 如何知道结果是否可靠？
**A:** 工具使用实时市场数据，建议在交易时段使用，并导出CSV查看完整数据。

### Q5: 可以同时分析多只股票吗？
**A:** 可以！参考案例5（多股票对比）的提示词。

### Q6: 提示词没有我需要的场景怎么办？
**A:** 使用通用模板，或参考类似案例修改。Claude很灵活！

---

## 🎯 最佳实践

### ✅ 推荐做法

1. **从简单开始** - 先用QUICK_PROMPTS中的基础提示词
2. **交易时段使用** - 获得最准确的实时数据
3. **对比分析** - 请求分析多个周期或股票
4. **追问细节** - 根据结果继续问"如果...怎么办"
5. **查看CSV** - 导出的CSV包含完整期权链数据

### ❌ 避免的做法

1. **过于模糊** - 提示词要包含必要参数
2. **忽略风险** - 关注胜率和分配概率
3. **只看收益** - 要平衡风险和收益
4. **盲目跟随** - 结果仅供参考，需自行判断

---

## 🛠️ 环境要求

### MCP Server配置

确保 `claude_desktop_config.json` 中已配置：

```json
{
  "mcpServers": {
    "TradingAgentMCP": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/TradingAgentMCP",
        "run",
        "trading-agent-mcp"
      ],
      "env": {
        "TRADIER_API_TOKEN": "your_token_here"
      }
    }
  }
}
```

### API Token

```bash
export TRADIER_API_TOKEN="your_tradier_token"
```

获取Token: https://developer.tradier.com/

---

## 📖 相关资源

### MCP工具列表
查看所有可用的MCP工具：
```
在Claude Code中问：列出所有TradingAgentMCP的工具
```

主要工具包括：
- `cash_secured_put_strategy_tool_mcp` - CSP策略
- `covered_call_strategy_tool_mcp` - CC策略
- `stock_info_tool` - 股票信息
- `options_chain_tool_mcp` - 期权链
- `option_assignment_probability_tool_mcp` - 分配概率
- `get_market_time_tool` - 市场时间
- `earnings_calendar_tool` - 财报日历

### 策略文档
- [Cash Secured Put策略详解](../docs/strategies/cash_secured_put.md)
- [Covered Call策略详解](../docs/strategies/covered_call.md)

---

## ⚠️ 免责声明

- 所有分析结果仅供教育和研究目的
- 不构成投资建议
- 期权交易存在重大风险，可能损失全部本金
- 请根据自身情况谨慎决策
- 实际交易前请咨询专业投资顾问

---

## 🎉 开始使用

**现在就试试！**

1. 打开 [QUICK_PROMPTS.md](./QUICK_PROMPTS.md)
2. 复制提示词 1️⃣
3. 在Claude Code中粘贴并修改股票代码
4. 发送，查看结果
5. 根据需要追问或调整参数

**祝您投资顺利！** 🚀