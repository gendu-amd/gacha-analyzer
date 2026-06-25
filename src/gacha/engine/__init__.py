"""引擎层：统一封装 GGanalysis（主）+ reference 自研引擎（校验/教学）。"""

from gacha.engine.base import PullState, Target, PullDistribution, Solver

__all__ = ["PullState", "Target", "PullDistribution", "Solver"]
