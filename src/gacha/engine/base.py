"""统一数据结构与求解器契约（接口冻结，修改需走 DECISIONS.md 变更流程）.

设计要点（见 PROJECT_PROPOSAL.md §6.4）：
- 求解器只产出 ``PullDistribution``；CDF / 期望 / 分位数等派生指标统一在 ``analysis.metrics``。
- ``games/`` 只放数据（机制 + 经济参数），不放算法。
- 新增游戏 = 新增 ``games/*.py``，不改引擎/分析核心。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import numpy as np

# 池子键常量（消除散落的魔法字符串，避免静默错配）。
BANNER_CHARACTER = "character"
BANNER_WEAPON = "weapon"
BANNER_STANDARD = "standard"
BANNER_CHRONICLED = "chronicled"


@dataclass(frozen=True)
class PullState:
    """玩家当前抽卡状态（输入）.

    Attributes:
        item_pity: 当前已垫抽数（距上次出 5★/最高稀有度的抽数计数）。
        is_guaranteed: 是否处于「大保底」（上次 50/50 歪了，下个必为 UP）。
        radiance_losses: 「捕获明光」连续歪的次数（0~3）。仅对支持该机制的池子有效。

    注意（与真实机制一致）：「大保底」是由「50/50 歪了」产生的，而那次歪同时会让捕获明光
    连歪计数 +1。因此 ``is_guaranteed=True`` 时 ``radiance_losses`` 必 >=1；若调用方只知道
    自己处于大保底而未跟踪明光计数，可保持默认 0，适配层会按 GGanalysis 约定折算为 1。
    """

    item_pity: int = 0
    is_guaranteed: bool = False
    radiance_losses: int = 0

    def __post_init__(self) -> None:
        if self.item_pity < 0:
            raise ValueError("item_pity 不能为负")
        if not 0 <= self.radiance_losses <= 3:
            raise ValueError("radiance_losses 取值范围为 0~3")


@dataclass(frozen=True)
class Target:
    """抽卡目标（输入）.

    Attributes:
        banner: 池子类型键，如 "character" / "weapon"（见 BANNER_* 常量）。
        copies: 需要的拷贝数（角色 C0=1, C6=7；武器 R1=1, R5=5）。
    """

    banner: str = BANNER_CHARACTER
    copies: int = 1

    def __post_init__(self) -> None:
        if self.copies < 1:
            raise ValueError("copies 至少为 1")


@dataclass(frozen=True)
class PullDistribution:
    """统一输出：达成目标所需抽数的分布.

    Attributes:
        pmf: 一维数组，``pmf[k]`` = 恰好在第 k 抽达成目标的概率；``pmf[0]`` 恒为 0。
        source: 产生该分布的求解器标识（如 "gganalysis" / "reference-mc"）。
    """

    pmf: np.ndarray
    source: str = ""

    def __post_init__(self) -> None:
        arr = np.asarray(self.pmf, dtype=float)
        if arr.ndim != 1:
            raise ValueError("pmf 必须是一维数组")
        object.__setattr__(self, "pmf", arr)

    @classmethod
    def from_finite_dist(cls, dist, source: str = "gganalysis") -> "PullDistribution":
        """从 GGanalysis 的 ``FiniteDist`` 构造。"""
        return cls(pmf=np.asarray(dist.dist, dtype=float), source=source)

    @property
    def max_pulls(self) -> int:
        """分布覆盖的最大抽数（数组最后一个下标）。"""
        return len(self.pmf) - 1


@runtime_checkable
class Solver(Protocol):
    """求解器契约：所有引擎（GGanalysis 封装 / reference 自研）实现同一签名。

    ``max_pulls`` 统一约定（所有求解器一致，保证可无缝替换）：
    - ``max_pulls <= 0``（含缺省 0）= **自动选取合理上限**。精确解（GGanalysis）直接返回
      完整分布；蒙特卡洛等需要显式上限的求解器自行根据机制推导一个足以覆盖全部概率
      质量的上限（不得报错）。
    - ``max_pulls > 0`` = 截断/补齐到该上限（pmf 长度为 max_pulls+1）。
    """

    name: str

    def solve(
        self,
        game,
        state: PullState,
        target: Target,
        max_pulls: int,
    ) -> PullDistribution:
        ...
