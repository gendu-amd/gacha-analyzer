"""绝区零（Zenless Zone Zero）机制 + 经济参数.

角色频段 50/50（无捕获明光），音擎频段 75/25（保底必出当期）。
数值基于 GGanalysis。
"""

from __future__ import annotations

import GGanalysis.games.zenless_zone_zero as ZZZ

from gacha.engine.base import BANNER_CHARACTER, BANNER_STANDARD, BANNER_WEAPON, PullState
from gacha.games.base import BannerSpec, GameSpec


def _character_dist(state: PullState, copies: int):
    """独家频段（角色）：抽 copies 个 UP S 级（50/50）。"""
    up_pity = 1 if state.is_guaranteed else 0
    return ZZZ.up_5star_character(item_num=copies, item_pity=state.item_pity, up_pity=up_pity)


def _engine_dist(state: PullState, copies: int):
    """音擎频段（武器）：抽 copies 个 UP S 级音擎（75/25，保底必出当期；非 EP 定轨）。"""
    up_pity = 1 if state.is_guaranteed else 0
    return ZZZ.up_5star_weapon(item_num=copies, item_pity=state.item_pity, up_pity=up_pity)


def _standard_dist(state: PullState, copies: int):
    """绝区零常驻频段「独家视界」：抽 copies 个任意 S 级所需抽数（无 50/50）。"""
    return ZZZ.common_5star(item_num=copies, item_pity=state.item_pity)


ZZZ_GAME = GameSpec(
    key="zzz",
    name="绝区零",
    currency_name="菲林",
    currency_per_pull=160,
    money_per_pull_cny=16.0,
    money_note="米哈游统一口径 ≈¥16/抽。近似值，可配。",
    free_pulls_per_month=48.0,  # 零氪约 67 抽/42天版本 → ≈48 抽/30天（社区统计，近似）
    banners={
        BANNER_CHARACTER: BannerSpec(
            key=BANNER_CHARACTER, name="独家频段(角色)", top_rarity_label="S级",
            hard_pity=90, has_5050=True, has_capturing_radiance=False,
            dist_fn=_character_dist,
        ),
        BANNER_WEAPON: BannerSpec(
            key=BANNER_WEAPON, name="音擎频段(武器)", top_rarity_label="S级",
            hard_pity=80, has_5050=True, has_capturing_radiance=False,  # 75/25，非 EP 定轨
            dist_fn=_engine_dist,
        ),
        BANNER_STANDARD: BannerSpec(
            key=BANNER_STANDARD, name="常驻频段(任意S级)", top_rarity_label="S级",
            hard_pity=90, has_5050=False, has_capturing_radiance=False,
            dist_fn=_standard_dist,
        ),
    },
)
