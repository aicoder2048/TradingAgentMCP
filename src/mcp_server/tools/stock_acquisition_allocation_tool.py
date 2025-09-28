"""
股票建仓导向分配工具 MCP集成
Stock Acquisition Allocation Tool for MCP Server

该工具将建仓导向专属分配模型集成到MCP服务器，
提供API接口进行投资组合权重优化。

作者: TradingAgentMCP
日期: 2025-09-28
"""

from typing import Dict, List, Optional, Any
from dataclasses import asdict
import json
from datetime import datetime

try:
    from .portfolio_allocation_model import (
        StockData,
        StockAcquisitionAllocationModel
    )
except ImportError:
    # 用于独立测试
    from portfolio_allocation_model import (
        StockData,
        StockAcquisitionAllocationModel
    )


async def stock_acquisition_allocation_tool(
    stocks_data: List[Dict[str, Any]],
    alpha: float = 0.45,
    beta: float = 0.35,
    gamma: float = 0.20,
    min_weight: float = 0.15,
    max_weight: float = 0.35,
    include_report: bool = True
) -> Dict[str, Any]:
    """
    计算股票建仓导向的最优投资组合权重分配
    
    使用建仓导向专属分配模型，通过完全量化的指标计算最优权重。
    
    Args:
        stocks_data: 股票期权策略数据列表，每个元素包含:
            - symbol: 股票代码
            - assignment_prob: 分配概率 (0.65-1.0)
            - strike_price: 执行价
            - current_price: 当前价格
            - premium: 权利金
            - annual_return: 年化收益率 (小数形式)
            - implied_volatility: 隐含波动率 (小数形式)
            - week_52_high: 52周最高价
            - days_to_expiry: 到期天数
            - delta: Delta值
            - theta: Theta值
        
        alpha: 分配概率权重 (默认0.45)
        beta: 折扣深度权重 (默认0.35)  
        gamma: 质量因子权重 (默认0.20)
        min_weight: 最小权重限制 (默认0.15)
        max_weight: 最大权重限制 (默认0.35)
        include_report: 是否包含详细报告 (默认True)
    
    Returns:
        包含权重分配结果、评分详情和分析报告的字典
    """
    
    try:
        # 验证输入数据
        if not stocks_data:
            return {
                'success': False,
                'error': '股票数据列表为空'
            }
        
        # 验证权重参数
        if abs(alpha + beta + gamma - 1.0) > 0.001:
            return {
                'success': False,
                'error': '权重参数之和必须等于1'
            }
        
        # 转换为StockData对象
        stocks = []
        for data in stocks_data:
            try:
                # 提供默认值以处理可选字段
                stock = StockData(
                    symbol=data['symbol'],
                    assignment_prob=data.get('assignment_prob', 0.65),
                    strike_price=data['strike_price'],
                    current_price=data['current_price'],
                    premium=data['premium'],
                    annual_return=data.get('annual_return', 0.25),
                    implied_volatility=data.get('implied_volatility', 0.30),
                    week_52_high=data.get('week_52_high', data['current_price'] * 1.1),
                    days_to_expiry=data.get('days_to_expiry', 82),
                    delta=data.get('delta', -0.5),
                    theta=data.get('theta', -0.1)
                )
                stocks.append(stock)
            except (KeyError, TypeError) as e:
                return {
                    'success': False,
                    'error': f'股票数据格式错误 ({data.get("symbol", "unknown")}): {str(e)}'
                }
        
        # 创建模型实例
        model = StockAcquisitionAllocationModel(
            alpha=alpha,
            beta=beta,
            gamma=gamma,
            min_weight=min_weight,
            max_weight=max_weight
        )
        
        # 计算权重
        weights, scores = model.calculate_portfolio_weights(stocks)
        
        # 分析结果
        analysis = model.analyze_allocation(weights, scores, stocks)
        
        # 构建返回结果
        result = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'model_parameters': {
                'alpha': alpha,
                'beta': beta,
                'gamma': gamma,
                'min_weight': min_weight,
                'max_weight': max_weight
            },
            'weights': weights,
            'detailed_scores': scores,
            'portfolio_analysis': analysis,
            'optimization_summary': {
                'total_stocks': len(stocks),
                'weighted_assignment_prob': analysis['portfolio_metrics']['weighted_assignment_prob'],
                'weighted_annual_return': analysis['portfolio_metrics']['weighted_annual_return'],
                'improvement_vs_equal': analysis['comparison']['improvement_percent']
            }
        }
        
        # 添加详细报告
        if include_report:
            report = model.generate_report(stocks, weights, scores, analysis)
            result['detailed_report'] = report
        
        # 添加建议执行顺序
        result['execution_order'] = [
            {
                'priority': i + 1,
                'symbol': score['symbol'],
                'weight': weights[score['symbol']],
                'allocation_amount': None,  # 需要总资金才能计算
                'reason': _get_execution_reason(score, i)
            }
            for i, score in enumerate(scores)
        ]
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': f'计算过程出错: {str(e)}'
        }


def _get_execution_reason(score: Dict, rank: int) -> str:
    """生成执行顺序的原因说明"""
    reasons = []
    
    if rank == 0:
        reasons.append("最高综合评分")
    
    if score['discount_rate'] > 0.06:
        reasons.append(f"优秀折扣率({score['discount_rate']:.1%})")
    
    if score['prob_score'] > 5:
        reasons.append("高分配概率")
    
    if score['quality_details']['return_score'] > 90:
        reasons.append("极高年化收益")
    
    if score['quality_details']['iv_score'] > 80:
        reasons.append("高波动率机会")
    
    return ", ".join(reasons) if reasons else "综合评分排序"


async def calculate_allocation_with_capital(
    stocks_data: List[Dict[str, Any]],
    total_capital: float,
    **kwargs
) -> Dict[str, Any]:
    """
    计算带资金分配的投资组合权重
    
    Args:
        stocks_data: 股票期权策略数据列表
        total_capital: 总投资资金
        **kwargs: 传递给stock_acquisition_allocation_tool的其他参数
    
    Returns:
        包含具体资金分配的结果
    """
    # 调用基础分配工具
    result = await stock_acquisition_allocation_tool(stocks_data, **kwargs)
    
    if result['success']:
        # 计算具体资金分配
        weights = result['weights']
        capital_allocation = {}
        
        for symbol, weight in weights.items():
            capital_allocation[symbol] = {
                'weight': weight,
                'capital': total_capital * weight,
                'capital_formatted': f"${total_capital * weight:,.2f}"
            }
        
        result['capital_allocation'] = capital_allocation
        result['total_capital'] = total_capital
        
        # 更新执行顺序中的资金分配
        for item in result['execution_order']:
            symbol = item['symbol']
            item['allocation_amount'] = capital_allocation[symbol]['capital']
            item['allocation_formatted'] = capital_allocation[symbol]['capital_formatted']
    
    return result


# MCP工具注册信息
TOOL_DEFINITION = {
    "name": "stock_acquisition_allocation_tool",
    "description": "计算股票建仓导向的最优投资组合权重分配",
    "input_schema": {
        "type": "object",
        "properties": {
            "stocks_data": {
                "type": "array",
                "description": "股票期权策略数据列表",
                "items": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "股票代码"},
                        "assignment_prob": {"type": "number", "description": "分配概率"},
                        "strike_price": {"type": "number", "description": "执行价"},
                        "current_price": {"type": "number", "description": "当前价格"},
                        "premium": {"type": "number", "description": "权利金"},
                        "annual_return": {"type": "number", "description": "年化收益率"},
                        "implied_volatility": {"type": "number", "description": "隐含波动率"},
                        "week_52_high": {"type": "number", "description": "52周最高价"},
                        "days_to_expiry": {"type": "integer", "description": "到期天数"},
                        "delta": {"type": "number", "description": "Delta值"},
                        "theta": {"type": "number", "description": "Theta值"}
                    },
                    "required": ["symbol", "strike_price", "current_price", "premium"]
                }
            },
            "alpha": {
                "type": "number",
                "description": "分配概率权重",
                "default": 0.45
            },
            "beta": {
                "type": "number", 
                "description": "折扣深度权重",
                "default": 0.35
            },
            "gamma": {
                "type": "number",
                "description": "质量因子权重", 
                "default": 0.20
            },
            "min_weight": {
                "type": "number",
                "description": "最小权重限制",
                "default": 0.15
            },
            "max_weight": {
                "type": "number",
                "description": "最大权重限制",
                "default": 0.35
            },
            "include_report": {
                "type": "boolean",
                "description": "是否包含详细报告",
                "default": True
            }
        },
        "required": ["stocks_data"]
    }
}


if __name__ == "__main__":
    # 测试工具
    import asyncio
    
    # 创建测试数据
    test_data = [
        {
            "symbol": "GOOG",
            "assignment_prob": 0.678,
            "strike_price": 265.0,
            "current_price": 247.18,
            "premium": 25.03,
            "annual_return": 0.452,
            "implied_volatility": 0.325,
            "week_52_high": 256.70,
            "days_to_expiry": 82,
            "delta": -0.621,
            "theta": -0.098
        },
        {
            "symbol": "TSLA",
            "assignment_prob": 0.659,
            "strike_price": 480.0,
            "current_price": 440.40,
            "premium": 71.35,
            "annual_return": 0.542,
            "implied_volatility": 0.592,
            "week_52_high": 488.54,
            "days_to_expiry": 82,
            "delta": -0.546,
            "theta": -0.323
        }
    ]
    
    async def test():
        # 测试基础分配
        result = await stock_acquisition_allocation_tool(test_data)
        print("基础分配结果:")
        print(json.dumps(result['optimization_summary'], indent=2, ensure_ascii=False))
        print("\n权重分配:")
        for symbol, weight in result['weights'].items():
            print(f"  {symbol}: {weight:.2%}")
        
        print("\n" + "="*60 + "\n")
        
        # 测试带资金分配
        result_with_capital = await calculate_allocation_with_capital(
            test_data,
            total_capital=5000000
        )
        print("带资金分配结果:")
        for symbol, allocation in result_with_capital['capital_allocation'].items():
            print(f"  {symbol}: {allocation['weight']:.2%} = {allocation['capital_formatted']}")
    
    asyncio.run(test())