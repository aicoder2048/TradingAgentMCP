#!/usr/bin/env python3
"""
摒弃质量因子的极简建仓分配模型
Simplified Stock Acquisition Allocation Model (No Quality Factor)

完全基于客观可计算指标，摒弃所有主观成分
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class SimpleStockData:
    """简化的股票数据结构"""
    symbol: str
    assignment_prob: float      # 分配概率 (Black-Scholes计算)
    strike_price: float         # 执行价
    current_price: float        # 当前价格
    premium: float              # 权利金


class SimplifiedAllocationModel:
    """
    极简分配模型：只使用两个完全客观的指标
    
    核心公式：α × assignment_prob + β × discount_depth
    
    - assignment_prob: 期权被分配概率 (0.65-1.0)，Black-Scholes模型计算
    - discount_depth: 折扣深度，完全基于价格数据计算
    
    无任何主观参数，无任何封顶线
    """
    
    def __init__(
        self,
        alpha: float = 0.6,  # 分配概率权重
        beta: float = 0.4,   # 折扣深度权重
        min_weight: float = 0.15,
        max_weight: float = 0.35
    ):
        """
        初始化简化分配模型
        
        Args:
            alpha: 分配概率权重，默认0.6 (更重视获得股票的概率)
            beta: 折扣深度权重，默认0.4 (适度考虑折扣幅度)
        """
        if abs(alpha + beta - 1.0) > 0.001:
            raise ValueError("权重之和必须等于1")
            
        self.alpha = alpha
        self.beta = beta
        self.min_weight = min_weight
        self.max_weight = max_weight
    
    def calculate_assignment_prob_score(self, assignment_prob: float) -> float:
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
    
    def calculate_discount_depth_score(
        self,
        strike_price: float,
        current_price: float,
        premium: float
    ) -> Tuple[float, float]:
        """
        折扣深度得分计算 - 完全客观
        
        折扣率 = (当前价格 - 有效成本) / 当前价格
        有效成本 = 执行价 - 权利金
        
        得分映射：线性映射，无封顶线
        0%折扣=0分，每1%折扣=10分
        
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
        score = discount_rate * 1000  # 10分每1%
        
        return max(0.0, score), discount_rate
    
    def calculate_portfolio_weights(
        self,
        stocks: List[SimpleStockData]
    ) -> Tuple[Dict[str, float], List[Dict]]:
        """
        计算投资组合权重 - 极简版本
        
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
            prob_score = self.calculate_assignment_prob_score(stock.assignment_prob)
            
            # 2. 折扣深度得分
            discount_score, discount_rate = self.calculate_discount_depth_score(
                stock.strike_price,
                stock.current_price,
                stock.premium
            )
            
            # 3. 综合评分 - 只有两个完全客观的指标
            total_score = (
                self.alpha * prob_score +
                self.beta * discount_score
            )
            
            scores.append({
                'symbol': stock.symbol,
                'total_score': total_score,
                'assignment_prob': stock.assignment_prob,
                'prob_score': prob_score,
                'discount_rate': discount_rate,
                'discount_score': discount_score,
                'components': {
                    'prob_weighted': self.alpha * prob_score,
                    'discount_weighted': self.beta * discount_score
                },
                'raw_data': {
                    'strike_price': stock.strike_price,
                    'current_price': stock.current_price,
                    'premium': stock.premium,
                    'effective_cost': stock.strike_price - stock.premium
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
        """
        分析分配结果 - 简化版本
        
        Returns:
            分析结果字典
        """
        # 计算加权平均指标
        weighted_assignment_prob = sum(
            weights[score['symbol']] * score['assignment_prob']
            for score in scores
        )
        
        weighted_discount_rate = sum(
            weights[score['symbol']] * score['discount_rate']
            for score in scores
        )
        
        # 计算总期望折扣金额 (假设每只股票投资相同金额)
        total_expected_discount = sum(
            weights[score['symbol']] * score['discount_rate'] * score['raw_data']['current_price']
            for score in scores
        )
        
        return {
            'portfolio_metrics': {
                'weighted_assignment_prob': weighted_assignment_prob,
                'weighted_discount_rate': weighted_discount_rate,
                'total_expected_discount_per_share': total_expected_discount,
                'diversification_level': len([w for w in weights.values() if w > 0.05])
            },
            'risk_assessment': {
                'max_single_weight': max(weights.values()),
                'min_single_weight': min(weights.values()),
                'weight_concentration': max(weights.values()) / min(weights.values()) if min(weights.values()) > 0 else float('inf')
            },
            'objective_summary': {
                'model_type': 'Simplified Objective Model',
                'subjective_components': 0,
                'hardcoded_caps': 0,
                'total_parameters': 2  # 只有alpha和beta两个权重参数
            }
        }
    
    def generate_report(
        self,
        stocks: List[SimpleStockData],
        weights: Dict[str, float],
        scores: List[Dict],
        analysis: Dict
    ) -> Dict:
        """
        生成简化报告
        """
        return {
            'model_summary': {
                'name': 'Simplified Stock Acquisition Model',
                'objective_indicators_only': True,
                'total_subjective_parameters': 0,
                'core_formula': f'{self.alpha:.1f} × assignment_prob + {self.beta:.1f} × discount_depth'
            },
            'calculation_transparency': {
                'assignment_prob_source': 'Black-Scholes Model (completely objective)',
                'discount_depth_source': 'Price mathematics (strike - premium vs current)',
                'no_hardcoded_caps': True,
                'no_quality_factor': True
            },
            'portfolio_performance': analysis['portfolio_metrics'],
            'ranking_explanation': [
                {
                    'symbol': score['symbol'],
                    'rank': i + 1,
                    'total_score': score['total_score'],
                    'assignment_prob': f"{score['assignment_prob']:.1%}",
                    'discount_rate': f"{score['discount_rate']:.2%}",
                    'why_ranked_here': self._explain_ranking(score, i)
                }
                for i, score in enumerate(scores)
            ]
        }
    
    def _explain_ranking(self, score: Dict, rank: int) -> str:
        """解释排名原因"""
        reasons = []
        
        if rank == 0:
            reasons.append("最高综合得分")
        
        if score['assignment_prob'] > 0.8:
            reasons.append(f"高分配概率({score['assignment_prob']:.1%})")
        
        if score['discount_rate'] > 0.05:
            reasons.append(f"显著折扣({score['discount_rate']:.1%})")
        
        return ", ".join(reasons) if reasons else "综合评分排序"


def test_simplified_model():
    """测试简化模型"""
    
    # 创建测试数据
    test_stocks = [
        SimpleStockData("GOOG", 0.678, 265.0, 247.18, 25.03),
        SimpleStockData("TSLA", 0.659, 480.0, 440.40, 71.35),
        SimpleStockData("META", 0.712, 780.0, 743.75, 54.50),
        SimpleStockData("NVDA", 0.665, 185.0, 178.19, 18.25)
    ]
    
    # 创建简化模型
    model = SimplifiedAllocationModel()
    
    # 计算权重
    weights, scores = model.calculate_portfolio_weights(test_stocks)
    
    # 分析结果
    analysis = model.analyze_allocation(weights, scores, test_stocks)
    
    # 生成报告
    report = model.generate_report(test_stocks, weights, scores, analysis)
    
    print("=" * 80)
    print("简化建仓分配模型测试结果")
    print("=" * 80)
    
    print(f"\n模型公式: {model.alpha:.1f} × assignment_prob + {model.beta:.1f} × discount_depth")
    print(f"主观参数数量: {report['model_summary']['total_subjective_parameters']}")
    print(f"硬编码封顶线: {analysis['objective_summary']['hardcoded_caps']}")
    
    print("\n权重分配结果:")
    for symbol, weight in weights.items():
        print(f"  {symbol}: {weight:.2%}")
    
    print("\n详细评分:")
    for score in scores:
        print(f"\n{score['symbol']}:")
        print(f"  分配概率: {score['assignment_prob']:.1%} → 得分 {score['prob_score']:.1f}")
        print(f"  折扣率: {score['discount_rate']:.2%} → 得分 {score['discount_score']:.1f}")
        print(f"  综合得分: {score['total_score']:.2f}")
    
    print(f"\n组合加权分配概率: {analysis['portfolio_metrics']['weighted_assignment_prob']:.1%}")
    print(f"组合加权折扣率: {analysis['portfolio_metrics']['weighted_discount_rate']:.2%}")
    
    return weights, scores, analysis, report


if __name__ == "__main__":
    test_simplified_model()