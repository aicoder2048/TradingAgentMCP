import pytest
from mcp_server.tools.hello_tool import hello
from mcp_server.config.settings import settings

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
    assert f"Welcome to {settings.server_name}" in result["message"]

@pytest.mark.asyncio
async def test_hello_whitespace_name():
    """Test hello with whitespace-only name."""
    result = await hello("   ")

    assert result["status"] == "success"
    assert result["name"] == "Guest"
