"""HTML 报告生成测试。"""

from gacha.engine.base import PullState, Target
from gacha.engine.gg_adapter import GGanalysisSolver
from gacha.games.registry import get_game
from gacha.viz.report import generate_report, pmf_cdf_figure

SOLVER = GGanalysisSolver()
GENSHIN = get_game("genshin")


def test_report_generates_selfcontained_html(tmp_path):
    out = str(tmp_path / "report.html")
    path = generate_report(out, GENSHIN, PullState(), Target("character", 1),
                           SOLVER, budget=90)
    with open(path, encoding="utf-8") as f:
        content = f.read()
    # 自包含：内联 plotly.js
    assert "Plotly" in content
    # 中文正常写入
    assert "期望抽数" in content and "原神" in content
    # 含三大板块
    assert "核心指标" in content and "命座×精炼" in content and "跨游戏比对" in content
    assert len(content) > 100_000  # 内联 plotly.js，文件应较大


def test_report_sections_toggle(tmp_path):
    out = str(tmp_path / "r2.html")
    generate_report(out, GENSHIN, PullState(), Target("character", 1), SOLVER,
                    include_grid=False, include_compare=False)
    with open(out, encoding="utf-8") as f:
        content = f.read()
    assert "命座×精炼" not in content
    assert "跨游戏比对" not in content


def test_pmf_cdf_figure_builds():
    dist = SOLVER.solve(GENSHIN, PullState(), Target("character", 1), 0)
    fig = pmf_cdf_figure(dist, "t", budget=90)
    assert fig is not None and len(fig.data) == 2
