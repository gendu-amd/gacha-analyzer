"""集录祈愿（经典 50/50，无捕获明光）一致性验证。"""

import GGanalysis.games.genshin_impact as GI
import numpy as np
import pytest

from gacha.analysis import metrics
from gacha.engine.base import PullState, Target
from gacha.engine.gg_adapter import GGanalysisSolver

from gacha.games.registry import get_game

GENSHIN = get_game("genshin")
SOLVER = GGanalysisSolver()


def _solve(copies=1, pity=0, guaranteed=False):
    return SOLVER.solve(GENSHIN, PullState(item_pity=pity, is_guaranteed=guaranteed),
                        Target("chronicled", copies), 0)


@pytest.mark.parametrize("copies,guaranteed", [(1, False), (1, True), (2, False), (3, False)])
def test_chronicled_matches_gganalysis(copies, guaranteed):
    ours = _solve(copies=copies, guaranteed=guaranteed).pmf
    direct = np.asarray(
        GI.classic_up_5star_character(item_num=copies, up_pity=1 if guaranteed else 0).dist,
        dtype=float,
    )
    n = min(len(ours), len(direct))
    assert np.allclose(ours[:n], direct[:n], atol=1e-12)


def test_chronicled_no_capturing_radiance():
    """集录无捕获明光：多拷贝期望应等于经典 50/50（高于含 CR 的角色池）。"""
    chron3 = metrics.expectation(_solve(copies=3))
    char3 = metrics.expectation(
        SOLVER.solve(GENSHIN, PullState(), Target("character", 3), 0)
    )
    assert chron3 > char3  # 无 CR 增益，故更费抽


def test_chronicled_guaranteed_equals_single_5star():
    """有命定值时，1 个指定 5★ 期望 = 单个 5★ ≈ 62.3。"""
    assert metrics.expectation(_solve(1, guaranteed=True)) == pytest.approx(62.3, abs=0.2)
