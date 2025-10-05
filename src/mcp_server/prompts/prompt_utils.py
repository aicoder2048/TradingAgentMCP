"""
MCP Server Prompt公共工具模块

为各类期权策略Prompt提供通用的辅助函数。
消除代码重复，提供统一的输入解析和参数转换功能。
"""

from typing import List, Union
import json
import ast


def parse_tickers_input(tickers_input: Union[List[str], str]) -> List[str]:
    """
    解析不同格式的tickers输入

    支持的格式:
    - Python列表: ['TSLA', 'GOOG', 'META']
    - JSON字符串: ["TSLA", "GOOG", "META"]
    - 空格分隔: "TSLA GOOG META"
    - 逗号分隔: "TSLA,GOOG,META"
    - 单个ticker: "TSLA"

    Args:
        tickers_input: 输入的tickers，可以是列表或字符串

    Returns:
        List[str]: 解析后的ticker列表

    Example:
        >>> parse_tickers_input('AAPL TSLA GOOG')
        ['AAPL', 'TSLA', 'GOOG']

        >>> parse_tickers_input('["AAPL", "TSLA"]')
        ['AAPL', 'TSLA']

        >>> parse_tickers_input(['AAPL', 'TSLA'])
        ['AAPL', 'TSLA']
    """
    # DEBUG: 记录函数入口
    try:
        from ..utils.debug_logger import debug_parse_step, debug_param
        debug_param(
            "parse_tickers_input:ENTRY",
            "tickers_input",
            tickers_input,
            f"Initial type: {type(tickers_input).__name__}"
        )
    except:
        pass

    # 如果已经是列表，直接返回
    if isinstance(tickers_input, list):
        try:
            debug_parse_step(
                "parse_tickers_input",
                "CHECK_IS_LIST",
                tickers_input,
                tickers_input,
                success=True
            )
        except:
            pass
        return tickers_input

    # 如果不是字符串，转换为字符串
    if not isinstance(tickers_input, str):
        result = [str(tickers_input)]
        try:
            debug_parse_step(
                "parse_tickers_input",
                "CONVERT_TO_STRING",
                tickers_input,
                result,
                success=True
            )
        except:
            pass
        return result

    # 去除首尾空格
    tickers_str = tickers_input.strip()

    try:
        debug_param(
            "parse_tickers_input:STRIPPED",
            "tickers_str",
            tickers_str,
            f"After strip, length: {len(tickers_str)}"
        )
    except:
        pass

    # 如果为空字符串
    if not tickers_str:
        try:
            debug_parse_step(
                "parse_tickers_input",
                "EMPTY_STRING",
                tickers_str,
                [],
                success=True
            )
        except:
            pass
        return []

    # 方法1: 尝试JSON解析
    try:
        result = json.loads(tickers_str)
        if isinstance(result, list):
            try:
                debug_parse_step(
                    "parse_tickers_input",
                    "JSON_PARSE_LIST",
                    tickers_str,
                    result,
                    success=True
                )
            except:
                pass
            return result
        elif isinstance(result, str):
            result_list = [result]
            try:
                debug_parse_step(
                    "parse_tickers_input",
                    "JSON_PARSE_STRING",
                    tickers_str,
                    result_list,
                    success=True
                )
            except:
                pass
            return result_list
    except Exception as e:
        try:
            debug_parse_step(
                "parse_tickers_input",
                "JSON_PARSE_FAILED",
                tickers_str,
                None,
                success=False,
                error=str(e)
            )
        except:
            pass

    # 方法2: 尝试Python ast解析
    try:
        result = ast.literal_eval(tickers_str)
        if isinstance(result, list):
            try:
                debug_parse_step(
                    "parse_tickers_input",
                    "AST_PARSE_LIST",
                    tickers_str,
                    result,
                    success=True
                )
            except:
                pass
            return result
        elif isinstance(result, str):
            result_list = [result]
            try:
                debug_parse_step(
                    "parse_tickers_input",
                    "AST_PARSE_STRING",
                    tickers_str,
                    result_list,
                    success=True
                )
            except:
                pass
            return result_list
    except Exception as e:
        try:
            debug_parse_step(
                "parse_tickers_input",
                "AST_PARSE_FAILED",
                tickers_str,
                None,
                success=False,
                error=str(e)
            )
        except:
            pass

    # 方法3: 检查是否是逗号分隔（优先于空格）
    if ',' in tickers_str:
        result = [s.strip() for s in tickers_str.split(',') if s.strip()]
        try:
            debug_parse_step(
                "parse_tickers_input",
                "COMMA_SPLIT",
                tickers_str,
                result,
                success=True
            )
        except:
            pass
        return result

    # 方法4: 检查是否是空格分隔
    if ' ' in tickers_str:
        result = [s.strip() for s in tickers_str.split() if s.strip()]
        try:
            debug_parse_step(
                "parse_tickers_input",
                "SPACE_SPLIT",
                tickers_str,
                result,
                success=True
            )
        except:
            pass
        return result

    # 方法5: 作为单个ticker
    result = [tickers_str]
    try:
        debug_parse_step(
            "parse_tickers_input",
            "SINGLE_TICKER",
            tickers_str,
            result,
            success=True
        )
    except:
        pass
    return result


def get_duration_from_days(min_days: int, max_days: int) -> str:
    """
    根据天数范围转换为duration参数

    Args:
        min_days: 最小天数
        max_days: 最大天数

    Returns:
        str: duration参数值 ("1w", "2w", "1m", "3m", "6m", "1y")

    Example:
        >>> get_duration_from_days(7, 14)
        '1w'

        >>> get_duration_from_days(21, 35)
        '1m'

        >>> get_duration_from_days(60, 90)
        '3m'
    """
    avg_days = (min_days + max_days) / 2

    if avg_days <= 9:
        return "1w"
    elif avg_days <= 18:
        return "2w"
    elif avg_days <= 35:
        return "1m"
    elif avg_days <= 100:
        return "3m"
    elif avg_days <= 190:
        return "6m"
    else:
        return "1y"
