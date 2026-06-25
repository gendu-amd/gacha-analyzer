"""封装层与 GGanalysis 直调结果一致性 + 与官方/社区数值收敛性。"""

import GGanalysis.games.genshin_impact as GI
import numpy as np
import pytest

from gacha.analysis import metrics
from gacha.engine.base import PullState, Target
from gacha.engine.gg_adapter import GGanalysisSolver
from gacha.games.genshin import five_star_pull_prob
from gacha.games.registry import get_game

SOLVER = GGanalysisSolver()
GENSHIN = get_game("genshin")


def _solve(copies=1, pity=0, guaranteed=False, losses=0):
    state = PullState(item_pity=pity, is_guaranteed=guaranteed, radiance_losses=losses)
    return SOLVER.solve(GENSHIN, state, Target("character", copies), max_pulls=0)


@pytest.mark.parametrize("copies", [1, 2, 3])
def test_adapter_matches_gganalysis_directly(copies):
    """适配层 PMF 必须与 GGanalysis 直接调用逐点一致。"""
    direct = np.asarray(GI.up_5star_character(item_num=copies).dist, dtype=float)
    ours = _solve(copies=copies).pmf
    n = min(len(direct), len(ours))
    assert np.allclose(direct[:n], ours[:n], atol=1e-12)


def test_expectation_one_copy():
    """1 个 UP 5★ 期望 ≈ 93.45 抽（社区共识 ≈1.5×62.3）。"""
    assert metrics.expectation(_solve(1)) == pytest.approx(93.45, abs=0.1)


def test_common_5star_average():
    """单个 5★（不分 UP）平均 ≈ 62.3 抽。"""
    d = np.asarray(GI.common_5star(item_num=1).dist, dtype=float)
    exp = float((np.arange(len(d)) * d).sum())
    assert exp == pytest.approx(62.3, abs=0.1)


def test_capturing_radiance_helps_multi_copy():
    """捕获明光对多拷贝有效：新模型期望应低于旧 50/50。"""
    new3 = metrics.expectation(_solve(3))
    classic3 = float(
        (np.arange(len(GI.classic_up_5star_character(item_num=3).dist))
         * np.asarray(GI.classic_up_5star_character(item_num=3).dist)).sum()
    )
    assert new3 < classic3


def test_soft_pity_curve():
    """软保底曲线与 GGanalysis PITY_5STAR 对齐。"""
    assert five_star_pull_prob(1) == pytest.approx(0.006)
    assert five_star_pull_prob(73) == pytest.approx(0.006)
    assert five_star_pull_prob(74) == pytest.approx(0.066)
    assert five_star_pull_prob(90) == pytest.approx(1.0)
    for p in range(1, 91):
        assert five_star_pull_prob(p) == pytest.approx(GI.PITY_5STAR[p], abs=1e-12)
