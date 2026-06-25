"""星铁/绝区零常驻池（任意 5★/S 级）一致性验证。"""

import GGanalysis.games.honkai_star_rail as SR
import GGanalysis.games.zenless_zone_zero as ZZZ
import numpy as np
import pytest

from gacha.analysis import metrics
from gacha.engine.base import PullState, Target
from gacha.engine.gg_adapter import GGanalysisSolver
from gacha.games.registry import get_game

SOLVER = GGanalysisSolver()

STANDARD_E = 62.297332039630945  # metrics.expectation(common_5star)，三游相同


@pytest.mark.parametrize("game_key,gg", [
    ("hsr", SR.common_5star),
    ("zzz", ZZZ.common_5star),
])
@pytest.mark.parametrize("copies", [1, 2, 3])
def test_standard_matches_gganalysis(game_key, gg, copies):
    game = get_game(game_key)
    ours = SOLVER.solve(game, PullState(), Target("standard", copies), 0).pmf
    direct = np.asarray(gg(item_num=copies).dist, dtype=float)
    n = min(len(ours), len(direct))
    assert np.allclose(ours[:n], direct[:n], atol=1e-12)


@pytest.mark.parametrize("game_key", ["hsr", "zzz"])
def test_standard_expectation(game_key):
    game = get_game(game_key)
    d = SOLVER.solve(game, PullState(), Target("standard", 1), 0)
    assert metrics.expectation(d) == pytest.approx(STANDARD_E, abs=1e-10)


@pytest.mark.parametrize("game_key", ["hsr", "zzz"])
def test_standard_no_5050_state_ignored(game_key):
    """常驻池无 50/50：大保底状态不应改变结果。"""
    game = get_game(game_key)
    base = SOLVER.solve(game, PullState(), Target("standard", 1), 0).pmf
    other = SOLVER.solve(
        game, PullState(item_pity=0, is_guaranteed=True, radiance_losses=1),
        Target("standard", 1), 0,
    ).pmf
    n = min(len(base), len(other))
    assert np.allclose(base[:n], other[:n], atol=1e-12)
