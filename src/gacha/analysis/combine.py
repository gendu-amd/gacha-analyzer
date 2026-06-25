"""组合目标：多个独立目标合并所需的总抽数分布（卷积）.

数学：若分别需要 A、B 两个目标，且按顺序各自独立抽取，则「总抽数 = 抽到A的抽数 +
抽到B的抽数」，其分布为两者分布的**卷积**。这正是 GGanalysis FiniteDist 的 `*` 运算，
本模块用 numpy 卷积在统一的 PullDistribution 上实现，便于跨求解器复用。

典型用法：角色(C0) + 武器(R1) 的联合期望。
"""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np

from gacha.engine.base import PullDistribution, PullState, Target


def combine(dists: Sequence[PullDistribution]) -> PullDistribution:
    """把多个目标的抽数分布卷积为「全部达成」的总抽数分布。"""
    dists = list(dists)
    if not dists:
        raise ValueError("至少需要一个分布")
    if len(dists) == 1:
        return dists[0]
    pmf = np.array([1.0])
    for d in dists:
        pmf = np.convolve(pmf, d.pmf)
    src = "+".join(d.source or "?" for d in dists)
    return PullDistribution(pmf=pmf, source=f"combined({src})")


def combine_targets(
    game,
    solver,
    items: Iterable[tuple[PullState, Target]],
    max_pulls: int = 0,
) -> PullDistribution:
    """便捷函数：对每个 (state, target) 求解后卷积合并。

    Args:
        game: GameSpec。
        solver: 实现 Solver 协议的求解器。
        items: 若干 (PullState, Target) 对。
        max_pulls: 透传给求解器（0 表示用各自完整分布）。
    """
    dists = [solver.solve(game, state, target, max_pulls) for state, target in items]
    return combine(dists)
