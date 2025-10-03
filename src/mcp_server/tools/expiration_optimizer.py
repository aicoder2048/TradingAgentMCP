"""
智能期权到期日选择器
Intelligent Option Expiration Optimizer

基于客观数学指标优化期权到期日选择，避免主观硬编码
支持批量处理和缓存优化
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExpirationCandidate:
    """到期日候选对象"""
    date: str  # YYYY-MM-DD格式
    days_to_expiry: int
    type: str  # 'weekly', 'monthly', 'quarterly'
    theta_efficiency: float  # Theta衰减效率评分
    gamma_risk: float  # Gamma风险评分
    liquidity_score: float  # 流动性评分
    composite_score: float  # 综合评分
    selection_reason: str  # 选择理由


class ExpirationOptimizer:
    """
    智能到期日优化器
    
    核心原理：
    1. Theta效率：30-45天是期权时间价值衰减的甜蜜点
    2. Gamma风险：<21天Gamma风险急剧上升，>60天资金效率下降
    3. 流动性：周期权和月期权通常有最佳流动性
    4. 事件风险：避开财报等重大事件
    """
    
    # 最优参数（基于期权理论和实证研究）
    OPTIMAL_THETA_RANGE = (25, 45)  # Theta效率最高的天数范围
    HIGH_GAMMA_THRESHOLD = 21  # Gamma风险开始急剧上升的阈值
    MAX_EFFICIENT_DAYS = 60  # 资金效率开始显著下降的天数
    
    # 权重配置（可根据策略类型调整）
    DEFAULT_WEIGHTS = {
        'theta_efficiency': 0.35,
        'gamma_risk': 0.25,
        'liquidity': 0.25,
        'event_buffer': 0.15
    }

    # 股票市场档案 - Phase 1静态映射表（技术债：Phase 4后迁移到实时API）
    # 高波动科技股
    HIGH_VOLATILITY_TECH = {
        'TSLA': {'volatility_ratio': 1.30, 'beta': 1.40, 'liquidity': 1.20, 'market_cap_tier': 1.0, 'options_activity': 0.8},
        'NVDA': {'volatility_ratio': 1.25, 'beta': 1.35, 'liquidity': 1.30, 'market_cap_tier': 1.5, 'options_activity': 0.9},
        'AMD': {'volatility_ratio': 1.28, 'beta': 1.45, 'liquidity': 1.10, 'market_cap_tier': 1.0, 'options_activity': 0.7},
        'PLTR': {'volatility_ratio': 1.35, 'beta': 1.50, 'liquidity': 0.90, 'market_cap_tier': 0.7, 'options_activity': 0.6},
    }

    # 大盘蓝筹股
    LARGE_CAP_BLUE_CHIP = {
        'AAPL': {'volatility_ratio': 0.95, 'beta': 1.05, 'liquidity': 1.50, 'market_cap_tier': 1.5, 'options_activity': 0.9},
        'MSFT': {'volatility_ratio': 0.90, 'beta': 0.95, 'liquidity': 1.40, 'market_cap_tier': 1.5, 'options_activity': 0.8},
        'GOOG': {'volatility_ratio': 1.00, 'beta': 1.10, 'liquidity': 1.35, 'market_cap_tier': 1.5, 'options_activity': 0.7},
        'AMZN': {'volatility_ratio': 1.05, 'beta': 1.15, 'liquidity': 1.30, 'market_cap_tier': 1.5, 'options_activity': 0.8},
    }

    # 高Beta波动股
    HIGH_BETA_STOCKS = {
        'GME': {'volatility_ratio': 1.50, 'beta': 1.80, 'liquidity': 1.00, 'market_cap_tier': 0.7, 'options_activity': 0.9},
        'AMC': {'volatility_ratio': 1.45, 'beta': 1.75, 'liquidity': 0.95, 'market_cap_tier': 0.7, 'options_activity': 0.8},
    }

    # 稳健大盘股
    STABLE_LARGE_CAP = {
        'SPY': {'volatility_ratio': 0.85, 'beta': 1.00, 'liquidity': 1.60, 'market_cap_tier': 1.5, 'options_activity': 1.0},
        'QQQ': {'volatility_ratio': 0.95, 'beta': 1.10, 'liquidity': 1.55, 'market_cap_tier': 1.5, 'options_activity': 0.95},
        'DIA': {'volatility_ratio': 0.80, 'beta': 0.95, 'liquidity': 1.30, 'market_cap_tier': 1.5, 'options_activity': 0.7},
    }

    # 默认调整因子（用于未知股票或不提供symbol时）
    DEFAULT_ADJUSTMENTS = {
        'gamma_adjustment': 1.0,
        'theta_adjustment': 1.0,
        'liquidity_adjustment': 1.0,
        'income_adjustment': 1.0,
    }
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        初始化优化器
        
        Args:
            weights: 自定义权重配置
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
        self._validate_weights()
    
    def _validate_weights(self):
        """验证权重配置"""
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.001:
            # 自动归一化
            for key in self.weights:
                self.weights[key] /= total

    def _get_stock_market_profile(self, symbol: str) -> Dict[str, float]:
        """
        获取股票市场档案（客观市场特征）

        Phase 1实现：使用静态映射表
        Phase 4计划：迁移到实时API数据

        Args:
            symbol: 股票代码

        Returns:
            包含以下字段的字典:
            - volatility_ratio: IV/HV比值 (范围: 0.5-2.0)
            - liquidity: 流动性因子 (范围: 0.5-2.0)
            - market_cap_tier: 市值分级 (大盘1.5, 中盘1.0, 小盘0.7)
            - beta: Beta系数 (范围: 0.5-2.0)
            - options_activity: 期权活跃度 (范围: 0-1.0)
        """
        # 优先级查找：高波动科技股 -> 大盘蓝筹股 -> 高Beta股 -> 稳健大盘股
        if symbol in self.HIGH_VOLATILITY_TECH:
            return self.HIGH_VOLATILITY_TECH[symbol]
        elif symbol in self.LARGE_CAP_BLUE_CHIP:
            return self.LARGE_CAP_BLUE_CHIP[symbol]
        elif symbol in self.HIGH_BETA_STOCKS:
            return self.HIGH_BETA_STOCKS[symbol]
        elif symbol in self.STABLE_LARGE_CAP:
            return self.STABLE_LARGE_CAP[symbol]
        else:
            # 未知股票：返回中性档案
            logger.info(f"{symbol} 不在已知档案中，使用中性默认值")
            return {
                'volatility_ratio': 1.0,
                'beta': 1.0,
                'liquidity': 1.0,
                'market_cap_tier': 1.0,
                'options_activity': 0.5
            }

    def _calculate_dynamic_adjustments(self, market_profile: Dict[str, float]) -> Dict[str, float]:
        """
        基于股票市场档案计算动态调整因子（完全客观数学公式）

        Args:
            market_profile: 股票市场特征字典

        Returns:
            调整因子字典，包含:
            - gamma_adjustment: Gamma风险调整 (0.7-1.3)
            - theta_adjustment: Theta效率调整 (0.8-1.2)
            - liquidity_adjustment: 流动性调整 (0.8-1.3)
            - income_adjustment: 收入优化调整 (0.8-1.2)
        """
        vol_ratio = market_profile.get('volatility_ratio', 1.0)
        beta = market_profile.get('beta', 1.0)
        liquidity = market_profile.get('liquidity', 1.0)
        market_cap_tier = market_profile.get('market_cap_tier', 1.0)
        options_activity = market_profile.get('options_activity', 0.5)

        # 1. Gamma风险调整（高波动高Beta -> 更保守）
        # 公式: 0.8 + (vol_ratio - 1.0) * (-0.15) + (beta - 1.0) * (-0.10)
        # TSLA示例: 0.8 + (1.3-1.0)*(-0.15) + (1.4-1.0)*(-0.10) = 0.8 - 0.045 - 0.040 = 0.715
        gamma_adjustment = 0.8 + (vol_ratio - 1.0) * (-0.15) + (beta - 1.0) * (-0.10)
        gamma_adjustment = max(0.7, min(1.3, gamma_adjustment))  # 限制范围

        # 2. Theta效率调整（大盘股 -> 更灵活）
        # 公式: 0.9 + (market_cap_tier - 1.0) * 0.15 + (liquidity - 1.0) * 0.10
        # AAPL示例: 0.9 + (1.5-1.0)*0.15 + (1.5-1.0)*0.10 = 0.9 + 0.075 + 0.050 = 1.025
        theta_adjustment = 0.9 + (market_cap_tier - 1.0) * 0.15 + (liquidity - 1.0) * 0.10
        theta_adjustment = max(0.8, min(1.2, theta_adjustment))

        # 3. 流动性调整（高流动性 -> 更高评分）
        # 公式: 0.8 + liquidity * 0.15 + options_activity * 0.15
        liquidity_adjustment = 0.8 + liquidity * 0.15 + options_activity * 0.15
        liquidity_adjustment = max(0.8, min(1.3, liquidity_adjustment))

        # 4. 收入优化调整（高IV -> 更激进收入策略）
        # 公式: 0.9 + (vol_ratio - 1.0) * 0.20
        # 高IV意味着期权权利金更高，可以更激进
        income_adjustment = 0.9 + (vol_ratio - 1.0) * 0.20
        income_adjustment = max(0.8, min(1.2, income_adjustment))

        return {
            'gamma_adjustment': gamma_adjustment,
            'theta_adjustment': theta_adjustment,
            'liquidity_adjustment': liquidity_adjustment,
            'income_adjustment': income_adjustment,
        }
    
    def calculate_theta_efficiency(self, days: int, adjustment_factor: float = 1.0) -> float:
        """
        计算Theta衰减效率评分

        基于期权理论：Theta在30-45天达到最优平衡
        - 太短（<21天）：Theta绝对值大但Gamma风险高
        - 太长（>60天）：Theta效率低，资金占用时间长

        Args:
            days: 到期天数
            adjustment_factor: 调整因子（用于股票特定优化）

        Returns:
            0-100的效率评分
        """
        # 基础评分曲线（通用数学模型）
        if days < 7:
            base_score = 10.0  # 过短，风险太高
        elif days < 21:
            # 线性下降：从60分降到30分
            base_score = 30 + (days - 7) * 30 / 14
        elif days <= 30:
            # 快速上升：从60分升到95分
            base_score = 60 + (days - 21) * 35 / 9
        elif days <= 45:
            # 最优区间：95-100分
            base_score = 95 + (45 - days) * 5 / 15
        elif days <= 60:
            # 缓慢下降：从95分降到70分
            base_score = 95 - (days - 45) * 25 / 15
        else:
            # 继续下降
            base_score = max(40, 70 - (days - 60) * 0.5)

        # 应用股票特定调整因子
        return base_score * adjustment_factor
    
    def calculate_gamma_risk(self, days: int, volatility: float = 0.3, adjustment_factor: float = 1.0) -> float:
        """
        计算Gamma风险评分（越高越好）

        Gamma风险在接近到期时急剧上升

        Args:
            days: 到期天数
            volatility: 隐含波动率（用于调整风险曲线）
            adjustment_factor: 调整因子（用于股票特定优化）

        Returns:
            0-100的风险控制评分（高分表示风险可控）
        """
        # 基础评分曲线（基于Black-Scholes的Gamma特性）
        if days < 7:
            base_score = 20.0  # 极高Gamma风险
        elif days < 14:
            base_score = 20 + (days - 7) * 20 / 7
        elif days < 21:
            base_score = 40 + (days - 14) * 20 / 7
        elif days < 30:
            base_score = 60 + (days - 21) * 20 / 9
        else:
            # 30天以上Gamma风险较低且稳定
            base_score = 80
            # 根据波动率调整
            vol_adjustment = (0.3 - volatility) * 20  # 高波动率降低评分
            base_score = base_score + vol_adjustment + (days - 30) * 0.2

        # 应用股票特定调整因子，并限制在合理范围内
        adjusted_score = base_score * adjustment_factor
        return min(100, adjusted_score)
    
    def calculate_liquidity_score(self, expiration_type: str,
                                 days: int,
                                 volume: Optional[int] = None,
                                 open_interest: Optional[int] = None,
                                 adjustment_factor: float = 1.0) -> float:
        """
        计算流动性评分

        Args:
            expiration_type: 'weekly', 'monthly', 'quarterly'
            days: 到期天数
            volume: 交易量（可选）
            open_interest: 未平仓量（可选）
            adjustment_factor: 调整因子（用于股票特定优化）

        Returns:
            0-100的流动性评分
        """
        # 基础评分基于到期类型
        base_scores = {
            'weekly': 85,  # 周期权通常流动性好
            'eow': 85,     # 周末到期
            'monthly': 95,  # 月期权流动性最佳
            'eom': 95,      # 月末到期
            'quarterly': 75,  # 季度期权流动性一般
            'eoq': 75,      # 季末到期
            'other': 60     # 其他
        }

        base_score = base_scores.get(expiration_type.lower(), 60)

        # 根据到期天数调整
        if days < 7:
            # 太近的期权流动性可能变差
            base_score *= 0.7
        elif days > 90:
            # 太远的期权流动性较差
            base_score *= 0.8

        # 如果提供了实际交易数据，进一步调整
        if volume is not None and open_interest is not None:
            if open_interest > 0:
                turnover = volume / open_interest
                if turnover > 1.0:
                    base_score = min(100, base_score * 1.1)
                elif turnover < 0.1:
                    base_score *= 0.8

        # 应用股票特定调整因子
        adjusted_score = base_score * adjustment_factor
        return min(100, adjusted_score)
    
    def calculate_event_buffer_score(self, days: int, 
                                    next_earnings_days: Optional[int] = None) -> float:
        """
        计算事件缓冲评分
        
        Args:
            days: 到期天数
            next_earnings_days: 距离下次财报的天数
        
        Returns:
            0-100的事件缓冲评分
        """
        if next_earnings_days is None:
            # 没有财报信息，给基础分
            return 75
        
        if days < next_earnings_days - 5:
            # 在财报前到期，完美
            return 100
        elif days > next_earnings_days + 5:
            # 跨越财报，根据缓冲天数评分
            buffer = days - next_earnings_days
            if buffer > 10:
                return 90
            elif buffer > 5:
                return 70
            else:
                return 50
        else:
            # 太接近财报
            return 30
    
    def evaluate_expiration(self,
                           days: int,
                           expiration_type: str,
                           date: Optional[str] = None,
                           volatility: float = 0.3,
                           next_earnings_days: Optional[int] = None,
                           symbol: Optional[str] = None) -> ExpirationCandidate:
        """
        评估单个到期日（支持股票特定优化）

        Args:
            days: 到期天数
            expiration_type: 到期类型
            date: 到期日期 (YYYY-MM-DD格式, 可选)
            volatility: 隐含波动率
            next_earnings_days: 距离财报天数
            symbol: 股票代码（可选，用于股票特定优化）

        Returns:
            ExpirationCandidate对象
        """
        # 获取股票特定调整因子
        if symbol:
            market_profile = self._get_stock_market_profile(symbol)
            adjustments = self._calculate_dynamic_adjustments(market_profile)
        else:
            # 向后兼容：不提供symbol时使用默认调整因子（全部为1.0）
            adjustments = self.DEFAULT_ADJUSTMENTS
            market_profile = None

        # 计算各项指标（应用股票特定调整）
        theta_score = self.calculate_theta_efficiency(
            days,
            adjustment_factor=adjustments['theta_adjustment']
        )
        gamma_score = self.calculate_gamma_risk(
            days,
            volatility,
            adjustment_factor=adjustments['gamma_adjustment']
        )
        liquidity_score = self.calculate_liquidity_score(
            expiration_type,
            days,
            adjustment_factor=adjustments['liquidity_adjustment']
        )
        event_score = self.calculate_event_buffer_score(days, next_earnings_days)

        # 计算综合评分
        composite_score = (
            self.weights['theta_efficiency'] * theta_score +
            self.weights['gamma_risk'] * gamma_score +
            self.weights['liquidity'] * liquidity_score +
            self.weights['event_buffer'] * event_score
        )

        # 生成选择理由（包含股票特定信息）
        reasons = []
        
        # 添加股票特定调整说明
        if symbol and market_profile:
            vol_ratio = market_profile.get('volatility_ratio', 1.0)
            beta = market_profile.get('beta', 1.0)
            
            if vol_ratio > 1.15:
                reasons.append(f"{symbol}高波动(IV/HV={vol_ratio:.2f})")
            elif vol_ratio < 0.90:
                reasons.append(f"{symbol}低波动(IV/HV={vol_ratio:.2f})")
            
            if beta > 1.25:
                reasons.append(f"高Beta({beta:.2f})")
            elif beta < 0.85:
                reasons.append(f"低Beta({beta:.2f})")

        # 添加评分说明
        if theta_score > 90:
            reasons.append(f"Theta效率极佳({theta_score:.0f}/100)")
        if gamma_score > 80:
            reasons.append(f"Gamma风险可控({gamma_score:.0f}/100)")
        if liquidity_score > 85:
            reasons.append(f"流动性优秀({liquidity_score:.0f}/100)")
        if event_score > 90:
            reasons.append("完美避开财报事件")

        if not reasons:
            reasons.append(f"综合评分{composite_score:.1f}/100")

        # 使用提供的日期，如果没有则根据天数计算
        if date:
            expiration_date = date
        else:
            expiration_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

        return ExpirationCandidate(
            date=expiration_date,
            days_to_expiry=days,
            type=expiration_type,
            theta_efficiency=theta_score,
            gamma_risk=gamma_score,
            liquidity_score=liquidity_score,
            composite_score=composite_score,
            selection_reason="; ".join(reasons)
        )
    
    def find_optimal_expiration(self,
                               available_expirations: List[Dict[str, Any]],
                               symbol: str = "",
                               volatility: float = 0.3,
                               strategy_type: str = "csp",
                               return_process: bool = False) -> Tuple[ExpirationCandidate, Optional[Dict[str, Any]]]:
        """
        从可用到期日中找出最优选择（支持股票特定优化）

        Args:
            available_expirations: 可用到期日列表
            symbol: 股票代码（用于股票特定优化和日志）
            volatility: 当前隐含波动率
            strategy_type: 策略类型（csp, covered_call等）
            return_process: 是否返回完整优化过程

        Returns:
            如果return_process=False: 最优到期日
            如果return_process=True: (最优到期日, 优化过程详情)
        """
        candidates = []

        # 获取股票市场档案（用于优化过程跟踪）
        market_profile = None
        adjustments = None
        if symbol:
            market_profile = self._get_stock_market_profile(symbol)
            adjustments = self._calculate_dynamic_adjustments(market_profile)

        for exp in available_expirations:
            candidate = self.evaluate_expiration(
                days=exp['days'],
                expiration_type=exp.get('type', 'other'),
                date=exp.get('date'),  # 传递原始日期字符串
                volatility=volatility,
                next_earnings_days=exp.get('next_earnings_days'),
                symbol=symbol  # ✅ 传递symbol启用股票特定优化
            )
            candidates.append(candidate)

        # 排序并选择最优
        candidates.sort(key=lambda x: x.composite_score, reverse=True)

        best = candidates[0]

        # 记录决策
        logger.info(f"{symbol} 最优到期日: {best.date} ({best.days_to_expiry}天), "
                   f"评分: {best.composite_score:.1f}, 理由: {best.selection_reason}")

        # 如果需要返回优化过程
        if return_process:
            process_details = self._generate_optimization_process(
                candidates, best, symbol, market_profile, adjustments
            )
            return best, process_details

        return best, None

    def _generate_optimization_process(self,
                                      all_candidates: List[ExpirationCandidate],
                                      selected: ExpirationCandidate,
                                      symbol: str = "",
                                      market_profile: Optional[Dict[str, float]] = None,
                                      adjustments: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        生成优化过程详情（增强：包含股票特定优化信息）

        Args:
            all_candidates: 所有候选（已排序）
            selected: 最终选择
            symbol: 股票代码
            market_profile: 股票市场档案（可选）
            adjustments: 动态调整因子（可选）

        Returns:
            优化过程详情字典
        """
        # 1. 候选总数
        total_candidates = len(all_candidates)

        # 2. 筛选标准
        screening_criteria = {
            "权重配置": self.weights,
            "Theta最优区间": f"{self.OPTIMAL_THETA_RANGE[0]}-{self.OPTIMAL_THETA_RANGE[1]}天",
            "Gamma风险阈值": f"<{self.HIGH_GAMMA_THRESHOLD}天为高风险区",
            "资金效率上限": f">{self.MAX_EFFICIENT_DAYS}天效率下降"
        }

        # 3. 所有候选的评分详情（按评分降序）
        all_evaluations = []
        for i, candidate in enumerate(all_candidates):
            all_evaluations.append({
                "排名": i + 1,
                "日期": candidate.date,
                "天数": candidate.days_to_expiry,
                "类型": candidate.type,
                "综合评分": round(candidate.composite_score, 2),
                "Theta效率": round(candidate.theta_efficiency, 2),
                "Gamma风险控制": round(candidate.gamma_risk, 2),
                "流动性": round(candidate.liquidity_score, 2),
                "是否最优": (candidate.date == selected.date)
            })

        # 4. 淘汰分析 - 为什么其他候选被淘汰
        rejections = []
        for candidate in all_candidates[1:]:  # 跳过第一个（已选择）
            reasons = []

            # 评分差距
            score_gap = selected.composite_score - candidate.composite_score
            if score_gap > 10:
                reasons.append(f"综合评分低{score_gap:.1f}分")
            elif score_gap > 5:
                reasons.append(f"综合评分略低{score_gap:.1f}分")

            # Theta效率对比
            theta_gap = selected.theta_efficiency - candidate.theta_efficiency
            if theta_gap > 15:
                reasons.append(f"Theta效率差距大({theta_gap:.1f}分)")

            # Gamma风险对比
            if candidate.days_to_expiry < self.HIGH_GAMMA_THRESHOLD:
                reasons.append(f"Gamma风险过高({candidate.days_to_expiry}天<{self.HIGH_GAMMA_THRESHOLD}天阈值)")

            # 流动性对比
            liquidity_gap = selected.liquidity_score - candidate.liquidity_score
            if liquidity_gap > 20:
                reasons.append(f"流动性显著偏低({liquidity_gap:.1f}分)")

            # 天数不在最优区间
            if not (self.OPTIMAL_THETA_RANGE[0] <= candidate.days_to_expiry <= self.OPTIMAL_THETA_RANGE[1]):
                if candidate.days_to_expiry < self.OPTIMAL_THETA_RANGE[0]:
                    reasons.append(f"天数偏短({candidate.days_to_expiry}天<{self.OPTIMAL_THETA_RANGE[0]}天)")
                else:
                    reasons.append(f"天数偏长({candidate.days_to_expiry}天>{self.OPTIMAL_THETA_RANGE[1]}天)")

            if not reasons:
                reasons.append("综合评分略低于最优选择")

            rejections.append({
                "日期": candidate.date,
                "天数": candidate.days_to_expiry,
                "评分": round(candidate.composite_score, 2),
                "淘汰原因": "; ".join(reasons)
            })

        # 5. 最终选择的详细理由
        selection_details = {
            "选中日期": selected.date,
            "到期天数": selected.days_to_expiry,
            "到期类型": selected.type,
            "综合评分": round(selected.composite_score, 2),
            "选择理由": selected.selection_reason,
            "优势分析": []
        }

        # 分析为什么这个是最优的
        if selected.theta_efficiency > 90:
            selection_details["优势分析"].append(
                f"✓ Theta效率极佳({selected.theta_efficiency:.1f}/100)，时间衰减收益最大化"
            )
        if selected.gamma_risk > 80:
            selection_details["优势分析"].append(
                f"✓ Gamma风险可控({selected.gamma_risk:.1f}/100)，Delta稳定性好"
            )
        if selected.liquidity_score > 85:
            selection_details["优势分析"].append(
                f"✓ 流动性优秀({selected.liquidity_score:.1f}/100)，{selected.type}期权成交活跃"
            )
        if self.OPTIMAL_THETA_RANGE[0] <= selected.days_to_expiry <= self.OPTIMAL_THETA_RANGE[1]:
            selection_details["优势分析"].append(
                f"✓ 天数处于最优区间({self.OPTIMAL_THETA_RANGE[0]}-{self.OPTIMAL_THETA_RANGE[1]}天)"
            )

        # 6. 构建完整过程
        process = {
            "symbol": symbol,
            "总候选数": total_candidates,
            "筛选标准": screening_criteria,
            "所有候选评估": all_evaluations,
            "候选淘汰分析": rejections[:5],  # 只显示前5个被淘汰的
            "最终选择详情": selection_details,
            "评分方法说明": {
                "Theta效率": f"基于期权时间衰减理论，{self.OPTIMAL_THETA_RANGE[0]}-{self.OPTIMAL_THETA_RANGE[1]}天为最优平衡点",
                "Gamma风险": f"到期时间<{self.HIGH_GAMMA_THRESHOLD}天时Gamma急剧上升，Delta波动加大",
                "流动性": "周期权和月期权通常流动性最佳，便于进出场",
                "综合评分": f"加权计算: Theta{self.weights['theta_efficiency']:.0%} + Gamma{self.weights['gamma_risk']:.0%} + 流动性{self.weights['liquidity']:.0%} + 事件缓冲{self.weights['event_buffer']:.0%}"
            }
        }

        # 7. 添加股票特定优化信息（如果可用）
        if market_profile and adjustments:
            process["market_profile"] = {
                "波动率比值": round(market_profile.get('volatility_ratio', 1.0), 2),
                "Beta系数": round(market_profile.get('beta', 1.0), 2),
                "流动性因子": round(market_profile.get('liquidity', 1.0), 2),
                "市值分级": round(market_profile.get('market_cap_tier', 1.0), 2),
                "期权活跃度": round(market_profile.get('options_activity', 0.5), 2)
            }
            process["dynamic_adjustments"] = {
                "Gamma调整": round(adjustments.get('gamma_adjustment', 1.0), 3),
                "Theta调整": round(adjustments.get('theta_adjustment', 1.0), 3),
                "流动性调整": round(adjustments.get('liquidity_adjustment', 1.0), 3),
                "收入调整": round(adjustments.get('income_adjustment', 1.0), 3)
            }
            
            # 添加调整推理
            adjustment_reasoning = []
            vol_ratio = market_profile.get('volatility_ratio', 1.0)
            beta = market_profile.get('beta', 1.0)
            
            if vol_ratio > 1.15:
                adjustment_reasoning.append(f"高波动率(IV/HV={vol_ratio:.2f}) → Gamma风险评分降低{(1-adjustments['gamma_adjustment'])*100:.1f}%")
            if beta > 1.25:
                adjustment_reasoning.append(f"高Beta({beta:.2f}) → Gamma风险更保守")
            if market_profile.get('market_cap_tier', 1.0) >= 1.5:
                adjustment_reasoning.append("大盘股 → Theta效率评分提升")
            if market_profile.get('liquidity', 1.0) >= 1.3:
                adjustment_reasoning.append("高流动性 → 流动性评分加成")
                
            if adjustment_reasoning:
                process["adjustment_reasoning"] = adjustment_reasoning

        return process
    
    def batch_optimize(self,
                       symbols_data: Dict[str, List[Dict[str, Any]]],
                       volatilities: Optional[Dict[str, float]] = None) -> Dict[str, ExpirationCandidate]:
        """
        批量优化多个股票的到期日选择

        Args:
            symbols_data: {symbol: [expiration_list]}
            volatilities: {symbol: volatility}

        Returns:
            {symbol: optimal_expiration}
        """
        results = {}
        default_vol = 0.3

        for symbol, expirations in symbols_data.items():
            vol = volatilities.get(symbol, default_vol) if volatilities else default_vol
            # Note: batch_optimize doesn't need process details, so return_process=False
            optimal, _ = self.find_optimal_expiration(
                expirations,
                symbol=symbol,
                volatility=vol,
                return_process=False
            )
            results[symbol] = optimal

        return results
    
    def generate_report(self, optimization_results: Dict[str, ExpirationCandidate]) -> str:
        """
        生成优化报告
        
        Args:
            optimization_results: 优化结果
        
        Returns:
            格式化的报告字符串
        """
        report_lines = [
            "=" * 80,
            "期权到期日智能优化报告",
            "=" * 80,
            ""
        ]
        
        for symbol, result in optimization_results.items():
            report_lines.extend([
                f"【{symbol}】",
                f"  最优到期日: {result.date} ({result.days_to_expiry}天)",
                f"  到期类型: {result.type}",
                f"  综合评分: {result.composite_score:.1f}/100",
                f"  - Theta效率: {result.theta_efficiency:.1f}/100",
                f"  - Gamma风险控制: {result.gamma_risk:.1f}/100",
                f"  - 流动性: {result.liquidity_score:.1f}/100",
                f"  选择理由: {result.selection_reason}",
                ""
            ])
        
        report_lines.extend([
            "=" * 80,
            "优化说明：",
            "- 基于期权理论和数学模型的客观选择",
            "- 避免了主观硬编码的21-60天限制",
            "- 动态适应不同市场条件和股票特性",
            "=" * 80
        ])
        
        return "\n".join(report_lines)


# 便捷函数
def optimize_expiration_for_symbol(symbol: str,
                                  available_expirations: List[Dict],
                                  volatility: float = 0.3,
                                  weights: Optional[Dict] = None) -> Dict[str, Any]:
    """
    为单个股票优化到期日选择

    Args:
        symbol: 股票代码
        available_expirations: 可用到期日列表
        volatility: 隐含波动率
        weights: 自定义权重

    Returns:
        优化结果字典
    """
    optimizer = ExpirationOptimizer(weights)
    # Convenience function doesn't need process details
    result, _ = optimizer.find_optimal_expiration(
        available_expirations,
        symbol=symbol,
        volatility=volatility,
        return_process=False
    )

    return {
        'symbol': symbol,
        'optimal_expiration': result.date,
        'days_to_expiry': result.days_to_expiry,
        'score': result.composite_score,
        'reason': result.selection_reason,
        'details': {
            'theta_efficiency': result.theta_efficiency,
            'gamma_risk': result.gamma_risk,
            'liquidity_score': result.liquidity_score
        }
    }