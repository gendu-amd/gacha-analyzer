"""崩坏：星穹铁道（Honkai: Star Rail）机制 + 经济参数.

机制与原神高度相似：角色跃迁 50/50（无捕获明光），光锥跃迁 75/25。
数值基于 GGanalysis（1500 万抽统计）。
"""

from __future__ import annotations

import GGanalysis.games.honkai_star_rail as SR

from gacha.engine.base import BANNER_CHARACTER, BANNER_STANDARD, BANNER_WEAPON, PullState
from gacha.games.base import BannerSpec, GameSpec


def _character_dist(state: PullState, copies: int):
    """角色活动跃迁：抽 copies 个 UP 5★（50/50，无捕获明光）。"""
    up_pity = 1 if state.is_guaranteed else 0
    return SR.up_5star_character(item_num=copies, item_pity=state.item_pity, up_pity=up_pity)


def _light_cone_dist(state: PullState, copies: int):
    """光锥活动跃迁：抽 copies 个 UP 5★ 光锥（75/25，保底必出当期；非 EP 定轨）。"""
    up_pity = 1 if state.is_guaranteed else 0
    return SR.up_5star_weapon(item_num=copies, item_pity=state.item_pity, up_pity=up_pity)


def _standard_dist(state: PullState, copies: int):
    """星铁常驻跃迁「群星跃迁」：抽 copies 个任意 5★ 所需抽数（无 50/50、无捕获明光）。"""
    return SR.common_5star(item_num=copies, item_pity=state.item_pity)


HSR = GameSpec(
    key="hsr",
    name="星穹铁道",
    currency_name="星琼",
    currency_per_pull=160,
    money_per_pull_cny=16.0,
    money_note="米哈游统一口径 ≈¥16/抽（648 元 = 6480 古老梦华/星琼档）。近似值，可配。",
    free_pulls_per_month=60.0,  # 零氪约 84 抽/42天版本 → ≈60 抽/30天（社区统计，近似）
    banners={
        BANNER_CHARACTER: BannerSpec(
            key=BANNER_CHARACTER, name="角色活动跃迁", top_rarity_label="5★",
            hard_pity=90, has_5050=True, has_capturing_radiance=False,
            dist_fn=_character_dist,
        ),
        BANNER_WEAPON: BannerSpec(
            key=BANNER_WEAPON, name="光锥活动跃迁", top_rarity_label="5★",
            hard_pity=80, has_5050=True, has_capturing_radiance=False,  # 75/25，非 EP 定轨
            dist_fn=_light_cone_dist,
        ),
        BANNER_STANDARD: BannerSpec(
            key=BANNER_STANDARD, name="常驻跃迁(任意5★)", top_rarity_label="5★",
            hard_pity=90, has_5050=False, has_capturing_radiance=False,
            dist_fn=_standard_dist,
        ),
    },
)
