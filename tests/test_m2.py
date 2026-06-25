"""M2 测试：武器池一致性、组合卷积、UIGF 往返、history 还原。"""

import GGanalysis.games.genshin_impact as GI
import numpy as np
import pytest

from gacha.analysis import combine, metrics
from gacha.engine.base import PullState, Target
from gacha.engine.gg_adapter import GGanalysisSolver
from gacha.games.registry import get_game
from gacha.io.history import analyze_character_history
from gacha.io.uigf import GachaArchive, GachaRecord, UigfFile, load_uigf, save_uigf

GENSHIN = get_game("genshin")
SOLVER = GGanalysisSolver()


# ---------- 武器池 ----------
def test_weapon_adapter_matches_gganalysis():
    ours = SOLVER.solve(GENSHIN, PullState(), Target("weapon", 1), 0).pmf
    direct = np.asarray(GI.up_5star_ep_weapon(item_num=1).dist, dtype=float)
    n = min(len(ours), len(direct))
    assert np.allclose(ours[:n], direct[:n], atol=1e-12)


def test_weapon_expectation():
    d = SOLVER.solve(GENSHIN, PullState(), Target("weapon", 1), 0)
    assert metrics.expectation(d) == pytest.approx(86.53, abs=0.2)


# ---------- 组合目标（卷积）----------
def test_combine_matches_gganalysis_convolution():
    char = SOLVER.solve(GENSHIN, PullState(), Target("character", 1), 0)
    weap = SOLVER.solve(GENSHIN, PullState(), Target("weapon", 1), 0)
    combined = combine.combine([char, weap])

    # GGanalysis FiniteDist 卷积作为金标准
    gg = GI.up_5star_character(item_num=1) * GI.up_5star_ep_weapon(item_num=1)
    gg_pmf = np.asarray(gg.dist, dtype=float)
    n = min(len(combined.pmf), len(gg_pmf))
    assert np.allclose(combined.pmf[:n], gg_pmf[:n], atol=1e-12)


def test_combine_expectation_is_sum():
    char = SOLVER.solve(GENSHIN, PullState(), Target("character", 1), 0)
    weap = SOLVER.solve(GENSHIN, PullState(), Target("weapon", 1), 0)
    combined = combine.combine([char, weap])
    assert metrics.expectation(combined) == pytest.approx(
        metrics.expectation(char) + metrics.expectation(weap), abs=0.1
    )


# ---------- UIGF 往返 ----------
def _make_archive():
    recs = []
    for i in range(1, 6):
        recs.append(GachaRecord(id=str(1000 + i), gacha_type="301",
                                uigf_gacha_type="301", item_id=str(i),
                                name=f"item{i}", rank_type="3",
                                item_type="武器", time="2024-01-01 00:00:00"))
    return GachaArchive(game="genshin", uid="100000001", timezone=8,
                        lang="zh-cn", records=recs)


def test_uigf_round_trip(tmp_path):
    src = UigfFile(archives=[_make_archive()])
    path = str(tmp_path / "uigf.json")
    save_uigf(src, path)
    loaded = load_uigf(path)
    a0 = loaded.archives_for("genshin")[0]
    assert a0.uid == "100000001"
    assert len(a0.records) == 5
    assert a0.records[0].time == "2024-01-01 00:00:00"  # 时间保留原始字符串
    assert loaded.version.startswith("v4")


# ---------- history 还原 ----------
def _record(i, rank, name):
    return GachaRecord(id=str(10_000 + i), gacha_type="301", uigf_gacha_type="301",
                       item_id=str(i), name=name, rank_type=rank,
                       item_type="角色", time="2024-01-01 00:00:00")


def test_history_reconstruction():
    recs = []
    idx = 0
    # 10 抽出 UP（赢 50/50）
    for _ in range(9):
        idx += 1; recs.append(_record(idx, "3", "x"))
    idx += 1; recs.append(_record(idx, "5", "芙宁娜"))      # win
    # 80 抽出常驻（歪了 → 大保底）
    for _ in range(79):
        idx += 1; recs.append(_record(idx, "3", "x"))
    idx += 1; recs.append(_record(idx, "5", "七七"))        # lose (standard)
    # 再垫 5 抽未出
    for _ in range(5):
        idx += 1; recs.append(_record(idx, "3", "x"))

    arch = GachaArchive(game="genshin", uid="u", records=recs)
    h = analyze_character_history(arch)

    assert h.total_pulls == 95
    assert h.five_star_count == 2
    assert h.five_star_pities == [10, 80]
    assert h.average_5star_pity == pytest.approx(45.0)
    assert h.fifty_fifty_total == 2
    assert h.fifty_fifty_wins == 1
    assert h.fifty_fifty_winrate == pytest.approx(0.5)
    assert h.current_pity == 5
    assert h.current_guaranteed is True
    assert h.radiance_losses == 1
    # 还原的 state 可直接用于求解
    d = SOLVER.solve(GENSHIN, h.state, Target("character", 1), 0)
    assert metrics.expectation(d) > 0
