"""共享分布取数层：PNG(plots.py) 与 HTML(report.py) 复用同一套 pmf/cdf/关键分位计算。

把"截到哪、取哪段、算哪些标注点"的逻辑收敛到一处，避免两套渲染器各写一遍。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from gacha.analysis import metrics
from gacha.engine.base import PullDistribution
from gacha.viz import theme


def plot_range(dist: PullDistribution, pad: int = 20) -> int:
    """绘图横轴上限：取 P99 再留 pad 抽余量，封顶到分布最大抽数。"""
    p99 = metrics.quantile(dist, 0.99)
    base = p99 if p99 > 0 else dist.max_pulls
    return min(dist.max_pulls, base + pad)


@dataclass(frozen=True)
class DistPlotData:
    """一次性算好的绘图数据与关键标注点。"""

    n: np.ndarray
    pmf: np.ndarray
    cdf: np.ndarray
    exp: float
    p50: int
    p90: int
    p99: int
    cap: int

    @property
    def ymax(self) -> float:
        return float(self.pmf.max()) if len(self.pmf) else 1.0


def dist_plot_data(
    dist: PullDistribution,
    max_pulls: int | None = None,
    pad: int = 20,
) -> DistPlotData:
    """计算 PMF 切片、CDF 与期望/P50/P90/P99。`max_pulls` 为 None 时按 P99 自适应截断。"""
    cap = plot_range(dist, pad) if max_pulls is None else min(max_pulls, dist.max_pulls)
    pmf = dist.pmf[: cap + 1]
    n = np.arange(len(pmf))
    cdf = np.cumsum(pmf)
    return DistPlotData(
        n=n,
        pmf=pmf,
        cdf=cdf,
        exp=metrics.expectation(dist),
        p50=metrics.quantile(dist, 0.5),
        p90=metrics.quantile(dist, 0.9),
        p99=metrics.quantile(dist, 0.99),
        cap=cap,
    )


@dataclass(frozen=True)
class GridPlotData:
    """命座×精炼成本网格的绘图数据：期望抽数/人民币矩阵 + 行列标签。"""

    exp: np.ndarray  # shape (n_const, n_refine)
    money: np.ndarray
    const_labels: list[str]
    refine_labels: list[str]
    game_key: str
    game_name: str

    @property
    def vmax(self) -> float:
        return float(self.exp.max()) if self.exp.size else 1.0


def grid_plot_data(grid) -> GridPlotData:
    """从 ``CostGrid`` 提取绘图所需的矩阵与标签（PNG/HTML 共用）。"""
    return GridPlotData(
        exp=np.array(grid.exp_pulls),
        money=np.array(grid.money_cny),
        const_labels=grid.const_labels(),
        refine_labels=grid.refine_labels(),
        game_key=grid.game_key,
        game_name=grid.game_name,
    )


@dataclass(frozen=True)
class CompareData:
    """跨游戏比对的绘图数据：与渲染无关的取数与配色（PNG/HTML 共用）。"""

    rows: list
    game_keys: list[str]
    game_names: list[str]
    exp_pulls: list[float]
    exp_money_cny: list[float]
    free_featured_per_month: list[float]
    colors: list[str]
    shared_cny: float | None


def comparison_data(rows) -> CompareData:
    """从 ``ComparisonRow`` 列表提取柱状图取数与统一配色。"""
    from gacha.analysis.compare import shared_money_per_pull_cny

    return CompareData(
        rows=list(rows),
        game_keys=[r.game_key for r in rows],
        game_names=[r.game_name for r in rows],
        exp_pulls=[r.exp_pulls for r in rows],
        exp_money_cny=[r.exp_money_cny for r in rows],
        free_featured_per_month=[r.free_featured_per_month for r in rows],
        colors=[theme.game_color(r.game_key, i) for i, r in enumerate(rows)],
        shared_cny=shared_money_per_pull_cny(rows),
    )


@dataclass(frozen=True)
class CombineCdfSeries:
    """跨游戏组合目标 CDF 叠加图的单条曲线（含配色与关键标量）。"""

    game_key: str
    game_name: str
    char_only: bool
    exp_pulls: float
    exp_money_cny: float
    n: np.ndarray
    cdf: np.ndarray
    color: str


@dataclass(frozen=True)
class CombineCdfData:
    """跨游戏组合目标比对的绘图数据：CDF 曲线集合 + 横轴上限 + 元信息。"""

    series: list[CombineCdfSeries]
    max_x: int
    char_copies: int
    weap_copies: int
    shared_cny: float | None


def combine_cdf_data(rows) -> CombineCdfData:
    """从 ``CombineComparisonRow`` 列表计算各游戏 CDF 切片与统一配色。

    过滤掉无 ``dist`` 的行；至少需要一行有效，否则抛 ``ValueError``。
    """
    from gacha.analysis.compare import (
        CombineComparisonRow,
        shared_money_per_pull_cny,
    )

    rows = [r for r in rows if isinstance(r, CombineComparisonRow) and r.dist is not None]
    if not rows:
        raise ValueError("需要至少一行带 dist 的 CombineComparisonRow")

    shared_cny = shared_money_per_pull_cny(rows)
    series: list[CombineCdfSeries] = []
    max_x = 0
    for i, r in enumerate(rows):
        dist = r.dist
        assert dist is not None
        cap = plot_range(dist)
        series.append(CombineCdfSeries(
            game_key=r.game_key,
            game_name=r.game_name,
            char_only=r.char_only,
            exp_pulls=r.exp_pulls,
            exp_money_cny=r.exp_money_cny,
            n=np.arange(cap),
            cdf=np.cumsum(dist.pmf[:cap]),
            color=theme.game_color(r.game_key, i),
        ))
        max_x = max(max_x, cap - 1)
    return CombineCdfData(
        series=series,
        max_x=max_x,
        char_copies=rows[0].char_copies,
        weap_copies=rows[0].weap_copies,
        shared_cny=shared_cny,
    )
