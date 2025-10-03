"""
MCP工具：智能期权到期日选择器
Optimal Expiration Selector Tool for MCP

提供基于客观数学指标的期权到期日优化选择
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import logging
from dataclasses import asdict

from .expiration_optimizer import ExpirationOptimizer, ExpirationCandidate

logger = logging.getLogger(__name__)


class OptimalExpirationSelectorTool:
    """
    智能期权到期日选择工具
    
    基于Theta效率、Gamma风险、流动性等客观指标
    自动选择最优到期日，避免主观硬编码
    """
    
    name = "optimal_expiration_selector_tool"
    description = """智能期权到期日选择器 - 基于客观数学指标优化选择

为期权策略自动选择最优到期日，完全基于量化指标：
- Theta效率曲线（30-45天最优）
- Gamma风险控制（避免<21天的高风险）
- 流动性评分（周期权/月期权优先）
- 事件缓冲（避开财报等事件）

输入参数：
- symbol: 股票代码
- available_expirations: 可用到期日列表（可选，如不提供则自动获取）
- strategy_type: 策略类型 - "csp", "covered_call"等（默认"csp"）
- volatility: 当前隐含波动率（可选，默认0.3）
- weights: 自定义权重配置（可选）

返回：
- 最优到期日及详细评分
- 选择理由说明
- 各维度评分细节
"""
    
    def __init__(self, tradier_client=None):
        """初始化工具"""
        self.tradier_client = tradier_client
        self.optimizer = ExpirationOptimizer()
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行到期日优化选择
        
        Args:
            symbol: 股票代码
            available_expirations: 可用到期日列表（可选）
            strategy_type: 策略类型
            volatility: 隐含波动率
            weights: 自定义权重
        
        Returns:
            优化结果
        """
        try:
            # 提取参数
            symbol = kwargs.get('symbol', '').upper()
            if not symbol:
                return self._error_response("缺少必需参数: symbol")
            
            strategy_type = kwargs.get('strategy_type', 'csp')
            volatility = kwargs.get('volatility', 0.3)
            weights = kwargs.get('weights')
            
            # 获取或使用提供的到期日列表
            available_expirations = kwargs.get('available_expirations')
            
            if not available_expirations:
                # 如果没有提供，尝试从Tradier获取
                available_expirations = self._fetch_available_expirations(symbol)
                if not available_expirations:
                    return self._error_response(f"无法获取{symbol}的可用到期日")
            
            # 确保到期日格式正确
            formatted_expirations = self._format_expirations(available_expirations)
            
            # 创建优化器（可能使用自定义权重）
            if weights:
                optimizer = ExpirationOptimizer(weights)
            else:
                # 根据策略类型使用不同的默认权重
                strategy_weights = self._get_strategy_weights(strategy_type)
                optimizer = ExpirationOptimizer(strategy_weights)
            
            # 执行优化（启用详细过程）
            optimal, optimization_process = optimizer.find_optimal_expiration(
                formatted_expirations,
                symbol=symbol,
                volatility=volatility,
                strategy_type=strategy_type,
                return_process=True
            )
            
            # 生成对比分析（传递symbol）
            comparison = self._generate_comparison(
                formatted_expirations,
                optimal,
                optimizer,
                volatility,
                symbol  # ✅ 传递symbol启用股票特定优化
            )
            
            # 构建返回结果
            result = {
                'success': True,
                'symbol': symbol,
                'strategy_type': strategy_type,
                'optimal_expiration': {
                    'date': optimal.date,
                    'days_to_expiry': optimal.days_to_expiry,
                    'type': optimal.type,
                    'composite_score': round(optimal.composite_score, 2),
                    'selection_reason': optimal.selection_reason
                },
                'score_details': {
                    'theta_efficiency': round(optimal.theta_efficiency, 2),
                    'gamma_risk_control': round(optimal.gamma_risk, 2),
                    'liquidity_score': round(optimal.liquidity_score, 2),
                    'composite_score': round(optimal.composite_score, 2)
                },
                'top_3_candidates': comparison['top_3'],
                'analysis': {
                    'total_candidates': len(formatted_expirations),
                    'optimal_days': optimal.days_to_expiry,
                    'improvement_vs_random': self._calculate_improvement(comparison),
                    'weights_used': optimizer.weights
                },
                'recommendation': self._generate_recommendation(optimal, strategy_type),

                # 新增：完整优化过程
                'optimization_process': optimization_process,

                'timestamp': datetime.now().isoformat()
            }

            return result
            
        except Exception as e:
            logger.error(f"到期日优化失败: {str(e)}", exc_info=True)
            return self._error_response(f"优化失败: {str(e)}")
    
    def _get_strategy_weights(self, strategy_type: str) -> Dict[str, float]:
        """
        根据策略类型返回优化的权重配置
        
        不同策略有不同的优先级：
        - CSP（现金担保看跌）：重视Theta效率和流动性
        - Covered Call（备兑看涨）：重视Gamma风险控制
        - Credit Spread：平衡各因素
        """
        weights_map = {
            'csp': {
                'theta_efficiency': 0.40,  # CSP重视时间衰减
                'gamma_risk': 0.20,
                'liquidity': 0.30,         # 需要好的流动性
                'event_buffer': 0.10
            },
            'covered_call': {
                'theta_efficiency': 0.30,
                'gamma_risk': 0.35,        # 备兑更关注风险
                'liquidity': 0.25,
                'event_buffer': 0.10
            },
            'credit_spread': {
                'theta_efficiency': 0.35,
                'gamma_risk': 0.25,
                'liquidity': 0.25,
                'event_buffer': 0.15
            },
            'default': {
                'theta_efficiency': 0.35,
                'gamma_risk': 0.25,
                'liquidity': 0.25,
                'event_buffer': 0.15
            }
        }
        
        return weights_map.get(strategy_type.lower(), weights_map['default'])
    
    def _format_expirations(self, expirations: List[Any]) -> List[Dict[str, Any]]:
        """
        格式化到期日数据

        支持多种输入格式：
        - 字符串列表: ['2025-10-31', '2025-11-07', ...]
        - 字典列表: [{'date': '2025-10-31', 'type': 'monthly'}, ...]
        - 混合格式
        """
        formatted = []

        # 修复: 在循环外固定时间基准,避免不一致
        now = datetime.now()

        for exp in expirations:
            if isinstance(exp, str):
                # 字符串格式，计算天数和类型
                try:
                    exp_date = datetime.strptime(exp, "%Y-%m-%d")
                    days = (exp_date - now).days
                except ValueError as e:
                    logger.error(f"无效的日期格式 '{exp}': {e}")
                    continue  # 跳过无效日期
                
                # 判断到期类型
                if exp_date.day >= 28 or exp_date.day <= 3:
                    exp_type = 'monthly'
                elif exp_date.weekday() == 4:  # 周五
                    exp_type = 'weekly'
                else:
                    exp_type = 'other'
                
                formatted.append({
                    'date': exp,
                    'days': days,
                    'type': exp_type
                })
                
            elif isinstance(exp, dict):
                # 字典格式，确保有必需字段
                if 'date' in exp:
                    if 'days' not in exp:
                        try:
                            exp_date = datetime.strptime(exp['date'], "%Y-%m-%d")
                            exp['days'] = (exp_date - now).days
                        except ValueError as e:
                            logger.error(f"无效的日期格式 '{exp.get('date')}': {e}")
                            continue  # 跳过无效日期
                    if 'type' not in exp:
                        exp['type'] = 'other'
                    formatted.append(exp)
        
        return formatted
    
    def _fetch_available_expirations(self, symbol: str) -> Optional[List[str]]:
        """
        从Tradier获取可用到期日

        注意: 此方法是同步的,因为TradierClient是同步实现。
        虽然父方法execute()是async(MCP要求),但内部可以安全地调用同步方法。
        """
        if not self.tradier_client:
            # 如果没有客户端，返回None让调用方处理
            logger.warning(f"无Tradier客户端，无法获取{symbol}的到期日数据")
            return None

        try:
            # 实际调用Tradier API（同步方法）
            response = self.tradier_client.get_option_expirations(symbol)
            if response:
                # response是List[OptionExpiration]对象列表
                return [exp.date for exp in response]
        except Exception as e:
            logger.error(f"获取到期日失败: {e}")

        return None
    
    def _generate_comparison(self,
                            all_expirations: List[Dict],
                            optimal: ExpirationCandidate,
                            optimizer: ExpirationOptimizer,
                            volatility: float,
                            symbol: str = "") -> Dict[str, Any]:
        """
        生成到期日对比分析（支持股票特定优化）

        Args:
            all_expirations: 所有到期日列表
            optimal: 最优候选
            optimizer: 优化器实例
            volatility: 波动率
            symbol: 股票代码（用于股票特定优化）
        """
        # 评估所有候选（传递symbol启用股票特定优化）
        all_candidates = []
        for exp in all_expirations:
            candidate = optimizer.evaluate_expiration(
                days=exp['days'],
                expiration_type=exp.get('type', 'other'),
                date=exp.get('date'),  # 传递原始日期字符串
                volatility=volatility,
                symbol=symbol  # ✅ 传递symbol
            )
            all_candidates.append(candidate)

        # 排序
        all_candidates.sort(key=lambda x: x.composite_score, reverse=True)

        # 返回前3名
        top_3 = []
        for i, candidate in enumerate(all_candidates[:3]):
            top_3.append({
                'rank': i + 1,
                'date': candidate.date,
                'days': candidate.days_to_expiry,
                'score': round(candidate.composite_score, 2),
                'reason': candidate.selection_reason
            })

        return {
            'top_3': top_3,
            'all_candidates': all_candidates
        }
    
    def _calculate_improvement(self, comparison: Dict) -> str:
        """
        计算相对于随机选择的改进
        """
        all_scores = [c.composite_score for c in comparison['all_candidates']]
        if not all_scores:
            return "N/A"
        
        best_score = all_scores[0]
        avg_score = sum(all_scores) / len(all_scores)
        
        if avg_score > 0:
            improvement = ((best_score - avg_score) / avg_score) * 100
            return f"{improvement:.1f}%"
        
        return "N/A"
    
    def _generate_recommendation(self, optimal: ExpirationCandidate, strategy_type: str) -> str:
        """
        生成具体的操作建议
        """
        recommendations = []
        
        # 基于天数的建议
        if optimal.days_to_expiry < 21:
            recommendations.append("⚠️ 注意：到期时间较短，Gamma风险较高，建议密切监控Delta变化")
        elif optimal.days_to_expiry > 45:
            recommendations.append("📊 到期时间较长，Theta衰减较慢，适合追求稳定的投资者")
        else:
            recommendations.append("✅ 到期时间处于最优区间(21-45天)，Theta效率和风险平衡良好")
        
        # 基于策略类型的建议
        if strategy_type.lower() == 'csp':
            recommendations.append("💡 CSP策略建议：选择略低于当前价格的执行价，Delta在-0.3到-0.4之间")
        elif strategy_type.lower() == 'covered_call':
            recommendations.append("💡 备兑策略建议：选择略高于当前价格的执行价，Delta在0.3到0.4之间")
        
        # 基于流动性的建议
        if optimal.liquidity_score > 85:
            recommendations.append("💧 流动性优秀，适合大资金操作")
        elif optimal.liquidity_score < 60:
            recommendations.append("⚠️ 流动性一般，建议使用限价单并耐心等待成交")
        
        return " | ".join(recommendations)
    
    def _error_response(self, message: str) -> Dict[str, Any]:
        """生成错误响应"""
        return {
            'success': False,
            'error': message,
            'timestamp': datetime.now().isoformat()
        }