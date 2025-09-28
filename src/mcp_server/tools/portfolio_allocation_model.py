"""
建仓导向专属分配模型 (Stock Acquisition-Oriented Allocation Model)

该模型专门为现金担保PUT策略的建仓导向目标设计，
通过完全量化的指标计算最优投资组合权重分配。

作者: TradingAgentMCP
日期: 2025-09-28
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json


@dataclass
class StockData:
    """股票期权策略数据"""
    symbol: str
    assignment_prob: float  # 分配概率 (0.65-1.0)
    strike_price: float     # 执行价
    current_price: float    # 当前价格
    premium: float          # 权利金
    annual_return: float    # 年化收益率 (小数形式，如0.45表示45%)
    implied_volatility: float  # 隐含波动率 (小数形式)
    week_52_high: float     # 52周最高价
    days_to_expiry: int     # 到期天数
    delta: float           # Delta值（负数）
    theta: float           # Theta值（负数）


class StockAcquisitionAllocationModel:
    """
    建仓导向专属分配模型
    
    核心公式：
    综合评分 = α × 分配概率得分 + β × 折扣深度得分 + γ × 质量因子得分
    """
    
    def __init__(
        self,
        alpha: float = 0.45,  # 分配概率权重
        beta: float = 0.35,   # 折扣深度权重
        gamma: float = 0.20,  # 质量因子权重
        min_weight: float = 0.15,  # 最小权重限制
        max_weight: float = 0.35,  # 最大权重限制
    ):
        """
        初始化模型参数
        
        Args:
            alpha: 分配概率权重 (默认0.45)
            beta: 折扣深度权重 (默认0.35)
            gamma: 质量因子权重 (默认0.20)
            min_weight: 最小权重限制 (默认0.15)
            max_weight: 最大权重限制 (默认0.35)
        """
        # 验证权重和为1
        assert abs(alpha + beta + gamma - 1.0) < 0.001, "权重之和必须等于1"
        
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.min_weight = min_weight
        self.max_weight = max_weight
    
    def calculate_assignment_probability_score(self, prob: float) -> float:
        """
        计算分配概率得分
        
        线性映射：65% = 0分, 100% = 100分
        
        Args:
            prob: 分配概率 (0.65-1.0)
            
        Returns:
            得分 (0-100)
        """
        # 确保概率在合理范围内
        prob = max(0.65, min(1.0, prob))
        
        # 线性映射
        score = (prob - 0.65) / 0.35 * 100
        
        return max(0, min(100, score))
    
    def calculate_discount_depth_score(
        self, 
        strike_price: float,
        current_price: float,
        premium: float
    ) -> Tuple[float, float]:
        """
        计算折扣深度得分
        
        折扣率映射：0% = 0分, 10% = 100分
        
        Args:
            strike_price: 执行价
            current_price: 当前价格
            premium: 权利金
            
        Returns:
            (折扣深度得分, 实际折扣率)
        """
        # 计算有效成本
        effective_cost = strike_price - premium
        
        # 计算折扣率
        discount_rate = (current_price - effective_cost) / current_price
        
        # 映射到得分
        score = min(discount_rate / 0.10 * 100, 100)
        
        return max(0, score), discount_rate
    
    def calculate_quality_factor_score(
        self,
        stock: StockData
    ) -> Tuple[float, Dict[str, float]]:
        """
        计算质量因子得分
        
        质量因子 = 0.30×年化收益得分 + 0.25×隐含波动率得分 + 
                   0.25×价格位置得分 + 0.20×时间价值得分
        
        Args:
            stock: StockData对象
            
        Returns:
            (质量因子综合得分, 各子项得分详情)
        """
        # 1. 年化收益得分 (50%封顶)
        return_score = min(stock.annual_return / 0.50 * 100, 100)
        
        # 2. 隐含波动率得分 (60%封顶)
        iv_score = min(stock.implied_volatility / 0.60 * 100, 100)
        
        # 3. 价格位置得分 (距离52周高点越远越好)
        position_score = (1 - stock.current_price / stock.week_52_high) * 100
        position_score = max(0, min(100, position_score))
        
        # 4. 时间价值得分 (权利金/执行价比率，15%封顶)
        time_value_ratio = stock.premium / stock.strike_price
        time_value_score = min(time_value_ratio / 0.15 * 100, 100)
        
        # 综合质量因子得分
        quality_score = (
            0.30 * return_score +
            0.25 * iv_score +
            0.25 * position_score +
            0.20 * time_value_score
        )
        
        details = {
            'return_score': return_score,
            'iv_score': iv_score,
            'position_score': position_score,
            'time_value_score': time_value_score
        }
        
        return quality_score, details
    
    def calculate_portfolio_weights(
        self,
        stocks: List[StockData]
    ) -> Tuple[Dict[str, float], List[Dict]]:
        """
        计算投资组合权重
        
        Args:
            stocks: StockData对象列表
            
        Returns:
            (权重字典, 详细评分列表)
        """
        if not stocks:
            return {}, []
        
        scores = []
        
        for stock in stocks:
            # 1. 分配概率得分
            prob_score = self.calculate_assignment_probability_score(
                stock.assignment_prob
            )
            
            # 2. 折扣深度得分
            discount_score, discount_rate = self.calculate_discount_depth_score(
                stock.strike_price,
                stock.current_price,
                stock.premium
            )
            
            # 3. 质量因子得分
            quality_score, quality_details = self.calculate_quality_factor_score(
                stock
            )
            
            # 综合评分
            total_score = (
                self.alpha * prob_score +
                self.beta * discount_score +
                self.gamma * quality_score
            )
            
            scores.append({
                'symbol': stock.symbol,
                'total_score': total_score,
                'prob_score': prob_score,
                'discount_score': discount_score,
                'discount_rate': discount_rate,
                'quality_score': quality_score,
                'quality_details': quality_details,
                'components': {
                    'prob_weighted': self.alpha * prob_score,
                    'discount_weighted': self.beta * discount_score,
                    'quality_weighted': self.gamma * quality_score
                }
            })
        
        # 按总分排序
        scores.sort(key=lambda x: x['total_score'], reverse=True)
        
        # 计算初始权重
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
                
                # 记录原始权重
                score_data['raw_weight'] = raw_weight
                score_data['adjusted_weight'] = adjusted_weight
            
            # 重新归一化到100%
            weight_sum = sum(weights.values())
            for symbol in weights:
                weights[symbol] = weights[symbol] / weight_sum
            
            # 更新最终权重
            for score_data in scores:
                score_data['final_weight'] = weights[score_data['symbol']]
        
        return weights, scores
    
    def analyze_allocation(
        self,
        weights: Dict[str, float],
        scores: List[Dict],
        stocks: List[StockData]
    ) -> Dict:
        """
        分析权重分配结果
        
        Args:
            weights: 权重字典
            scores: 评分详情列表
            stocks: 原始股票数据
            
        Returns:
            分析结果字典
        """
        # 创建股票数据映射
        stock_map = {s.symbol: s for s in stocks}
        
        # 计算加权平均指标
        weighted_prob = sum(
            weights[s] * stock_map[s].assignment_prob 
            for s in weights
        )
        
        weighted_return = sum(
            weights[s] * stock_map[s].annual_return 
            for s in weights
        )
        
        weighted_iv = sum(
            weights[s] * stock_map[s].implied_volatility 
            for s in weights
        )
        
        # 计算集中度指标
        max_weight = max(weights.values())
        min_weight = min(weights.values())
        concentration_ratio = max_weight - min_weight
        
        # 与均等权重对比
        equal_weight = 1.0 / len(weights)
        equal_weighted_return = sum(
            equal_weight * stock_map[s].annual_return 
            for s in weights
        )
        
        return {
            'portfolio_metrics': {
                'weighted_assignment_prob': weighted_prob,
                'weighted_annual_return': weighted_return,
                'weighted_implied_volatility': weighted_iv,
            },
            'concentration': {
                'max_weight': max_weight,
                'min_weight': min_weight,
                'concentration_ratio': concentration_ratio,
            },
            'comparison': {
                'equal_weighted_return': equal_weighted_return,
                'optimized_return': weighted_return,
                'improvement': weighted_return - equal_weighted_return,
                'improvement_percent': (weighted_return - equal_weighted_return) / equal_weighted_return * 100
            },
            'ranking': [
                {
                    'rank': i + 1,
                    'symbol': score['symbol'],
                    'weight': weights[score['symbol']],
                    'total_score': score['total_score']
                }
                for i, score in enumerate(scores)
            ]
        }
    
    def generate_report(
        self,
        stocks: List[StockData],
        weights: Dict[str, float],
        scores: List[Dict],
        analysis: Dict
    ) -> str:
        """
        生成详细的分析报告
        
        Args:
            stocks: 股票数据列表
            weights: 权重分配结果
            scores: 评分详情
            analysis: 分析结果
            
        Returns:
            格式化的报告字符串
        """
        report = []
        report.append("=" * 80)
        report.append("建仓导向专属分配模型 - 分析报告")
        report.append("=" * 80)
        report.append("")
        
        # 模型参数
        report.append(f"模型参数:")
        report.append(f"  α (分配概率权重): {self.alpha:.2%}")
        report.append(f"  β (折扣深度权重): {self.beta:.2%}")
        report.append(f"  γ (质量因子权重): {self.gamma:.2%}")
        report.append(f"  权重限制: {self.min_weight:.1%} - {self.max_weight:.1%}")
        report.append("")
        
        # 权重分配结果
        report.append("权重分配结果:")
        report.append("-" * 40)
        for rank_info in analysis['ranking']:
            report.append(
                f"{rank_info['rank']:2d}. {rank_info['symbol']:6s} "
                f"权重: {rank_info['weight']:6.2%}  "
                f"综合评分: {rank_info['total_score']:6.2f}"
            )
        report.append("")
        
        # 详细评分分解
        report.append("详细评分分解:")
        report.append("-" * 40)
        for score in scores:
            report.append(f"\n{score['symbol']}:")
            report.append(f"  综合评分: {score['total_score']:.2f}")
            report.append(f"  ├─ 分配概率得分: {score['prob_score']:.2f} (权重贡献: {score['components']['prob_weighted']:.2f})")
            report.append(f"  ├─ 折扣深度得分: {score['discount_score']:.2f} (权重贡献: {score['components']['discount_weighted']:.2f})")
            report.append(f"  │   └─ 实际折扣率: {score['discount_rate']:.2%}")
            report.append(f"  └─ 质量因子得分: {score['quality_score']:.2f} (权重贡献: {score['components']['quality_weighted']:.2f})")
            
            details = score['quality_details']
            report.append(f"      ├─ 年化收益: {details['return_score']:.2f}")
            report.append(f"      ├─ 隐含波动率: {details['iv_score']:.2f}")
            report.append(f"      ├─ 价格位置: {details['position_score']:.2f}")
            report.append(f"      └─ 时间价值: {details['time_value_score']:.2f}")
        
        report.append("")
        report.append("投资组合指标:")
        report.append("-" * 40)
        metrics = analysis['portfolio_metrics']
        report.append(f"  加权分配概率: {metrics['weighted_assignment_prob']:.2%}")
        report.append(f"  加权年化收益: {metrics['weighted_annual_return']:.2%}")
        report.append(f"  加权隐含波动率: {metrics['weighted_implied_volatility']:.2%}")
        report.append("")
        
        # 与均等权重对比
        report.append("与均等权重对比:")
        report.append("-" * 40)
        comp = analysis['comparison']
        report.append(f"  均等权重收益: {comp['equal_weighted_return']:.2%}")
        report.append(f"  优化权重收益: {comp['optimized_return']:.2%}")
        report.append(f"  改善幅度: {comp['improvement']:.2%} ({comp['improvement_percent']:+.1f}%)")
        report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)


def create_sample_data() -> List[StockData]:
    """创建示例数据用于测试"""
    return [
        StockData(
            symbol="GOOG",
            assignment_prob=0.678,
            strike_price=265.0,
            current_price=247.18,
            premium=25.03,
            annual_return=0.452,
            implied_volatility=0.325,
            week_52_high=256.70,
            days_to_expiry=82,
            delta=-0.621,
            theta=-0.098
        ),
        StockData(
            symbol="META",
            assignment_prob=0.685,
            strike_price=780.0,
            current_price=743.75,
            premium=54.50,
            annual_return=0.428,
            implied_volatility=0.385,
            week_52_high=796.25,
            days_to_expiry=82,
            delta=-0.645,
            theta=-0.125
        ),
        StockData(
            symbol="NVDA",
            assignment_prob=0.662,
            strike_price=185.0,
            current_price=178.19,
            premium=18.25,
            annual_return=0.525,
            implied_volatility=0.485,
            week_52_high=184.55,
            days_to_expiry=82,
            delta=-0.598,
            theta=-0.145
        ),
        StockData(
            symbol="TSLA",
            assignment_prob=0.659,
            strike_price=480.0,
            current_price=440.40,
            premium=71.35,
            annual_return=0.542,
            implied_volatility=0.592,
            week_52_high=488.54,
            days_to_expiry=82,
            delta=-0.546,
            theta=-0.323
        )
    ]


if __name__ == "__main__":
    # 测试模型
    model = StockAcquisitionAllocationModel()
    stocks = create_sample_data()
    
    # 计算权重
    weights, scores = model.calculate_portfolio_weights(stocks)
    
    # 分析结果
    analysis = model.analyze_allocation(weights, scores, stocks)
    
    # 生成报告
    report = model.generate_report(stocks, weights, scores, analysis)
    print(report)
    
    # 输出JSON格式结果（便于API调用）
    result = {
        'weights': weights,
        'scores': scores,
        'analysis': analysis
    }
    
    print("\n\nJSON输出:")
    print(json.dumps(result, indent=2, ensure_ascii=False))