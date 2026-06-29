"""终端表格格式化（compare / grid 等 CLI 输出）。"""

from __future__ import annotations

from gacha.analysis.compare import ComparisonRow, CombineComparisonRow, shared_money_per_pull_cny
from gacha.analysis.grid import CostGrid
from gacha.viz.text_width import format_row, ljust_display


def format_compare_table(rows: list[ComparisonRow]) -> str:
    """跨游戏比对结果 → 对齐文本表（CJK 列宽正确）。"""
    if not rows:
        return ""
    shared_cny = shared_money_per_pull_cny(rows)
    lines: list[str] = []

    col_game, col_banner = 8, 14
    for r in rows:
        col_game = max(col_game, len(r.game_name) + 2)
        col_banner = max(col_banner, len(r.banner_name) + 2)

    headers = ["游戏", "卡池", "期望抽数", "期望货币", "P50", "P90", "白嫖/月", "相对成本"]
    widths = [col_game, col_banner, 9, 10, 6, 6, 10, 9]
    aligns = ["left", "left", "right", "right", "right", "right", "right", "right"]
    lines.append(format_row(headers, widths, aligns))
    lines.append("-" * sum(widths))

    for r in rows:
        cells = [
            r.game_name,
            r.banner_name,
            f"{r.exp_pulls:.1f}",
            f"{r.exp_currency:.0f}",
            str(r.p50),
            str(r.p90),
            f"{r.free_featured_per_month:.2f}",
            f"{r.relative_cost:.2f}",
        ]
        lines.append(format_row(cells, widths, aligns))

    if shared_cny is not None:
        money_note = f"折人民币统一按 ¥{shared_cny:.0f}/抽（三游相同，不重复列）"
        lines.append(ljust_display(money_note, sum(widths)))
    else:
        money_header = "折人民币"
        money_w = 10
        lines.append("")
        lines.append(format_row(["游戏", money_header], [col_game, money_w], ["left", "right"]))
        lines.append("-" * (col_game + money_w))
        for r in rows:
            lines.append(format_row(
                [r.game_name, f"¥{r.exp_money_cny:.0f}"],
                [col_game, money_w],
                ["left", "right"],
            ))

    return "\n".join(lines)


def format_grid_table(grid: CostGrid) -> str:
    """角色重复×武器重复成本网格 → 对齐文本表（术语随游戏切换）。"""
    cols = grid.refine_labels()
    corner = f"{grid.terms.const_noun}\\{grid.terms.refine_noun}"
    col_w = 16
    header_cells = [corner] + cols
    widths = [10] + [col_w] * len(cols)
    aligns = ["left"] + ["right"] * len(cols)
    lines = [format_row(header_cells, widths, aligns), "-" * sum(widths)]
    for ci, clabel in enumerate(grid.const_labels()):
        cells = [clabel] + [
            f"{grid.exp_pulls[ci][wi]:.0f}/¥{grid.money_cny[ci][wi]:.0f}"
            for wi in range(len(cols))
        ]
        lines.append(format_row(cells, widths, aligns))
    return "\n".join(lines)


def format_combine_compare_table(rows: list[CombineComparisonRow]) -> str:
    """跨游戏组合目标比对 → 对齐文本表。"""
    if not rows:
        return ""
    shared_cny = shared_money_per_pull_cny(rows)
    col_game = max(8, max(len(r.game_name) + 2 for r in rows))
    headers = ["游戏", "角色拷贝", "武器拷贝", "期望抽数", "期望货币", "P50", "P90", "相对成本"]
    widths = [col_game, 8, 8, 9, 10, 6, 6, 9]
    aligns = ["left"] + ["right"] * 7
    lines = [format_row(headers, widths, aligns), "-" * sum(widths)]
    for r in rows:
        weap = "—" if r.char_only else str(r.weap_copies)
        note = " *" if r.char_only else ""
        lines.append(format_row([
            r.game_name + note,
            str(r.char_copies),
            weap,
            f"{r.exp_pulls:.1f}",
            f"{r.exp_currency:.0f}",
            str(r.p50),
            str(r.p90),
            f"{r.relative_cost:.2f}",
        ], widths, aligns))
    if shared_cny is not None:
        lines.append(ljust_display(f"折人民币统一按 ¥{shared_cny:.0f}/抽", sum(widths)))
    else:
        lines.append("")
        lines.append(format_row(["游戏", "折人民币"], [col_game, 10], ["left", "right"]))
        lines.append("-" * (col_game + 10))
        for r in rows:
            lines.append(format_row([r.game_name, f"¥{r.exp_money_cny:.0f}"],
                                    [col_game, 10], ["left", "right"]))
    if any(r.char_only for r in rows):
        lines.append(ljust_display("* 无武器池，仅角色部分", sum(widths)))
    return "\n".join(lines)
