"""表现层：图表与报告。"""

from gacha.viz.plots import (
    plot_compare_combine_cdf,
    plot_comparison,
    plot_cost_grid,
    plot_pmf_cdf,
)
from gacha.viz.report import build_report, generate_report

__all__ = [
    "plot_pmf_cdf", "plot_comparison", "plot_cost_grid", "plot_compare_combine_cdf",
    "build_report", "generate_report",
]
