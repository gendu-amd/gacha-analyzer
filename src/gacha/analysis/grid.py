"""命座×精炼 成本网格：角色拷贝数 × 武器拷贝数 的联合期望抽数/花费.

行 = 角色命座（C0..C6 → 1..7 个拷贝），列 = 武器精炼（R0..R5，R0=不要武器）。
每格 = 角色+武器联合期望（卷积），可换算货币/人民币。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gacha.analysis import budget as budget_mod
from gacha.analysis import combine, metrics
from gacha.engine.base import BANNER_CHARACTER, BANNER_WEAPON, PullState, Target


@dataclass(frozen=True)
class GridTerms:
    """单个游戏「角色重复 × 武器重复」网格的术语（按游戏切换，避免写死原神黑话）.

    Attributes:
        const_noun: 角色重复维度的中文名（命座 / 星魂 / 影位）。
        const_noun_en: 对应英文名（PNG 在无 CJK 字体环境下使用）。
        const_prefix: 行标前缀（C / E / M）。
        refine_noun: 武器重复维度的中文名（精炼 / 叠影）。
        refine_noun_en: 对应英文名。
        refine_prefix: 列标前缀（R / S）。
    """

    const_noun: str
    const_noun_en: str
    const_prefix: str
    refine_noun: str
    refine_noun_en: str
    refine_prefix: str


# 各游戏术语单一数据源：原神=命座/精炼、星铁=星魂/叠影、绝区零=影位/叠影。
GRID_TERMS: dict[str, GridTerms] = {
    "genshin": GridTerms("命座", "Constellation", "C", "精炼", "Refinement", "R"),
    "hsr": GridTerms("星魂", "Eidolon", "E", "叠影", "Superimposition", "S"),
    "zzz": GridTerms("影位", "Mindscape", "M", "叠影", "Superimposition", "S"),
}
DEFAULT_TERMS = GridTerms("命座", "Constellation", "C", "精炼", "Refinement", "R")


def grid_terms(game_key: str) -> GridTerms:
    """按游戏键取术语，未知游戏回退到原神口径。"""
    return GRID_TERMS.get(game_key, DEFAULT_TERMS)


@dataclass
class CostGrid:
    game_key: str
    game_name: str
    terms: GridTerms
    max_const: int
    max_refine: int
    exp_pulls: list[list[float]] = field(default_factory=list)
    money_cny: list[list[float]] = field(default_factory=list)

    @property
    def const_prefix(self) -> str:
        return self.terms.const_prefix

    @property
    def refine_prefix(self) -> str:
        return self.terms.refine_prefix

    def const_labels(self) -> list[str]:
        return [f"{self.terms.const_prefix}{c}" for c in range(self.max_const + 1)]

    def refine_labels(self) -> list[str]:
        p = self.terms.refine_prefix
        return [f"{p}{r}" for r in range(self.max_refine + 1)]


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
        terms=grid_terms(game.key),
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
    """单元格标签，如 genshin 的 (2,1) → ``C2R1``、hsr 的 (2,1) → ``E2S1``。"""
    t = grid_terms(game_key)
    return f"{t.const_prefix}{const}{t.refine_prefix}{refine}"


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

