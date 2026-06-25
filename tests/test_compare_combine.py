"""跨游戏组合目标比对测试。"""

import warnings

import pytest

from gacha.analysis import compare, metrics
from gacha.analysis.compare import CombineComparisonRow
from gacha.engine.gg_adapter import GGanalysisSolver
from gacha.games.registry import get_game

SOLVER = GGanalysisSolver()


def test_compare_combine_three_games():
    rows = compare.compare_combine_games(SOLVER, char_copies=1, weap_copies=1,
                                         game_keys=["genshin", "hsr", "zzz"])
    assert len(rows) == 3
    assert all(isinstance(r, CombineComparisonRow) for r in rows)
    assert rows[0].relative_cost == pytest.approx(1.0)
    assert rows[0].exp_pulls <= rows[-1].exp_pulls
    for r in rows:
        assert r.dist is not None
        assert r.exp_pulls == pytest.approx(metrics.expectation(r.dist), abs=0.01)


def test_compare_combine_genshin_01_matches_combine():
    rows = compare.compare_combine_games(SOLVER, char_copies=1, weap_copies=1,
                                         game_keys=["genshin"])
    assert len(rows) == 1
    assert rows[0].exp_pulls == pytest.approx(179.98, abs=0.5)


def test_compare_combine_table_renders():
    rows = compare.compare_combine_games(SOLVER, char_copies=1, weap_copies=1)
    from gacha.viz.tables import format_combine_compare_table
    txt = format_combine_compare_table(rows)
    assert "期望抽数" in txt and "相对成本" in txt


def test_compare_combine_cdf_plot(tmp_path):
    rows = compare.compare_combine_games(SOLVER, char_copies=1, weap_copies=1)
    from gacha.viz.plots import plot_compare_combine_cdf
    out = str(tmp_path / "cdf.png")
    path = plot_compare_combine_cdf(rows, out_path=out)
    assert path == out
    import os
    assert os.path.getsize(out) > 1000


def test_compare_combine_warns():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        compare.compare_combine_games(SOLVER, char_copies=1, weap_copies=1)
    assert any("仅供参考" in str(x.message) for x in w)
