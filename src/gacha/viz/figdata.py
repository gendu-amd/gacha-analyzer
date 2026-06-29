"""共享分布取数层：PNG(plots.py) 与 HTML(report.py) 复用同一套 pmf/cdf/关键分位计算。

把"截到哪、取哪段、算哪些标注点"的逻辑收敛到一处，避免两套渲染器各写一遍。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from gacha.analysis import metrics
from gacha.engine.base import PullDistribution


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
