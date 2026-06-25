"""网格单元格 PMF 导出测试。"""

import os

import pytest

from gacha.analysis import grid, metrics
from gacha.engine.gg_adapter import GGanalysisSolver
from gacha.games.registry import get_game

SOLVER = GGanalysisSolver()
GENSHIN = get_game("genshin")


def test_parse_cell_code():
    assert grid.parse_cell_code("00") == (0, 0)
    assert grid.parse_cell_code("01") == (0, 1)
    assert grid.parse_cell_code("21") == (2, 1)
    assert grid.parse_cell_code("65") == (6, 5)
    with pytest.raises(ValueError):
        grid.parse_cell_code("abc")


def test_cell_label():
    assert grid.cell_label("genshin", 2, 1) == "C2R1"
    assert grid.cell_label("hsr", 0, 1) == "E0R1"


def test_cell_distribution_matches_grid():
    g = grid.cost_grid(SOLVER, GENSHIN)
    dist = grid.cell_distribution(SOLVER, GENSHIN, 0, 1)
    assert metrics.expectation(dist) == pytest.approx(g.exp_pulls[0][1], abs=0.01)


def test_export_pmf_pngs(tmp_path):
    from gacha.viz.plots import plot_pmf_cdf
    out_dir = str(tmp_path / "pmfs")
    os.makedirs(out_dir)
    for code in ("00", "01"):
        const, refine = grid.parse_cell_code(code)
        dist = grid.cell_distribution(SOLVER, GENSHIN, const, refine)
        label = grid.cell_label("genshin", const, refine)
        path = os.path.join(out_dir, f"genshin_{label}.png")
        plot_pmf_cdf(dist, title=f"test {label}", out_path=path)
        assert os.path.getsize(path) > 500


def test_all_cell_codes_count():
    codes = grid.all_cell_codes()
    assert len(codes) == 7 * 6  # C0..C6 × R0..R5
    assert "00" in codes and "65" in codes
