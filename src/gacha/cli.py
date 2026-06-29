"""命令行入口：原神角色/武器池 + 组合目标 + UIGF 历史。

示例：
  gacha games
  gacha analyze --copies 1 --budget 90 --plot out/up5.png --mc
  gacha analyze --banner weapon --copies 1 --guaranteed
  gacha combine --char-copies 1 --weap-copies 1 --budget 200
  gacha history --file mydata.json
"""

from __future__ import annotations

import argparse
import os
import sys

from gacha.analysis import budget as budget_mod
from gacha.analysis import combine as combine_mod
from gacha.analysis import compare as compare_mod
from gacha.analysis import grid as grid_mod
from gacha.analysis import metrics
from gacha.engine.base import BANNER_CHARACTER, BANNER_WEAPON, PullState, Target
from gacha.engine.gg_adapter import GGanalysisSolver
from gacha.games.registry import get_game, list_games

SOLVER = GGanalysisSolver()


def _fmt_pulls(p: int) -> str:
    return "覆盖范围内无法达成" if p < 0 else f"{p} 抽"


def _print_core_metrics(game, dist, indent: str = "  ") -> dict:
    s = metrics.summary(dist)
    cur = game.currency_name
    print(f"{indent}期望抽数 E[N]      : {s['expectation']:.2f} 抽"
          f"（≈ {budget_mod.pulls_to_currency(game, s['expectation']):.0f} {cur}"
          f"，≈ ¥{budget_mod.pulls_to_money_cny(game, s['expectation']):.0f}）")
    print(f"{indent}标准差 σ           : {s['std']:.2f} 抽")
    print(f"{indent}中位数 P50         : {_fmt_pulls(s['p50'])}")
    print(f"{indent}P90               : {_fmt_pulls(s['p90'])}（安全垫）")
    print(f"{indent}P99               : {_fmt_pulls(s['p99'])}")
    print(f"{indent}Cashback(十连)     : {s['cashback_10pull']:.2f} 抽")
    print(f"{indent}CVaR@90%           : {s['cvar_p90']:.2f} 抽")
    print(f"{indent}分布覆盖概率        : {s['total_mass']:.6f}")
    return s


def _print_budget_block(game, dist, budget):
    if budget is not None:
        r = budget_mod.budget_outlook(game, dist, budget)
        print(f"\n[看得懂] 预算 {r.pulls} 抽"
              f"（{r.currency:.0f} {game.currency_name} / ≈¥{r.money_cny:.0f}）"
              f" → 达成把握 {r.probability:.2%}")
        print(f"        运气分位：若 {r.pulls} 抽达成，你比 "
              f"{metrics.luck_percentile(dist, r.pulls):.1%} 的人更欧")
    for conf in (0.5, 0.9, 0.99):
        r = budget_mod.cost_for_confidence(game, dist, conf)
        if r.pulls < 0:
            print(f"        {conf:.0%} 把握：覆盖范围内无法达成")
        else:
            print(f"        {conf:.0%} 把握需 {r.pulls} 抽"
                  f"（{r.currency:.0f} {game.currency_name} / ≈¥{r.money_cny:.0f}）")


def _cmd_games(_args) -> int:
    print("已注册游戏：")
    for key in list_games():
        g = get_game(key)
        banners = "、".join(f"{b.name}({k})" for k, b in g.banners.items())
        print(f"  - {key}  {g.name}  | 货币:{g.currency_name} {g.currency_per_pull}/抽"
              f" ≈¥{g.money_per_pull_cny}/抽 | 池子: {banners}")
    return 0


def _cmd_analyze(args) -> int:
    game = get_game(args.game)
    banner = game.banner(args.banner)
    state = PullState(item_pity=args.pity, is_guaranteed=args.guaranteed,
                      radiance_losses=args.losses)
    target = Target(banner=args.banner, copies=args.copies)
    dist = SOLVER.solve(game, state, target, max_pulls=0)

    print(f"== {game.name} · {banner.name} ==")
    print(f"目标：{target.copies} 个 UP {banner.top_rarity_label}"
          f"  | 当前：垫 {state.item_pity} 抽，"
          f"{'大保底' if state.is_guaranteed else '小保底'}，连歪 {state.radiance_losses}")
    print("\n[算得准] 核心指标")
    s = _print_core_metrics(game, dist)
    _print_budget_block(game, dist, args.budget)

    if args.mc:
        mc_factory = banner.reference_mc_mechanism
        if mc_factory is None:
            print(f"\n[校验] reference-MC 跳过：{banner.name} 未配置 MC 校验"
                  f"（GGanalysis 主引擎已精确建模）")
        else:
            from gacha.engine.reference.mc import ReferenceMCSolver
            max_pulls = max(args.budget or 0, s["p99"] if s["p99"] > 0 else 0, 600)
            mc = ReferenceMCSolver(mc_factory(), runs=args.mc_runs).solve(
                game, state, target, max_pulls)
            gg_exp, mc_exp = s["expectation"], metrics.expectation(mc)
            diff = abs(mc_exp - gg_exp) / gg_exp if gg_exp else float("nan")
            print(f"\n[校验] reference-MC({args.mc_runs} 次) E[N]={mc_exp:.2f}"
                  f" vs GGanalysis {gg_exp:.2f} 相对误差 {diff:.3%}")

    if args.plot:
        from gacha.viz.plots import plot_pmf_cdf
        cap = max(args.budget or 0, s["p99"] if s["p99"] > 0 else dist.max_pulls)
        title = (f"{args.game.capitalize()} · {args.banner} banner"
                 f"  |  target: {target.copies}x UP {banner.top_rarity_label}")
        subtitle = (f"start: pity {state.item_pity}, "
                    f"{'guaranteed' if state.is_guaranteed else '50/50'}")
        path = plot_pmf_cdf(dist, title=title, subtitle=subtitle, out_path=args.plot,
                            max_pulls=min(cap + 20, dist.max_pulls), budget=args.budget)
        print(f"\n[看得懂] 图已保存：{path}")
    return 0


def _cmd_combine(args) -> int:
    game = get_game(args.game)
    items = []
    desc = []
    if args.char_copies > 0:
        items.append((PullState(item_pity=args.char_pity,
                                is_guaranteed=args.char_guaranteed),
                      Target(BANNER_CHARACTER, args.char_copies)))
        desc.append(f"{args.char_copies}个UP角色5★(垫{args.char_pity},"
                    f"{'大保底' if args.char_guaranteed else '小保底'})")
    if args.weap_copies > 0:
        items.append((PullState(item_pity=args.weap_pity,
                                is_guaranteed=args.weap_guaranteed),
                      Target(BANNER_WEAPON, args.weap_copies)))
        desc.append(f"{args.weap_copies}把UP武器(垫{args.weap_pity},"
                    f"{'定轨' if args.weap_guaranteed else '无定轨'})")
    if not items:
        print("请至少指定 --char-copies 或 --weap-copies")
        return 2

    dist = combine_mod.combine_targets(game, SOLVER, items)
    print(f"== {game.name} · 组合目标 ==")
    print("目标：" + " + ".join(desc))
    print("\n[算得准] 组合后核心指标（角色与武器独立、抽数相加）")
    s = _print_core_metrics(game, dist)
    _print_budget_block(game, dist, args.budget)

    if args.plot:
        from gacha.viz.plots import plot_pmf_cdf
        cap = max(args.budget or 0, s["p99"] if s["p99"] > 0 else dist.max_pulls)
        path = plot_pmf_cdf(dist, title=f"{args.game.capitalize()} · combined target",
                            subtitle=" + ".join(desc), out_path=args.plot,
                            max_pulls=min(cap + 20, dist.max_pulls), budget=args.budget)
        print(f"\n[看得懂] 图已保存：{path}")
    return 0


def _cmd_history(args) -> int:
    from gacha.io.history import analyze_character_history
    from gacha.io.uigf import load_uigf

    uigf = load_uigf(args.file)
    archives = uigf.archives_for("genshin")
    if not archives:
        print(f"文件中未找到原神(hk4e)记录：{args.file}")
        return 1
    if args.uid:
        archives = [a for a in archives if a.uid == args.uid]
        if not archives:
            print(f"未找到 uid={args.uid}")
            return 1

    genshin = get_game("genshin")
    for arch in archives:
        h = analyze_character_history(arch, genshin)
        print(f"== 原神 角色活动祈愿 · uid {arch.uid} ==")
        print(f"  终身抽数        : {h.total_pulls}")
        print(f"  5★ 数量         : {h.five_star_count}")
        print(f"  平均出 5★ 抽数  : {h.average_5star_pity:.1f}")
        wr = h.fifty_fifty_winrate
        print(f"  50/50 胜率      : "
              f"{wr:.1%}（{h.fifty_fifty_wins}/{h.fifty_fifty_total}）"
              if h.fifty_fifty_total else "  50/50 胜率      : 无数据")
        print(f"  当前水位        : 垫 {h.current_pity} 抽，"
              f"{'大保底' if h.current_guaranteed else '小保底'}，连歪 {h.radiance_losses}")

        if args.predict:
            dist = SOLVER.solve(get_game("genshin"), h.state,
                                Target(BANNER_CHARACTER, args.predict), 0)
            print(f"\n  [预测] 基于当前水位，再抽 {args.predict} 个 UP 5★：")
            _print_core_metrics(get_game("genshin"), dist, indent="    ")
        print()
    return 0


def _cmd_compare(args) -> int:
    games = args.games.split(",") if args.games else None
    combine_mode = args.char_copies is not None or args.weap_copies is not None

    if combine_mode:
        char_c = args.char_copies if args.char_copies is not None else 1
        weap_c = args.weap_copies if args.weap_copies is not None else 0
        rows = compare_mod.compare_combine_games(
            SOLVER, char_copies=char_c, weap_copies=weap_c, game_keys=games,
        )
        if not rows:
            print("没有可比较的游戏（检查 --games）")
            return 1
        print(f"== 跨游戏组合比对 · {char_c} 角色 + {weap_c} 武器拷贝（从零）==")
        from gacha.viz.tables import format_combine_compare_table
        print(format_combine_compare_table(rows))
        cheapest = rows[0]
        print("\n最划算：", cheapest.game_name,
              f"（{cheapest.exp_pulls:.0f} 抽，相对成本 {cheapest.relative_cost:.2f}×）")
        if args.plot:
            from gacha.viz.plots import plot_compare_combine_cdf
            path = plot_compare_combine_cdf(rows, out_path=args.plot)
            print(f"\n[看得懂] 组合比对图已保存：{path}")
        print("注：组合目标假设角色池与武器池独立；详见 docs/RESEARCH.md §3。")
        return 0

    rows = compare_mod.compare_games(SOLVER, game_keys=games, banner=args.banner,
                                     copies=args.copies)
    if not rows:
        print("没有可比较的游戏（检查 --games / --banner）")
        return 1
    print(f"== 跨游戏比对 · {args.banner} 池 · 抽 {args.copies} 个限定（从零，含50/50）==")
    from gacha.viz.tables import format_compare_table
    print(format_compare_table(rows))
    shared = compare_mod.shared_money_per_pull_cny(rows)
    cheapest = rows[0]
    freest = max(rows, key=lambda r: r.free_featured_per_month)
    print("\n最划算：", cheapest.game_name,
          f"（{cheapest.exp_pulls:.0f} 抽/限定，相对成本 {cheapest.relative_cost:.2f}×）")
    print("白嫖最快：", freest.game_name,
          f"（≈{freest.free_featured_per_month:.2f} 限定/月，"
          f"{freest.free_pulls_per_month:.0f} 抽/月）")
    if shared is not None:
        print(f"注：三游单抽均为 ¥{shared:.0f}，人民币差异仅由期望抽数决定。")
    print("注：仅比限定同类池；货币与白嫖速率为社区近似口径；详见 docs/RESEARCH.md §3。")

    if args.plot:
        from gacha.viz.plots import plot_comparison
        path = plot_comparison(rows, out_path=args.plot)
        print(f"\n[看得懂] 比对图已保存：{path}")
    return 0


def _cmd_grid(args) -> int:
    game = get_game(args.game)
    char_state = PullState(item_pity=args.char_pity, is_guaranteed=args.char_guaranteed)
    weap_state = PullState(item_pity=args.weap_pity, is_guaranteed=args.weap_guaranteed)
    g = grid_mod.cost_grid(SOLVER, game, char_state, weap_state,
                           max_const=args.max_const, max_refine=args.max_refine)
    print(f"== {game.name} · 命座×精炼 成本网格（期望抽数 / 折人民币）==")
    print(f"角色起始：垫 {char_state.item_pity} 抽，"
          f"{'大保底' if char_state.is_guaranteed else '小保底'}"
          f" | 武器起始：垫 {weap_state.item_pity} 抽，"
          f"{'定轨' if weap_state.is_guaranteed else '无定轨'}")
    from gacha.viz.tables import format_grid_table
    print(format_grid_table(g))

    cells: list[str] = []
    if args.cells:
        if args.cells.strip().lower() == "all":
            cells = grid_mod.all_cell_codes(args.max_const, args.max_refine)
        else:
            cells = [c.strip() for c in args.cells.split(",") if c.strip()]

    if cells:
        from gacha.viz.plots import plot_pmf_cdf
        out_dir = args.cells_dir
        os.makedirs(out_dir, exist_ok=True)
        saved = []
        for code in cells:
            const, refine = grid_mod.parse_cell_code(code)
            if const > args.max_const or refine > args.max_refine:
                print(f"  跳过 {code}：超出网格范围 C0..C{args.max_const} R0..R{args.max_refine}")
                continue
            dist = grid_mod.cell_distribution(SOLVER, game, const, refine,
                                              char_state, weap_state)
            label = grid_mod.cell_label(game.key, const, refine)
            fname = f"{game.key}_{label}.png"
            out_path = os.path.join(out_dir, fname)
            s = metrics.summary(dist)
            subtitle = f"constellation × refinement cell {label}"
            from gacha.viz import theme
            if theme.pick_matplotlib_cjk_font():
                title = f"{game.name} · {label}"
            else:
                title = f"{game.key} · {label}"
            plot_pmf_cdf(dist, title=title, subtitle=subtitle,
                         out_path=out_path,
                         max_pulls=min(s["p99"] + 20 if s["p99"] > 0 else dist.max_pulls,
                                     dist.max_pulls))
            saved.append(out_path)
        print(f"\n[看得懂] 已导出 {len(saved)} 个单元格 PMF/CDF → {out_dir}/")
        for p in saved:
            print(f"  · {p}")

    if args.plot:
        from gacha.viz.plots import plot_cost_grid
        path = plot_cost_grid(g, out_path=args.plot,
                              title=f"{args.game}: cost grid (expected pulls / CNY)")
        print(f"\n[看得懂] 网格热力图已保存：{path}")
    return 0


def _cmd_report(args) -> int:
    from gacha.viz.report import generate_report

    game = get_game(args.game)
    state = PullState(item_pity=args.pity, is_guaranteed=args.guaranteed,
                      radiance_losses=args.losses)
    target = Target(banner=args.banner, copies=args.copies)
    path = generate_report(
        args.out, game, state, target, SOLVER, budget=args.budget,
        include_grid=not args.no_grid, include_compare=not args.no_compare,
        grid_cell_codes=(
            [c.strip() for c in args.grid_cells.split(",") if c.strip()]
            if args.grid_cells else None
        ),
    )
    print(f"[报告] 交互式 HTML 报告已生成：{path}")
    print("  用浏览器打开即可（自包含、可交互、中文正常）。")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="gacha", description="抽卡概率分析工具（基于 GGanalysis）")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("games", help="列出已注册游戏").set_defaults(func=_cmd_games)

    a = sub.add_parser("analyze", help="分析某目标的抽数分布与决策指标")
    a.add_argument("--game", default="genshin")
    a.add_argument("--banner", default=BANNER_CHARACTER, help="character / weapon")
    a.add_argument("--copies", type=int, default=1)
    a.add_argument("--pity", type=int, default=0)
    a.add_argument("--guaranteed", action="store_true")
    a.add_argument("--losses", type=int, default=0, help="捕获明光连歪 0~3（仅角色池）")
    a.add_argument("--budget", type=int, default=None)
    a.add_argument("--plot", default=None)
    a.add_argument("--mc", action="store_true")
    a.add_argument("--mc-runs", type=int, default=500_000)
    a.set_defaults(func=_cmd_analyze)

    c = sub.add_parser("combine", help="组合目标：角色 + 武器 联合期望")
    c.add_argument("--game", default="genshin")
    c.add_argument("--char-copies", type=int, default=1)
    c.add_argument("--char-pity", type=int, default=0)
    c.add_argument("--char-guaranteed", action="store_true")
    c.add_argument("--weap-copies", type=int, default=1)
    c.add_argument("--weap-pity", type=int, default=0)
    c.add_argument("--weap-guaranteed", action="store_true")
    c.add_argument("--budget", type=int, default=None)
    c.add_argument("--plot", default=None)
    c.set_defaults(func=_cmd_combine)

    h = sub.add_parser("history", help="导入 UIGF 文件，还原水位与历史统计")
    h.add_argument("--file", required=True, help="UIGF v4.x JSON 文件路径")
    h.add_argument("--uid", default=None)
    h.add_argument("--predict", type=int, default=None, help="基于当前水位预测再抽 N 个 UP")
    h.set_defaults(func=_cmd_history)

    cmp = sub.add_parser("compare", help="跨游戏归一化比对（期望抽数/花费/白嫖速率）")
    cmp.add_argument("--games", default=None, help="逗号分隔，如 genshin,hsr,zzz；默认全部")
    cmp.add_argument("--banner", default=BANNER_CHARACTER, help="比较的池子类型（单目标模式）")
    cmp.add_argument("--copies", type=int, default=1, help="单目标模式：限定拷贝数")
    cmp.add_argument("--char-copies", type=int, default=None,
                     help="组合模式：角色 UP 拷贝数（与 --weap-copies 联用）")
    cmp.add_argument("--weap-copies", type=int, default=None,
                     help="组合模式：武器 UP 拷贝数")
    cmp.add_argument("--plot", default=None)
    cmp.set_defaults(func=_cmd_compare)

    gr = sub.add_parser("grid", help="命座×精炼 成本网格（联合期望抽数/人民币）+ 热力图")
    gr.add_argument("--game", default="genshin")
    gr.add_argument("--max-const", type=int, default=6, help="最大命座（默认6=C0~C6）")
    gr.add_argument("--max-refine", type=int, default=5, help="最大精炼（默认5=R0~R5）")
    gr.add_argument("--char-pity", type=int, default=0)
    gr.add_argument("--char-guaranteed", action="store_true")
    gr.add_argument("--weap-pity", type=int, default=0)
    gr.add_argument("--weap-guaranteed", action="store_true")
    gr.add_argument("--plot", default=None, help="导出网格热力图 PNG")
    gr.add_argument("--cells", default=None,
                    help="导出单元格 PMF/CDF：'all' 表示全部，或逗号分隔如 00,01,21,65")
    gr.add_argument("--cells-dir", default="out/pmfs",
                    help="单元格 PMF/CDF 导出目录（默认 out/pmfs/）")
    gr.set_defaults(func=_cmd_grid)

    rp = sub.add_parser("report", help="生成交互式 HTML 报告（指标+分布+网格+跨游戏比对）")
    rp.add_argument("--game", default="genshin")
    rp.add_argument("--banner", default=BANNER_CHARACTER)
    rp.add_argument("--copies", type=int, default=1)
    rp.add_argument("--pity", type=int, default=0)
    rp.add_argument("--guaranteed", action="store_true")
    rp.add_argument("--losses", type=int, default=0)
    rp.add_argument("--budget", type=int, default=None)
    rp.add_argument("-o", "--out", default="out/report.html")
    rp.add_argument("--no-grid", action="store_true", help="不含命座×精炼网格")
    rp.add_argument("--no-compare", action="store_true", help="不含跨游戏比对")
    rp.add_argument("--grid-cells", default=None,
                    help="网格章节嵌入指定单元格 PMF，如 00,01,21,65")
    rp.set_defaults(func=_cmd_report)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv if argv is not None else sys.argv[1:])
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
