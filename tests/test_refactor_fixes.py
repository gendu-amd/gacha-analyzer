"""代码审查修复的针对性测试（issues 3/4/5/9c/9d）。"""

import warnings

import numpy as np
import pytest

from gacha.analysis import compare, metrics
from gacha.analysis.compare import COMPARE_CAVEAT
from gacha.engine.base import BANNER_CHARACTER, PullState, Target
from gacha.engine.gg_adapter import GGanalysisSolver
from gacha.games.registry import get_game
from gacha.io.history import analyze_character_history
from gacha.io.uigf import GachaArchive, GachaRecord, UigfFile

SOLVER = GGanalysisSolver()
GENSHIN = get_game("genshin")


# ---------- issue 3：截断分布期望/方差归一化 ----------
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


# ---------- issue 4：严格 Expected Shortfall ----------
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


# ---------- issue 5：history game-agnostic + 301/400 合池 + lang 告警 ----------
def _rec(i, rank, name, gacha_type="301", uigf="301", item_id=None):
    return GachaRecord(id=str(10_000 + i), gacha_type=gacha_type, uigf_gacha_type=uigf,
                       item_id=str(item_id if item_id is not None else i), name=name, rank_type=rank,
                       item_type="角色", time="2024-01-01 00:00:00")


def test_history_merges_301_and_400():
    """301/400 共享保底：两类记录都应归入角色历史；某条 400 缺 uigf_gacha_type 不被排除。"""
    recs = []
    idx = 0
    for _ in range(9):
        idx += 1; recs.append(_rec(idx, "3", "x", "301", "301"))
    idx += 1; recs.append(_rec(idx, "5", "芙宁娜", "301", "301"))    # 301 的 5★
    for _ in range(9):
        idx += 1; recs.append(_rec(idx, "3", "y", "400", ""))        # 400 缺 uigf_gacha_type
    idx += 1; recs.append(_rec(idx, "5", "七七", "400", ""))         # 400 的 5★（常驻→歪）
    arch = GachaArchive(game="genshin", uid="u", lang="zh-cn", records=recs)

    h = analyze_character_history(arch, GENSHIN)
    assert h.total_pulls == 20            # 301+400 全计入
    assert h.five_star_count == 2
    assert h.five_star_pities == [10, 10]
    assert h.fifty_fifty_total == 2 and h.fifty_fifty_wins == 1


def test_history_default_game_lookup():
    """game 缺省时按 archive.game 自动查注册表（仍 game-agnostic）。"""
    recs = [_rec(1, "5", "芙宁娜")]
    arch = GachaArchive(game="genshin", uid="u", lang="zh-cn", records=recs)
    h = analyze_character_history(arch)  # 不传 game
    assert h.five_star_count == 1


def test_history_warns_on_unreliable_lang():
    """lang 非中英文且仅靠名字判定：发出 50/50 可能不准的告警。"""
    recs = [_rec(1, "5", "フリーナ")]  # 日文名，无 avatar item_id
    arch = GachaArchive(game="genshin", uid="u", lang="ja", records=recs)
    with pytest.warns(UserWarning, match="50/50"):
        analyze_character_history(arch, GENSHIN)


def test_history_reliable_lang_no_warning():
    recs = [_rec(1, "5", "Furina")]
    arch = GachaArchive(game="genshin", uid="u", lang="en", records=recs)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        analyze_character_history(arch, GENSHIN)  # 不应告警


# ---------- issue 9c：UIGF 版本正则 + 字段校验 ----------
def test_uigf_bad_version_warns():
    data = {"info": {"version": "4.2"}, "hk4e": []}  # 缺前缀 v
    with pytest.warns(UserWarning, match="version"):
        UigfFile.from_dict(data)


def test_uigf_good_version_no_version_warning():
    data = {"info": {"version": "v4.2"}, "hk4e": []}
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        UigfFile.from_dict(data)


def test_uigf_missing_id_record_skipped_with_warning():
    data = {
        "info": {"version": "v4.2"},
        "hk4e": [{
            "uid": "1", "lang": "zh-cn",
            "list": [
                {"id": "1", "gacha_type": "301", "rank_type": "5", "name": "x"},
                {"gacha_type": "301", "rank_type": "3", "name": "y"},  # 缺 id
            ],
        }],
    }
    with pytest.warns(UserWarning, match="必需字段"):
        uigf = UigfFile.from_dict(data)
    arch = uigf.archives_for("genshin")[0]
    assert len(arch.records) == 1  # 缺 id 的被跳过


# ---------- issue 9d：compare 护栏 ----------
def test_compare_warns_and_carries_caveat():
    with pytest.warns(UserWarning, match="仅供参考"):
        rows = compare.compare_games(SOLVER, ["genshin", "hsr"], banner=BANNER_CHARACTER)
    assert len(rows) == 2
    assert all(r.caveat == COMPARE_CAVEAT for r in rows)
