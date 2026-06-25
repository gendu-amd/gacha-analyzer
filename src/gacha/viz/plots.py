"""分布可视化：PMF + CDF 双图，标注关键分位与预算线。"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import PercentFormatter  # noqa: E402
import numpy as np  # noqa: E402

from gacha.analysis import metrics  # noqa: E402
from gacha.engine.base import PullDistribution  # noqa: E402
from gacha.viz import theme  # noqa: E402

theme.apply_matplotlib_theme()


def _style_axes(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(colors=theme.MUTED, labelsize=9)
    ax.grid(axis="x", visible=False)


def _annotate(ax, x, text, color, y, va="bottom"):
    ax.annotate(
        text, xy=(x, y), xytext=(4, 0), textcoords="offset points",
        color=color, fontsize=8.5, fontweight="bold", va=va, ha="left",
    )


def _add_watermark(fig) -> None:
    fig.text(0.995, 0.01, theme.watermark_text(), ha="right",
             va="bottom", color=theme.WATERMARK, fontsize=8)


def plot_pmf_cdf(
    dist: PullDistribution,
    title: str = "Pull count distribution",
    out_path: str = "out/distribution.png",
    max_pulls: int | None = None,
    budget: int | None = None,
    subtitle: str | None = None,
) -> str:
    """绘制 PMF + CDF 双子图并保存为 PNG，返回保存路径。"""
    pmf = dist.pmf
    if max_pulls is not None:
        pmf = pmf[: max_pulls + 1]
    n = np.arange(len(pmf))
    c = np.cumsum(pmf)

    p50 = metrics.quantile(dist, 0.5)
    p90 = metrics.quantile(dist, 0.9)
    exp = metrics.expectation(dist)
    ymax = float(pmf.max()) if len(pmf) else 1.0

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(11, 7.2), sharex=True,
        gridspec_kw={"height_ratios": [1.15, 1], "hspace": 0.12},
    )

    ax1.fill_between(n, pmf, color=theme.BLUE_FILL, alpha=0.55, linewidth=0)
    ax1.plot(n, pmf, color=theme.BLUE, lw=1.6)
    ax1.axvline(exp, color=theme.AMBER, ls="--", lw=1.6)
    _annotate(ax1, exp, f"mean {exp:.0f}", theme.AMBER, ymax * 0.92)
    if 0 <= p50 < len(pmf):
        ax1.axvline(p50, color=theme.GREEN, ls=":", lw=1.6)
        _annotate(ax1, p50, f"median {p50}", theme.GREEN, ymax * 0.78)
    ax1.set_ylim(0, ymax * 1.18)
    ax1.set_ylabel("Probability per pull", color=theme.INK, fontsize=10)
    ax1.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=1))
    _style_axes(ax1)

    full_title = title if not subtitle else f"{title}\n{subtitle}"
    ax1.set_title(full_title, color=theme.INK, fontsize=13, fontweight="bold",
                  loc="left", pad=12)

    ax2.fill_between(n, c, color=theme.BLUE_FILL, alpha=0.30, linewidth=0)
    ax2.plot(n, c, color=theme.BLUE, lw=2.2)
    for lvl in (0.5, 0.9):
        ax2.axhline(lvl, color="#C5CCD6", ls=":", lw=1.0)
    if 0 <= p90 < len(c):
        ax2.axvline(p90, color=theme.RED, ls="--", lw=1.6)
        _annotate(ax2, p90, f"P90 = {p90} (safety net)", theme.RED, 0.05)
    if budget is not None and budget >= 0:
        prob = metrics.prob_within(dist, budget)
        ax2.axvline(budget, color=theme.PURPLE, ls="-.", lw=1.8)
        bx = min(budget, len(c) - 1)
        ax2.plot([budget], [c[bx]], "o", color=theme.PURPLE, ms=7, zorder=5)
        _annotate(ax2, budget, f"budget {budget} -> {prob:.0%}", theme.PURPLE, c[bx] + 0.04)
    ax2.set_ylim(0, 1.02)
    ax2.set_ylabel("Chance of success", color=theme.INK, fontsize=10)
    ax2.set_xlabel("Number of pulls", color=theme.INK, fontsize=10)
    ax2.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=0))
    ax2.set_xlim(0, len(pmf) - 1)
    _style_axes(ax2)

    _add_watermark(fig)
    fig.tight_layout(rect=(0, 0.015, 1, 1))
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    return out_path


def plot_cost_grid(grid, out_path: str = "out/grid.png",
                   show_money: bool = True, title: str | None = None) -> str:
    """命座×精炼 成本热力图：颜色=期望抽数，格内标注 抽数(/¥)。"""
    exp = np.array(grid.exp_pulls)
    money = np.array(grid.money_cny)
    rows = grid.const_labels()
    cols = grid.refine_labels()

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    h = 0.7 * len(rows) + 1.8
    w = 1.5 * len(cols) + 1.5
    fig, ax = plt.subplots(figsize=(w, h))
    im = ax.imshow(exp, cmap=theme.HEATMAP_SCALE, aspect="auto")

    ax.set_xticks(range(len(cols)), labels=cols)
    ax.set_yticks(range(len(rows)), labels=rows)
    ax.set_xlabel("Weapon refinement (R0 = no weapon)", color=theme.INK)
    ax.set_ylabel("Constellation", color=theme.INK)
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)

    vmax = exp.max()
    for i in range(len(rows)):
        for j in range(len(cols)):
            txt = f"{exp[i, j]:.0f}"
            if show_money:
                txt += f"\n¥{money[i, j]:.0f}"
            color = "white" if exp[i, j] > 0.6 * vmax else theme.INK
            ax.text(j, i, txt, ha="center", va="center", fontsize=8.5, color=color)

    cbar = fig.colorbar(im, ax=ax, shrink=0.85)
    cbar.set_label("Expected pulls", color=theme.INK)
    ax.set_title(title or f"{grid.game_key}: cost grid (expected pulls / CNY)",
                 color=theme.INK, fontsize=13, fontweight="bold", loc="left", pad=10)
    _add_watermark(fig)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    return out_path


def plot_comparison(rows, out_path: str = "out/compare.png",
                    title: str = "Cross-game comparison (per featured 5-star)") -> str:
    """跨游戏比对：左轴期望抽数（越低越划算），右图每月白嫖可得限定数。"""
    from gacha.analysis.compare import shared_money_per_pull_cny

    labels = [f"{r.game_key}" for r in rows]
    exp = [r.exp_pulls for r in rows]
    free = [r.free_featured_per_month for r in rows]
    shared_cny = shared_money_per_pull_cny(rows)
    colors = [theme.game_color(r.game_key, i) for i, r in enumerate(rows)]

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    bars = ax1.bar(labels, exp, color=colors, edgecolor=theme.INK, width=0.6, alpha=0.85)
    for b, e, r in zip(bars, exp, rows):
        if shared_cny is not None:
            ann = f"{e:.0f} pulls"
        else:
            ann = f"{e:.0f} pulls\n~¥{r.exp_money_cny:.0f}"
        ax1.annotate(ann, (b.get_x() + b.get_width() / 2, e),
                     ha="center", va="bottom", fontsize=9, color=theme.INK)
    ax1.set_title("Expected pulls per featured 5★ (lower = cheaper)",
                  fontsize=11, color=theme.INK, loc="left")
    ax1.set_ylabel("Expected pulls")
    ax1.set_ylim(0, max(exp) * 1.25 if exp else 1)
    if shared_cny is not None:
        ax1.text(0.99, 0.02, f"CNY @ ¥{shared_cny:.0f}/pull (shared)",
                 transform=ax1.transAxes, ha="right", va="bottom",
                 fontsize=8, color=theme.MUTED)
    _style_axes(ax1)

    bars2 = ax2.bar(labels, free, color=theme.GREEN_FILL, edgecolor=theme.GREEN, width=0.6)
    for b, f in zip(bars2, free):
        ax2.annotate(f"{f:.2f}", (b.get_x() + b.get_width() / 2, f),
                     ha="center", va="bottom", fontsize=9, color=theme.INK)
    ax2.set_title("Free featured 5★ per month (higher = more generous)",
                  fontsize=11, color=theme.INK, loc="left")
    ax2.set_ylabel("Featured 5★ / month (F2P)")
    ax2.set_ylim(0, max(free) * 1.3 if free else 1)
    _style_axes(ax2)

    fig.suptitle(title, fontsize=13, fontweight="bold", color=theme.INK, x=0.02, ha="left")
    _add_watermark(fig)
    fig.tight_layout(rect=(0, 0.015, 1, 0.96))
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    return out_path


def plot_compare_combine_cdf(
    rows,
    out_path: str = "out/compare_combine.png",
    title: str | None = None,
) -> str:
    """跨游戏组合目标：叠加 CDF 对比 + 期望抽数柱状图。"""
    from gacha.analysis.compare import CombineComparisonRow, shared_money_per_pull_cny

    rows = [r for r in rows if isinstance(r, CombineComparisonRow) and r.dist is not None]
    if not rows:
        raise ValueError("需要至少一行带 dist 的 CombineComparisonRow")

    shared_cny = shared_money_per_pull_cny(rows)
    char_n, weap_n = rows[0].char_copies, rows[0].weap_copies
    if title is None:
        title = f"Cross-game combine: {char_n} char + {weap_n} weapon copies"

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig, (ax_cdf, ax_bar) = plt.subplots(1, 2, figsize=(13, 5.5))

    max_x = 0
    for i, r in enumerate(rows):
        dist = r.dist
        assert dist is not None
        p99 = metrics.quantile(dist, 0.99)
        cap = min(len(dist.pmf), (p99 if p99 > 0 else len(dist.pmf)) + 20)
        n = np.arange(cap)
        cdf = np.cumsum(dist.pmf[:cap])
        color = theme.game_color(r.game_key, i)
        label = r.game_key + ("*" if r.char_only else "")
        ax_cdf.plot(n, cdf, color=color, lw=2.2, label=label)
        max_x = max(max_x, cap - 1)

    ax_cdf.axhline(0.5, color="#C5CCD6", ls=":", lw=1.0)
    ax_cdf.axhline(0.9, color="#C5CCD6", ls=":", lw=1.0)
    ax_cdf.set_xlabel("Total pulls", color=theme.INK)
    ax_cdf.set_ylabel("Cumulative success probability", color=theme.INK)
    ax_cdf.set_title("Combined target CDF overlay", fontsize=11, color=theme.INK, loc="left")
    ax_cdf.set_ylim(0, 1.02)
    ax_cdf.set_xlim(0, max_x)
    ax_cdf.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=0))
    ax_cdf.legend(loc="lower right", frameon=True, fontsize=9)
    _style_axes(ax_cdf)

    labels = [r.game_key for r in rows]
    exp = [r.exp_pulls for r in rows]
    colors = [theme.game_color(r.game_key, i) for i, r in enumerate(rows)]
    bars = ax_bar.bar(labels, exp, color=colors, edgecolor=theme.INK, width=0.55, alpha=0.85)
    for b, r in zip(bars, rows):
        if shared_cny is not None:
            ann = f"{r.exp_pulls:.0f}"
        else:
            ann = f"{r.exp_pulls:.0f}\n¥{r.exp_money_cny:.0f}"
        ax_bar.annotate(ann, (b.get_x() + b.get_width() / 2, r.exp_pulls),
                        ha="center", va="bottom", fontsize=9, color=theme.INK)
    ax_bar.set_title("Expected pulls (lower = cheaper)", fontsize=11, color=theme.INK, loc="left")
    ax_bar.set_ylabel("Expected pulls")
    ax_bar.set_ylim(0, max(exp) * 1.25 if exp else 1)
    _style_axes(ax_bar)

    fig.suptitle(title, fontsize=13, fontweight="bold", color=theme.INK, x=0.02, ha="left")
    if any(r.char_only for r in rows):
        fig.text(0.02, 0.01, "* = weapon pool unavailable, character-only",
                 fontsize=8, color=theme.MUTED)
    _add_watermark(fig)
    fig.tight_layout(rect=(0, 0.04, 1, 0.96))
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    return out_path
