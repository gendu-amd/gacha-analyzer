"""分布可视化：PMF + CDF 双图，标注关键分位与预算线。"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import PercentFormatter  # noqa: E402

from gacha.analysis import metrics  # noqa: E402
from gacha.engine.base import PullDistribution  # noqa: E402
from gacha.viz import figdata, theme  # noqa: E402

theme.apply_matplotlib_theme()


def _style_axes(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(colors=theme.MUTED, labelsize=9)
    ax.grid(axis="x", visible=False)


def _tick_label(ax, x, text, color):
    """Short categorical marker label pinned just above the axis top (declutter)."""
    ax.annotate(
        text, xy=(x, 1.0), xycoords=("data", "axes fraction"),
        xytext=(0, 3), textcoords="offset points",
        color=color, fontsize=8.5, fontweight="bold", va="bottom", ha="center",
    )


def _stat_caption(ax, lines: list[tuple[str, str]]) -> None:
    """Compact top-right caption box: the single source for the headline numbers.

    `lines` is a list of (text, color); the vertical guide lines stay label-light
    so each number appears exactly once.
    """
    y = 0.95
    for text, color in lines:
        ax.text(0.985, y, text, transform=ax.transAxes, ha="right", va="top",
                fontsize=9, fontweight="bold", color=color)
        y -= 0.11


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
    d = figdata.dist_plot_data(dist, max_pulls=max_pulls, pad=0)
    n, pmf, c = d.n, d.pmf, d.cdf
    p50, p90, exp = d.p50, d.p90, d.exp
    ymax = d.ymax

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(11, 7.4), sharex=True,
        gridspec_kw={"height_ratios": [1.15, 1], "hspace": 0.16},
    )

    # ---- Top: distribution shape. One conclusion = "where the mass sits". ----
    ax1.fill_between(n, pmf, color=theme.BLUE_FILL, alpha=0.55, linewidth=0)
    ax1.plot(n, pmf, color=theme.BLUE, lw=1.8)
    # Median is the actionable "typical" marker; mean is a faint reference only.
    ax1.axvline(exp, color=theme.AMBER, ls="--", lw=1.2, alpha=0.55)
    _tick_label(ax1, exp, "mean", theme.AMBER)
    if 0 <= p50 < len(pmf):
        ax1.axvline(p50, color=theme.GREEN, ls=":", lw=1.8)
        _tick_label(ax1, p50, "P50", theme.GREEN)
    # Headline numbers live in one compact caption (single source, no line-label dup).
    # Two-space gaps are intentional visual padding to loosely align the value column.
    _stat_caption(ax1, [
        (f"mean  {exp:.0f}", theme.AMBER),
        (f"P50   {p50}", theme.GREEN),
        (f"P90   {p90}", theme.RED),
    ])
    ax1.set_ylim(0, ymax * 1.22)
    ax1.set_ylabel("Probability per pull", color=theme.INK, fontsize=10)
    ax1.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=1))
    ax1.grid(axis="y", color=theme.GRID, lw=0.8)
    _style_axes(ax1)

    full_title = title if not subtitle else f"{title}\n{subtitle}"
    ax1.set_title(full_title, color=theme.INK, fontsize=13, fontweight="bold",
                  loc="left", pad=16)

    # ---- Bottom: the decision panel. One conclusion = "is my budget enough?". ----
    ax2.fill_between(n, c, color=theme.BLUE_FILL, alpha=0.28, linewidth=0)
    ax2.plot(n, c, color=theme.BLUE, lw=2.4)
    for lvl in (0.5, 0.9):
        ax2.axhline(lvl, color="#D5DBE4", ls=":", lw=1.0)
    if 0 <= p90 < len(c):
        ax2.axvline(p90, color=theme.RED, ls="--", lw=1.4, alpha=0.8)
        _tick_label(ax2, p90, "P90 safety net", theme.RED)
    if budget is not None and budget >= 0:
        prob = metrics.prob_within(dist, budget)
        bx = min(budget, len(c) - 1)
        ax2.axvline(budget, color=theme.PURPLE, ls="-.", lw=1.8)
        ax2.plot([budget], [c[bx]], "o", color=theme.PURPLE, ms=8, zorder=5)
        # Offset the callout up-left so it never sits on top of the guide line.
        ax2.annotate(
            f"budget {budget} → {prob:.0%}", xy=(budget, c[bx]),
            xytext=(-10, 18), textcoords="offset points",
            color=theme.PURPLE, fontsize=9, fontweight="bold", ha="right", va="bottom",
        )
    ax2.set_ylim(0, 1.04)
    ax2.set_ylabel("Chance of success", color=theme.INK, fontsize=10)
    ax2.set_xlabel("Number of pulls", color=theme.INK, fontsize=10)
    ax2.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=0))
    ax2.set_xlim(0, len(pmf) - 1)
    ax2.grid(axis="y", color=theme.GRID, lw=0.8)
    _style_axes(ax2)

    _add_watermark(fig)
    fig.tight_layout(rect=(0, 0.015, 1, 1))
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    return out_path


def plot_cost_grid(grid, out_path: str = "out/grid.png",
                   show_money: bool = True, title: str | None = None) -> str:
    """角色重复×武器重复 成本热力图：颜色=期望抽数，格内标注 抽数(/¥)。

    标签按游戏切换（英文，避免无 CJK 字体环境下 PNG 乱码）：
    原神=Constellation/Refinement、星铁=Eidolon/Superimposition、绝区零=Mindscape/Superimposition。
    """
    d = figdata.grid_plot_data(grid)
    exp, money = d.exp, d.money
    rows = d.const_labels
    cols = d.refine_labels

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    h = 0.7 * len(rows) + 1.8
    w = 1.5 * len(cols) + 1.5
    fig, ax = plt.subplots(figsize=(w, h))
    im = ax.imshow(exp, cmap=theme.heatmap_cmap(), aspect="auto")

    ax.set_xticks(range(len(cols)), labels=cols)
    ax.set_yticks(range(len(rows)), labels=rows)
    ax.set_xlabel(f"{d.refine_noun_en} ({d.refine_prefix}0 = no weapon)", color=theme.INK)
    ax.set_ylabel(d.const_noun_en, color=theme.INK)
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)

    vmax = d.vmax
    for i in range(len(rows)):
        for j in range(len(cols)):
            txt = f"{exp[i, j]:.0f}"
            if show_money:
                txt += f"\n¥{money[i, j]:.0f}"
            # White text only on the darkest (red) cells; ink elsewhere for contrast.
            color = "white" if exp[i, j] > theme.HEATMAP_WHITE_TEXT_THRESHOLD * vmax else theme.INK
            ax.text(j, i, txt, ha="center", va="center", fontsize=8.5, color=color)

    cbar = fig.colorbar(im, ax=ax, shrink=0.85)
    cbar.set_label("Expected pulls", color=theme.INK)
    ax.set_title(title or f"{grid.game_key}: {d.const_noun_en}×{d.refine_noun_en} "
                 f"cost grid (expected pulls / CNY)",
                 color=theme.INK, fontsize=13, fontweight="bold", loc="left", pad=10)
    _add_watermark(fig)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    return out_path


def plot_comparison(rows, out_path: str = "out/compare.png",
                    title: str = "Cross-game comparison (per featured 5-star)") -> str:
    """跨游戏比对：左轴期望抽数（越低越划算），右图每月白嫖可得限定数。"""
    d = figdata.comparison_data(rows)
    labels = d.game_keys
    exp = d.exp_pulls
    free = d.free_featured_per_month
    shared_cny = d.shared_cny
    colors = d.colors

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    bars = ax1.bar(labels, exp, color=colors, edgecolor=theme.INK, width=0.6, alpha=0.85)
    for b, e, r in zip(bars, exp, d.rows):
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
    if shared_cny is not None:
        fig.text(0.02, 0.005, f"CNY @ ¥{shared_cny:.0f}/pull (shared across games)",
                 fontsize=8, color=theme.MUTED, ha="left", va="bottom")
    _add_watermark(fig)
    fig.tight_layout(rect=(0, 0.03, 1, 0.96))
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    return out_path


def plot_compare_combine_cdf(
    rows,
    out_path: str = "out/compare_combine.png",
    title: str | None = None,
) -> str:
    """跨游戏组合目标：叠加 CDF 对比 + 期望抽数柱状图。"""
    d = figdata.combine_cdf_data(rows)
    shared_cny = d.shared_cny
    char_n, weap_n = d.char_copies, d.weap_copies
    if title is None:
        title = f"Cross-game combine: {char_n} char + {weap_n} weapon copies"

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig, (ax_cdf, ax_bar) = plt.subplots(1, 2, figsize=(13, 5.5))

    for s in d.series:
        label = s.game_key + ("*" if s.char_only else "")
        ax_cdf.plot(s.n, s.cdf, color=s.color, lw=2.2, label=label)
    max_x = d.max_x

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

    labels = [s.game_key for s in d.series]
    exp = [s.exp_pulls for s in d.series]
    colors = [s.color for s in d.series]
    bars = ax_bar.bar(labels, exp, color=colors, edgecolor=theme.INK, width=0.55, alpha=0.85)
    for b, s in zip(bars, d.series):
        if shared_cny is not None:
            ann = f"{s.exp_pulls:.0f}"
        else:
            ann = f"{s.exp_pulls:.0f}\n¥{s.exp_money_cny:.0f}"
        ax_bar.annotate(ann, (b.get_x() + b.get_width() / 2, s.exp_pulls),
                        ha="center", va="bottom", fontsize=9, color=theme.INK)
    ax_bar.set_title("Expected pulls (lower = cheaper)", fontsize=11, color=theme.INK, loc="left")
    ax_bar.set_ylabel("Expected pulls")
    ax_bar.set_ylim(0, max(exp) * 1.25 if exp else 1)
    _style_axes(ax_bar)

    fig.suptitle(title, fontsize=13, fontweight="bold", color=theme.INK, x=0.02, ha="left")
    if any(s.char_only for s in d.series):
        fig.text(0.02, 0.01, "* = weapon pool unavailable, character-only",
                 fontsize=8, color=theme.MUTED)
    _add_watermark(fig)
    fig.tight_layout(rect=(0, 0.04, 1, 0.96))
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    return out_path
