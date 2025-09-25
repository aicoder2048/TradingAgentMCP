async def call_hello_multiple(name: str, times: int = 3) -> str:
    """
    Generate a prompt to call hello tool multiple times.
    
    Args:
        name: The name to use in the hello calls
        times: Number of times to call hello (default: 3)
        
    Returns:
        str: A formatted prompt string
    """
    if not name or not name.strip():
        name = "Guest"
    else:
        name = name.strip()
    
    times = max(1, min(times, 10))
    
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