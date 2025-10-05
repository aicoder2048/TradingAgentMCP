# Bug: optimal_expiration_selector_tool Missing TradierClient Initialization

## Bug Description
When calling `optimal_expiration_selector_tool_mcp` without providing `available_expirations` parameter (i.e., `available_expirations=None`), the tool fails with an error message "无法获取GOOG的可用到期日" (Unable to get available expirations for GOOG).

**Expected Behavior**: The tool should automatically fetch available expirations from the Tradier API when `available_expirations` is not provided.

**Actual Behavior**: The tool returns an error because it tries to fetch data from Tradier but the `tradier_client` attribute is `None`.

## Problem Statement
The `OptimalExpirationSelectorTool` class is initialized in `server.py:441` without passing a `tradier_client` instance. When `available_expirations=None`, the tool's `_fetch_available_expirations()` method attempts to use `self.tradier_client` to fetch data from Tradier API, but since it's `None`, the method returns `None`, causing the `execute()` method to return an error response.

## Solution Statement
Initialize a `TradierClient()` instance in the `optimal_expiration_selector_tool_mcp` function in `server.py` and pass it to the `OptimalExpirationSelectorTool` constructor. This follows the same pattern used by other tools in the codebase (e.g., `get_options_chain_tool`, `get_stock_history_tool`).

## Steps to Reproduce
1. Call `optimal_expiration_selector_tool_mcp` with only the `symbol` parameter:
   ```python
   result = await optimal_expiration_selector_tool_mcp(symbol="GOOG")
   ```
2. Observe that the function returns:
   ```json
   {
     "success": false,
     "error": "无法获取GOOG的可用到期日",
     "timestamp": "..."
   }
   ```

## Root Cause Analysis
1. **Location**: `src/mcp_server/server.py:441`
2. **Code**:
   ```python
   tool = OptimalExpirationSelectorTool()
   ```
3. **Issue**: No `tradier_client` is passed to the constructor
4. **Impact**: When `available_expirations=None`, the tool cannot fetch data from Tradier API

**Comparison with working tools**:
- `get_options_chain_tool` (line 67): `tradier_client = TradierClient()`
- `get_stock_history_tool` (line 122): `tradier_client = TradierClient()`
- `get_earnings_calendar_tool` (line 54): `tradier_client = TradierClient()`

All these tools create a `TradierClient` instance before using it.

## Relevant Files
Use these files to fix the bug:

- **`src/mcp_server/server.py`** (lines 414-448)
  - Contains the `optimal_expiration_selector_tool_mcp` function that needs to be fixed
  - Currently creates `OptimalExpirationSelectorTool()` without passing `tradier_client`
  - Need to add `TradierClient()` initialization before creating the tool instance

- **`src/mcp_server/tools/optimal_expiration_selector_tool.py`** (lines 48-51, 229-248)
  - Contains the `OptimalExpirationSelectorTool.__init__()` method that accepts `tradier_client` parameter
  - Contains the `_fetch_available_expirations()` method that uses `self.tradier_client`
  - No changes needed here - the class is correctly designed to accept and use `tradier_client`

- **`src/provider/tradier/client.py`**
  - Contains the `TradierClient` class that needs to be imported
  - Reference for understanding the client interface

### Reference Files (for pattern matching)
- **`src/mcp_server/tools/get_options_chain_tool.py`** (line 67)
  - Example of correct `TradierClient()` initialization pattern
- **`src/mcp_server/tools/get_stock_history_tool.py`** (line 122)
  - Example of correct `TradierClient()` initialization pattern

## Step by Step Tasks

### Task 1: Add TradierClient import to server.py
- Open `src/mcp_server/server.py`
- Add import statement for `TradierClient` at the top of the file where other imports are located
- Follow the existing import pattern in the file

### Task 2: Initialize TradierClient in optimal_expiration_selector_tool_mcp
- Locate the `optimal_expiration_selector_tool_mcp` function (around line 414-448)
- Before line 441 where `tool = OptimalExpirationSelectorTool()` is called, add:
  ```python
  # Initialize Tradier client for fetching expiration data
  tradier_client = TradierClient()
  ```
- Update line 441 to pass the client:
  ```python
  tool = OptimalExpirationSelectorTool(tradier_client=tradier_client)
  ```

### Task 3: Create test to validate the fix
- Create a new test file `tests/tools/test_optimal_expiration_selector_tool.py`
- Write test cases:
  - Test with `available_expirations=None` (should auto-fetch from Tradier)
  - Test with provided `available_expirations` (should use provided data)
  - Test error handling when Tradier API fails
- Use pytest async fixtures and mocking for Tradier API calls

### Task 4: Run validation commands
- Execute all validation commands listed below to ensure:
  - The bug is fixed
  - No regressions are introduced
  - All existing tests still pass

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run python -c "import asyncio; from src.mcp_server.tools.optimal_expiration_selector_tool import OptimalExpirationSelectorTool; from src.provider.tradier.client import TradierClient; asyncio.run(OptimalExpirationSelectorTool(tradier_client=TradierClient()).execute(symbol='GOOG'))"` - Test that the tool works with TradierClient
- `cd tests && uv run pytest tests/tools/test_optimal_expiration_selector_tool.py -v` - Run new tests for the optimal expiration selector tool
- `cd tests && uv run pytest` - Run all server tests to validate zero regressions
- `uv run python -c "from src.mcp_server.server import create_server; print('Server created successfully')"` - Verify server can be created without errors

## Notes
- **Pattern Consistency**: This fix makes `optimal_expiration_selector_tool_mcp` consistent with other tools that need Tradier API access
- **Minimal Change**: Only 2 lines need to be added to `server.py` - one import and one client initialization
- **No Breaking Changes**: The fix is backward compatible since `available_expirations` can still be provided explicitly
- **Import Location**: Add the import near other tool-related imports in `server.py`, likely after line 22 where `OptimalExpirationSelectorTool` is imported
- **Testing Strategy**: Mock the Tradier API in tests to avoid dependency on live API during test runs
