"""
极简股票建仓分配工具 MCP集成
Simplified Stock Allocation Tool for MCP Server

核心公式：0.6 × assignment_prob + 0.4 × discount_depth
摒弃所有主观成分，专注CSP策略本质

作者: TradingAgentMCP  
日期: 2025-09-28
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json
from datetime import datetime


@dataclass
class SimpleStockData:
    """简化股票数据结构 - 只需4个核心字段"""
    symbol: str
    assignment_prob: float      # 分配概率 (Black-Scholes计算，完全客观)
    strike_price: float         # 执行价
    current_price: float        # 当前价格
    premium: float              # 权利金


class SimplifiedStockAllocationModel:
    """
    极简股票建仓分配模型
    
    核心理念：Cash-Secured PUT策略的本质是获得股票
    核心公式：0.6 × assignment_prob + 0.4 × discount_depth
    
    完全客观计算，无任何主观参数
    """
    
    def __init__(
        self,
        assignment_weight: float = 0.6,  # 分配概率权重
        discount_weight: float = 0.4,    # 折扣深度权重
        min_weight: float = 0.15,        # 最小权重限制
        max_weight: float = 0.35         # 最大权重限制
    ):
        """
        初始化简化分配模型
        
        Args:
            assignment_weight: 分配概率权重，默认0.6
            discount_weight: 折扣深度权重，默认0.4
            min_weight: 最小权重限制
            max_weight: 最大权重限制
        """
        if abs(assignment_weight + discount_weight - 1.0) > 0.001:
            raise ValueError(f"权重之和必须等于1，当前：{assignment_weight + discount_weight}")
            
        self.assignment_weight = assignment_weight
        self.discount_weight = discount_weight
        self.min_weight = min_weight
        self.max_weight = max_weight
    
    def calculate_assignment_score(self, assignment_prob: float) -> float:
        """
        分配概率得分计算 - 完全客观
        
        线性映射：65%分配概率=0分，100%分配概率=100分
        公式：(prob - 0.65) / (1.0 - 0.65) * 100
        
        Args:
            assignment_prob: 分配概率 (0.65-1.0)
            
        Returns:
            分配概率得分 (0-100)
        """
        if assignment_prob < 0.65:
            return 0.0
        
        # 线性映射：65%->0分，100%->100分
        score = (assignment_prob - 0.65) / (1.0 - 0.65) * 100
        return min(100.0, max(0.0, score))
    
    def calculate_discount_score(
        self,
        strike_price: float,
        current_price: float,
        premium: float
    ) -> tuple[float, float]:
        """
        折扣深度得分计算 - 完全客观
        
        折扣率 = (当前价格 - 有效成本) / 当前价格
        有效成本 = 执行价 - 权利金
        
        得分映射：线性映射，无封顶线
        每1%折扣=10分
        
        Args:
            strike_price: 执行价
            current_price: 当前价格  
            premium: 权利金
            
        Returns:
            (折扣深度得分, 实际折扣率)
        """
        # 计算有效成本 (实际买入成本)
        effective_cost = strike_price - premium
        
        # 计算折扣率
        discount_rate = (current_price - effective_cost) / current_price
        
        # 线性映射到得分：每1%折扣=10分，无封顶
        score = discount_rate * 1000  # 1%=10分
        
        return max(0.0, score), discount_rate
    
    def calculate_portfolio_weights(
        self,
        stocks: List[SimpleStockData]
    ) -> tuple[Dict[str, float], List[Dict]]:
        """
        计算投资组合权重 - 极简版本
        
        核心公式：0.6 × assignment_prob + 0.4 × discount_depth
        
        Args:
            stocks: 股票数据列表
            
        Returns:
            (权重字典, 详细评分列表)
        """
        if not stocks:
            return {}, []
        
        scores = []
        
        # 计算每只股票的评分
        for stock in stocks:
            # 1. 分配概率得分
            assignment_score = self.calculate_assignment_score(stock.assignment_prob)
            
            # 2. 折扣深度得分
            discount_score, discount_rate = self.calculate_discount_score(
                stock.strike_price,
                stock.current_price,
                stock.premium
            )
            
            # 3. 综合评分 - 核心公式
            total_score = (
                self.assignment_weight * assignment_score +
                self.discount_weight * discount_score
            )
            
            # 计算有效成本
            effective_cost = stock.strike_price - stock.premium
            
            scores.append({
                'symbol': stock.symbol,
                'total_score': total_score,
                'assignment_prob': stock.assignment_prob,
                'assignment_score': assignment_score,
                'discount_rate': discount_rate,
                'discount_score': discount_score,
                'effective_cost': effective_cost,
                'components': {
                    'assignment_weighted': self.assignment_weight * assignment_score,
                    'discount_weighted': self.discount_weight * discount_score
                },
                'raw_data': {
                    'strike_price': stock.strike_price,
                    'current_price': stock.current_price,
                    'premium': stock.premium
                }
            })
        
        # 按总分排序
        scores.sort(key=lambda x: x['total_score'], reverse=True)
        
        # 计算权重
        total_score_sum = sum(s['total_score'] for s in scores)
        
        if total_score_sum == 0:
            # 如果所有得分都是0，使用均等权重
            equal_weight = 1.0 / len(stocks)
            weights = {s['symbol']: equal_weight for s in scores}
        else:
            weights = {}
            for score_data in scores:
                raw_weight = score_data['total_score'] / total_score_sum
                
                # 应用最小最大权重限制
                adjusted_weight = max(self.min_weight, min(self.max_weight, raw_weight))
                weights[score_data['symbol']] = adjusted_weight
                
                # 记录权重信息
                score_data['raw_weight'] = raw_weight
                score_data['adjusted_weight'] = adjusted_weight
            
            # 重新归一化到100%
            weight_sum = sum(weights.values())
            for symbol in weights:
                weights[symbol] = weights[symbol] / weight_sum
                
        return weights, scores
    
    def analyze_allocation(
        self,
        weights: Dict[str, float],
        scores: List[Dict],
        stocks: List[SimpleStockData]
    ) -> Dict:
        """分析分配结果"""
        # 计算加权平均指标
        weighted_assignment_prob = sum(
            weights[score['symbol']] * score['assignment_prob']
            for score in scores
        )
        
        weighted_discount_rate = sum(
            weights[score['symbol']] * score['discount_rate']
            for score in scores
        )
        
        # 计算加权平均有效成本
        weighted_effective_cost = sum(
            weights[score['symbol']] * score['effective_cost']
            for score in scores
        )
        
        return {
            'portfolio_metrics': {
                'weighted_assignment_prob': weighted_assignment_prob,
                'weighted_discount_rate': weighted_discount_rate,
                'weighted_effective_cost': weighted_effective_cost,
                'diversification_level': len([w for w in weights.values() if w > 0.05]),
                'total_stocks': len(stocks)
            },
            'risk_assessment': {
                'max_single_weight': max(weights.values()),
                'min_single_weight': min(weights.values()),
                'weight_concentration': max(weights.values()) / min(weights.values()) if min(weights.values()) > 0 else float('inf')
            },
            'model_characteristics': {
                'model_type': 'Simplified Objective Model',
                'core_formula': f'{self.assignment_weight:.1f} × assignment_prob + {self.discount_weight:.1f} × discount_depth',
                'subjective_parameters': 0,
                'hardcoded_caps': 0,
                'data_fields_required': 4
            }
        }


async def simplified_stock_allocation_tool(
    stocks_data: List[Dict[str, Any]],
    assignment_weight: float = 0.6,
    discount_weight: float = 0.4,
    min_weight: float = 0.15,
    max_weight: float = 0.35,
    include_detailed_report: bool = True
) -> Dict[str, Any]:
    """
    极简股票建仓分配工具 - MCP接口
    
    核心公式：0.6 × assignment_prob + 0.4 × discount_depth
    
    Args:
        stocks_data: 股票数据列表，每个包含:
            - symbol: 股票代码 (必需)
            - assignment_prob: 分配概率 (必需)
            - strike_price: 执行价 (必需)
            - current_price: 当前价格 (必需)
            - premium: 权利金 (必需)
        assignment_weight: 分配概率权重 (默认0.6)
        discount_weight: 折扣深度权重 (默认0.4)
        min_weight: 最小权重限制 (默认0.15)
        max_weight: 最大权重限制 (默认0.35)
        include_detailed_report: 是否包含详细报告 (默认True)
    
    Returns:
        包含权重分配和分析结果的字典
    """
    
    try:
        # 验证输入数据
        if not stocks_data:
            return {
                'success': False,
                'error': '股票数据列表为空'
            }
        
        # 验证权重参数
        if abs(assignment_weight + discount_weight - 1.0) > 0.001:
            return {
                'success': False,
                'error': f'权重参数之和必须等于1，当前：{assignment_weight + discount_weight}'
            }
        
        # 转换为SimpleStockData对象
        stocks = []
        for data in stocks_data:
            try:
                required_fields = ['symbol', 'assignment_prob', 'strike_price', 'current_price', 'premium']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    return {
                        'success': False,
                        'error': f'股票 {data.get("symbol", "unknown")} 缺少必需字段: {missing_fields}'
                    }
                
                stock = SimpleStockData(
                    symbol=data['symbol'],
                    assignment_prob=data['assignment_prob'],
                    strike_price=data['strike_price'],
                    current_price=data['current_price'],
                    premium=data['premium']
                )
                stocks.append(stock)
                
            except (KeyError, TypeError, ValueError) as e:
                return {
                    'success': False,
                    'error': f'股票数据格式错误 ({data.get("symbol", "unknown")}): {str(e)}'
                }
        
        # 创建模型实例
        model = SimplifiedStockAllocationModel(
            assignment_weight=assignment_weight,
            discount_weight=discount_weight,
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
            'model_info': {
                'name': 'Simplified Stock Allocation Model',
                'version': '1.0',
                'core_formula': f'{assignment_weight:.1f} × assignment_prob + {discount_weight:.1f} × discount_depth',
                'parameters': {
                    'assignment_weight': assignment_weight,
                    'discount_weight': discount_weight,
                    'min_weight': min_weight,
                    'max_weight': max_weight
                }
            },
            'allocation_results': {
                'weights': weights,
                'detailed_scores': scores,
                'portfolio_analysis': analysis
            },
            'summary': {
                'total_stocks': len(stocks),
                'weighted_assignment_prob': analysis['portfolio_metrics']['weighted_assignment_prob'],
                'weighted_discount_rate': analysis['portfolio_metrics']['weighted_discount_rate'],
                'model_complexity': 'Minimal - 0 subjective parameters'
            }
        }
        
        # 添加详细报告
        if include_detailed_report:
            result['detailed_report'] = _generate_detailed_report(stocks, weights, scores, analysis, model)
        
        # 添加执行顺序建议
        result['execution_order'] = [
            {
                'priority': i + 1,
                'symbol': score['symbol'],
                'weight': weights[score['symbol']],
                'assignment_prob': f"{score['assignment_prob']:.1%}",
                'discount_rate': f"{score['discount_rate']:.2%}",
                'effective_cost': f"${score['effective_cost']:.2f}",
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


def _generate_detailed_report(
    stocks: List[SimpleStockData], 
    weights: Dict[str, float], 
    scores: List[Dict], 
    analysis: Dict,
    model: SimplifiedStockAllocationModel
) -> Dict:
    """生成详细报告"""
    return {
        'model_summary': {
            'approach': 'Objective-Only Calculation',
            'core_principle': 'Focus on CSP strategy essence: assignment probability + discount depth',
            'formula_breakdown': {
                'assignment_component': f'{model.assignment_weight:.1f} × assignment_prob_score',
                'discount_component': f'{model.discount_weight:.1f} × discount_depth_score',
                'total_formula': f'{model.assignment_weight:.1f} × assignment_prob + {model.discount_weight:.1f} × discount_depth'
            }
        },
        'calculation_details': [
            {
                'symbol': score['symbol'],
                'assignment_prob': f"{score['assignment_prob']:.1%}",
                'assignment_score': f"{score['assignment_score']:.1f}",
                'discount_rate': f"{score['discount_rate']:.2%}",
                'discount_score': f"{score['discount_score']:.1f}",
                'total_score': f"{score['total_score']:.2f}",
                'final_weight': f"{weights[score['symbol']]:.2%}",
                'calculation_breakdown': f"{score['components']['assignment_weighted']:.1f} + {score['components']['discount_weighted']:.1f} = {score['total_score']:.1f}"
            }
            for score in scores
        ],
        'portfolio_performance': analysis['portfolio_metrics'],
        'transparency_report': {
            'data_sources': {
                'assignment_prob': 'Black-Scholes Model (completely objective)',
                'discount_calculation': 'Pure price mathematics: (current_price - effective_cost) / current_price',
                'effective_cost': 'strike_price - premium'
            },
            'no_subjective_elements': True,
            'no_hardcoded_caps': True,
            'calculation_steps_verifiable': True
        }
    }


def _get_execution_reason(score: Dict, rank: int) -> str:
    """生成执行顺序的原因说明"""
    reasons = []
    
    if rank == 0:
        reasons.append("最高综合得分")
    
    if score['assignment_prob'] > 0.75:
        reasons.append(f"高分配概率({score['assignment_prob']:.1%})")
    
    if score['discount_rate'] > 0.05:
        reasons.append(f"显著折扣({score['discount_rate']:.1%})")
    
    if score['discount_rate'] > 0.08:
        reasons.append("极优折扣机会")
    
    return ", ".join(reasons) if reasons else "综合评分排序"


# MCP工具注册信息
SIMPLIFIED_TOOL_DEFINITION = {
    "name": "simplified_stock_allocation_tool",
    "description": "极简股票建仓分配工具 - 核心公式：0.6 × assignment_prob + 0.4 × discount_depth",
    "input_schema": {
        "type": "object",
        "properties": {
            "stocks_data": {
                "type": "array",
                "description": "股票数据列表，只需5个核心字段",
                "items": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "股票代码"},
                        "assignment_prob": {"type": "number", "description": "分配概率 (0.65-1.0)"},
                        "strike_price": {"type": "number", "description": "执行价"},
                        "current_price": {"type": "number", "description": "当前价格"},
                        "premium": {"type": "number", "description": "权利金"}
                    },
                    "required": ["symbol", "assignment_prob", "strike_price", "current_price", "premium"]
                }
            },
            "assignment_weight": {
                "type": "number",
                "description": "分配概率权重",
                "default": 0.6
            },
            "discount_weight": {
                "type": "number", 
                "description": "折扣深度权重",
                "default": 0.4
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
            "include_detailed_report": {
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
            "premium": 25.03
        },
        {
            "symbol": "TSLA", 
            "assignment_prob": 0.659,
            "strike_price": 480.0,
            "current_price": 440.40,
            "premium": 71.35
        },
        {
            "symbol": "META",
            "assignment_prob": 0.712,
            "strike_price": 780.0,
            "current_price": 743.75,
            "premium": 54.50
        },
        {
            "symbol": "NVDA",
            "assignment_prob": 0.665,
            "strike_price": 185.0,
            "current_price": 178.19,
            "premium": 18.25
        }
    ]
    
    async def test():
        print("=" * 80)
        print("极简股票建仓分配工具测试")
        print("=" * 80)
        
        result = await simplified_stock_allocation_tool(test_data)
        
        if result['success']:
            print(f"\n核心公式: {result['model_info']['core_formula']}")
            print(f"模型复杂度: {result['summary']['model_complexity']}")
            
            print("\n权重分配结果:")
            for symbol, weight in result['allocation_results']['weights'].items():
                print(f"  {symbol}: {weight:.2%}")
            
            print(f"\n组合指标:")
            metrics = result['allocation_results']['portfolio_analysis']['portfolio_metrics']
            print(f"  加权分配概率: {metrics['weighted_assignment_prob']:.1%}")
            print(f"  加权折扣率: {metrics['weighted_discount_rate']:.2%}")
            
            print("\n执行顺序:")
            for order in result['execution_order']:
                print(f"  {order['priority']}. {order['symbol']} ({order['weight']:.1%}) - {order['reason']}")
        else:
            print(f"错误: {result['error']}")
    
    asyncio.run(test())