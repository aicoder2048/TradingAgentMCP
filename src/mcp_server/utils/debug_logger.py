"""
调试日志工具模块
用于追踪MCP参数传递和解析过程
"""

import logging
import json
from typing import Any
import traceback
from datetime import datetime

# 配置日志格式
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mcp_debug.log', mode='a', encoding='utf-8')
    ]
)

logger = logging.getLogger('MCP_DEBUG')
logger.setLevel(logging.DEBUG)


def debug_param(
    location: str,
    param_name: str,
    param_value: Any,
    additional_info: str = ""
) -> None:
    """
    记录参数调试信息
    
    Args:
        location: 代码位置（如 "server.py:income_generation_csp_engine_prompt"）
        param_name: 参数名称
        param_value: 参数值
        additional_info: 额外信息
    """
    debug_info = {
        "timestamp": datetime.now().isoformat(),
        "location": location,
        "param_name": param_name,
        "param_type": type(param_value).__name__,
        "param_value": _safe_repr(param_value),
        "additional_info": additional_info
    }
    
    logger.debug(f"🔍 PARAM_DEBUG: {json.dumps(debug_info, ensure_ascii=False, indent=2)}")
    
    # 额外的类型分析
    if isinstance(param_value, str):
        _analyze_string_param(location, param_name, param_value)
    elif isinstance(param_value, list):
        _analyze_list_param(location, param_name, param_value)


def debug_parse_step(
    function_name: str,
    step_name: str,
    input_value: Any,
    output_value: Any = None,
    success: bool = None,
    error: str = None
) -> None:
    """
    记录解析步骤调试信息
    
    Args:
        function_name: 函数名称
        step_name: 步骤名称
        input_value: 输入值
        output_value: 输出值
        success: 是否成功
        error: 错误信息
    """
    debug_info = {
        "timestamp": datetime.now().isoformat(),
        "function": function_name,
        "step": step_name,
        "input": _safe_repr(input_value),
        "input_type": type(input_value).__name__,
        "output": _safe_repr(output_value) if output_value is not None else None,
        "success": success,
        "error": error
    }
    
    status = "✅" if success else "❌" if success is False else "➡️"
    logger.debug(f"{status} PARSE_STEP: {json.dumps(debug_info, ensure_ascii=False, indent=2)}")


def debug_stack_trace(location: str, message: str = "Stack trace") -> None:
    """
    记录调用栈信息
    
    Args:
        location: 代码位置
        message: 调试信息
    """
    stack = traceback.format_stack()
    logger.debug(f"📚 STACK_TRACE at {location}: {message}")
    for frame in stack[-5:-1]:  # 显示最近的4层调用栈（排除当前函数）
        logger.debug(f"  {frame.strip()}")


def _safe_repr(value: Any) -> str:
    """
    安全地获取值的字符串表示
    
    Args:
        value: 任意值
        
    Returns:
        值的字符串表示
    """
    try:
        if isinstance(value, str):
            # 对于字符串，显示原始内容和repr
            if len(value) > 100:
                return f"{repr(value[:100])}... (length: {len(value)})"
            return repr(value)
        elif isinstance(value, (list, tuple)):
            if len(value) > 10:
                return f"{type(value).__name__}[{len(value)} items]: {repr(value[:3])}..."
            return repr(value)
        elif isinstance(value, dict):
            if len(value) > 10:
                keys = list(value.keys())[:3]
                return f"dict[{len(value)} keys]: {keys}..."
            return repr(value)
        else:
            return repr(value)
    except:
        return f"<{type(value).__name__} object>"


def _analyze_string_param(location: str, param_name: str, value: str) -> None:
    """
    详细分析字符串参数
    """
    analysis = {
        "location": location,
        "param_name": param_name,
        "length": len(value),
        "starts_with_bracket": value.strip().startswith('[') if value else False,
        "ends_with_bracket": value.strip().endswith(']') if value else False,
        "contains_comma": ',' in value,
        "contains_space": ' ' in value,
        "contains_quotes": '"' in value or "'" in value,
        "first_10_chars": repr(value[:10]) if len(value) > 0 else "",
        "last_10_chars": repr(value[-10:]) if len(value) > 0 else "",
    }
    
    # 尝试不同的解析方法
    parse_attempts = {}
    
    # JSON解析
    try:
        import json
        json_result = json.loads(value)
        parse_attempts["json"] = {"success": True, "result_type": type(json_result).__name__}
    except Exception as e:
        parse_attempts["json"] = {"success": False, "error": str(e)}
    
    # AST解析
    try:
        import ast
        ast_result = ast.literal_eval(value)
        parse_attempts["ast"] = {"success": True, "result_type": type(ast_result).__name__}
    except Exception as e:
        parse_attempts["ast"] = {"success": False, "error": str(e)}
    
    analysis["parse_attempts"] = parse_attempts
    
    logger.debug(f"📊 STRING_ANALYSIS: {json.dumps(analysis, ensure_ascii=False, indent=2)}")


def _analyze_list_param(location: str, param_name: str, value: list) -> None:
    """
    详细分析列表参数
    """
    analysis = {
        "location": location,
        "param_name": param_name,
        "length": len(value),
        "item_types": list(set(type(item).__name__ for item in value)) if value else [],
        "first_3_items": [_safe_repr(item) for item in value[:3]] if value else [],
        "all_strings": all(isinstance(item, str) for item in value) if value else True,
    }
    
    logger.debug(f"📊 LIST_ANALYSIS: {json.dumps(analysis, ensure_ascii=False, indent=2)}")


# 导出便捷函数
def debug_mcp_entry(tickers: Any, **kwargs) -> None:
    """
    MCP入口点调试 - 增强版
    """
    # 记录主要参数
    debug_param("MCP_ENTRY", "tickers", tickers, f"其他参数: {list(kwargs.keys())}")
    
    # 详细分析 tickers 参数
    logger.debug(f"🔍 ENHANCED_MCP_DEBUG: {{")
    logger.debug(f"  \"tickers_raw_type\": \"{type(tickers).__name__}\",")
    logger.debug(f"  \"tickers_raw_value\": {repr(tickers)},")
    logger.debug(f"  \"tickers_str_representation\": \"{str(tickers)}\",")
    logger.debug(f"  \"tickers_length\": {len(tickers) if hasattr(tickers, '__len__') else 'N/A'},")
    
    if isinstance(tickers, str):
        logger.debug(f"  \"string_analysis\": {{")
        logger.debug(f"    \"contains_brackets\": {tickers.startswith('[') and tickers.endswith(']')},")
        logger.debug(f"    \"contains_quotes\": {('\"' in tickers) or (\"'\" in tickers)},")
        logger.debug(f"    \"contains_comma\": {',' in tickers},")
        logger.debug(f"    \"contains_space\": {' ' in tickers},")
        logger.debug(f"    \"raw_bytes\": {repr(tickers.encode('utf-8'))}")
        logger.debug(f"  }},")
    
    # 记录所有参数的详细信息
    for key, value in kwargs.items():
        logger.debug(f"  \"{key}\": {{\"type\": \"{type(value).__name__}\", \"value\": {repr(value)}}},")
    
    logger.debug(f"}}")
    
    debug_stack_trace("MCP_ENTRY", "调用栈追踪")


def debug_parse_entry(tickers: Any) -> None:
    """
    解析函数入口调试
    """
    debug_param("PARSE_ENTRY", "tickers", tickers)


def debug_parse_result(original: Any, parsed: Any) -> None:
    """
    解析结果调试
    """
    logger.debug(f"🎯 PARSE_RESULT: {type(original).__name__} -> {type(parsed).__name__}")
    logger.debug(f"   原始值: {_safe_repr(original)}")
    logger.debug(f"   解析后: {_safe_repr(parsed)}")