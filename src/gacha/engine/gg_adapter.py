"""GGanalysis 封装求解器（主引擎）.

把统一的 (game, state, target) 委托给游戏的 dist_fn（内部调用 GGanalysis），
返回统一的 PullDistribution。这是项目的「算得准」基座。
"""

from __future__ import annotations

import numpy as np

from gacha.engine.base import PullDistribution, PullState, Target


class GGanalysisSolver:
    """主求解器：基于 GGanalysis 的精确卷积解。"""

    name = "gganalysis"

    def solve(
        self,
        game,
        state: PullState,
        target: Target,
        max_pulls: int = 0,
    ) -> PullDistribution:
        banner = game.banner(target.banner)
        finite_dist = banner.dist_fn(state, target.copies)
        pmf = np.asarray(finite_dist.dist, dtype=float)
        if max_pulls and max_pulls > 0:
            if len(pmf) > max_pulls + 1:
                pmf = pmf[: max_pulls + 1]
            elif len(pmf) < max_pulls + 1:
                pmf = np.pad(pmf, (0, max_pulls + 1 - len(pmf)))
        return PullDistribution(pmf=pmf, source=self.name)
