"""
期权到期日选择器模块

提供智能的期权到期日选择功能，包括：
- 基于持续时间的到期日映射
- 流动性优化选择
- 周度/月度期权偏好
- 特殊事件避让（财报、分红等）
- 交易日历处理
"""

import math
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..provider.tradier.client import TradierClient, OptionExpiration


class ExpirationPreference(Enum):
    """到期日偏好类型"""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    LEAPS = "leaps"
    ANY = "any"


@dataclass
class ExpirationCandidate:
    """到期日候选者数据类"""
    date: str
    days_to_expiry: int
    expiration_type: str
    is_weekly: bool
    is_monthly: bool
    is_quarterly: bool
    liquidity_score: float
    distance_score: float  # 与目标天数的距离评分
    final_score: float
    special_events: List[str]  # 特殊事件（财报、分红等）


@dataclass
class ExpirationSelectionResult:
    """到期日选择结果"""
    selected_date: str
    selection_reason: str
    metadata: Dict[str, Any]
    alternatives: List[ExpirationCandidate]


# 持续时间映射配置
DURATION_MAPPINGS = {
        "1w": {
            "min_days": 5, 
            "max_days": 9, 
            "target_days": 7,
            "preferred": ExpirationPreference.WEEKLY,
            "description": "1周期权策略"
        },
        "2w": {
            "min_days": 10, 
            "max_days": 18, 
            "target_days": 14,
            "preferred": ExpirationPreference.WEEKLY,
            "description": "2周期权策略"
        },
        "1m": {
            "min_days": 25, 
            "max_days": 35, 
            "target_days": 30,
            "preferred": ExpirationPreference.MONTHLY,
            "description": "1月期权策略"
        },
        "3m": {
            "min_days": 80, 
            "max_days": 100, 
            "target_days": 90,
            "preferred": ExpirationPreference.MONTHLY,
            "description": "3月期权策略"
        },
        "6m": {
            "min_days": 170, 
            "max_days": 190, 
            "target_days": 180,
            "preferred": ExpirationPreference.QUARTERLY,
            "description": "6月期权策略"
        },
        "1y": {
            "min_days": 350, 
            "max_days": 380, 
            "target_days": 365,
            "preferred": ExpirationPreference.LEAPS,
            "description": "1年期权策略(LEAPS)"
        }
    }


class ExpirationSelector:
    """智能期权到期日选择器"""
    
    def __init__(
        self,
        tradier_client: Optional[TradierClient] = None,
        prefer_high_liquidity: bool = True,
        avoid_earnings: bool = True,
        avoid_dividends: bool = False
    ):
        self.client = tradier_client or TradierClient()
        self.prefer_high_liquidity = prefer_high_liquidity
        self.avoid_earnings = avoid_earnings
        self.avoid_dividends = avoid_dividends
        
        # 权重配置
        self.liquidity_weight = 0.4
        self.distance_weight = 0.4
        self.preference_weight = 0.2
    
    async def get_optimal_expiration(
        self,
        symbol: str,
        duration: str,
        preference_override: Optional[ExpirationPreference] = None
    ) -> ExpirationSelectionResult:
        """
        获取最优期权到期日
        
        Args:
            symbol: 股票代码
            duration: 持续时间 ("1w", "2w", "1m", "3m", "6m", "1y")
            preference_override: 偏好覆盖 (可选)
            
        Returns:
            到期日选择结果
        """
        if duration not in DURATION_MAPPINGS:
            raise ValueError(f"不支持的持续时间: {duration}")
        
        mapping = DURATION_MAPPINGS[duration]
        preference = preference_override or mapping["preferred"]
        
        # 获取所有可用到期日
        expirations = self.client.get_option_expirations(
            symbol, 
            include_all_roots=True, 
            include_strikes=False,
            include_details=True
        )
        
        # 生成候选者
        candidates = await self._generate_candidates(
            symbol, expirations, mapping, preference
        )
        
        if not candidates:
            raise ValueError(f"未找到符合{duration}要求的期权到期日")
        
        # 选择最优候选者
        best_candidate = max(candidates, key=lambda x: x.final_score)
        
        # 生成选择理由
        reason = self._generate_selection_reason(best_candidate, mapping, preference)
        
        # 准备元数据
        metadata = {
            "duration": duration,
            "target_days": mapping["target_days"],
            "actual_days": best_candidate.days_to_expiry,
            "expiration_type": best_candidate.expiration_type,
            "liquidity_score": best_candidate.liquidity_score,
            "preference_used": preference.value,
            "total_candidates": len(candidates)
        }
        
        return ExpirationSelectionResult(
            selected_date=best_candidate.date,
            selection_reason=reason,
            metadata=metadata,
            alternatives=sorted(candidates, key=lambda x: x.final_score, reverse=True)[1:6]
        )
    
    async def _generate_candidates(
        self,
        symbol: str,
        expirations: List[OptionExpiration],
        mapping: Dict[str, Any],
        preference: ExpirationPreference
    ) -> List[ExpirationCandidate]:
        """生成到期日候选者列表"""
        
        today = datetime.now().date()
        min_days = mapping["min_days"]
        max_days = mapping["max_days"]
        target_days = mapping["target_days"]
        
        candidates = []
        
        for exp in expirations:
            exp_date = datetime.strptime(exp.date, "%Y-%m-%d").date()
            days_to_expiry = (exp_date - today).days
            
            # 检查天数范围
            if not (min_days <= days_to_expiry <= max_days):
                continue
            
            # 分类期权类型
            is_weekly = self._is_weekly_expiration(exp_date)
            is_monthly = self._is_monthly_expiration(exp_date)
            is_quarterly = self._is_quarterly_expiration(exp_date)
            
            # 计算流动性评分
            liquidity_score = await self._calculate_liquidity_score(symbol, exp.date)
            
            # 计算距离评分
            distance_score = self._calculate_distance_score(days_to_expiry, target_days)
            
            # 检查特殊事件
            special_events = await self._check_special_events(symbol, exp_date)
            
            # 计算最终评分
            final_score = self._calculate_final_score(
                liquidity_score, distance_score, 
                is_weekly, is_monthly, is_quarterly,
                preference, special_events
            )
            
            candidate = ExpirationCandidate(
                date=exp.date,
                days_to_expiry=days_to_expiry,
                expiration_type=exp.expiration_type,
                is_weekly=is_weekly,
                is_monthly=is_monthly,
                is_quarterly=is_quarterly,
                liquidity_score=liquidity_score,
                distance_score=distance_score,
                final_score=final_score,
                special_events=special_events
            )
            candidates.append(candidate)
        
        return candidates
    
    def _is_weekly_expiration(self, exp_date: date) -> bool:
        """判断是否为周度期权到期日"""
        # 周度期权通常在周五到期，且不是第三个周五
        if exp_date.weekday() != 4:  # 不是周五
            return False
        
        third_friday = self._get_third_friday(exp_date.year, exp_date.month)
        return exp_date != third_friday
    
    def _is_monthly_expiration(self, exp_date: date) -> bool:
        """判断是否为月度期权到期日"""
        # 月度期权在第三个周五到期
        if exp_date.weekday() != 4:  # 不是周五
            return False
        
        third_friday = self._get_third_friday(exp_date.year, exp_date.month)
        return exp_date == third_friday
    
    def _is_quarterly_expiration(self, exp_date: date) -> bool:
        """判断是否为季度期权到期日"""
        # 季度期权在3、6、9、12月的第三个周五到期
        if not self._is_monthly_expiration(exp_date):
            return False
        
        return exp_date.month in [3, 6, 9, 12]
    
    async def _calculate_liquidity_score(self, symbol: str, expiration: str) -> float:
        """计算流动性评分 (0-100)"""
        try:
            liquidity_metrics = self.client.get_option_liquidity_metrics(symbol, expiration)
            return liquidity_metrics.get("liquidity_score", 50.0)
        except Exception:
            # 如果无法获取流动性数据，返回中等评分
            return 50.0
    
    def _calculate_distance_score(self, actual_days: int, target_days: int) -> float:
        """计算距离评分 (0-100)"""
        # 距离目标天数越近，评分越高
        max_distance = max(abs(actual_days - target_days), 1)
        distance_ratio = abs(actual_days - target_days) / target_days
        
        # 使用指数衰减函数
        score = 100 * math.exp(-2 * distance_ratio)
        return max(0, min(100, score))
    
    async def _check_special_events(self, symbol: str, exp_date: date) -> List[str]:
        """检查特殊事件（财报、分红等）"""
        events = []
        
        # 简化实现 - 在实际应用中应该调用财报日历API
        # 这里使用估算方法
        
        # 检查财报季度（通常在季度末月份）
        if exp_date.month in [1, 4, 7, 10]:  # 财报月份
            week_of_month = (exp_date.day - 1) // 7 + 1
            if week_of_month <= 3:  # 前三周通常是财报密集期
                events.append("earnings_season")
        
        # 检查期权到期日当周（通常波动较大）
        if exp_date.weekday() == 4:  # 周五
            events.append("expiration_week")
        
        return events
    
    def _calculate_final_score(
        self,
        liquidity_score: float,
        distance_score: float,
        is_weekly: bool,
        is_monthly: bool,
        is_quarterly: bool,
        preference: ExpirationPreference,
        special_events: List[str]
    ) -> float:
        """计算最终评分"""
        
        # 基础评分
        base_score = (
            liquidity_score * self.liquidity_weight +
            distance_score * self.distance_weight
        )
        
        # 偏好加成
        preference_bonus = 0
        if preference == ExpirationPreference.WEEKLY and is_weekly:
            preference_bonus = 20
        elif preference == ExpirationPreference.MONTHLY and is_monthly:
            preference_bonus = 20
        elif preference == ExpirationPreference.QUARTERLY and is_quarterly:
            preference_bonus = 25
        elif preference == ExpirationPreference.LEAPS:
            preference_bonus = 15  # LEAPS通常流动性较低，给较少加成
        
        preference_score = preference_bonus * self.preference_weight
        
        # 特殊事件惩罚
        event_penalty = 0
        for event in special_events:
            if event == "earnings_season" and self.avoid_earnings:
                event_penalty += 15
            elif event == "expiration_week":
                event_penalty += 5  # 轻微惩罚
        
        final_score = base_score + preference_score - event_penalty
        return max(0, min(100, final_score))
    
    def _generate_selection_reason(
        self,
        candidate: ExpirationCandidate,
        mapping: Dict[str, Any],
        preference: ExpirationPreference
    ) -> str:
        """生成选择理由"""
        
        reasons = []
        
        # 时间匹配
        target_days = mapping["target_days"]
        actual_days = candidate.days_to_expiry
        if abs(actual_days - target_days) <= 3:
            reasons.append(f"到期时间({actual_days}天)与目标({target_days}天)非常接近")
        else:
            reasons.append(f"到期时间为{actual_days}天，在{mapping['description']}范围内")
        
        # 期权类型
        if candidate.is_weekly and preference == ExpirationPreference.WEEKLY:
            reasons.append("符合周度期权偏好")
        elif candidate.is_monthly and preference == ExpirationPreference.MONTHLY:
            reasons.append("符合月度期权偏好")
        elif candidate.is_quarterly and preference == ExpirationPreference.QUARTERLY:
            reasons.append("符合季度期权偏好")
        
        # 流动性
        if candidate.liquidity_score >= 70:
            reasons.append("流动性优秀")
        elif candidate.liquidity_score >= 50:
            reasons.append("流动性良好")
        else:
            reasons.append("流动性一般")
        
        # 特殊事件
        if candidate.special_events:
            event_descriptions = {
                "earnings_season": "财报季",
                "expiration_week": "期权到期周"
            }
            events_str = ", ".join([event_descriptions.get(e, e) for e in candidate.special_events])
            reasons.append(f"注意: {events_str}")
        
        return "；".join(reasons)
    
    def _get_third_friday(self, year: int, month: int) -> date:
        """获取指定年月的第三个周五"""
        # 找到该月第一天
        first_day = date(year, month, 1)
        
        # 找到第一个周五
        days_until_friday = (4 - first_day.weekday()) % 7
        first_friday = first_day + timedelta(days=days_until_friday)
        
        # 第三个周五
        third_friday = first_friday + timedelta(days=14)
        
        # 确保没有超出该月
        import calendar
        last_day = calendar.monthrange(year, month)[1]
        if third_friday.day > last_day:
            # 如果超出，返回第二个周五
            return first_friday + timedelta(days=7)
        
        return third_friday
    
    def get_expiration_analysis(
        self,
        symbol: str,
        duration: str
    ) -> Dict[str, Any]:
        """
        获取期权到期日分析报告
        
        Args:
            symbol: 股票代码
            duration: 持续时间
            
        Returns:
            分析报告字典
        """
        import asyncio
        
        async def _analyze():
            result = await self.get_optimal_expiration(symbol, duration)
            
            return {
                "symbol": symbol,
                "duration": duration,
                "recommended_expiration": result.selected_date,
                "selection_reason": result.selection_reason,
                "metadata": result.metadata,
                "alternatives": [
                    {
                        "date": alt.date,
                        "days_to_expiry": alt.days_to_expiry,
                        "score": alt.final_score,
                        "type": "weekly" if alt.is_weekly else "monthly" if alt.is_monthly else "other",
                        "special_events": alt.special_events
                    }
                    for alt in result.alternatives
                ],
                "analysis_timestamp": datetime.now().isoformat()
            }
        
        # 运行异步分析
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _analyze())
                    return future.result()
            else:
                return loop.run_until_complete(_analyze())
        except RuntimeError:
            return asyncio.run(_analyze())


# 便捷函数

def get_optimal_expiration_date(
    symbol: str,
    duration: str,
    tradier_client: Optional[TradierClient] = None,
    prefer_high_liquidity: bool = True
) -> str:
    """
    获取最优期权到期日的便捷函数
    
    Args:
        symbol: 股票代码
        duration: 持续时间
        tradier_client: Tradier客户端 (可选)
        prefer_high_liquidity: 是否偏好高流动性
        
    Returns:
        最优到期日 (YYYY-MM-DD)
    """
    selector = ExpirationSelector(
        tradier_client=tradier_client,
        prefer_high_liquidity=prefer_high_liquidity
    )
    
    import asyncio
    
    async def _get_date():
        result = await selector.get_optimal_expiration(symbol, duration)
        return result.selected_date
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _get_date())
                return future.result()
        else:
            return loop.run_until_complete(_get_date())
    except RuntimeError:
        return asyncio.run(_get_date())


def analyze_expiration_candidates(
    symbol: str,
    duration: str,
    tradier_client: Optional[TradierClient] = None
) -> List[Dict[str, Any]]:
    """
    分析期权到期日候选者的便捷函数
    
    Args:
        symbol: 股票代码
        duration: 持续时间
        tradier_client: Tradier客户端
        
    Returns:
        候选者分析列表
    """
    selector = ExpirationSelector(tradier_client=tradier_client)
    analysis = selector.get_expiration_analysis(symbol, duration)
    
    candidates = [
        {
            "date": analysis["recommended_expiration"],
            "rank": 1,
            "is_recommended": True,
            "reason": analysis["selection_reason"],
            **analysis["metadata"]
        }
    ]
    
    for i, alt in enumerate(analysis.get("alternatives", []), 2):
        candidates.append({
            "rank": i,
            "is_recommended": False,
            "reason": f"备选方案 - {alt['type']}期权",
            **alt
        })
    
    return candidates