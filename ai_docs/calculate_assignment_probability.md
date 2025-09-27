# Reference Implementation to Calculate Assignment Probability for both Put and Call Options

```python
"""
期权被行权概率精确计算模块
基于Black-Scholes模型计算期权到期时处于实值的精确概率

替代Delta近似值，提供更准确的被行权风险评估
"""

import json
from typing import Any, Dict, Union

import numpy as np
from scipy.stats import norm


def calculate_assignment_probability(
    underlying_price: float,
    strike_price: float,
    time_to_expiry_days: float,
    implied_volatility: float,
    risk_free_rate: float = 0.048,
    option_type: str = "put",
) -> Dict[str, Any]:
    """
    计算期权被行权概率（到期时处于实值的精确概率）

    基于Black-Scholes模型的严格数学计算，替代Delta近似值

    参数:
        underlying_price (float): 标的资产当前价格
        strike_price (float): 期权行权价格
        time_to_expiry_days (float): 距离到期天数
        implied_volatility (float): 隐含波动率（年化，小数形式）
        risk_free_rate (float): 无风险利率（年化，默认4.8%）
        option_type (str): 期权类型，"put"或"call"

    返回:
        包含详细分析结果的字典
    """

    try:
        # 参数验证
        if underlying_price <= 0:
            raise ValueError("标的价格必须大于0")
        if strike_price <= 0:
            raise ValueError("行权价必须大于0")
        if time_to_expiry_days <= 0:
            raise ValueError("到期天数必须大于0")
        if implied_volatility <= 0:
            raise ValueError("隐含波动率必须大于0")
        if option_type.lower() not in ["put", "call"]:
            raise ValueError("期权类型必须是'put'或'call'")

        # 转换时间单位：天数 → 年
        T = time_to_expiry_days / 365.0

        # 标准化参数
        S = float(underlying_price)
        K = float(strike_price)
        r = float(risk_free_rate)
        sigma = float(implied_volatility)

        # 计算Black-Scholes模型核心参数
        sqrt_T = np.sqrt(T)
        ln_S_K = np.log(S / K)

        d1 = (ln_S_K + (r + 0.5 * sigma**2) * T) / (sigma * sqrt_T)
        d2 = d1 - sigma * sqrt_T

        # 计算概率
        if option_type.lower() == "put":
            # 看跌期权：实值条件是 S < K
            # 被行权概率 = P(S_T < K) = N(-d2)
            prob_assignment = norm.cdf(-d2)
            prob_expire_otm = norm.cdf(d2)
        else:  # call
            # 看涨期权：实值条件是 S > K
            # 被行权概率 = P(S_T > K) = N(d2)
            prob_assignment = norm.cdf(d2)
            prob_expire_otm = norm.cdf(-d2)

        # 计算价值状态
        moneyness_ratio = S / K
        if option_type.lower() == "put":
            if moneyness_ratio < 0.95:
                moneyness = "深度实值"
                risk_level = "极高"
            elif moneyness_ratio < 0.98:
                moneyness = "实值"
                risk_level = "高"
            elif moneyness_ratio < 1.02:
                moneyness = "接近平值"
                risk_level = "中"
            elif moneyness_ratio < 1.05:
                moneyness = "虚值"
                risk_level = "低"
            else:
                moneyness = "深度虚值"
                risk_level = "极低"
        else:  # call
            if moneyness_ratio > 1.05:
                moneyness = "深度实值"
                risk_level = "极高"
            elif moneyness_ratio > 1.02:
                moneyness = "实值"
                risk_level = "高"
            elif moneyness_ratio > 0.98:
                moneyness = "接近平值"
                risk_level = "中"
            elif moneyness_ratio > 0.95:
                moneyness = "虚值"
                risk_level = "低"
            else:
                moneyness = "深度虚值"
                risk_level = "极低"

        # 计算风险指标
        if prob_assignment > 0.7:
            assignment_risk = "极高"
        elif prob_assignment > 0.5:
            assignment_risk = "高"
        elif prob_assignment > 0.3:
            assignment_risk = "中等"
        elif prob_assignment > 0.15:
            assignment_risk = "较低"
        else:
            assignment_risk = "极低"

        # 构建返回结果
        result = {
            "status": "success",
            "calculation_method": "Black-Scholes精确计算",
            "assignment_probability": float(prob_assignment),
            "assignment_probability_percent": f"{prob_assignment:.2%}",
            "expire_otm_probability": float(prob_expire_otm),
            "expire_otm_probability_percent": f"{prob_expire_otm:.2%}",
            "assignment_risk_level": assignment_risk,
            "moneyness": moneyness,
            "moneyness_ratio": float(moneyness_ratio),
            "risk_assessment": risk_level,
            "black_scholes_parameters": {
                "d1": float(d1),
                "d2": float(d2),
                "time_to_expiry_years": float(T),
                "ln_stock_strike_ratio": float(ln_S_K),
            },
            "input_parameters": {
                "underlying_price": float(S),
                "strike_price": float(K),
                "time_to_expiry_days": float(time_to_expiry_days),
                "implied_volatility": float(sigma),
                "implied_volatility_percent": f"{sigma:.2%}",
                "risk_free_rate": float(r),
                "option_type": option_type.upper(),
            },
            "interpretation": {
                "assignment_probability_meaning": f"到期时期权处于实值被行权的概率为 {prob_assignment:.2%}",
                "risk_explanation": f"基于当前参数，该期权的被行权风险评级为：{assignment_risk}",
                "moneyness_explanation": f"当前期权状态为：{moneyness}（股价/行权价比率：{moneyness_ratio:.4f}）",
            },
        }

        return result

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"计算被行权概率失败: {str(e)}",
            "input_parameters": {
                "underlying_price": underlying_price,
                "strike_price": strike_price,
                "time_to_expiry_days": time_to_expiry_days,
                "implied_volatility": implied_volatility,
                "risk_free_rate": risk_free_rate,
                "option_type": option_type,
            },
        }


def compare_with_delta_approximation(
    underlying_price: float,
    strike_price: float,
    time_to_expiry_days: float,
    implied_volatility: float,
    delta_value: float,
    risk_free_rate: float = 0.048,
    option_type: str = "put",
) -> Dict[str, Any]:
    """
    比较精确被行权概率与Delta近似值的差异

    参数:
        delta_value (float): 期权的Delta值
        其他参数同calculate_assignment_probability

    返回:
        包含比较分析的详细字典
    """

    try:
        # 计算精确概率
        exact_result = calculate_assignment_probability(
            underlying_price, strike_price, time_to_expiry_days, implied_volatility, risk_free_rate, option_type
        )

        if exact_result["status"] == "error":
            return exact_result

        # Delta近似值（绝对值）
        delta_approx = abs(float(delta_value))
        exact_prob = exact_result["assignment_probability"]

        # 计算差异
        absolute_diff = abs(exact_prob - delta_approx)
        relative_diff = (absolute_diff / exact_prob * 100) if exact_prob != 0 else 0

        # 精度评估
        if relative_diff < 5:
            accuracy = "高精度"
            recommendation = "Delta近似值可接受"
        elif relative_diff < 15:
            accuracy = "中等精度"
            recommendation = "建议使用精确计算"
        else:
            accuracy = "低精度"
            recommendation = "强烈建议使用精确计算"

        comparison_result = {
            "status": "success",
            "exact_assignment_probability": float(exact_prob),
            "exact_probability_percent": f"{exact_prob:.2%}",
            "delta_approximation": float(delta_approx),
            "delta_approximation_percent": f"{delta_approx:.2%}",
            "absolute_difference": float(absolute_diff),
            "relative_difference_percent": float(relative_diff),
            "accuracy_assessment": accuracy,
            "recommendation": recommendation,
            "comparison_summary": {
                "method_comparison": "Black-Scholes精确计算 vs Delta近似值",
                "difference_analysis": f"精确值与Delta近似值相差 {absolute_diff:.4f} ({relative_diff:.2f}%)",
                "accuracy_note": f"在当前参数下，Delta近似的精度为：{accuracy}",
            },
            "exact_calculation_details": exact_result,
        }

        return comparison_result

    except Exception as e:
        return {"status": "error", "error_message": f"比较计算失败: {str(e)}", "delta_value": delta_value}


def analyze_multiple_positions_assignment_risk(positions: list) -> Dict[str, Any]:
    """
    批量分析多个期权仓位的被行权风险

    参数:
        positions (list): 包含多个期权仓位信息的列表
        每个仓位应包含: symbol, underlying_price, strike_price,
                    time_to_expiry_days, implied_volatility, option_type
                    可选: contracts, risk_free_rate

    返回:
        包含所有仓位风险分析的汇总报告
    """

    try:
        results = []
        total_high_risk_positions = 0
        total_positions = len(positions)

        for i, pos in enumerate(positions):
            try:
                # 计算被行权概率
                prob_result = calculate_assignment_probability(
                    pos["underlying_price"],
                    pos["strike_price"],
                    pos["time_to_expiry_days"],
                    pos["implied_volatility"],
                    pos.get("risk_free_rate", 0.048),
                    pos["option_type"],
                )

                if prob_result["status"] == "success":
                    contracts = pos.get("contracts", 1)
                    assignment_prob = prob_result["assignment_probability"]
                    expected_assignments = assignment_prob * contracts

                    # 统计高风险仓位
                    if assignment_prob > 0.5:
                        total_high_risk_positions += 1

                    position_analysis = {
                        "position_id": i + 1,
                        "symbol": pos.get("symbol", "N/A"),
                        "option_type": pos["option_type"].upper(),
                        "strike_price": pos["strike_price"],
                        "current_price": pos["underlying_price"],
                        "days_to_expiry": pos["time_to_expiry_days"],
                        "contracts": contracts,
                        "assignment_probability": assignment_prob,
                        "assignment_probability_percent": f"{assignment_prob:.2%}",
                        "expected_assignments": float(expected_assignments),
                        "risk_level": prob_result["assignment_risk_level"],
                        "moneyness": prob_result["moneyness"],
                        "detailed_analysis": prob_result,
                    }

                    results.append(position_analysis)
                else:
                    results.append(
                        {
                            "position_id": i + 1,
                            "symbol": pos.get("symbol", "N/A"),
                            "status": "error",
                            "error": prob_result["error_message"],
                        }
                    )

            except Exception as e:
                results.append(
                    {"position_id": i + 1, "symbol": pos.get("symbol", "N/A"), "status": "error", "error": str(e)}
                )

        # 生成汇总报告
        portfolio_summary = {
            "status": "success",
            "analysis_timestamp": "当前时间",
            "portfolio_overview": {
                "total_positions": total_positions,
                "analyzed_positions": len([r for r in results if r.get("status") != "error"]),
                "high_risk_positions": total_high_risk_positions,
                "high_risk_ratio": f"{total_high_risk_positions/total_positions:.1%}" if total_positions > 0 else "0%",
            },
            "position_analyses": results,
            "portfolio_risk_assessment": {
                "overall_risk": (
                    "高"
                    if total_high_risk_positions > total_positions * 0.5
                    else "中等" if total_high_risk_positions > 0 else "低"
                ),
                "recommendation": (
                    "建议优先关注高风险仓位的调整机会"
                    if total_high_risk_positions > 0
                    else "当前投资组合被行权风险较低"
                ),
            },
        }

        return portfolio_summary

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"投资组合风险分析失败: {str(e)}",
            "positions_count": len(positions) if positions else 0,
        }

```
