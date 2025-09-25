# PRD v5 - 期权链 MCP 服务器工具实施计划

## 项目概述

本文档详细规划期权链 (Options Chains) MCP 服务器工具的实施方案。该工具将为 TradingAgentMCP 项目添加全面的期权数据分析功能，包括期权链检索、到期日管理和执行价格查询等核心功能。

## 问题陈述与目标

### 核心问题
- 当前 TradingAgent MCP 仅提供股票数据，缺乏期权交易分析功能
- 期权交易者需要获取期权链数据、希腊字母、到期日和执行价格等关键信息
- 需要高效的数据导出机制以支持进一步的量化分析

### 项目目标
1. **期权链数据检索**: 创建 MCP 工具获取指定股票的期权链数据
2. **到期日管理**: 实现期权到期日查询功能
3. **执行价格查询**: 提供特定到期日的可用执行价格列表
4. **数据持久化**: 自动将期权数据导出为 CSV 格式便于分析
5. **智能筛选**: 提供 ITM、ATM、OTM 期权的智能分类和筛选

## 技术架构设计

### 整体架构
```
Claude Code Client
        ↓ (MCP Protocol)
MCP Server (FastMCP)
        ↓
┌─────────────────────────────────────┐
│     Options Chain MCP Tool          │
├─────────────────────────────────────┤
│ MCP Tools:                          │
│ • options_chain_tool                │
├─────────────────────────────────────┤
│ Local Functions:                    │
│ • get_option_expiration_dates       │
│ • get_option_strikes                │
│ • process_options_data              │
├─────────────────────────────────────┤
│ Data Processing:                    │
│ • Options classification (ITM/ATM/OTM) │
│ • Greeks calculation integration    │
│ • CSV export with naming convention│
└─────────────────────────────────────┘
        ↓ (REST API)
    Tradier API
        ↓ (Options Endpoints)
   • /v1/markets/options/chains
   • /v1/markets/options/expirations
   • /v1/markets/options/strikes
```

### 模块结构
```
src/
├── option/                    # 新增期权模块
│   ├── __init__.py
│   ├── options_chain.py       # 期权链核心功能
│   ├── option_expiration_dates.py  # 到期日管理
│   └── option_strikes.py      # 执行价格查询
├── mcp_server/
│   └── tools/
│       └── get_options_chain_tool.py  # MCP 工具实现
└── provider/tradier/
    └── client.py              # 扩展 Tradier 客户端
```

## 详细实施计划

### 阶段一：核心数据结构与 API 集成

#### 1.1 扩展 Tradier API 客户端
**文件**: `src/provider/tradier/client.py`

**新增方法**:
```python
def get_option_chain(
    self,
    symbol: str,
    expiration: str,
    include_greeks: bool = True
) -> List[OptionContract]:
    """获取指定股票和到期日的期权链数据"""

def get_option_expirations(
    self,
    symbol: str,
    include_all_roots: bool = True
) -> List[OptionExpiration]:
    """获取股票的所有可用到期日"""

def get_option_strikes(
    self,
    symbol: str,
    expiration: str,
    include_all_roots: bool = True
) -> List[float]:
    """获取指定到期日的所有执行价格"""
```

**数据模型扩展**:
```python
@dataclass
class OptionContract:
    symbol: str
    strike: float
    expiration_date: str
    option_type: str  # "call" or "put"
    bid: Optional[float] = None
    ask: Optional[float] = None
    last: Optional[float] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    greeks: Optional[Dict[str, float]] = None

@dataclass
class OptionExpiration:
    date: str
    contract_size: int
    expiration_type: str
    strikes: List[float]
```

#### 1.2 期权链核心处理模块
**文件**: `src/option/options_chain.py`

**核心功能**:
```python
async def get_options_chain_data(
    symbol: str,
    expiration: str,
    option_type: str,
    include_greeks: bool = True
) -> Dict[str, Any]:
    """
    获取并处理期权链数据

    Args:
        symbol: 股票代码 (e.g., "AAPL", "TSLA")
        expiration: 到期日 (YYYY-MM-DD format)
        option_type: 期权类型 ("call", "put", "both")
        include_greeks: 是否包含希腊字母 (默认 True)

    Returns:
        包含期权数据、分类信息和统计的字典
    """

def classify_options_by_moneyness(
    options: List[OptionContract],
    underlying_price: float
) -> Dict[str, List[OptionContract]]:
    """
    按价值性分类期权 (ITM/ATM/OTM)

    Returns:
        {
            "itm": [...],    # In-The-Money options
            "atm": [...],    # At-The-Money options
            "otm": [...]     # Out-Of-The-Money options
        }
    """

def export_options_to_csv(
    options_data: Dict[str, Any],
    symbol: str,
    option_type: str,
    expiration: str
) -> str:
    """
    导出期权数据到 CSV 文件

    文件命名格式: <symbol>_<option_type>_<expiration>_<timestamp>.csv
    保存位置: ./data/

    Returns:
        CSV 文件的完整路径
    """
```

#### 1.3 到期日管理模块
**文件**: `src/option/option_expiration_dates.py`

```python
def get_option_expiration_dates(
    symbol: str,
    min_days: Optional[int] = None,
    max_days: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    获取期权到期日列表

    Args:
        symbol: 股票代码
        min_days: 最小到期天数过滤
        max_days: 最大到期天数过滤

    Returns:
        [{
            "date": "2024-01-19",
            "days_to_expiration": 30,
            "expiration_type": "standard",
            "contract_size": 100,
            "available_strikes": [...]
        }]
    """

def get_next_expiration_date(symbol: str) -> Optional[str]:
    """获取下一个最近的到期日"""

def filter_expirations_by_days(
    expirations: List[Dict],
    min_days: int = 0,
    max_days: int = 365
) -> List[Dict]:
    """按到期天数过滤到期日列表"""
```

#### 1.4 执行价格查询模块
**文件**: `src/option/option_strikes.py`

```python
def get_option_strikes(
    symbol: str,
    expiration: str,
    strike_range_pct: Optional[float] = None
) -> Dict[str, Any]:
    """
    获取指定到期日的执行价格列表

    Args:
        symbol: 股票代码
        expiration: 到期日 (YYYY-MM-DD)
        strike_range_pct: 执行价格范围百分比 (例如 0.1 = ±10%)

    Returns:
        {
            "symbol": "AAPL",
            "expiration": "2024-01-19",
            "underlying_price": 150.00,
            "all_strikes": [...],
            "filtered_strikes": [...],
            "atm_strike": 150.0
        }
    """

def find_atm_strike(
    strikes: List[float],
    underlying_price: float
) -> float:
    """查找最接近股价的执行价格 (ATM)"""

def filter_strikes_by_range(
    strikes: List[float],
    center_price: float,
    range_pct: float
) -> List[float]:
    """按价格范围过滤执行价格"""
```

### 阶段二：MCP 工具实现

#### 2.1 期权链 MCP 工具
**文件**: `src/mcp_server/tools/get_options_chain_tool.py`

```python
async def options_chain_tool(
    symbol: str,
    expiration: str,
    option_type: str = "both",
    include_greeks: bool = True
) -> Dict[str, Any]:
    """
    获取期权链数据并返回分析结果

    MCP 工具参数:
        symbol: 股票代码 (必需)
        expiration: 到期日 YYYY-MM-DD (必需)
        option_type: "call", "put", 或 "both" (默认 "both")
        include_greeks: 是否包含希腊字母 (默认 True)

    Returns:
        {
            "csv_file_path": "/path/to/saved/file.csv",
            "summary": {
                "symbol": "AAPL",
                "expiration": "2024-01-19",
                "underlying_price": 150.00,
                "total_options": 200,
                "calls_count": 100,
                "puts_count": 100
            },
            "itm_options": [...],      # 20个 ITM 期权
            "atm_options": [...],      # ATM 期权 (如有)
            "otm_options": [...],      # 20个 OTM 期权
            "greeks_summary": {
                "avg_delta": 0.5,
                "avg_gamma": 0.02,
                "avg_theta": -0.1,
                "avg_vega": 0.3
            }
        }
    """
```

#### 2.2 MCP 服务器注册
**文件**: `src/mcp_server/server.py`

```python
@mcp.tool()
async def options_chain_tool(
    symbol: str,
    expiration: str,
    option_type: str = "both",
    include_greeks: bool = True
) -> Dict[str, Any]:
    """获取股票期权链数据和分析"""
    return await get_options_chain_tool.options_chain_tool(
        symbol, expiration, option_type, include_greeks
    )
```

### 阶段三：数据处理与导出

#### 3.1 CSV 导出功能
**规格要求**:
- **文件命名**: `<symbol>_<option_type>_<expiration>_<timestamp>.csv`
- **保存位置**: `./data/` 目录
- **字段结构**:
```csv
symbol,strike_price,expiration_date,option_type,bid,ask,mid_price,last,volume,open_interest,implied_volatility,delta,gamma,theta,vega,rho,intrinsic_value,time_value,moneyness,days_to_expiration,in_the_money
AAPL,145.0,2024-01-19,call,2.50,2.55,2.525,2.52,150,1200,0.25,0.65,0.02,-0.08,0.30,0.05,5.0,0.525,1.034,30,true
```

#### 3.2 期权分类算法
**价值性分类**:
```python
def classify_option_moneyness(
    strike: float,
    underlying_price: float,
    option_type: str
) -> str:
    """
    Call Options:
    - ITM: strike < underlying_price
    - ATM: strike ≈ underlying_price (±1%)
    - OTM: strike > underlying_price

    Put Options:
    - ITM: strike > underlying_price
    - ATM: strike ≈ underlying_price (±1%)
    - OTM: strike < underlying_price
    """
```

**筛选逻辑**:
- **ITM 期权**: 返回按价值排序的前 20 个
- **ATM 期权**: 返回所有 ATM 期权 (通常 1-3 个)
- **OTM 期权**: 返回按流动性排序的前 20 个

### 阶段四：测试与验证

#### 4.1 单元测试
**文件**: `tests/option/test_options_chain.py`

```python
class TestOptionsChain:
    def test_get_options_chain_data(self):
        """测试期权链数据获取"""

    def test_classify_options_by_moneyness(self):
        """测试期权价值性分类"""

    def test_export_options_to_csv(self):
        """测试 CSV 导出功能"""

    def test_csv_file_naming_convention(self):
        """测试 CSV 文件命名规范"""
```

**文件**: `tests/option/test_option_expiration_dates.py`
**文件**: `tests/option/test_option_strikes.py`
**文件**: `tests/tools/test_get_options_chain_tool.py`

#### 4.2 集成测试
```python
class TestOptionsChainIntegration:
    def test_full_workflow_with_tradier_api(self):
        """测试完整工作流程"""

    def test_mcp_tool_response_format(self):
        """测试 MCP 工具响应格式"""

    def test_csv_export_integration(self):
        """测试 CSV 导出集成"""
```

#### 4.3 性能测试
- **API 响应时间**: < 3 秒
- **数据处理时间**: < 1 秒
- **CSV 导出时间**: < 0.5 秒
- **内存使用**: < 100MB

### 阶段五：文档与部署

#### 5.1 API 文档更新
**更新文件**: `README.md`

```markdown
## 📊 期权分析工具 🆕

- **options_chain_tool**: 获取期权链数据和分析
  - 输入: `symbol` (股票代码), `expiration` (到期日), `option_type` (期权类型), `include_greeks` (包含希腊字母)
  - 返回: 期权链数据、ITM/ATM/OTM 分类、CSV 文件路径、统计摘要
  - 特色:
    - 自动 CSV 导出到 `./data` 目录
    - 智能筛选：20个 ITM + ATM + 20个 OTM 期权
    - 完整希腊字母数据集成
    - 期权价值性自动分类

### 示例用法
```
# 获取 AAPL 2024-01-19 到期的期权链
使用 options_chain_tool 获取 AAPL 在 2024-01-19 到期的所有期权数据

# 获取仅看涨期权数据
使用 options_chain_tool 获取 TSLA 在 2024-02-16 到期的看涨期权 (option_type="call")

# 分析期权希腊字母
使用 options_chain_tool 获取 NVDA 期权数据并分析 Delta、Gamma、Theta、Vega
```
```

#### 5.2 配置更新
**环境变量扩展**:
```env
# 期权数据配置
OPTIONS_DEFAULT_RANGE_PCT=0.15     # 默认执行价格范围 ±15%
OPTIONS_MAX_RESULTS_PER_TYPE=50    # 每种类型最大返回数量
OPTIONS_CSV_EXPORT_ENABLED=true    # 启用 CSV 导出
```

## 实施时间线

| 阶段 | 任务 | 预计时间 | 依赖关系 |
|------|------|----------|----------|
| 1.1 | 扩展 Tradier API 客户端 | 2 天 | - |
| 1.2 | 期权链核心处理模块 | 3 天 | 1.1 |
| 1.3 | 到期日管理模块 | 1 天 | 1.1 |
| 1.4 | 执行价格查询模块 | 1 天 | 1.1 |
| 2.1 | MCP 工具实现 | 2 天 | 1.2-1.4 |
| 2.2 | MCP 服务器注册 | 0.5 天 | 2.1 |
| 3.1-3.2 | 数据处理与导出 | 2 天 | 2.1 |
| 4.1-4.3 | 测试与验证 | 3 天 | 3.2 |
| 5.1-5.2 | 文档与部署 | 1 天 | 4.3 |

**总计**: 约 15.5 天

## 潜在挑战与解决方案

### 技术挑战

#### 1. Tradier API 限制
**挑战**: API 调用频率限制和数据量限制
**解决方案**:
- 实施请求缓存机制
- 批量处理多个到期日
- 错误重试和指数退避策略

#### 2. 期权数据复杂性
**挑战**: 期权数据结构复杂，希腊字母计算准确性
**解决方案**:
- 使用 Tradier API 提供的预计算希腊字母
- 实施数据验证和清洗流程
- 提供降级方案处理缺失数据

#### 3. 大数据量处理
**挑战**: 期权链数据量可能很大，影响性能
**解决方案**:
- 实施分页和流式处理
- 智能筛选减少数据传输量
- 异步处理和并发优化

### 业务挑战

#### 1. 用户体验优化
**挑战**: 期权数据复杂，用户需要易于理解的格式
**解决方案**:
- 提供清晰的数据分类 (ITM/ATM/OTM)
- 智能默认设置
- 丰富的统计摘要和可视化建议

#### 2. 数据准确性保证
**挑战**: 期权数据实时性和准确性要求高
**解决方案**:
- 数据时间戳和新鲜度检查
- 多重验证和异常检测
- 清晰的数据来源标注

## 成功标准

### 功能验收标准
- ✅ 成功获取任意股票的期权链数据
- ✅ 准确分类 ITM/ATM/OTM 期权
- ✅ 正确导出 CSV 文件到指定目录
- ✅ MCP 工具返回格式符合规范
- ✅ 支持看涨、看跌和混合期权查询

### 性能验收标准
- ✅ API 响应时间 < 3 秒
- ✅ 处理 100+ 期权合约 < 2 秒
- ✅ CSV 导出 < 0.5 秒
- ✅ 内存使用 < 100MB

### 质量验收标准
- ✅ 单元测试覆盖率 > 90%
- ✅ 集成测试全部通过
- ✅ 无严重或高优先级缺陷
- ✅ 代码审查通过

### 用户体验标准
- ✅ 中文显示和错误消息
- ✅ 清晰的工具参数说明
- ✅ 有用的数据摘要和统计
- ✅ 直观的期权分类展示

## 未来扩展规划

### v5.1 增强功能
- 期权策略分析工具 (Straddle, Strangle 等)
- 期权链历史数据对比
- 隐含波动率微笑分析

### v5.2 高级功能
- 实时期权价格流推送
- 期权组合风险分析
- 自定义期权筛选条件

### v5.3 集成功能
- 与股票历史数据工具集成
- 期权与股票关联分析
- 投资组合期权敞口分析

---

## 附录

### A. Tradier API 端点参考

```python
# 期权链
GET /v1/markets/options/chains
params: symbol, expiration, greeks=true

# 到期日
GET /v1/markets/options/expirations
params: symbol, includeAllRoots=true, strikes=true, contractSize=true, expirationType=true

# 执行价格
GET /v1/markets/options/strikes
params: symbol, expiration, includeAllRoots=true
```

### B. CSV 数据格式规范

```csv
# 必需字段
symbol,strike_price,expiration_date,option_type,bid,ask,last,volume,open_interest

# 希腊字母字段 (当 include_greeks=true)
delta,gamma,theta,vega,rho,implied_volatility

# 计算字段
mid_price,intrinsic_value,time_value,moneyness,days_to_expiration,in_the_money
```

### C. 错误代码定义

```python
class OptionsChainError:
    INVALID_SYMBOL = "OC001"           # 无效股票代码
    INVALID_EXPIRATION = "OC002"       # 无效到期日
    NO_OPTIONS_FOUND = "OC003"         # 未找到期权数据
    API_RATE_LIMIT = "OC004"           # API 调用限制
    CSV_EXPORT_FAILED = "OC005"        # CSV 导出失败
```

---

*此文档作为 TradingAgent MCP v5 期权链功能的完整技术规格，为开发团队提供详细的实施指导。*
