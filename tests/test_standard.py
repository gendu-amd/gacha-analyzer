"""常驻祈愿（任意 5★）一致性验证。"""

import GGanalysis.games.genshin_impact as GI
import numpy as np
import pytest

from gacha.analysis import metrics
from gacha.engine.base import PullState, Target
from gacha.engine.gg_adapter import GGanalysisSolver
from gacha.games.registry import get_game

GENSHIN = get_game("genshin")
SOLVER = GGanalysisSolver()


def _solve(copies=1, pity=0):
    return SOLVER.solve(GENSHIN, PullState(item_pity=pity),
                        Target("standard", copies), 0)


@pytest.mark.parametrize("copies", [1, 2, 3])
def test_standard_matches_gganalysis(copies):
    ours = _solve(copies=copies).pmf
    direct = np.asarray(GI.common_5star(item_num=copies).dist, dtype=float)
    n = min(len(ours), len(direct))
    assert np.allclose(ours[:n], direct[:n], atol=1e-12)


def test_standard_expectation():
    assert metrics.expectation(_solve(1)) == pytest.approx(62.3, abs=0.1)


def test_standard_no_5050_state_ignored():
    """常驻池无 50/50：大保底/连歪状态不应改变结果。"""
    base = _solve(1).pmf
    other = SOLVER.solve(
        GENSHIN, PullState(item_pity=0, is_guaranteed=True, radiance_losses=1),
        Target("standard", 1), 0,
    ).pmf
    n = min(len(base), len(other))
    assert np.allclose(base[:n], other[:n], atol=1e-12)
