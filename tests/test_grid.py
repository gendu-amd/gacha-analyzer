"""命座×精炼 成本网格测试。"""

import pytest

from gacha.analysis import combine, grid, metrics
from gacha.engine.base import PullState, Target
from gacha.engine.gg_adapter import GGanalysisSolver
from gacha.games.registry import get_game

SOLVER = GGanalysisSolver()
GENSHIN = get_game("genshin")


def test_grid_shape_and_labels():
    g = grid.cost_grid(SOLVER, GENSHIN)
    assert len(g.exp_pulls) == 7          # C0..C6
    assert len(g.exp_pulls[0]) == 6       # R0..R5
    assert g.const_labels()[0] == "C0" and g.const_labels()[-1] == "C6"
    assert g.refine_labels() == ["R0", "R1", "R2", "R3", "R4", "R5"]


def test_grid_monotonic():
    """命座或精炼越高，期望抽数越大。"""
    g = grid.cost_grid(SOLVER, GENSHIN)
    for c in range(7):
        for w in range(5):
            assert g.exp_pulls[c][w] < g.exp_pulls[c][w + 1]   # 精炼递增
    for c in range(6):
        for w in range(6):
            assert g.exp_pulls[c][w] < g.exp_pulls[c + 1][w]   # 命座递增


def test_grid_cell_matches_combine():
    """网格某格 = 直接 combine 的期望。"""
    g = grid.cost_grid(SOLVER, GENSHIN)
    # C0R0 = 1 角色，无武器
    c0r0 = metrics.expectation(SOLVER.solve(GENSHIN, PullState(), Target("character", 1), 0))
    assert g.exp_pulls[0][0] == pytest.approx(c0r0, abs=0.01)
    # C2R3 = 3 角色 + 3 武器
    d = combine.combine_targets(GENSHIN, SOLVER,
                                [(PullState(), Target("character", 3)),
                                 (PullState(), Target("weapon", 3))])
    assert g.exp_pulls[2][3] == pytest.approx(metrics.expectation(d), abs=0.01)


def test_grid_money_conversion():
    g = grid.cost_grid(SOLVER, GENSHIN)
    assert g.money_cny[6][5] == pytest.approx(g.exp_pulls[6][5] * 16.0, abs=0.01)


def test_grid_hsr_prefix():
    g = grid.cost_grid(SOLVER, get_game("hsr"))
    assert g.const_labels()[0] == "E0"   # 星铁用魂(Eidolon)
