"""自研 reference-MC 与 GGanalysis 精确解交叉验证。"""

import pytest

from gacha.analysis import metrics
from gacha.engine.base import BANNER_CHARACTER, PullState, Target
from gacha.engine.gg_adapter import GGanalysisSolver
from gacha.engine.reference.mc import CharacterMechanism, ReferenceMCSolver
from gacha.games.genshin import genshin_character_mechanism
from gacha.games.registry import get_game

GENSHIN = get_game("genshin")
MECH = genshin_character_mechanism()
RUNS = 300_000
MAX_PULLS = 600


def _mc(runs=RUNS, seed=42):
    return ReferenceMCSolver(MECH, runs=runs, seed=seed)


@pytest.mark.parametrize(
    "copies,pity,guaranteed,losses",
    [
        (1, 0, False, 0),
        (1, 0, True, 1),
        (2, 0, False, 0),
        (3, 0, False, 0),
        (1, 70, False, 0),
        # 大保底但未跟踪明光计数（losses=0）：曾经的盲区——MC 用 losses=0、适配层折算为 1，
        # 导致 ~2% 分叉。修复后两引擎应收敛（见 DECISIONS.md）。
        (2, 0, True, 0),
        (3, 0, True, 0),
    ],
)
def test_mc_matches_gganalysis_expectation(copies, pity, guaranteed, losses):
    state = PullState(item_pity=pity, is_guaranteed=guaranteed, radiance_losses=losses)
    target = Target(BANNER_CHARACTER, copies)
    gg = GGanalysisSolver().solve(GENSHIN, state, target, max_pulls=0)
    mc = _mc().solve(GENSHIN, state, target, MAX_PULLS)

    gg_exp = metrics.expectation(gg)
    mc_exp = metrics.expectation(mc)
    # 蒙卡统计误差：相对误差 < 0.5%
    assert abs(mc_exp - gg_exp) / gg_exp < 0.005


def test_mc_big_pity_losses_folding_matches_gg():
    """显式堵盲区：(guaranteed=True, losses=0) 与 (guaranteed=True, losses=1) 等价，
    且 MC 与 GG 相对误差 < 0.5%（折算逻辑与 _to_gg_kwargs 一致）。"""
    for copies in (2, 3):
        target = Target(BANNER_CHARACTER, copies)
        st0 = PullState(is_guaranteed=True, radiance_losses=0)
        st1 = PullState(is_guaranteed=True, radiance_losses=1)
        gg = GGanalysisSolver().solve(GENSHIN, st0, target, 0)
        mc0 = _mc(seed=11).solve(GENSHIN, st0, target, MAX_PULLS)
        mc1 = _mc(seed=11).solve(GENSHIN, st1, target, MAX_PULLS)
        gg_exp = metrics.expectation(gg)
        # losses=0 与 losses=1 折算后应同分布（逐点一致）
        assert metrics.expectation(mc0) == pytest.approx(metrics.expectation(mc1), abs=1e-9)
        assert abs(metrics.expectation(mc0) - gg_exp) / gg_exp < 0.005


def test_mc_auto_max_pulls_when_nonpositive():
    """max_pulls<=0 应自动取合理上限（不报错），覆盖几乎全部概率质量。"""
    target = Target(BANNER_CHARACTER, 1)
    mc = _mc(seed=3).solve(GENSHIN, PullState(), target, max_pulls=0)
    assert metrics.total_mass(mc) == pytest.approx(1.0, abs=1e-6)
    assert mc.max_pulls == 2 * MECH.hard_pity  # 1 拷贝 → 2*hard_pity


def test_mc_cdf_close_to_gganalysis():
    """关键分位点 CDF 接近（容差含蒙卡噪声）。"""
    state = PullState()
    target = Target(BANNER_CHARACTER, 1)
    gg = GGanalysisSolver().solve(GENSHIN, state, target, max_pulls=0)
    mc = _mc(seed=7).solve(GENSHIN, state, target, MAX_PULLS)
    for n in (80, 90, 160):
        assert metrics.prob_within(mc, n) == pytest.approx(
            metrics.prob_within(gg, n), abs=0.01
        )


def test_mechanism_injection_is_game_agnostic():
    """ReferenceMCSolver 不依赖 games：任意自定义机制可直接驱动。"""
    mech = CharacterMechanism(
        rate_fn=MECH.rate_fn, hard_pity=MECH.hard_pity, cr_up_prob=MECH.cr_up_prob
    )
    mc = ReferenceMCSolver(mech, runs=50_000, seed=1)
    d = mc.solve(GENSHIN, PullState(), Target(BANNER_CHARACTER, 1), MAX_PULLS)
    assert metrics.expectation(d) > 0
