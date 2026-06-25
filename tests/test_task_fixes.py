"""本轮修复的回归测试：history item_id、compare CNY 折叠、CJK 列宽。"""

import warnings

import pytest

from gacha.analysis import compare
from gacha.engine.gg_adapter import GGanalysisSolver
from gacha.games.genshin import STANDARD_5STAR_CHARACTER_ITEM_IDS
from gacha.games.registry import get_game
from gacha.io.history import analyze_character_history
from gacha.io.uigf import GachaArchive, GachaRecord
from gacha.viz.text_width import display_width, ljust_display

SOLVER = GGanalysisSolver()
GENSHIN = get_game("genshin")


def _rec(i, rank, name, item_id="", gacha_type="301", uigf="301", lang_item_id=True):
    iid = item_id if item_id else (list(STANDARD_5STAR_CHARACTER_ITEM_IDS)[0]
                                   if name == "七七" else str(i))
    return GachaRecord(
        id=str(10_000 + i), gacha_type=gacha_type, uigf_gacha_type=uigf,
        item_id=iid if lang_item_id else "", name=name, rank_type=rank,
        item_type="角色", time="2024-01-01 00:00:00",
    )


def test_history_standard_by_item_id_japanese_no_warning():
    """日文 lang + item_id：不依赖名字，50/50 可正确判定且无告警。"""
    recs = []
    idx = 0
    for _ in range(9):
        idx += 1
        recs.append(_rec(idx, "3", "xxx", item_id=str(1000 + idx)))
    idx += 1
    recs.append(_rec(idx, "5", "フリーナ", item_id="10000089"))  # Furina UP
    for _ in range(9):
        idx += 1
        recs.append(_rec(idx, "3", "yyy", item_id=str(2000 + idx)))
    idx += 1
    recs.append(_rec(idx, "5", "ナナ", item_id="10000035"))  # Qiqi standard, ja name
    arch = GachaArchive(game="genshin", uid="u", lang="ja", records=recs)

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        h = analyze_character_history(arch, GENSHIN)

    assert h.five_star_count == 2
    assert h.fifty_fifty_total == 2 and h.fifty_fifty_wins == 1
    assert h.current_guaranteed is True


def test_history_item_id_takes_priority_over_name():
    """item_id 为常驻时，即使名字像 UP 也判为歪。"""
    recs = [_rec(1, "5", "芙宁娜", item_id="10000035")]  # Qiqi id, Furina name
    arch = GachaArchive(game="genshin", uid="u", lang="zh-cn", records=recs)
    h = analyze_character_history(arch, GENSHIN)
    assert h.current_guaranteed is True
    assert h.fifty_fifty_total == 1 and h.fifty_fifty_wins == 0


def test_compare_shared_cny_collapses_column():
    rows = compare.compare_games(SOLVER, ["genshin", "hsr", "zzz"], banner="character")
    assert compare.shared_money_per_pull_cny(rows) == pytest.approx(16.0)
    from gacha.viz.tables import format_compare_table
    txt = format_compare_table(rows)
    assert "折人民币统一按 ¥16/抽" in txt
    assert "¥1495" not in txt  # 不应逐行重复大额人民币


def test_display_width_cjk_alignment():
    assert display_width("原神") == 4
    assert display_width("abc") == 3
    padded = ljust_display("原神", 8)
    assert display_width(padded) == 8
