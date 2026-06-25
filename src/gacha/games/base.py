"""游戏与池子的声明式描述（机制 + 经济参数）.

设计：`BannerSpec.dist_fn` 是该池子把玩家状态映射到「抽数分布」的绑定函数
（内部委托 GGanalysis），这是唯一的游戏专属粘合点；引擎/分析层保持通用。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal, Mapping, Optional, Protocol

from gacha.engine.base import PullState


class HistoryRecord(Protocol):
    """UIGF 记录的最小接口（``games`` 层不依赖 ``io`` 模块）。"""

    @property
    def item_id(self) -> str: ...

    @property
    def name(self) -> str: ...


@dataclass(frozen=True)
class StandardDetection:
    """50/50 判定：是否抽到常驻（歪了）。

    Attributes:
        is_standard: True=常驻/歪，False=UP/赢，None=无法判定。
        source: 判定依据，供 ``io/history`` 决定是否告警。
    """

    is_standard: bool | None
    source: Literal["item_id", "name", "unknown"]


@dataclass(frozen=True)
class HistoryPolicy:
    """真实记录还原策略（``io/history`` 的可选钩子，使其 game-agnostic）.

    游戏专属逻辑（如原神 avatar_id 前缀、常驻表）封装在 ``detect_standard`` 回调中，
    ``io/history`` 只负责通用状态机（保底 / 捕获明光 / 50-50 计数）。

    Attributes:
        character_uigf_gacha_types: 归入「角色历史」的 uigf_gacha_type 集合。
        detect_standard: 判定单条 5★ 记录是否为常驻（歪了）。
        reliable_langs: 名字回退判定可靠的 UIGF 语言。
        has_capturing_radiance: 角色池是否有捕获明光。
        max_radiance_losses: 连歪计数上限。
    """

    character_uigf_gacha_types: frozenset[str]
    detect_standard: Callable[[HistoryRecord], StandardDetection]
    reliable_langs: frozenset[str] = frozenset({"zh-cn", "en"})
    has_capturing_radiance: bool = False
    max_radiance_losses: int = 3


@dataclass(frozen=True)
class BannerSpec:
    """单个池子的机制描述.

    Attributes:
        key: 池子键，如 "character" / "weapon"。
        name: 显示名。
        top_rarity_label: 最高稀有度标签，如 "5★"。
        hard_pity: 硬保底抽数（必出）。
        has_5050: 是否有「限定 UP 概率」机制。角色池为经典 50/50；
            武器池在星铁/绝区零为 75/25（大保底必出当期，非原神 EP 定轨）；
            原神武器池虽标 True，实际为 75/25 + 定轨命定值 1（见 ``up_5star_ep_weapon``）。
        has_capturing_radiance: 是否有「捕获明光」机制。
        dist_fn: (PullState, copies) -> GGanalysis FiniteDist。游戏专属绑定。
        reference_mc_mechanism: 可选；注入给 ``ReferenceMCSolver`` 的机制工厂（教学/校验）。
    """

    key: str
    name: str
    top_rarity_label: str
    hard_pity: int
    has_5050: bool
    has_capturing_radiance: bool
    dist_fn: Callable[[PullState, int], object]
    reference_mc_mechanism: Callable[[], object] | None = None


@dataclass(frozen=True)
class GameSpec:
    """单个游戏的机制 + 经济参数（跨游戏比对的基础）.

    Attributes:
        key: 游戏键，如 "genshin"。
        name: 显示名，如 "原神"。
        currency_name: 抽卡货币名，如 "原石"。
        currency_per_pull: 一抽所需货币量。
        money_per_pull_cny: 估算每抽人民币（按最高性价比常规档位，排除首充双倍；近似值）。
        money_note: 经济参数口径/来源说明。
        free_pulls_per_month: 零氪每 30 天可获得的抽数（近似，用于跨游戏白嫖速率比较）。
        banners: 池子键 -> BannerSpec。
        history_policy: 真实记录还原策略（可选钩子）；None 表示该游戏暂不支持 history 还原。
    """

    key: str
    name: str
    currency_name: str
    currency_per_pull: int
    money_per_pull_cny: float
    money_note: str
    banners: Mapping[str, BannerSpec]
    free_pulls_per_month: float = 0.0
    history_policy: Optional[HistoryPolicy] = None

    def banner(self, key: str) -> BannerSpec:
        if key not in self.banners:
            raise KeyError(
                f"游戏 {self.name} 不支持池子 '{key}'，可选：{list(self.banners)}"
            )
        return self.banners[key]
