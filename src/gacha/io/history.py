"""从真实抽卡记录还原保底状态与历史统计（game-agnostic，机制由 GameSpec 提供）.

输出可直接喂给求解器的 PullState，以及终身抽数 / 5★ 出货 / 50-50 胜率等统计。
50/50 判定、常驻识别等游戏专属逻辑由 ``game.history_policy.detect_standard`` 注入。
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field

from gacha.engine.base import BANNER_CHARACTER, PullState
from gacha.games.base import GameSpec, HistoryPolicy
from gacha.io.uigf import GachaArchive, GachaRecord


@dataclass
class BannerHistory:
    game: str
    banner: str
    total_pulls: int
    five_star_count: int
    five_star_pities: list[int] = field(default_factory=list)
    five_star_names: list[str] = field(default_factory=list)
    average_5star_pity: float = 0.0
    current_pity: int = 0
    current_guaranteed: bool = False
    radiance_losses: int = 0
    fifty_fifty_total: int = 0
    fifty_fifty_wins: int = 0

    @property
    def fifty_fifty_winrate(self) -> float:
        if self.fifty_fifty_total == 0:
            return float("nan")
        return self.fifty_fifty_wins / self.fifty_fifty_total

    @property
    def state(self) -> PullState:
        """还原出的当前抽卡状态，可直接用于预测。"""
        return PullState(
            item_pity=self.current_pity,
            is_guaranteed=self.current_guaranteed,
            radiance_losses=self.radiance_losses,
        )


def _character_records(
    archive: GachaArchive, policy: HistoryPolicy
) -> list[GachaRecord]:
    """归入「角色历史」的记录（按 id 升序）。

    同时检查 ``uigf_gacha_type`` 与 ``gacha_type``，避免某条记录缺 uigf 字段时被排除。
    """
    types = policy.character_uigf_gacha_types
    out = []
    for r in archive.sorted_records():
        if r.uigf_gacha_type in types or r.gacha_type in types:
            out.append(r)
    return out


def analyze_character_history(
    archive: GachaArchive, game: GameSpec | None = None
) -> BannerHistory:
    """分析角色活动池历史记录（机制由 ``game.history_policy`` 注入）。"""
    if game is None:
        from gacha.games.registry import get_game

        game = get_game(archive.game)
    policy = game.history_policy
    if policy is None:
        raise NotImplementedError(
            f"游戏 {game.name} 未配置 history_policy，暂不支持真实记录还原"
        )

    records = _character_records(archive, policy)

    pities: list[int] = []
    names: list[str] = []
    five_stars: list[GachaRecord] = []
    since = 0
    for r in records:
        since += 1
        if r.rank_type == "5":
            pities.append(since)
            names.append(r.name)
            five_stars.append(r)
            since = 0
    current_pity = since

    unreliable_5050 = []
    for r in five_stars:
        det = policy.detect_standard(r)
        if det.source == "unknown" or (
            det.source == "name" and archive.lang not in policy.reliable_langs
        ):
            unreliable_5050.append(r)
    if unreliable_5050:
        warnings.warn(
            f"UIGF lang='{archive.lang}' 且 {len(unreliable_5050)} 条 5★ "
            f"依赖名字或无法判定常驻，50/50 可能不准（可靠语言：{sorted(policy.reliable_langs)}）。",
            stacklevel=2,
        )

    guaranteed = False
    losses = 0
    wins = 0
    total_5050 = 0
    for r in five_stars:
        det = policy.detect_standard(r)
        std = det.is_standard if det.is_standard is not None else False
        if guaranteed:
            guaranteed = False
        else:
            total_5050 += 1
            if std:
                guaranteed = True
                if policy.has_capturing_radiance:
                    losses = min(losses + 1, policy.max_radiance_losses)
            else:
                wins += 1
                losses = 0

    avg = sum(pities) / len(pities) if pities else 0.0
    return BannerHistory(
        game=game.key,
        banner=BANNER_CHARACTER,
        total_pulls=len(records),
        five_star_count=len(pities),
        five_star_pities=pities,
        five_star_names=names,
        average_5star_pity=avg,
        current_pity=current_pity,
        current_guaranteed=guaranteed,
        radiance_losses=losses,
        fifty_fifty_total=total_5050,
        fifty_fifty_wins=wins,
    )
