import pytest
from mcp_server.prompts.hello_prompt import call_hello_multiple

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
    result = await call_hello_multiple("User", 15)
    
    assert "10" in result
    assert result.count('hello("User")') == 10