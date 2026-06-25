"""预算与资源换算：抽数 <-> 货币 <-> 人民币，以及预算->把握度。"""

from __future__ import annotations

from dataclasses import dataclass

from gacha.analysis import metrics
from gacha.engine.base import PullDistribution
from gacha.games.base import GameSpec


def pulls_to_currency(game: GameSpec, pulls: float) -> float:
    return pulls * game.currency_per_pull


def currency_to_pulls(game: GameSpec, currency: float) -> float:
    return currency / game.currency_per_pull


def pulls_to_money_cny(game: GameSpec, pulls: float) -> float:
    return pulls * game.money_per_pull_cny


@dataclass(frozen=True)
class BudgetResult:
    pulls: int
    currency: float
    money_cny: float
    probability: float


def budget_outlook(game: GameSpec, dist: PullDistribution, pulls: int) -> BudgetResult:
    """给定抽数预算，给出对应货币/人民币与达成把握。"""
    return BudgetResult(
        pulls=pulls,
        currency=pulls_to_currency(game, pulls),
        money_cny=pulls_to_money_cny(game, pulls),
        probability=metrics.prob_within(dist, pulls),
    )


def cost_for_confidence(game: GameSpec, dist: PullDistribution, p: float) -> BudgetResult:
    """达成把握 p 所需的抽数 / 货币 / 人民币。"""
    pulls = metrics.pulls_for_confidence(dist, p)
    if pulls < 0:
        return BudgetResult(pulls=-1, currency=float("nan"),
                            money_cny=float("nan"), probability=p)
    return budget_outlook(game, dist, pulls)
