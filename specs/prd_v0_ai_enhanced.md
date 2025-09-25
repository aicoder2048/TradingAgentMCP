# <TEMPLATE_PROJECT> 产品需求文档 v1.0

## 1. 项目概述

### 1.1 项目名称
<TEMPLATE_PROJECT> - MCP Server 项目模板

### 1.2 项目定位
一个基于 MCP (Model Context Protocol) 的服务器项目模板框架。本框架提供了构建 MCP 服务器所需的基础架构和标准化组件，开发者可以基于此模板快速创建自己的 MCP 服务器项目。采用模块化设计，初期实现基础的 MCP 服务器框架和示例工具，后续可逐步添加特定领域的功能。

### 1.3 核心价值
- **快速启动**：提供即用的 MCP Server 项目结构，减少重复搭建工作
- **Claude Code 优化**：专门为 Claude Code 作为 MCP 客户端优化集成体验
- **模块化架构**：参考 quick-data-mcp 的清晰架构，便于功能扩展和维护
- **生产就绪**：使用 FastMCP 框架，具备生产级别的错误处理和日志功能
- **最佳实践**：遵循 MCP 协议标准和 Python 开发最佳实践

### 1.4 模板特性
本 MCP Server 模板提供了以下核心能力：

#### 标准化项目结构
- 清晰的目录组织（工具、提示、配置、模型）
- 模块化的代码架构
- 完整的测试框架
- 文档和规格说明

#### 示例实现
- **Hello 工具**：演示基础工具的实现方式
- **多次调用提示**：展示提示功能的使用
- **配置管理**：提供灵活的配置系统
- **错误处理**：标准化的异常处理模式

#### 开发工具链
- UV 包管理器集成
- pytest 测试框架
- Claude Code 配置文件
- 开发和生产环境配置

#### 应用场景（示例）
作为模板，本框架可以用于创建各种类型的 MCP 服务器，例如：
- 数据分析工具服务器
- API 集成服务器
- 业务流程自动化服务器
- AI 辅助工具服务器
- 领域特定的专业服务器（如本模板原型：小六壬占卜服务器）

## 2. 技术架构

### 2.1 技术栈
- **框架**: FastMCP (最新版本 2.0+)
- **语言**: Python 3.10+
- **包管理**: UV
- **运行方式**: `uv run python`
- **客户端**: Claude Code

### 2.2 项目结构
```
/Users/szou/Python/Playground/<TEMPLATE_PROJECT>/
├── pyproject.toml           # 项目配置和依赖
├── uv.lock                  # 依赖锁文件
├── README.md               # 项目说明
├── main.py                 # 服务器入口点
├── .mcp.json              # Claude Code MCP 配置
├── src/
│   └── mcp_server/        # 核心服务器代码（参考 quick-data-mcp）
│       ├── __init__.py
│       ├── server.py       # 主服务器逻辑和 MCP 装饰器
│       ├── config/         # 配置管理
│       │   ├── __init__.py
│       │   └── settings.py
│       ├── models/         # 数据模型
│       │   ├── __init__.py
│       │   └── schemas.py  # Pydantic 模型定义
│       ├── tools/          # MCP 工具实现
│       │   ├── __init__.py
│       │   └── hello_tool.py
│       └── prompts/        # MCP 提示实现
│           ├── __init__.py
│           └── hello_prompt.py
├── tests/                  # 测试代码
│   ├── __init__.py
│   ├── tools/
│   │   └── test_hello_tool.py
│   └── prompts/
│       └── test_hello_prompt.py
├── specs/                  # 规格文档
│   └── prd_v1.md          # 本文档
└── ai_docs/               # AI 参考文档
    └── ...                # 技术参考文档
```

### 2.3 核心组件

#### 2.3.1 MCP Server Tool: `hello`
- **功能**: 接收一个名字参数，返回问候语
- **签名**: `hello(name: str) -> dict`
- **返回**: 标准化的响应字典
- **示例**:
  ```python
  # 输入
  hello("Claude")
  # 输出
  {
      "status": "success",
      "message": "Hello, Claude! Welcome to <TEMPLATE_PROJECT>.",
      "timestamp": "2024-01-20T10:30:00Z"
  }
  ```

#### 2.3.2 MCP Server Prompt: `call_hello_multiple`
- **功能**: 生成一个提示，引导 Claude Code 多次调用 hello 工具
- **签名**: `call_hello_multiple(name: str, times: int) -> str`
- **返回**: 格式化的提示字符串
- **示例输出**:
  ```
  请使用 hello 工具打招呼 3 次。
  
  调用参数：
  - name: "Claude"
  
  期望的调用序列：
  1. hello("Claude")
  2. hello("Claude")
  3. hello("Claude")
  
  完成所有调用后，请总结所有的响应结果。
  ```

## 3. 实现细节

### 3.1 主服务器实现 (`main.py`)
```python
#!/usr/bin/env python3
"""<TEMPLATE_PROJECT> - Minimal MCP Server."""

import asyncio
from src.mcp_server.server import create_server

def main():
    """Main entry point."""
    server = create_server()
    asyncio.run(server.run())

if __name__ == "__main__":
    main()
```

### 3.2 服务器核心 (`src/mcp_server/server.py`)
```python
"""Main server implementation with MCP decorators."""

from fastmcp import FastMCP
from contextlib import asynccontextmanager
from typing import Dict, Any
from .tools.hello_tool import hello
from .prompts.hello_prompt import call_hello_multiple

@asynccontextmanager
async def lifespan(server: FastMCP):
    """Server lifecycle management."""
    print("🚀 Starting <TEMPLATE_PROJECT> server...")
    yield
    print("👋 Shutting down <TEMPLATE_PROJECT> server...")

def create_server() -> FastMCP:
    """Create and configure the MCP server."""
    mcp = FastMCP(
        name="<TEMPLATE_PROJECT>",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # ============================================================================
    # TOOLS - Functions that can be called by LLMs
    # ============================================================================
    
    @mcp.tool()
    async def hello_tool(name: str) -> Dict[str, Any]:
        """
        Say hello to someone.
        
        Args:
            name: The name of the person to greet
            
        Returns:
            A greeting response with status and message
        """
        return await hello(name)
    
    # ============================================================================
    # PROMPTS - Reusable conversation templates
    # ============================================================================
    
    @mcp.prompt()
    async def call_hello_multiple_prompt(name: str, times: int = 3) -> str:
        """
        Generate a prompt to call hello multiple times.
        
        Args:
            name: The name to use in the hello calls
            times: Number of times to call hello (default: 3)
            
        Returns:
            A formatted prompt string
        """
        return await call_hello_multiple(name, times)
    
    return mcp
```

### 3.3 工具实现 (`src/mcp_server/tools/hello_tool.py`)
```python
"""Hello tool implementation."""

from datetime import datetime
from typing import Dict, Any

async def hello(name: str) -> Dict[str, Any]:
    """
    Say hello to someone with a structured response.
    
    Args:
        name: The name of the person to greet
        
    Returns:
        dict: Structured response with status, message, and metadata
    """
    try:
        # 验证输入
        if not name or not name.strip():
            message = "Hello! Welcome to <TEMPLATE_PROJECT>."
            name = "Guest"
        else:
            name = name.strip()
            message = f"Hello, {name}! Welcome to <TEMPLATE_PROJECT>."
        
        return {
            "status": "success",
            "message": message,
            "name": name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": {
                "server": "<TEMPLATE_PROJECT>",
                "tool": "hello",
                "version": "1.0.0"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to process greeting: {str(e)}",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
```

### 3.4 工具包导出 (`src/mcp_server/tools/__init__.py`)
```python
"""Tools module exports."""

from .hello_tool import hello

__all__ = ["hello"]
```

### 3.5 提示实现 (`src/mcp_server/prompts/hello_prompt.py`)
```python
"""Hello prompt implementation."""

async def call_hello_multiple(name: str, times: int = 3) -> str:
    """
    Generate a prompt to call hello tool multiple times.
    
    Args:
        name: The name to use in the hello calls
        times: Number of times to call hello (default: 3)
        
    Returns:
        str: A formatted prompt string
    """
    # 参数验证
    if not name or not name.strip():
        name = "Guest"
    else:
        name = name.strip()
    
    # 限制次数范围
    times = max(1, min(times, 10))  # 1-10 次
    
    prompt = f"""🎯 **Hello 工具测试任务**

您需要使用 `hello` 工具打招呼 **{times}** 次。

## 📝 任务参数
- **name**: "{name}"
- **调用次数**: {times}

## 🔄 期望的调用序列
"""
    
    for i in range(1, times + 1):
        prompt += f"\n{i}. `hello(\"{name}\")`"
    
    prompt += f"""

## ✅ 完成标准
1. 成功调用 hello 工具 {times} 次
2. 每次调用都使用名字 "{name}"
3. 收集所有响应结果
4. 总结调用结果，包括：
   - 成功调用的次数
   - 每次调用的响应状态
   - 任何错误或异常情况

## 💡 提示
这个任务用于测试 MCP 工具的多次调用功能，确保客户端能够正确处理重复的工具调用。"""
    
    return prompt
```

### 3.6 提示包导出 (`src/mcp_server/prompts/__init__.py`)
```python
"""Prompts module exports."""

from .hello_prompt import call_hello_multiple

__all__ = ["call_hello_multiple"]
```

### 3.7 配置管理 (`src/mcp_server/config/settings.py`)
```python
"""Configuration settings."""

import os
from typing import Optional

class Settings:
    """Application settings."""
    
    def __init__(self):
        self.server_name = "<TEMPLATE_PROJECT>"
        self.version = "1.0.0"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.debug_mode = os.getenv("DEBUG", "false").lower() == "true"
        
        # 扩展配置（为未来功能预留）
        self.max_prompt_calls = int(os.getenv("MAX_PROMPT_CALLS", "10"))
        self.enable_metrics = os.getenv("ENABLE_METRICS", "false").lower() == "true"

settings = Settings()
```

## 4. Claude Code 集成

### 4.1 配置文件
创建项目级 Claude Code 配置 (`/Users/szou/Python/Playground/<TEMPLATE_PROJECT>/.mcp.json`):

```json
{
  "mcpServers": {
    "template": {
      "command": "uv",
      "args": ["run", "python", "/Users/szou/Python/Playground/<TEMPLATE_PROJECT>/main.py"],
      "env": {
        "LOG_LEVEL": "DEBUG",
        "PYTHONPATH": "/Users/szou/Python/Playground/<TEMPLATE_PROJECT>"
      }
    }
  }
}
```

### 4.2 验证命令
```bash
# 在 Claude Code 中检查服务器状态
/mcp

# 应该看到:
# template: Connected ✓

# 测试工具调用
# 使用 Claude Code 调用: hello("测试用户")
```

## 5. 开发计划

### 5.1 第一阶段：基础实现（当前）
- [ ] 项目初始化（`uv init`）
- [ ] 创建目录结构
- [ ] 实现 hello 工具
- [ ] 实现 call_hello_multiple 提示
- [ ] 配置 Claude Code 集成
- [ ] 基础测试

### 5.2 第二阶段：领域特定功能
- [ ] 实现核心业务工具
- [ ] 实现智能提示和模板
- [ ] 完善错误处理和日志记录
- [ ] 扩展单元测试覆盖

### 5.3 第三阶段：生产优化
- [ ] 添加中间件支持
- [ ] 实现速率限制
- [ ] 性能监控和指标
- [ ] Docker 容器化部署

## 6. 测试策略

### 6.1 单元测试示例 (`tests/tools/test_hello_tool.py`)
```python
"""Test hello tool."""

import pytest
from src.mcp_server.tools.hello_tool import hello

@pytest.mark.asyncio
async def test_hello_with_name():
    """Test hello with a valid name."""
    result = await hello("Claude")
    
    assert result["status"] == "success"
    assert "Claude" in result["message"]
    assert result["name"] == "Claude"
    assert "timestamp" in result

@pytest.mark.asyncio
async def test_hello_empty_name():
    """Test hello with empty name."""
    result = await hello("")
    
    assert result["status"] == "success"
    assert result["name"] == "Guest"
    assert "Welcome to <TEMPLATE_PROJECT>" in result["message"]

@pytest.mark.asyncio
async def test_hello_whitespace_name():
    """Test hello with whitespace-only name."""
    result = await hello("   ")
    
    assert result["status"] == "success"
    assert result["name"] == "Guest"
```

### 6.2 提示测试 (`tests/prompts/test_hello_prompt.py`)
```python
"""Test hello prompt."""

import pytest
from src.mcp_server.prompts.hello_prompt import call_hello_multiple

@pytest.mark.asyncio
async def test_call_hello_multiple_default():
    """Test prompt with default parameters."""
    result = await call_hello_multiple("Test", 3)
    
    assert "Test" in result
    assert "3" in result
    assert 'hello("Test")' in result

@pytest.mark.asyncio
async def test_call_hello_multiple_max_times():
    """Test prompt with maximum times."""
    result = await call_hello_multiple("User", 15)  # Should cap at 10
    
    assert "10" in result  # Capped at 10
    assert result.count('hello("User")') == 10
```

## 7. 依赖管理

### 7.1 pyproject.toml
```toml
[project]
name = "template-mcp"
version = "1.0.0"
description = "Minimal MCP Server for Claude Code"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "fastmcp>=2.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
asyncio_mode = "auto"
```

## 8. 运行和部署

### 8.1 开发环境设置
```bash
# 进入项目目录
cd /Users/szou/Python/Playground/<TEMPLATE_PROJECT>

# 初始化项目
uv init

# 添加依赖
uv add fastmcp pydantic
uv add --dev pytest pytest-asyncio pytest-cov

# 运行服务器
uv run python main.py

# 运行测试
uv run pytest tests/ -v

# 运行测试并生成覆盖率报告
uv run pytest tests/ --cov=src/mcp_server --cov-report=html
```

### 8.2 Claude Code 集成测试
1. 确保 `.mcp.json` 配置正确
2. 重启 Claude Code 或重新加载配置
3. 使用 `/mcp` 命令验证连接
4. 测试工具调用和提示功能

## 9. 扩展指南

### 9.1 添加新工具的标准流程
1. 在 `src/mcp_server/tools/` 创建新文件（如 `calculator_tool.py`）
2. 实现异步函数，返回标准化的字典响应
3. 在 `tools/__init__.py` 中导出函数
4. 在 `server.py` 中使用 `@mcp.tool()` 注册
5. 在 `tests/tools/` 添加对应测试文件
6. 运行测试确保功能正常

### 9.2 添加新提示的标准流程
1. 在 `src/mcp_server/prompts/` 创建新文件
2. 实现异步函数，返回格式化的提示字符串
3. 在 `prompts/__init__.py` 中导出函数
4. 在 `server.py` 中使用 `@mcp.prompt()` 注册
5. 添加相应测试

## 10. 成功标准

### 10.1 基础功能验证
- ✅ MCP 服务器能够使用 `uv run python main.py` 启动
- ✅ Claude Code 能够通过 `.mcp.json` 配置连接
- ✅ hello 工具可以被调用并返回结构化响应
- ✅ call_hello_multiple 提示能够生成有效指令
- ✅ 所有单元测试通过

### 10.2 代码质量标准
- ✅ 遵循 quick-data-mcp 的模块化设计模式
- ✅ 使用标准化的响应格式
- ✅ 完整的错误处理
- ✅ 清晰的代码注释和文档

## 11. 注意事项

### 11.1 与 quick-data-mcp 的差异
- **简化版本**：只实现核心的工具和提示功能
- **暂不实现**：Resources（资源）功能暂不实现
- **聚焦基础**：专注于建立可工作的最小框架

### 11.2 开发建议
- 严格遵循目录结构，便于后续扩展
- 保持代码简洁，避免过度设计
- 优先确保 Claude Code 集成工作正常
- 逐步迭代，每次添加少量功能

## 12. 总结

<TEMPLATE_PROJECT> 是一个 MCP Server 项目模板框架，为开发者提供了构建 MCP 服务器所需的基础架构。项目参考 quick-data-mcp 的架构设计，通过 FastMCP 框架和模块化设计，提供了清晰的扩展路径。

本模板采用分阶段开发方法：
- **第一阶段**：建立基础 MCP 服务器框架，验证技术可行性
- **第二阶段**：根据具体需求实现领域特定功能
- **第三阶段**：生产优化和部署

项目专门为 Claude Code 作为 MCP 客户端进行优化，确保开发者能够快速搭建并运行自己的 MCP 服务器，为 AI 助手提供专业的工具和能力扩展。