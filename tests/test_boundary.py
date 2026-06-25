"""硬规则边界用例 + 指标与契约健全性。"""

import numpy as np
import pytest

from gacha.analysis import budget, metrics
from gacha.engine.base import PullDistribution, PullState, Target
from gacha.engine.gg_adapter import GGanalysisSolver
from gacha.games.registry import get_game

GENSHIN = get_game("genshin")
SOLVER = GGanalysisSolver()


def _solve(copies=1, pity=0, guaranteed=False, losses=0):
    state = PullState(item_pity=pity, is_guaranteed=guaranteed, radiance_losses=losses)
    return SOLVER.solve(GENSHIN, state, Target("character", copies), 0)


def test_hard_pity_one_copy_bounded():
    """1 个 UP：最坏需两个 5★，硬保底 90 → 必在 180 抽内达成。"""
    dist = _solve()
    assert metrics.prob_within(dist, 180) == pytest.approx(1.0, abs=1e-9)


def test_guaranteed_first_5star_is_up():
    """大保底下，第一个 5★ 必为 UP：达成分布等价于「单个 5★」分布。"""
    guaranteed = _solve(guaranteed=True, losses=1)
    # 大保底 1 个 UP 的期望应约等于单个 5★ 期望 62.3
    assert metrics.expectation(guaranteed) == pytest.approx(62.3, abs=0.2)


def test_pity_reduces_expectation():
    """已垫抽越多，期望剩余抽数越少。"""
    assert metrics.expectation(_solve(pity=80)) < metrics.expectation(_solve(pity=0))


def test_quantile_monotonic():
    dist = _solve()
    assert metrics.quantile(dist, 0.5) <= metrics.quantile(dist, 0.9) <= metrics.quantile(dist, 0.99)


def test_cdf_and_mass():
    dist = _solve()
    c = metrics.cdf(dist)
    assert np.all(np.diff(c) >= -1e-12)  # 单调不降
    assert metrics.total_mass(dist) == pytest.approx(1.0, abs=1e-6)


def test_budget_conversions():
    dist = _solve()
    r = budget.budget_outlook(GENSHIN, dist, 90)
    assert r.currency == 90 * 160
    assert r.money_cny == pytest.approx(90 * 16.0)
    assert 0 <= r.probability <= 1


def test_luck_percentile_bounds():
    dist = _solve()
    assert metrics.luck_percentile(dist, 0) == pytest.approx(1.0, abs=1e-6)
    assert 0 <= metrics.luck_percentile(dist, 90) <= 1


def test_pullstate_validation():
    with pytest.raises(ValueError):
        PullState(item_pity=-1)
    with pytest.raises(ValueError):
        PullState(radiance_losses=5)
    with pytest.raises(ValueError):
        Target(copies=0)
