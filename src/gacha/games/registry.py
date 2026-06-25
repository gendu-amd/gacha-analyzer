"""游戏注册表：跨游戏比对的统一入口。"""

from __future__ import annotations

from gacha.games.base import GameSpec
from gacha.games.genshin import GENSHIN
from gacha.games.hsr import HSR
from gacha.games.zzz import ZZZ_GAME

_REGISTRY: dict[str, GameSpec] = {
    GENSHIN.key: GENSHIN,
    HSR.key: HSR,
    ZZZ_GAME.key: ZZZ_GAME,
}


def get_game(key: str) -> GameSpec:
    if key not in _REGISTRY:
        raise KeyError(f"未注册的游戏 '{key}'，可选：{list(_REGISTRY)}")
    return _REGISTRY[key]


def list_games() -> list[str]:
    return list(_REGISTRY)
