"""指标层：从 PullDistribution 派生 CDF / 期望 / 分位数 / Cashback / 运气分位 / 风险.

所有函数接受 PullDistribution 或一维 pmf 数组。约定 pmf[k] = 恰好第 k 抽达成目标的概率。
"""

from __future__ import annotations

import math
from typing import Union

import numpy as np

from gacha.engine.base import PullDistribution

DistLike = Union[PullDistribution, np.ndarray]


def _pmf(dist: DistLike) -> np.ndarray:
    if isinstance(dist, PullDistribution):
        return dist.pmf
    return np.asarray(dist, dtype=float)


def total_mass(dist: DistLike) -> float:
    """分布覆盖的总概率（截断分布 <1，可用于健全性检查）。"""
    return float(_pmf(dist).sum())


def cdf(dist: DistLike) -> np.ndarray:
    """累计分布：cdf[n] = P(在 n 抽以内达成目标)。"""
    return np.cumsum(_pmf(dist))


def expectation(dist: DistLike) -> float:
    """期望抽数 E[N]。

    对**截断分布**（total_mass<1，例如 ``solve(..., max_pulls=90)``）按 total_mass 归一化，
    即返回「条件于在支持范围内达成」的期望 E[N | N<=max_pulls]，与 ``cashback_expected``
    的除以 mass 口径一致；否则未覆盖的尾部概率会被当成 0 而**系统性低估**期望。
    full 分布（mass≈1）行为不变。
    """
    p = _pmf(dist)
    mass = p.sum()
    if mass <= 0:
        return float("nan")
    k = np.arange(len(p))
    return float((k * p).sum() / mass)


def variance(dist: DistLike) -> float:
    """方差 Var[N]；与 ``expectation`` 同口径，对截断分布按 total_mass 归一化（条件方差）。"""
    p = _pmf(dist)
    mass = p.sum()
    if mass <= 0:
        return float("nan")
    k = np.arange(len(p))
    mean = (k * p).sum() / mass
    return float((((k - mean) ** 2) * p).sum() / mass)


def std(dist: DistLike) -> float:
    """标准差 σ；与 ``expectation``/``variance`` 同口径（截断分布按 total_mass 归一化）。"""
    return math.sqrt(variance(dist))


def prob_within(dist: DistLike, n: int) -> float:
    """在 n 抽以内达成目标的概率 P(N<=n)。"""
    if n < 0:
        return 0.0
    c = cdf(dist)
    return float(c[min(n, len(c) - 1)])


def quantile(dist: DistLike, q: float) -> int:
    """达成把握 q 所需的最少抽数：最小的 n 使 P(N<=n) >= q。

    若分布覆盖的总概率不足 q（截断），返回 -1。
    """
    if not 0.0 < q <= 1.0:
        raise ValueError("q 应在 (0, 1]")
    c = cdf(dist)
    idx = np.searchsorted(c, q, side="left")
    if idx >= len(c):
        return -1
    return int(idx)


def pulls_for_confidence(dist: DistLike, p: float) -> int:
    """达成把握 p 所需抽数（quantile 的别名，决策语义）。"""
    return quantile(dist, p)


def percentiles(dist: DistLike, qs=(0.25, 0.5, 0.75, 0.9, 0.99)) -> dict[float, int]:
    return {q: quantile(dist, q) for q in qs}


def cashback_expected(dist: DistLike, pack_size: int = 10) -> float:
    """Cashback / 剩余抽数返还期望.

    若按 ``pack_size`` 连抽（如十连）购买，达成目标时当前连抽包内「多买的抽数」期望：
    E[ceil(N/pack)*pack - N | 已达成]。衡量「凑整连抽的浪费」，规划向指标。
    """
    p = _pmf(dist)
    mass = p.sum()
    if mass <= 0:
        return float("nan")
    n = np.arange(len(p))
    overshoot = (np.ceil(n / pack_size) * pack_size - n)
    return float((overshoot * p).sum() / mass)


def luck_percentile(dist: DistLike, n: int) -> float:
    """运气分位：在第 n 抽达成，比例上「比多少人更欧」.

    返回 P(N > n)，即「需要更多抽才达成」的人群占比 —— 你用更少抽，超过了他们。
    取值 0~1，越大越欧。
    """
    return float(max(0.0, 1.0 - prob_within(dist, n)))


def value_at_risk(dist: DistLike, q: float = 0.9) -> int:
    """VaR_q：达成把握 q 的抽数门槛（即 quantile(q)）。常作「安全垫」抽数。"""
    return quantile(dist, q)


def conditional_value_at_risk(dist: DistLike, q: float = 0.9) -> float:
    """严格 Expected Shortfall（ES）：最坏 α=(1-q) 尾部概率质量上的平均抽数。

    与朴素的「条件尾期望 CTE = E[N | N>=VaR_q]」不同：因 ``VaR_q`` 处通常有原子且
    ``P(N>=VaR_q) > α``，CTE 会把整块原子计入、稀释到 VaR，低估风险。本函数按
    Acerbi–Tasche 的相干 ES 公式，对 VaR 处原子只取 ``(α - P(N>VaR))`` 的份额：

        ES_α = [ E[N·1{N>VaR}] + VaR·(α - P(N>VaR)) ] / α,  α = (1-q)

    故恒有 ``ES >= CTE >= VaR``，更保守地刻画「非酋情形」。截断分布按 total_mass 归一化。
    """
    var = value_at_risk(dist, q)
    if var < 0:
        return float("nan")
    p = _pmf(dist)
    mass = float(p.sum())
    if mass <= 0:
        return float("nan")
    alpha = (1.0 - q) * mass  # 目标尾部概率质量（按覆盖质量缩放，兼容截断分布）
    if alpha <= 0:
        return float(var)
    n = np.arange(len(p))
    strict = n > var
    e_strict = float((n[strict] * p[strict]).sum())  # E[N·1{N>VaR}]（未归一）
    p_strict = float(p[strict].sum())                # P(N>VaR)（未归一）
    atom_weight = alpha - p_strict                   # VaR 原子计入份额（可能为 0）
    if atom_weight < 0:  # 数值兜底：尾部已超出 α，仅取严格尾部
        atom_weight = 0.0
    es = (e_strict + var * atom_weight) / alpha
    return float(es)


def summary(dist: DistLike) -> dict:
    """一站式核心指标汇总。"""
    return {
        "total_mass": total_mass(dist),
        "expectation": expectation(dist),
        "std": std(dist),
        "p50": quantile(dist, 0.5),
        "p90": quantile(dist, 0.9),
        "p99": quantile(dist, 0.99),
        "cashback_10pull": cashback_expected(dist, 10),
        "safety_floor_p90": value_at_risk(dist, 0.9),
        "cvar_p90": conditional_value_at_risk(dist, 0.9),
    }
