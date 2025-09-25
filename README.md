# MCP Server Template

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.0+-green.svg)](https://github.com/fastmcp/fastmcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready Model Context Protocol (MCP) server template built with FastMCP framework. This template provides a solid foundation for building MCP servers that integrate seamlessly with Claude Code and other MCP clients.

## 🌟 Features

- **🚀 Quick Start**: Ready-to-use MCP server structure with minimal setup
- **🔧 Configurable**: Environment-based configuration for easy customization
- **🧩 Modular Architecture**: Clean separation of tools, prompts, and configurations
- **🧪 Test Ready**: Built-in testing framework with pytest
- **📝 Type Safe**: Full type hints and Pydantic models support
- **🔌 Claude Code Optimized**: Pre-configured for Claude Code integration
- **📦 UV Package Manager**: Modern Python package management with UV

## 📋 Prerequisites

- Python 3.13 or higher
- [UV package manager](https://github.com/astral-sh/uv)
- Claude Code (for MCP client integration)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <project-directory>
```

### 2. Setup Environment

```bash
# Copy environment configuration
cp .env.sample .env

# Edit .env file with your settings
# Customize MCP_SERVER_NAME and other variables
```

### 3. Install Dependencies

```bash
# Create virtual environment and install dependencies
uv sync --python 3.13
```

### 4. Configure Claude Code Integration

```bash
# Copy MCP configuration
cp .mcp.json.sample .mcp.json

# Edit .mcp.json with your paths
# Update server name and project path
```

### 5. Run the Server

```bash
# Run directly with UV
uv run python main.py

# Or activate environment first
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
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
│   └── mcp_server/
│       ├── __init__.py
│       ├── server.py         # Main server implementation
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py   # Configuration management
│       ├── models/
│       │   ├── __init__.py
│       │   └── schemas.py    # Pydantic data models
│       ├── tools/
│       │   ├── __init__.py
│       │   └── hello_tool.py # Example tool implementation
│       └── prompts/
│           ├── __init__.py
│           └── hello_prompt.py # Example prompt implementation
├── tests/
│   ├── __init__.py
│   ├── tools/
│   │   └── test_hello_tool.py
│   └── prompts/
│       └── test_hello_prompt.py
├── specs/
│   └── prd_v0_ai_enhanced.md  # Product requirements document
└── ai_docs/                    # Reference documentation
```

## ⚙️ Configuration

### Environment Variables

Configure your server by setting environment variables in `.env`:

```env
# Server Configuration
MCP_SERVER_NAME=YourServerName   # Your MCP server name
MCP_VERSION=1.0.0                # Server version

# Logging
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR, CRITICAL
DEBUG=false                      # Enable debug mode

# Features
MAX_PROMPT_CALLS=10             # Maximum prompt iterations
ENABLE_METRICS=false            # Enable metrics collection
```

### Claude Code Integration

Configure Claude Code to connect to your server in `.mcp.json`:

```json
{
  "mcpServers": {
    "YourServerName": {
      "command": "uv",
      "args": ["run", "python", "/path/to/project/main.py"],
      "env": {
        "LOG_LEVEL": "DEBUG",
        "PYTHONPATH": "/path/to/project"
      }
    }
  }
}
```

## 🛠️ Development

### Adding New Tools

1. Create a new file in `src/mcp_server/tools/`
2. Implement your async tool function
3. Export it in `tools/__init__.py`
4. Register in `server.py` with `@mcp.tool()` decorator

Example:
```python
# src/mcp_server/tools/my_tool.py
async def my_tool(param: str) -> dict:
    """Your tool description."""
    return {"result": f"Processed: {param}"}
```

### Adding New Prompts

1. Create a new file in `src/mcp_server/prompts/`
2. Implement your async prompt function
3. Export it in `prompts/__init__.py`
4. Register in `server.py` with `@mcp.prompt()` decorator

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/mcp_server

# Run specific test file
uv run pytest tests/tools/test_hello_tool.py
```

## 🔍 Available Tools and Prompts

### Tools

- **hello**: A simple greeting tool that demonstrates basic tool structure
  - Input: `name` (string)
  - Output: Structured response with greeting message

### Prompts

- **call_hello_multiple**: Demonstrates prompt functionality
  - Generates instructions to call the hello tool multiple times
  - Parameters: `name` (string), `times` (integer)

## 🎯 Usage with Claude Code

1. **Start the server**: The server will run as configured in `.mcp.json`
2. **Check connection**: Use `/mcp` command in Claude Code to verify
3. **Use tools**: Call tools directly through Claude Code
4. **Use prompts**: Access prompts for guided interactions

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

## 📈 Template Extension Guide

This template currently includes only a basic "hello" tool and prompt as examples, designed to be extended for any domain-specific MCP server project.

### Product Requirements Documents (PRDs)

The `specs/` directory contains project PRDs for iterative development:

- **Human Version**: `prd_v0.md` - Initial human-written requirements
- **AI-Enhanced Version**: `prd_v0_ai_enhanced.md` - AI-enhanced requirements with detailed specifications

#### Version Management
- Progress through versions: v1, v2, v3, etc.
- Each version represents:
  - New feature additions
  - Major architectural changes
  - Critical bug fixes
- Maintain both human (`prd_vX.md`) and AI-enhanced (`prd_vX_ai_enhanced.md`) versions

#### AI Enhancement Process
- Use Claude Code slash command `/quick-plan` to generate AI-enhanced PRDs
- This command is defined in `.claude/commands/quick-plan.md`
- Automatically creates comprehensive technical specifications from human requirements

### Claude Code Commands

Located in `.claude/commands/`:

#### Context Priming Commands
- **`prime.md`**: General context priming for Claude
- **`prime_cc.md`**: Claude Code-specific context priming
- Use these at the beginning of sessions to establish project context

#### Planning Command
- **`quick-plan.md`**: Converts human PRDs into detailed technical specifications
- Automatically generates implementation plans with code examples

### Output Styles

Located in `.claude/output-styles/`:

- **`genui.md`**: General-purpose HTML output style
  - Generates complete, self-contained HTML documents
  - Includes modern embedded CSS styling
  - Automatically opens in browser
  - Useful for creating reports, documentation, or visual outputs

### Extending the Template

1. **Start with PRD**: Write your requirements in `specs/prd_v1.md`
2. **Generate AI-Enhanced Version**: Use `/quick-plan` to create detailed specifications
3. **Implement Features**: Add tools and prompts following the established patterns
4. **Document Progress**: Update PRDs for each major version
5. **Utilize Claude Commands**: Use context priming and planning commands for efficiency

## 📚 Documentation

- [FastMCP Documentation](https://github.com/fastmcp/fastmcp)
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [Claude Code MCP Guide](https://docs.anthropic.com/claude/docs/mcp)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [FastMCP](https://github.com/fastmcp/fastmcp) framework
- Designed for [Claude Code](https://claude.ai) integration
- Package management by [UV](https://github.com/astral-sh/uv)

## 📮 Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

*This is a template project. Customize it for your specific MCP server needs.*