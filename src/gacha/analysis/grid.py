"""命座×精炼 成本网格：角色拷贝数 × 武器拷贝数 的联合期望抽数/花费.

行 = 角色命座（C0..C6 → 1..7 个拷贝），列 = 武器精炼（R0..R5，R0=不要武器）。
每格 = 角色+武器联合期望（卷积），可换算货币/人民币。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gacha.analysis import budget as budget_mod
from gacha.analysis import combine, metrics
from gacha.engine.base import BANNER_CHARACTER, BANNER_WEAPON, PullState, Target

# 各游戏命座/魂/影位的称呼前缀
CONST_PREFIX = {"genshin": "C", "hsr": "E", "zzz": "M"}


@dataclass
class CostGrid:
    game_key: str
    game_name: str
    const_prefix: str
    max_const: int
    max_refine: int
    exp_pulls: list[list[float]] = field(default_factory=list)
    money_cny: list[list[float]] = field(default_factory=list)

    def const_labels(self) -> list[str]:
        return [f"{self.const_prefix}{c}" for c in range(self.max_const + 1)]

    def refine_labels(self) -> list[str]:
        return ["R0"] + [f"R{r}" for r in range(1, self.max_refine + 1)]


def cost_grid(
    solver,
    game,
    char_state: PullState | None = None,
    weap_state: PullState | None = None,
    max_const: int = 6,
    max_refine: int = 5,
) -> CostGrid:
    """计算某游戏的「命座×精炼」联合期望抽数与人民币网格。"""
    char_state = char_state or PullState()
    weap_state = weap_state or PullState()
    has_weapon = BANNER_WEAPON in game.banners

    grid = CostGrid(
        game_key=game.key, game_name=game.name,
        const_prefix=CONST_PREFIX.get(game.key, "C"),
        max_const=max_const, max_refine=max_refine,
    )
    for c in range(max_const + 1):           # 命座 0..max_const → 角色拷贝 c+1
        exp_row, money_row = [], []
        for w in range(max_refine + 1):       # 精炼 0..max_refine → 武器拷贝 w
            items = [(char_state, Target(BANNER_CHARACTER, c + 1))]
            if w > 0 and has_weapon:
                items.append((weap_state, Target(BANNER_WEAPON, w)))
            dist = combine.combine_targets(game, solver, items)
            e = metrics.expectation(dist)
            exp_row.append(e)
            money_row.append(budget_mod.pulls_to_money_cny(game, e))
        grid.exp_pulls.append(exp_row)
        grid.money_cny.append(money_row)
    return grid


def parse_cell_code(code: str) -> tuple[int, int]:
    """解析两位数编码 ``CR`` → (命座等级, 精炼等级)，如 ``01`` → (0,1)。"""
    code = code.strip()
    if len(code) != 2 or not code.isdigit():
        raise ValueError(f"无效单元格编码 '{code}'，应为两位数字如 00/01/21/65")
    return int(code[0]), int(code[1])


def cell_label(game_key: str, const: int, refine: int) -> str:
    """单元格标签，如 genshin 的 (2,1) → ``C2R1``。"""
    prefix = CONST_PREFIX.get(game_key, "C")
    return f"{prefix}{const}R{refine}"


def cell_distribution(
    solver,
    game,
    const: int,
    refine: int,
    char_state: PullState | None = None,
    weap_state: PullState | None = None,
):
    """某格 (命座, 精炼) 的联合抽数分布。"""
    char_state = char_state or PullState()
    weap_state = weap_state or PullState()
    items = [(char_state, Target(BANNER_CHARACTER, const + 1))]
    if refine > 0 and BANNER_WEAPON in game.banners:
        items.append((weap_state, Target(BANNER_WEAPON, refine)))
    return combine.combine_targets(game, solver, items)


def all_cell_codes(max_const: int = 6, max_refine: int = 5) -> list[str]:
    """全部 ``CR`` 编码列表。"""
    return [f"{c}{r}" for c in range(max_const + 1) for r in range(max_refine + 1)]

