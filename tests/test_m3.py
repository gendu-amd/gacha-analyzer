"""M3 测试：星铁/绝区零 一致性 + 跨游戏比对健全性。"""

import GGanalysis.games.honkai_star_rail as SR
import GGanalysis.games.zenless_zone_zero as ZZZ
import numpy as np
import pytest

from gacha.analysis import compare, metrics
from gacha.engine.base import PullState, Target
from gacha.engine.gg_adapter import GGanalysisSolver
from gacha.games.registry import get_game, list_games

SOLVER = GGanalysisSolver()


def test_games_registered():
    for k in ("genshin", "hsr", "zzz"):
        assert k in list_games()


@pytest.mark.parametrize("banner,gg", [
    ("character", SR.up_5star_character),
    ("weapon", SR.up_5star_weapon),
])
def test_hsr_matches_gganalysis(banner, gg):
    ours = SOLVER.solve(get_game("hsr"), PullState(), Target(banner, 1), 0).pmf
    direct = np.asarray(gg(item_num=1).dist, dtype=float)
    n = min(len(ours), len(direct))
    assert np.allclose(ours[:n], direct[:n], atol=1e-12)


@pytest.mark.parametrize("banner,gg", [
    ("character", ZZZ.up_5star_character),
    ("weapon", ZZZ.up_5star_weapon),
])
def test_zzz_matches_gganalysis(banner, gg):
    ours = SOLVER.solve(get_game("zzz"), PullState(), Target(banner, 1), 0).pmf
    direct = np.asarray(gg(item_num=1).dist, dtype=float)
    n = min(len(ours), len(direct))
    assert np.allclose(ours[:n], direct[:n], atol=1e-12)


def test_hsr_character_expectation():
    d = SOLVER.solve(get_game("hsr"), PullState(), Target("character", 1), 0)
    assert metrics.expectation(d) == pytest.approx(89.55, abs=0.3)


def test_compare_sorted_and_consistent():
    rows = compare.compare_games(SOLVER, ["genshin", "hsr", "zzz"], banner="character")
    assert len(rows) == 3
    # 按期望抽数升序
    assert rows[0].exp_pulls <= rows[1].exp_pulls <= rows[2].exp_pulls
    # 最划算的相对成本为 1.0
    assert rows[0].relative_cost == pytest.approx(1.0)
    # 货币换算正确
    for r in rows:
        g = get_game(r.game_key)
        assert r.exp_currency == pytest.approx(r.exp_pulls * g.currency_per_pull)
    # 星铁角色池应比原神便宜（更早软保底）
    by = {r.game_key: r for r in rows}
    assert by["hsr"].exp_pulls < by["genshin"].exp_pulls


def test_compare_table_renders():
    rows = compare.compare_games(SOLVER, banner="character")
    from gacha.viz.tables import format_compare_table
    txt = format_compare_table(rows)
    assert "期望抽数" in txt and len(txt.splitlines()) >= 4
