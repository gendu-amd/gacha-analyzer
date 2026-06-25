"""自研蒙特卡洛引擎（50/50 + 捕获明光 角色池）—— 教学 + 独立校验.

实现思路（玻璃盒）：
1. 把抽卡拆成「一个个 5★ 事件」。从给定水位采样「距下个 5★ 还要多少抽」（软/硬保底支配）。
2. 每个 5★ 事件按 50/50 + 捕获明光 决定是否 UP（带记忆的条件概率）。
3. 重复到集齐目标 UP 数，统计总抽数分布。

为可在百万级模拟下保持速度，采用「按 5★ 事件分轮、对所有 run 向量化」的写法：
每个 run 平均只有 ~1.5~5 个 5★ 事件，故按事件分轮远快于逐抽循环。

捕获明光状态转移（对齐 GGanalysis CR 模型）：
- 非大保底命中 5★：以 cr_up_prob[losses] 概率为 UP（连歪计数清零）；否则歪（转大保底，连歪 +1）。
- 大保底命中 5★：必为 UP（连歪计数保持不变）。

**单向依赖**：本模块只依赖 ``engine.base``，不 import ``gacha.games.*``。游戏专属机制
（出率曲线 / 硬保底 / 捕获明光表）通过 ``CharacterMechanism`` 由上层注入（见
``games.genshin.genshin_character_mechanism``）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from gacha.engine.base import BANNER_CHARACTER, PullDistribution, PullState, Target


@dataclass(frozen=True)
class CharacterMechanism:
    """game-agnostic 角色池机制描述（依赖注入用，避免 engine 反向依赖 games）.

    Attributes:
        rate_fn: ``pity`` (1-indexed，距上次 5★) -> 该抽出 5★ 的条件概率。
        hard_pity: 硬保底抽数（必出 5★）。
        cr_up_prob: 捕获明光表，索引=连歪次数 0..n；值=该状态下 50/50 转 UP 的概率。
    """

    rate_fn: Callable[[int], float]
    hard_pity: int
    cr_up_prob: tuple[float, ...]


def _gap_cdf_from(mech: CharacterMechanism, start_pity: int) -> np.ndarray:
    """从水位 ``start_pity`` 出发，「再抽多少抽得到下一个 5★」的 CDF（1-indexed gap）。"""
    rates = np.array(
        [mech.rate_fn(p) for p in range(start_pity + 1, mech.hard_pity + 1)],
        dtype=float,
    )
    surv = np.cumprod(1.0 - rates)
    pmf = np.empty_like(rates)
    pmf[0] = rates[0]
    pmf[1:] = rates[1:] * surv[:-1]
    return np.cumsum(pmf)


def _sample_gaps(cdf: np.ndarray, u: np.ndarray) -> np.ndarray:
    """用均匀随机数 u 按 CDF 反查采样 gap（返回抽数，1-indexed）。"""
    return np.searchsorted(cdf, u, side="right").astype(np.int64) + 1


class ReferenceMCSolver:
    """蒙特卡洛求解器（50/50 + 捕获明光 角色池，用于校验/教学）。

    机制由构造时注入的 ``CharacterMechanism`` 提供，本身 game-agnostic。
    """

    name = "reference-mc"

    def __init__(
        self,
        mechanism: CharacterMechanism,
        runs: int = 1_000_000,
        seed: int = 20260625,
    ) -> None:
        self.mechanism = mechanism
        self.runs = runs
        self.seed = seed

    def solve(
        self,
        game,
        state: PullState,
        target: Target,
        max_pulls: int = 0,
    ) -> PullDistribution:
        if target.banner != BANNER_CHARACTER:
            raise NotImplementedError(
                "reference-mc 仅实现「50/50 + 捕获明光」角色池（教学/校验用途）"
            )
        mech = self.mechanism
        copies = target.copies

        # max_pulls 统一约定：<=0 自动取合理上限（不报错）。
        # 每个拷贝最坏需 2 个 5★ 事件（歪一次→大保底），故 2*hard_pity*copies 为绝对上限。
        if max_pulls <= 0:
            max_pulls = 2 * mech.hard_pity * copies

        rng = np.random.default_rng(self.seed)
        runs = self.runs

        cdf_start = _gap_cdf_from(mech, state.item_pity)  # 首个 5★ 事件（条件于当前水位）
        cdf_zero = _gap_cdf_from(mech, 0)  # 之后每个 5★ 事件均从水位 0 起算

        total_pulls = np.zeros(runs, dtype=np.int64)
        up_count = np.zeros(runs, dtype=np.int64)
        guaranteed = np.full(runs, state.is_guaranteed, dtype=bool)
        # 与适配层 _to_gg_kwargs 同口径折算：处于大保底但未跟踪明光计数(losses=0)时折算为 1，
        # 否则 MC 会少算「连歪 1 次」的捕获明光增益，与 GGanalysis 分叉 ~2%。
        init_losses = state.radiance_losses
        if state.is_guaranteed and init_losses == 0:
            init_losses = 1
        losses = np.full(runs, init_losses, dtype=np.int64)

        cr_up = np.array(mech.cr_up_prob, dtype=float)
        max_loss_idx = len(cr_up) - 1
        first_event = True

        # 按 5★ 事件分轮，直到所有 run 达成目标
        while True:
            active = up_count < copies
            if not active.any():
                break
            idx = np.where(active)[0]

            cdf = cdf_start if first_event else cdf_zero
            u = rng.random(idx.size)
            gaps = _sample_gaps(cdf, u)
            total_pulls[idx] += gaps
            first_event = False

            # 解析这次 5★ 是否为 UP
            g = guaranteed[idx]
            l = losses[idx]
            # 非大保底：按 cr_up_prob[losses] 判定是否 UP
            r = rng.random(idx.size)
            win_5050 = (~g) & (r < cr_up[l])
            lose_5050 = (~g) & (~win_5050)

            # 大保底：必 UP，连歪计数不变
            is_up = g | win_5050
            up_count[idx[is_up]] += 1

            # 状态转移
            # 大保底命中后清除大保底标记（losses 不变）
            guaranteed[idx[g]] = False
            # 50/50 赢：连歪清零
            losses[idx[win_5050]] = 0
            # 50/50 歪：转大保底，连歪 +1（上限 = cr 表末位索引）
            guaranteed[idx[lose_5050]] = True
            losses[idx[lose_5050]] = np.minimum(l[lose_5050] + 1, max_loss_idx)

        counts = np.bincount(
            np.minimum(total_pulls, max_pulls + 1), minlength=max_pulls + 2
        ).astype(float)
        # 丢弃溢出桶（> max_pulls），仅保留 0..max_pulls
        pmf = counts[: max_pulls + 1] / runs
        return PullDistribution(pmf=pmf, source=self.name)
