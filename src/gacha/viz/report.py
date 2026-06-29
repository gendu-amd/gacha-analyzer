"""交互式 HTML 报告（Plotly）.

一份自包含、可交互、中文正常、双击即开的 HTML：汇总核心指标 + PMF/CDF 曲线 +
预算把握表 +（可选）命座×精炼热力图 + 跨游戏比对。Plotly.js 内联，无需联网/服务器。
"""

from __future__ import annotations

import html
import os

import plotly.graph_objects as go
from plotly.offline import get_plotlyjs
from plotly.subplots import make_subplots

from gacha.analysis import budget as budget_mod
from gacha.analysis import metrics
from gacha.engine.base import BANNER_CHARACTER, BANNER_WEAPON
from gacha.viz import figdata, theme


def _apply_plotly(fig: go.Figure, height: int = 620) -> go.Figure:
    fig.update_layout(**theme.plotly_template(), height=height, showlegend=False)
    return fig


def pmf_cdf_figure(dist, title: str, budget: int | None = None) -> go.Figure:
    d = figdata.dist_plot_data(dist)
    n, pmf, cdf = d.n, d.pmf, d.cdf
    cap, exp, p50, p90 = d.cap, d.exp, d.p50, d.p90

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        subplot_titles=("每抽达成概率 (PMF)", "累计达成概率 (CDF)"))
    fig.add_trace(go.Scatter(x=n, y=pmf, fill="tozeroy", mode="lines",
                            line=dict(color=theme.BLUE, width=2), name="PMF",
                            hovertemplate="第%{x}抽: %{y:.3%}<extra></extra>"), row=1, col=1)
    fig.add_trace(go.Scatter(x=n, y=cdf, fill="tozeroy", mode="lines",
                            line=dict(color=theme.BLUE, width=3), name="CDF",
                            hovertemplate="%{x}抽以内: %{y:.1%}<extra></extra>"), row=2, col=1)

    fig.add_vline(x=exp, line=dict(color=theme.AMBER, dash="dash"), row=1, col=1,
                 annotation_text=f"期望 {exp:.0f}", annotation_position="top")
    if 0 <= p50:
        fig.add_vline(x=p50, line=dict(color=theme.GREEN, dash="dot"), row=1, col=1,
                     annotation_text=f"P50 {p50}", annotation_position="top left")
    fig.add_hline(y=0.9, line=dict(color=theme.GRID, dash="dot"), row=2, col=1)
    if 0 <= p90 <= cap:
        fig.add_vline(x=p90, line=dict(color=theme.RED, dash="dash"), row=2, col=1,
                     annotation_text=f"P90 {p90}", annotation_position="bottom right")
    if budget is not None and 0 <= budget <= cap:
        prob = metrics.prob_within(dist, budget)
        fig.add_vline(x=budget, line=dict(color=theme.PURPLE, dash="dashdot"), row=2, col=1,
                     annotation_text=f"预算{budget}→{prob:.0%}", annotation_position="top right")

    fig.update_yaxes(tickformat=".1%", row=1, col=1)
    fig.update_yaxes(tickformat=".0%", row=2, col=1, range=[0, 1.02])
    fig.update_xaxes(title_text="抽数", row=2, col=1)
    return _apply_plotly(fig, height=620).update_layout(title=dict(text=title, x=0))


def grid_figure(grid) -> go.Figure:
    d = figdata.grid_plot_data(grid)
    z, money = d.exp, d.money
    text = [[f"{z[i, j]:.0f}抽<br>¥{money[i, j]:.0f}" for j in range(z.shape[1])]
            for i in range(z.shape[0])]
    custom = [[f"{d.const_labels[i]}_{d.refine_labels[j]}"
               for j in range(z.shape[1])] for i in range(z.shape[0])]
    fig = go.Figure(go.Heatmap(
        z=z, x=d.refine_labels, y=d.const_labels,
        text=text, texttemplate="%{text}", textfont=dict(size=11),
        customdata=custom,
        colorscale=theme.HEATMAP_SCALE_PLOTLY,
        colorbar=dict(title="期望抽数", thickness=14),
        hovertemplate="%{y} · %{x}<br>期望 %{z:.0f} 抽<extra></extra>",
    ))
    layout = theme.plotly_layout_defaults()
    layout.update(height=480, margin=dict(l=60, r=30, t=70, b=50))
    fig.update_layout(
        title=f"{d.game_name} 命座×精炼 成本网格（期望抽数/人民币）",
        xaxis_title="武器精炼 (R0=不要武器)", yaxis_title="命座",
        yaxis=dict(autorange="reversed"),
        **layout,
    )
    return fig


def comparison_figure(rows) -> go.Figure:
    d = figdata.comparison_data(rows)
    labels = d.game_names
    shared_cny = d.shared_cny
    colors = d.colors
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.12,
                       subplot_titles=("每限定期望抽数（越低越划算）",
                                       "每月白嫖可得限定数（越高越慷慨）"))
    if shared_cny is not None:
        bar_text = [f"{e:.0f}抽" for e in d.exp_pulls]
        subtitle = f"折人民币统一 ¥{shared_cny:.0f}/抽"
    else:
        bar_text = [f"{e:.0f}抽<br>¥{m:.0f}"
                    for e, m in zip(d.exp_pulls, d.exp_money_cny)]
        subtitle = None
    fig.add_trace(go.Bar(x=labels, y=d.exp_pulls, marker_color=colors,
                        text=bar_text, textposition="outside"), row=1, col=1)
    fig.add_trace(go.Bar(x=labels, y=d.free_featured_per_month,
                        marker_color=theme.GREEN_FILL,
                        text=[f"{f:.2f}" for f in d.free_featured_per_month],
                        textposition="outside"), row=1, col=2)
    title = "跨游戏比对（抽 1 个限定，从零）"
    if subtitle:
        title += f"<br><sup>{subtitle}</sup>"
    return _apply_plotly(fig, height=440).update_layout(title=dict(text=title, x=0))


def combine_comparison_figure(rows) -> go.Figure:
    """跨游戏组合目标：叠加 CDF + 期望柱状图。"""
    d = figdata.combine_cdf_data(rows)
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.10,
                       subplot_titles=("联合目标 CDF 叠加", "期望抽数对比"))
    for s in d.series:
        fig.add_trace(go.Scatter(
            x=s.n, y=s.cdf, mode="lines", name=s.game_name,
            line=dict(color=s.color, width=2.5),
            hovertemplate=f"{s.game_name}<br>%{{x}}抽: %{{y:.1%}}<extra></extra>",
        ), row=1, col=1)
    max_x = d.max_x

    labels = [s.game_name for s in d.series]
    colors = [s.color for s in d.series]
    fig.add_trace(go.Bar(
        x=labels, y=[s.exp_pulls for s in d.series], marker_color=colors,
        text=[f"{s.exp_pulls:.0f}抽" for s in d.series], textposition="outside",
    ), row=1, col=2)
    fig.update_xaxes(range=[0, max_x], row=1, col=1)
    fig.update_yaxes(tickformat=".0%", range=[0, 1.02], row=1, col=1)
    char_n, weap_n = d.char_copies, d.weap_copies
    title = f"跨游戏组合比对（{char_n} 角色 + {weap_n} 武器拷贝）"
    return _apply_plotly(fig, height=460).update_layout(
        title=dict(text=title, x=0), showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )


def _fig_div(fig: go.Figure) -> str:
    return fig.to_html(full_html=False, include_plotlyjs=False,
                       config={"displayModeBar": False, "responsive": True})


def metrics_cards_html(game, dist, target_desc: str, budget: int | None) -> str:
    s = metrics.summary(dist)
    cur = game.currency_name
    cards = [
        ("期望抽数", f"{s['expectation']:.0f} 抽"),
        ("折合原石", f"{budget_mod.pulls_to_currency(game, s['expectation']):.0f} {cur}"),
        ("折合人民币", f"¥{budget_mod.pulls_to_money_cny(game, s['expectation']):.0f}"),
        ("中位数 P50", f"{s['p50']} 抽"),
        ("安全垫 P90", f"{s['p90']} 抽"),
        ("P99", f"{s['p99']} 抽"),
        ("Cashback(十连)", f"{s['cashback_10pull']:.1f} 抽"),
        ("CVaR@90%", f"{s['cvar_p90']:.0f} 抽"),
    ]
    items = "".join(
        f'<div class="card"><div class="v">{html.escape(v)}</div>'
        f'<div class="k">{html.escape(k)}</div></div>' for k, v in cards
    )
    rows = ""
    for conf in (0.5, 0.9, 0.99):
        r = budget_mod.cost_for_confidence(game, dist, conf)
        if r.pulls >= 0:
            rows += (f"<tr><td>{conf:.0%} 把握</td><td>{r.pulls} 抽</td>"
                     f"<td>{r.currency:.0f} {cur}</td><td>¥{r.money_cny:.0f}</td></tr>")
    budget_html = ""
    if budget is not None:
        r = budget_mod.budget_outlook(game, dist, budget)
        budget_html = (f'<p class="budget">预算 <b>{r.pulls} 抽</b>'
                       f'（{r.currency:.0f} {cur} / ≈¥{r.money_cny:.0f}）'
                       f' → 达成把握 <b>{r.probability:.1%}</b>，'
                       f'比 {metrics.luck_percentile(dist, r.pulls):.0%} 的人更欧。</p>')
    return (f'<p class="desc">{html.escape(target_desc)}</p>'
            f'<div class="cards">{items}</div>{budget_html}'
            f'<table class="tbl"><tr><th>把握</th><th>抽数</th><th>货币</th><th>人民币</th></tr>'
            f'{rows}</table>')


_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<script type="text/javascript">{plotlyjs}</script>
<style>
 :root {{
   --blue: {blue}; --green: {green}; --ink: {ink}; --muted: {muted};
   --bg: {bg_page}; --card: white; --accent: {bg_accent}; --border: {border};
 }}
 body{{font-family:{font_sans}; margin:0; background:var(--bg); color:var(--ink);}}
 .wrap{{max-width:1080px;margin:0 auto;padding:24px 20px 40px;}}
 header{{margin-bottom:24px;padding-bottom:16px;border-bottom:2px solid var(--blue);}}
 h1{{font-size:24px;margin:0 0 6px;font-weight:700;letter-spacing:-0.02em;}}
 .sub{{color:var(--muted);font-size:14px;line-height:1.5;}}
 section{{background:var(--card);border-radius:14px;padding:22px 26px;margin:18px 0;
   box-shadow:0 2px 8px rgba(0,0,0,.05);border:1px solid var(--border);}}
 h2{{font-size:17px;margin:0 0 16px;color:var(--blue);font-weight:600;
   padding-bottom:8px;border-bottom:1px solid var(--border);}}
 .desc{{color:#374151;margin:0 0 14px;line-height:1.55;}}
 .cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));
   gap:12px;margin-bottom:16px;}}
 .card{{background:var(--accent);border:1px solid var(--border);
   border-radius:12px;padding:14px 12px;text-align:center;
   transition:box-shadow .15s;}}
 .card:hover{{box-shadow:0 2px 6px rgba(61,111,229,.12);}}
 .card .v{{font-size:21px;font-weight:700;color:var(--ink);}}
 .card .k{{font-size:12px;color:var(--muted);margin-top:5px;}}
 .budget{{background:#F3EEFB;border-radius:10px;padding:12px 16px;color:#5B3A9E;
   line-height:1.5;margin:12px 0;}}
 table.tbl{{border-collapse:collapse;width:100%;font-size:14px;margin-top:10px;}}
 table.tbl th,table.tbl td{{border:1px solid var(--border);padding:8px 12px;text-align:left;}}
 table.tbl th{{background:var(--accent);font-weight:600;}}
 table.tbl tr:nth-child(even){{background:#FAFBFD;}}
 .pmf-anchor{{scroll-margin-top:20px;padding-top:8px;}}
 footer{{color:#9AA3B2;font-size:12px;text-align:center;padding:24px 0 8px;}}
</style></head>
<body><div class="wrap">
<header><h1>{title}</h1><div class="sub">{subtitle}</div></header>
{sections}
</div><footer>gacha · 基于 GGanalysis · 结果为估计值，与厂商无关</footer></body></html>
"""


def build_report(out_path: str, title: str, subtitle: str,
                 sections: list[tuple[str, str]]) -> str:
    body = "".join(f"<section><h2>{html.escape(h)}</h2>{c}</section>"
                   for h, c in sections)
    out = _TEMPLATE.format(
        title=html.escape(title), subtitle=html.escape(subtitle),
        plotlyjs=get_plotlyjs(), sections=body,
        blue=theme.BLUE, green=theme.GREEN, ink=theme.INK, muted=theme.MUTED,
        bg_page=theme.BG_PAGE, bg_accent=theme.BG_ACCENT, border=theme.GRID,
        font_sans=", ".join(f'"{f}"' for f in theme.FONT_SANS[:6]),
    )
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out)
    return out_path


def generate_report(out_path, game, state, target, solver, budget=None,
                    include_grid=True, include_compare=True,
                    grid_cell_codes: list[str] | None = None) -> str:
    """为给定目标生成综合 HTML 报告（指标 + PMF/CDF + 预算 + 网格 + 跨游戏比对）。"""
    from gacha.analysis import compare as compare_mod
    from gacha.analysis import grid as grid_mod

    banner = game.banner(target.banner)
    dist = solver.solve(game, state, target, 0)
    target_desc = (f"目标：{target.copies} 个 UP {banner.top_rarity_label}（{banner.name}）"
                   f"；当前：垫 {state.item_pity} 抽，"
                   f"{'大保底' if state.is_guaranteed else '小保底'}"
                   f"，连歪 {state.radiance_losses}")

    sections = [(
        "核心指标与分布",
        metrics_cards_html(game, dist, target_desc, budget)
        + _fig_div(pmf_cdf_figure(dist, f"{game.name} · {banner.name}", budget)),
    )]

    if include_grid and BANNER_WEAPON in game.banners:
        g = grid_mod.cost_grid(solver, game)
        grid_html = _fig_div(grid_figure(g))
        if grid_cell_codes:
            for code in grid_cell_codes:
                const, refine = grid_mod.parse_cell_code(code)
                cell_dist = grid_mod.cell_distribution(solver, game, const, refine)
                label = grid_mod.cell_label(game.key, const, refine)
                anchor = f"pmf-{label}"
                grid_html += (
                    f'<div id="{anchor}" class="pmf-anchor">'
                    f'<h3 style="font-size:14px;color:{theme.MUTED};margin:20px 0 8px">'
                    f'{label} 分布详情</h3>'
                    + _fig_div(pmf_cdf_figure(cell_dist, f"{game.name} · {label}"))
                    + '</div>'
                )
        sections.append(("命座×精炼 成本网格", grid_html))

    if include_compare:
        rows = compare_mod.compare_games(solver, banner=BANNER_CHARACTER)
        if len(rows) >= 2:
            sections.append(("跨游戏比对", _fig_div(comparison_figure(rows))))

    title = f"{game.name} 抽卡分析报告"
    subtitle = target_desc
    return build_report(out_path, title, subtitle, sections)
