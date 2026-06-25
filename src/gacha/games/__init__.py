"""游戏层：机制 + 经济参数（声明式）+ 游戏注册表。

新增游戏 = 新增 games/<game>.py 并在 registry 注册，不改引擎/分析核心。
"""

from gacha.games.base import BannerSpec, GameSpec
from gacha.games.registry import get_game, list_games

__all__ = ["BannerSpec", "GameSpec", "get_game", "list_games"]
