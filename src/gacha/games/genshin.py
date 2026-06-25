"""原神（Genshin Impact）机制 + 经济参数.

机制数值来源见 docs/games/genshin.md（社区基于 2500 万+ 抽实测，与官方公示一致）。
本文件同时定义「自研 reference 引擎」所需的机制常量（教学透明），并与 GGanalysis 交叉验证。
"""

from __future__ import annotations

import GGanalysis.games.genshin_impact as GI

from gacha.engine.base import (
    BANNER_CHARACTER,
    BANNER_CHRONICLED,
    BANNER_STANDARD,
    BANNER_WEAPON,
    PullState,
)
from gacha.engine.reference.mc import CharacterMechanism
from gacha.games.base import BannerSpec, GameSpec, HistoryPolicy, StandardDetection

# --- 角色活动池 5★ 机制常量（自研引擎与教学使用） ---
FIVE_STAR_BASE = 0.006      # 基础概率
SOFT_PITY_START = 74        # 软保底起点（第 74 抽起线性提升）
SOFT_PITY_STEP = 0.06       # 软保底每抽增量
HARD_PITY = 90              # 硬保底（必出）

# 「捕获明光」：连歪 k 次时，下一个 5★ 为 UP 的概率（索引 = 连歪次数 0..3）
# 对齐 GGanalysis CR_PITY[1:] = [0.5, 0.55, 0.95, 1]
CR_UP_PROB = (0.5, 0.55, 0.95, 1.0)

# 角色池常驻 5★：优先用 UIGF item_id（语言无关），名字作回退。
# item_id 来源：游戏内角色 avatar_id / UIGF API（https://uigf.org/en/api.html）
STANDARD_5STAR_CHARACTER_ITEM_IDS = frozenset({
    "10000003",  # 琴 Jean
    "10000023",  # 迪卢克 Diluc
    "10000035",  # 七七 Qiqi
    "10000041",  # 莫娜 Mona
    "10000042",  # 刻晴 Keqing
    "10000069",  # 提纳里 Tighnari
    "10000079",  # 迪希雅 Dehya
})
# 名字回退（item_id 缺失时）；含中英文名以兼容不同 lang。
STANDARD_5STAR_CHARACTERS = frozenset({
    "迪卢克", "琴", "刻晴", "莫娜", "七七", "提纳里", "迪希雅",
    "Diluc", "Jean", "Keqing", "Mona", "Qiqi", "Tighnari", "Dehya",
})

# UIGF 中原神角色活动祈愿（含 301 与 400，共享保底）的 uigf_gacha_type
CHARACTER_UIGF_GACHA_TYPE = "301"
WEAPON_UIGF_GACHA_TYPE = "302"


def _detect_genshin_standard(record) -> StandardDetection:
    """原神角色池：判定 5★ 是否为常驻（歪了）。优先 item_id，回退名字。"""
    iid = (record.item_id or "").strip()
    if iid:
        if iid in STANDARD_5STAR_CHARACTER_ITEM_IDS:
            return StandardDetection(True, "item_id")
        if len(iid) >= 8 and iid.startswith("1000"):
            return StandardDetection(False, "item_id")
    name = (record.name or "").strip()
    if name:
        return StandardDetection(name in STANDARD_5STAR_CHARACTERS, "name")
    return StandardDetection(None, "unknown")


def five_star_pull_prob(pity: int) -> float:
    """第 ``pity`` 抽（1-indexed，距上次 5★）的 5★ 出货概率。

    pity<=73: 基础 0.6%；74<=pity<=89: 线性提升；pity>=90: 100%。
    """
    if pity < 1:
        raise ValueError("pity 从 1 开始计数")
    if pity >= HARD_PITY:
        return 1.0
    if pity < SOFT_PITY_START:
        return FIVE_STAR_BASE
    return min(1.0, FIVE_STAR_BASE + SOFT_PITY_STEP * (pity - SOFT_PITY_START + 1))


def genshin_character_mechanism() -> CharacterMechanism:
    """构造注入给 reference-MC 的原神角色池机制（出率曲线 / 硬保底 / 捕获明光表）。

    这是「engine 不依赖 games」单向铁律下的注入点：由 games 层把原神常量喂给 game-agnostic
    的 ``ReferenceMCSolver``。
    """
    return CharacterMechanism(
        rate_fn=five_star_pull_prob,
        hard_pity=HARD_PITY,
        cr_up_prob=CR_UP_PROB,
    )


def _to_gg_kwargs(state: PullState) -> dict:
    """把统一 PullState 映射为 GGanalysis 角色池参数。

    约定（与 GGanalysis 一致）：大保底(up_pity=1)必伴随捕获明光连歪>=1；
    若调用方未跟踪明光计数（radiance_losses=0）但处于大保底，折算为 1。
    """
    up_pity = 1 if state.is_guaranteed else 0
    cr_pity = state.radiance_losses
    if up_pity == 1 and cr_pity == 0:
        cr_pity = 1
    return {"item_pity": state.item_pity, "up_pity": up_pity, "cr_pity": cr_pity}


def _character_dist(state: PullState, copies: int):
    """原神角色活动池：抽 ``copies`` 个 UP 5★ 所需抽数分布（GGanalysis，含捕获明光）。"""
    return GI.up_5star_character(item_num=copies, **_to_gg_kwargs(state))


# --- 武器活动池常量（5.0 起命定值为 1 的定轨） ---
W_FIVE_STAR_BASE = 0.007
W_SOFT_PITY_START = 63
W_HARD_PITY = 80  # 官方公示硬保底（GGanalysis 模型在 77 抽即升至 100%）


def _weapon_dist(state: PullState, copies: int):
    """原神武器活动池：抽 ``copies`` 把指定 UP 5★ 武器所需抽数（定轨命定值 1）。

    捕获明光不作用于武器池，radiance_losses 被忽略；is_guaranteed 表示已有 1 命定值。
    """
    up_pity = 1 if state.is_guaranteed else 0
    return GI.up_5star_ep_weapon(item_num=copies, item_pity=state.item_pity, up_pity=up_pity)


def _standard_dist(state: PullState, copies: int):
    """原神常驻祈愿「奔行世间」：抽 ``copies`` 个任意 5★ 所需抽数（无 50/50、无捕获明光）。"""
    return GI.common_5star(item_num=copies, item_pity=state.item_pity)


def _chronicled_dist(state: PullState, copies: int):
    """原神集录祈愿：抽 ``copies`` 个指定 5★ 所需抽数。

    机制为经典 50/50（1 命定值保底，无捕获明光），等价于 GGanalysis classic_up_5star_character。
    is_guaranteed 表示已有 1 命定值；radiance_losses 不适用，被忽略。
    """
    up_pity = 1 if state.is_guaranteed else 0
    return GI.classic_up_5star_character(item_num=copies, item_pity=state.item_pity, up_pity=up_pity)


GENSHIN = GameSpec(
    key="genshin",
    name="原神",
    currency_name="原石",
    currency_per_pull=160,
    money_per_pull_cny=16.0,  # 6480 创世结晶=¥648 → 40.5 抽，约 ¥16/抽（最优常规档，排除首充双倍）
    money_note="按国服 6480 创世结晶 ¥648 的常规档折算（≈¥16/抽）；首充双倍约 ¥8/抽。近似值，可配。",
    free_pulls_per_month=54.0,  # 零氪约 76 抽/42天版本 → ≈54 抽/30天（社区统计，近似）
    banners={
        BANNER_CHARACTER: BannerSpec(
            key=BANNER_CHARACTER,
            name="角色活动祈愿",
            top_rarity_label="5★",
            hard_pity=HARD_PITY,
            has_5050=True,
            has_capturing_radiance=True,
            dist_fn=_character_dist,
            reference_mc_mechanism=genshin_character_mechanism,
        ),
        BANNER_WEAPON: BannerSpec(
            key=BANNER_WEAPON,
            name="武器活动祈愿",
            top_rarity_label="5★",
            hard_pity=W_HARD_PITY,
            has_5050=True,  # 75/25 + 定轨命定值1
            has_capturing_radiance=False,
            dist_fn=_weapon_dist,
        ),
        BANNER_STANDARD: BannerSpec(
            key=BANNER_STANDARD,
            name="常驻祈愿(任意5★)",
            top_rarity_label="5★",
            hard_pity=HARD_PITY,
            has_5050=False,
            has_capturing_radiance=False,
            dist_fn=_standard_dist,
        ),
        BANNER_CHRONICLED: BannerSpec(
            key=BANNER_CHRONICLED,
            name="集录祈愿",
            top_rarity_label="5★",
            hard_pity=HARD_PITY,
            has_5050=True,  # 经典 50/50，1 命定值，无捕获明光
            has_capturing_radiance=False,
            dist_fn=_chronicled_dist,
        ),
    },
    # 历史还原策略（io/history 通过该可选钩子 game-agnostic 地读取；目前仅原神填充）。
    history_policy=HistoryPolicy(
        character_uigf_gacha_types=frozenset({CHARACTER_UIGF_GACHA_TYPE, "400"}),
        detect_standard=_detect_genshin_standard,
        reliable_langs=frozenset({"zh-cn", "en"}),
        has_capturing_radiance=True,
        max_radiance_losses=3,
    ),
)
