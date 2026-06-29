"""历史还原测试：301/400 合池、game-agnostic 查表、语言告警、item_id 优先判定。"""

import warnings

import pytest

from gacha.games.genshin import STANDARD_5STAR_CHARACTER_ITEM_IDS
from gacha.games.registry import get_game
from gacha.io.history import analyze_character_history
from gacha.io.uigf import GachaArchive, GachaRecord

GENSHIN = get_game("genshin")


def _rec(i, rank, name, gacha_type="301", uigf="301", item_id=None):
    return GachaRecord(id=str(10_000 + i), gacha_type=gacha_type, uigf_gacha_type=uigf,
                       item_id=str(item_id if item_id is not None else i), name=name, rank_type=rank,
                       item_type="角色", time="2024-01-01 00:00:00")


def _rec_id(i, rank, name, item_id):
    """显式 item_id 记录（用于 item_id 优先判定测试）。"""
    return GachaRecord(
        id=str(10_000 + i), gacha_type="301", uigf_gacha_type="301",
        item_id=item_id, name=name, rank_type=rank,
        item_type="角色", time="2024-01-01 00:00:00",
    )


# ---------- history game-agnostic + 301/400 合池 + lang 告警 ----------
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


# ---------- item_id 优先于名字判定 50/50 ----------
def test_history_standard_by_item_id_japanese_no_warning():
    """日文 lang + item_id：不依赖名字，50/50 可正确判定且无告警。"""
    recs = []
    idx = 0
    for _ in range(9):
        idx += 1
        recs.append(_rec_id(idx, "3", "xxx", item_id=str(1000 + idx)))
    idx += 1
    recs.append(_rec_id(idx, "5", "フリーナ", item_id="10000089"))  # Furina UP
    for _ in range(9):
        idx += 1
        recs.append(_rec_id(idx, "3", "yyy", item_id=str(2000 + idx)))
    idx += 1
    recs.append(_rec_id(idx, "5", "ナナ", item_id="10000035"))  # Qiqi standard, ja name
    arch = GachaArchive(game="genshin", uid="u", lang="ja", records=recs)

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        h = analyze_character_history(arch, GENSHIN)

    assert h.five_star_count == 2
    assert h.fifty_fifty_total == 2 and h.fifty_fifty_wins == 1
    assert h.current_guaranteed is True


def test_history_item_id_takes_priority_over_name():
    """item_id 为常驻时，即使名字像 UP 也判为歪。"""
    recs = [_rec_id(1, "5", "芙宁娜", item_id="10000035")]  # Qiqi id, Furina name
    arch = GachaArchive(game="genshin", uid="u", lang="zh-cn", records=recs)
    h = analyze_character_history(arch, GENSHIN)
    assert h.current_guaranteed is True
    assert h.fifty_fifty_total == 1 and h.fifty_fifty_wins == 0
    # 常驻 5★ item_id 应来自该游戏的常驻角色集合
    assert "10000035" in STANDARD_5STAR_CHARACTER_ITEM_IDS
