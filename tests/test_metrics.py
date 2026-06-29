"""指标层测试：截断分布归一化期望/方差、严格 Expected Shortfall。"""

import numpy as np
import pytest

from gacha.analysis import metrics
from gacha.engine.base import BANNER_CHARACTER, PullState, Target
from gacha.engine.gg_adapter import GGanalysisSolver
from gacha.games.registry import get_game

SOLVER = GGanalysisSolver()
GENSHIN = get_game("genshin")


# ---------- 截断分布期望/方差归一化 ----------
def test_truncated_expectation_normalized():
    """max_pulls=90 截断分布：归一化后期望 ≈ 条件期望，远大于未归一化的错误低估值。"""
    d = SOLVER.solve(GENSHIN, PullState(), Target(BANNER_CHARACTER, 1), max_pulls=90)
    mass = metrics.total_mass(d)
    assert mass < 0.95  # 确实被截断
    naive_underestimate = float((np.arange(len(d.pmf)) * d.pmf).sum())  # 旧的错误口径
    exp = metrics.expectation(d)
    assert exp == pytest.approx(naive_underestimate / mass)  # = 条件期望
    assert exp > naive_underestimate * 1.3  # 远大于低估值
    assert exp <= 90  # 条件于 N<=90，故不超过上限
    # 方差/标准差同样归一化（与未归一化不同）
    assert metrics.std(d) > 0


def test_full_distribution_expectation_unchanged():
    """full 分布（mass≈1）期望不受归一化影响，仍 ≈ 93.45。"""
    d = SOLVER.solve(GENSHIN, PullState(), Target(BANNER_CHARACTER, 1), max_pulls=0)
    assert metrics.total_mass(d) == pytest.approx(1.0, abs=1e-6)
    assert metrics.expectation(d) == pytest.approx(93.45, abs=0.1)


# ---------- 严格 Expected Shortfall ----------
def test_strict_es_small_example():
    """手算小例：pmf=[0,.1,.2,.3,.4], q=0.5 → VaR=3, ES=3.8, CTE≈3.571。"""
    pmf = np.array([0.0, 0.1, 0.2, 0.3, 0.4])
    var = metrics.value_at_risk(pmf, 0.5)
    assert var == 3
    es = metrics.conditional_value_at_risk(pmf, 0.5)
    assert es == pytest.approx(3.8, abs=1e-9)
    # 朴素 CTE = E[N|N>=VaR]
    tail = pmf[var:]
    cte = float((np.arange(var, len(pmf)) * tail).sum() / tail.sum())
    assert cte == pytest.approx(3.5714285, abs=1e-5)
    assert es >= cte >= var  # 严格 ES 更保守


def test_es_ge_cte_on_real_dist():
    """真实角色池分布上：ES >= CTE >= VaR。"""
    d = SOLVER.solve(GENSHIN, PullState(), Target(BANNER_CHARACTER, 1), 0)
    var = metrics.value_at_risk(d, 0.9)
    es = metrics.conditional_value_at_risk(d, 0.9)
    tail = d.pmf[var:]
    cte = float((np.arange(var, len(d.pmf)) * tail).sum() / tail.sum())
    assert es >= cte >= var
