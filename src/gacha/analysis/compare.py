"""跨游戏归一化比对（M3）.

口径（见 docs/RESEARCH.md §3）：以「抽 1 个当期限定最高稀有度（从零、含 50/50）」为单位，
比较 期望抽数 / 期望货币 / 折算人民币 / 每月白嫖可得限定数 / 相对成本。

⚠️ 不可比的坑（务必知晓）：仅比限定、仅比同类池（默认角色池）；不同游戏货币与白嫖速率
口径有近似误差；明日方舟等非米哈游游戏的「基础出率」不可直接比（本模块默认比米哈游三游）。
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

from gacha.analysis import combine, metrics
from gacha.engine.base import BANNER_CHARACTER, BANNER_WEAPON, PullState, Target
from gacha.engine.base import PullDistribution
from gacha.games.registry import get_game, list_games

# 跨游戏比对的固定免责标注（8 个不可比的坑只在文档里，这里落到返回结构 + 运行期告警）。
COMPARE_CAVEAT = (
    "仅供参考：跨游戏比对仅比『限定·同类池』，货币与白嫖速率为社区近似口径；"
    "基础出率/保底结构/版本长度等不可直接比（详见 docs/RESEARCH.md §3.4）。"
)


@dataclass
class ComparisonRow:
    game_key: str
    game_name: str
    banner_name: str
    top_rarity: str
    exp_pulls: float
    currency_name: str
    exp_currency: float
    exp_money_cny: float
    p50: int
    p90: int
    free_pulls_per_month: float
    free_featured_per_month: float
    relative_cost: float = 1.0
    caveat: str = COMPARE_CAVEAT


def shared_money_per_pull_cny(rows: list[ComparisonRow]) -> float | None:
    """若所有参与比对的游戏单抽人民币相同，返回该统一基准；否则 None。"""
    if not rows:
        return None
    rates = {get_game(r.game_key).money_per_pull_cny for r in rows}
    if len(rates) == 1:
        return rates.pop()
    return None


def compare_games(
    solver,
    game_keys: list[str] | None = None,
    banner: str = BANNER_CHARACTER,
    copies: int = 1,
    state: PullState | None = None,
) -> list[ComparisonRow]:
    """对多款游戏的同类卡池做归一化比较，返回按期望抽数升序（最划算在前）的行。

    护栏：比较 ≥2 款游戏时发出 ``warnings.warn``，提醒「8 个不可比的坑」，并在每行
    ``caveat`` 字段附带「仅供参考」标注（见 ``COMPARE_CAVEAT``）。
    """
    if game_keys is None:
        game_keys = list_games()
    if state is None:
        state = PullState()

    rows: list[ComparisonRow] = []
    for key in game_keys:
        game = get_game(key)
        if banner not in game.banners:
            continue
        b = game.banners[banner]
        dist = solver.solve(game, state, Target(banner, copies), 0)
        exp = metrics.expectation(dist)
        free_feat = (game.free_pulls_per_month / exp) if exp > 0 else 0.0
        rows.append(ComparisonRow(
            game_key=key,
            game_name=game.name,
            banner_name=b.name,
            top_rarity=b.top_rarity_label,
            exp_pulls=exp,
            currency_name=game.currency_name,
            exp_currency=exp * game.currency_per_pull,
            exp_money_cny=exp * game.money_per_pull_cny,
            p50=metrics.quantile(dist, 0.5),
            p90=metrics.quantile(dist, 0.9),
            free_pulls_per_month=game.free_pulls_per_month,
            free_featured_per_month=free_feat,
        ))

    rows.sort(key=lambda r: r.exp_pulls)
    if rows:
        cheapest = rows[0].exp_pulls
        for r in rows:
            r.relative_cost = r.exp_pulls / cheapest if cheapest else 1.0
    if len(rows) >= 2:
        warnings.warn(COMPARE_CAVEAT, stacklevel=2)
    return rows


@dataclass
class CombineComparisonRow:
    """跨游戏 n+n（角色+武器组合）比对行。"""

    game_key: str
    game_name: str
    char_copies: int
    weap_copies: int
    exp_pulls: float
    currency_name: str
    exp_currency: float
    exp_money_cny: float
    p50: int
    p90: int
    relative_cost: float = 1.0
    char_only: bool = False
    dist: PullDistribution | None = None
    caveat: str = COMPARE_CAVEAT


def compare_combine_games(
    solver,
    char_copies: int = 1,
    weap_copies: int = 1,
    game_keys: list[str] | None = None,
    char_state: PullState | None = None,
    weap_state: PullState | None = None,
) -> list[CombineComparisonRow]:
    """跨游戏组合目标比对：各游戏运行 combine_targets，比较联合期望与分位。

    无武器池的游戏：若 weap_copies>0 则降级为仅角色并 ``char_only=True``，发出告警。
    """
    if game_keys is None:
        game_keys = list_games()
    char_state = char_state or PullState()
    weap_state = weap_state or PullState()

    rows: list[CombineComparisonRow] = []
    for key in game_keys:
        game = get_game(key)
        has_weapon = BANNER_WEAPON in game.banners
        char_only = False
        items: list[tuple[PullState, Target]] = []
        if char_copies > 0:
            items.append((char_state, Target(BANNER_CHARACTER, char_copies)))
        if weap_copies > 0:
            if has_weapon:
                items.append((weap_state, Target(BANNER_WEAPON, weap_copies)))
            else:
                char_only = True
                warnings.warn(
                    f"{game.name} 无武器池，跳过武器部分（仅角色 {char_copies} 拷贝）",
                    stacklevel=2,
                )
        if not items:
            continue

        dist = combine.combine_targets(game, solver, items)
        exp = metrics.expectation(dist)
        rows.append(CombineComparisonRow(
            game_key=key,
            game_name=game.name,
            char_copies=char_copies,
            weap_copies=0 if char_only else weap_copies,
            exp_pulls=exp,
            currency_name=game.currency_name,
            exp_currency=exp * game.currency_per_pull,
            exp_money_cny=exp * game.money_per_pull_cny,
            p50=metrics.quantile(dist, 0.5),
            p90=metrics.quantile(dist, 0.9),
            char_only=char_only,
            dist=dist,
        ))

    rows.sort(key=lambda r: r.exp_pulls)
    if rows:
        cheapest = rows[0].exp_pulls
        for r in rows:
            r.relative_cost = r.exp_pulls / cheapest if cheapest else 1.0
    if len(rows) >= 2:
        warnings.warn(COMPARE_CAVEAT, stacklevel=2)
    return rows

